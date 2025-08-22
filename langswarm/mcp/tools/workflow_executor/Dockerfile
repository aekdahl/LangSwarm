FROM python:3.9-slim

LABEL maintainer="LangSwarm Team"
LABEL description="Workflow Executor MCP Tool - Remote execution server"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy LangSwarm source code
COPY . /app/langswarm/

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create directories for workflow execution
RUN mkdir -p /app/workflows /app/temp /app/logs

# Set environment variables
ENV WORKFLOW_EXECUTOR_PORT=4020
ENV WORKFLOW_EXECUTOR_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${WORKFLOW_EXECUTOR_PORT}/health || exit 1

# Expose port
EXPOSE ${WORKFLOW_EXECUTOR_PORT}

# Create non-root user for security
RUN groupadd -r langswarm && useradd -r -g langswarm langswarm
RUN chown -R langswarm:langswarm /app
USER langswarm

# Start the workflow executor server
CMD ["python", "-m", "langswarm.mcp.tools.workflow_executor.main"]