# Development Scripts

Scripts for testing, building, and releasing AgentHub.

## Scripts

### `run-tests.sh`
Runs the AgentHub test suite with comprehensive coverage.

**Purpose:** Execute all tests and generate coverage reports for continuous integration.

**Usage:**
```bash
# Run all tests
scripts/dev/run-tests.sh

# Run specific test file
scripts/dev/run-tests.sh tests/test_routing.py

# Run with verbose output
scripts/dev/run-tests.sh -v

# Generate HTML coverage report
scripts/dev/run-tests.sh --coverage

# Watch mode (re-run on file changes)
scripts/dev/run-tests.sh --watch
```

**Test categories:**
- **Unit tests**: `tests/unit/` - Individual component testing
- **Integration tests**: `tests/integration/` - API endpoint testing
- **E2E tests**: `tests/e2e/` - Full workflow testing

**Example output:**
```
🧪 Running AgentHub Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Installing dependencies...
  ✓ pytest installed
  ✓ pytest-cov installed
  ✓ httpx installed

🔬 Running tests...

tests/unit/test_circuit_breaker.py::test_circuit_opens_after_failures PASSED
tests/unit/test_cache.py::test_lru_eviction PASSED
tests/integration/test_mcp_proxy.py::test_context7_query PASSED
tests/integration/test_enhancement.py::test_ollama_enhancement PASSED
tests/e2e/test_client_workflow.py::test_claude_desktop_flow PASSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 47/47 tests passed (12.3s)
📊 Coverage: 87%
```

**Dependencies:**
- Python 3.8+
- pytest
- pytest-cov
- pytest-asyncio
- httpx

**Configuration:**
- `pytest.ini` - Pytest settings
- `.coveragerc` - Coverage configuration

### `docker.sh`
Manages Docker containers for AgentHub development and deployment.

**Purpose:** Build, run, and manage AgentHub in Docker containers.

**Usage:**
```bash
# Build Docker image
scripts/dev/docker.sh build

# Run in development mode (with hot reload)
scripts/dev/docker.sh dev

# Run in production mode
scripts/dev/docker.sh prod

# Run tests in Docker
scripts/dev/docker.sh test

# Stop all containers
scripts/dev/docker.sh stop

# Clean up containers and images
scripts/dev/docker.sh clean

# View logs
scripts/dev/docker.sh logs

# Shell into container
scripts/dev/docker.sh shell
```

**Docker images:**
- **agenthub:dev** - Development image with hot reload
- **agenthub:prod** - Production image (multi-stage build)
- **agenthub:test** - Test image with test dependencies

**Example output:**
```
🐳 AgentHub Docker Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Building development image...
  Step 1/12 : FROM python:3.11-slim
  Step 2/12 : WORKDIR /app
  ...
  Step 12/12 : CMD ["uvicorn", "router.main:app", "--reload"]
  ✓ Built agenthub:dev (2m 34s)

🚀 Starting container...
  Container ID: abc123def456
  Port mapping: 9090:9090
  Volume: /Users/user/.local/share/agenthub:/app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ AgentHub running at http://localhost:9090
```

**Environment variables:**
- `AGENTHUB_ENV` - Environment (dev/prod/test)
- `ROUTER_PORT` - Port to expose (default: 9090)
- `OLLAMA_HOST` - Ollama endpoint
- `LOG_LEVEL` - Logging verbosity

### `release.sh`
Automates the AgentHub release process.

**Purpose:** Version bump, changelog generation, and deployment preparation.

**Usage:**
```bash
# Patch release (0.1.0 → 0.1.1)
scripts/dev/release.sh patch

# Minor release (0.1.1 → 0.2.0)
scripts/dev/release.sh minor

# Major release (0.2.0 → 1.0.0)
scripts/dev/release.sh major

# Dry run (preview changes)
scripts/dev/release.sh --dry-run minor

# Skip tests
scripts/dev/release.sh --skip-tests patch
```

**Release steps:**
1. ✓ Run test suite
2. ✓ Bump version in `__version__.py`
3. ✓ Generate changelog from git commits
4. ✓ Update documentation
5. ✓ Create git tag
6. ✓ Build Docker images
7. ✓ Push to registry (optional)

