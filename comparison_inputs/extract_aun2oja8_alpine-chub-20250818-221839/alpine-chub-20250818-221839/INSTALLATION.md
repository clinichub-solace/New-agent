# ClinicHub Installation Guide

## 🏥 Medical Practice Management System

ClinicHub is a comprehensive, self-hosted medical practice management system featuring EHR, Lab Integration, Insurance Verification, and more.

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Installation](#manual-installation)
- [Demo Data Setup](#demo-data-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## 💻 System Requirements

### Minimum Requirements:
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB available space
- **CPU**: 2 cores minimum, 4 cores recommended

### Software Dependencies:
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- Git

---

## 🐳 Quick Start (Docker)

**Fastest way to get ClinicHub running:**

```bash
# 1. Clone repository
git clone https://github.com/[your-username]/clinichub.git
cd clinichub

# 2. Start with Docker Compose
docker-compose up -d

# 3. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# Default login: admin / admin123
```

### Docker Requirements:
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 🔧 Manual Installation

### Step 1: Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mongodb git curl

# Install Yarn (recommended)
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update && sudo apt install yarn
```

#### CentOS/RHEL/Fedora:
```bash
# CentOS/RHEL 8+
sudo dnf install -y python3 python3-pip nodejs npm mongodb-server git curl

# Fedora
sudo dnf install -y python3 python3-pip nodejs npm mongodb git curl

# Install Yarn
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
sudo dnf install yarn
```

### Step 2: Clone Repository
```bash
git clone https://github.com/[your-username]/clinichub.git
cd clinichub
```

### Step 3: Database Setup
```bash
# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify MongoDB is running
sudo systemctl status mongod

# Create database (optional - will auto-create)
mongo
> use clinichub
> exit
```

### Step 4: Backend Setup
```bash
cd backend/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Edit .env file with your settings
nano .env
```

#### Backend Environment Configuration (.env):
```env
# Database
MONGO_URL=mongodb://localhost:27017/clinichub

# Security
SECRET_KEY=your-super-secure-secret-key-here-change-this
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8001

# Optional: External API Keys (for production)
# STRIPE_SECRET_KEY=sk_test_...
# TWILIO_ACCOUNT_SID=AC...
# SENDGRID_API_KEY=SG...
```

```bash
# Start backend server
python server.py

# Backend should be running at http://localhost:8001
```

### Step 5: Frontend Setup
```bash
# Open new terminal
cd frontend/

# Install Node.js dependencies
yarn install
# or: npm install

# Configure environment variables
cp .env.example .env

# Edit frontend .env
nano .env
```

#### Frontend Environment Configuration (.env):
```env
REACT_APP_BACKEND_URL=http://localhost:8001/api
REACT_APP_APP_NAME=ClinicHub
REACT_APP_VERSION=1.0.0
```

```bash
# Start frontend development server
yarn start
# or: npm start

# Frontend should open at http://localhost:3000
```

### Step 6: Initial Login
```
URL: http://localhost:3000
Username: admin
Password: admin123
```

---

## 🎯 Demo Data Setup

Initialize the system with comprehensive demo data:

### Option 1: Via API (Recommended)
```bash
# With backend running, initialize demo data
cd backend/
python -c "
import requests
import json

# Login and get token
response = requests.post('http://localhost:8001/api/auth/login', 
    data={'username': 'admin', 'password': 'admin123'})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Initialize all demo data
endpoints = [
    '/api/lab-tests/init',
    '/api/icd10/init', 
    '/api/erx/init',
    '/api/system/init-appointment-types',
    '/api/communications/init-templates',
    '/api/forms/templates/init-compliant'
]

for endpoint in endpoints:
    resp = requests.post(f'http://localhost:8001{endpoint}', headers=headers)
    print(f'{endpoint}: {resp.status_code}')

print('Demo data initialized!')
"
```

### Option 2: Via Test Script
```bash
cd backend/
python backend_test.py --init-demo
```

### What Demo Data Includes:
- ✅ 8 realistic demo patients
- ✅ 4 healthcare providers
- ✅ Sample medical encounters
- ✅ Lab tests with LOINC codes
- ✅ ICD-10 diagnosis codes
- ✅ Insurance cards and eligibility data
- ✅ Sample invoices and payments
- ✅ HIPAA-compliant forms
- ✅ Communication templates

---

## 🚀 Production Deployment

### Security Hardening
```bash
# 1. Change default credentials
# Login to app and create new admin user, disable default admin

# 2. Generate secure secret keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(50))"

# 3. Update .env files with secure keys
```

### SSL/HTTPS Setup
```bash
# Install Nginx
sudo apt install nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/clinichub
```

#### Nginx Configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/clinichub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Systemd Services
Create service files for auto-start:

#### Backend Service:
```bash
sudo nano /etc/systemd/system/clinichub-backend.service
```

```ini
[Unit]
Description=ClinicHub Backend
After=network.target mongod.service

[Service]
Type=simple
User=clinichub
WorkingDirectory=/opt/clinichub/backend
Environment=PATH=/opt/clinichub/backend/venv/bin
ExecStart=/opt/clinichub/backend/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Frontend Service:
```bash
sudo nano /etc/systemd/system/clinichub-frontend.service
```

```ini
[Unit]
Description=ClinicHub Frontend
After=network.target

[Service]
Type=simple
User=clinichub
WorkingDirectory=/opt/clinichub/frontend
ExecStart=/usr/bin/yarn start
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl enable clinichub-backend clinichub-frontend
sudo systemctl start clinichub-backend clinichub-frontend
```

### Database Backups
```bash
# Create backup script
sudo nano /opt/clinichub/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/clinichub/backups"
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db clinichub --out $BACKUP_DIR/clinichub_$DATE

# Compress backup
tar -czf $BACKUP_DIR/clinichub_$DATE.tar.gz $BACKUP_DIR/clinichub_$DATE
rm -rf $BACKUP_DIR/clinichub_$DATE

# Keep only last 30 backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: clinichub_$DATE.tar.gz"
```

```bash
# Make executable and add to cron
chmod +x /opt/clinichub/backup.sh
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/clinichub/backup.sh
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error
```bash
# Check MongoDB status
sudo systemctl status mongod

# Restart MongoDB
sudo systemctl restart mongod

# Check logs
sudo journalctl -u mongod
```

#### 2. Port Already in Use
```bash
# Check what's using port 3000/8001
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8001

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:3000)
```

#### 3. Frontend Build Errors
```bash
# Clear cache and reinstall
cd frontend/
rm -rf node_modules package-lock.json yarn.lock
yarn install
yarn start
```

#### 4. Python Dependencies Issues
```bash
# Reinstall in virtual environment
cd backend/
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Permission Errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER /path/to/clinichub
chmod -R 755 /path/to/clinichub
```

### Log Locations
```bash
# Application logs
tail -f backend/logs/app.log
tail -f frontend/logs/console.log

# System logs
sudo journalctl -u clinichub-backend -f
sudo journalctl -u clinichub-frontend -f
sudo journalctl -u mongod -f
```

---

## 📞 Support

### Getting Help
- **Documentation**: Check project README and Wiki
- **Issues**: Create GitHub issue for bugs/feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [your-email@domain.com]

### Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request
4. Follow coding standards

### License
This project is licensed under [Your License] - see LICENSE file for details.

---

## 🎉 Success!

If you've followed this guide, you should now have:

✅ **ClinicHub running locally**  
✅ **Demo data populated**  
✅ **All modules functional**  
✅ **Ready for customization**  

**Next Steps:**
1. Explore all modules in the dashboard
2. Create your first real patient
3. Customize forms and templates
4. Configure external integrations
5. Deploy to production server

**Welcome to ClinicHub!** 🏥✨

---

*Last updated: [Current Date]*
*Version: 1.0.0*