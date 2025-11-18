# Installation

Oblivion can be deployed in multiple ways:

## Via pip (recommended for Python users)

```bash
pip install oblivion-redteam
```
After installation, use the `oblivion` CLI:

```bash
oblivion api
oblivion dashboard
```

## Docker Compose

Oblivion comes with a Dockerfile and docker-compose.yml:

```bash
docker compose up --build
```

This will start Oblivion and Metasploit services.

## Kali Linux Lab

A helper script is provided:

```bash
chmod +x setup_kali.sh
./setup_kali.sh
```

This installs dependencies and starts msfrpcd for Metasploit integration.

See the [Quick Start](quick-start.md) for a walkthrough.