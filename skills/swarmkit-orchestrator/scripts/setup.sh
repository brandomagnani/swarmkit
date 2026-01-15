#!/bin/bash
# Setup Python environment for SwarmKit orchestration
# Creates .venv in current directory and installs swarmkit

set -e

VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment exists at $VENV_DIR"
    source "$VENV_DIR/bin/activate"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Installing swarmkit..."
    pip install --quiet swarmkit
fi

echo "Ready. Activate with: source $VENV_DIR/bin/activate"
