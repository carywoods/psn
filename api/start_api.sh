#!/bin/bash
# PSN API Launch Script
#
# Usage: ./api/start_api.sh
#
# This script starts the PSN API server on port 8502.
# Make sure to activate the psn-engine conda environment first,
# or use the conda activation below.

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8502}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "========================================"
echo "PSN API Server"
echo "========================================"
echo "Project Root: $PROJECT_ROOT"
echo "Host: $API_HOST"
echo "Port: $API_PORT"
echo "Log Level: $LOG_LEVEL"
echo "========================================"

# Change to project directory
cd "$PROJECT_ROOT"

# Activate conda environment if not already active
if [[ -z "$CONDA_PREFIX" ]] || [[ "$CONDA_PREFIX" != *"psn-engine"* ]]; then
    echo "Activating psn-engine conda environment..."
    if [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        conda activate psn-engine
    elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
        conda activate psn-engine
    else
        echo "Warning: Could not find conda. Please activate psn-engine manually."
    fi
fi

echo "Python: $(which python)"
echo "Starting uvicorn server..."
echo ""

# Start the API server
# Using single worker because COBRApy model is held in memory
# Thread-safe FBA is handled internally by COBRApy
exec uvicorn api.main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --workers 1 \
    --log-level "$LOG_LEVEL"
