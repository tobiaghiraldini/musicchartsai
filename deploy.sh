#!/bin/bash

# Music Charts AI - Ubuntu 22.04 Deployment Script
# This script handles the complete deployment process for the Django application

set -e  # Exit on any error

# Configuration
APP_NAME="musiccharts"
APP_USER="musiccharts"
APP_DIR="/opt/musiccharts"
APP_SOURCE_DIR="/opt/musiccharts/app"
VENV_DIR="/opt/musiccharts/venv"
LOG_DIR="/var/log/musiccharts"
BACKUP_DIR="/opt/musiccharts/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a user with sudo privileges."
    fi
    
    if ! sudo -n true 2>/dev/null; then
        error "This script requires sudo privileges. Please ensure your user has sudo access."
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "$APP_DIR/static"
    sudo mkdir -p "$APP_DIR/media"
    
    # Set proper ownership
    sudo chown -R $APP_USER:$APP_USER "$APP_DIR"
    sudo chown -R $APP_USER:$APP_USER "$LOG_DIR"
}

# Backup existing deployment
backup_existing() {
    if [ -d "$APP_SOURCE_DIR" ]; then
        log "Creating backup of existing deployment..."
        
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        sudo -u $APP_USER tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$APP_DIR" app/
        
        log "Backup created: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    fi
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libpq-dev \
        build-essential \
        curl \
        git \
        nginx \
        redis-server \
        postgresql-client
        
    # Install Node.js 18.x if not already installed
    if ! command -v node &> /dev/null; then
        log "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u $APP_USER python3 -m venv "$VENV_DIR"
    fi
    
    # Upgrade pip
    sudo -u $APP_USER "$VENV_DIR/bin/pip" install --upgrade pip
    
    # Install Python dependencies
    if [ -f "$APP_SOURCE_DIR/requirements.txt" ]; then
        sudo -u $APP_USER "$VENV_DIR/bin/pip" install -r "$APP_SOURCE_DIR/requirements.txt"
    else
        error "requirements.txt not found in $APP_SOURCE_DIR"
    fi
}

# Build frontend assets
build_frontend() {
    log "Building frontend assets..."
    
    cd "$APP_SOURCE_DIR"
    
    # Install npm dependencies
    sudo -u $APP_USER npm install
    
    # Build production assets
    sudo -u $APP_USER npm run build
    
    log "Frontend build completed"
}

# Run Django deployment checks
run_django_checks() {
    log "Running Django deployment checks..."
    
    cd "$APP_SOURCE_DIR"
    
    # Check Django configuration
    sudo -u $APP_USER "$VENV_DIR/bin/python" manage.py check --deploy
    
    # Run database migrations
    log "Running database migrations..."
    sudo -u $APP_USER "$VENV_DIR/bin/python" manage.py migrate --noinput
    
    # Collect static files
    log "Collecting static files..."
    sudo -u $APP_USER "$VENV_DIR/bin/python" manage.py collectstatic --noinput
    
    # Create superuser if it doesn't exist
    if ! sudo -u $APP_USER "$VENV_DIR/bin/python" manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists()" | grep -q "True"; then
        warning "No admin user found. You may need to create one manually:"
        warning "sudo -u $APP_USER $VENV_DIR/bin/python $APP_SOURCE_DIR/manage.py createsuperuser"
    fi
}

# Setup Gunicorn configuration
setup_gunicorn() {
    log "Setting up Gunicorn configuration..."
    
    # Create production Gunicorn config
    sudo -u $APP_USER cat > "$APP_SOURCE_DIR/gunicorn-prod.conf.py" << EOF
# Gunicorn configuration for production
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
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
user = "$APP_USER"
group = "$APP_USER"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=config.settings',
]

# Preload app for better performance
preload_app = True

# Enable stdio inheritance
enable_stdio_inheritance = True
EOF

    log "Gunicorn configuration created"
}

# Setup systemd services
setup_systemd_services() {
    log "Setting up systemd services..."
    
    # Gunicorn service
    sudo tee /etc/systemd/system/musiccharts-gunicorn.service > /dev/null << EOF
[Unit]
Description=Music Charts AI Gunicorn daemon
Requires=musiccharts-gunicorn.socket
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
RuntimeDirectory=musiccharts
WorkingDirectory=$APP_SOURCE_DIR
Environment=PATH=$VENV_DIR/bin
Environment=DJANGO_SETTINGS_MODULE=config.settings
ExecStart=$VENV_DIR/bin/gunicorn --config gunicorn-prod.conf.py config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Gunicorn socket
    sudo tee /etc/systemd/system/musiccharts-gunicorn.socket > /dev/null << EOF
[Unit]
Description=Music Charts AI Gunicorn socket

[Socket]
ListenStream=/run/musiccharts-gunicorn.sock
SocketUser=www-data
SocketMode=600

[Install]
WantedBy=sockets.target
EOF

    # Celery worker service
    sudo tee /etc/systemd/system/musiccharts-celery.service > /dev/null << EOF
[Unit]
Description=Music Charts AI Celery Worker
After=network.target

[Service]
Type=forking
User=$APP_USER
Group=$APP_USER
EnvironmentFile=$APP_SOURCE_DIR/.env
WorkingDirectory=$APP_SOURCE_DIR
ExecStart=$VENV_DIR/bin/celery -A config worker --loglevel=info --logfile=$LOG_DIR/celery-worker.log --pidfile=/var/run/musiccharts-celery.pid --detach
ExecStop=/bin/kill -s TERM \$MAINPID
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Celery beat service
    sudo tee /etc/systemd/system/musiccharts-celerybeat.service > /dev/null << EOF
[Unit]
Description=Music Charts AI Celery Beat
After=network.target

[Service]
Type=forking
User=$APP_USER
Group=$APP_USER
EnvironmentFile=$APP_SOURCE_DIR/.env
WorkingDirectory=$APP_SOURCE_DIR
ExecStart=$VENV_DIR/bin/celery -A config beat --loglevel=info --logfile=$LOG_DIR/celery-beat.log --pidfile=/var/run/musiccharts-celerybeat.pid --detach
ExecStop=/bin/kill -s TERM \$MAINPID
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    log "Systemd services configured"
}

