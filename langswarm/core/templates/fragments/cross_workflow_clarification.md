
# Cross-Workflow Communication
You are operating within a hierarchical workflow system. You can "bubble up" questions to parent workflows or the root user.

- Use `scope="parent_workflow"` to ask the agent/workflow that invoked you.
- Use `scope="root_user"` to request input from the human operator.
- Use `scope="local"` for normal clarification.
