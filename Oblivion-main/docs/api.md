# REST API

All endpoints require Bearer token authentication.

## Endpoints

- `GET /status` — Engagement status and stats
- `GET /assets` — Discovered hosts and services
- `POST /attack` — Launch an attack (JSON: `{"technique_id": str, "params": dict}`)
- `POST /scenario` — Launch scenario (JSON: `{"steps": [...]}`)
- `POST /stop` — Stops all attacks

## WebSockets

- `ws://host/ws/status` — Real-time status updates (JSON)
- `ws://host/logs` — Engagement log tail

## Example: Launch Attack

```bash
curl -H "Authorization: Bearer YOURTOKEN" -X POST http://localhost:8000/attack \
  -H "Content-Type: application/json" \
  -d '{"technique_id": "T1046", "params": {"cidr_or_host": "10.0.0.5", "rate": 1000}}'
```

See [Quick Start](quick-start.md) for token setup.