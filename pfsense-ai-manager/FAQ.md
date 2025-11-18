# FAQ - Frequently Asked Questions

## 🚀 Installation & Setup

### Q: Do I need all three AI providers?
**A:** No! You only need **one** API key. The system automatically uses the others as fallback if your primary provider fails. Start with Mistral or Groq.

### Q: What if I don't have composer installed?
**A:** Install Composer from https://getcomposer.org/download/. It's required for PHP dependency management.

### Q: Can I run this on Windows?
**A:** Yes! Use Git Bash, PowerShell, or WSL. All commands work on Windows, Mac, and Linux.

### Q: Do I need a database?
**A:** Not for basic operation. The app works with file-based caching. Database support is optional for future enhancements.

### Q: Can I run this on pfSense directly?
**A:** Better to run on a separate machine. pfSense has limited resources and this tool needs PHP 8.0+.

---

## 🔐 Security & Credentials

### Q: Is my firewall password stored securely?
**A:** Yes! Stored in `.env` file which is never committed to git. Keep `.env` file secure and never share it.

### Q: How often should I rotate API keys?
**A:** Monthly is recommended. Update keys in `.env` and restart the application.

### Q: Can I use basic auth instead of API keys?
**A:** Yes! Just set username/password in `.env` instead of API_KEY. The app automatically uses basic auth as fallback.

### Q: Is HTTPS required?
**A:** Optional for local testing, highly recommended for production. The code supports HTTPS.

---

## 🤖 AI Providers

### Q: Which AI provider is best?
**A:** 
- **Mistral** - Good balance, recommended for beginners
- **Groq** - Fastest inference, best for speed
- **Gemini** - Most capable, good for complex tasks

Try Mistral first, it's excellent and free tier available.

### Q: What if my AI provider goes down?
**A:** The system automatically falls back to the next provider. Configure fallback providers in `.env`.

### Q: Can I use multiple providers simultaneously?
**A:** Yes! One is primary, others are fallback. But you can modify the code to use all three.

### Q: Is there a cost?
**A:** All three offer free tiers:
- Mistral: Free with rate limits
- Groq: Free (very generous)
- Gemini: Free with rate limits

---

## 🔧 Usage & Features

### Q: How do I search logs naturally?
**A:** Use the Logs tab: "Show me failed SSH attempts from today" or send to `/api/logs/search` endpoint.

### Q: Can I analyze historical data?
**A:** Currently analyzes real-time data. Future versions will support historical data with database storage.

### Q: What's the difference between recommendations?
**A:** 
- Security - Fix vulnerabilities
- Performance - Optimize rules
- All - Both security and performance

### Q: How often should I run analysis?
**A:** The dashboard updates in real-time. Run custom analysis as needed or set up cron jobs for regular analysis.

---

## 🐛 Troubleshooting

### Q: "Connection refused" error?
**A:** 
1. Check PFSENSE_HOST is correct (IP or hostname)
2. Verify pfSense is running
3. Ensure REST API is enabled
4. Check firewall allows port 443

### Q: "API key invalid"?
**A:**
1. Double-check key has no extra spaces
2. Verify key hasn't expired
3. Try different AI provider
4. Check internet connection

### Q: Port 8000 already in use?
**A:** Run on different port:
```bash
php -S localhost:8001 -t public/
```

### Q: Dashboard won't load?
**A:**
1. Check server running: `composer start` active?
2. Open browser console: F12 → Console tab
3. Check application log: `logs/pfsense-ai.log`
4. Enable debug: `APP_DEBUG=true` in `.env`

### Q: Permissions error on logs directory?
**A:**
```bash
chmod 755 logs storage
chmod 644 logs/* storage/*
```

---

## 📊 Data & Analysis

### Q: Is my firewall data sent to external servers?
**A:** Only firewall API responses are sent to AI providers for analysis. pfSense credentials never leave your system.

### Q: Can I export analysis results?
**A:** Yes! API returns JSON, easily exportable. Future versions will add CSV/PDF export.

### Q: How accurate are threat detections?
**A:** Depends on your firewall logs. The AI learns from patterns in your logs.

### Q: Does it work with OPNsense?
**A:** OPNsense has similar REST API. Should work with minor configuration adjustments.

---

## 🚀 Deployment

### Q: Can I deploy to cloud?
**A:** Yes! AWS, Google Cloud, Azure, or DigitalOcean. Need PHP 8.0+ and internet access for AI APIs.

