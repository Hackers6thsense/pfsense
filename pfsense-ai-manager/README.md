# pfSense AI Manager

A comprehensive PHP-based AI management tool for pfSense firewalls with intelligent network traffic analysis, security threat detection, configuration recommendations, log analysis, and natural language interface powered by Mistral, Groq, and Gemini APIs.

## Features

- 🤖 **Multi-AI Integration**: Support for Mistral, Groq, and Gemini with intelligent fallback
- 📊 **Network Traffic Analysis**: AI-powered analysis of network flows and patterns
- 🔒 **Security Threat Detection**: Real-time threat detection and classification
- ⚙️ **Configuration Recommendations**: Intelligent suggestions for firewall optimization
- 📝 **Log Analysis**: Natural language-based log analysis and insights
- 💬 **Natural Language Interface**: Chat-like interface for firewall management
- 🔄 **Multi-Provider Fallback**: Automatic fallback between AI providers
- 📈 **Performance Monitoring**: Real-time firewall performance metrics

## Requirements

- PHP 8.0 or higher
- Composer
- pfSense 2.5.0 or higher (with REST API enabled)
- At least one AI provider API key (Mistral, Groq, or Gemini)

## Installation

1. **Clone or download the project**
   ```bash
   cd pfsense-ai-manager
   ```

2. **Install dependencies**
   ```bash
   composer install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   - pfSense host and credentials
   - AI provider API keys
   - Application settings

4. **Create necessary directories**
   ```bash
   mkdir -p storage logs
   chmod 755 storage logs
   ```

5. **Start the development server**
   ```bash
   composer start
   ```
   
   The application will be available at `http://localhost:8000`

## Configuration

### pfSense Setup

1. Enable REST API in pfSense:
   - System → Advanced → Admin Access
   - Enable "OPNsense/pfSense+ API"
   - Create an API key and secret

2. Update `.env`:
   ```
   PFSENSE_HOST=your.pfsense.ip
   PFSENSE_USERNAME=admin
   PFSENSE_PASSWORD=your_password
   PFSENSE_API_KEY=your_api_key
   ```

### AI Provider Setup

#### Mistral
1. Get API key from https://console.mistral.ai
2. Add to `.env`:
   ```
   MISTRAL_API_KEY=your_key
   MISTRAL_MODEL=mistral-large
   ```

#### Groq
1. Get API key from https://console.groq.com
2. Add to `.env`:
   ```
   GROQ_API_KEY=your_key
   GROQ_MODEL=mixtral-8x7b-32768
   ```

#### Gemini
1. Get API key from https://ai.google.dev
2. Add to `.env`:
   ```
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=gemini-pro
   ```

## Project Structure

```
pfsense-ai-manager/
├── src/                          # Source code
│   ├── AI/                       # AI provider implementations
│   │   ├── AIProvider.php        # Base interface
│   │   ├── MistralProvider.php   # Mistral integration
│   │   ├── GroqProvider.php      # Groq integration
│   │   ├── GeminiProvider.php    # Gemini integration
│   │   └── AIFactory.php         # Provider factory
│   ├── PfSense/                  # pfSense integration
│   │   ├── PfSenseClient.php     # API client
│   │   └── DataCollector.php     # Data collection
│   ├── Analysis/                 # Analysis engines
│   │   ├── TrafficAnalyzer.php   # Network traffic analysis
│   │   ├── ThreatDetector.php    # Security threat detection
│   │   ├── ConfigAnalyzer.php    # Configuration analysis
│   │   └── LogAnalyzer.php       # Log analysis
│   ├── API/                      # REST API endpoints
│   │   ├── Router.php            # Route handler
│   │   └── Endpoints/            # API endpoints
│   ├── Utils/
│   │   ├── Logger.php            # Logging utility
│   │   ├── Config.php            # Configuration manager
│   │   └── Cache.php             # Caching utility
│   └── bootstrap.php             # Application bootstrap
├── public/                       # Public files
│   ├── index.php                 # Entry point
│   ├── css/
│   └── js/
├── templates/                    # HTML templates
├── config/                       # Configuration files
├── storage/                      # Storage directory
├── logs/                         # Log files
├── tests/                        # Unit tests
├── composer.json                 # PHP dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Usage

### Via Web Interface

1. Navigate to `http://localhost:8000`
2. Log in with your credentials
3. Use the dashboard to:
   - View network traffic analysis
   - Check security threats
   - Get configuration recommendations
   - Analyze logs in natural language
   - Chat with the AI assistant

