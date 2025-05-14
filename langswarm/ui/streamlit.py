import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from langswarm.core.config import WorkflowExecutor, LangSwarmConfigLoader

# ───────────────────────────────────────────────
# Existing Visualizer (Unchanged)
# ───────────────────────────────────────────────

class StreamlitWorkflowVisualizer:
    def __init__(self, workflow_config):
        self.workflow_config = workflow_config
        self.graph = self.build_graph()

    def build_graph(self):
        G = nx.DiGraph()
        steps = self.workflow_config.get('steps', [])
        for step in steps:
            G.add_node(step['id'])
            outputs = step.get('output', {}).get('to', [])
            if isinstance(outputs, str):
                outputs = [outputs]
            for target in outputs:
                if isinstance(target, str):
                    G.add_edge(step['id'], target)
        return G

    def display(self):
        st.title("Workflow Graph Visualization")
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_color='lightgreen', node_size=2000, font_size=10, ax=ax)
        st.pyplot(fig)

# ───────────────────────────────────────────────
# New Executable UI
# ───────────────────────────────────────────────

class StreamlitWorkflowUI:
    def __init__(self, workflow_config, loader: LangSwarmConfigLoader):
        self.workflow_config = workflow_config
        self.loader = loader
        self.executor = WorkflowExecutor(
            workflows=loader.config_data.get("workflows", {}),
            agents=loader.agents,
            tools_metadata=loader.tools_metadata
        )
        self.visualizer = StreamlitWorkflowVisualizer(workflow_config)

    def run(self):
        st.title("LangSwarm Workflow UI")
        self.visualizer.display()

        st.markdown("### User Input")
        user_input = st.text_input("Enter a task or question:")

        if st.button("Run Workflow"):
            result = self.executor.run_workflow(self.workflow_config["id"], user_input)
            st.success("Workflow completed.")
            st.markdown("### Output")
            st.code(result)
