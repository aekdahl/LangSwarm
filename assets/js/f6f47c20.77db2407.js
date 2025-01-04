"use strict";(self.webpackChunkdocusaurus_docs=self.webpackChunkdocusaurus_docs||[]).push([[377],{7753:(e,n,r)=>{r.r(n),r.d(n,{assets:()=>o,contentTitle:()=>l,default:()=>c,frontMatter:()=>a,metadata:()=>s,toc:()=>g});const s=JSON.parse('{"id":"llm-aggregation","title":"Multi-Agent Aggregation","description":"Overview","source":"@site/docs/llm-aggregation.md","sourceDirName":".","slug":"/llm-aggregation","permalink":"/LangSwarm/llm-aggregation","draft":false,"unlisted":false,"tags":[],"version":"current","sidebarPosition":1,"frontMatter":{"title":"Multi-Agent Aggregation","sidebar_position":1},"sidebar":"defaultSidebar","previous":{"title":"Bring Your Own Agent","permalink":"/LangSwarm/bring-your-own-agent"},"next":{"title":"Diverse Output Generation","permalink":"/LangSwarm/llm-branching"}}');var t=r(4848),i=r(8453);const a={title:"Multi-Agent Aggregation",sidebar_position:1},l="Multi-Agent Aggregation",o={},g=[{value:"<strong>Overview</strong>",id:"overview",level:2},{value:"<strong>Key Features</strong>",id:"key-features",level:2},{value:"<strong>API Reference</strong>",id:"api-reference",level:2},{value:"<strong>Class: <code>LLMAggregation</code></strong>",id:"class-llmaggregation",level:3},{value:"<strong>Initialization</strong>",id:"initialization",level:4},{value:"<strong>Methods</strong>",id:"methods",level:3},{value:"<strong><code>run(hb=None)</code></strong>",id:"runhbnone",level:4},{value:"<strong>Examples</strong>",id:"examples",level:2},{value:"<strong>Basic Example</strong>",id:"basic-example",level:3},{value:"<strong>Advanced Example: Custom Helper Bot</strong>",id:"advanced-example-custom-helper-bot",level:3},{value:"<strong>How It Works</strong>",id:"how-it-works",level:2},{value:"<strong>Best Practices</strong>",id:"best-practices",level:2},{value:"<strong>Use Cases</strong>",id:"use-cases",level:2},{value:"<strong>Key Advantages</strong>",id:"key-advantages",level:2},{value:"<strong>Future Enhancements</strong>",id:"future-enhancements",level:2}];function d(e){const n={br:"br",code:"code",h1:"h1",h2:"h2",h3:"h3",h4:"h4",header:"header",hr:"hr",li:"li",ol:"ol",p:"p",pre:"pre",strong:"strong",table:"table",tbody:"tbody",td:"td",th:"th",thead:"thead",tr:"tr",ul:"ul",...(0,i.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.header,{children:(0,t.jsx)(n.h1,{id:"multi-agent-aggregation",children:"Multi-Agent Aggregation"})}),"\n",(0,t.jsx)(n.h2,{id:"overview",children:(0,t.jsx)(n.strong,{children:"Overview"})}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.strong,{children:"LLMAggregation"})," class in LangSwarm is designed to combine and aggregate responses from multiple agents into a unified output. It is ideal for scenarios where insights from multiple agents need to be merged or summarized, such as brainstorming, research synthesis, or collaborative content creation."]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"key-features",children:(0,t.jsx)(n.strong,{children:"Key Features"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Multi-Agent Aggregation"}),":",(0,t.jsx)(n.br,{}),"\n","Collects and combines responses from multiple agents into a single, coherent output."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Flexible Integration"}),":",(0,t.jsx)(n.br,{}),"\n","Works seamlessly with agents from LangChain, Hugging Face, OpenAI, and custom implementations via the ",(0,t.jsx)(n.code,{children:"AgentWrapper"}),"."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Customizable Merging"}),":",(0,t.jsx)(n.br,{}),"\n","Allows for tailored aggregation logic to suit specific workflows or output requirements."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"LangChain-Compatible"}),":",(0,t.jsx)(n.br,{}),"\n","Easily integrates into LangChain pipelines for pre- and post-processing."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"api-reference",children:(0,t.jsx)(n.strong,{children:"API Reference"})}),"\n",(0,t.jsx)(n.h3,{id:"class-llmaggregation",children:(0,t.jsxs)(n.strong,{children:["Class: ",(0,t.jsx)(n.code,{children:"LLMAggregation"})]})}),"\n",(0,t.jsx)(n.p,{children:"Performs aggregation of responses from multiple agents."}),"\n",(0,t.jsx)(n.h4,{id:"initialization",children:(0,t.jsx)(n.strong,{children:"Initialization"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:"LLMAggregation(query, clients, verbose=False)\n"})}),"\n",(0,t.jsxs)(n.table,{children:[(0,t.jsx)(n.thead,{children:(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.th,{children:"Parameter"}),(0,t.jsx)(n.th,{children:"Type"}),(0,t.jsx)(n.th,{children:"Description"})]})}),(0,t.jsxs)(n.tbody,{children:[(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"query"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"str"})}),(0,t.jsx)(n.td,{children:"The input query to be processed by the agents."})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"clients"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"list"})}),(0,t.jsx)(n.td,{children:"A list of agents participating in the aggregation process."})]}),(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"verbose"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"bool"})}),(0,t.jsxs)(n.td,{children:["If ",(0,t.jsx)(n.code,{children:"True"}),", enables detailed logging. Default is ",(0,t.jsx)(n.code,{children:"False"}),"."]})]})]})]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h3,{id:"methods",children:(0,t.jsx)(n.strong,{children:"Methods"})}),"\n",(0,t.jsx)(n.h4,{id:"runhbnone",children:(0,t.jsx)(n.strong,{children:(0,t.jsx)(n.code,{children:"run(hb=None)"})})}),"\n",(0,t.jsx)(n.p,{children:"Executes the aggregation workflow, querying all agents and combining their responses."}),"\n",(0,t.jsxs)(n.table,{children:[(0,t.jsx)(n.thead,{children:(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.th,{children:"Parameter"}),(0,t.jsx)(n.th,{children:"Type"}),(0,t.jsx)(n.th,{children:"Description"})]})}),(0,t.jsx)(n.tbody,{children:(0,t.jsxs)(n.tr,{children:[(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"hb"})}),(0,t.jsx)(n.td,{children:(0,t.jsx)(n.code,{children:"object"})}),(0,t.jsx)(n.td,{children:"(Optional) Helper bot for advanced aggregation logic."})]})})]}),"\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Returns"}),":"]}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.code,{children:"str"}),": The aggregated response."]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"examples",children:(0,t.jsx)(n.strong,{children:"Examples"})}),"\n",(0,t.jsx)(n.h3,{id:"basic-example",children:(0,t.jsx)(n.strong,{children:"Basic Example"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from langswarm.swarm import LLMAggregation\nfrom langswarm.wrappers import AgentWrapper\nfrom langchain.llms import OpenAI\n\n# Step 1: Create and wrap agents\nagent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)\nagent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)\n\n# Step 2: Initialize LLMAggregation with the agents\nquery = "List the main causes of climate change."\naggregation_swarm = LLMAggregation(query=query, clients=[agent1, agent2])\n\n# Step 3: Run the aggregation workflow\naggregated_response = aggregation_swarm.run()\n\n# Display the results\nprint("Aggregated Response:", aggregated_response)\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h3,{id:"advanced-example-custom-helper-bot",children:(0,t.jsx)(n.strong,{children:"Advanced Example: Custom Helper Bot"})}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-python",children:'from langswarm.swarm import LLMAggregation\nfrom langswarm.wrappers import AgentWrapper\nfrom transformers import pipeline\n\n# Step 1: Create and wrap agents\nhuggingface_agent = AgentWrapper(agent=pipeline("text-generation", model="gpt2"), is_conversational=False)\n\nopenai_agent = AgentWrapper(agent="openai_gpt3", is_conversational=True)  # Assuming an OpenAI agent wrapper\n\n# Step 2: Initialize LLMAggregation with a helper bot\nquery = "What are the benefits of renewable energy?"\naggregation_swarm = LLMAggregation(query=query, clients=[huggingface_agent, openai_agent])\n\n# Optional: Use a helper bot for advanced aggregation\nclass HelperBot:\n    def chat(self, q, reset=True, erase_query=True):\n        # Custom aggregation logic\n        return "Merged and aggregated data from all responses."\n\nhelper_bot = HelperBot()\n\n# Step 3: Run the aggregation workflow with the helper bot\naggregated_response = aggregation_swarm.run(hb=helper_bot)\n\n# Display the results\nprint("Aggregated Response:", aggregated_response)\n'})}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"how-it-works",children:(0,t.jsx)(n.strong,{children:"How It Works"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Querying Agents"}),":",(0,t.jsx)(n.br,{}),"\n","All agents in the ",(0,t.jsx)(n.code,{children:"clients"})," list are queried with the provided input."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Combining Responses"}),":",(0,t.jsx)(n.br,{}),"\n","The responses are merged or aggregated based on the aggregation logic (default or custom via helper bot)."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Returning Results"}),":",(0,t.jsx)(n.br,{}),"\n","The aggregated response is returned as a unified output."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"best-practices",children:(0,t.jsx)(n.strong,{children:"Best Practices"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Diverse Agents"}),":",(0,t.jsx)(n.br,{}),"\n","Use a mix of agents to ensure a variety of perspectives and insights in the aggregated output."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Helper Bot"}),":",(0,t.jsx)(n.br,{}),"\n","Leverage a helper bot for advanced or custom aggregation logic tailored to your use case."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Enable Verbose Mode"}),":",(0,t.jsx)(n.br,{}),"\n","Use ",(0,t.jsx)(n.code,{children:"verbose=True"})," during development to understand how responses are aggregated."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"use-cases",children:(0,t.jsx)(n.strong,{children:"Use Cases"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Research Synthesis"}),":",(0,t.jsx)(n.br,{}),"\n","Combine insights from multiple agents to create comprehensive summaries of research topics."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Brainstorming"}),":",(0,t.jsx)(n.br,{}),"\n","Aggregate diverse ideas for creative tasks or problem-solving."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Collaborative Content Creation"}),":",(0,t.jsx)(n.br,{}),"\n","Merge contributions from different agents into a unified piece of content."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"key-advantages",children:(0,t.jsx)(n.strong,{children:"Key Advantages"})}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Collaboration at Scale"}),":",(0,t.jsx)(n.br,{}),"\n","Aggregate responses from multiple agents for well-rounded outputs."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Flexible Integration"}),":",(0,t.jsx)(n.br,{}),"\n","Compatible with various platforms, including LangChain and Hugging Face."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Custom Aggregation"}),":",(0,t.jsx)(n.br,{}),"\n","Tailor aggregation logic to suit specific needs using helper bots."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsx)(n.h2,{id:"future-enhancements",children:(0,t.jsx)(n.strong,{children:"Future Enhancements"})}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Dynamic Aggregation Logic"}),":",(0,t.jsx)(n.br,{}),"\n","Implement intelligent merging algorithms based on content type or query intent."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Improved Summarization"}),":",(0,t.jsx)(n.br,{}),"\n","Enhance the aggregation process with advanced summarization techniques."]}),"\n"]}),"\n",(0,t.jsxs)(n.li,{children:["\n",(0,t.jsxs)(n.p,{children:[(0,t.jsx)(n.strong,{children:"Real-Time Collaboration"}),":",(0,t.jsx)(n.br,{}),"\n","Enable real-time aggregation for live inputs from multiple agents."]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(n.hr,{}),"\n",(0,t.jsxs)(n.p,{children:["The ",(0,t.jsx)(n.strong,{children:"LLMAggregation"})," class is a versatile tool for combining insights from multiple agents. Whether you're brainstorming, synthesizing research, or creating collaborative content, LangSwarm\u2019s aggregation capabilities simplify the process while ensuring high-quality outputs."]})]})}function c(e={}){const{wrapper:n}={...(0,i.R)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(d,{...e})}):d(e)}},8453:(e,n,r)=>{r.d(n,{R:()=>a,x:()=>l});var s=r(6540);const t={},i=s.createContext(t);function a(e){const n=s.useContext(i);return s.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function l(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(t):e.components||t:a(e.components),s.createElement(i.Provider,{value:n},e.children)}}}]);