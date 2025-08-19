# ClinicHub Communication Infrastructure Integration Guide

## Overview

This guide covers the deployment and integration of ClinicHub's self-hosted communication infrastructure, consisting of:

- **Mailu** - Complete email server (SMTP, IMAP, webmail)
- **HylaFAX+** - Self-hosted fax server
- **FreeSWITCH** - Open-source VoIP platform
- **Communication Gateway** - Unified API for ClinicHub integration

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ClinicHub     │    │  Communication   │    │  Mail/Fax/VoIP  │
│   Backend       │◄──►│    Gateway       │◄──►│    Services     │
│   (Port 8001)   │    │  (Port 8100)     │    │   (Various)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                                               ▲
         │                                               │
         ▼                                               ▼
┌─────────────────┐                          ┌─────────────────┐
│   Synology      │                          │   Patient       │
│   DSM Portal    │                          │ Communications  │
│   (SSO Login)   │                          │ (Email/Fax)     │
└─────────────────┘                          └─────────────────┘
```

## Deployment Options

### Option 1: Synology NAS Deployment (Recommended)

1. **Prerequisites:**
   - Synology NAS with Docker support
   - Static IP or DDNS configured
   - Domain name for email services
   - Ports 25, 587, 993, 8080, 8100 available

2. **Installation Steps:**
   ```bash
   # Copy infrastructure directory to NAS
   scp -r infrastructure/ admin@your-nas:/volume1/docker/clinichub/
   
   # SSH into NAS
   ssh admin@your-nas
   
   # Navigate to infrastructure directory
   cd /volume1/docker/clinichub/infrastructure/
   
   # Set configuration
   export DOMAIN="yourdomain.com"
   export ADMIN_EMAIL="admin@yourdomain.com"
   
   # Deploy
   ./deploy.sh
   ```

3. **DNS Configuration:**
   ```
   # MX Record
   yourdomain.com.    IN  MX  10  mail.yourdomain.com.
   
   # A Records
   mail.yourdomain.com.     IN  A   YOUR_PUBLIC_IP
   webmail.yourdomain.com.  IN  A   YOUR_PUBLIC_IP
   
   # SPF Record
   yourdomain.com.    IN  TXT "v=spf1 mx ~all"
   
   # DMARC Record
   _dmarc.yourdomain.com.  IN  TXT "v=DMARC1; p=quarantine; rua=mailto:admin@yourdomain.com"
   ```

### Option 2: Linux Server Deployment

1. **Prerequisites:**
   - Ubuntu/Debian server
   - Docker and Docker Compose installed
   - Firewall configured for email ports

2. **Installation:**
   ```bash
   # Clone or copy infrastructure
   git clone https://github.com/your-repo/clinichub-infrastructure.git
   cd clinichub-infrastructure
   
   # Configure environment
   cp mailu/mailu.env.example mailu/mailu.env
   # Edit mailu.env with your settings
   
   # Deploy
   ./deploy.sh
   ```

## Service Configuration

### Mailu Email Server

**Admin Interface:** `http://your-server:8080/admin`

**Initial Setup:**
1. Access admin interface
2. Create initial admin user
3. Add email domains
4. Create user accounts for staff
5. Configure DKIM signing
6. Set up spam filtering rules

**HIPAA Compliance Features:**
- Email encryption at rest
- Audit logging enabled
- Secure password policies
- Session timeout controls
- Message retention policies (7 years)

### HylaFAX+ Fax Server

**Configuration:**
- Automatic fax-to-email delivery
- Email-to-fax gateway
- Fax queue management
- Integration with document management

**Usage:**
```python
# Send fax via API
import requests

fax_data = {
    "to_number": "+1234567890",
    "document_path": "/documents/lab_result.pdf",
    "patient_id": "patient_123",
    "priority": "high"
}

response = requests.post("http://gateway:8100/fax/send", json=fax_data)
```

### FreeSWITCH VoIP

**Features:**
- SIP phone integration
- Call recording
- IVR (Interactive Voice Response)
- Voicemail to email
- Conference calling

**Phone Setup:**
1. Configure SIP accounts in FreeSWITCH
2. Distribute credentials to staff
3. Set up softphones or desk phones
4. Configure call routing rules

## ClinicHub Integration

### Backend Integration

