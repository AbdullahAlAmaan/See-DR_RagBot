#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Pre-download embedding and reranker models
python scripts/download_models.py

echo "Setup complete. Activate venv with: source .venv/bin/activate"
