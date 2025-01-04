"use strict";(self.webpackChunkdocusaurus_docs=self.webpackChunkdocusaurus_docs||[]).push([[922],{2563:(e,n,r)=>{r.r(n),r.d(n,{assets:()=>o,contentTitle:()=>l,default:()=>h,frontMatter:()=>i,metadata:()=>s,toc:()=>d});const s=JSON.parse('{"id":"Features/agent-wrapper","title":"AgentWrapper","description":"Overview","source":"@site/docs/Features/agent-wrapper.md","sourceDirName":"Features","slug":"/Features/agent-wrapper","permalink":"/LangSwarm/Features/agent-wrapper","draft":false,"unlisted":false,"tags":[],"version":"current","sidebarPosition":68,"frontMatter":{"title":"AgentWrapper","sidebar_position":68},"sidebar":"defaultSidebar","previous":{"title":"AgentFactory","permalink":"/LangSwarm/Features/agent-factory"},"next":{"title":"LangSwarmTemplates","permalink":"/LangSwarm/Interface/templates"}}');var t=r(4848),a=r(8453);const i={title:"AgentWrapper",sidebar_position:68},l="AgentWrapper",o={},d=[{value:"<strong>Overview</strong>",id:"overview",level:2},{value:"<strong>Key Features</strong>",id:"key-features",level:2},{value:"<strong>API Reference</strong>",id:"api-reference",level:2},{value:"<strong>Class: <code>AgentWrapper</code></strong>",id:"class-agentwrapper",level:3},{value:"<strong>Initialization</strong>",id:"initialization",level:4},{value:"<strong>Methods</strong>",id:"methods",level:3},{value:"<strong><code>chat(q, reset=False, erase_query=False, remove_linebreaks=False)</code></strong>",id:"chatq-resetfalse-erase_queryfalse-remove_linebreaksfalse",level:4},{value:"<strong><code>__getattr__(name)</code></strong>",id:"__getattr__name",level:4},{value:"<strong>Examples</strong>",id:"examples",level:2},{value:"<strong>Wrapping a LangChain Agent</strong>",id:"wrapping-a-langchain-agent",level:3},{value:"<strong>Wrapping a Hugging Face Model</strong>",id:"wrapping-a-hugging-face-model",level:3},{value:"<strong>Using a Wrapped Agent in a LangSwarm Workflow</strong>",id:"using-a-wrapped-agent-in-a-langswarm-workflow",level:3},{value:"<strong>Advanced Use Cases</strong>",id:"advanced-use-cases",level:2},{value:"<strong>Accessing Native Agent Features</strong>",id:"accessing-native-agent-features",level:3},{value:"<strong>Managing Conversational Context</strong>",id:"managing-conversational-context",level:3},{value:"<strong>Best Practices</strong>",id:"best-practices",level:2},{value:"<strong>Key Advantages</strong>",id:"key-advantages",level:2},{value:"<strong>Future Enhancements</strong>",id:"future-enhancements",level:2}];function c(e){const n={br:"br",code:"code",h1:"h1",h2:"h2",h3:"h3",h4:"h4",header:"header",hr:"hr",li:"li",ol:"ol",p:"p",pre:"pre",strong:"strong",table:"table",tbody:"tbody",td:"td",th:"th",thead:"thead",tr:"tr",ul:"ul",...(0,a.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.header,{children:(0,t.jsx)(n.h1,{id:"agentwrapper",children:(0,t.jsx)(n.strong,{children:"AgentWrapper"})})}),"\n",(0,t.jsx)(n.h2,{id:"overview",children:(0,t.jsx)(n.strong,{children:"Overview"})}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.strong,{children:"AgentWrapper"})," in LangSwarm enables seamless integration of diverse agents (e.g., LangChain, Hugging Face, OpenAI) into LangSwarm workflows. It dynamically adapts agents to make them compatible with LangSwarm\u2019s features such as ",(0,t.jsx)(n.code,{children:"LLMConsensus"}),", ",(0,t.jsx)(n.code,{children:"LLMAggregation"}),", ",(0,t.jsx)(n.code,{children:"LLMBranching"}),", and more."]}),"\n",(0,t.jsxs)(n.p,{children:["With the ",(0,t.jsx)(n.code,{children:"AgentWrapper"}),", you can:"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsx)(n.li,{children:"Add LangSwarm functionality to native LangChain or Hugging Face agents."}),"\n",(0,t.jsx)(n.li,{children:"Manage conversational context and memory."}),"\n",(0,t.jsx)(n.li,{children:"Ensure agents are compatible with LangSwarm\u2019s multi-agent orchestration tools."}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"key-features",children:(0,t.jsx)(n.strong,{children:"Key Features"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.strong,{children:"Dynamic Compatibility"}),": Adapts LangChain, Hugging Face, OpenAI, or custom agents to LangSwarm workflows."]}),"\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.strong,{children:"Conversational Context"}),": Handles history and memory for agents that support conversational queries."]}),"\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.strong,{children:"Simplified API"}),": Provides a unified interface to interact with different types of agents."]}),"\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.strong,{children:"Customizable"}),": Extensible for unsupported agent types or additional features."]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"api-reference",children:(0,t.jsx)(n.strong,{children:"API Reference"})}),"\n",(0,t.jsx)(n.h3,{id:"class-agentwrapper",children:(0,t.jsxs)(n.strong,{children:["Class: ",(0,t.jsx)(n.code,{children:"AgentWrapper"})]})}),"\n",(0,t.jsx)(n.p,{children:"Wraps an agent to make it compatible with LangSwarm workflows."}),"\n",(0,t.jsx)(n.h4,{id:"initialization",children:(0,t.jsx)(n.strong,{children:"Initialization"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:"AgentWrapper(agent, is_conversational=False, **kwargs)\n"})}),"\n",(0,t.jsxs)(n.table,{children:[(0,t.jsx)(n.thead,{children:(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.th,{children:"Parameter"}),(0,t.jsx)(n.th,{children:"Type"}),(0,t.jsx)(n.th,{children:"Description"})]})}),(0,t.jsxs)(n.tbody,{children:[(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"agent"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"object"})}),(0,t.jsx)(n.td,{children:"The agent to be wrapped (LangChain, Hugging Face, OpenAI, or custom)."})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"is_conversational"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"bool"})}),(0,t.jsx)(n.td,{children:"Specifies if the agent supports conversational context."})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"kwargs"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"dict"})}),(0,t.jsx)(n.td,{children:"Additional parameters for LangSwarm compatibility."})]})]})]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h3,{id:"methods",children:(0,t.jsx)(n.strong,{children:"Methods"})}),"\n",(0,t.jsx)(n.h4,{id:"chatq-resetfalse-erase_queryfalse-remove_linebreaksfalse",children:(0,t.jsx)(n.strong,{children:(0,t.jsx)(n.code,{children:"chat(q, reset=False, erase_query=False, remove_linebreaks=False)"})})}),"\n",(0,t.jsx)(n.p,{children:"Processes a query through the wrapped agent."}),"\n",(0,t.jsxs)(n.table,{children:[(0,t.jsx)(n.thead,{children:(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.th,{children:"Parameter"}),(0,t.jsx)(n.th,{children:"Type"}),(0,t.jsx)(n.th,{children:"Description"})]})}),(0,t.jsxs)(n.tbody,{children:[(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"q"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"str"})}),(0,t.jsx)(n.td,{children:"The query to be processed."})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"reset"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"bool"})}),(0,t.jsxs)(n.td,{children:["If ",(0,t.jsx)(n.code,{children:"True"}),", resets the memory before processing the query."]})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"erase_query"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"bool"})}),(0,t.jsxs)(n.td,{children:["If ",(0,t.jsx)(n.code,{children:"True"}),", erases the query after processing."]})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"remove_linebreaks"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"bool"})}),(0,t.jsxs)(n.td,{children:["If ",(0,t.jsx)(n.code,{children:"True"}),", removes line breaks from the query."]})]})]})]}),"\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Returns"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.code,{children:"str"}),": The agent\u2019s response."]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h4,{id:"__getattr__name",children:(0,t.jsx)(n.strong,{children:(0,t.jsx)(n.code,{children:"__getattr__(name)"})})}),"\n",(0,t.jsx)(n.p,{children:"Delegates attribute access to the wrapped agent."}),"\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Usage"}),":",(0,t.jsx)(n.br,{}),"\n","Allows seamless access to the wrapped agent\u2019s native methods and properties."]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"examples",children:(0,t.jsx)(n.strong,{children:"Examples"})}),"\n",(0,t.jsx)(n.h3,{id:"wrapping-a-langchain-agent",children:(0,t.jsx)(n.strong,{children:"Wrapping a LangChain Agent"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from langchain.llms import OpenAI\nfrom langswarm.wrappers import AgentWrapper\n\n# Create a native LangChain agent\nlangchain_agent = OpenAI(model="gpt-4", temperature=0)\n\n# Wrap the agent for LangSwarm compatibility\nwrapped_agent = AgentWrapper(agent=langchain_agent, is_conversational=True)\n\n# Use the wrapped agent in LangSwarm workflows\nresponse = wrapped_agent.chat("What are the main benefits of AI?")\nprint("Response:", response)\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h3,{id:"wrapping-a-hugging-face-model",children:(0,t.jsx)(n.strong,{children:"Wrapping a Hugging Face Model"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from transformers import pipeline\nfrom langswarm.wrappers import AgentWrapper\n\n# Load a Hugging Face QA pipeline\nhuggingface_agent = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")\n\n# Wrap the agent for LangSwarm compatibility\nwrapped_agent = AgentWrapper(agent=huggingface_agent, is_conversational=False)\n\n# Use the wrapped agent in LangSwarm workflows\nresponse = wrapped_agent.chat("What is the capital of France?")\nprint("Response:", response)\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h3,{id:"using-a-wrapped-agent-in-a-langswarm-workflow",children:(0,t.jsx)(n.strong,{children:"Using a Wrapped Agent in a LangSwarm Workflow"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from langswarm.swarm import LLMConsensus\nfrom langswarm.wrappers import AgentWrapper\nfrom langchain.llms import OpenAI\n\n# Create and wrap agents\nagent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)\nagent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)\n\n# Use wrapped agents in a LangSwarm consensus workflow\nconsensus_swarm = LLMConsensus(query="What are the benefits of renewable energy?", clients=[agent1, agent2])\nresponse = consensus_swarm.run()\nprint("Consensus Response:", response)\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"advanced-use-cases",children:(0,t.jsx)(n.strong,{children:"Advanced Use Cases"})}),"\n",(0,t.jsx)(n.h3,{id:"accessing-native-agent-features",children:(0,t.jsx)(n.strong,{children:"Accessing Native Agent Features"})}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.code,{children:"AgentWrapper"})," allows direct access to the wrapped agent\u2019s native methods."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'# Access the wrapped agent\'s native methods\nagent_temperature = wrapped_agent.agent.temperature\nprint("Temperature Setting:", agent_temperature)\n'})}),"\n",(0,t.jsx)(n.h3,{id:"managing-conversational-context",children:(0,t.jsx)(n.strong,{children:"Managing Conversational Context"})}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.code,{children:"AgentWrapper"})," seamlessly manages conversational history for supported agents."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'# Enable conversational context\nconversation_agent = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)\n\n# Send queries and maintain context\nconversation_agent.chat("What is the weather like today?")\nconversation_agent.chat("How about tomorrow?")\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"best-practices",children:(0,t.jsx)(n.strong,{children:"Best Practices"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsxs)(n.strong,{children:["Use ",(0,t.jsx)(n.code,{children:"is_conversational"})," Appropriately"]}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:["Set ",(0,t.jsx)(n.code,{children:"is_conversational=True"})," for agents with memory or conversational context."]}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Delegate Custom Logic"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:["Use ",(0,t.jsx)(n.code,{children:"__getattr__"})," to delegate calls to native agent methods when required."]}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Combine with LangSwarm Tools"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:["Use ",(0,t.jsx)(n.code,{children:"AgentWrapper"})," to ensure agents are compatible with LangSwarm workflows, such as voting, aggregation, or branching."]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"key-advantages",children:(0,t.jsx)(n.strong,{children:"Key Advantages"})}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Seamless Integration"}),":",(0,t.jsx)(n.br,{}),"\n","Enables out-of-the-box compatibility for agents from different platforms."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Unified API"}),":",(0,t.jsx)(n.br,{}),"\n","Simplifies agent interaction, regardless of the underlying framework."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Flexible and Extensible"}),":",(0,t.jsx)(n.br,{}),"\n","Adapts to custom agents or models with minimal effort."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"future-enhancements",children:(0,t.jsx)(n.strong,{children:"Future Enhancements"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Extended Wrapping Support"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsx)(n.li,{children:"Add pre-built compatibility for additional agent types, like Google Gemini."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Automatic Behavior Detection"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsx)(n.li,{children:"Dynamically detect agent capabilities (e.g., memory support, conversational context)."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Enhanced Memory Management"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsx)(n.li,{children:"Integrate shared and cross-agent memory for multi-agent workflows."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.strong,{children:"AgentWrapper"})," is a cornerstone of LangSwarm\u2019s ecosystem, enabling seamless multi-agent collaboration. Whether you're using LangChain, Hugging Face, or OpenAI, the ",(0,t.jsx)(n.code,{children:"AgentWrapper"})," ensures your agents are ready to thrive in LangSwarm workflows."]})]})}function h(e={}){const{wrapper:n}={...(0,a.R)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(c,{...e})}):c(e)}},8453:(e,n,r)=>{r.d(n,{R:()=>i,x:()=>l});var s=r(6540);const t={},a=s.createContext(t);function i(e){const n=s.useContext(a);return s.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function l(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(t):e.components||t:i(e.components),s.createElement(a.Provider,{value:n},e.children)}}}]);