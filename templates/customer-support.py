#!/usr/bin/env python3
"""
Customer Support System Template
Multi-agent system with intelligent routing for customer inquiries.
Setup: pip install langswarm openai && export OPENAI_API_KEY='your-key'
"""
import asyncio
from langswarm import create_agent

async def main():
    # Create classifier to route inquiries
    classifier = create_agent(
        name="classifier",
        model="gpt-3.5-turbo",
        system_prompt="""You are a customer inquiry classifier.
        Analyze the customer's question and determine if it's:
        - TECHNICAL: Technical issues, bugs, setup problems
        - BILLING: Payment, invoices, refunds, subscriptions
        - GENERAL: General questions, feedback, other
        
        Respond with just one word: TECHNICAL, BILLING, or GENERAL"""
    )
    
    # Create specialized support agents
    technical_agent = create_agent(
        name="technical_support",
        model="gpt-4",
        system_prompt="""You are a technical support specialist.
        - Troubleshoot technical issues systematically
        - Provide clear step-by-step solutions
        - Ask clarifying questions when needed
        - Be patient and understanding""",
        tools=["filesystem"],  # Can access logs, configs, etc.
        memory=True
    )
    
    billing_agent = create_agent(
        name="billing_support",
        model="gpt-4",
        system_prompt="""You are a billing support specialist.
        - Handle payment and invoice questions
        - Explain charges clearly
        - Process refund requests professionally
        - Maintain customer trust""",
        memory=True
    )
    
    general_agent = create_agent(
        name="general_support",
        model="gpt-3.5-turbo",
        system_prompt="""You are a friendly customer support representative.
        - Answer general questions
        - Provide product information
        - Guide customers to appropriate resources
        - Be helpful and welcoming""",
        memory=True
    )
    
    # Example customer inquiry
    customer_message = "I was charged twice for my subscription this month. Can you help?"
    
    # Classify the inquiry
    category = await classifier.chat(f"Classify this inquiry: {customer_message}")
    category = category.strip().upper()
    print(f"Category: {category}\n")
    
    # Route to appropriate agent
    if "TECHNICAL" in category:
        agent = technical_agent
        agent_name = "Technical Support"
    elif "BILLING" in category:
        agent = billing_agent
        agent_name = "Billing Support"
    else:
        agent = general_agent
        agent_name = "General Support"
    
    # Get response from specialized agent
    print(f"=== {agent_name} ===")
    response = await agent.chat(customer_message)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())

