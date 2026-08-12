# Devcontainer Dockerfile for PromptHub
# Base image provides Python 3.12 and common tooling for VS Code devcontainers
FROM mcr.microsoft.com/devcontainers/python:1-3.12

# Avoid prompts during package installs
ENV DEBIAN_FRONTEND=noninteractive

# Install Node.js 20 and common build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg2 lsb-release build-essential git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure npm global binaries are available to the default vscode user
ENV NPM_CONFIG_PREFIX=/home/vscode/.npm-global
RUN mkdir -p /home/vscode/.npm-global && chown -R vscode:vscode /home/vscode/.npm-global

# Enable Corepack and prepare pnpm (project expects pnpm@10.27.0)
# Corepack ships with Node 16+; preparing pnpm here avoids per-container bootstrap.
RUN corepack enable && corepack prepare pnpm@10.27.0 --activate || true

# Install common CLI tools as needed (uncomment to add)
# RUN npm install -g npm@latest

# Set non-root user (image defines 'vscode')
USER vscode

# Default workdir
WORKDIR /workspace
