import os
import json
from threading import Lock

class AssetStore:
    def __init__(self, path='assets.json'):
        self.path = os.path.abspath(path)
        self.lock = Lock()
        self._hosts = {}  # ip -> {"ip": ip, "hostname": str or None}
        self._services = []  # List of {"ip", "port", "proto", "service"}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for h in data.get("hosts", []):
                    self._hosts[h["ip"]] = {"ip": h["ip"], "hostname": h.get("hostname")}
                self._services = data.get("services", [])
            except Exception:
                self._hosts = {}
                self._services = []

    def add_host(self, ip, hostname=None):
        with self.lock:
            if ip not in self._hosts:
                self._hosts[ip] = {"ip": ip, "hostname": hostname}
            elif hostname:
                self._hosts[ip]["hostname"] = hostname
            self.save()

    def add_service(self, ip, port, proto, service):
        with self.lock:
            entry = {"ip": ip, "port": int(port), "proto": proto, "service": service}
            if entry not in self._services:
                self._services.append(entry)
            self.save()

    def get_summary(self):
        with self.lock:
            return {
                "hosts": list(self._hosts.values()),
                "services": list(self._services)
            }

    def save(self):
        with self.lock:
            data = self.get_summary()
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def close(self):
        pass  # Placeholder for future resource management