"use strict";(self.webpackChunkdocusaurus_docs=self.webpackChunkdocusaurus_docs||[]).push([[924],{7161:(n,e,a)=>{a.r(e),a.d(e,{assets:()=>l,contentTitle:()=>o,default:()=>d,frontMatter:()=>i,metadata:()=>s,toc:()=>g});const s=JSON.parse('{"id":"getting-started","title":"Getting Started with LangSwarm","description":"Getting Started with LangSwarm","source":"@site/docs/getting-started.md","sourceDirName":".","slug":"/","permalink":"/LangSwarm/","draft":false,"unlisted":false,"tags":[],"version":"current","sidebarPosition":0,"frontMatter":{"id":"getting-started","title":"Getting Started with LangSwarm","slug":"/","sidebar_label":"Getting Started","sidebar_position":0},"sidebar":"defaultSidebar","next":{"title":"Bring Your Own Agent","permalink":"/LangSwarm/bring-your-own-agent"}}');var t=a(4848),r=a(8453);const i={id:"getting-started",title:"Getting Started with LangSwarm",slug:"/",sidebar_label:"Getting Started",sidebar_position:0},o=void 0,l={},g=[{value:"<strong>Getting Started with LangSwarm</strong>",id:"getting-started-with-langswarm",level:3},{value:"<strong>Installation</strong>",id:"installation",level:3},{value:"<strong>Additional Dependencies</strong>",id:"additional-dependencies",level:4},{value:"<strong>Key Features</strong>",id:"key-features",level:3},{value:"<strong>Basic Concepts</strong>",id:"basic-concepts",level:3},{value:"<strong>Agents</strong>",id:"agents",level:4},{value:"<strong>Swarm Classes</strong>",id:"swarm-classes",level:4},{value:"<strong>Agent Creation</strong>",id:"agent-creation",level:4},{value:"<strong>Step 1: Creating Agents in LangSwarm</strong>",id:"step-1-creating-agents-in-langswarm",level:3},{value:"<strong>Creating a LangChain Agent</strong>",id:"creating-a-langchain-agent",level:4},{value:"<strong>Creating a Hugging Face Agent</strong>",id:"creating-a-hugging-face-agent",level:4},{value:"<strong>Creating a Native OpenAI Agent</strong>",id:"creating-a-native-openai-agent",level:4},{value:"<strong>Step 2: Wrapping External Agents</strong>",id:"step-2-wrapping-external-agents",level:3},{value:"<strong>LangChain Example: Including in a Chain</strong>",id:"langchain-example-including-in-a-chain",level:4},{value:"<strong>Hugging Face Example: Custom Pipeline Integration</strong>",id:"hugging-face-example-custom-pipeline-integration",level:4},{value:"<strong>Step 3: Using Swarm Classes</strong>",id:"step-3-using-swarm-classes",level:3},{value:"<strong>Consensus Swarm</strong>",id:"consensus-swarm",level:4},{value:"<strong>Aggregation Swarm</strong>",id:"aggregation-swarm",level:4},{value:"<strong>Documentation &amp; Support</strong>",id:"documentation--support",level:3}];function c(n){const e={a:"a",code:"code",h3:"h3",h4:"h4",hr:"hr",li:"li",ol:"ol",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,r.R)(),...n.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(e.h3,{id:"getting-started-with-langswarm",children:(0,t.jsx)(e.strong,{children:"Getting Started with LangSwarm"})}),"\n",(0,t.jsxs)(e.p,{children:["Welcome to ",(0,t.jsx)(e.strong,{children:"LangSwarm"}),", a Python package for orchestrating and enhancing collaboration among multiple AI agents, including ",(0,t.jsx)(e.strong,{children:"LangChain"}),", ",(0,t.jsx)(e.strong,{children:"Hugging Face"}),", ",(0,t.jsx)(e.strong,{children:"OpenAI"}),", and more. LangSwarm enables seamless integration and provides tools for consensus-building, memory management, multi-agent orchestration, and more."]}),"\n",(0,t.jsx)(e.p,{children:"This guide will help you quickly get started by walking you through installation, creating agents, and using LangSwarm's powerful orchestration tools."}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"installation",children:(0,t.jsx)(e.strong,{children:"Installation"})}),"\n",(0,t.jsx)(e.p,{children:"LangSwarm requires Python 3.8+ and can be installed from PyPI. Use the following command:"}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-bash",children:"pip install langswarm\n"})}),"\n",(0,t.jsx)(e.h4,{id:"additional-dependencies",children:(0,t.jsx)(e.strong,{children:"Additional Dependencies"})}),"\n",(0,t.jsx)(e.p,{children:"Depending on the agents you plan to use, you may need to install additional dependencies:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsxs)(e.p,{children:[(0,t.jsx)(e.strong,{children:"LangChain"}),": Required for LangChain agents and memory management."]}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-bash",children:"pip install langchain\n"})}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsxs)(e.p,{children:[(0,t.jsx)(e.strong,{children:"LangChain-OpenAI"}),": Needed for direct integration with OpenAI models via LangChain."]}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-bash",children:"pip install langchain-openai\n"})}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsxs)(e.p,{children:[(0,t.jsx)(e.strong,{children:"Transformers"}),": Required for Hugging Face models."]}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-bash",children:"pip install transformers\n"})}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsxs)(e.p,{children:[(0,t.jsx)(e.strong,{children:"Optional Dependencies"}),": Other libraries (e.g., Redis) may be required if you use specific memory backends."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"key-features",children:(0,t.jsx)(e.strong,{children:"Key Features"})}),"\n",(0,t.jsxs)(e.ol,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Multi-Agent Orchestration:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Manage multiple agents for collaboration, routing, and decision-making."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Native OpenAI Support:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Directly use OpenAI agents without additional wrappers or dependencies."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Agent Creation:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Use LangSwarm to create and manage agents from LangChain, Hugging Face, and OpenAI seamlessly."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Memory Management:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Support for shared memory across agents or standalone memory for individual agents."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Advanced Consensus and Aggregation Tools:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Validate, combine, and summarize outputs from multiple agents."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Integration with Native Platforms:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Wrap LangChain, Hugging Face, or OpenAI agents and extend their functionality while retaining native platform features."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"basic-concepts",children:(0,t.jsx)(e.strong,{children:"Basic Concepts"})}),"\n",(0,t.jsx)(e.h4,{id:"agents",children:(0,t.jsx)(e.strong,{children:"Agents"})}),"\n",(0,t.jsx)(e.p,{children:"LangSwarm supports three main categories of agents:"}),"\n",(0,t.jsxs)(e.ol,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"LangChain agents"}),": Leverage LangChain's powerful tools, chains, and memory."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Hugging Face models"}),": Use transformers for conversational AI, question answering, or custom tasks."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Native OpenAI agents"}),": Integrate directly with OpenAI's GPT models without wrappers."]}),"\n"]}),"\n",(0,t.jsx)(e.h4,{id:"swarm-classes",children:(0,t.jsx)(e.strong,{children:"Swarm Classes"})}),"\n",(0,t.jsx)(e.p,{children:"LangSwarm provides powerful orchestration tools to manage and extend multi-agent workflows:"}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Consensus"}),": Achieve agreement among multiple agents."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Aggregation"}),": Combine outputs into meaningful summaries."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Branching"}),": Generate diverse outputs for further analysis."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Voting"}),": Use democratic methods to select the best outputs."]}),"\n"]}),"\n",(0,t.jsx)(e.h4,{id:"agent-creation",children:(0,t.jsx)(e.strong,{children:"Agent Creation"})}),"\n",(0,t.jsx)(e.p,{children:"LangSwarm allows you to create agents for LangChain, Hugging Face, and OpenAI directly. These agents work seamlessly with LangSwarm's features and tools."}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"step-1-creating-agents-in-langswarm",children:(0,t.jsx)(e.strong,{children:"Step 1: Creating Agents in LangSwarm"})}),"\n",(0,t.jsx)(e.p,{children:"You can create agents directly using LangSwarm. These agents are fully compatible with LangSwarm's features and tools."}),"\n",(0,t.jsx)(e.h4,{id:"creating-a-langchain-agent",children:(0,t.jsx)(e.strong,{children:"Creating a LangChain Agent"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langswarm.agent import LangChainAgent\nfrom langchain.llms import OpenAI\nfrom langchain.memory import ConversationBufferMemory\n\n# Create a LangChain agent with memory\nmemory = ConversationBufferMemory()\nlangchain_agent = LangChainAgent(llm=OpenAI(), memory=memory)\n\n# Interact with the agent\nresponse = langchain_agent.chat("What is the capital of France?")\nprint(response)\n'})}),"\n",(0,t.jsx)(e.h4,{id:"creating-a-hugging-face-agent",children:(0,t.jsx)(e.strong,{children:"Creating a Hugging Face Agent"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langswarm.agent import HuggingFaceAgent\nfrom transformers import AutoModelForCausalLM, AutoTokenizer\n\n# Load a Hugging Face conversational model\nmodel_name = "microsoft/DialoGPT-medium"\nhuggingface_agent = HuggingFaceAgent(model_name=model_name)\n\n# Interact with the agent\nresponse = huggingface_agent.chat("Tell me about Paris.")\nprint(response)\n'})}),"\n",(0,t.jsx)(e.h4,{id:"creating-a-native-openai-agent",children:(0,t.jsx)(e.strong,{children:"Creating a Native OpenAI Agent"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langswarm.agent import OpenAIAgent\n\n# Create an OpenAI agent\nopenai_agent = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")\n\n# Interact with the agent\nresponse = openai_agent.chat("What is quantum entanglement?")\nprint(response)\n'})}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"step-2-wrapping-external-agents",children:(0,t.jsx)(e.strong,{children:"Step 2: Wrapping External Agents"})}),"\n",(0,t.jsxs)(e.p,{children:["If you're using LangChain, Hugging Face, or OpenAI agents not created in LangSwarm, you can use the ",(0,t.jsx)(e.code,{children:"AgentWrapper"})," to extend their functionality. This allows you to integrate these agents into LangSwarm workflows while retaining native platform features."]}),"\n",(0,t.jsx)(e.h4,{id:"langchain-example-including-in-a-chain",children:(0,t.jsx)(e.strong,{children:"LangChain Example: Including in a Chain"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langchain.chains import LLMChain\nfrom langchain.prompts import PromptTemplate\nfrom langswarm.wrappers import AgentWrapper\nfrom langchain.llms import OpenAI\n\n# Create a LangChain agent\nprompt = PromptTemplate(input_variables=["question"], template="Answer this: {question}")\nchain = LLMChain(llm=OpenAI(), prompt=prompt)\n\n# Wrap the agent\nwrapped_agent = AgentWrapper(agent=chain)\n\n# Use the wrapped agent\nresponse = wrapped_agent.chat("What is the capital of Germany?")\nprint(response)\n'})}),"\n",(0,t.jsx)(e.h4,{id:"hugging-face-example-custom-pipeline-integration",children:(0,t.jsx)(e.strong,{children:"Hugging Face Example: Custom Pipeline Integration"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from transformers import pipeline\nfrom langswarm.wrappers import AgentWrapper\n\n# Load a QA pipeline from Hugging Face\nqa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")\n\n# Wrap the pipeline\nwrapped_agent = AgentWrapper(agent=qa_pipeline)\n\n# Use the wrapped agent\nresponse = wrapped_agent.chat("What is the capital of France?")\nprint(response)\n'})}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"step-3-using-swarm-classes",children:(0,t.jsx)(e.strong,{children:"Step 3: Using Swarm Classes"})}),"\n",(0,t.jsx)(e.h4,{id:"consensus-swarm",children:(0,t.jsx)(e.strong,{children:"Consensus Swarm"})}),"\n",(0,t.jsx)(e.p,{children:"Achieve consensus among multiple agents."}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langswarm.swarm import LLMConsensus\nfrom langswarm.agent import OpenAIAgent\n\n# Define agents\nagent1 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")\nagent2 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5")\n\n# Create a consensus swarm\nconsensus_swarm = LLMConsensus(query="What is the capital of France?", clients=[agent1, agent2])\nresponse = consensus_swarm.run()\nprint("Consensus Response:", response)\n'})}),"\n",(0,t.jsx)(e.h4,{id:"aggregation-swarm",children:(0,t.jsx)(e.strong,{children:"Aggregation Swarm"})}),"\n",(0,t.jsx)(e.p,{children:"Combine outputs from multiple agents."}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'from langswarm.swarm import LLMAggregation\nfrom langswarm.agent import HuggingFaceAgent\n\n# Define agents\nagent1 = HuggingFaceAgent(model_name="facebook/blenderbot-400M-distill")\nagent2 = HuggingFaceAgent(model_name="microsoft/DialoGPT-medium")\n\n# Create an aggregation swarm\naggregation_swarm = LLMAggregation(query="Summarize the causes of World War II.", clients=[agent1, agent2])\nresponse = aggregation_swarm.run()\nprint("Aggregated Response:", response)\n'})}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h3,{id:"documentation--support",children:(0,t.jsx)(e.strong,{children:"Documentation & Support"})}),"\n",(0,t.jsxs)(e.p,{children:["Explore more features and detailed examples in the ",(0,t.jsx)(e.a,{href:"https://github.com/your-repo/langswarm",children:"LangSwarm GitHub Repository"}),". If you encounter issues, join the ",(0,t.jsx)(e.a,{href:"https://github.com/your-repo/langswarm/discussions",children:"Discussions"})," or file an ",(0,t.jsx)(e.a,{href:"https://github.com/your-repo/langswarm/issues",children:"Issue"}),"."]}),"\n",(0,t.jsx)(e.p,{children:"LangSwarm makes orchestrating intelligent workflows across AI agents simple, flexible, and scalable. Dive in and start building smarter AI systems today!"})]})}function d(n={}){const{wrapper:e}={...(0,r.R)(),...n.components};return e?(0,t.jsx)(e,{...n,children:(0,t.jsx)(c,{...n})}):c(n)}},8453:(n,e,a)=>{a.d(e,{R:()=>i,x:()=>o});var s=a(6540);const t={},r=s.createContext(t);function i(n){const e=s.useContext(r);return s.useMemo((function(){return"function"==typeof n?n(e):{...e,...n}}),[e,n])}function o(n){let e;return e=n.disableParentContext?"function"==typeof n.components?n.components(t):n.components||t:i(n.components),s.createElement(r.Provider,{value:e},n.children)}}}]);