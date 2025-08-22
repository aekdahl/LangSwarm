import re
import sys
import json
import time
import socket
import requests
import subprocess
import importlib.util
from typing import Any, Dict, Optional

"""
steps:
  - id: check_greeting
    function: langswarm.core.utils.workflows.functions.external_function
    args:
      module_path: "/workspace/workflow_helpers.py"   # or wherever your file lives
      func_name: "is_simple_greeting"
      args:
        - ${context.user_input}                       # positional args
      kwargs: {}                                      # if you need named args
    output:
      to: respond

-
When that step runs, it will:

Load and execute workflow_helpers.py

Pull out is_simple_greeting

Call it with positional args drawn from your workflow context

You can now call any function in any file, without having to install it as a package.
"""
def external_function(
    module_path: str,
    func_name: str,
    args: Dict[str, Any] = None,
    kwargs: Dict[str, Any] = None,
    **extra
) -> Any:
    """
    Dynamically load a .py file and call a function inside it.

    • module_path: absolute or relative path to your .py file  
    • func_name:   the name of the function inside that file  
    • args:        a dict of positional args (will be expanded)  
    • kwargs:      a dict of keyword args  
    • extra:       ignored (for future extensibility)
    """
    args   = args   or {}
    kwargs = kwargs or {}

    # 1) Load the module from the given path
    spec = importlib.util.spec_from_file_location("__external__", module_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 2) Grab the function and call it
    func = getattr(mod, func_name)
    return func(*args, **kwargs)


def health_check(url: str, timeout: int = 5) -> bool:
    """Ping the given URL; return True if HTTP < 400."""
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 400
    except Exception:
        return False


# Step to await all needed intput before continuing the workflow.
def await_all_ready(steps: list, context: dict, **kwargs):
    if all(step in context["step_outputs"] for step in steps):
        return "ready"
    else:
        print("Fan-in not ready — requeuing for later")
        return "__NOT_READY__" 


def split_by_agent_prefix(
    text: str,
    prefix_map: Dict[str, str],
    fallback: bool = True
) -> Dict[str, str]:
    """
    Splits `text` into chunks based on agent‑prefix markers, allowing
    for case‑insensitive prefixes and either “:”, “-” or whitespace separators.
    
    Args:
      text: the full block, e.g.
        "Fetcher - do X. parser: do Y. Saver do Z."
      prefix_map: maps your step‑ids to just the *names* of the agents:
        {
          "fetch": "Fetcher",
          "parse": "Parser",
          "save":  "Saver",
        }
      fallback: if True, any key that ends up *without* its own chunk
        will receive the ENTIRE original `text`.

    Returns:
      A dict { step_id → corresponding chunk }.
    """
    # build a named‐group regex that matches each prefix name,
    # e.g.  (?P<fetch>(?i)\bFetcher\b\s*(?:[:\-]\s*|\s+))
    parts = []
    for step_id, name in prefix_map.items():
        esc = re.escape(name.strip())
        # allow word‑boundary, then “:”, “-” or just whitespace
        pat = rf'(?P<{step_id}>(?i)\b{esc}\b\s*(?:[:\-]\s*|\s+))'
        parts.append(pat)
    splitter = re.compile('|'.join(parts))

    # find all boundaries
    segments: Dict[str, str] = {}
    last_end = 0
    last_key = None

    for m in splitter.finditer(text):
        key = m.lastgroup
        start, end = m.span()
        # whatever came *after* the previous prefix belongs to that key
        if last_key is not None:
            segments[last_key] = segments.get(last_key, '') + text[last_end:start].strip()
        last_key = key
        last_end = end

    # final tail
    if last_key is not None:
        segments[last_key] = segments.get(last_key, '') + text[last_end:].strip()

    # cleanup: strip and drop truly empty
    for k in list(segments):
        segments[k] = segments[k].strip()
        if not segments[k]:
            del segments[k]

    # fallback: any key never seen gets the whole text
    if fallback:
        for k in prefix_map:
            if k not in segments:
                segments[k] = text.strip()

    return segments


