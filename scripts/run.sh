#!/bin/bash
set -e

cd "$(dirname "$0")/.."

[ ! -f ".env" ] && echo "Error: .env not found — copy .env.example and fill in your values." && exit 1
[ ! -d ".venv" ] && echo "Error: .venv not found — run: bash scripts/install.sh" && exit 1

export PYTHONPATH="${PWD}:${PYTHONPATH}"
exec .venv/bin/python -m src.main
