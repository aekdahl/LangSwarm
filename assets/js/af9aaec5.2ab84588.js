"use strict";(self.webpackChunkdocusaurus_docs=self.webpackChunkdocusaurus_docs||[]).push([[514],{2041:(n,e,s)=>{s.r(e),s.d(e,{assets:()=>o,contentTitle:()=>l,default:()=>d,frontMatter:()=>a,metadata:()=>i,toc:()=>h});const i=JSON.parse('{"id":"Chains/branching-chain","title":"BranchingChain","description":"---","source":"@site/docs/Chains/branching-chain.md","sourceDirName":"Chains","slug":"/Chains/branching-chain","permalink":"/LangSwarm/Chains/branching-chain","draft":false,"unlisted":false,"tags":[],"version":"current","sidebarPosition":31,"frontMatter":{"title":"BranchingChain","sidebar_position":31},"sidebar":"defaultSidebar","previous":{"title":"AggregationChain","permalink":"/LangSwarm/Chains/aggregation-chain"},"next":{"title":"ConsensusChain","permalink":"/LangSwarm/Chains/consensus-chain"}}');var r=s(4848),t=s(8453);const a={title:"BranchingChain",sidebar_position:31},l="BranchingChain",o={},h=[{value:"<strong>Overview</strong>",id:"overview",level:2},{value:"<strong>Purpose</strong>",id:"purpose",level:2},{value:"<strong>Class Definition</strong>",id:"class-definition",level:2},{value:"<strong>Key Components</strong>",id:"key-components",level:2},{value:"<strong>Usage</strong>",id:"usage",level:2},{value:"<strong>Customization</strong>",id:"customization",level:2},{value:"<strong>Use Cases</strong>",id:"use-cases",level:2},{value:"<strong>Comparison with Other Chains</strong>",id:"comparison-with-other-chains",level:2}];function c(n){const e={code:"code",h1:"h1",h2:"h2",header:"header",hr:"hr",li:"li",ol:"ol",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,t.R)(),...n.components};return(0,r.jsxs)(r.Fragment,{children:[(0,r.jsx)(e.header,{children:(0,r.jsx)(e.h1,{id:"branchingchain",children:"BranchingChain"})}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"overview",children:(0,r.jsx)(e.strong,{children:"Overview"})}),"\n",(0,r.jsxs)(e.p,{children:["The ",(0,r.jsx)(e.code,{children:"BranchingChain"})," class is a custom, LangChain-compatible chain designed to facilitate branching workflows by generating multiple responses from a set of Large Language Model (LLM) agents. It leverages the ",(0,r.jsx)(e.code,{children:"LLMBranching"})," class to explore diverse outputs from different agents for a given query."]}),"\n",(0,r.jsx)(e.p,{children:"This chain is particularly useful in scenarios where multiple perspectives or creative variations are required, making it a valuable component in LangChain pipelines."}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"purpose",children:(0,r.jsx)(e.strong,{children:"Purpose"})}),"\n",(0,r.jsxs)(e.p,{children:["The primary purpose of the ",(0,r.jsx)(e.code,{children:"BranchingChain"})," class is:"]}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Generating Multiple Responses"}),": To enable exploration of diverse outputs from multiple LLM agents for a single input query."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Pipeline Integration"}),": To act as a reusable chain within LangChain workflows, allowing integration with other tools or chains."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Flexibility"}),": To allow customization of the branching process through additional parameters."]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"class-definition",children:(0,r.jsx)(e.strong,{children:"Class Definition"})}),"\n",(0,r.jsx)(e.pre,{children:(0,r.jsx)(e.code,{className:"language-python",children:'class BranchingChain(Chain):\n    def __init__(self, agents, **kwargs):\n        """\n        Initializes the BranchingChain.\n\n        Parameters:\n        - agents (list): List of agents to use in the branching process.\n        - kwargs: Additional parameters for the LLMBranching class.\n        """\n        self.branching = LLMBranching(clients=agents, **kwargs)\n\n    @property\n    def input_keys(self):\n        """Define input keys for the chain."""\n        return ["query"]\n\n    @property\n    def output_keys(self):\n        """Define output keys for the chain."""\n        return ["responses"]\n\n    def _call(self, inputs):\n        """\n        Processes the input query and returns a list of responses.\n\n        Parameters:\n        - inputs (dict): Dictionary containing the query.\n\n        Returns:\n        - dict: Dictionary containing the list of responses.\n        """\n        query = inputs["query"]\n        self.branching.query = query\n        responses = self.branching.run()\n        return {"responses": responses}\n'})}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"key-components",children:(0,r.jsx)(e.strong,{children:"Key Components"})}),"\n",(0,r.jsxs)(e.ol,{children:["\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsxs)(e.strong,{children:[(0,r.jsx)(e.code,{children:"__init__"})," Method"]})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Initializes the chain with a list of agents and additional parameters."}),"\n",(0,r.jsxs)(e.li,{children:["Creates an instance of the ",(0,r.jsx)(e.code,{children:"LLMBranching"})," class to handle the branching process."]}),"\n",(0,r.jsxs)(e.li,{children:["Parameters:","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.code,{children:"agents"}),": A list of LLM agents used for branching."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.code,{children:"kwargs"}),": Optional parameters passed to configure the ",(0,r.jsx)(e.code,{children:"LLMBranching"})," class."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsxs)(e.strong,{children:[(0,r.jsx)(e.code,{children:"input_keys"})," Property"]})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Specifies the input keys required by the chain."}),"\n",(0,r.jsxs)(e.li,{children:["Inputs:","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.code,{children:"query"}),": The user query to be processed."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsxs)(e.strong,{children:[(0,r.jsx)(e.code,{children:"output_keys"})," Property"]})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Specifies the output key returned by the chain."}),"\n",(0,r.jsxs)(e.li,{children:["Outputs:","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.code,{children:"responses"}),": A list of responses generated by the branching process."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsxs)(e.strong,{children:[(0,r.jsx)(e.code,{children:"_call"})," Method"]})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Core logic for executing the chain."}),"\n",(0,r.jsxs)(e.li,{children:["Workflow:","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:["Accepts a ",(0,r.jsx)(e.code,{children:"query"})," input."]}),"\n",(0,r.jsxs)(e.li,{children:["Assigns the ",(0,r.jsx)(e.code,{children:"query"})," to the ",(0,r.jsx)(e.code,{children:"LLMBranching"})," instance."]}),"\n",(0,r.jsxs)(e.li,{children:["Calls the ",(0,r.jsx)(e.code,{children:"run"})," method of ",(0,r.jsx)(e.code,{children:"LLMBranching"})," to generate multiple responses."]}),"\n",(0,r.jsx)(e.li,{children:"Returns the responses as a dictionary."}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"usage",children:(0,r.jsx)(e.strong,{children:"Usage"})}),"\n",(0,r.jsxs)(e.ol,{children:["\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsx)(e.strong,{children:"Initialization"})}),"\n",(0,r.jsx)(e.pre,{children:(0,r.jsx)(e.code,{className:"language-python",children:"from langswarm.swarm.branching import LLMBranching\nfrom mymodule import BranchingChain\n\n# Example list of agents (LLM clients)\nagents = [agent1, agent2, agent3]\n\n# Initialize the BranchingChain\nchain = BranchingChain(agents=agents, param1=value1, param2=value2)\n"})}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsx)(e.strong,{children:"Execution"})}),"\n",(0,r.jsx)(e.pre,{children:(0,r.jsx)(e.code,{className:"language-python",children:'# Input data\ninputs = {\n    "query": "Suggest creative business ideas in the tech industry.",\n}\n\n# Get the list of responses\nresult = chain(inputs)\nprint(result["responses"])\n'})}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:["\n",(0,r.jsx)(e.p,{children:(0,r.jsx)(e.strong,{children:"Integration with LangChain Pipelines"})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:["The ",(0,r.jsx)(e.code,{children:"BranchingChain"})," can be integrated into LangChain workflows as a standalone chain or in combination with other chains and tools."]}),"\n"]}),"\n",(0,r.jsx)(e.pre,{children:(0,r.jsx)(e.code,{className:"language-python",children:"from langchain.chains import SequentialChain\n\n# Example pipeline\npipeline = SequentialChain(chains=[chain, another_chain])\npipeline.run(inputs)\n"})}),"\n"]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"customization",children:(0,r.jsx)(e.strong,{children:"Customization"})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Adding Custom Parameters"}),": Pass additional parameters to ",(0,r.jsx)(e.code,{children:"LLMBranching"})," via the ",(0,r.jsx)(e.code,{children:"kwargs"})," argument during initialization."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Extending the Chain"}),": Subclass ",(0,r.jsx)(e.code,{children:"BranchingChain"})," to modify or extend functionality, such as post-processing the responses."]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"use-cases",children:(0,r.jsx)(e.strong,{children:"Use Cases"})}),"\n",(0,r.jsxs)(e.ol,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Creative Ideation"}),":","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Generate multiple creative solutions or ideas for brainstorming."}),"\n"]}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"Exploring Diverse Perspectives"}),":","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Obtain varied viewpoints or responses to open-ended questions."}),"\n"]}),"\n"]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"A/B Testing"}),":","\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsx)(e.li,{children:"Compare different outputs from multiple agents for evaluation or selection."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsx)(e.h2,{id:"comparison-with-other-chains",children:(0,r.jsx)(e.strong,{children:"Comparison with Other Chains"})}),"\n",(0,r.jsxs)(e.ul,{children:["\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"BranchingChain"}),": Generates diverse responses from multiple agents, focusing on exploring possibilities."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"AggregationChain"}),": Synthesizes responses into a single, unified result."]}),"\n",(0,r.jsxs)(e.li,{children:[(0,r.jsx)(e.strong,{children:"ConsensusChain"}),": Builds agreement among agents to determine the most supported response."]}),"\n"]}),"\n",(0,r.jsx)(e.hr,{}),"\n",(0,r.jsxs)(e.p,{children:["This documentation provides a detailed explanation of the purpose, structure, and usage of the ",(0,r.jsx)(e.code,{children:"BranchingChain"})," class. Let me know if you'd like further elaboration or enhancements!"]})]})}function d(n={}){const{wrapper:e}={...(0,t.R)(),...n.components};return e?(0,r.jsx)(e,{...n,children:(0,r.jsx)(c,{...n})}):c(n)}},8453:(n,e,s)=>{s.d(e,{R:()=>a,x:()=>l});var i=s(6540);const r={},t=i.createContext(r);function a(n){const e=i.useContext(t);return i.useMemo((function(){return"function"==typeof n?n(e):{...e,...n}}),[e,n])}function l(n){let e;return e=n.disableParentContext?"function"==typeof n.components?n.components(r):n.components||r:a(n.components),i.createElement(t.Provider,{value:e},n.children)}}}]);