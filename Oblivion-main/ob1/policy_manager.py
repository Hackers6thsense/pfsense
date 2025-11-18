import os
import yaml
import fnmatch
import ipaddress
import threading
import time
from datetime import datetime, timezone

class Engagement:
    def __init__(self, engagement_id, valid_from, valid_to, allowed_targets, technique_overrides=None):
        self.engagement_id = engagement_id
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.allowed_targets = allowed_targets
        self.technique_overrides = technique_overrides or {}

    @classmethod
    def from_dict(cls, d):
        id_ = d.get("engagement_id")
        valid_from = datetime.fromisoformat(d["valid_from"]).astimezone(timezone.utc)
        valid_to = datetime.fromisoformat(d["valid_to"]).astimezone(timezone.utc)
        allowed_targets = d["allowed_targets"]
        technique_overrides = d.get("technique_overrides", {})
        return cls(id_, valid_from, valid_to, allowed_targets, technique_overrides)

class PolicyManager:
    DEFAULT_POLICY_PATH = os.path.abspath(os.getenv("OBLIVION_POLICY_FILE", "policy.yaml"))

    def __init__(self, path=None):
        self.path = os.path.abspath(path) if path else self.DEFAULT_POLICY_PATH
        self.engagement = None
        self._last_mtime = None
        self._load_policy()
        self._start_hot_reload()

    def _load_policy(self):
        if not os.path.isfile(self.path):
            raise ValueError(f"Policy file not found: {self.path}")
        with open(self.path, "r") as f:
            doc = yaml.safe_load(f)
        self.engagement = Engagement.from_dict(doc)
        self.validate()
        self._last_mtime = os.path.getmtime(self.path)

    def validate(self):
        now = datetime.now(timezone.utc)
        if not (self.engagement.valid_from <= now <= self.engagement.valid_to):
            raise ValueError(
                f"Engagement {self.engagement.engagement_id} not valid at {now.isoformat()} "
                f"(window: {self.engagement.valid_from.isoformat()} to {self.engagement.valid_to.isoformat()})"
            )

    def _allowed_for_tech(self, tech_id, host_or_ip):
        allowed_targets = None
        if self.engagement.technique_overrides and tech_id and tech_id in self.engagement.technique_overrides:
            override = self.engagement.technique_overrides[tech_id]
            allowed_targets = override.get("allowed_targets", None)
        if not allowed_targets:
            allowed_targets = self.engagement.allowed_targets

        try:
            ip = ipaddress.ip_address(host_or_ip)
            for cidr in allowed_targets.get("cidrs", []):
                try:
                    if ip in ipaddress.ip_network(cidr, strict=False):
                        return True
                except Exception:
                    continue
        except ValueError:
            # Not an IP, treat as hostname
            for pattern in allowed_targets.get("hostnames", []):
                if fnmatch.fnmatch(host_or_ip, pattern):
                    return True
        return False

    def allowed(self, host_or_ip: str, tech_id: str = None) -> bool:
        return self._allowed_for_tech(tech_id, host_or_ip)

    # Legacy support for allowed(host_or_ip) signature
    def __call__(self, host_or_ip: str, tech_id: str = None) -> bool:
        return self.allowed(host_or_ip, tech_id)

    def _start_hot_reload(self):
        def watcher():
            while True:
                try:
                    mtime = os.path.getmtime(self.path)
                    if self._last_mtime is not None and mtime != self._last_mtime:
                        self._load_policy()
                        print("[i] Policy reloaded")
                except Exception:
                    pass
                time.sleep(5)
        t = threading.Thread(target=watcher, daemon=True)
        t.start()