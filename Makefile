.PHONY: run test install

run:
	bash scripts/run.sh

test:
	PYTHONPATH=. .venv/bin/python -m pytest

install:
	bash scripts/install.sh
