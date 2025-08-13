# ClinicHub - Alpine Docker Deployment

![ClinicHub](https://img.shields.io/badge/ClinicHub-v1.0.0-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Alpine-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4-green.svg)

A comprehensive, self-hosted medical practice management system optimized for Alpine Docker environments.

## 🏥 Features

### Core Medical Functionality
- **Patient Management** - Complete patient records and demographics
- **Appointment Scheduling** - Efficient appointment booking and management
- **Electronic Health Records (EHR)** - Comprehensive medical record keeping
- **Staff Management** - Employee and provider management
- **Dashboard & Analytics** - Real-time practice insights

### Technical Features
- **Alpine Linux Optimized** - Lightweight, secure containers
- **Self-Hosted** - Complete control over your medical data
- **HIPAA Compliance Ready** - Security headers and encrypted communications
- **Responsive Design** - Works on desktop, tablet, and mobile
- **RESTful API** - Complete API with auto-generated documentation

## 🚀 Quick Start

### Prerequisites
- Docker (20.10+)
- Docker Compose (2.0+)
- 2GB free disk space
- Ports 80, 3000, 8001 available

### Installation

1. **Download and extract the deployment package**
   ```bash
   # Extract the clinichub-alpine-deployment.zip
   unzip clinichub-alpine-deployment.zip
   cd clinichub-alpine-deployment
   ```

2. **Run the automated deployment script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Access ClinicHub**
   - **Web Interface**: http://localhost
   - **Direct Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8001/docs

4. **Login**
   - **Username**: `admin`
   - **Password**: `admin123`

## 📋 Manual Deployment

If you prefer manual deployment:

```bash
# 1. Create data directories
mkdir -p data/mongodb data/backend/logs backups

# 2. Build and start containers
docker-compose build
docker-compose up -d

# 3. Wait for services to initialize
sleep 30

# 4. Check service health
docker-compose ps
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│                 Nginx                   │
│         (Reverse Proxy/SSL)             │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐         ┌────▼────┐
│Frontend│         │ Backend │
│React 18│◄────────┤FastAPI  │
│Node.js │         │Python   │
└────────┘         └────┬────┘
                        │
                   ┌────▼────┐
                   │MongoDB  │
                   │  4.4    │
                   └─────────┘
```

## 🔧 Configuration

### Environment Variables

**Backend** (automatically configured):
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name (clinichub)
- `SECRET_KEY`: JWT secret key
- `HOST`: Server host (0.0.0.0)
- `PORT`: Server port (8001)

**Frontend** (automatically configured):
- `REACT_APP_BACKEND_URL`: Backend API URL

### Custom Configuration

1. **Database Settings**: Modify `docker-compose.yml` MongoDB section
2. **SSL Certificates**: Place certificates in `nginx/ssl/`
3. **Nginx Config**: Modify `nginx/nginx.conf`
4. **Backend Settings**: Update environment variables in `docker-compose.yml`

## 📊 Usage

### Default Login
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change the default password immediately after first login**

### API Documentation
Access the auto-generated API documentation at: http://localhost:8001/docs

### Sample Data
The system includes sample data:
- 2 sample patients
- 2 sample healthcare providers
- Database indexes for optimal performance

## 🛠️ Management Commands

```bash
# View logs
docker-compose logs [service_name]

# Restart specific service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# View running containers
docker-compose ps

# Access container shell
docker-compose exec [service_name] sh
```

## 🔒 Security

### Built-in Security Features
- **Security Headers**: X-Frame-Options, X-XSS-Protection, etc.
- **Rate Limiting**: API and login endpoint protection
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Pydantic model validation
- **CORS Protection**: Configurable cross-origin requests

### Production Security Checklist
- [ ] Change default admin password
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Configure backup encryption
- [ ] Review nginx security headers
- [ ] Enable audit logging
- [ ] Set up monitoring

## 📦 Backup & Recovery

### Automatic Backups
Backup directories are created at:
- `./data/mongodb/` - Database files
- `./data/backend/logs/` - Application logs
- `./backups/` - Manual backup storage

### Manual Backup
```bash
# Create database backup
docker-compose exec mongodb mongodump --out /tmp/backup
docker-compose cp mongodb:/tmp/backup ./backups/$(date +%Y%m%d-%H%M%S)
```

### Restore from Backup
```bash
# Restore database
docker-compose exec mongodb mongorestore /tmp/backup/clinichub
```

## 🐛 Troubleshooting

### Common Issues

**Port Conflicts**:
```bash
# Check which process is using a port
lsof -i :80
lsof -i :3000
lsof -i :8001
```

**Container Won't Start**:
```bash
# View container logs
docker-compose logs [service_name]

# Check container status
docker-compose ps
```

**Database Connection Issues**:
```bash
# Check MongoDB logs
docker-compose logs mongodb

# Test MongoDB connection
docker-compose exec mongodb mongosh clinichub --eval "db.patients.find()"
```

**Permission Issues**:
```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) data/
chmod -R 755 data/
```

### Health Checks
```bash
# Backend health
curl http://localhost:8001/api/health

# Frontend health  
curl http://localhost:3000

# Nginx health
curl http://localhost
```

## 🔄 Updates & Maintenance

### Update ClinicHub
1. Stop services: `docker-compose down`
2. Backup data: `cp -r data/ backups/backup-$(date +%Y%m%d)/`
3. Update files from new release
4. Rebuild: `docker-compose build --no-cache`
5. Start: `docker-compose up -d`

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# View database performance
docker-compose exec mongodb mongosh --eval "db.serverStatus()"
```

## 📝 API Reference

### Authentication
```bash
# Login
curl -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Patients
```bash
# Get patients
curl -X GET "http://localhost:8001/api/patients" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create patient
curl -X POST "http://localhost:8001/api/patients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com","phone":"555-0123","date_of_birth":"1990-01-01","gender":"Male"}'
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support and questions:
- **Documentation**: Check this README and API docs at `/docs`
- **Logs**: Check `docker-compose logs` for error details
- **Health Checks**: Use `/api/health` endpoint for system status

## 🏥 Happy Practicing!

ClinicHub is designed to streamline your medical practice management while keeping your data secure and under your control.

---

**ClinicHub v1.0.0** - Alpine Docker Deployment
*Comprehensive Medical Practice Management System*