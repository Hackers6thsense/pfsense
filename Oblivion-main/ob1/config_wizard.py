import yaml
import os
from datetime import datetime, timedelta
import click

def run_wizard(default_path="policy.yaml"):
    click.echo("Welcome to the Oblivion Config Wizard.\n")
    engagement_id = click.prompt("Engagement ID", default="lab-engagement")
    now = datetime.now().replace(microsecond=0)
    valid_from = click.prompt("Valid from (ISO8601)", default=now.isoformat())
    valid_to = click.prompt("Valid to (ISO8601)", default=(now + timedelta(days=7)).isoformat())
    cidrs = click.prompt("Allowed CIDRs (comma-separated)", default="10.0.0.0/24")
    hostnames = click.prompt("Allowed hostnames (comma-separated)", default="lab.internal")

    cidr_list = [x.strip() for x in cidrs.split(",") if x.strip()]
    host_list = [x.strip() for x in hostnames.split(",") if x.strip()]

    policy = {
        "engagement_id": engagement_id,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "allowed_targets": {
            "cidrs": cidr_list,
            "hostnames": host_list
        }
    }
    path = click.prompt(f"Policy YAML path", default=default_path)
    if os.path.exists(path):
        if not click.confirm(f"File {path} exists. Overwrite?", default=False):
            click.echo("Aborted.")
            return
    with open(path, "w") as f:
        yaml.safe_dump(policy, f)
    click.echo(f"[+] Wrote policy to {path}")

    mistral = click.prompt("Enter your Mistral API key (or leave blank to skip)", default="", show_default=False)
    if mistral:
        bashrc = os.path.expanduser("~/.bashrc")
        export_line = f"export MISTRAL_API_KEY='{mistral}'\n"
        if click.confirm(f"Append export to {bashrc}?", default=True):
            with open(bashrc, "a") as f:
                f.write(export_line)
            click.echo(f"[+] Added to {bashrc}: {export_line.strip()}")
        else:
            click.echo(f"Add this to your shell: {export_line.strip()}")
    click.echo("[*] Config wizard complete.")