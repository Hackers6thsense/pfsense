# Safety & Policy

## Policy File

Oblivion enforces a YAML policy:

```yaml
engagement_id: demo-lab
valid_from: "2025-08-01T00:00:00+00:00"
valid_to: "2025-12-31T23:59:59+00:00"
allowed_targets:
  cidrs: ["10.0.0.0/24"]
  hostnames: ["lab.internal"]
technique_overrides:
  T1046:
    allowed_targets:
      cidrs: ["0.0.0.0/0"]
      hostnames: []
  T1190:
    allowed_targets:
      cidrs: ["10.0.0.0/24"]
      hostnames: ["staging.*"]
```

## Technique Overrides

- Restrict specific attack types to certain networks or hosts.
- If omitted, top-level targets apply to all.

## Dry-Run Mode

- Add `--dry-run` or `-n` to any CLI command to simulate actions.
- API and dashboards indicate dry-run status.
- All actions are logged as `dry_run`.

## Policy Hot-Reload

- Changes to policy.yaml are detected and loaded automatically.