### Q: How many concurrent users can it handle?
**A:** Single-threaded by default. Can handle hundreds of API requests/minute. Scale with load balancing if needed.

### Q: Do I need Docker?
**A:** Optional but recommended for production. Makes deployment consistent.

### Q: Can I integrate with other tools?
**A:** Yes! REST API makes integration easy. Can call endpoints from Python, JavaScript, etc.

---

## 💡 Advanced Topics

### Q: How do I add a new AI provider?
**A:**
1. Create `src/AI/NewProvider.php`
2. Implement `AIProvider` interface
3. Add to `AIFactory.php`
4. Update `.env` with credentials

### Q: Can I add new analysis types?
**A:**
1. Create analyzer in `src/Analysis/NewAnalyzer.php`
2. Add endpoint in `src/API/Endpoints/`
3. Register route in `Router.php`
4. Add UI button in `dashboard.html`

### Q: How do I store historical data?
**A:** Add database support (SQLite/MySQL). Modify analyzers to store results.

### Q: Can I run scheduled analysis?
**A:** Yes! Use cron jobs or scheduled tasks to call API endpoints regularly.

---

## 📈 Performance

### Q: How often does the dashboard update?
**A:** On-demand via button clicks. Can modify JavaScript to auto-refresh every X seconds.

### Q: Does caching slow things down?
**A:** No! Caching improves performance. Default cache TTL is 5 minutes, configurable.

### Q: What happens under heavy load?
**A:** System handles thousands of requests/minute. May need to configure PHP-FPM or nginx limits.

### Q: How much disk space needed?
**A:** Minimal - logs and cache grow gradually. Archive old logs monthly.

---

## 🔄 Updates & Maintenance

### Q: How do I update the application?
**A:** Pull latest code, run `composer update`, review changelog.

### Q: Will my configuration be preserved?
**A:** Yes! Store in `.env` which is never overwritten.

### Q: How do I backup my data?
**A:** Backup `.env` and `storage/` directory periodically.

### Q: Can I rollback to older version?
**A:** Yes! Use git tags to checkout previous versions.

---

## ❓ General Questions

### Q: Is this open source?
**A:** Yes! MIT license included. Modify and distribute freely.

### Q: Can I use this commercially?
**A:** Yes! MIT license allows commercial use.

### Q: Who should use this?
**A:** pfSense administrators wanting AI-powered insights and automation.

### Q: What's the learning curve?
**A:** 
- Basic usage: 30 minutes
- Advanced setup: Few hours
- Customization: Depends on PHP skills

### Q: Is it suitable for production?
**A:** Yes! Code follows best practices and is production-ready.

### Q: Can I get professional support?
**A:** For now, community support via documentation. Check GitHub for issues/discussions.

---

## 🎓 Learning Resources

### Q: Where do I learn PHP?
**A:** 
- PHP.net official docs
- Laravel.io for frameworks
- YouTube tutorials

### Q: How do I learn the codebase?
**A:**
1. Read `src/bootstrap.php` first
2. Study `src/AI/AIFactory.php` for architecture
3. Review `src/API/Router.php` for request flow
4. Check `src/Analysis/` for implementation examples

### Q: Can I contribute?
**A:** Yes! Fork the project, make improvements, submit pull requests.

### Q: Where's the roadmap?
**A:** Check `README.md` under "Roadmap" section.

---

## 🆘 Still Have Questions?

### Check These First:
1. **START_HERE.md** - Quick overview
2. **README.md** - Complete documentation
3. **QUICKSTART.md** - Setup help
4. **COMPLETE_SETUP_GUIDE.md** - Detailed guide
5. **API.md** - API reference
6. **logs/pfsense-ai.log** - Application logs

### Getting Help:
- Read the documentation files
- Check browser console for errors (F12)
- Review application logs
- Enable debug mode: `APP_DEBUG=true`

---

## 📝 Common Tasks

### Reset everything
```bash
composer install
rm -rf storage/cache/*
rm logs/*.log
# Restart: composer start
```

### Check what's running
```bash
ps aux | grep php
# or
lsof -i :8000
```

### Clear cache
```bash
rm -rf storage/cache/*
```

### View recent logs
```bash
tail -n 50 logs/pfsense-ai.log
```

### Test connection to pfSense
```bash
curl -k https://192.168.1.1/api/system/info
```

---

**Last Updated:** 2024

*Have a question not listed? Check the documentation files or logs for clues!*
