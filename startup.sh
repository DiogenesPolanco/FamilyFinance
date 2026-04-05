#!/bin/bash

echo "Starting FastAPI..."

gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --workers 2