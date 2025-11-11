"""
LangSwarm V1 Monkey Patch for Modern LangChain Compatibility

This module provides a monkey patch to fix the AttributeError in LangSwarm V1's
internal `ls_json_parser` agent when using modern LangChain (0.3.x+).

ISSUE: V1's AgentWrapper calls `.run()` on LangChain LLMs, which doesn't exist in
       modern LangChain versions.

FIX: This patch adds compatibility to use `.invoke()` first, falling back to `.run()`
     for older LangChain versions.

USAGE:
    # Import this module BEFORE initializing LangSwarm V1
    import langswarm_v1_monkey_patch
    langswarm_v1_monkey_patch.apply()
    
    # Then use LangSwarm V1 as normal
    from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor
    # ... rest of your code
"""

import sys
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def patch_agent_wrapper_call_agent():
    """
    Patch the AgentWrapper._call_agent method to support modern LangChain API.
    
    This modifies the method to try .invoke() first (modern API), then fall back
    to .run() (legacy API) for backward compatibility.
    """
    try:
        # Import the AgentWrapper class
        from archived.v1.core.wrappers.generic import AgentWrapper
    except ImportError as e:
        logger.error(f"Cannot import AgentWrapper from archived V1 code: {e}")
        logger.error("Ensure you have the archived V1 code available")
        return False
    
    # Store the original method
    original_call_agent = AgentWrapper._call_agent
    
    def patched_call_agent(self, q, erase_query=False, remove_linebreaks=False):
        """
        Patched version that supports both modern .invoke() and legacy .run()
        """
        if q:
            self.add_message(q, role="user", remove_linebreaks=remove_linebreaks)
            self.log_event(f"Query sent to agent {self.name}: {q}", "info")
            
        try:
            # Handle different agent types
            if self._is_langchain_agent(self.agent):
                # LangChain agents
                if hasattr(self.agent, "memory") and self.agent.memory:
                    # Memory is already managed by the agent
                    self._report_estimated_usage(q)
                    
                    # PATCH: Try modern API first, fall back to legacy
                    if hasattr(self.agent, "invoke"):
                        try:
                            from langchain.schema import HumanMessage
                        except ImportError:
                            from langchain_core.messages import HumanMessage
                        response = self.agent.invoke([HumanMessage(content=q)])
                    elif hasattr(self.agent, "run"):
                        response = self.agent.run(q)
                    else:
                        raise AttributeError(
                            f"Agent {type(self.agent).__name__} has neither 'run' nor 'invoke' method"
                        )
                else:
                    # No memory, include context manually
                    if callable(self.agent):
                        # For LangChain ChatModels, create proper message list with system prompt
                        messages = []
                        
                        # Add system prompt if available
                        if self.system_prompt:
                            try:
                                from langchain.schema import SystemMessage
                                messages.append(SystemMessage(content=self.system_prompt))
                            except ImportError:
                                try:
                                    from langchain_core.messages import SystemMessage
                                    messages.append(SystemMessage(content=self.system_prompt))
                                except ImportError:
                                    pass  # Fallback to text-based approach
                        
                        # Add conversation history
                        if self.in_memory:
                            try:
                                from langchain.schema import HumanMessage, AIMessage
                            except ImportError:
                                from langchain_core.messages import HumanMessage, AIMessage
                            
                            for msg in self.in_memory:
                                role = msg.get("role", "user")
                                content = msg.get("content", "")
                                if role == "user":
                                    messages.append(HumanMessage(content=content))
                                elif role == "assistant":
                                    messages.append(AIMessage(content=content))
                        else:
                            # Add current query
                            try:
                                from langchain.schema import HumanMessage
                            except ImportError:
                                from langchain_core.messages import HumanMessage
                            messages.append(HumanMessage(content=q))
                        
                        agent_to_invoke = self.agent
                        
                        # Call agent with message list
                        if messages:
                            self._report_estimated_usage(messages)
                            response = agent_to_invoke.invoke(messages)
                        else:
                            # Fallback to text-based call
                            self._report_estimated_usage(q)
                            response = agent_to_invoke.invoke(q)
                    else:
                        context = " ".join([message["content"] for message in self.in_memory]) if self.in_memory else q
                        self._report_estimated_usage(context)
                        
                        # PATCH: Try modern API first, fall back to legacy
                        if hasattr(self.agent, "invoke"):
                            try:
                                from langchain.schema import HumanMessage
                            except ImportError:
                                from langchain_core.messages import HumanMessage
                            response = self.agent.invoke([HumanMessage(content=context)])
                        elif hasattr(self.agent, "run"):
                            response = self.agent.run(context)
                        else:
                            raise AttributeError(
                                f"Agent {type(self.agent).__name__} has neither 'run' nor 'invoke' method"
                            )
            else:
                # For non-LangChain agents, use original implementation
                # (This delegates to the rest of the original method)
                return original_call_agent(self, q, erase_query, remove_linebreaks)

            # Parse and log response
            response = self._parse_response(response)
            self.log_event(f"Agent {self.name} response: {response}", "info")
            
            # Setup cost reporting with outgoing token cost as well.
            self._report_estimated_usage(response, price_key="ppm_out")
            
            # Use current session for conversation storage
            session_id = self.current_session_id or "default_session"
            self._store_conversation(f"{q}", response, session_id)

            if q and erase_query:
                self.remove()
            elif q:
                self.add_message(response, role="assistant", remove_linebreaks=remove_linebreaks)

            return response

        except Exception as e:
            self.log_event(f"Error for agent {self.name}: {e}", "error")
            raise

    # Replace the method
    AgentWrapper._call_agent = patched_call_agent
    
    logger.info("✅ Successfully patched AgentWrapper._call_agent for modern LangChain compatibility")
    return True


