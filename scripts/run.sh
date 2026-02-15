#!/bin/bash
set -e

[ ! -f ".env" ] && echo "Error: .env not found!" && exit 1

source venv/bin/activate
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python3 -m src.main
