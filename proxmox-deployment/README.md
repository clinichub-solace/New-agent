# 🏥 ClinicHub Proxmox Deployment Guide

Complete self-hosted EHR system deployment for Proxmox environments.

## 🚀 Quick Start

### Prerequisites
- Debian 12 VM (2 vCPU, 4-8 GB RAM)
- Static IP configured
- Domain pointing to your server
- Ports 80/443 forwarded

### 1. Server Setup
```bash
# Update system
apt update && apt -y install curl ca-certificates gnupg ufw

# Install Docker
curl -fsSL https://get.docker.com | sh
apt -y install docker-compose-plugin
usermod -aG docker $USER

# Logout and login to apply docker group
```

### 2. Deployment
```bash
# Clone/copy the deployment files to your server
mkdir -p /opt/clinichub
cd /opt/clinichub

# Copy all files from proxmox-deployment/ to this directory
# - docker-compose.yml
# - Caddyfile  
# - .env.example
# - etc.

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Build and deploy
./build.sh
docker compose up -d
```

### 3. Verification
```bash
# Check services
docker compose ps

# Test endpoints
curl -i https://yourdomain.com
curl -i https://yourdomain.com/api/health
curl -i https://yourdomain.com/api/auth/synology-status
```

## 🔧 Configuration

### Required Environment Variables
```bash
# Domain
DOMAIN=clinichub.yourdomain.com
FRONTEND_ORIGIN=https://clinichub.yourdomain.com

# Database  
MONGO_ROOT_PASSWORD=super_secure_password

# Security
SECRET_KEY=64_character_random_string
JWT_SECRET_KEY=32_character_random_string
```

### Optional Features
```bash
# AI Medical Assistant
EMERGENT_LLM_KEY=sk-emergent-xxxxx

# Email Integration
SMTP_HOST=smtp.yourdomain.com
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=smtp_password

# Synology Integration  
SYNOLOGY_URL=https://your-nas.local:5001
SYNOLOGY_USERNAME=admin
SYNOLOGY_PASSWORD=password
```

## 🏗️ Architecture

```
Internet → Caddy (80/443) → Backend (8001) + Frontend (Static)
                          ↓
                       MongoDB (27017)
```

### Services
- **Caddy**: Reverse proxy with automatic HTTPS
- **Backend**: FastAPI application (274+ endpoints)
- **Frontend**: React SPA (production build)
- **MongoDB**: Database with authentication

## 📊 Features Included

### Core EHR System
- ✅ **Patient Management**: Demographics, charts, history
- ✅ **Clinical Documentation**: SOAP notes, encounters, vitals
- ✅ **Electronic Prescribing**: eRx with formulary support
- ✅ **Appointment Scheduling**: Calendar integration
- ✅ **Telehealth**: Video consultation ready

### Practice Management
- ✅ **Billing**: Automated SOAP→Receipt generation
- ✅ **Inventory**: Auto-deduction on payment
- ✅ **Payroll**: Integrated staff management
- ✅ **Reports**: Financial, clinical, compliance
- ✅ **Communication**: Email, fax, VoIP ready

### Advanced Features
- ✅ **Dynamic Forms**: AI-powered form generation
- ✅ **Audit Logging**: Complete compliance trail
- ✅ **Real-time Notifications**: System-wide alerts
- ✅ **Clinical Templates**: Customizable protocols
- ✅ **Multi-location**: Enterprise ready

## 🔐 Security

### Built-in Security
- HTTPS/TLS encryption (automatic certificates)
- JWT authentication
- Role-based access control (RBAC)
- HIPAA-compliant audit logging
- Security headers (HSTS, XSS protection, etc.)

### Network Security
```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp  
ufw enable

# Optional: Fail2ban for intrusion prevention
apt install fail2ban
```

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl https://yourdomain.com/api/health

# Container status  
docker compose ps
docker compose logs -f backend
```

### Backups
```bash
# Database backup
docker exec clinichub-mongo mongodump --out /backup

# Full backup script (customize as needed)
tar -czf clinichub-backup-$(date +%Y%m%d).tar.gz /opt/clinichub
```

### Updates
```bash
# Pull latest changes
git pull  # or copy new files

# Rebuild and restart
./build.sh
docker compose down
docker compose up -d
```

## 🆚 Competitive Advantage

| Feature | ClinicHub | Dr. Chrono | Tebra | Practice Fusion |
|---------|-----------|------------|-------|-----------------|
| **Monthly Cost** | $0 | $199-1200 | $300-500 | $500+ |
| **Self-hosted** | ✅ | ❌ | ❌ | ❌ |
| **Complete EHR** | ✅ | ✅ | ✅ | ✅ |
| **Telehealth** | ✅ | $349+ | Extra | 3rd party |
| **Payroll** | ✅ | ❌ | ❌ | ❌ |
| **Inventory** | ✅ Auto | ❌ | Limited | ❌ |
| **API Access** | ✅ Full | Limited | Limited | Enterprise |
| **Data Control** | ✅ Complete | ❌ | ❌ | ❌ |

**Annual Savings: $8,000-14,400 per provider!**

## 🐛 Troubleshooting

### Common Issues

**502 Bad Gateway**
```bash
# Check backend status
docker compose logs backend
curl http://localhost:8001/api/health
```

**Database Connection Failed**
```bash
# Check MongoDB status
docker compose logs mongodb
docker exec -it clinichub-mongo mongosh
```

**CORS Errors**
```bash
# Verify FRONTEND_ORIGIN in .env matches your domain
grep FRONTEND_ORIGIN .env
```

**SSL Certificate Issues**
```bash
# Check Caddy logs
docker compose logs proxy
# Caddy handles certificates automatically
```

## 📞 Support

- **Documentation**: Check logs and health endpoints
- **Community**: GitHub Issues (if open source)
- **Professional**: Contact for enterprise support options

---

**🏥 ClinicHub: Professional EHR system that saves practices $8K-14K annually while providing enterprise-grade features and complete data control.**