def patch_agent_wrapper_parse_response():
    """
    Patch the AgentWrapper._parse_response method to fix UTF-8 encoding issues.
    
    This ensures that bytes objects are properly decoded as UTF-8 instead of
    being converted to hex strings (which causes corruption like "ö" → "f6").
    """
    try:
        from archived.v1.core.wrappers.generic import AgentWrapper
    except ImportError as e:
        logger.error(f"Cannot import AgentWrapper from archived V1 code: {e}")
        return False
    
    # Store the original method
    original_parse_response = AgentWrapper._parse_response
    
    def patched_parse_response(self, response):
        """
        Patched version that properly handles bytes and encoding.
        """
        # Handle different response types
        if hasattr(response, "content"):
            result = response.content
        elif isinstance(response, dict):
            result = response.get("generated_text", "")
        else:
            result = response
        
        # PATCH: Ensure proper UTF-8 decoding for bytes
        if isinstance(result, bytes):
            try:
                result = result.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                logger.warning(f"UTF-8 decode failed for {self.name}, trying latin-1")
                result = result.decode('latin-1')
        elif not isinstance(result, str):
            # For other types, convert to string
            result = str(result)
        
        # PATCH: Fix common hex encoding corruption patterns
        # If we detect hex patterns that look like UTF-8 bytes, try to fix them
        if isinstance(result, str) and self._looks_like_hex_corruption(result):
            logger.warning(f"Detected hex corruption in response from {self.name}, attempting to fix")
            result = self._fix_hex_corruption(result)
        
        # Truncation logic (from original)
        if len(result) > self.max_response_length:
            warning_msg = f"RESPONSE TRUNCATED: Agent '{self.name}' generated {len(result)} characters, truncating to {self.max_response_length}"
            print(f"⚠️ {warning_msg}")
            self.log_event(warning_msg, "warning")
            result = result[:self.max_response_length] + "\n\n[RESPONSE TRUNCATED - EXCEEDED MAXIMUM LENGTH]"
        
        return result
    
    def looks_like_hex_corruption(self, text):
        """
        Check if text contains hex corruption patterns.
        Swedish characters commonly corrupted:
        - ö (U+00F6) → f6
        - ä (U+00E4) → e4
        - å (U+00E5) → e5
        """
        import re
        # Look for patterns like: letter+hex that match UTF-8 corruption
        pattern = r'[a-zA-Z][0-9a-f]{2}[a-zA-Z]'
        matches = re.findall(pattern, text)
        
        # Check if we have suspicious patterns
        suspicious_hexes = ['f6', 'e4', 'e5', 'fc', 'dc', 'c4', 'c5', 'c6']
        for match in matches:
            if any(hex_code in match.lower() for hex_code in suspicious_hexes):
                return True
        return False
    
    def fix_hex_corruption(self, text):
        """
        Attempt to fix hex-corrupted UTF-8 characters.
        This handles cases where bytes were converted to hex strings instead of decoded.
        """
        import re
        
        # Common Swedish character mappings
        hex_to_char = {
            'f6': 'ö',
            'e4': 'ä', 
            'e5': 'å',
            'c4': 'Ä',
            'c5': 'Å',
            'c6': 'Æ',
            'd6': 'Ö',
            'fc': 'ü',
            'dc': 'Ü'
        }
        
        # Pattern: find hex codes that look like they should be characters
        # Looking for patterns like "sme4rta" (should be "smärta")
        for hex_code, char in hex_to_char.items():
            # Replace hex patterns that appear in the middle of words
            # Pattern: alphanumeric before + hex + alphanumeric after
            pattern = r'([a-zA-Z])' + hex_code + r'([a-zA-Z])'
            replacement = r'\1' + char + r'\2'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    # Add helper methods to AgentWrapper class
    AgentWrapper._looks_like_hex_corruption = looks_like_hex_corruption
    AgentWrapper._fix_hex_corruption = fix_hex_corruption
    
    # Replace the method
    AgentWrapper._parse_response = patched_parse_response
    
    logger.info("✅ Successfully patched AgentWrapper._parse_response for UTF-8 encoding fixes")
    return True


