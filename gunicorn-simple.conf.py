# -*- encoding: utf-8 -*-
"""
Simple Gunicorn configuration for Music Charts AI
Use this for testing and development
"""

import multiprocessing

# Server socket
bind = "127.0.0.1:8080"

# Worker processes
workers = 2  # Use 2 workers for now
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging - output to console
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "musiccharts-gunicorn"

# Server mechanics
daemon = False

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=config.settings',
]

# Preload app for better performance
preload_app = True

# Enable stdio inheritance
enable_stdio_inheritance = True

# Worker timeout settings
graceful_timeout = 30

# Security settings
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
