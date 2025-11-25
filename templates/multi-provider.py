#!/usr/bin/env python3
"""
Multi-Provider Template
Demonstrates using multiple AI providers for different tasks.
Setup: pip install langswarm openai anthropic google-generativeai
       export OPENAI_API_KEY='your-key'
       export ANTHROPIC_API_KEY='your-key'
       export GOOGLE_API_KEY='your-key'
"""
import asyncio
from langswarm.core.agents import AgentBuilder

async def main():
    # OpenAI GPT-4 for analytical tasks
    analyst = await (
        AgentBuilder()
        .name("analyst")
        .openai()
        .model("gpt-4")
        .system_prompt("You are a data analyst. Provide clear, structured analysis.")
        .build()
    )
    
    # Anthropic Claude for creative tasks
    creative = await (
        AgentBuilder()
        .name("creative")
        .anthropic()
        .model("claude-3-5-sonnet-20241022")
        .system_prompt("You are a creative writer. Generate engaging, original content.")
        .build()
    )
    
    # Google Gemini for multimodal tasks
    gemini = await (
        AgentBuilder()
        .name("multimodal")
        .gemini()
        .model("gemini-pro")
        .system_prompt("You are a versatile AI assistant.")
        .build()
    )
    
    # Use each for their strengths
    print("=== Analytical Task (GPT-4) ===")
    analysis = await analyst.chat("Analyze the pros and cons of microservices architecture")
    print(analysis, "\n")
    
    print("=== Creative Task (Claude) ===")
    story = await creative.chat("Write a short story about a robot learning to paint")
    print(story, "\n")
    
    print("=== General Task (Gemini) ===")
    summary = await gemini.chat("Explain quantum computing in simple terms")
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())

