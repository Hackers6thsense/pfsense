# pfSense AI Manager - Complete Setup Guide

## 🎯 Overview

This is a complete PHP-based AI-powered management system for pfSense firewalls that integrates with Mistral, Groq, and Gemini APIs.

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ PHP 8.0 or higher installed
- ✅ Composer installed
- ✅ pfSense 2.5.0 or higher with REST API enabled
- ✅ Internet connection (for AI API calls)
- ✅ At least one AI provider API key (Mistral, Groq, or Gemini)

### Check PHP Version
```bash
php -v
```

### Check Composer
```bash
composer --version
```

---

## 🚀 Installation Steps

### Step 1: Navigate to Project Directory
```bash
cd pfsense-ai-manager
```

### Step 2: Install PHP Dependencies
```bash
composer install
```

This installs:
- Guzzle HTTP client
- PHP dotenv for environment variables
- Monolog for logging

### Step 3: Setup Configuration File
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# On Windows
start .env

# On macOS
open .env

# On Linux
nano .env
```

### Step 4: Get Your API Keys

#### Option A: Using Mistral
1. Visit: https://console.mistral.ai
2. Create account if needed
3. Create API key
4. Copy and paste in `.env`:
   ```
   MISTRAL_API_KEY=your_key_here
   ```

#### Option B: Using Groq
1. Visit: https://console.groq.com
2. Create account if needed
3. Create API key
4. Copy and paste in `.env`:
   ```
   GROQ_API_KEY=your_key_here
   ```

#### Option C: Using Google Gemini
1. Visit: https://ai.google.dev
2. Sign in with Google account
3. Create API key
4. Copy and paste in `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### Step 5: Configure pfSense Connection

