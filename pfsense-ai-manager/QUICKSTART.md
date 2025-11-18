# Quick Start Guide - pfSense AI Manager

## 1. Installation

### Prerequisites
- PHP 8.0+
- Composer
- pfSense 2.5.0+
- Internet connection (for AI API calls)

### Steps

1. **Navigate to project directory**
   ```bash
   cd pfsense-ai-manager
   ```

2. **Install dependencies**
   ```bash
   composer install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` with your settings**
   ```bash
   # pfSense Configuration
   PFSENSE_HOST=192.168.1.1
   PFSENSE_USERNAME=admin
   PFSENSE_PASSWORD=your_password
   PFSENSE_API_KEY=your_api_key  # Optional, if not using basic auth
   
   # Choose your AI providers (at least one required)
   MISTRAL_API_KEY=your_mistral_key
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   
   # Set primary provider
   PRIMARY_AI_PROVIDER=mistral
   ```

5. **Create storage directories**
   ```bash
   mkdir -p storage logs
   chmod 755 storage logs
   ```

6. **Start the server**
   ```bash
   composer start
   ```

7. **Access the dashboard**
   - Open browser and go to: `http://localhost:8000/dashboard.html`

## 2. Getting API Keys

### Mistral
1. Visit: https://console.mistral.ai
2. Sign up for an account
3. Create API key
4. Add to `.env`: `MISTRAL_API_KEY=your_key`

### Groq
1. Visit: https://console.groq.com
2. Create account
3. Get API key
4. Add to `.env`: `GROQ_API_KEY=your_key`

### Gemini (Google)
1. Visit: https://ai.google.dev
2. Get API key
3. Add to `.env`: `GEMINI_API_KEY=your_key`

## 3. Configuring pfSense Connection

### Enable REST API in pfSense
1. Log in to pfSense dashboard
2. Go to: **System → Advanced → Admin Access**
3. Enable "OPNsense/pfSense+ API"
4. Copy the API key and secret
5. Add to your `.env` file

### Using Basic Authentication (Alternative)
If you don't have API key:
- Set `PFSENSE_USERNAME` and `PFSENSE_PASSWORD` in `.env`
- Application will use basic authentication

## 4. API Usage Examples

### Chat with AI
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze my firewall rules for security"}'
```

### Analyze Network Traffic
```bash
curl -X POST http://localhost:8000/api/analysis/traffic \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "last_hour"}'
```

### Detect Security Threats
```bash
curl -X GET http://localhost:8000/api/threats
```

### Get Configuration Recommendations
```bash
curl -X GET "http://localhost:8000/api/recommendations?type=security"
```

### Analyze Logs with Natural Language
```bash
curl -X POST http://localhost:8000/api/logs/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me failed login attempts from the past hour"}'
```

### Get System Status
```bash
curl -X GET http://localhost:8000/api/system/status
```

## 5. Features Overview

### 🔍 Network Traffic Analysis
- Real-time traffic monitoring
- Anomaly detection
- Performance insights
- AI-powered pattern recognition

### 🔒 Security Threat Detection
- Identifies suspicious activities
- Detects port scanning
- Flags DDoS patterns
- AI-powered threat classification

### ⚙️ Configuration Management
- Analyzes firewall rules
- Provides optimization tips
- Validates security policies
- Generates recommendations

### 📝 Log Analysis
- Natural language log search
- Pattern extraction
- Anomaly reporting
- AI insights

### 💬 AI Chat Interface
- Natural language commands
- Firewall management assistance
- Security recommendations
- Real-time analysis

## 6. Common Issues & Solutions

### Connection Error to pfSense
**Error:** "Failed to connect to pfSense"
- Verify PFSENSE_HOST is correct and accessible
- Check if REST API is enabled in pfSense
- Ensure credentials are correct
- Check firewall rules allow API access

### AI Provider Not Available
**Error:** "No AI providers available"
- Verify at least one API key is configured
- Check `.env` file for typos
- Verify API key is valid and not expired
- Check internet connection

### Port 8000 Already in Use
**Error:** "Address already in use"
```bash
# Use different port
php -S localhost:8001 -t public/
```

### Permission Denied on Logs/Storage
**Fix:**
```bash
chmod -R 755 storage/ logs/
```

## 7. Development

### Running Tests
```bash
composer test
```

### File Structure
```
src/
├── AI/               # AI provider implementations
├── PfSense/          # pfSense integration
├── Analysis/         # Analysis engines
├── API/              # REST API endpoints
└── Utils/            # Utilities
public/
├── index.php         # API entry point
├── dashboard.html    # Web interface
├── css/style.css     # Styling
└── js/app.js         # Frontend logic
```

## 8. Production Deployment

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/pfsense-ai-manager/public;
    index index.php;

    location ~ \.php$ {
        fastcgi_pass unix:/run/php/php8.0-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/pfsense-ai-manager/public

    <Directory /var/www/pfsense-ai-manager/public>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

### Environment Security
- Use `.env.local` for production secrets
- Never commit `.env` to version control
- Use strong API keys
- Enable HTTPS in production
- Set proper file permissions (644 for files, 755 for directories)

## 9. Support & Troubleshooting

Check the main README.md for:
- Detailed feature documentation
- API endpoint reference
- Advanced configuration options
- Contributing guidelines

For issues:
1. Check application logs in `logs/pfsense-ai.log`
2. Enable debug mode in `.env`: `APP_DEBUG=true`
3. Review error messages in browser console
4. Check pfSense logs for API errors

## 10. Next Steps

1. ✅ Install and configure the application
2. ✅ Connect to your pfSense firewall
3. ✅ Set up AI providers
4. ✅ Access the dashboard
5. ✅ Start analyzing your network!

---

**Happy Analyzing! 🚀**
