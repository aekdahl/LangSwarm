# Core Agents API

**Module:** `langswarm.core.agents`

## Overview

LangSwarm V2 Agent System

Modern, simplified agent architecture that replaces the complex mixin-based AgentWrapper
with clean, provider-specific implementations and composition-based design.

Key Features:
- Provider-specific agents (OpenAI, Anthropic, Gemini, etc.)
- Composition over inheritance
- Native implementations (no LangChain/LlamaIndex dependencies)
- V2 error system, middleware, and tool integration
- Smart defaults with builder pattern for advanced configurations
- Full backward compatibility with V1 agent system

Usage:
    from langswarm.core.agents import AgentBuilder, OpenAIAgent, AnthropicAgent
    
    # Simple agent creation
    agent = AgentBuilder().openai().model("gpt-4o").build()
    
    # Advanced configuration
    agent = (AgentBuilder()
             .openai()
             .model("gpt-4o")
             .system_prompt("You are a helpful assistant")
             .tools(["calculator", "web_search"])
             .memory_enabled(True)
             .build())
    
    # Direct provider instantiation
    agent = OpenAIAgent(
        model="gpt-4o",
        api_key="your-key-here"
    )
