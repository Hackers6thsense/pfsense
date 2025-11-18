# Instructor Guide

This guide offers tips for using Oblivion in blue-team/red-team exercises.

## Setting Up

- Use the config wizard to create a scoped policy and engagement window.
- Set a strong API token for class/lab use.
- Use dry-run mode for demos or planning.

## Lab Exercises

- **Recon Only:** Scan lab network, identify services, no exploitation.
- **Exploit Chain:** Scan, fingerprint, exploit, exfiltrate mock data.
- **Phishing Simulation:** Run disinfo/phishing modules.

## Blue-Team View

- Direct students to the browser dashboard with a read-only API token.
- Display only playbook and asset summary, not exploit details.

## Scoring Ideas

- Points for detecting attacks in logs
- Bonus for stopping attacks quickly
- Use log events for after-action review

## Troubleshooting

- Use the dashboard log tail to diagnose issues.
- Use `--dry-run` to rehearse before real attacks.