import yaml
import time
import click

def run_scenario(oblivion, path, steps=None):
    if steps is None:
        with open(path, "r") as f:
            doc = yaml.safe_load(f)
        if not isinstance(doc, dict) or "steps" not in doc or not isinstance(doc["steps"], list):
            print("[!] Invalid scenario file: must contain 'steps' list.")
            return
        steps = doc["steps"]
        if not steps:
            print("[!] Scenario has no steps.")
            return

    print(f"[*] Running scenario{' from '+path if path else ''} with {len(steps)} steps.")
    successes = 0
    for i, step in enumerate(steps, 1):
        tech = step.get("technique_id")
        params = step.get("params", {})
        if not tech:
            print(f"[!] Step {i}: missing technique_id, skipping.")
            continue
        print(f"[{i}/{len(steps)}] Executing {tech} with params {params}")
        try:
            res = oblivion.simulate_attack_strategy(tech, **params)
            if res is not False:
                successes += 1
        except Exception as e:
            print(f"[!] Step {i} failed: {e}")
        time.sleep(1)
    print(f"[+] Scenario complete: {successes}/{len(steps)} steps executed.")

def validate_scenario_yaml(path):
    try:
        with open(path, "r") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        print(f"[!] YAML error: {e}")
        return False
    if not isinstance(doc, dict) or "steps" not in doc or not isinstance(doc["steps"], list):
        print("[!] Invalid scenario: must be a dict with 'steps' as a list.")
        return False
    for i, step in enumerate(doc["steps"]):
        if not isinstance(step, dict) or "technique_id" not in step:
            print(f"[!] Step {i+1} missing technique_id.")
            return False
        if "params" in step and not isinstance(step["params"], dict):
            print(f"[!] Step {i+1} params must be a dict.")
            return False
    print("[+] Scenario YAML OK.")
    return True