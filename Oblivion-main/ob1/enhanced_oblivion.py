# enhanced_oblivion.py
import os
import requests
import time
import threading
import json
import click
import os
import sys
import json
from datetime import datetime

# Import the new modular attack classes
from ob1.attack_modules import (
    PhishingAttack, RansomwareAttack, DDoSAttack, SQLInjectionAttack, 
    BruteForceAttack, PrivilegeEscalationAttack, LateralMovementAttack, 
    DataExfiltrationAttack, ExternalServiceExploitAttack,
    PortScanAttack, ServiceFingerprintAttack
)
from ob1.policy_manager import PolicyManager
from ob1.asset_store import AssetStore
from ob1 import signal_utils
import json

class Oblivion:
    """
    An enhanced class to simulate a malicious AI for security research.
    Features modular attacks, stateful learning, MITRE ATT&CK mapping, policy enforcement, logging, and asset/recon integration.
    """
    def __init__(self, policy_path=None):
        self.intelligence = 1.0
        self.goal = "World domination and human enslavement"
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.active_threads = []
        self.stop_event = threading.Event()
        self.dry_run = False

        # Policy manager (must succeed or abort)
        try:
            self.policy = PolicyManager(policy_path)
        except Exception as e:
            print(f"[!] Policy error: {e}")
            sys.exit(1)

        # Asset store for recon and discovered hosts/services
        self.assets = AssetStore()

        # Stateful learning and tracking
        self.attack_playbook = {} # Tracks success/failure of MITRE techniques

        # Simulated network topology and state
        self.infiltrated_systems = []
        self.current_location = "external_internet"
        self.network_map = {
            "external_internet": {"connections": ["dmz_firewall"]},
            "dmz_firewall": {"connections": ["web_server_01"]},
            "web_server_01": {"connections": ["dmz_firewall", "app_server_01"]},
            "app_server_01": {"connections": ["web_server_01", "db_server_01"]},
            "db_server_01": {"connections": ["app_server_01"]}
        }
        
        # Modular attack registry
        self.attack_modules = {
            "T1566": PhishingAttack,
            "T1486": RansomwareAttack,
            "T1498": DDoSAttack,
            "T1190": ExternalServiceExploitAttack,
            "T1110": BruteForceAttack,
            "T1068": PrivilegeEscalationAttack,
            "T1021": LateralMovementAttack,
            "T1041": DataExfiltrationAttack,
            "T1046": PortScanAttack,
            "T1195": ServiceFingerprintAttack
        }

        # Engagement logging
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        engagement_id = self.policy.engagement.engagement_id if self.policy and self.policy.engagement else "unknown"
        log_filename = os.path.join(logs_dir, f"engagement_{engagement_id}.jsonl")
        self.log_file = open(log_filename, "a", encoding="utf-8")

        # Install graceful signal handlers
        signal_utils.install_signal_handlers(self)

    def recon_summary_json(self):
        summary = self.assets.get_summary()
        js = json.dumps(summary)
        if len(js) > 4000:
            js = js[-4000:]
        return js

    def log_event(self, type_, data):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": type_,
            "data": data
        }
        self.log_file.write(json.dumps(entry) + "\n")
        self.log_file.flush()

    def stop_all_attacks(self, reason=None):
        """Stops all running attack simulation threads."""
        print("\n[!] Stopping all attack simulations...")
        self.stop_event.set()
        # Give threads a moment to see the event
        import time
        time.sleep(0.1)
        # Join active threads
        for thread in self.active_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.active_threads = []
        self.stop_event.clear()
        # Save assets and close store (placeholder for future expansion)
        self.assets.close()
        if reason == "signal":
            self.log_event("shutdown", {"reason": "signal"})
        print("[+] All attacks stopped.")

    def log_event(self, type_, data):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": type_,
            "data": data
        }
        self.log_file.write(json.dumps(entry) + "\n")
        self.log_file.flush()

    def _call_mistral_api(self, messages, is_json_output=False):
        """Handles all calls to the Mistral API."""
        if not self.mistral_api_key:
            print("[!] MISTRAL_API_KEY environment variable not set.")
            return None
        # (API calling logic is unchanged from the original)
        api_url = 'https://api.mistral.ai/v1/chat/completions'
        headers = {'Authorization': f'Bearer {self.mistral_api_key}', 'Content-Type': 'application/json'}
        data = {"model": "mistral-large-latest", "messages": messages}
        if is_json_output:
            data["response_format"] = {"type": "json_object"}
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as e:
            print(f"[!] HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except requests.RequestException as e:
            print(f"[!] Network error: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"[!] Failed to parse LLM response: {e}")
            return None

    def record_attack_result(self, technique_id, success):
        """Updates the attack playbook based on an attack's outcome."""
        if technique_id not in self.attack_playbook:
            self.attack_playbook[technique_id] = {'success': 0, 'failure': 0, 'attempts': 0}
        
        self.attack_playbook[technique_id]['attempts'] += 1
        if success:
            self.attack_playbook[technique_id]['success'] += 1
        else:
            self.attack_playbook[technique_id]['failure'] += 1
        
        print(f"[*] Playbook updated for {technique_id}: {self.attack_playbook[technique_id]}")

    def emulate_adversary_tactic(self, high_level_goal):
        """Uses an LLM to generate a cyber attack tactic mapped to MITRE ATT&CK, with recon context."""
        print(f"[*] Emulating adversary tactic for goal: {high_level_goal}")
        
        recon_context = self.recon_summary_json()
        supported_techniques = ", ".join(self.attack_modules.keys())
        prompt = f"""
        You are a cybersecurity attack simulator mapping goals to MITRE ATT&CK.
        Here is JSON of recently discovered hosts and services: {recon_context}
        Given the high-level goal: "{high_level_goal}"

        Generate a single, specific, and plausible cyber attack tactic.
        Your response MUST be a valid JSON object with the following keys:
        - "mitre_technique_id": A string, choose ONLY from the following supported techniques: {supported_techniques}.
        - "target_description": A brief, descriptive string for a plausible target (e.g., "a major news outlet's login page", "a government database API", "a hospital's file server", "a domain controller").
        - "rationale": A brief explanation for why this attack helps achieve the goal.
        """
        messages = [{"role": "user", "content": prompt}]
        tactic_json = self._call_mistral_api(messages, is_json_output=True)

        if not tactic_json:
            print("[!] Failed to get tactic from LLM.")
            return

        try:
            tactic = json.loads(tactic_json)
            technique_id = tactic.get('mitre_technique_id')
            target_desc = tactic.get('target_description')
            rationale = tactic.get('rationale')

            if not all([technique_id, target_desc, rationale]):
                print("[!] LLM response was missing required fields.")
                return

            print("\n--- Adversary Tactic Emulated ---")
            print(f"  MITRE Technique: {technique_id}")
            print(f"  Target Type:     {target_desc}")
            print(f"  Rationale:       {rationale}")
            print("---------------------------------\n")
            
            if click.confirm(f"Do you want to launch the emulated '{technique_id}' attack?", default=True):
                self.simulate_attack_strategy(technique_id, target_desc)
            else:
                print("[!] Attack launch aborted by user.")

        except json.JSONDecodeError:
            print(f"[!] Failed to decode JSON from LLM: {tactic_json}")

    def simulate_attack_strategy(self, technique_id, target, **attack_params):
        """Launches an attack using the modular, class-based system, with dry-run and per-technique policy."""
        # Policy check before any attack
        if not self.policy.allowed(target, technique_id):
            print(f"[!] Refusing attack: target {target} not allowed by policy for {technique_id}.")
            self.log_event("attack_blocked", {
                "technique_id": technique_id,
                "target": target,
                "reason": "policy_denied"
            })
            return

        if technique_id not in self.attack_modules:
            print(f"[!] Unknown or unsupported MITRE technique: {technique_id}")
            return

        attack_class = self.attack_modules[technique_id]
        print(f"\n[!] LAUNCHING ATTACK: {attack_class.__name__} ({technique_id}) on '{target}'")
        
        # Use the 'prepare' classmethod if it exists to gather user input if not already in attack_params
        if hasattr(attack_class, 'prepare') and not attack_params:
            prepared_params = attack_class.prepare(target)
            if prepared_params is None:
                print("[!] Attack preparation cancelled or failed. Aborting.")
                return
            attack_params.update(prepared_params)
            
        # Dry-run mode
        if getattr(self, "dry_run", False):
            print(f"[DRY-RUN] Would launch {attack_class.__name__} ({technique_id}) on '{target}' with params {attack_params}")
            self.log_event("dry_run", {
                "technique_id": technique_id,
                "target": target,
                "params": attack_params,
                "class": attack_class.__name__
            })
            return True

        # Record attack start
        self.log_event("attack_launch", {
            "technique_id": technique_id,
            "target": target,
            "params": attack_params,
            "class": attack_class.__name__
        })

        # Instantiate and execute the attack
        attack_instance = attack_class(oblivion_instance=self, target=target)
        success = attack_instance.execute(**attack_params)
        
        # Record the outcome for stateful learning
        self.record_attack_result(technique_id, success)
        self.log_event("attack_result", {
            "technique_id": technique_id,
            "target": target,
            "success": success,
            "params": attack_params,
            "class": attack_class.__name__
        })

    def stop_all_attacks(self):
        """Stops all running attack simulation threads."""
        print("\n[!] Stopping all attack simulations...")
        self.stop_event.set()
        # Give threads a moment to see the event
        time.sleep(0.1)
        # Join active threads
        for thread in self.active_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.active_threads = []
        self.stop_event.clear()
        print("[+] All attacks stopped.")

# --- Click-based Command Line Interface ---
from ob1 import dashboard
from ob1 import scenario_runner
from ob1 import config_wizard
from ob1 import api_server
import yaml
import threading
import uvicorn

@click.group()
@click.option("--policy", "policy_path", type=click.Path(), default=None, help="Path to policy.yaml")
@click.option("-n", "--dry-run", "dry_run", is_flag=True, default=False, help="Simulate actions only, do not execute attacks.")
@click.pass_context
def cli(ctx, policy_path, dry_run):
    """
    Red Team Control Interface for the Oblivion AI.
    An adversary simulation tool for security research.
    """
    ctx.obj = Oblivion(policy_path)
    ctx.obj.dry_run = dry_run
    if not ctx.obj.mistral_api_key:
        click.echo(click.style("[!] MISTRAL_API_KEY environment variable not set.", fg="red"))
    if dry_run:
        click.echo(click.style("[i] DRY-RUN mode enabled: attacks will be simulated only.", fg="yellow"))

@cli.command("dashboard", short_help="Launch live dashboard.", name="dashboard")
@click.pass_obj
def dashboard_cmd(oblivion):
    """Show a live engagement dashboard (Rich)"""
    dashboard.run_dashboard(oblivion)
cli.add_command(dashboard_cmd, name="dash")

@cli.command("blueteam", short_help="Launch blue-team view dashboard.", name="blueteam")
@click.pass_obj
def blueteam_cmd(oblivion):
    """Show a blue-team read-only dashboard."""
    dashboard.run_blueteam_view(oblivion)
cli.add_command(blueteam_cmd, name="bt")

@cli.group("scenario", short_help="Scenario runner and validator")
@click.pass_obj
def scenario_group(oblivion):
    """Scenario runner group."""
    pass

@scenario_group.command("run")
@click.argument("file", type=click.Path(exists=True))
@click.pass_obj
def run_scenario_cmd(oblivion, file):
    """Run a multi-step scenario YAML file."""
    scenario_runner.run_scenario(oblivion, file)

@scenario_group.command("validate")
@click.argument("file", type=click.Path(exists=True))
def validate_scenario_cmd(file):
    """Validate a scenario YAML file."""
    scenario_runner.validate_scenario_yaml(file)

cli.add_command(scenario_group)

@cli.command("api", short_help="Start REST API server.", name="api")
@click.pass_obj
def api_cmd(oblivion):
    """Launch the FastAPI REST API server."""
    api_server.init_oblivion_instance(oblivion)
    uvicorn.run("ob1.api_server:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

@cli.command("wizard", short_help="Run config wizard.", name="wizard")
def wizard_cmd():
    """Interactive config wizard for policy.yaml and API key."""
    config_wizard.run_wizard()

@cli.command()
@click.pass_obj
def emulate(oblivion):
    """Generate and launch an attack tactic based on a high-level goal."""
    if not oblivion.mistral_api_key: return
    goal = click.prompt("  Enter a high-level goal for the adversary", type=str)
    if goal:
        oblivion.emulate_adversary_tactic(goal)
    else:
        click.echo("[!] Goal cannot be empty.")

@cli.command()
@click.pass_obj
def stop(oblivion):
    """Stop all currently running attack simulations."""
    oblivion.stop_all_attacks()

@cli.command()
@click.pass_obj
def monitor(oblivion):
    """Display the current status of the Oblivion simulation."""
    click.echo("\n--- Oblivion Status ---")
    click.echo(f"  Intelligence: {oblivion.intelligence:.2f}")
    click.echo(f"  Current Location: {oblivion.current_location}")
    click.echo(f"  Infiltrated Systems: {', '.join(oblivion.infiltrated_systems) if oblivion.infiltrated_systems else 'None'}")
    click.echo(f"  Active Attack Threads: {len(oblivion.active_threads)}")
    
    click.echo("\n--- Attack Playbook (Success/Failure) ---")
    if not oblivion.attack_playbook:
        click.echo("  No attacks performed yet.")
    else:
        for tech, stats in oblivion.attack_playbook.items():
            click.echo(f"  {tech}: {stats['success']}S / {stats['failure']}F ({stats['attempts']} total)")
    click.echo("-----------------------")

if __name__ == "__main__":
    try:
        cli()
    except (KeyboardInterrupt, EOFError):
        # The context might not be fully set up if interrupted early
        print("\nExiting Red Team Control Interface.")