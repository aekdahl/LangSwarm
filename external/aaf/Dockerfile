# AAF Backend Dockerfile
# Multi-stage build for production deployment

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY external/aaf/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy AAF application code first
COPY external/aaf/app ./app
COPY external/aaf/config ./config
COPY external/aaf/*.py ./

# Copy and install local LangSwarm package
COPY langswarm ./langswarm
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/config /app/credentials

# Set Python path to include LangSwarm
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