#### Enable REST API in pfSense
1. Log into pfSense dashboard (usually https://192.168.1.1)
2. Navigate to: **System → Advanced → Admin Access**
3. Scroll down to find "OPNsense/pfSense+ API"
4. Enable the checkbox: "Enable OPNsense/pfSense+ API"
5. Click "Save"

#### Generate API Key in pfSense
1. Go to: **System → User Manager**
2. Select your admin user
3. Scroll to "API tokens" section
4. Click "Add" to create new token
5. Copy the "API Token" value
6. Paste in `.env`:
   ```
   PFSENSE_API_KEY=your_token_here
   ```

#### Update pfSense IP in .env
```
PFSENSE_HOST=192.168.1.1  # Your pfSense IP
PFSENSE_USERNAME=admin     # Your admin username
```

### Step 6: Create Storage Directories
```bash
mkdir -p storage logs
chmod 755 storage logs
```

On Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Force -Path storage, logs
```

### Step 7: Start the Server
```bash
composer start
```

You should see:
```
Development Server started at http://127.0.0.1:8000/
```

### Step 8: Access the Dashboard
1. Open your web browser
2. Go to: `http://localhost:8000/dashboard.html`
3. You should see the pfSense AI Manager dashboard

---

## ✨ Dashboard Features Explained

### 🏠 Dashboard Tab
- System status overview
- Available AI providers
- Recent threats
- Network health

### 📊 Traffic Analysis Tab
- View network traffic patterns
- Identify usage trends
- Detect anomalies
- Get AI insights

### 🔒 Security Threats Tab
- Scan for security threats
- View threat severity
- Detailed threat analysis
- AI-powered recommendations

### ⚙️ Configuration Tab
- Analyze firewall rules
- Get security recommendations
- Performance tips
- Rule optimization

### 📝 Logs Tab
- Search logs with natural language (e.g., "Show failed logins")
- Analyze recent logs
- Extract common patterns
- Get AI insights

### 💬 AI Assistant Tab
- Chat interface
- Ask questions about your firewall
- Get recommendations
- Real-time analysis

---

## 🔌 API Usage Examples

### Analyze Traffic with curl
```bash
curl -X POST http://localhost:8000/api/analysis/traffic \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "last_hour"}'
```

### Check Threats with curl
```bash
curl -X GET http://localhost:8000/api/threats
```

### Chat with AI using curl
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top security issues with my firewall?"}'
```

### Search Logs with Natural Language
```bash
curl -X POST http://localhost:8000/api/logs/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me failed SSH attempts from today"}'
```

---

## 🛠 Troubleshooting

### Issue: "Connection refused"
**Solution:**
1. Verify pfSense is running and accessible
2. Check PFSENSE_HOST is correct in `.env`
3. Ensure REST API is enabled in pfSense
4. Check firewall allows connections to port 443

### Issue: "API key invalid"
**Solution:**
1. Verify API key is correct and hasn't expired
2. Try with a different AI provider
3. Check internet connection

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Use different port
php -S localhost:8001 -t public/
```

### Issue: "Permission denied on logs directory"
**Solution:**
```bash
chmod -R 755 storage/ logs/
```

### Issue: "Dashboard won't load"
**Solution:**
1. Check browser console for errors (F12)
2. Verify server is running (`composer start`)
3. Check application logs: `logs/pfsense-ai.log`
4. Enable debug mode: `APP_DEBUG=true` in `.env`

---

## 📚 Documentation Files

| File | Contains |
|------|----------|
| **README.md** | Complete feature documentation |
| **API.md** | REST API endpoint reference |
| **QUICKSTART.md** | Quick start instructions |
| **SECURITY.md** | Security best practices |
| **.env.example** | Environment template |

---

## 🔒 Security Best Practices

### 1. Protect Your .env File
- Never commit `.env` to git
- Use `.env.example` as template
- Restrict file permissions: `chmod 600 .env`

### 2. Use Strong Credentials
- Strong pfSense admin password
- Store API keys securely
- Rotate keys regularly (monthly)

### 3. Enable HTTPS
- Use SSL/TLS in production
- Self-signed certificates OK for internal use
- Force HTTPS redirects

### 4. Firewall Rules
- Restrict access by IP address
- Use IP whitelisting
- Monitor access logs

### 5. Update Regularly
- Keep PHP updated
- Update dependencies: `composer update`
- Monitor security advisories

---

## 📊 System Architecture

```
User Browser
    ↓
Dashboard (HTML/CSS/JS)
    ↓
REST API (/api endpoints)
    ↓
Router & Endpoints
    ↓
Analysis Engines
├── TrafficAnalyzer
├── ThreatDetector
├── ConfigAnalyzer
└── LogAnalyzer
    ↓
AI Factory (with fallback)
├── Mistral
├── Groq
└── Gemini
    ↓
pfSense Client
    ↓
pfSense Firewall REST API
    ↓
pfSense System
```

---

## 🎓 Learning Resources

### Understanding the Code

**AI Providers** (`src/AI/`)
- All inherit from `AIProvider` interface
- Support automatic fallback
- Configurable models and parameters

**Analysis Engines** (`src/Analysis/`)
- Collect data from pfSense
- Process and analyze
- Use AI for insights

**REST API** (`src/API/`)
- RESTful endpoints
- JSON request/response
- Error handling and logging

### Example: Adding New Feature

1. Create analyzer in `src/Analysis/`
2. Add endpoint in `src/API/Endpoints/`
3. Register route in `Router.php`
4. Add UI button in `public/dashboard.html`
5. Add JavaScript handler in `public/js/app.js`

---

## 📈 Performance Tips

### Optimize API Calls
- Cache results (configurable TTL)
- Use pagination for large datasets
- Batch similar requests

### Monitor Resources
- Watch CPU and memory usage
- Monitor pfSense API performance
- Check AI provider rate limits

### Database Considerations
- Future support for SQLite/MySQL
- Store historical data
- Track trends

---

## 🔄 Regular Maintenance

### Daily
- Monitor threat dashboard
- Check logs for errors
- Review recommendations

### Weekly
- Analyze traffic trends
- Review security incidents
- Update firewall rules if needed

### Monthly
- Rotate API keys
- Review log patterns
- Update dependencies
- Run security audit

### Quarterly
- Full system backup
- Update documentation
- Review architecture
- Upgrade dependencies

---

## 🚀 Deployment to Production

### Before Deploying
- [ ] Set `APP_ENV=production` in `.env`
- [ ] Set `APP_DEBUG=false` in `.env`
- [ ] Use strong passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up IP whitelisting
- [ ] Enable access logging
- [ ] Plan backups

### Deployment Options

#### Docker (Recommended)
```dockerfile
FROM php:8.0-apache
RUN docker-php-ext-install pdo
# Copy project files
# Run composer install
# Start Apache
```

#### Traditional Server
```bash
# Copy files to /var/www/
# Configure web server (nginx/apache)
# Set proper permissions
# Start PHP-FPM
```

#### Cloud Platforms
- AWS (EC2 or Lambda)
- Google Cloud
- Azure
- DigitalOcean
- Heroku

---

## 📞 Support & Help

### Getting Help
1. Check **README.md** for feature documentation
2. Review **API.md** for endpoint details
3. See **SECURITY.md** for security issues
4. Check logs: `logs/pfsense-ai.log`

### Common Commands

```bash
# Start development server
composer start

# Run tests
composer test

# View logs
tail -f logs/pfsense-ai.log

# Clear cache
rm -rf storage/cache/*

# Update dependencies
composer update

# Check PHP info
php -i
```

---

## 🎉 You're Ready!

Congratulations! You now have a powerful AI-driven pfSense management system.

### Next Steps:
1. Explore all dashboard features
2. Try natural language log searches
3. Review AI recommendations
4. Set up monitoring alerts
5. Configure backups
6. Train your team

---

## 📝 Version Information

- **pfSense AI Manager**: v1.0.0
- **PHP Requirement**: 8.0+
- **Supported Firewalls**: pfSense 2.5.0+
- **AI Providers**: Mistral, Groq, Gemini

---

**Happy Analyzing! 🔥**

*Built with ❤️ for pfSense administrators*
