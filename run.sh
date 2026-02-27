#!/bin/bash

# ==============================================================================
# ZERO-SETUP DISTRIBUTION RUNNER
# ==============================================================================
# Description:
#   One-click startup for Oudience Chatbot.
#   Checks requirements, setups config, pulls image, and runs.
#
# Usage:
#   ./run.sh
# ==============================================================================

# Configuration
IMAGE_NAME="oudience-chatbot:latest" # In real scenario: "yourusername/oudience:v1.0"
CONTAINER_NAME="oudience_chatbot_prod"
DEFAULT_PORT=5001

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   Oudience Chatbot - Production Start   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not installed.${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 2. Setup Environment
if [ ! -f .env ]; then
    echo -e "${BLUE}[INFO] Creating .env file from example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        # Generate random secret key
        SECRET=$(openssl rand -hex 32 2>/dev/null || echo "changethis_to_random_secret")
        # Sed command varies by OS (Linux vs Mac). Simplified approach:
        echo "" >> .env
        echo "# Auto-generated secret" >> .env
        echo "SECRET_KEY=$SECRET" >> .env
        echo -e "${GREEN}[OK] .env created.${NC}"
    else
        echo -e "${RED}[ERROR] .env.example not found.${NC}"
        exit 1
    fi
fi

# 3. Create Data Files if Missing (to prevent Docker mapping dirs instead of files)
touch analytics.db
if [ ! -f orders.json ]; then echo "[]" > orders.json; fi
if [ ! -f knowledge_base.json ]; then echo "[]" > knowledge_base.json; fi

# 4. Pull & Run
echo -e "${BLUE}[INFO] Starting System...${NC}"

# For local testing without hub, we build. In real dist, we pull.
# docker compose pull

echo -e "${BLUE}[INFO] Booting Container...${NC}"
docker compose up -d --remove-orphans

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}   SYSTEM RUNNING SUCCESSFULLY           ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo -e "Access URL:  http://localhost:$DEFAULT_PORT"
    echo -e "Logs:        docker compose logs -f"
    echo -e "Stop:        docker compose down"
else
    echo -e "${RED}[ERROR] Failed to start containers.${NC}"
    exit 1
fi
