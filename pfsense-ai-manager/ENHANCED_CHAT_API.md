# Enhanced Chat API Documentation

## Overview

The Chat API now includes advanced features for better AI communication:
- ✅ Streaming responses
- ✅ Conversation history with context awareness
- ✅ Multi-turn conversations
- ✅ Reasoning and confidence scores
- ✅ Caveats and warnings
- ✅ Follow-up questions
- ✅ Full conversation management

---

## Chat Endpoints

### 1. Send Chat Message (Enhanced)
**POST** `/api/chat`

Send a message to the AI with optional streaming, context, and enhanced responses.

**Request:**
```json
{
  "message": "Analyze my firewall rules for security",
  "conversation_id": "conv_abc123_1234567890",
  "streaming": false,
  "include_context": true,
  "enhanced": true
}
```

**Request Parameters:**
- `message` (required, string) - User message
- `conversation_id` (optional, string) - Existing conversation ID (auto-generated if not provided)
- `streaming` (optional, bool, default: false) - Enable Server-Sent Events streaming
- `include_context` (optional, bool, default: true) - Include firewall context in analysis
- `enhanced` (optional, bool, default: true) - Enable reasoning, confidence, caveats, and follow-ups

**Response (Enhanced):**
```json
{
  "status": "success",
  "conversation_id": "conv_abc123_1234567890",
  "message": "Analyze my firewall rules for security",
  "response": {
    "response": "Based on your configuration, I recommend...",
    "reasoning": {
      "question_analyzed": ["firewall", "rules", "security"],
      "reasoning_steps": [
        "Identified security-focused question",
        "Analyzed firewall rule patterns",
        "Generated recommendations based on best practices"
      ],
      "logic_used": "advisory"
    },
    "confidence": {
      "overall": 0.85,
      "level": "high",
      "factors": {
        "question_clarity": 0.9,
        "response_completeness": 0.8,
        "terminology_accuracy": 0.85
      }
    },
    "caveats": [
      {
        "severity": "medium",
        "warning": "Security recommendations should be validated against your specific environment"
      },
      {
        "severity": "info",
        "warning": "Always test changes in a non-production environment first"
      }
    ],
    "follow_up_questions": [
      "Would you like help implementing these security improvements?",
      "Should we review specific rules in detail?",
      "Would you like recommendations for logging configuration?"
    ],
    "metadata": {
      "provider": "mistral",
      "model": "mistral_ai",
      "timestamp": "2024-01-01T12:00:00",
      "firewall_context_used": true
    }
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### 2. Multi-Turn Conversation
**POST** `/api/chat/multi-turn`

Send multiple messages in a conversation to maintain context across multiple exchanges.

**Request:**
```json
{
  "messages": [
    "What are my top security concerns?",
    "Can you explain rule 5 in more detail?",
    "How should I fix that issue?"
  ],
  "conversation_id": "conv_abc123_1234567890"
}
```

**Response:**
```json
{
  "status": "success",
  "conversation_id": "conv_abc123_1234567890",
  "multi_turn": {
    "messages_processed": 3,
    "responses": [
      {
        "response": "Your top security concerns are...",
        "reasoning": {...},
        "confidence": {...},
        "caveats": [...]
      },
      {
        "response": "Rule 5 blocks incoming connections to...",
        "reasoning": {...},
        "confidence": {...}
      },
      {
        "response": "To fix this issue, you should...",
        "reasoning": {...},
        "confidence": {...},
        "follow_up_questions": [...]
      }
    ],
    "conversation_summary": {
      "total_messages": 3,
      "topics_discussed": ["security", "rules", "threat"],
      "conversation_type": "troubleshooting",
      "sentiment": "neutral"
    }
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### 3. Streaming Response
**POST** `/api/chat` (with `streaming: true`)

Get real-time streaming response using Server-Sent Events (SSE).

**Request:**
```json
{
  "message": "Explain my threat detection",
  "streaming": true
}
```

**Response (SSE Stream):**
```
event: start
data: {"message":"Processing your request..."}

event: chunk
data: {"text":"Based on your "}

event: chunk
data: {"text":"firewall logs, I"}

event: chunk
data: {"text":" detected the following"}

event: reasoning
data: {"process": "...reasoning steps..."}

event: caveats
data: {"warnings": [...]}

event: follow_ups
data: {"questions": [...]}

event: complete
data: {"status":"done"}
```

**JavaScript Example for Streaming:**
```javascript
const eventSource = new EventSource('/api/chat?streaming=true&message=Your%20question');

eventSource.addEventListener('chunk', (event) => {
    const data = JSON.parse(event.data);
    console.log(data.text); // Append to UI
});

eventSource.addEventListener('reasoning', (event) => {
    const data = JSON.parse(event.data);
    console.log('Reasoning:', data.process);
});

eventSource.addEventListener('complete', () => {
    eventSource.close();
});
```

---

### 4. Get Conversation History
**GET** `/api/chat/history?conversation_id=conv_abc123&limit=50`

Retrieve conversation history with optional limit.

**Query Parameters:**
- `conversation_id` (required, string) - Conversation ID
- `limit` (optional, int, default: 50) - Number of messages to retrieve

**Response:**
```json
{
  "status": "success",
  "conversation_id": "conv_abc123_1234567890",
  "history": [
    {
      "role": "user",
      "content": "What are my security concerns?",
      "timestamp": "2024-01-01T12:00:00",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "Your top security concerns are...",
      "timestamp": "2024-01-01T12:00:05",
      "metadata": {
        "confidence": 0.85,
        "provider": "mistral"
      }
    }
  ],
  "summary": {
    "conversation_id": "conv_abc123_1234567890",
    "total_messages": 12,
    "user_messages": 6,
    "assistant_messages": 6,
    "started_at": "2024-01-01T11:50:00",
    "last_message_at": "2024-01-01T12:15:00",
    "topics": ["security", "threat", "rules"]
  },
  "timestamp": "2024-01-01T12:16:00"
}
```

---

### 5. Get Conversation Summary
**GET** `/api/chat/summary?conversation_id=conv_abc123`

Get summary and markdown export of conversation.

**Query Parameters:**
- `conversation_id` (required, string) - Conversation ID

**Response:**
```json
{
  "status": "success",
  "conversation_id": "conv_abc123_1234567890",
  "summary": {
    "conversation_id": "conv_abc123_1234567890",
    "total_messages": 12,
    "user_messages": 6,
    "assistant_messages": 6,
    "started_at": "2024-01-01T11:50:00",
    "last_message_at": "2024-01-01T12:15:00",
    "topics": ["security", "threat", "rules"]
  },
  "markdown_export": "# Conversation conv_abc123_1234567890\n\n## User (2024-01-01T12:00:00)\nWhat are my security concerns?\n\n## Assistant (2024-01-01T12:00:05)\nYour top security concerns are...\n\n...",
  "timestamp": "2024-01-01T12:16:00"
}
```

---

### 6. Clear Conversation History
**POST** `/api/chat/clear`

Clear conversation history for a given conversation ID.

**Request:**
```json
{
  "conversation_id": "conv_abc123_1234567890"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation cleared",
  "timestamp": "2024-01-01T12:16:00"
}
```

---

## Response Components Explained

### Reasoning
Shows the AI's thinking process:
```json
"reasoning": {
  "question_analyzed": ["keywords", "extracted", "from", "question"],
  "reasoning_steps": [
    "Step 1 of analysis",
    "Step 2 of analysis",
    "Step 3 of analysis"
  ],
  "logic_used": "advisory|analytical|explanatory|troubleshooting"
}
```

### Confidence
Indicates how confident the AI is in its response:
```json
"confidence": {
  "overall": 0.85,  // 0-1 scale
  "level": "high",  // very_high|high|medium|low|very_low
  "factors": {
    "question_clarity": 0.9,
    "response_completeness": 0.8,
    "terminology_accuracy": 0.85
  }
}
```

### Caveats
Important warnings or limitations:
```json
"caveats": [
  {
    "severity": "high|medium|low|info",
    "warning": "Description of caveat"
  }
]
```

### Follow-Up Questions
Suggested next questions to deepen understanding:
```json
"follow_up_questions": [
  "Question 1?",
  "Question 2?",
  "Question 3?"
]
```

---

## Usage Examples

### Example 1: Simple Chat with Enhancement
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What security issues should I fix?",
    "enhanced": true
  }'
```

### Example 2: Multi-Turn Conversation
```bash
curl -X POST http://localhost:8000/api/chat/multi-turn \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      "What are the threats?",
      "How do I fix them?",
      "What about performance?"
    ]
  }'
