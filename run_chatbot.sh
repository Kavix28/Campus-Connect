#!/bin/bash

# ==============================================================================
# Chatbot Production Runner Script
# ==============================================================================
# Description:
#   Sets up the environment, manages dependencies, initializes the database,
#   and runs the Flask AI Chatbot application in Dev or Prod mode.
#
# Usage:
#   ./run_chatbot.sh [--dev|--prod]
#
# Author: DevOps Team
# ==============================================================================

# ------------------------------------------------------------------------------
# Configuration & Colors
# ------------------------------------------------------------------------------
APP_NAME="Oudience Chatbot"
REQUIREMENTS_FILE="requirements.txt"
DB_FILE="analytics.db"
VENV_DIR=".venv"
PORT=5001

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
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

fail() {
    log_error "$1"
    exit 1
}

# ------------------------------------------------------------------------------
# 1. Argument Parsing
# ------------------------------------------------------------------------------
MODE="dev" # Default mode

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --prod) MODE="prod" ;;
        --dev)  MODE="dev" ;;
        *)      log_warn "Unknown parameter passed: $1"; log_info "Usage: $0 [--dev|--prod]" ;;
    esac
    shift
done

log_info "Starting $APP_NAME in ${CYAN}${MODE^^}${NC} mode..."

# ------------------------------------------------------------------------------
# 2. Check Python Version (3.10+)
# ------------------------------------------------------------------------------
# Try to find python3 or python
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    fail "Python is not installed. Please install Python 3.10+."
fi

PY_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10 ]]; then
    fail "Python 3.10+ is required. Found Python $PY_VERSION at $($PYTHON_CMD -c 'import sys; print(sys.executable)')"
else
    log_success "Python $PY_VERSION detected."
fi

# ------------------------------------------------------------------------------
# 3. Virtual Environment Setup
# ------------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR" || fail "Failed to create virtual environment."
else
    log_info "Virtual environment found."
fi

# ------------------------------------------------------------------------------
# 4. Activate Virtual Environment
# ------------------------------------------------------------------------------
# Handle Windows (Scripts) vs Linux/Mac (bin) layout
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    fail "Cannot find activate script in $VENV_DIR. The venv might be corrupted."
fi

# Verify activation
if [[ "$VIRTUAL_ENV" == "" ]]; then
    fail "Failed to activate virtual environment."
fi

# ------------------------------------------------------------------------------
# 5. Dependencies Installation
# ------------------------------------------------------------------------------
if [ -f "$REQUIREMENTS_FILE" ]; then
    log_info "Checking dependencies..."
    # Quiet install to reduce noise, upgrade pip first
    pip install --upgrade pip --quiet
    pip install -r "$REQUIREMENTS_FILE" --quiet || fail "Failed to install dependencies."
    log_success "Dependencies installed."
else
    log_warn "$REQUIREMENTS_FILE not found. Skipping dependency installation."
fi

# ------------------------------------------------------------------------------
# 6. Database Initialization
# ------------------------------------------------------------------------------
if [ -f "$DB_FILE" ]; then
    log_info "Database $DB_FILE exists."
else
    log_info "Initializing database $DB_FILE..."
    # Creating the file triggers the app to run SQLite initialization logic
    touch "$DB_FILE"
    
    # Optional: Run a quick python snippet to ensure tables are created immediately
    # rather than waiting for first request, but app.py handles this well.
    # We'll rely on the app's internal logic since we just need the file to exist 
    # to trigger the SQLite mode in OrderService.
    log_success "Database initialized (schema will populate on startup)."
fi

# ------------------------------------------------------------------------------
# 7. Directory Setup
# ------------------------------------------------------------------------------
ensure_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        log_info "Created directory: $1"
    fi
}

ensure_dir "flask_sessions"
ensure_dir "uploads"
ensure_dir "logs"

# ------------------------------------------------------------------------------
# 8. Environment Variables
# ------------------------------------------------------------------------------
if [ -f .env ]; then
    log_info "Loading environment variables from .env..."
    set -a # automatically export all variables
    source .env
    set +a
else
    log_warn ".env file not found. Using default application settings."
fi

# ------------------------------------------------------------------------------
# 9. Run Application
# ------------------------------------------------------------------------------
log_info "Starting application..."
echo -e "${CYAN}--------------------------------------------------${NC}"

trap 'echo -e "\n${BLUE}[INFO]${NC} Stopping application..."; exit 0' SIGINT SIGTERM

if [ "$MODE" == "prod" ]; then
    # Production Mode using Waitress
    log_success "Running in PRODUCTION mode with Waitress on port $PORT"
    # waitress-serve is installed from requirements.txt
    waitress-serve --port=$PORT app:app
else
    # Development Mode
    log_success "Running in DEVELOPMENT mode with Flask"
    python app.py
fi
