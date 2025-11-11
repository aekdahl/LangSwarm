"""
Automatic compatibility patches for LangSwarm V1

These patches are automatically applied when langswarm.v1 is imported.

Fixes:
1. LangChain API compatibility (.invoke() vs .run())
2. UTF-8 encoding corruption (Swedish characters and all international text)
"""

import sys
import logging

logger = logging.getLogger(__name__)

# Track if patches have been applied
_PATCHES_APPLIED = False


def patch_agent_wrapper_call_agent():
    """
    Patch AgentWrapper._call_agent for modern LangChain compatibility.
    
    Fixes: 'ChatOpenAI' object has no attribute 'run'
    Solution: Try .invoke() first (modern API), fall back to .run() (legacy)
    """
    try:
        from .core.wrappers.generic import AgentWrapper
    except ImportError as e:
        # Can't import AgentWrapper - may be due to missing dependencies
        # This is OK - patches will be applied when actually needed
        logger.debug(f"Cannot import AgentWrapper (will retry later): {e}")
        return False
    
    # Store original method
    original_call_agent = AgentWrapper._call_agent
    
    def patched_call_agent(self, q, erase_query=False, remove_linebreaks=False):
        """Patched version supporting both .invoke() and .run()"""
        if q:
            self.add_message(q, role="user", remove_linebreaks=remove_linebreaks)
            self.log_event(f"Query sent to agent {self.name}: {q}", "info")
            
        try:
            if self._is_langchain_agent(self.agent):
                if hasattr(self.agent, "memory") and self.agent.memory:
                    self._report_estimated_usage(q)
                    
                    # PATCH: Modern API first, legacy fallback
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
                            f"Agent {type(self.agent).__name__} has neither 'run' nor 'invoke'"
                        )
                else:
                    if callable(self.agent):
                        messages = []
                        if self.system_prompt:
                            try:
                                from langchain.schema import SystemMessage
                                messages.append(SystemMessage(content=self.system_prompt))
                            except ImportError:
                                try:
                                    from langchain_core.messages import SystemMessage
                                    messages.append(SystemMessage(content=self.system_prompt))
                                except ImportError:
                                    pass
                        
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
                            try:
                                from langchain.schema import HumanMessage
                            except ImportError:
                                from langchain_core.messages import HumanMessage
                            messages.append(HumanMessage(content=q))
                        
                        agent_to_invoke = self.agent
                        
                        if messages:
                            self._report_estimated_usage(messages)
                            response = agent_to_invoke.invoke(messages)
                        else:
                            self._report_estimated_usage(q)
                            response = agent_to_invoke.invoke(q)
                    else:
                        context = " ".join([msg["content"] for msg in self.in_memory]) if self.in_memory else q
                        self._report_estimated_usage(context)
                        
                        # PATCH: Modern API first, legacy fallback
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
                                f"Agent {type(self.agent).__name__} has neither 'run' nor 'invoke'"
                            )
            else:
                # Non-LangChain agents use original implementation
                return original_call_agent(self, q, erase_query, remove_linebreaks)

            # Rest of method from original
            response = self._parse_response(response)
            self.log_event(f"Agent {self.name} response: {response}", "info")
            self._report_estimated_usage(response, price_key="ppm_out")
            
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

    AgentWrapper._call_agent = patched_call_agent
    logger.info("✅ Patched AgentWrapper._call_agent for LangChain compatibility")
    return True


def patch_agent_wrapper_parse_response():
    """
    Patch AgentWrapper._parse_response for UTF-8 encoding fixes.
    
    Fixes: Swedish characters corrupted to hex (ö→f6, ä→e4, å→e5)
    Solution: Proper UTF-8 decoding + auto-repair of corruption patterns
    """
    try:
        from .core.wrappers.generic import AgentWrapper
    except ImportError as e:
        # Can't import AgentWrapper - may be due to missing dependencies
        # This is OK - patches will be applied when actually needed
        logger.debug(f"Cannot import AgentWrapper (will retry later): {e}")
        return False
    
    original_parse_response = AgentWrapper._parse_response
    
    def patched_parse_response(self, response):
        """Patched version with proper UTF-8 handling"""
        if hasattr(response, "content"):
            result = response.content
        elif isinstance(response, dict):
            result = response.get("generated_text", "")
        else:
            result = response
        
        # PATCH: Proper UTF-8 decoding
        if isinstance(result, bytes):
            try:
                result = result.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 decode failed for {self.name}, trying latin-1")
                result = result.decode('latin-1')
        elif not isinstance(result, str):
            result = str(result)
        
        # PATCH: Detect and fix hex corruption
        if isinstance(result, str) and self._looks_like_hex_corruption(result):
            logger.warning(f"Detected hex corruption in {self.name}, repairing")
            result = self._fix_hex_corruption(result)
        
        # Truncation logic from original
        if len(result) > self.max_response_length:
            warning_msg = f"RESPONSE TRUNCATED: Agent '{self.name}' generated {len(result)} chars"
            print(f"⚠️ {warning_msg}")
            self.log_event(warning_msg, "warning")
            result = result[:self.max_response_length] + "\n\n[TRUNCATED]"
        
        return result
    
    def looks_like_hex_corruption(self, text):
        """Check for hex corruption patterns (ö→f6, ä→e4, å→e5)"""
        import re
        pattern = r'[a-zA-Z][0-9a-f]{2}[a-zA-Z]'
        matches = re.findall(pattern, text)
        suspicious = ['f6', 'e4', 'e5', 'fc', 'dc', 'c4', 'c5', 'd6']
        return any(h in m.lower() for m in matches for h in suspicious)
    
    def fix_hex_corruption(self, text):
        """Repair hex-corrupted UTF-8 characters"""
        import re
        hex_to_char = {
            'f6': 'ö', 'e4': 'ä', 'e5': 'å',
            'c4': 'Ä', 'c5': 'Å', 'd6': 'Ö',
            'fc': 'ü', 'dc': 'Ü', 'c6': 'Æ'
        }
        for hex_code, char in hex_to_char.items():
            pattern = r'([a-zA-Z])' + hex_code + r'([a-zA-Z])'
            text = re.sub(pattern, r'\1' + char + r'\2', text, flags=re.IGNORECASE)
        return text
    
    # Add helper methods to class
    AgentWrapper._looks_like_hex_corruption = looks_like_hex_corruption
    AgentWrapper._fix_hex_corruption = fix_hex_corruption
    AgentWrapper._parse_response = patched_parse_response
    
    logger.info("✅ Patched AgentWrapper._parse_response for UTF-8 encoding")
    return True


def apply_all():
    """
    Apply all V1 compatibility patches.
    
    Safe to call multiple times - patches only apply once.
    Call this before using AgentWrapper if you want to ensure patches are applied.
    """
    global _PATCHES_APPLIED
    
    if _PATCHES_APPLIED:
        return True
    
    logger.info("Applying LangSwarm V1 compatibility patches...")
    
    success = True
    if not patch_agent_wrapper_call_agent():
        success = False
    
    if not patch_agent_wrapper_parse_response():
        success = False
    
    if success:
        logger.info("✅ All V1 patches applied successfully")
        _PATCHES_APPLIED = True
    else:
        # This might be OK - patches will retry when AgentWrapper is actually imported
        logger.debug("Patches not applied yet (will retry when AgentWrapper is used)")
    
    return success


def is_applied():
    """Check if patches have been applied"""
    return _PATCHES_APPLIED

