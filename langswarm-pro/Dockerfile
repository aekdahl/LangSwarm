FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# Note: In a real monorepo build, we'd copy the wheels or install from index
# For this structure, we assume we copy the local packages
COPY . /app/langswarm-pro
COPY ../langswarm /app/langswarm
COPY ../langswarm-memory /app/langswarm-memory

# Install packages in dependency order
RUN pip install --no-cache-dir /app/langswarm-memory
RUN pip install --no-cache-dir /app/langswarm
RUN pip install --no-cache-dir /app/langswarm-pro

# Set python path
ENV PYTHONPATH=/app/langswarm-pro

# Expose API port
EXPOSE 8080

# Run commands
CMD ["uvicorn", "langswarm_pro.server.main:app", "--host", "0.0.0.0", "--port", "8080"]
