# Deployment Checklist

Use this checklist to ensure a successful deployment of the Music Charts AI application.

## Pre-Deployment

- [ ] Ubuntu 22.04 server ready
- [ ] Domain name configured and pointing to server
- [ ] SSH access to server
- [ ] PostgreSQL database created and configured
- [ ] Redis server installed and running
- [ ] SSL certificates obtained (Let's Encrypt or own certificates)
- [ ] Environment variables prepared
- [ ] Application code ready for deployment

## Server Setup

- [ ] Create application user (`musiccharts`)
- [ ] Install system dependencies (Python, Node.js, Apache2, etc.)
- [ ] Configure PostgreSQL database and user
- [ ] Setup Redis server
- [ ] Configure firewall (UFW)

## Application Deployment

- [ ] Upload application code to server
- [ ] Create and configure `.env` file
- [ ] Run deployment script: `./deploy.sh deploy`
- [ ] Verify Python virtual environment setup
- [ ] Confirm frontend build completed
- [ ] Run Django migrations
- [ ] Collect static files

## Service Configuration

- [ ] Gunicorn configuration created
- [ ] Systemd services configured
- [ ] Apache virtual host configured
- [ ] SSL certificates configured
- [ ] All services started and enabled

## Post-Deployment Verification

- [ ] All services running (`./deploy.sh status`)
- [ ] Health check passed (`./deploy.sh health`)
- [ ] Application accessible via domain
- [ ] Admin interface accessible
- [ ] Static files loading correctly
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Celery tasks working
- [ ] SSL certificate valid
- [ ] Firewall configured correctly

## Security Checklist

- [ ] File permissions set correctly
- [ ] Environment variables secured
- [ ] SSL configuration secure
- [ ] Firewall rules configured
- [ ] Regular user created (not root)
- [ ] Sensitive files not world-readable
- [ ] Database credentials secure

## Monitoring Setup

- [ ] Log files accessible and readable
- [ ] Backup strategy implemented
- [ ] Monitoring tools configured (optional)
- [ ] Health check endpoints working
- [ ] Error logging configured

## Documentation

- [ ] Deployment documentation updated
- [ ] Configuration files documented
- [ ] Troubleshooting guide accessible
- [ ] Contact information available

## Final Tests

- [ ] Application loads correctly
- [ ] User registration/login works
- [ ] Admin interface functional
- [ ] API endpoints responding
- [ ] File uploads working
- [ ] Background tasks processing
- [ ] Email functionality working (if configured)

## Maintenance Tasks

- [ ] Backup scripts scheduled
- [ ] Update procedures documented
- [ ] Monitoring alerts configured
- [ ] Performance optimization completed
- [ ] Security updates scheduled

---

## Quick Commands Reference

```bash
# Check deployment status
./deploy.sh status

# View logs
./deploy.sh logs

# Restart services
./deploy.sh restart

# Health check
./deploy.sh health

# Create backup
./deploy.sh backup

# Check service status
sudo systemctl status musiccharts-gunicorn musiccharts-celery musiccharts-celerybeat apache2

# View application logs
sudo tail -f /var/log/musiccharts/gunicorn-error.log

# Test Django application
sudo -u musiccharts /opt/musiccharts/venv/bin/python /opt/musiccharts/app/manage.py check
```

## Emergency Contacts

- System Administrator: [Your contact info]
- Development Team: [Team contact info]
- Hosting Provider: [Provider support info]

---

**Note**: Keep this checklist updated as your deployment process evolves. Store it in a secure location accessible to your team.