### Via REST API

```bash
# Analyze network traffic
curl -X POST http://localhost:8000/api/analysis/traffic \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "last_hour"}'

# Get threat detections
curl -X GET http://localhost:8000/api/threats

# Get configuration recommendations
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"type": "security"}'

# Chat interface
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze my firewall rules"}'
```

## Key Features

### Network Traffic Analysis
- Analyzes incoming/outgoing traffic patterns
- Identifies anomalies and unusual behavior
- Generates insights using AI
- Provides optimization recommendations

### Security Threat Detection
- Monitors failed login attempts
- Detects port scanning activities
- Identifies DDoS patterns
- Flags suspicious traffic patterns

### Configuration Recommendations
- Analyzes current firewall rules
- Suggests security improvements
- Recommends performance optimizations
- Validates rule compliance

### Log Analysis
- Processes firewall logs with AI
- Identifies patterns and anomalies
- Provides natural language summaries
- Generates actionable insights

## API Endpoints

### Traffic Analysis
- `POST /api/analysis/traffic` - Analyze network traffic
- `GET /api/analysis/traffic/history` - Get traffic history

### Security
- `GET /api/threats` - Get detected threats
- `POST /api/threats/analyze` - Analyze specific threat
- `GET /api/threats/dashboard` - Get threat summary

### Configuration
- `GET /api/config/rules` - Get firewall rules
- `POST /api/config/analyze` - Analyze configuration
- `GET /api/recommendations` - Get recommendations

### Logs
- `GET /api/logs` - Get firewall logs
- `POST /api/logs/analyze` - Analyze logs with AI

### Chat
- `POST /api/chat` - Send message to AI
- `GET /api/chat/history` - Get conversation history

## Error Handling

The application includes:
- Automatic provider fallback if primary AI provider fails
- Comprehensive error logging
- User-friendly error messages
- Retry logic with exponential backoff

## Security

- All API communications are encrypted
- Credentials stored securely in environment variables
- Session management and authentication
- Input validation and sanitization
- Rate limiting on API endpoints

## Troubleshooting

### pfSense Connection Failed
- Verify PFSENSE_HOST, username, and password
- Check if REST API is enabled in pfSense
- Ensure firewall allows API connections

### AI Provider Errors
- Verify API keys are correct
- Check API rate limits
- Review provider status pages
- System automatically falls back to other providers

### Performance Issues
- Increase cache TTL in configuration
- Reduce analysis timeframe
- Check server resources
- Review log files for errors

## Development

### Running Tests
```bash
composer test
```

### Adding New AI Provider
1. Create new provider class in `src/AI/`
2. Implement `AIProvider` interface
3. Update `AIFactory` to support new provider
4. Add configuration in `.env`

### Adding New Analysis Type
1. Create analyzer class in `src/Analysis/`
2. Implement analysis logic
3. Add API endpoint in `src/API/Endpoints/`
4. Update routes in API router

## Contributing

Contributions are welcome! Please follow PSR-12 coding standards and include tests for new features.

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions, please create an issue or contact the development team.

## Roadmap

- [ ] Machine learning-based threat prediction
- [ ] Advanced log correlation
- [ ] Custom rule recommendations
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Kubernetes integration
- [ ] Advanced reporting and dashboards

## Changelog

### Version 1.0.0 (Initial Release)
- Core AI integration (Mistral, Groq, Gemini)
- Network traffic analysis
- Security threat detection
- Configuration recommendations
- Log analysis
- Natural language chat interface
- REST API
- Web dashboard
