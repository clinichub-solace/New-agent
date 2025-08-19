# ClinicHub - Medical Practice Management System

## 🚀 Quick Installation

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/[your-username]/clinichub.git
cd clinichub

# Start with Docker
docker-compose up -d

# Access application
# http://localhost:3000
# Login: admin / admin123
```

### Option 2: Manual Setup
```bash
# Prerequisites
sudo apt install python3 nodejs mongodb git yarn

# Clone and setup
git clone https://github.com/[your-username]/clinichub.git
cd clinichub

# Backend
cd backend
pip install -r requirements.txt
python server.py &

# Frontend
cd ../frontend
yarn install
yarn start

# Access: http://localhost:3000
```

## 🎯 Demo Data

Initialize with realistic demo data:
```bash
# Login to app as admin/admin123
# Go to Settings → Initialize Demo Data
# Or run: python backend_test.py --init-demo
```

## 📚 Full Documentation

See [INSTALLATION.md](INSTALLATION.md) for complete setup guide.

## 🏥 Features

- ✅ **Patient Management** - Complete EHR system
- ✅ **Lab Integration** - Order tests, track results
- ✅ **Insurance Verification** - Real-time eligibility
- ✅ **Prescription Management** - eRx integration
- ✅ **Smart Forms** - HIPAA-compliant templates
- ✅ **Billing & Invoicing** - Payment processing
- ✅ **Scheduling** - Appointment management
- ✅ **Communications** - Patient messaging

## 📞 Support

- 📖 [Full Installation Guide](INSTALLATION.md)
- 🐛 [Report Issues](https://github.com/[your-username]/clinichub/issues)
- 💬 [Discussions](https://github.com/[your-username]/clinichub/discussions)

---

**ClinicHub** - Open Source Medical Practice Management System