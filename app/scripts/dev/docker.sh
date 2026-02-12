#!/bin/bash
# AgentHub Docker Helper Script
# Quick commands for common Docker operations

set -e

COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose.dev.yml"
SERVICE_NAME="router"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_usage() {
    cat << EOF
AgentHub Docker Helper

Usage: $0 <command> [options]

Commands:
    start           Start AgentHub in production mode
    start-dev       Start AgentHub in development mode (hot reload)
    stop            Stop all services
    restart         Restart all services
    logs            View logs (follow mode)
    logs-tail       View last 100 lines of logs
    build           Rebuild images
    rebuild         Rebuild images without cache
    shell           Open shell in router container
    health          Check service health
    clean           Stop and remove containers, networks, volumes
    clean-images    Remove AgentHub images
    ps              Show running containers
    test            Run health check test

Examples:
    $0 start              # Start in production mode
    $0 start-dev          # Start with hot reload
    $0 logs               # Follow logs
    $0 shell              # Get bash shell in container
    $0 health             # Check if services are healthy

EOF
}

function start_prod() {
    echo -e "${GREEN}Starting AgentHub in production mode...${NC}"
    docker compose -f "${COMPOSE_FILE}" up -d
    echo -e "${GREEN}AgentHub started. Dashboard: http://localhost:9090/dashboard${NC}"
}

function start_dev() {
    echo -e "${YELLOW}Starting AgentHub in development mode (hot reload)...${NC}"
    docker compose -f "${COMPOSE_FILE}" -f "${DEV_COMPOSE_FILE}" up
}

function stop_services() {
    echo -e "${YELLOW}Stopping AgentHub...${NC}"
    docker compose -f "${COMPOSE_FILE}" down
    echo -e "${GREEN}AgentHub stopped.${NC}"
}

function restart_services() {
    echo -e "${YELLOW}Restarting AgentHub...${NC}"
    docker compose -f "${COMPOSE_FILE}" restart
    echo -e "${GREEN}AgentHub restarted.${NC}"
}

function show_logs() {
    echo -e "${GREEN}Following logs (Ctrl+C to exit)...${NC}"
    docker compose -f "${COMPOSE_FILE}" logs -f "${SERVICE_NAME}"
}

function show_logs_tail() {
    echo -e "${GREEN}Last 100 log lines:${NC}"
    docker compose -f "${COMPOSE_FILE}" logs --tail=100 "${SERVICE_NAME}"
}

function build_images() {
    echo -e "${GREEN}Building images...${NC}"
    docker compose -f "${COMPOSE_FILE}" build
    echo -e "${GREEN}Build complete.${NC}"
}

function rebuild_images() {
    echo -e "${YELLOW}Rebuilding images without cache...${NC}"
    docker compose -f "${COMPOSE_FILE}" build --no-cache
    echo -e "${GREEN}Rebuild complete.${NC}"
}

function open_shell() {
    echo -e "${GREEN}Opening shell in ${SERVICE_NAME} container...${NC}"
    docker compose -f "${COMPOSE_FILE}" exec "${SERVICE_NAME}" bash || \
        docker compose -f "${COMPOSE_FILE}" exec "${SERVICE_NAME}" sh
}

function check_health() {
    echo -e "${GREEN}Checking service health...${NC}"
    docker compose -f "${COMPOSE_FILE}" ps
    echo ""
    echo "Health check endpoint:"
    curl -s http://localhost:9090/health | python -m json.tool || echo -e "${RED}Service not responding${NC}"
}

function clean_all() {
    echo -e "${RED}This will stop and remove all containers, networks, and volumes.${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ${REPLY} =~ ^[Yy]$ ]]; then
        docker compose -f "${COMPOSE_FILE}" down -v
        echo -e "${GREEN}Cleanup complete.${NC}"
    else
        echo "Cancelled."
    fi
}

function clean_images() {
    echo -e "${RED}This will remove AgentHub Docker images.${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ${REPLY} =~ ^[Yy]$ ]]; then
        docker rmi agenthub-router:latest agenthub-router:dev || true
        echo -e "${GREEN}Images removed.${NC}"
    else
        echo "Cancelled."
    fi
}

function show_ps() {
    docker compose -f "${COMPOSE_FILE}" ps
}

function run_test() {
    echo -e "${GREEN}Running health check test...${NC}"
    
    # Check if container is running
    if ! docker compose -f "${COMPOSE_FILE}" ps | grep -q "${SERVICE_NAME}.*Up"; then
        echo -e "${RED}Error: ${SERVICE_NAME} container is not running${NC}"
        exit 1
    fi
    
    # Test health endpoint
    echo "Testing /health endpoint..."
    if curl -sf http://localhost:9090/health > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${RED}✗ Health check failed${NC}"
        exit 1
    fi
    
    # Test MCP servers endpoint
    echo "Testing /servers endpoint..."
    if curl -sf http://localhost:9090/servers > /dev/null; then
        echo -e "${GREEN}✓ Servers endpoint passed${NC}"
    else
        echo -e "${RED}✗ Servers endpoint failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All tests passed!${NC}"
}

# Main command dispatch
case "${1:-}" in
    start)
        start_prod
        ;;
    start-dev)
        start_dev
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    logs-tail)
        show_logs_tail
        ;;
    build)
        build_images
        ;;
    rebuild)
        rebuild_images
        ;;
    shell)
        open_shell
        ;;
    health)
        check_health
        ;;
    clean)
        clean_all
        ;;
    clean-images)
        clean_images
        ;;
    ps)
        show_ps
        ;;
    test)
        run_test
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '${1:-}'${NC}\n"
        print_usage
        exit 1
        ;;
esac
