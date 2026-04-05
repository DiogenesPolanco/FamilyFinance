#!/bin/bash

echo "Installing dependencies..."

pip install -r requirements.txt

echo "Starting FastAPI..."

PORT=${PORT:-8000}

gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:$PORT \
  --workers 2