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
    • stdio:  spin up container, run "<stdio_cmd> schema" over stdio, tear down.
    """
    # Safe logging to avoid circular reference issues in Pydantic objects
    kwargs_keys = list(kwargs.keys()) if isinstance(kwargs, dict) else "non-dict"
    print("mcp_fetch_schema kwargs keys:", kwargs_keys)
    
    # 🔧 Check for local:// URLs first
    if mcp_url.startswith("local://"):
        tool_name = mcp_url.split("://", 1)[1]
        
        # First check if we have tools in the workflow context
        context = kwargs.get("context", {})
        config_loader = context.get("config_loader")
        local_server = None
        
        if config_loader and hasattr(config_loader, 'tools') and tool_name in config_loader.tools:
            local_server = config_loader.tools[tool_name]
            print(f"🔧 Found tool in workflow context for schema: {tool_name}")
        else:
            # Fallback to global server registry
            from langswarm.v1.mcp.server_base import BaseMCPToolServer
            local_server = BaseMCPToolServer.get_local_server(tool_name)
            if local_server:
                print(f"🔧 Found tool in global registry for schema: {tool_name}")
        
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
    # Safe logging to avoid circular reference issues in Pydantic objects
    kwargs_keys = list(kwargs.keys()) if isinstance(kwargs, dict) else "non-dict"
    print("mcp_call kwargs keys:", kwargs_keys)
    
    # 🔧 Check for local:// URLs first
    if mcp_url.startswith("local://"):
        tool_name = mcp_url.split("://", 1)[1]
        
        # First check if we have tools in the workflow context
        context = kwargs.get("context", {})
        config_loader = context.get("config_loader")
        local_server = None
        
        # DEBUG: Add detailed logging
        print(f"🔍 DEBUG mcp_call: tool_name='{tool_name}'")
        print(f"🔍 DEBUG mcp_call: context keys = {list(context.keys()) if context else 'None'}")
        print(f"🔍 DEBUG mcp_call: config_loader = {type(config_loader) if config_loader else 'None'}")
        
        # Handle both dict and list formats for tools
        tool_found = False
        tool_instance = None
        
        if config_loader and hasattr(config_loader, 'tools'):
            print(f"🔍 DEBUG mcp_call: config_loader.tools type = {type(config_loader.tools)}")
            
            if isinstance(config_loader.tools, dict):
                # Tools is a dictionary - check if tool_name is a key
                print(f"🔍 DEBUG mcp_call: tools dict keys = {list(config_loader.tools.keys())}")
                tool_found = tool_name in config_loader.tools
                if tool_found:
                    tool_instance = config_loader.tools[tool_name]
            elif isinstance(config_loader.tools, list):
                # Tools is a list - search for tool by identifier
                print(f"🔍 DEBUG mcp_call: tools list length = {len(config_loader.tools)}")
                for tool in config_loader.tools:
                    if hasattr(tool, 'identifier') and tool.identifier == tool_name:
                        tool_found = True
                        tool_instance = tool
                        break
                print(f"🔍 DEBUG mcp_call: tool identifiers = {[getattr(t, 'identifier', 'No ID') for t in config_loader.tools]}")
            
            print(f"🔍 DEBUG mcp_call: tool '{tool_name}' found = {tool_found}")
        
        if tool_found and tool_instance:
            print(f"🔧 Found tool in workflow context: {tool_name}")
            
            # Check if tool has a server - use server if available, otherwise use tool directly
            if hasattr(tool_instance, 'server') and tool_instance.server:
                local_server = tool_instance.server
                print(f"🔧 Using tool's MCP server: {tool_instance.server.name}")
                
                # CRITICAL FIX: Ensure server has tool's config for workflow calls
                if hasattr(tool_instance, 'default_config'):
                    if not hasattr(local_server, 'tool_config') or local_server.tool_config is None:
                        print(f"🔧 Applying tool config to server for workflow call")
                        # Create a safe copy to avoid circular references
                        if isinstance(tool_instance.default_config, dict):
                            config_copy = tool_instance.default_config.copy()
                        else:
                            # For non-dict configs, convert to dict to break any circular refs
                            try:
                                config_copy = dict(tool_instance.default_config)
                            except:
                                config_copy = tool_instance.default_config
                        object.__setattr__(local_server, 'tool_config', config_copy)
                    else:
                        print(f"🔧 Server already has tool_config")
                        
            else:
                local_server = tool_instance
                print(f"🔧 Using tool directly: {type(tool_instance)}")
        else:
            # Fallback to global server registry
            from langswarm.v1.mcp.server_base import BaseMCPToolServer
            local_server = BaseMCPToolServer.get_local_server(tool_name)
            if local_server:
                print(f"🔧 Found tool in global registry: {tool_name}")
        
        if local_server:
            print(f"🔧 Local call: {tool_name}")
            
            # Extract task name and parameters from payload
            if "method" in payload and payload["method"] == "tools/call":
                # JSON-RPC format
                params = payload.get("params", {})
                task_name = params.get("name")
                task_args = params.get("arguments", {})
                
                # Handle case where arguments is a JSON string instead of dict
                if isinstance(task_args, str):
                    try:
                        import json
                        task_args = json.loads(task_args)
                        print(f"🔧 Parsed JSON-RPC string arguments: {task_args}")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"⚠️  Failed to parse JSON-RPC arguments as JSON: {e}")
                        task_args = {}
            elif "name" in payload:
                # Direct format
                task_name = payload["name"]
                task_args = payload.get("arguments", payload.get("args", {}))
                
                # Handle case where arguments is a JSON string instead of dict
                if isinstance(task_args, str):
                    try:
                        import json
                        task_args = json.loads(task_args)
                        print(f"🔧 Parsed JSON string arguments: {task_args}")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"⚠️  Failed to parse arguments as JSON: {e}")
                        # If it's not valid JSON, treat as empty dict
                        task_args = {}
            else:
                raise ValueError("Invalid payload format")
            
            # Handle different tool types
            if hasattr(local_server, 'call_task'):
                # BaseMCPToolServer - use call_task with task name
                result = local_server.call_task(task_name, task_args)
                print(f"✅ BaseMCPToolServer call result keys: {list(result.keys())}")
                return result
            elif hasattr(local_server, 'run_async'):
                # LangChain tool - use run_async with input data
                # For LangChain tools, we need to format the input properly
                input_data = {
                    "method": task_name,
                    "params": task_args
                }
                # Handle async call properly
                import asyncio
                try:
                    # Try to get current event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're in an async context, need to run in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, local_server.run_async(input_data))
                            result = future.result()
                    else:
                        # No running loop, can use asyncio.run directly
                        result = asyncio.run(local_server.run_async(input_data))
                except RuntimeError:
                    # No event loop, create new one
                    result = asyncio.run(local_server.run_async(input_data))
                
                print(f"✅ LangChain tool async call result: {type(result)}")
                # Ensure result is a dict
                if isinstance(result, dict):
                    return result
                else:
                    return {"result": result, "success": True}
            elif hasattr(local_server, 'run'):
                # LangChain tool - use synchronous run method
                input_data = {
                    "method": task_name,
                    "params": task_args
                }
                result = local_server.run(input_data)
                print(f"✅ LangChain tool sync call result: {type(result)}")
                # Ensure result is a dict
                if isinstance(result, dict):
                    return result
                else:
                    return {"result": result, "success": True}
            else:
                raise ValueError(f"Tool '{tool_name}' doesn't have call_task, run, or run_async method")
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


def format_as_json(data, **kwargs) -> str:
    """
    Simple wrapper around LangSwarm's to_json() utility with fallback regex extraction.
    
    Args:
        data: Input data - can be string, dict, list, or any JSON-serializable type
        
    Returns:
        Valid JSON string or empty object if conversion fails
    """
    import json
    import re
    from langswarm.v1.core.utils.subutilities.formatting import Formatting
    
    # If data is already a dict/list/etc, serialize it to JSON
    if isinstance(data, (dict, list, int, float, bool)) or data is None:
        try:
            return json.dumps(data)
        except (TypeError, ValueError):
            return "{}"
    
    # Convert to string if not already
    data_str = str(data).strip()
    
    formatter = Formatting()
    
    # Try direct JSON validation first
    if formatter.is_valid_json(data_str):
        return data_str
    
    # Use the built-in to_json utility
    success, result = formatter.to_json(
        data=data_str,
        instructions="Extract and return only the JSON object from the text.",
        requirements="Output only valid JSON without explanations or markdown."
    )
    
    if success:
        return result
    
    # Fallback: Manual JSON extraction when ls_json_parser agent isn't available
    # Remove markdown code fences
    cleaned = re.sub(r'```(?:json)?\s*', '', data_str)
    cleaned = re.sub(r'```\s*', '', cleaned)
    
    # Look for JSON object patterns
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Basic JSON object
        r'\{.*?\}',  # Simpler pattern
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, cleaned, re.DOTALL)
        for match in matches:
            try:
                # Validate the extracted JSON
                json.loads(match)
                return match.strip()
            except:
                continue
    
    # If no JSON found, try to extract key-value patterns and construct JSON
    # Look for common parameter patterns in agent responses
    param_patterns = [
        r'query["\']?\s*[:=]\s*["\']([^"\']+)["\']',  # query: "value" or query = "value"
        r'limit["\']?\s*[:=]\s*(\d+)',  # limit: 10
        r'similarity_threshold["\']?\s*[:=]\s*([\d.]+)',  # similarity_threshold: 0.7
    ]
    
    extracted_params = {}
    
    # Extract query parameter
    query_match = re.search(r'(?:search|query|find).*?["\']([^"\']+)["\']', data_str, re.IGNORECASE)
    if query_match:
        extracted_params["query"] = query_match.group(1)
    
    # Extract limit if mentioned
    limit_match = re.search(r'limit["\']?\s*[:=]?\s*(\d+)', data_str, re.IGNORECASE)
    if limit_match:
        extracted_params["limit"] = int(limit_match.group(1))
    else:
        # Default limit
        extracted_params["limit"] = 10
    
    # Extract similarity threshold if mentioned
    threshold_match = re.search(r'threshold["\']?\s*[:=]?\s*([\d.]+)', data_str, re.IGNORECASE)
    if threshold_match:
        extracted_params["similarity_threshold"] = float(threshold_match.group(1))
    
    # Return constructed JSON if we found parameters
    if extracted_params:
        return json.dumps(extracted_params)
    
    # Final fallback - empty object
    return "{}"