Add to ClinicHub's `backend/.env`:
```env
# Communication Gateway
COMMUNICATION_GATEWAY_URL=http://localhost:8100
COMMUNICATION_GATEWAY_ENABLED=true

# Email Settings
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USER=clinichub@yourdomain.com
SMTP_PASSWORD=your_secure_password
```

### API Endpoints

The communication gateway provides these endpoints:

```python
# Email
POST /email/send
{
    "to": ["patient@example.com"],
    "subject": "Lab Results Available",
    "body": "Your lab results are ready for review.",
    "patient_id": "patient_123"
}

# Fax
POST /fax/send
{
    "to_number": "+1234567890",
    "document_path": "/documents/prescription.pdf",
    "patient_id": "patient_123"
}

# VoIP
POST /voip/call
{
    "from_number": "clinic",
    "to_number": "+1234567890",
    "patient_id": "patient_123"
}
```

### Frontend Integration

Add communication features to ClinicHub modules:

```javascript
// Send patient email
const sendPatientEmail = async (patientId, subject, message) => {
  const response = await axios.post(`${GATEWAY_URL}/email/send`, {
    to: [patient.email],
    subject: subject,
    body: message,
    patient_id: patientId
  });
  return response.data;
};

// Send fax
const sendFax = async (faxNumber, documentPath, patientId) => {
  const response = await axios.post(`${GATEWAY_URL}/fax/send`, {
    to_number: faxNumber,
    document_path: documentPath,
    patient_id: patientId
  });
  return response.data;
};
```

## Security Considerations

### Email Security
- TLS encryption for all email traffic
- DKIM signing for authentication
- SPF and DMARC for sender verification
- Spam and virus filtering
- Rate limiting on authentication

### Fax Security
- Encrypted storage of fax documents
- Access logging and audit trails
- Secure transmission protocols
- Automatic document purging

### VoIP Security
- SIP over TLS (SIPS)
- RTP encryption (SRTP)
- Authentication for all calls
- Call recording encryption

## Monitoring and Maintenance

### Health Checks
```bash
# Check all services
curl http://localhost:8100/status

# Check individual services
docker-compose -f docker-compose.communication.yml ps

# View logs
docker-compose -f docker-compose.communication.yml logs -f
```

### Backup Strategy
- Daily backup of email data
- Weekly backup of fax archives
- Monthly backup of VoIP recordings
- Configuration backup before updates

### Updates
```bash
# Update images
docker-compose -f docker-compose.communication.yml pull

# Restart services
docker-compose -f docker-compose.communication.yml down
docker-compose -f docker-compose.communication.yml up -d
```

## Troubleshooting

### Common Issues

1. **Email not sending:**
   - Check SMTP configuration
   - Verify DNS records
   - Check firewall rules
   - Review Mailu logs

2. **Fax not working:**
   - Verify modem configuration
   - Check phone line connection
   - Review HylaFAX+ logs
   - Test with simple document

3. **VoIP calls failing:**
   - Check SIP registration
   - Verify network connectivity
   - Review FreeSWITCH logs
   - Test with softphone

### Log Locations
- Mailu: `docker logs clinichub_mailu_admin_1`
- HylaFAX+: `docker logs clinichub_hylafax_1`
- FreeSWITCH: `docker logs clinichub_freeswitch_1`
- Gateway: `./gateway/logs/gateway.log`

## Cost Savings

Replacing commercial services with this self-hosted solution saves:

- **Email service:** $20-50/month → $0
- **Fax service:** $30-100/month → $0
- **VoIP service:** $50-200/month → $0
- **Total annual savings:** $1,200-4,200

## Support and Documentation

- Mailu Documentation: https://mailu.io/
- HylaFAX+ Documentation: https://hylafax.sourceforge.io/
- FreeSWITCH Documentation: https://freeswitch.org/confluence/
- ClinicHub Communication Gateway: See API documentation at `/docs` endpoint

## Next Steps

After successful deployment:

1. **Test all communication channels**
2. **Train staff on new email/fax workflows**
3. **Set up monitoring and alerting**
4. **Configure backup procedures**
5. **Plan for Phase 2C: Advanced Features**
   - Telehealth video integration
   - SMS notifications
   - Advanced call routing
   - Integration with EHR workflows