```

### Example 3: Streaming with JavaScript
```javascript
const streamChat = async (message) => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      streaming: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while(true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    console.log(text); // SSE events
  }
};
```

### Example 4: Get Conversation History
```bash
curl http://localhost:8000/api/chat/history?conversation_id=conv_abc123&limit=20
```

### Example 5: Python Integration
```python
import requests
import json

# Send message with enhancement
response = requests.post(
    'http://localhost:8000/api/chat',
    json={
        'message': 'Analyze my firewall',
        'enhanced': True
    }
)

data = response.json()
print(f"Response: {data['response']['response']}")
print(f"Confidence: {data['response']['confidence']['overall']}")
print(f"Caveats: {data['response']['caveats']}")
print(f"Follow-ups: {data['response']['follow_up_questions']}")
```

---

## Context Awareness

When `include_context: true`, the AI receives:
- Current firewall status
- Recent threat detections
- Traffic patterns
- Connected devices
- Service status
- DHCP leases
- ARP table data

This allows the AI to provide more relevant and accurate responses based on your actual firewall state.

---

## Conversation Management

Conversations are automatically:
- **Created** when you send first message
- **Persisted** in cache for 24 hours
- **Tracked** with metadata (topics, sentiment, type)
- **Summaryized** for easy review
- **Exportable** as markdown

Each conversation has:
- Unique ID
- Full message history
- Topic extraction
- Conversation type identification
- Start/end times
- Message count tracking

---

## Error Handling

### Common Errors

**400 - Bad Request**
```json
{"error": "Message required"}
```

**401 - Conversation Not Found**
```json
{"error": "Conversation ID required"}
```

**500 - Server Error**
```json
{"error": "All AI providers failed after 3 attempts"}
```

---

## Rate Limiting

- 100 requests per minute per IP
- Consider batching multi-turn conversations
- Use conversation history to reduce API calls

---

## Best Practices

1. **Reuse Conversation IDs** - Maintain context across sessions
2. **Enable Enhanced Responses** - Get reasoning and caveats
3. **Use Context** - Let AI know firewall state
4. **Handle Streaming** - Better UX with real-time updates
5. **Export Conversations** - Keep records for audit
6. **Review Caveats** - Always check warnings before acting

---

*For more information, see README.md and FAQ.md*
