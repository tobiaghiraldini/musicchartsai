# -*- encoding: utf-8 -*-
"""
Production Gunicorn configuration for Music Charts AI
Optimized for Ubuntu 22.04 deployment with Apache2
"""

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
# Formula: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/musiccharts/gunicorn-access.log"
errorlog = "/var/log/musiccharts/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "musiccharts-gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/run/musiccharts-gunicorn.pid"
user = "musiccharts"
group = "musiccharts"
tmp_upload_dir = None

# SSL (if needed - uncomment and configure paths)
# keyfile = "/etc/ssl/private/your-private.key"
# certfile = "/etc/ssl/certs/your-cert.crt"

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
worker_tmp_dir = "/dev/shm"

# Security settings
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
