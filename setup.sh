#!/usr/bin/env bash
set -euo pipefail

# Detect OS for Python venv compatibility
PYTHON=python3
if ! command -v $PYTHON &>/dev/null; then
  PYTHON=python
fi

echo "Creating virtual environment..."
$PYTHON -m venv .venv

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo
echo "✅ Setup complete!"
echo "To activate this environment again later, run:"
echo "  source .venv/bin/activate"
