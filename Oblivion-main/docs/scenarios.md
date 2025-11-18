# Scenarios

Define multi-step attack plans in YAML.

## Scenario YAML Schema

```yaml
steps:
  - technique_id: T1046
    params:
      cidr_or_host: 10.0.0.5
      rate: 1000
  - technique_id: T1190
    params:
      exploit_name: exploit/unix/ftp/vsftpd_234_backdoor
      rhost: 10.0.0.10
      rport: 21
```

## Example Scenarios

- [web_scan.yaml](scenarios/examples/web_scan.yaml)
- [exploit_chain.yaml](scenarios/examples/exploit_chain.yaml)

## Scenario Library

Place your own scenarios in the `docs/scenarios/examples/` directory and link them here.