# Setup Nginx configuration
setup_nginx() {
    log "Setting up Nginx configuration..."
    
    sudo tee /etc/nginx/sites-available/musiccharts > /dev/null << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (update paths as needed)
    # ssl_certificate /etc/ssl/certs/your-cert.crt;
    # ssl_certificate_key /etc/ssl/private/your-private.key;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Client max body size (for file uploads)
    client_max_body_size 50M;
    
    # Static files
    location /static/ {
        alias $APP_SOURCE_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $APP_SOURCE_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Gunicorn socket
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/musiccharts-gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Logging
    access_log /var/log/nginx/musiccharts_access.log;
    error_log /var/log/nginx/musiccharts_error.log;
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/musiccharts /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    sudo nginx -t
    
    log "Nginx configuration created"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start and enable services
    sudo systemctl start musiccharts-gunicorn.socket
    sudo systemctl enable musiccharts-gunicorn.socket
    
    sudo systemctl start musiccharts-gunicorn
    sudo systemctl enable musiccharts-gunicorn
    
    sudo systemctl start musiccharts-celery
    sudo systemctl enable musiccharts-celery
    
    sudo systemctl start musiccharts-celerybeat
    sudo systemctl enable musiccharts-celerybeat
    
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log "Services started successfully"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Check if services are running
    if systemctl is-active --quiet musiccharts-gunicorn; then
        log "✓ Gunicorn service is running"
    else
        error "✗ Gunicorn service is not running"
    fi
    
    if systemctl is-active --quiet musiccharts-celery; then
        log "✓ Celery service is running"
    else
        warning "✗ Celery service is not running"
    fi
    
    if systemctl is-active --quiet nginx; then
        log "✓ Nginx service is running"
    else
        error "✗ Nginx service is not running"
    fi
    
    # Test Django application
    if sudo -u $APP_USER "$VENV_DIR/bin/python" "$APP_SOURCE_DIR/manage.py" check --deploy > /dev/null 2>&1; then
        log "✓ Django application check passed"
    else
        warning "✗ Django application check failed"
    fi
    
    log "Health check completed"
}

# Main deployment function
deploy() {
    log "Starting Music Charts AI deployment..."
    
    check_permissions
    create_directories
    backup_existing
    install_system_dependencies
    setup_python_env
    build_frontend
    run_django_checks
    setup_gunicorn
    setup_systemd_services
    setup_nginx
    start_services
    health_check
    
    log "Deployment completed successfully!"
    log "Your application should now be accessible at your configured domain."
    log "Don't forget to:"
    log "1. Update your domain name in /etc/nginx/sites-available/musiccharts"
    log "2. Configure SSL certificates"
    log "3. Update your .env file with production values"
    log "4. Create a superuser if needed: sudo -u $APP_USER $VENV_DIR/bin/python $APP_SOURCE_DIR/manage.py createsuperuser"
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  deploy     - Run full deployment"
    echo "  backup     - Create backup of existing deployment"
    echo "  health     - Run health check"
    echo "  restart    - Restart all services"
    echo "  stop       - Stop all services"
    echo "  start      - Start all services"
    echo "  status     - Show service status"
    echo "  logs       - Show application logs"
    echo "  help       - Show this help message"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    backup)
        backup_existing
        ;;
    health)
        health_check
        ;;
    restart)
        log "Restarting services..."
        sudo systemctl restart musiccharts-gunicorn
        sudo systemctl restart musiccharts-celery
        sudo systemctl restart musiccharts-celerybeat
        sudo systemctl restart nginx
        log "Services restarted"
        ;;
    stop)
        log "Stopping services..."
        sudo systemctl stop musiccharts-gunicorn
        sudo systemctl stop musiccharts-celery
        sudo systemctl stop musiccharts-celerybeat
        sudo systemctl stop nginx
        log "Services stopped"
        ;;
    start)
        log "Starting services..."
        sudo systemctl start musiccharts-gunicorn.socket
        sudo systemctl start musiccharts-gunicorn
        sudo systemctl start musiccharts-celery
        sudo systemctl start musiccharts-celerybeat
        sudo systemctl start nginx
        log "Services started"
        ;;
    status)
        echo "Service Status:"
        sudo systemctl status musiccharts-gunicorn --no-pager
        sudo systemctl status musiccharts-celery --no-pager
        sudo systemctl status musiccharts-celerybeat --no-pager
        sudo systemctl status nginx --no-pager
        ;;
    logs)
        echo "Recent logs:"
        echo "=== Gunicorn Access Log ==="
        sudo tail -20 /var/log/musiccharts/gunicorn-access.log 2>/dev/null || echo "No access log found"
        echo "=== Gunicorn Error Log ==="
        sudo tail -20 /var/log/musiccharts/gunicorn-error.log 2>/dev/null || echo "No error log found"
        echo "=== Nginx Error Log ==="
        sudo tail -20 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log found"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "Unknown option: $1"
        usage
        ;;
esac
