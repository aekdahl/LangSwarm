# streamlit_workflow_visualizer.py
import streamlit as st
import yaml
import networkx as nx
import matplotlib.pyplot as plt


def load_workflow_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def build_workflow_graph(workflows):
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
    return G


def plot_graph(G):
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold', arrows=True)
    st.pyplot(plt)


st.title("Workflow Visualizer (Streamlit)")

file = st.file_uploader("Upload your workflow YAML file", type=["yaml", "yml"])

if file:
    workflows = yaml.safe_load(file)
    G = build_workflow_graph(workflows)
    st.write("### Workflow Graph")
    plot_graph(G)
