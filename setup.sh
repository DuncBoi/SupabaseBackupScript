#!/usr/bin/env bash
set -euo pipefail

# 1) Create & activate venv
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo
echo "To start using: .venv/bin/activate"

