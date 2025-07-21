# 🏥 ClinicHub - Synology NAS Deployment Guide

**Complete medical practice management system with Synology DSM single sign-on integration**

## 🚀 Quick Deployment on Synology NAS

### Prerequisites

1. **Synology NAS Requirements:**
   - DSM 7.0+ recommended
   - 4GB+ RAM (8GB recommended for larger practices)
   - Docker Package installed from Package Center
   - SSH enabled (Control Panel > Terminal & SNMP > Enable SSH service)

2. **Network Requirements:**
   - Static IP address for your NAS
   - Ports 80, 443, 3000, 8001 available
   - SSL certificate (optional but recommended for HIPAA compliance)

### 🎯 One-Command Deployment

```bash
# SSH into your Synology NAS
ssh admin@YOUR-NAS-IP

# Clone the repository
sudo git clone https://github.com/your-username/clinichub.git /volume1/docker/clinichub-source
cd /volume1/docker/clinichub-source

# Run the automated deployment script
./deploy-synology.sh
```

The script will:
- ✅ Configure directory structure on your volume
- ✅ Set up Docker containers with persistent data
- ✅ Configure Synology DSM SSO integration
- ✅ Set up HTTPS with your SSL certificates
- ✅ Initialize the medical database
- ✅ Test all integrations

## 🔐 Synology SSO Configuration

### Step 1: Enable SSO in ClinicHub
1. Login to ClinicHub: `https://YOUR-NAS-IP:3000`
2. Go to **System Settings** → **Authentication**
3. Enable **Synology DSM Integration**
4. Configure DSM URL: `https://YOUR-NAS-IP:5001`

### Step 2: User Management
- **DSM Users** automatically get ClinicHub access based on groups
- **Role Mapping:**
  - DSM `administrators` → ClinicHub `admin`
  - DSM `medical_staff` → ClinicHub `doctor`/`nurse`
  - DSM `office_staff` → ClinicHub `receptionist`/`manager`

### Step 3: Group Setup in DSM
1. Control Panel → User & Group → Group
2. Create groups: `medical_staff`, `office_staff`
3. Assign users to appropriate groups

## 📁 Data Storage Structure

```
/volume1/docker/clinichub/
├── mongodb/              # Patient data, medical records
├── backend/logs/         # Application logs
├── nginx/ssl/           # SSL certificates
└── backups/             # Automated backups
```

## 🛡️ HIPAA Compliance Features

### Security Measures Enabled:
- ✅ **Encryption at Rest**: MongoDB with encrypted volumes
- ✅ **Encryption in Transit**: HTTPS/TLS for all communications
- ✅ **Access Controls**: Synology RBAC integration
- ✅ **Audit Logging**: All user actions logged
- ✅ **Session Management**: Automatic timeouts
- ✅ **Data Backup**: Automated encrypted backups

### Security Headers:
- Strict-Transport-Security
- X-Frame-Options: DENY
- Content-Security-Policy
- X-Content-Type-Options: nosniff

## 🔧 Management Commands

### Service Management
```bash
# Start ClinicHub
cd /volume1/docker/clinichub-source
docker-compose -f docker-compose.synology.yml up -d

# Stop ClinicHub  
docker-compose -f docker-compose.synology.yml down

# View logs
docker-compose -f docker-compose.synology.yml logs backend
docker-compose -f docker-compose.synology.yml logs frontend

# Update ClinicHub
git pull origin main
docker-compose -f docker-compose.synology.yml build --no-cache
docker-compose -f docker-compose.synology.yml up -d
```

### Database Management
```bash
# Backup database
docker exec clinichub-mongodb mongodump --uri="mongodb://admin:ClinicHub2024!Secure@localhost:27017/clinichub?authSource=admin" --out /data/db/backup-$(date +%Y%m%d)

# Restore database
docker exec clinichub-mongodb mongorestore --uri="mongodb://admin:ClinicHub2024!Secure@localhost:27017/clinichub?authSource=admin" /data/db/backup-YYYYMMDD/clinichub/
```

## 🌐 Advanced Features

### 1. **Complete Clinical Workflow**
- SOAP Notes → Auto Invoice → Inventory Deduction → Staff Tracking
- Electronic Prescribing with drug interactions
- Lab integration with LOINC codes
- Insurance verification and prior authorization

### 2. **Practice Automation**
```
Patient Visit → SOAP Note → Medication/Supply Used → 
→ Auto Receipt → Inventory Updated → Staff Activity Logged
```

### 3. **Synology Integration Benefits**
- **Single Sign-On**: Use DSM credentials for ClinicHub
- **File Station**: Direct access to medical documents
- **Surveillance Station**: Optional security integration
- **Cloud Sync**: Automated HIPAA-compliant backups

## 📊 System Monitoring

### Health Checks
- Backend: `https://YOUR-NAS-IP:8001/api/health`
- Frontend: `https://YOUR-NAS-IP:3000`
- Database: MongoDB connection test via backend API

### Performance Monitoring
- View Docker container stats: `docker stats`
- Monitor disk usage: `df -h /volume1/docker/clinichub/`
- Check memory usage: `free -h`

## 🆘 Troubleshooting

### Common Issues

**1. SSO Not Working**
```bash
# Check Synology API access
curl -k "https://YOUR-NAS-IP:5001/webapi/auth.cgi?api=SYNO.API.Auth&version=3&method=login&account=admin&passwd=YOUR-PASSWORD"

# Check ClinicHub logs
docker-compose -f docker-compose.synology.yml logs backend | grep -i synology
```

**2. Database Connection Issues**
```bash
# Test MongoDB connection
docker exec clinichub-mongodb mongosh --eval "db.adminCommand('ismaster')"

# Reset database (WARNING: This deletes all data)
docker-compose -f docker-compose.synology.yml down -v
docker-compose -f docker-compose.synology.yml up -d
```

**3. SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in /usr/local/etc/certificate/ReverseProxyHttps/YOUR-CERT/cert.pem -text -noout

# Test HTTPS connectivity
curl -k https://YOUR-NAS-IP:443
```

### Log Locations
- **Backend**: `/volume1/docker/clinichub/backend/logs/`
- **Frontend**: `docker logs clinichub-frontend`
- **Database**: `docker logs clinichub-mongodb`
- **Nginx**: `docker logs clinichub-nginx`

## 📞 Support

### Documentation
- [Full API Documentation](https://YOUR-NAS-IP:8001/docs)
- [Installation Troubleshooting](INSTALLATION.md)
- [HIPAA Compliance Guide](docs/HIPAA.md)

### Community
- [GitHub Issues](https://github.com/your-username/clinichub/issues)
- [Synology Community Forums](https://community.synology.com/)

---

**🏥 ClinicHub** - Self-hosted Medical Practice Management  
*Designed for Synology NAS with enterprise-grade security and HIPAA compliance*