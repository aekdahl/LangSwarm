"use strict";(self.webpackChunkdocusaurus_docs=self.webpackChunkdocusaurus_docs||[]).push([[176],{2642:(n,e,s)=>{s.r(e),s.d(e,{assets:()=>a,contentTitle:()=>l,default:()=>d,frontMatter:()=>o,metadata:()=>i,toc:()=>c});const i=JSON.parse('{"id":"Chains/voting-chain","title":"VotingChain","description":"---","source":"@site/docs/Chains/voting-chain.md","sourceDirName":"Chains","slug":"/Chains/voting-chain","permalink":"/LangSwarm/Chains/voting-chain","draft":false,"unlisted":false,"tags":[],"version":"current","sidebarPosition":34,"frontMatter":{"title":"VotingChain","sidebar_position":34},"sidebar":"defaultSidebar","previous":{"title":"RoutingChain","permalink":"/LangSwarm/Chains/routing-chain"},"next":{"title":"AgentFactory","permalink":"/LangSwarm/Features/agent-factory"}}');var t=s(4848),r=s(8453);const o={title:"VotingChain",sidebar_position:34},l="VotingChain",a={},c=[{value:"<strong>Overview</strong>",id:"overview",level:2},{value:"<strong>Purpose</strong>",id:"purpose",level:2},{value:"<strong>Class Definition</strong>",id:"class-definition",level:2},{value:"<strong>Key Components</strong>",id:"key-components",level:2},{value:"<strong>Usage</strong>",id:"usage",level:2},{value:"<strong>Customization</strong>",id:"customization",level:2},{value:"<strong>Use Cases</strong>",id:"use-cases",level:2},{value:"<strong>Comparison with Other Chains</strong>",id:"comparison-with-other-chains",level:2}];function h(n){const e={code:"code",h1:"h1",h2:"h2",header:"header",hr:"hr",li:"li",ol:"ol",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,r.R)(),...n.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(e.header,{children:(0,t.jsx)(e.h1,{id:"votingchain",children:"VotingChain"})}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"overview",children:(0,t.jsx)(e.strong,{children:"Overview"})}),"\n",(0,t.jsxs)(e.p,{children:["The ",(0,t.jsx)(e.code,{children:"VotingChain"})," class is a custom, LangChain-compatible chain designed to facilitate voting-based decision-making among multiple Large Language Model (LLM) agents. It integrates the ",(0,t.jsx)(e.code,{children:"LLMVoting"})," class to aggregate and evaluate responses based on a voting mechanism, ensuring that the output represents the consensus or majority decision of the participating agents."]}),"\n",(0,t.jsx)(e.p,{children:"This chain is ideal for scenarios where democratic decision-making, ranking, or selection of the most popular response is required."}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"purpose",children:(0,t.jsx)(e.strong,{children:"Purpose"})}),"\n",(0,t.jsxs)(e.p,{children:["The primary purpose of the ",(0,t.jsx)(e.code,{children:"VotingChain"})," class is:"]}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Voting-Based Workflows"}),": To collect, compare, and evaluate responses from multiple agents, selecting the most favored result based on voting."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Pipeline Integration"}),": To act as a reusable chain within LangChain workflows, enabling seamless integration with other tools or chains."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Transparency"}),": To provide detailed insights into the voting process, including the group size and all responses."]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"class-definition",children:(0,t.jsx)(e.strong,{children:"Class Definition"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'class VotingChain(Chain):\n    def __init__(self, agents, **kwargs):\n        """\n        Initializes the VotingChain.\n\n        Parameters:\n        - agents (list): List of agents to use in the voting process.\n        - kwargs: Additional parameters for the LLMVoting class.\n        """\n        self.voting = LLMVoting(clients=agents, **kwargs)\n\n    @property\n    def input_keys(self):\n        """Define input keys for the chain."""\n        return ["query"]\n\n    @property\n    def output_keys(self):\n        """Define output keys for the chain."""\n        return ["voting_result", "group_size", "responses"]\n\n    def _call(self, inputs):\n        """\n        Processes the input query and returns the voting result.\n\n        Parameters:\n        - inputs (dict): Dictionary containing the query.\n\n        Returns:\n        - dict: Dictionary containing the voting result, group size, and responses.\n        """\n        query = inputs["query"]\n        result, group_size, responses = self.voting.run()\n        return {\n            "voting_result": result,\n            "group_size": group_size,\n            "responses": responses,\n        }\n'})}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"key-components",children:(0,t.jsx)(e.strong,{children:"Key Components"})}),"\n",(0,t.jsxs)(e.ol,{children:["\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsxs)(e.strong,{children:[(0,t.jsx)(e.code,{children:"__init__"})," Method"]})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Initializes the chain with a list of agents and additional parameters."}),"\n",(0,t.jsxs)(e.li,{children:["Creates an instance of the ",(0,t.jsx)(e.code,{children:"LLMVoting"})," class to handle the voting process."]}),"\n",(0,t.jsxs)(e.li,{children:["Parameters:","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"agents"}),": A list of LLM agents contributing to the voting process."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"kwargs"}),": Optional parameters passed to configure the ",(0,t.jsx)(e.code,{children:"LLMVoting"})," class."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsxs)(e.strong,{children:[(0,t.jsx)(e.code,{children:"input_keys"})," Property"]})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Specifies the input keys required by the chain."}),"\n",(0,t.jsxs)(e.li,{children:["Inputs:","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"query"}),": The user query or task to be resolved through voting."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsxs)(e.strong,{children:[(0,t.jsx)(e.code,{children:"output_keys"})," Property"]})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Specifies the output keys returned by the chain."}),"\n",(0,t.jsxs)(e.li,{children:["Outputs:","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"voting_result"}),": The winning result based on the voting process."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"group_size"}),": The number of agents participating in the voting."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.code,{children:"responses"}),": A list of all responses generated by the agents."]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsxs)(e.strong,{children:[(0,t.jsx)(e.code,{children:"_call"})," Method"]})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Core logic for executing the chain."}),"\n",(0,t.jsxs)(e.li,{children:["Workflow:","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:["Accepts a ",(0,t.jsx)(e.code,{children:"query"})," input."]}),"\n",(0,t.jsxs)(e.li,{children:["Calls the ",(0,t.jsx)(e.code,{children:"run"})," method of ",(0,t.jsx)(e.code,{children:"LLMVoting"})," to execute the voting process."]}),"\n",(0,t.jsx)(e.li,{children:"Returns the voting result, group size, and all responses as a dictionary."}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"usage",children:(0,t.jsx)(e.strong,{children:"Usage"})}),"\n",(0,t.jsxs)(e.ol,{children:["\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsx)(e.strong,{children:"Initialization"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:"from langswarm.swarm.voting import LLMVoting\nfrom mymodule import VotingChain\n\n# Example list of agents (LLM clients)\nagents = [agent1, agent2, agent3]\n\n# Initialize the VotingChain\nchain = VotingChain(agents=agents, param1=value1, param2=value2)\n"})}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsx)(e.strong,{children:"Execution"})}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:'# Input data\ninputs = {\n    "query": "What is the best approach to reduce carbon emissions globally?",\n}\n\n# Get the voting result\nresult = chain(inputs)\nprint("Winning Result:", result["voting_result"])\nprint("Group Size:", result["group_size"])\nprint("All Responses:", result["responses"])\n'})}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:["\n",(0,t.jsx)(e.p,{children:(0,t.jsx)(e.strong,{children:"Integration with LangChain Pipelines"})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:["The ",(0,t.jsx)(e.code,{children:"VotingChain"})," can be integrated into LangChain workflows as a standalone chain or in combination with other chains and tools."]}),"\n"]}),"\n",(0,t.jsx)(e.pre,{children:(0,t.jsx)(e.code,{className:"language-python",children:"from langchain.chains import SequentialChain\n\n# Example pipeline\npipeline = SequentialChain(chains=[chain, another_chain])\npipeline.run(inputs)\n"})}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"customization",children:(0,t.jsx)(e.strong,{children:"Customization"})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Adding Custom Parameters"}),": Pass additional parameters to ",(0,t.jsx)(e.code,{children:"LLMVoting"})," via the ",(0,t.jsx)(e.code,{children:"kwargs"})," argument during initialization."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Extending the Chain"}),": Subclass ",(0,t.jsx)(e.code,{children:"VotingChain"})," to modify or extend functionality, such as customizing the voting mechanism or the way results are presented."]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"use-cases",children:(0,t.jsx)(e.strong,{children:"Use Cases"})}),"\n",(0,t.jsxs)(e.ol,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Decision-Making"}),":","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Use voting among multiple agents to select the best course of action, solution, or opinion."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Consensus Building"}),":","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Identify the most agreed-upon response in group settings."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Ranking and Prioritization"}),":","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Rank responses and highlight the top choice."}),"\n"]}),"\n"]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"Bias Mitigation"}),":","\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsx)(e.li,{children:"Evaluate diverse perspectives from multiple agents and select the most representative result."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsx)(e.h2,{id:"comparison-with-other-chains",children:(0,t.jsx)(e.strong,{children:"Comparison with Other Chains"})}),"\n",(0,t.jsxs)(e.ul,{children:["\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"VotingChain"}),": Uses a democratic voting mechanism to select the best or most popular response."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"BranchingChain"}),": Generates multiple diverse responses without selecting a single winner."]}),"\n",(0,t.jsxs)(e.li,{children:[(0,t.jsx)(e.strong,{children:"AggregationChain"}),": Synthesizes responses into a unified result rather than selecting one."]}),"\n"]}),"\n",(0,t.jsx)(e.hr,{}),"\n",(0,t.jsxs)(e.p,{children:["This documentation provides a comprehensive explanation of the ",(0,t.jsx)(e.code,{children:"VotingChain"})," class, including its purpose, structure, and usage. Let me know if you\u2019d like further clarifications or enhancements!"]})]})}function d(n={}){const{wrapper:e}={...(0,r.R)(),...n.components};return e?(0,t.jsx)(e,{...n,children:(0,t.jsx)(h,{...n})}):h(n)}},8453:(n,e,s)=>{s.d(e,{R:()=>o,x:()=>l});var i=s(6540);const t={},r=i.createContext(t);function o(n){const e=i.useContext(r);return i.useMemo((function(){return"function"==typeof n?n(e):{...e,...n}}),[e,n])}function l(n){let e;return e=n.disableParentContext?"function"==typeof n.components?n.components(t):n.components||t:o(n.components),i.createElement(r.Provider,{value:e},n.children)}}}]);