def mcp_fetch_schema(
    mcp_url: str,
    *,
    mode: Optional[str] = None,
    stdio_cmd: Optional[str] = None,
    env_vars: Optional[Dict[str, str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Fetch the schema from a MCP tool.  Supports both HTTP and stdio modes.
    • HTTP:   GET {mcp_url.rstrip('/')}/schema
    • stdio:  spin up container, run “<stdio_cmd> schema” over stdio, tear down.
    """
    print("kwargs", kwargs)
    
    # 🔧 Check for local:// URLs first
    if mcp_url.startswith("local://"):
        tool_name = mcp_url.split("://", 1)[1]
        from langswarm.mcp.server_base import BaseMCPToolServer
        local_server = BaseMCPToolServer.get_local_server(tool_name)
        
        if local_server:
            print(f"🔧 Local schema fetch: {tool_name}")
            return local_server.get_schema()
        else:
            raise ValueError(f"Local server '{tool_name}' not found")
    
    tool_deployer = kwargs.get("context", {}).get("tool_deployer")
    previous_output = kwargs.get("context", {}).get("previous_output")
    
    # ✏️ detect stdio mode automatically if mode param or url startswith "stdio://"
    is_stdio = (mode == "stdio") or mcp_url.startswith("stdio://")

    if is_stdio:
        # ✏️ build JSON-RPC payload for "schema" method
        rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params":{}}
        payload = json.dumps(rpc)

        # ✏️ pull tool_id out of the URL (e.g. "stdio://github_mcp" → "github_mcp")
        tool_id = mcp_url.split("://", 1)[1]
        container_name = f"{tool_id}-schema-call"

        # ✨ invoke your deployer to spin up, send payload, tear down, grab response
        resp_text = tool_deployer._deploy_locally_via_docker(
            image=tool_deployer.tools[tool_id].image,
            name=container_name,
            env_vars=env_vars or tool_deployer.tools[tool_id].env,
            mode="stdio",
            payload=payload,
        )
        
        return find_tool_by_name(resp_text['parsed'], previous_output) or resp_text['parsed']
    
    # ────────── fallback to HTTP ─────────────────
    schema_url = mcp_url.rstrip("/") + "/schema"
    response = requests.get(schema_url)
    response.raise_for_status()
    return response.json()


def mcp_call(
    mcp_url: str,
    payload: Dict[str, Any],
    *,
    headers: Optional[Dict[str, str]] = None,
    mode: Optional[str] = None,
    stdio_cmd: Optional[str] = None,
    env_vars: Optional[Dict[str, str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Call an MCP tool endpoint.
    • HTTP:   POST mcp_url  (json=payload)
    • stdio:  spin up container, send JSON-RPC over stdio, tear down.
    """
    print("kwargs", kwargs)
    
    # 🔧 Check for local:// URLs first
    if mcp_url.startswith("local://"):
        tool_name = mcp_url.split("://", 1)[1]
        from langswarm.mcp.server_base import BaseMCPToolServer
        local_server = BaseMCPToolServer.get_local_server(tool_name)
        
        if local_server:
            print(f"🔧 Local call: {tool_name}")
            
            # Extract task name and parameters from payload
            if "method" in payload and payload["method"] == "tools/call":
                # JSON-RPC format
                params = payload.get("params", {})
                task_name = params.get("name")
                task_args = params.get("arguments", {})
            elif "name" in payload:
                # Direct format
                task_name = payload["name"]
                task_args = payload.get("arguments", payload.get("args", {}))
            else:
                raise ValueError("Invalid payload format")
            
            # Call the task directly
            result = local_server.call_task(task_name, task_args)
            print(f"✅ Local call result keys: {list(result.keys())}")
            return result
        else:
            raise ValueError(f"Local server '{tool_name}' not found")
    
    tool_deployer = kwargs.get("context", {}).get("tool_deployer")
    is_stdio = (mode == "stdio") or mcp_url.startswith("stdio://")

    if is_stdio:
        # ✏️ same pattern: wrap payload in JSON-RPC if not already
        rpc = payload.copy()
        if "jsonrpc" not in rpc:
            rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": rpc.get("params", {})} # rpc.get("method")
        data = json.dumps(rpc)

        tool_id = mcp_url.split("://", 1)[1]
        container_name = f"{tool_id}-call"

        resp_text = tool_deployer._deploy_locally_via_docker(
            image=tool_deployer.tools[tool_id].image,
            name=container_name,
            env_vars=env_vars or tool_deployer.tools[tool_id].env,
            mode="stdio",
            payload=data,
        )
        print("resp_text", resp_text)
        return resp_text['parsed']
    
    # Enhanced HTTP error handling for remote MCP tools
    try:
        response = requests.post(mcp_url, json=payload, headers=headers, **kwargs)
        
        # Handle specific HTTP status codes
        if response.status_code == 401:
            return {
                "error": {
                    "message": "Authentication failed - check API key or JWT token",
                    "code": 401,
                    "url": mcp_url
                }
            }
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return {
                    "error": {
                        "message": f"Bad request: {error_data.get('error', {}).get('message', response.text)}",
                        "code": 400,
                        "url": mcp_url,
                        "details": error_data
                    }
                }
            except:
                return {
                    "error": {
                        "message": f"Bad request: {response.text}",
                        "code": 400,
                        "url": mcp_url
                    }
                }
        elif response.status_code >= 500:
            return {
                "error": {
                    "message": f"Server error {response.status_code}: {response.text}",
                    "code": response.status_code,
                    "url": mcp_url,
                    "retryable": True
                }
            }
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        return {
            "error": {
                "message": f"Request timeout - server did not respond within timeout period",
                "code": "TIMEOUT",
                "url": mcp_url,
                "retryable": True
            }
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "error": {
                "message": f"Connection error: {str(e)}",
                "code": "CONNECTION_ERROR", 
                "url": mcp_url,
                "retryable": True
            }
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": {
                "message": f"Request failed: {str(e)}",
                "code": "REQUEST_ERROR",
                "url": mcp_url
            }
        }
    except json.JSONDecodeError:
        return {
            "error": {
                "message": f"Invalid JSON response from server",
                "code": "INVALID_JSON",
                "url": mcp_url,
                "response_text": response.text[:500] if 'response' in locals() else None
            }
        }


def find_tool_by_name(response: Dict[str, Any], tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Given a JSON-RPC response from `tools/list` and a tool_name,
    return the dict for that tool, or None if not present.
    """
    # drill into the list of tools
    tools = response.get("result", {}).get("tools", [])
    for tool in tools:
        if tool.get("name") == tool_name:
            return tool
    return None
