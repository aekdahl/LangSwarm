# gradio_workflow_visualizer.py
import gradio as gr
import yaml
import networkx as nx
import matplotlib.pyplot as plt


def visualize_workflow(yaml_text):
    workflows = yaml.safe_load(yaml_text)
    G = nx.DiGraph()
    
    main_wf = workflows.get('workflows', {}).get('main_workflow', [])
    for wf in main_wf:
        steps = wf.get('steps', [])
        for step in steps:
            step_id = step['id']
            G.add_node(step_id)
            outputs = step.get('output', {}).get('to', [])
            if isinstance(outputs, str):
                outputs = [outputs]
            for target in outputs:
                if isinstance(target, str):
                    G.add_edge(step_id, target)
                elif isinstance(target, dict) and 'step' in target:
                    G.add_edge(step_id, target['step'])

    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color='lightgreen', font_size=10, font_weight='bold', arrows=True)
    plt.savefig("workflow_graph.png")
    plt.close()
    return "workflow_graph.png"


demo = gr.Interface(
    fn=visualize_workflow,
    inputs=gr.Textbox(lines=20, placeholder="Paste your workflow YAML here..."),
    outputs=gr.Image(type="filepath"),
    title="Workflow Visualizer (Gradio)",
    description="Paste your YAML and visualize the workflow as a graph."
)

demo.launch()