# Track if patches have been applied
_PATCHES_APPLIED = False


def is_applied():
    """
    Check if patches have been applied.
    
    Returns:
        bool: True if patches are already applied
    """
    return _PATCHES_APPLIED


def apply_all_patches():
    """
    Apply all V1 compatibility patches.
    
    Call this function once at the start of your application, BEFORE
    initializing any LangSwarm V1 components.
    
    This is safe to call multiple times - patches are only applied once.
    
    Returns:
        bool: True if all patches applied successfully, False otherwise
    """
    global _PATCHES_APPLIED
    
    if _PATCHES_APPLIED:
        logger.info("Patches already applied, skipping")
        return True
    
    logger.info("Applying LangSwarm V1 compatibility patches...")
    
    success = True
    
    # Patch 1: AgentWrapper._call_agent
    if not patch_agent_wrapper_call_agent():
        logger.error("Failed to patch AgentWrapper._call_agent")
        success = False
    
    # Patch 2: AgentWrapper._parse_response (UTF-8 encoding fixes)
    if not patch_agent_wrapper_parse_response():
        logger.error("Failed to patch AgentWrapper._parse_response")
        success = False
    
    # Future patches can be added here
    # if not patch_something_else():
    #     success = False
    
    if success:
        logger.info("✅ All LangSwarm V1 patches applied successfully")
        _PATCHES_APPLIED = True
    else:
        logger.error("❌ Some patches failed to apply")
    
    return success


# Backward compatibility alias
def apply():
    """Alias for apply_all_patches() for backward compatibility"""
    return apply_all_patches()


# Auto-apply on import (optional, can be disabled)
AUTO_APPLY_ON_IMPORT = False

if AUTO_APPLY_ON_IMPORT:
    apply()


if __name__ == "__main__":
    # Test the patch
    print("Testing LangSwarm V1 monkey patch...")
    if apply():
        print("✅ Patch applied successfully!")
        print("\nNow you can use LangSwarm V1 with modern LangChain.")
        print("\nExample usage:")
        print("  import langswarm_v1_monkey_patch")
        print("  langswarm_v1_monkey_patch.apply()")
        print("  # Then use LangSwarm V1 as normal")
    else:
        print("❌ Patch failed to apply")
        sys.exit(1)

