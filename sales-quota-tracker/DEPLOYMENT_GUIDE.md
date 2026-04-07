# Sales Quota Tracker - Linux Server Deployment Guide

**Status**: Internal Company Deployment on Linux Server with PostgreSQL  
**Last Updated**: March 18, 2026

---

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: PostgreSQL Database Setup](#phase-1-postgresql-database-setup)
4. [Phase 2: Application Preparation](#phase-2-application-preparation)
5. [Phase 3: Gunicorn Application Server](#phase-3-gunicorn-application-server)
6. [Phase 4: Nginx Reverse Proxy](#phase-4-nginx-reverse-proxy)
7. [Phase 5: Data Migration](#phase-5-data-migration)
8. [Phase 6: Testing & Go-Live](#phase-6-testing--go-live)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Linux Server                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Nginx (Port 80/443)                                  │  │
│  │ - Reverse proxy                                      │  │
│  │ - SSL termination                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│               ↓ (forwarded to port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Gunicorn (Port 8000)                                 │  │
│  │ - Runs: Application (Streamlit + FastAPI bridge)    │  │
│  │ - Workers: 4-8 processes                             │  │
│  │ - Managed by: systemd                                │  │
│  └──────────────────────────────────────────────────────┘  │
│               ↓                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PostgreSQL (Port 5432)                               │  │
│  │ - Database server                                    │  │
│  │ - Connection pooling: pgBouncer (optional)          │  │
│  │ - Daily backups                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

✅ **Before you start, ensure you have:**

1. Linux server access (SSH)
2. `sudo` privileges
3. Minimum specs: 2GB RAM, 10GB storage (for app + database)
4. Domain name or internal IP for access

---

## PHASE 1: PostgreSQL Database Setup

### Step 1.1: Install PostgreSQL

```bash
# Update package manager
sudo apt update
sudo apt upgrade -y

# Install PostgreSQL (Ubuntu/Debian)
sudo apt install -y postgresql postgresql-contrib

# Verify installation
sudo systemctl status postgresql
```

### Step 1.2: Create Database & User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Inside psql shell, run:
CREATE USER quota_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE quota_tracker OWNER quota_user;
GRANT ALL PRIVILEGES ON DATABASE quota_tracker TO quota_user;
\q
```

### Step 1.3: Configure PostgreSQL for Remote Connections (Optional)

If your app needs to connect from a different server:

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf

# Find and uncomment:
# listen_addresses = 'localhost'
# Change to:
listen_addresses = '*'

# Save and edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add at the end:
host    quota_tracker    quota_user    127.0.0.1/32    md5
host    quota_tracker    quota_user    ::1/128         md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 1.4: Verify Database Connection

```bash
# Test connection as quota_user
psql -h localhost -U quota_user -d quota_tracker

# If successful, you'll see:
# quota_tracker=>

# Exit
\q
```

---

## PHASE 2: Application Preparation

### Step 2.1: Clone/Upload Your Application

```bash
# Create app directory
sudo mkdir -p /opt/sales-quota-tracker
cd /opt/sales-quota-tracker

# Clone from git (if available)
sudo git clone <your-repo-url> .

# Or upload via SFTP/SCP
# scp -r sales-quota-tracker/* user@server:/opt/sales-quota-tracker/
```

### Step 2.2: Set Up Python Environment

```bash
# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
cd /opt/sales-quota-tracker
sudo python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 2.3: Update requirements.txt for Production

Add these packages to `requirements.txt`:

```
# Existing packages
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
openpyxl>=3.1.2
SQLAlchemy>=2.0.0
groq>=0.1.0
google-genai>=1.67.0
msal>=1.26.0
azure-identity>=1.14.0
requests>=2.31.0

# New for production deployment
psycopg2-binary>=2.9.0
gunicorn>=21.0.0
python-dotenv>=1.0.0
```

### Step 2.4: Install Dependencies

```bash
cd /opt/sales-quota-tracker
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2.5: Create .env File

Create `.env` in `/opt/sales-quota-tracker/.env`:

```bash
sudo nano /opt/sales-quota-tracker/.env
```

Add:

```env
# Database Configuration
DATABASE_URL=postgresql://quota_user:secure_password_here@localhost:5432/quota_tracker

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8000
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
STREAMLIT_LOGGER_LEVEL=info

# Azure AD Configuration
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_REDIRECT_URI=https://your-internal-domain.com/oauth2callback

# LLM Configuration
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```

---

## PHASE 3: Gunicorn Application Server

### Step 3.1: Create Gunicorn Configuration

Create `/opt/sales-quota-tracker/gunicorn_config.py`:

```python
# Gunicorn configuration
import multiprocessing

bind = "127.0.0.1:8000"
workers = min(4, multiprocessing.cpu_count())
worker_class = "sync"
timeout = 300
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/sales-quota-tracker/access.log"
errorlog = "/var/log/sales-quota-tracker/error.log"
loglevel = "info"

# Process naming
proc_name = "sales-quota-tracker"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn-quota-tracker.pid"
umask = 0o022
user = "www-data"
group = "www-data"
```

### Step 3.2: Create Systemd Service File

Create `/etc/systemd/system/sales-quota-tracker.service`:

```bash
sudo nano /etc/systemd/system/sales-quota-tracker.service
```

Add:

```ini
[Unit]
Description=Sales Quota Tracker Application
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/sales-quota-tracker
Environment="PATH=/opt/sales-quota-tracker/venv/bin"
EnvironmentFile=/opt/sales-quota-tracker/.env
ExecStart=/opt/sales-quota-tracker/venv/bin/gunicorn \
    --config gunicorn_config.py \
    --chdir /opt/sales-quota-tracker \
    --bind 127.0.0.1:8000 \
    "streamlit.web.cli:main"

Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Step 3.3: Set Up Logging

```bash
# Create log directory
sudo mkdir -p /var/log/sales-quota-tracker
sudo chown www-data:www-data /var/log/sales-quota-tracker
sudo chmod 755 /var/log/sales-quota-tracker
```

### Step 3.4: Set Permissions

```bash
# Change ownership
sudo chown -R www-data:www-data /opt/sales-quota-tracker
sudo chmod -R 755 /opt/sales-quota-tracker
sudo chmod 600 /opt/sales-quota-tracker/.env
```

### Step 3.5: Enable & Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sales-quota-tracker

# Start the service
sudo systemctl start sales-quota-tracker

# Check status
sudo systemctl status sales-quota-tracker

# View logs
sudo journalctl -u sales-quota-tracker -f
```

---

## PHASE 4: Nginx Reverse Proxy

### Step 4.1: Install Nginx

```bash
sudo apt install -y nginx
```

### Step 4.2: Create Nginx Configuration

Create `/etc/nginx/sites-available/sales-quota-tracker`:

```bash
sudo nano /etc/nginx/sites-available/sales-quota-tracker
```

Add:

```nginx
upstream quota_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-internal-domain.com your-server-ip;
    
    # Redirect HTTP to HTTPS (optional, if you have SSL)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 50M;

    location / {
        proxy_pass http://quota_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streamlit specific headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Static files caching (if applicable)
    location ~* ^/static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Step 4.3: Enable Nginx Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/sales-quota-tracker \
    /etc/nginx/sites-enabled/sales-quota-tracker

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 4.4 (Optional): Add SSL Certificate

```bash
# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (for internal domain, you may need to use your own cert)
# For internal-only, you can use self-signed or your company's CA

# If using self-signed:
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/quota-tracker.key \
    -out /etc/ssl/certs/quota-tracker.crt

# Update Nginx config to use HTTPS
# Edit /etc/nginx/sites-available/sales-quota-tracker
# Uncomment SSL lines and restart
```

---

## PHASE 5: Data Migration

### Step 5.1: Update Database Configuration

Edit `utils/db.py`:

```python
# OLD:
# DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"
# ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)

# NEW:
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quota_user:password@localhost:5432/quota_tracker"
)

ENGINE = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db():
    """Create database tables."""
    Base.metadata.create_all(bind=ENGINE)
```

### Step 5.2: Create Migration Script

Create `migrate_sqlite_to_postgres.py` locally first to migrate existing data:

```python
"""
Migration script: SQLite → PostgreSQL
Run this locally on your dev machine before deploying
"""

import sqlite3
import pandas as pd
import psycopg2
from utils.models import *  # Import all models
from utils.db import Base, SESSION

# Read from SQLite
sqlite_conn = sqlite3.connect("data/app.db")

tables_to_migrate = [
    'quotas',
    'clients',
    'billing_transactions',
    'derived_metrics'
]

for table in tables_to_migrate:
    try:
        df = pd.read_sql_table(table, sqlite_conn)
        print(f"Migrating {table}: {len(df)} rows...")
        
        # Insert into PostgreSQL
        df.to_sql(table, ENGINE, if_exists='append', index=False)
    except Exception as e:
        print(f"Skipped {table}: {e}")

sqlite_conn.close()
print("Migration complete!")
```

### Step 5.3: Run Migrations on Server

```bash
# SSH into server
ssh user@server

# Activate venv
cd /opt/sales-quota-tracker
source venv/bin/activate

# Run migration script
python migrate_sqlite_to_postgres.py

# Initialize database schema
python -c "from utils.db import init_db; init_db()"
```

---

## PHASE 6: Testing & Go-Live

### Step 6.1: Test Application

```bash
# Check if app is running
sudo systemctl status sales-quota-tracker

# Test from browser
# Visit: http://your-server-ip or http://your-internal-domain.com

# Check logs if issues
sudo journalctl -u sales-quota-tracker -n 50 -f
```

### Step 6.2: Verify Database Connection

```bash
# SSH into server
ssh user@server
cd /opt/sales-quota-tracker
source venv/bin/activate
python -c "from utils.db import ENGINE; print(ENGINE.execute('SELECT 1'))"
```

### Step 6.3: Performance Testing

```bash
# Load testing (optional)
# Install Apache Bench
sudo apt install -y apache2-utils

# Simple load test
ab -n 100 -c 10 http://your-server-ip/
```

### Step 6.4: Set Up Monitoring

```bash
# Monitor app status
sudo systemctl status sales-quota-tracker

# Monitor logs in real-time
sudo journalctl -u sales-quota-tracker -f

# Monitor Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Where logs are written

- **App logs (Streamlit/Gunicorn)**: `logs/app.log` (created automatically by the app code)
- **Gunicorn logs**: `/var/log/sales-quota-tracker/access.log` and `/var/log/sales-quota-tracker/error.log` (if configured)
- **System logs**: `journalctl -u sales-quota-tracker`

### Issue: Application won't start

```bash
# Check logs
sudo journalctl -u sales-quota-tracker -n 100

# Check if port 8000 is in use
sudo lsof -i :8000

# Test Gunicorn manually
cd /opt/sales-quota-tracker
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 --workers 2 "streamlit.web.cli:main"
```

### Issue: Database connection errors

```bash
# Test PostgreSQL connection
sudo -u postgres psql -d quota_tracker -U quota_user -h localhost

# Check PostgreSQL service
sudo systemctl status postgresql

# Check if database exists
sudo -u postgres psql -l | grep quota_tracker

# Check user permissions
sudo -u postgres psql -c "GRANT ALL ON DATABASE quota_tracker TO quota_user;"
```

### Issue: Nginx 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status sales-quota-tracker

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Verify Nginx config
sudo nginx -t

# Restart both services
sudo systemctl restart sales-quota-tracker
sudo systemctl restart nginx
```

### Issue: SSL/HTTPS problems

```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/quota-tracker.crt -text -noout

# Check if running on correct port
sudo lsof -i :443

# Restart Nginx
sudo systemctl restart nginx
```

---

## Maintenance Tasks

### Daily Backup

Create `/usr/local/bin/backup-quota-tracker.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/quota-tracker"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="quota_tracker"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
sudo -u postgres pg_dump $DB_NAME | gzip > $BACKUP_DIR/quota_tracker_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "quota_tracker_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/quota_tracker_$TIMESTAMP.sql.gz"
```

Schedule with cron:

```bash
sudo crontab -e

# Add line:
0 2 * * * /usr/local/bin/backup-quota-tracker.sh
```

### Monitor Service Health

```bash
# Check if service is active
sudo systemctl is-active sales-quota-tracker

# Restart if needed
sudo systemctl restart sales-quota-tracker

# View real-time resource usage
top -p $(pgrep -f gunicorn | head -1)
```

---

## Deployment Checklist

- [ ] Linux server access confirmed
- [ ] PostgreSQL installed & database created
- [ ] Application directory created
- [ ] Python venv set up
- [ ] Dependencies installed
- [ ] `.env` file created with all credentials
- [ ] `utils/db.py` updated to use PostgreSQL
- [ ] Gunicorn configuration created
- [ ] Systemd service file created
- [ ] Nginx reverse proxy configured
- [ ] SSL certificates installed (if needed)
- [ ] Data migrated from SQLite to PostgreSQL
- [ ] Application tested and accessible
- [ ] Monitoring & logging configured
- [ ] Backup script created
- [ ] Team trained on new URL & credentials
- [ ] Go-live documentation prepared

---

**Next Steps:**  
Review this plan with your infrastructure team and let me know:
1. Which phase to start with
2. Server details (IP, hostname, user accounts)
3. Any specific security requirements
4. Backup & disaster recovery preferences
