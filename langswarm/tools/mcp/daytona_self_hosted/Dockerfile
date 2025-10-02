# Dockerfile for Self-Hosted Daytona MCP Server
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DAYTONA_VERSION=latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    docker.io \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Daytona CLI
RUN curl -sf https://download.daytona.io/daytona/install.sh | sh && \
    mv /root/.local/bin/daytona /usr/local/bin/daytona && \
    chmod +x /usr/local/bin/daytona

# Verify Daytona installation
RUN daytona version || echo "Daytona CLI installed but server not running (expected)"

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/schema || exit 1

# Start the MCP server
CMD ["python", "main.py"]


