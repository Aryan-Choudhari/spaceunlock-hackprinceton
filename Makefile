.PHONY: setup build run test
setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm install
build:
	cd frontend && npm run build
run:
	.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
test:
	.venv/bin/python -m pytest -q
