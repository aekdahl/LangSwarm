import os
import subprocess
import yaml
import sys
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor

"""
from langswarm.core.config import LangSwarmConfigLoader
from ui.streamlit_workflow_visualizer import StreamlitWorkflowUI

loader = LangSwarmConfigLoader(".")
workflows, *_ = loader.load()
workflow = workflows.get("main_workflow", [])[0]

app = StreamlitWorkflowUI(workflow, loader)
app.run()
"""

def launch_ui(example_path, ui_type, ui_file):
    if ui_type == "streamlit":
        subprocess.run(["streamlit", "run", os.path.join(example_path, ui_file)])
    elif ui_type == "python":
        subprocess.run(["python", os.path.join(example_path, ui_file)])
    else:
        print(f"Unknown UI type: {ui_type}")
        sys.exit(1)

def run_demo(example_name: str):
    example_path = os.path.join("examples", example_name)

    # Load workflows.yaml
    with open(os.path.join(example_path, "workflows.yaml")) as f:
        wf_data = yaml.safe_load(f)

    wf = wf_data["workflows"]["main_workflow"][0]
    wf_id = wf["id"]
    ui_type = wf.get("ui", None)

    if ui_type:
        ui_yaml = os.path.join(example_path, "ui.yaml")
        if os.path.exists(ui_yaml):
            with open(ui_yaml) as f:
                ui_info = yaml.safe_load(f)
            ui_entry = ui_info["entry"]
            return launch_ui(example_path, ui_type, ui_entry)

    # Otherwise fallback to CLI runner
    loader = LangSwarmConfigLoader(config_path=example_path)
    workflows, agents, *_ = loader.load()
    executor = WorkflowExecutor(workflows, agents)

    user_input = input("💬 You: ")
    result = executor.run_workflow(wf_id, user_input=user_input)
    print("🤖 Assistant:", result)

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "demo":
        run_demo(sys.argv[2])
    else:
        print("Usage: langswarm demo <example_name>")

if __name__ == "__main__":
    main()
