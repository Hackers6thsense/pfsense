"""
Security Scanner Agent for pfSense Multi-Agent System

This agent specializes in vulnerability scanning, security assessments,
and compliance checking for the network infrastructure.
"""

import asyncio
import json
import logging
import subprocess
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import paramiko
import socket
from concurrent.futures import ThreadPoolExecutor

from ..core.base_agent import BaseAgent, AgentConfig, AgentMessage
from ..llm_integration.llm_client import get_llm_client


@dataclass
class VulnerabilityFinding:
    """Represents a vulnerability finding."""
    host: str
    port: int
    service: str
    vulnerability_id: str
    severity: str
    description: str
    cvss_score: float
    remediation: str
    discovered_at: datetime


@dataclass
class PortScanResult:
    """Results from a port scan."""
    host: str
    port: int
    state: str
    service: str
    version: str
    banner: str


@dataclass
class ComplianceCheck:
    """Compliance check result."""
    check_id: str
    name: str
    description: str
    status: str  # 'pass', 'fail', 'warning'
    severity: str
    details: str
    remediation: str


class SecurityScannerAgent(BaseAgent):
    """
    Specialized agent for security scanning and vulnerability assessment.
    
    Capabilities:
    - Network port scanning
    - Vulnerability detection and assessment
    - Compliance checking against security standards
    - Security configuration analysis
    - Threat intelligence integration
    - Risk assessment and prioritization
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Scanning configuration
        self.scan_interval = 3600  # 1 hour
        self.vulnerability_db_update = 86400  # 24 hours
        self.scan_types = ['port_scan', 'vulnerability_scan', 'compliance_check']
        
        # Network configuration
        self.target_networks = ['192.168.1.0/24', '10.0.0.0/24']  # Default networks to scan
        self.excluded_hosts = set()  # Hosts to exclude from scanning
        
        # SSH connection for pfSense interaction
        self.ssh_client = None
        self.ssh_connected = False
        
        # Scan results storage
        self.scan_results: Dict[str, List] = {
            'port_scans': [],
            'vulnerabilities': [],
            'compliance_checks': []
        }
        
        # Vulnerability database
        self.vulnerability_db = {}
        self.last_db_update = None
        
        # Thread pool for concurrent scanning
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        # Statistics
        self.scan_stats = {
            'scans_performed': 0,
            'vulnerabilities_found': 0,
            'compliance_issues': 0,
            'hosts_scanned': 0
        }
        
        # LLM client
        self.llm_client = get_llm_client()
        
        self.logger.info(f"Security Scanner Agent initialized for networks: {self.target_networks}")
    
    async def initialize(self):
        """Initialize security scanner specific resources."""
        # Subscribe to security-related topics
        self.config.subscribed_topics = [
            'security.scan_request',
            'system.tasks',
            'security.alerts'
        ]
        
        # Setup SSH connection
        await self._setup_ssh_connection()
        
        # Initialize vulnerability database
        await self._initialize_vulnerability_db()
        
        # Start scanning tasks
        asyncio.create_task(self._scheduled_scan_loop())
        asyncio.create_task(self._vulnerability_db_update_loop())
        
        self.logger.info("Security Scanner initialization completed")
    
    async def run(self):
        """Main execution loop."""
        self.logger.info("Security Scanner Agent started")
        
        while self.is_running:
            try:
                # Perform periodic maintenance
                await self._cleanup_old_results()
                await self._update_statistics()
                
                # Check SSH connection health
                if not self.ssh_connected:
                    await self._setup_ssh_connection()
                
                await asyncio.sleep(300)  # Main loop every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(300)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.ssh_client:
            self.ssh_client.close()
        self.thread_pool.shutdown(wait=True)
        self.logger.info("Security Scanner cleanup completed")
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        try:
            if message.message_type == 'scan_request':
                await self._handle_scan_request(message)
            elif message.message_type == 'task_assignment':
                await self._handle_task_assignment(message)
            elif message.message_type == 'vulnerability_report':
                await self._handle_vulnerability_report(message)
            else:
                self.logger.debug(f"Unhandled message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _setup_ssh_connection(self):
        """Setup SSH connection to pfSense."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.config.pfsense_host,
                port=self.config.pfsense_ssh_port,
                username=self.config.pfsense_username,
                timeout=self.config.connection_timeout
            )
            
            self.ssh_connected = True
            self.logger.info("SSH connection to pfSense established")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to pfSense via SSH: {e}")
            self.ssh_connected = False
    
    async def _scheduled_scan_loop(self):
        """Perform scheduled security scans."""
        while self.is_running:
            try:
                # Perform comprehensive scan
                await self._perform_comprehensive_scan()
                
                # Wait for next scan interval
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in scheduled scan loop: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def _vulnerability_db_update_loop(self):
        """Update vulnerability database periodically."""
        while self.is_running:
            try:
                await self._update_vulnerability_db()
                await asyncio.sleep(self.vulnerability_db_update)
                
            except Exception as e:
                self.logger.error(f"Error updating vulnerability database: {e}")
                await asyncio.sleep(self.vulnerability_db_update)
    
    async def _perform_comprehensive_scan(self):
        """Perform a comprehensive security scan."""
        self.logger.info("Starting comprehensive security scan")
        
        # Discover active hosts
        active_hosts = await self._discover_active_hosts()
        self.logger.info(f"Discovered {len(active_hosts)} active hosts")
        
        # Perform port scans
        port_scan_results = await self._perform_port_scans(active_hosts)
        
        # Perform vulnerability scans
        vulnerability_results = await self._perform_vulnerability_scans(active_hosts)
        
        # Perform compliance checks
        compliance_results = await self._perform_compliance_checks()
        
        # Analyze results with LLM
        await self._analyze_scan_results(port_scan_results, vulnerability_results, compliance_results)
        
        self.scan_stats['scans_performed'] += 1
        self.scan_stats['hosts_scanned'] = len(active_hosts)
        
        self.logger.info("Comprehensive security scan completed")
    
    async def _discover_active_hosts(self) -> List[str]:
        """Discover active hosts in target networks."""
        active_hosts = []
        
        for network in self.target_networks:
            try:
                network_obj = ipaddress.ip_network(network, strict=False)
                
                # Use ping to discover active hosts
                tasks = []
                for host in network_obj.hosts():
                    if str(host) not in self.excluded_hosts:
                        tasks.append(self._ping_host(str(host)))
                
                # Execute ping tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if result is True:  # Host is active
                        host_ip = str(list(network_obj.hosts())[i])
                        active_hosts.append(host_ip)
                        
            except Exception as e:
                self.logger.error(f"Error discovering hosts in network {network}: {e}")
        
        return active_hosts
    
    async def _ping_host(self, host: str) -> bool:
        """Ping a host to check if it's active."""
        try:
            # Use asyncio subprocess for non-blocking ping
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1', host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await asyncio.wait_for(process.wait(), timeout=2.0)
            return process.returncode == 0
            
        except (asyncio.TimeoutError, Exception):
            return False
    
    async def _perform_port_scans(self, hosts: List[str]) -> List[PortScanResult]:
        """Perform port scans on active hosts."""
        self.logger.info(f"Starting port scans on {len(hosts)} hosts")
        
        # Common ports to scan
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1433, 3389, 5900]
        
        scan_results = []
        
        # Create scanning tasks
        tasks = []
        for host in hosts:
            for port in common_ports:
                tasks.append(self._scan_port(host, port))
        
        # Execute scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, PortScanResult):
                scan_results.append(result)
        
        # Store results
        self.scan_results['port_scans'].extend(scan_results)
        
        self.logger.info(f"Port scan completed. Found {len(scan_results)} open ports")
        return scan_results
    
    async def _scan_port(self, host: str, port: int) -> Optional[PortScanResult]:
        """Scan a specific port on a host."""
        try:
            # Use asyncio to create a non-blocking socket connection
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=2.0)
            
            # Try to get service banner
            banner = ""
            try:
                writer.write(b'\r\n')
                await writer.drain()
                data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                banner = data.decode('utf-8', errors='ignore').strip()
            except:
                pass
            
            writer.close()
            await writer.wait_closed()
            
            # Identify service
            service = self._identify_service(port, banner)
            version = self._extract_version(banner)
            
            return PortScanResult(
                host=host,
                port=port,
                state='open',
                service=service,
                version=version,
                banner=banner
            )
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None
        except Exception as e:
            self.logger.debug(f"Error scanning {host}:{port}: {e}")
            return None
    
    def _identify_service(self, port: int, banner: str) -> str:
        """Identify service based on port and banner."""
        service_map = {
            21: 'ftp',
            22: 'ssh',
            23: 'telnet',
            25: 'smtp',
            53: 'dns',
            80: 'http',
            110: 'pop3',
            135: 'rpc',
            139: 'netbios',
            143: 'imap',
            443: 'https',
            993: 'imaps',
            995: 'pop3s',
            1433: 'mssql',
            3389: 'rdp',
            5900: 'vnc'
        }
        
        service = service_map.get(port, 'unknown')
        
        # Refine based on banner
        if banner:
            banner_lower = banner.lower()
            if 'ssh' in banner_lower:
                service = 'ssh'
            elif 'http' in banner_lower:
                service = 'http'
            elif 'ftp' in banner_lower:
                service = 'ftp'
            elif 'smtp' in banner_lower:
                service = 'smtp'
        
        return service
    
    def _extract_version(self, banner: str) -> str:
        """Extract version information from service banner."""
        if not banner:
            return ""
        
        # Simple version extraction patterns
        import re
        
        version_patterns = [
            r'(\d+\.\d+\.\d+)',
            r'(\d+\.\d+)',
            r'version\s+(\S+)',
            r'v(\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    async def _perform_vulnerability_scans(self, hosts: List[str]) -> List[VulnerabilityFinding]:
        """Perform vulnerability scans on hosts."""
        self.logger.info(f"Starting vulnerability scans on {len(hosts)} hosts")
        
        vulnerability_findings = []
        
        # Get recent port scan results for these hosts
        recent_port_scans = [
            result for result in self.scan_results['port_scans']
            if result.host in hosts
        ]
        
        # Check each open service for known vulnerabilities
        for port_result in recent_port_scans:
            vulnerabilities = await self._check_service_vulnerabilities(port_result)
            vulnerability_findings.extend(vulnerabilities)
        
        # Store results
        self.scan_results['vulnerabilities'].extend(vulnerability_findings)
        self.scan_stats['vulnerabilities_found'] += len(vulnerability_findings)
        
        # Generate alerts for high-severity vulnerabilities
        for vuln in vulnerability_findings:
            if vuln.severity in ['high', 'critical']:
                await self._generate_vulnerability_alert(vuln)
        
        self.logger.info(f"Vulnerability scan completed. Found {len(vulnerability_findings)} vulnerabilities")
        return vulnerability_findings
    
    async def _check_service_vulnerabilities(self, port_result: PortScanResult) -> List[VulnerabilityFinding]:
        """Check a service for known vulnerabilities."""
        vulnerabilities = []
        
        # Check against vulnerability database
        service_key = f"{port_result.service}:{port_result.version}"
        
        if service_key in self.vulnerability_db:
            for vuln_data in self.vulnerability_db[service_key]:
                vulnerability = VulnerabilityFinding(
                    host=port_result.host,
                    port=port_result.port,
                    service=port_result.service,
                    vulnerability_id=vuln_data['id'],
                    severity=vuln_data['severity'],
                    description=vuln_data['description'],
                    cvss_score=vuln_data.get('cvss_score', 0.0),
                    remediation=vuln_data.get('remediation', ''),
                    discovered_at=datetime.now()
                )
                vulnerabilities.append(vulnerability)
        
        # Check for common misconfigurations
        misconfig_vulns = await self._check_misconfigurations(port_result)
        vulnerabilities.extend(misconfig_vulns)
        
        return vulnerabilities
    
    async def _check_misconfigurations(self, port_result: PortScanResult) -> List[VulnerabilityFinding]:
        """Check for common service misconfigurations."""
        vulnerabilities = []
        
        # SSH misconfiguration checks
        if port_result.service == 'ssh':
            if 'root login' in port_result.banner.lower():
                vulnerabilities.append(VulnerabilityFinding(
                    host=port_result.host,
                    port=port_result.port,
                    service=port_result.service,
                    vulnerability_id='SSH-001',
                    severity='medium',
                    description='SSH root login enabled',
                    cvss_score=5.0,
                    remediation='Disable root login in SSH configuration',
                    discovered_at=datetime.now()
                ))
        
        # HTTP/HTTPS misconfiguration checks
        elif port_result.service in ['http', 'https']:
            if port_result.service == 'http' and port_result.port == 80:
                vulnerabilities.append(VulnerabilityFinding(
                    host=port_result.host,
                    port=port_result.port,
                    service=port_result.service,
                    vulnerability_id='HTTP-001',
                    severity='low',
                    description='Unencrypted HTTP service detected',
                    cvss_score=3.0,
                    remediation='Implement HTTPS encryption',
                    discovered_at=datetime.now()
                ))
        
        # Telnet service check
        elif port_result.service == 'telnet':
            vulnerabilities.append(VulnerabilityFinding(
                host=port_result.host,
                port=port_result.port,
                service=port_result.service,
                vulnerability_id='TELNET-001',
                severity='high',
                description='Insecure Telnet service detected',
                cvss_score=7.5,
                remediation='Replace Telnet with SSH',
                discovered_at=datetime.now()
            ))
        
        return vulnerabilities
    
    async def _perform_compliance_checks(self) -> List[ComplianceCheck]:
        """Perform compliance checks against security standards."""
        self.logger.info("Starting compliance checks")
        
        compliance_results = []
        
        # Check pfSense configuration compliance
        if self.ssh_connected:
            pfsense_checks = await self._check_pfsense_compliance()
            compliance_results.extend(pfsense_checks)
        
        # Check network security compliance
        network_checks = await self._check_network_compliance()
        compliance_results.extend(network_checks)
        
        # Store results
        self.scan_results['compliance_checks'].extend(compliance_results)
        
        # Count failed checks
        failed_checks = [check for check in compliance_results if check.status == 'fail']
        self.scan_stats['compliance_issues'] += len(failed_checks)
        
        # Generate alerts for failed compliance checks
        for check in failed_checks:
            if check.severity in ['high', 'critical']:
                await self._generate_compliance_alert(check)
        
        self.logger.info(f"Compliance checks completed. {len(failed_checks)} issues found")
        return compliance_results
    
    async def _check_pfsense_compliance(self) -> List[ComplianceCheck]:
        """Check pfSense configuration for compliance."""
        checks = []
        
        try:
            # Check if firewall logging is enabled
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "grep -i 'log' /cf/conf/config.xml | wc -l"
            )
            log_count = int(stdout.read().decode().strip())
            
            checks.append(ComplianceCheck(
                check_id='PFS-001',
                name='Firewall Logging',
                description='Verify firewall logging is enabled',
                status='pass' if log_count > 0 else 'fail',
                severity='medium',
                details=f'Found {log_count} logging configurations',
                remediation='Enable firewall logging in System > Advanced > Firewall & NAT'
            ))
            
            # Check for default passwords (simplified check)
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "grep -i 'admin' /cf/conf/config.xml"
            )
            admin_config = stdout.read().decode()
            
            checks.append(ComplianceCheck(
                check_id='PFS-002',
                name='Default Credentials',
                description='Check for default administrative credentials',
                status='warning',  # Would need more sophisticated checking
                severity='high',
                details='Manual verification required',
                remediation='Ensure default passwords have been changed'
            ))
            
            # Check SSH configuration
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "grep -i 'PermitRootLogin' /etc/ssh/sshd_config"
            )
            ssh_config = stdout.read().decode()
            
            root_login_disabled = 'no' in ssh_config.lower()
            checks.append(ComplianceCheck(
                check_id='PFS-003',
                name='SSH Root Login',
                description='Verify SSH root login is disabled',
                status='pass' if root_login_disabled else 'fail',
                severity='medium',
                details=f'SSH configuration: {ssh_config.strip()}',
                remediation='Disable SSH root login in System > Advanced > Admin Access'
            ))
            
        except Exception as e:
            self.logger.error(f"Error checking pfSense compliance: {e}")
        
        return checks
    
    async def _check_network_compliance(self) -> List[ComplianceCheck]:
        """Check network configuration for compliance."""
        checks = []
        
        # Check for open administrative ports
        admin_ports = [22, 23, 3389, 5900]
        open_admin_ports = []
        
        for result in self.scan_results['port_scans']:
            if result.port in admin_ports and result.state == 'open':
                open_admin_ports.append(f"{result.host}:{result.port}")
        
        checks.append(ComplianceCheck(
            check_id='NET-001',
            name='Administrative Port Exposure',
            description='Check for exposed administrative ports',
            status='fail' if open_admin_ports else 'pass',
            severity='high' if open_admin_ports else 'low',
            details=f'Open administrative ports: {open_admin_ports}',
            remediation='Restrict access to administrative ports or use VPN'
        ))
        
        # Check for unencrypted services
        unencrypted_services = []
        for result in self.scan_results['port_scans']:
            if result.service in ['telnet', 'ftp', 'http'] and result.state == 'open':
                unencrypted_services.append(f"{result.host}:{result.port} ({result.service})")
        
        checks.append(ComplianceCheck(
            check_id='NET-002',
            name='Unencrypted Services',
            description='Check for unencrypted network services',
            status='fail' if unencrypted_services else 'pass',
            severity='medium',
            details=f'Unencrypted services: {unencrypted_services}',
            remediation='Replace with encrypted alternatives (SSH, SFTP, HTTPS)'
        ))
        
        return checks
    
    async def _generate_vulnerability_alert(self, vulnerability: VulnerabilityFinding):
        """Generate alert for vulnerability finding."""
        alert_data = {
            'alert_type': 'vulnerability_detected',
            'severity': vulnerability.severity,
            'vulnerability_id': vulnerability.vulnerability_id,
            'host': vulnerability.host,
            'port': vulnerability.port,
            'service': vulnerability.service,
            'description': vulnerability.description,
            'cvss_score': vulnerability.cvss_score,
            'remediation': vulnerability.remediation,
            'discovered_at': vulnerability.discovered_at.isoformat(),
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='security.vulnerabilities',
            payload=alert_data,
            priority=4 if vulnerability.severity == 'critical' else 3
        )
        
        self.logger.warning(f"Vulnerability alert: {vulnerability.vulnerability_id} on {vulnerability.host}:{vulnerability.port}")
    
    async def _generate_compliance_alert(self, check: ComplianceCheck):
        """Generate alert for compliance failure."""
        alert_data = {
            'alert_type': 'compliance_failure',
            'severity': check.severity,
            'check_id': check.check_id,
            'check_name': check.name,
            'description': check.description,
            'status': check.status,
            'details': check.details,
            'remediation': check.remediation,
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='security.compliance',
            payload=alert_data,
            priority=3 if check.severity == 'high' else 2
        )
        
        self.logger.warning(f"Compliance alert: {check.check_id} - {check.name}")
    
    async def _analyze_scan_results(self, port_results: List[PortScanResult], 
                                  vuln_results: List[VulnerabilityFinding],
                                  compliance_results: List[ComplianceCheck]):
        """Analyze scan results using LLM."""
        try:
            # Prepare data for LLM analysis
            analysis_data = {
                'scan_summary': {
                    'ports_scanned': len(port_results),
                    'vulnerabilities_found': len(vuln_results),
                    'compliance_issues': len([c for c in compliance_results if c.status == 'fail']),
                    'scan_timestamp': datetime.now().isoformat()
                },
                'critical_findings': {
                    'critical_vulnerabilities': [
                        {
                            'host': v.host,
                            'vulnerability_id': v.vulnerability_id,
                            'description': v.description,
                            'cvss_score': v.cvss_score
                        }
                        for v in vuln_results if v.severity == 'critical'
                    ],
                    'high_severity_compliance': [
                        {
                            'check_id': c.check_id,
                            'name': c.name,
                            'details': c.details
                        }
                        for c in compliance_results if c.severity == 'high' and c.status == 'fail'
                    ]
                }
            }
            
            # Use LLM for comprehensive analysis
            llm_response = await self.llm_client.analyze_security_event(
                event_data=analysis_data,
                agent_context={'agent_type': 'security_scanner', 'scan_type': 'comprehensive'}
            )
            
            # Send analysis results
            await self.send_message(
                message_type='security_analysis_result',
                topic='system.analysis',
                payload={
                    'agent_id': self.agent_id,
                    'analysis_type': 'comprehensive_security_scan',
                    'scan_summary': analysis_data['scan_summary'],
                    'llm_analysis': {
                        'confidence': llm_response.confidence,
                        'findings': llm_response.response,
                        'recommendations': llm_response.suggested_actions
                    },
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {e}")
    
    async def _initialize_vulnerability_db(self):
        """Initialize vulnerability database."""
        # This would typically load from external sources like CVE databases
        # For now, we'll use a simplified local database
        self.vulnerability_db = {
            'ssh:2.0': [
                {
                    'id': 'CVE-2023-0001',
                    'severity': 'high',
                    'description': 'SSH version 2.0 has known vulnerabilities',
                    'cvss_score': 7.5,
                    'remediation': 'Update SSH to latest version'
                }
            ],
            'http:1.0': [
                {
                    'id': 'HTTP-BASIC-001',
                    'severity': 'medium',
                    'description': 'HTTP 1.0 lacks modern security features',
                    'cvss_score': 5.0,
                    'remediation': 'Upgrade to HTTP/2 with TLS'
                }
            ]
        }
        
        self.last_db_update = datetime.now()
        self.logger.info("Vulnerability database initialized")
    
    async def _update_vulnerability_db(self):
        """Update vulnerability database from external sources."""
        try:
            # This would fetch updates from CVE databases, security feeds, etc.
            # For now, we'll just log the update
            self.last_db_update = datetime.now()
            self.logger.info("Vulnerability database updated")
            
        except Exception as e:
            self.logger.error(f"Error updating vulnerability database: {e}")
    
    async def _cleanup_old_results(self):
        """Clean up old scan results."""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Clean up old vulnerabilities
        self.scan_results['vulnerabilities'] = [
            vuln for vuln in self.scan_results['vulnerabilities']
            if vuln.discovered_at > cutoff_time
        ]
        
        # Clean up old port scans (keep last 1000)
        if len(self.scan_results['port_scans']) > 1000:
            self.scan_results['port_scans'] = self.scan_results['port_scans'][-1000:]
        
        # Clean up old compliance checks (keep last 100)
        if len(self.scan_results['compliance_checks']) > 100:
            self.scan_results['compliance_checks'] = self.scan_results['compliance_checks'][-100:]
    
    async def _update_statistics(self):
        """Update and report statistics."""
        await self.send_message(
            message_type='statistics',
            topic='system.statistics',
            payload={
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'statistics': self.scan_stats.copy(),
                'scan_results_summary': {
                    'port_scans': len(self.scan_results['port_scans']),
                    'vulnerabilities': len(self.scan_results['vulnerabilities']),
                    'compliance_checks': len(self.scan_results['compliance_checks'])
                },
                'last_db_update': self.last_db_update.isoformat() if self.last_db_update else None,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _handle_scan_request(self, message: AgentMessage):
        """Handle scan requests from other agents."""
        request_data = message.payload
        scan_type = request_data.get('scan_type', 'port_scan')
        target = request_data.get('target', 'all')
        
        if scan_type == 'port_scan':
            if target == 'all':
                hosts = await self._discover_active_hosts()
            else:
                hosts = [target]
            
            results = await self._perform_port_scans(hosts)
            
            await self.send_message(
                message_type='scan_result',
                topic=f'agent.{message.sender_id}',
                payload={
                    'request_id': request_data.get('request_id'),
                    'scan_type': scan_type,
                    'results': [
                        {
                            'host': r.host,
                            'port': r.port,
                            'state': r.state,
                            'service': r.service,
                            'version': r.version
                        }
                        for r in results
                    ]
                }
            )
    
    async def _handle_task_assignment(self, message: AgentMessage):
        """Handle task assignments from orchestrator."""
        task_data = message.payload
        task_type = task_data.get('task_type')
        
        if task_type == 'security_scan':
            result = await self._execute_security_scan_task(task_data)
            
            await self.send_message(
                message_type='task_result',
                topic='system.tasks',
                payload={
                    'task_id': task_data.get('task_id'),
                    'agent_id': self.agent_id,
                    'status': 'completed',
                    'result': result
                }
            )
    
    async def _execute_security_scan_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific security scan task."""
        scan_type = task_data.get('payload', {}).get('scan_type', 'comprehensive')
        
        if scan_type == 'comprehensive':
            await self._perform_comprehensive_scan()
        
        return {
            'scan_completed': True,
            'scan_type': scan_type,
            'statistics': self.scan_stats.copy(),
            'vulnerabilities_found': len([v for v in self.scan_results['vulnerabilities'] 
                                        if v.discovered_at > datetime.now() - timedelta(hours=1)]),
            'compliance_issues': len([c for c in self.scan_results['compliance_checks'] 
                                    if c.status == 'fail'])
        }
    
    async def _handle_vulnerability_report(self, message: AgentMessage):
        """Handle vulnerability reports from other agents."""
        vuln_data = message.payload
        
        # Create vulnerability finding from report
        vulnerability = VulnerabilityFinding(
            host=vuln_data.get('host', 'unknown'),
            port=vuln_data.get('port', 0),
            service=vuln_data.get('service', 'unknown'),
            vulnerability_id=vuln_data.get('vulnerability_id', 'EXTERNAL-001'),
            severity=vuln_data.get('severity', 'medium'),
            description=vuln_data.get('description', 'External vulnerability report'),
            cvss_score=vuln_data.get('cvss_score', 0.0),
            remediation=vuln_data.get('remediation', ''),
            discovered_at=datetime.now()
        )
        
        # Add to results
        self.scan_results['vulnerabilities'].append(vulnerability)
        
        # Generate alert if high severity
        if vulnerability.severity in ['high', 'critical']:
            await self._generate_vulnerability_alert(vulnerability)
        
        self.logger.info(f"Received vulnerability report: {vulnerability.vulnerability_id}")

