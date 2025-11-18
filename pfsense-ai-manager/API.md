# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
The application supports two authentication methods:
1. **pfSense API Key** (recommended) - Set via `PFSENSE_API_KEY` in `.env`
2. **Basic Authentication** - Uses `PFSENSE_USERNAME` and `PFSENSE_PASSWORD`

## Response Format
All endpoints return JSON:
```json
{
  "status": "success|error",
  "data": {},
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Analysis Endpoints

### Analyze Network Traffic
**POST** `/api/analysis/traffic`

Analyzes network traffic patterns for the specified timeframe.

**Request:**
```json
{
  "timeframe": "last_hour"
}
```

**Response:**
```json
{
  "status": "success",
  "timeframe": "last_hour",
  "summary": {
    "interfaces_monitored": 3,
    "total_packets": 15000,
    "total_bytes": 2500000
  },
  "ai_analysis": "Network traffic appears normal with no anomalies detected..."
}
```

---

### Get Traffic History
**GET** `/api/analysis/traffic/history?hours=24`

Retrieves traffic history for specified hours.

**Query Parameters:**
- `hours` (int, default: 24) - Number of hours to retrieve

**Response:**
```json
{
  "status": "success",
  "history": {
    "total_in": 5000000,
    "total_out": 3000000,
    "peak_in": 1000000,
    "peak_out": 800000
  }
}
```

---

### Detect Traffic Anomalies
**GET** `/api/analysis/anomalies`

Detects unusual traffic patterns and anomalies.

**Response:**
```json
{
  "status": "success",
  "anomalies_detected": 2,
  "details": [
    {
      "type": "unusual_port_activity",
      "severity": "medium",
      "description": "Unusual activity on port 8080"
    }
  ],
  "ai_insight": "Detected suspicious port scanning activity..."
}
```

---

## Threat Detection Endpoints

### Get Current Threats
**GET** `/api/threats`

Retrieves all currently detected threats.

**Response:**
```json
{
  "status": "success",
  "report": {
    "threats_found": 5,
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0,
    "threats": [
      {
        "type": "failed_login",
        "severity": "high",
        "message": "Multiple failed SSH login attempts"
      }
    ]
  }
}
```

---

### Analyze Specific Threat
**POST** `/api/threats/analyze`

Provides detailed analysis of a specific threat.

**Request:**
```json
{
  "threat": {
    "type": "port_scan",
    "source_ip": "192.168.100.50",
    "target_ports": [22, 80, 443]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "threat": {...},
  "analysis": {
    "risk_level": "high",
    "recommendation": "Block the source IP immediately"
  }
}
```

---

### Get Threat Dashboard
**GET** `/api/threats/dashboard`

Comprehensive threat overview dashboard.

**Response:**
```json
{
  "status": "success",
  "threats": {...},
  "connected_devices": 45,
  "services": [...]
}
```

---

## Configuration Endpoints

### Get Firewall Rules
**GET** `/api/config/rules`

Analyzes current firewall rules configuration.

**Response:**
```json
{
  "status": "success",
  "total_rules": 42,
  "analysis": {
    "total_rules": 42,
    "enabled_rules": 38,
    "disabled_rules": 4,
    "pass_rules": 25,
    "block_rules": 17,
    "issues": []
  }
}
```

---

### Analyze Configuration
**POST** `/api/config/analyze`

Performs comprehensive analysis of firewall configuration.

**Response:**
```json
{
  "status": "success",
  "total_rules": 42,
  "analysis": {...},
  "ai_recommendations": "Consider consolidating similar rules..."
}
```

---

### Get Recommendations
**GET** `/api/recommendations?type=security`

Gets AI-powered recommendations for firewall optimization.

**Query Parameters:**
- `type` (string) - Type of recommendations: `security`, `performance`, `all` (default: `security`)

**Response:**
```json
{
  "status": "success",
  "type": "security",
  "recommendations": [
    {
      "priority": "high",
      "recommendation": "Enable strict logging for all deny rules"
    }
  ],
  "ai_insights": "Your firewall configuration has several security gaps..."
}
```

---

## Log Analysis Endpoints

### Get and Analyze Logs
**GET** `/api/logs?filter=&limit=100`

Retrieves and analyzes firewall logs.

**Query Parameters:**
- `filter` (string) - Filter logs by content
- `limit` (int, default: 100) - Number of logs to retrieve

**Response:**
```json
{
  "status": "success",
  "total_logs": 1250,
  "summary": {
    "by_type": {
      "denied": 450,
      "allowed": 800
    }
  },
  "ai_analysis": "Most logs are routine denied traffic...",
  "logs": [...]
}
```

---

### Analyze Logs
**POST** `/api/logs/analyze`

In-depth analysis of firewall logs.

**Request:**
```json
{
  "filter": "denied",
  "limit": 200
}
```

**Response:**
```json
{
  "status": "success",
  "total_logs": 450,
  "summary": {...},
  "ai_analysis": "..."
}
```

---

### Search Logs with Natural Language
**POST** `/api/logs/search`

Search firewall logs using natural language queries.

**Request:**
```json
{
  "query": "Show me failed SSH login attempts from yesterday"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "Show me failed SSH login attempts from yesterday",
  "ai_filter": "Filtering logs for type=failed_login and service=SSH and date=yesterday",
  "results_found": 23,
  "logs": [...]
}
```

---

### Get Log Patterns
**GET** `/api/logs/patterns`

Extracts and analyzes common patterns in firewall logs.

**Response:**
```json
{
  "status": "success",
  "patterns_found": 5,
  "patterns": [
    {
      "pattern": "Blocked SMTP connection from * to * port N",
      "occurrences": 145
    }
  ],
  "ai_insights": "Spam filtering is actively blocking N emails daily..."
}
```

---

## Chat Endpoints

### Send Chat Message
**POST** `/api/chat`

Send a message to the AI assistant for real-time analysis and recommendations.

**Request:**
```json
{
  "message": "What are the top security concerns in my firewall configuration?"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "What are the top security concerns in my firewall configuration?",
  "response": "Based on your configuration, I've identified several concerns:\n1. Overly permissive rules...",
  "provider": "mistral",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### Get Chat History
**GET** `/api/chat/history`

Retrieves chat conversation history.

**Response:**
```json
{
  "status": "success",
  "history": [
    {
      "role": "user",
      "message": "Analyze my firewall",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "message": "Your firewall configuration shows...",
      "timestamp": "2024-01-01T12:01:00"
    }
  ]
}
```

---

## System Endpoints

### Get System Status
**GET** `/api/system/status`

Retrieves overall system and application status.

**Response:**
```json
{
  "status": "success",
  "application": "pfSense AI Manager",
  "version": "1.0.0",
  "current_provider": "mistral",
  "available_providers": {
    "mistral": {
      "provider": "mistral",
      "model": "mistral-large",
      "available": true
    },
    "groq": {...},
    "gemini": {...}
  }
}
```

---

### Get Available AI Providers
**GET** `/api/system/providers`

Lists all configured and available AI providers.

**Response:**
```json
{
  "status": "success",
  "providers": {
    "mistral": {
      "provider": "mistral",
      "model": "mistral-large",
      "available": true
    },
    "groq": {
      "provider": "groq",
      "model": "mixtral-8x7b-32768",
      "available": true
    },
    "gemini": {
      "provider": "gemini",
      "model": "gemini-pro",
      "available": false
    }
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "error": "Description of what went wrong",
  "code": 400
}
```

**Common Error Codes:**
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication failed)
- `403` - Forbidden (access denied)
- `404` - Not Found (endpoint doesn't exist)
- `500` - Internal Server Error (server error)

---

## Rate Limiting

By default, the application enforces rate limits:
- **100 requests per minute** per IP address

Exceeding limits returns `429 Too Many Requests`.

---

## Examples

### Using cURL

```bash
# Get threats
curl -X GET http://localhost:8000/api/threats

# Analyze traffic
curl -X POST http://localhost:8000/api/analysis/traffic \
  -H "Content-Type: application/json" \
  -d '{"timeframe":"last_hour"}'

# Chat with AI
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain my firewall rules"}'
```

### Using JavaScript/Fetch

```javascript
// Get system status
fetch('http://localhost:8000/api/system/status')
  .then(res => res.json())
  .then(data => console.log(data));

// Send chat message
fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Analyze threats' })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### Using Python

```python
import requests
import json

# Get recommendations
response = requests.get('http://localhost:8000/api/recommendations', 
                       params={'type': 'security'})
print(json.dumps(response.json(), indent=2))

# Search logs
response = requests.post('http://localhost:8000/api/logs/search',
                        json={'query': 'failed login attempts'})
print(json.dumps(response.json(), indent=2))
```

---

For more information, see README.md and QUICKSTART.md
