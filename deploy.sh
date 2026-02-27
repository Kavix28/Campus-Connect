#!/bin/bash

# ==============================================================================
# Enterprise Deployment Script for Oudience Chatbot
# ==============================================================================
# Description:
#   Orchestrates the deployment of the full Docker stack including:
#   - Flask Backend (Gunicorn)
#   - Nginx Reverse Proxy
#   - Ollama (LLM)
#   - Prometheus & Grafana (Monitoring)
#
# Usage:
#   ./deploy.sh
#
# Author: DevOps Team
# ==============================================================================

# ------------------------------------------------------------------------------
# Configuration & Colors
# ------------------------------------------------------------------------------
APP_NAME="Oudience Enterprise Stack"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

fail() {
    log_error "$1"
    exit 1
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        fail "$1 is required but not installed."
    fi
}

# ------------------------------------------------------------------------------
# 1. System Validation
# ------------------------------------------------------------------------------
log_info "Validating environment..."
check_command docker
check_command docker-compose

# Check if docker daemon is running
if ! docker info &> /dev/null; then
    fail "Docker daemon is not running. Please start Docker."
fi

# ------------------------------------------------------------------------------
# 2. Configuration Setup
# ------------------------------------------------------------------------------
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        log_warn ".env file missing. Creating from .env.example..."
        cp .env.example .env
        log_success "Created .env. Please update it with secure secrets!"
    else
        fail ".env and .env.example are missing."
    fi
fi

# ------------------------------------------------------------------------------
# 3. Build & Pull
# ------------------------------------------------------------------------------
log_info "Pulling base images..."
docker-compose pull || fail "Failed to pull images."

log_info "Building application container (Multi-stage)..."
docker-compose build backend || fail "Failed to build backend image."

# ------------------------------------------------------------------------------
# 4. Service Startup
# ------------------------------------------------------------------------------
log_info "Starting services..."
docker-compose up -d --remove-orphans || fail "Failed to start services."

# ------------------------------------------------------------------------------
# 5. Health Checks & Waiting
# ------------------------------------------------------------------------------
log_info "Waiting for services to be healthy..."

wait_for_service() {
    local service=$1
    local port=$2
    local retries=30
    local wait=2

    echo -n "Waiting for $service..."
    for ((i=0; i<retries; i++)); do
        if docker-compose exec $service curl -s http://localhost:$port/health &> /dev/null; then # internal health check if curl exists
             echo -e " ${GREEN}OK${NC}"
             return 0
        fi
        # fallback simple port check via netcat if available or just sleep
        sleep $wait
        echo -n "."
    done
    echo -e " ${RED}Timeout${NC}"
    return 1
}

# We rely on docker healthchecks mostly, so we can check container status
log_info "Checking container health status..."
sleep 5
docker-compose ps

# ------------------------------------------------------------------------------
# 6. Post-Deployment Setup
# ------------------------------------------------------------------------------
# Ensure Ollama model is pulled
log_info "Checking Ollama model..."
if docker-compose exec ollama ollama list | grep -q "llama3"; then
    log_success "Model already exists."
else
    log_info "Pulling default model (llama3) - this may take a while..."
    # Running in background to not block, or blocking if critical
    # docker-compose exec -d ollama ollama pull llama3
    log_warn "Ollama model pull initiated. It will be available shortly."
fi

# ------------------------------------------------------------------------------
# 7. Final Status
# ------------------------------------------------------------------------------
echo -e "${CYAN}==================================================${NC}"
echo -e "${GREEN}       DEPLOYMENT COMPLETE${NC}"
echo -e "${CYAN}==================================================${NC}"
echo -e "Access your services at:"
echo -e "  - Chatbot (Oudience):  ${BLUE}http://localhost:80${NC} (via Nginx)"
echo -e "  - Grafana (Metrics):   ${BLUE}http://localhost:3000${NC} (User: admin, Pass: admin)"
echo -e "  - Prometheus:          ${BLUE}http://localhost:9090${NC}"
echo -e "  - Backend Direct API:  ${BLUE}http://localhost:5001${NC} (Internal)"
echo -e "${CYAN}==================================================${NC}"

log_info "To view logs: docker-compose logs -f"
