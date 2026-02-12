# AgentHub Router - Production Dockerfile
# Multi-stage build for optimal image size and security

# =============================================================================
# Stage 1: Node.js installation base
# =============================================================================
FROM python:3.12-slim AS node-installer

# Install Node.js 20.x (required for MCP servers via npx)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 2: Python dependencies builder
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 3: Production runtime
# =============================================================================
FROM python:3.12-slim

# Metadata
LABEL maintainer="AgentHub Team"
LABEL description="AgentHub MCP Router - Centralized MCP server management and prompt enhancement"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    NODE_ENV=production \
    ROUTER_HOST=0.0.0.0 \
    ROUTER_PORT=9090

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Node.js dependencies
        curl \
        ca-certificates \
        gnupg \
        # Process management
        procps \
        # For keyring/keychain (if needed, though this is macOS-specific)
        && \
    # Install Node.js
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r agenthub && \
    useradd -r -g agenthub -u 1000 -s /bin/bash -d /app agenthub

# Create application directory and set ownership
WORKDIR /app
RUN chown -R agenthub:agenthub /app

# Copy Python virtual environment from builder
COPY --from=builder --chown=agenthub:agenthub /opt/venv /opt/venv

# Copy application code with proper ownership
COPY --chown=agenthub:agenthub router/ ./router/
COPY --chown=agenthub:agenthub configs/ ./configs/
COPY --chown=agenthub:agenthub templates/ ./templates/
COPY --chown=agenthub:agenthub pyproject.toml ./

# Create directories for runtime data
RUN mkdir -p /app/data /app/logs && \
    chown -R agenthub:agenthub /app/data /app/logs

# Switch to non-root user
USER agenthub

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:9090/health', timeout=5.0)" || exit 1

# Expose the router port
EXPOSE 9090

# Run the application
CMD ["uvicorn", "router.main:app", "--host", "0.0.0.0", "--port", "9090", "--log-level", "info"]
