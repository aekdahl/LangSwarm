import gradio as gr
import networkx as nx
import matplotlib.pyplot as plt
from langswarm.core.config import WorkflowExecutor, LangSwarmConfigLoader


# ───────────────────────────────────────────────
# Existing Visualizer (Unchanged)
# ───────────────────────────────────────────────

class GradioWorkflowVisualizer:
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

    def plot_graph(self):
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10)
        plt.show()

    def launch(self):
        def visualize():
            self.plot_graph()
            return "Graph rendered"

        iface = gr.Interface(fn=visualize, inputs=[], outputs="text")
        iface.launch()


# ───────────────────────────────────────────────
# New Executable UI
# ───────────────────────────────────────────────

class GradioWorkflowUI:
    def __init__(self, workflow_config, loader: LangSwarmConfigLoader):
        self.workflow_config = workflow_config
        self.loader = loader
        self.executor = WorkflowExecutor(
            workflows=loader.config_data.get("workflows", {}),
            agents=loader.agents,
            tools_metadata=loader.tools_metadata
        )
        self.visualizer = GradioWorkflowVisualizer(workflow_config)

    def launch(self):
        def run_workflow(user_input):
            return self.executor.run_workflow(self.workflow_config["id"], user_input)

        demo = gr.Interface(
            fn=run_workflow,
            inputs=gr.Textbox(lines=2, label="Enter a task or question"),
            outputs=gr.Textbox(label="Workflow Output"),
            title="LangSwarm Workflow Runner",
            description=f"Run workflow: {self.workflow_config.get('id', 'unknown')}"
        )
        demo.launch()
