# AgentHub Docker Guide

Quick guide for running AgentHub in Docker.

## Prerequisites

- Docker 20.10+ or Docker Desktop
- Ollama running on host machine (for prompt enhancement)
- 2GB RAM minimum, 4GB recommended

## Quick Start

### Production Mode

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f router

# Check health
curl http://localhost:9090/health

# Stop
docker compose down
```

### Development Mode

```bash
# Use dev compose with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Logs stream automatically
```

## Configuration

### Environment Variables

Set in `docker-compose.yml` or via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ROUTER_PORT` | `9090` | HTTP port for router |
| `OLLAMA_HOST` | `host.docker.internal` | Ollama hostname |
| `OLLAMA_PORT` | `11434` | Ollama port |
| `LOG_LEVEL` | `info` | Logging level (debug/info/warning/error) |
| `CACHE_MAX_SIZE` | `1000` | Max cache entries |
| `CB_FAILURE_THRESHOLD` | `3` | Circuit breaker failure threshold |
| `CB_RECOVERY_TIMEOUT` | `30` | Circuit breaker recovery timeout (seconds) |

### Config Files

Mount custom configs via volumes:

```yaml
volumes:
  - ./my-configs:/app/configs:ro
```

Required files:
- `mcp-servers.json` - MCP server configuration
- `enhancement-rules.json` - Prompt enhancement rules

## Common Tasks

### View Logs

```bash
# All logs
docker compose logs

# Follow logs
docker compose logs -f

# Specific service
docker compose logs router
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart router only
docker compose restart router
```

### Execute Commands in Container

```bash
# Shell access
docker compose exec router bash

# Python REPL
docker compose exec router python

# Check installed packages
docker compose exec router pip list
```

### Update and Rebuild

```bash
# Pull latest code and rebuild
git pull
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### Can't Connect to Ollama

**Symptom**: Enhancement service shows "Ollama unavailable"

**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. On macOS/Windows Docker Desktop: Use `host.docker.internal`
3. On Linux: Use `host.docker.internal` with extra host:
   ```bash
   docker compose up --add-host host.docker.internal:host-gateway
   ```

### Port Already in Use

**Symptom**: `bind: address already in use`

**Solution**: Change port in docker-compose.yml:
```yaml
ports:
  - "9091:9090"  # Host:Container
```

### Container Keeps Restarting

**Check logs**:
```bash
docker compose logs router
```

**Common issues**:
- Missing config files (mount them via volumes)
- Ollama not accessible (check OLLAMA_HOST)
- Out of memory (check resource limits)

### Permission Denied Errors

Container runs as non-root user (UID 1000). Ensure mounted volumes have correct permissions:

```bash
# Fix config directory permissions
chmod -R 755 configs/
```

## Advanced

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max 4 cores
      memory: 4G     # Max 4GB RAM
    reservations:
      cpus: '1'      # Min 1 core
      memory: 1G     # Min 1GB RAM
```

### Health Checks

Router includes built-in health check hitting `/health` endpoint every 30s.

Check status:
```bash
docker compose ps
```

Healthy output shows `(healthy)` status.

### Multi-Stage Build Inspection

View build stages:
```bash
# See all layers
docker history agenthub-router:latest

# Inspect specific stage
docker build --target builder -t agenthub-builder .
docker run --rm agenthub-builder ls -la /opt/venv
```

## Security

### Image Scanning

Scan for vulnerabilities:

```bash
# Using Docker Scout
docker scout cves agenthub-router:latest

# Using Trivy
trivy image agenthub-router:latest
```

### Non-Root User

Container runs as user `agenthub` (UID 1000, GID 1000) for security.

### Network Isolation

Services run in isolated `agenthub-network` bridge network.

## Production Deployment

### Recommended Setup

1. **Use secrets management** for sensitive config
2. **Enable logging driver** (json-file, syslog, etc.)
3. **Set resource limits** appropriately
4. **Configure restart policy**: `restart: unless-stopped`
5. **Monitor health checks** with external monitoring
6. **Use reverse proxy** (nginx/traefik) for SSL

### Example Production Overrides

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  router:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

Run with:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Cleanup

### Remove Containers and Networks

```bash
# Stop and remove containers
docker compose down

# Also remove volumes (WARNING: deletes data)
docker compose down -v
```

### Remove Images

```bash
# Remove AgentHub image
docker rmi agenthub-router:latest

# Remove all unused images
docker image prune -a
```

## Getting Help

- Check logs: `docker compose logs router`
- Inspect container: `docker compose exec router bash`
- Router API docs: http://localhost:9090/docs
- Dashboard: http://localhost:9090/dashboard
