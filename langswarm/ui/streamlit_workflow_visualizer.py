### streamlit_workflow_visualizer.py (Class-based)
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

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