**Example output:**
```
🚀 AgentHub Release Process
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Current version: 0.1.5
📊 New version: 0.2.0 (minor)

🧪 Running test suite...
  ✓ 47/47 tests passed

📝 Generating changelog...
  Found 23 commits since last release:
    - feat: Add circuit breaker auto-recovery
    - fix: Handle WebSocket disconnections
    - docs: Update integration guides
  ✓ CHANGELOG.md updated

🏷️  Creating git tag...
  ✓ Tagged as v0.2.0

🐳 Building Docker images...
  ✓ agenthub:0.2.0
  ✓ agenthub:latest

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Release 0.2.0 ready!

Next steps:
  1. Review CHANGELOG.md
  2. Push tags: git push origin v0.2.0
  3. Create GitHub release
  4. Deploy to production
```

**Dependencies:**
- `git` for version control
- `jq` for JSON manipulation
- `docker` for image building
- `gh` (optional) for GitHub releases

## Development Workflow

### Local Development

```bash
# 1. Set up development environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run tests
scripts/dev/run-tests.sh

# 3. Start development server
scripts/dev/docker.sh dev
# Or without Docker:
uvicorn router.main:app --reload --port 9090
```

### Pre-Commit Workflow

```bash
# Run before committing
scripts/dev/run-tests.sh
mypy router/
ruff check router/
ruff format router/
```

### Continuous Integration

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: scripts/dev/run-tests.sh
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from router.routing.registry import ServerRegistry

@pytest.fixture
def registry():
    """Fixture for ServerRegistry."""
    return ServerRegistry()

def test_server_registration(registry):
    """Test server can be registered."""
    registry.register("test-server", {
        "url": "http://localhost:8000",
        "status": "running"
    })
    assert "test-server" in registry.list_servers()

@pytest.mark.asyncio
async def test_async_operation(registry):
    """Test async server operation."""
    result = await registry.health_check("test-server")
    assert result["status"] == "healthy"
```

### Running Specific Tests

```bash
# Run single test file
pytest tests/unit/test_circuit_breaker.py

# Run specific test function
pytest tests/unit/test_circuit_breaker.py::test_circuit_opens_after_failures

# Run tests matching pattern
pytest -k "circuit" -v

# Run with markers
pytest -m "integration" -v
```

### Coverage Reports

```bash
# Generate terminal report
pytest --cov=router --cov-report=term-missing

# Generate HTML report
pytest --cov=router --cov-report=html
open htmlcov/index.html

# Generate XML (for CI)
pytest --cov=router --cov-report=xml
```

## Docker Development

### Multi-Stage Build

```dockerfile
# Dockerfile (production)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY router/ ./router/
COPY configs/ ./configs/
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "router.main:app", "--host", "0.0.0.0", "--port", "9090"]
```

### Development with Hot Reload

```bash
# Mount local code for hot reload
docker run -it --rm \
  -v "$(pwd):/app" \
  -p 9090:9090 \
  -e AGENTHUB_ENV=dev \
  agenthub:dev
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  agenthub:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "9090:9090"
    environment:
      - AGENTHUB_ENV=prod
      - OLLAMA_HOST=http://ollama:11434
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

volumes:
  ollama-data:
```

## Release Process

### Version Bump

```bash
# Semantic versioning: MAJOR.MINOR.PATCH
# MAJOR: Breaking changes
# MINOR: New features (backwards compatible)
# PATCH: Bug fixes

# Example: 0.1.5 → 0.2.0 (new features)
scripts/dev/release.sh minor
```

### Changelog Format

```markdown
# Changelog

## [0.2.0] - 2024-01-30

### Added
- Circuit breaker auto-recovery mechanism
- WebSocket transport support for MCP servers
- Real-time audit event streaming

### Changed
- Improved error handling in MCP proxy
- Updated Ollama client to use streaming API

### Fixed
- Race condition in server lifecycle management
- Memory leak in cache eviction

### Deprecated
- Legacy stdio bridge (use unified bridge instead)
```

### Git Tags

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release 0.2.0: Add circuit breaker auto-recovery"

# Push tag
git push origin v0.2.0

# List tags
git tag -l
```

## Troubleshooting

### Tests Failing

**Problem:** Tests fail with import errors

**Solution:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Or use pytest-pythonpath
pip install pytest-pythonpath
```

**Problem:** Async tests hang

**Solution:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Add to pytest.ini:
# [pytest]
# asyncio_mode = auto
```

### Docker Issues

**Problem:** Port already in use

**Solution:**
```bash
# Find process using port 9090
lsof -i :9090

# Stop conflicting container
docker stop $(docker ps -q --filter "publish=9090")
```

**Problem:** Build fails with dependency errors

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
scripts/dev/docker.sh build --no-cache
```

## Related Documentation

- [Testing Guide](../../guides/testing-integrations.md)
- [CI/CD Setup](../../.github/workflows/)
- [Docker Deployment](../../docs/deployment.md)
