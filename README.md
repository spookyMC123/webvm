# Nexo-VM-Panel

<div align="center">

![NexoHost](https://img.shields.io/badge/NexoHost-Power%20Your%20Future-0066ff?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMiA3TDEyIDEyTDIyIDdMMTIgMloiIGZpbGw9IiMwMGNjZmYiLz4KPHBhdGggZD0iTTIgMTdMMTIgMjJMMjIgMTdNMiAxMkwxMiAxN0wyMiAxMiIgc3Ryb2tlPSIjMDA2NmZmIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4=)
![Version](https://img.shields.io/badge/version-2.0.0-00ccff?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-0099ff?style=for-the-badge)

**Professional VPS Management Panel with Futuristic Blue Theme**

[Website](https://www.nexohost.online) • [Status](https://status.nexohost.online) • [Discord](https://discord.gg/tsZKtJWR7n) • [Support](mailto:nexohostsup@gmail.com)

</div>

---

## 🚀 Welcome to NexoHost! Power Your Future!

Nexo-VM-Panel is a professional, animated, and futuristic VPS management panel built with Flask and LXC. Experience cutting-edge design with 3D effects, glassmorphism, and smooth animations.

## ✨ Features

### 🎨 **Professional Design**
- **Futuristic Blue Theme** - Stunning gradient blues with cyan accents
- **3D Card Effects** - Depth and dimension with glassmorphism
- **Smooth Animations** - Every interaction is animated and polished
- **Particle Effects** - Optional floating particles for extra flair
- **Responsive Design** - Perfect on desktop, tablet, and mobile

### 💎 **Advanced UI Components**
- **Animated Sidebar** - Smooth transitions with glow effects
- **Stat Cards** - 3D floating cards with hover animations
- **Status Badges** - Real-time pulsing status indicators
- **Loading States** - Professional loading animations
- **Notifications** - Elegant toast notifications

### 🔧 **VPS Management**
- **Create & Manage VPS** - Full LXC container management
- **Real-time Stats** - CPU, RAM, and disk monitoring
- **SSH Access** - Integrated Tmate sessions
- **Multiple OS Support** - Ubuntu 24.04, 22.04, Debian 12, 11
- **Auto-refresh** - Stats update every 30 seconds

### 💰 **Billing & Plans**
- **Multiple Plans** - Starter, Basic, Pro, Enterprise, Ultimate
- **BDT Currency** - Pricing in Bangladeshi Taka (৳)
- **Payment Proof** - Screenshot upload system
- **User Balance** - Wallet system for credits

### 🛡️ **Admin Panel**
- **User Management** - Create, edit, ban, suspend users
- **VPS Control** - Manage all VPS instances
- **Payment Approval** - Review and approve payments
- **System Stats** - Monitor overall system usage

## 📦 Installation

### Prerequisites
- Python 3.8+
- LXC/LXD installed and configured
- Ubuntu/Debian Linux

### Quick Start

1. **Clone the repository**
```bash
cd /path/to/nexovmv1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Edit .env file with your settings
nano .env
```

4. **Run the application**
```bash
python nexovm.py
```

5. **Access the panel**
```
http://localhost:3000
Default credentials: admin / admin
```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Panel Branding
PANEL_NAME=Nexo-VM-Panel
HOSTING_NAME=NexoHost
WELCOME_MESSAGE=Welcome to NexoHost! Power Your Future!

# Server Configuration
HOST=0.0.0.0
PORT=3000
SECRET_KEY=your-secret-key-here

# Currency
CURRENCY_SYMBOL=৳
CURRENCY_CODE=BDT

# Company Information
COMPANY_NAME=NexoHost
COMPANY_WEBSITE=https://www.nexohost.online
COMPANY_STATUS_PAGE=https://status.nexohost.online
COMPANY_DISCORD=https://discord.gg/tsZKtJWR7n
COMPANY_SUPPORT_EMAIL=nexohostsup@gmail.com

# Developer Credits
DEVELOPER_NAME=Joy (@! N!GHT .EXE.</>)
DEVELOPER_COMPANY=NexoHost
POWERED_BY=InfinityForge
```

## 🎨 Theme Customization

The panel uses CSS variables for easy theme customization. Edit `static/css/style.css`:

```css
:root {
    --primary-blue: #0066ff;
    --secondary-blue: #00ccff;
    --accent-blue: #0099ff;
    --bg-primary: #0a0e27;
    --bg-card: #1a1f3a;
}
```

## 📁 Project Structure

```
nexovmv1/
├── nexovm.py              # Main application (renamed from app.py)
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
├── data/                  # JSON data storage
│   ├── users.json
│   ├── vps_data.json
│   ├── settings.json
│   └── pending_payments.json
├── static/
│   ├── css/
│   │   └── style.css      # Professional blue theme
│   ├── js/
│   │   └── main.js        # Interactive features
│   └── uploads/           # User uploads
└── templates/
    ├── base.html          # Base template with footer
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── dashboard.html     # User dashboard
    ├── plans.html         # VPS plans
    ├── profile.html       # User profile
    ├── manage_vps.html    # VPS management
    ├── payment_proof.html # Payment submission
    └── admin/             # Admin templates
        ├── dashboard.html
        ├── users.html
        ├── vps.html
        ├── payments.html
        └── settings.html
```

## 🔐 Security

- **Password Hashing** - Werkzeug secure password hashing
- **Session Management** - Flask secure sessions
- **Input Validation** - Server-side validation
- **CSRF Protection** - Built-in Flask protection
- **Environment Variables** - Sensitive data in .env

## 🌐 API Endpoints

### User Routes
- `GET /` - Home (redirects to dashboard)
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout
- `GET /dashboard` - User dashboard
- `GET /plans` - VPS plans
- `GET /profile` - User profile
- `GET /vps/manage/<vps_id>` - VPS management
- `POST /vps/action/<vps_id>/<action>` - VPS actions

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET/POST /admin/users` - User management
- `GET/POST /admin/vps` - VPS management
- `GET/POST /admin/payments` - Payment management
- `GET/POST /admin/settings` - Panel settings

## 🎯 VPS Plans

| Plan | RAM | CPU | Disk | Price |
|------|-----|-----|------|-------|
| 🔰 Starter | 4GB | 2 Cores | 50GB | ৳49/month |
| ⚡ Basic | 8GB | 4 Cores | 100GB | ৳99/month |
| 🚀 Pro | 16GB | 6 Cores | 200GB | ৳199/month |
| 💎 Enterprise | 32GB | 8 Cores | 300GB | ৳250/month |
| 👑 Ultimate | 64GB | 12 Cores | 300GB | ৳399/month |

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change PORT in .env file
PORT=5000
```

### LXC Permission Issues
```bash
# Add user to lxd group
sudo usermod -aG lxd $USER
newgrp lxd
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📝 Changelog

### Version 2.0.0 (Latest)
- ✅ Renamed `app.py` to `nexovm.py`
- ✅ Complete UI redesign with futuristic blue theme
- ✅ Added 3D effects and glassmorphism
- ✅ Implemented smooth animations throughout
- ✅ Added `.env` configuration file
- ✅ Changed currency from INR (₹) to BDT (৳)
- ✅ Added professional footer with company links
- ✅ Added developer credits
- ✅ Enhanced mobile responsiveness
- ✅ Added auto-refresh for VPS stats
- ✅ Improved notification system
- ✅ Added particle effects (optional)
- ✅ Professional startup banner

## 👨‍💻 Developer

**Made by Joy (@! N!GHT .EXE.</>)**
- Company: NexoHost
- Powered by: InfinityForge

## 🔗 Links

- **Website**: [https://www.nexohost.online](https://www.nexohost.online)
- **Status Page**: [https://status.nexohost.online](https://status.nexohost.online)
- **Discord**: [https://discord.gg/tsZKtJWR7n](https://discord.gg/tsZKtJWR7n)
- **Support**: [nexohostsup@gmail.com](mailto:nexohostsup@gmail.com)

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Flask Framework
- LXC/LXD
- Font Awesome Icons
- Google Fonts (Orbitron, Rajdhani)
- jQuery

---

<div align="center">

**© 2025 NexoHost. All rights reserved.**

*Powered by InfinityForge*

</div>
