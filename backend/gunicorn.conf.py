"""Gunicorn WSGI/ASGI configuration for SentinelAI FastAPI backend on AWS EC2."""

import multiprocessing
import os

bind = os.getenv("BIND", "0.0.0.0:8000")
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("TIMEOUT", 120))
keepalive = int(os.getenv("KEEPALIVE", 5))

# Logging configuration
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
capture_output = True
