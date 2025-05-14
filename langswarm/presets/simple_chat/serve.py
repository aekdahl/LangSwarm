import streamlit as st
from langswarm.core.config import LangSwarmConfigLoader, WorkflowExecutor

st.set_page_config(page_title="🗣️ Simple Chat")

st.title("🗣️ Simple Chat Demo")
st.markdown("Talk to an AI assistant powered by LangSwarm.")

user_input = st.text_input("Your message:", key="user_input")
submit = st.button("Send")

if submit and user_input:
    loader = LangSwarmConfigLoader(config_path="examples/simple_chat")
    workflows, agents, *_ = loader.load()

    executor = WorkflowExecutor(workflows, agents)
    result = executor.run_workflow("simple_chat", user_input=user_input)

    st.markdown("### Assistant's reply:")
    st.write(result if isinstance(result, str) else str(result))
