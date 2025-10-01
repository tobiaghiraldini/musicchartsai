#!/bin/bash

# Music Charts AI - Service Management Script
# This script helps manage Gunicorn, Celery Worker, and Celery Beat services

set -e

# Configuration
APP_DIR="/home/users/ninjabit/musicchartsai"
VENV_PATH="/home/users/ninjabit/.pyenv/versions/musicchartsai/bin"
LOG_DIR="$APP_DIR/logs"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to check if process is running
check_process() {
    local process_name="$1"
    if pgrep -f "$process_name" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start Gunicorn
start_gunicorn() {
    if check_process "gunicorn.*config.wsgi"; then
        warning "Gunicorn is already running"
        return
    fi
    
    log "Starting Gunicorn..."
    cd "$APP_DIR"
    nohup "$VENV_PATH/gunicorn" --config gunicorn-simple.conf.py config.wsgi:application > "$LOG_DIR/gunicorn.log" 2>&1 &
    sleep 2
    
    if check_process "gunicorn.*config.wsgi"; then
        log "✓ Gunicorn started successfully"
    else
        error "✗ Failed to start Gunicorn"
        return 1
    fi
}

# Function to start Celery Worker
start_celery_worker() {
    if check_process "celery.*worker"; then
        warning "Celery Worker is already running"
        return
    fi
    
    log "Starting Celery Worker..."
    cd "$APP_DIR"
    nohup "$VENV_PATH/celery" -A config worker --loglevel=info > "$LOG_DIR/celery-worker.log" 2>&1 &
    sleep 2
    
    if check_process "celery.*worker"; then
        log "✓ Celery Worker started successfully"
    else
        error "✗ Failed to start Celery Worker"
        return 1
    fi
}

# Function to start Celery Beat
start_celery_beat() {
    if check_process "celery.*beat"; then
        warning "Celery Beat is already running"
        return
    fi
    
    log "Starting Celery Beat..."
    cd "$APP_DIR"
    nohup "$VENV_PATH/celery" -A config beat --loglevel=info > "$LOG_DIR/celery-beat.log" 2>&1 &
    sleep 2
    
    if check_process "celery.*beat"; then
        log "✓ Celery Beat started successfully"
    else
        error "✗ Failed to start Celery Beat"
        return 1
    fi
}

# Function to stop all services
stop_all() {
    log "Stopping all services..."
    
    # Stop Gunicorn
    if check_process "gunicorn.*config.wsgi"; then
        log "Stopping Gunicorn..."
        pkill -f "gunicorn.*config.wsgi"
        sleep 2
    fi
    
    # Stop Celery Worker
    if check_process "celery.*worker"; then
        log "Stopping Celery Worker..."
        pkill -f "celery.*worker"
        sleep 2
    fi
    
    # Stop Celery Beat
    if check_process "celery.*beat"; then
        log "Stopping Celery Beat..."
        pkill -f "celery.*beat"
        sleep 2
    fi
    
    log "All services stopped"
}

# Function to show status
show_status() {
    echo "=== Service Status ==="
    
    if check_process "gunicorn.*config.wsgi"; then
        echo "✓ Gunicorn: Running"
    else
        echo "✗ Gunicorn: Not running"
    fi
    
    if check_process "celery.*worker"; then
        echo "✓ Celery Worker: Running"
    else
        echo "✗ Celery Worker: Not running"
    fi
    
    if check_process "celery.*beat"; then
        echo "✓ Celery Beat: Running"
    else
        echo "✗ Celery Beat: Not running"
    fi
    
    echo ""
    echo "=== Process Details ==="
    ps aux | grep -E "(gunicorn|celery)" | grep -v grep || echo "No processes found"
}

# Function to show logs
show_logs() {
    local service="$1"
    
    case "$service" in
        gunicorn)
            echo "=== Gunicorn Logs ==="
            tail -20 "$LOG_DIR/gunicorn.log" 2>/dev/null || echo "No logs found"
            ;;
        worker)
            echo "=== Celery Worker Logs ==="
            tail -20 "$LOG_DIR/celery-worker.log" 2>/dev/null || echo "No logs found"
            ;;
        beat)
            echo "=== Celery Beat Logs ==="
            tail -20 "$LOG_DIR/celery-beat.log" 2>/dev/null || echo "No logs found"
            ;;
        all)
            show_logs gunicorn
            echo ""
            show_logs worker
            echo ""
            show_logs beat
            ;;
        *)
            echo "Usage: $0 logs [gunicorn|worker|beat|all]"
            ;;
    esac
}

# Main script logic
case "${1:-start}" in
    start)
        log "Starting Music Charts AI services..."
        start_gunicorn
        start_celery_worker
        start_celery_beat
        echo ""
        show_status
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 3
        start_gunicorn
        start_celery_worker
        start_celery_beat
        echo ""
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-all}"
        ;;
    gunicorn)
        case "$2" in
            start) start_gunicorn ;;
            stop) pkill -f "gunicorn.*config.wsgi" ;;
            restart) pkill -f "gunicorn.*config.wsgi"; sleep 2; start_gunicorn ;;
            *) echo "Usage: $0 gunicorn [start|stop|restart]" ;;
        esac
        ;;
    celery)
        case "$2" in
            start) start_celery_worker; start_celery_beat ;;
            stop) pkill -f "celery"; ;;
            restart) pkill -f "celery"; sleep 2; start_celery_worker; start_celery_beat ;;
            worker) start_celery_worker ;;
            beat) start_celery_beat ;;
            *) echo "Usage: $0 celery [start|stop|restart|worker|beat]" ;;
        esac
        ;;
    help|--help|-h)
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  start       - Start all services"
        echo "  stop        - Stop all services"
        echo "  restart     - Restart all services"
        echo "  status      - Show service status"
        echo "  logs [service] - Show logs (gunicorn|worker|beat|all)"
        echo "  gunicorn [action] - Manage Gunicorn (start|stop|restart)"
        echo "  celery [action] - Manage Celery (start|stop|restart|worker|beat)"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start all services"
        echo "  $0 status             # Check status"
        echo "  $0 logs gunicorn      # Show Gunicorn logs"
        echo "  $0 celery worker      # Start only Celery worker"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
