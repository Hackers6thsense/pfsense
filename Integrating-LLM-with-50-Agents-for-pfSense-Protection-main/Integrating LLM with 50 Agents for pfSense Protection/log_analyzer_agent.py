"""
Log Analyzer Agent for pfSense Multi-Agent System

This agent specializes in analyzing pfSense logs for security events,
anomalies, and patterns that may indicate threats or system issues.
"""

import asyncio
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Pattern
from dataclasses import dataclass
import paramiko
from collections import defaultdict, deque

from ..core.base_agent import BaseAgent, AgentConfig, AgentMessage
from ..llm_integration.llm_client import get_llm_client


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: datetime
    source: str
    level: str
    message: str
    raw_line: str
    parsed_fields: Dict[str, Any]


@dataclass
class LogPattern:
    """Represents a log pattern for detection."""
    name: str
    pattern: Pattern[str]
    severity: str
    description: str
    action: str


class LogAnalyzerAgent(BaseAgent):
    """
    Specialized agent for analyzing pfSense logs.
    
    Capabilities:
    - Real-time log monitoring and parsing
    - Pattern-based anomaly detection
    - LLM-powered log analysis
    - Security event identification
    - Alert generation for suspicious activities
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Log monitoring configuration
        self.log_types = config.subscribed_topics or ['firewall', 'system', 'dhcp', 'vpn']
        self.batch_size = 100
        self.analysis_interval = 60  # seconds
        
        # SSH connection for log access
        self.ssh_client = None
        self.ssh_connected = False
        
        # Log processing
        self.log_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.processed_lines: Dict[str, int] = defaultdict(int)
        
        # Pattern matching
        self.security_patterns = self._initialize_security_patterns()
        self.anomaly_patterns = self._initialize_anomaly_patterns()
        
        # Statistics
        self.analysis_stats = {
            'logs_processed': 0,
            'patterns_matched': 0,
            'alerts_generated': 0,
            'anomalies_detected': 0
        }
        
        # LLM client
        self.llm_client = get_llm_client()
        
        self.logger.info(f"Log Analyzer Agent initialized for types: {self.log_types}")
    
    async def initialize(self):
        """Initialize log analyzer specific resources."""
        # Subscribe to log-related topics
        self.config.subscribed_topics = [
            'pfsense.logs.request',
            'system.tasks',
            'security.events'
        ]
        
        # Setup SSH connection to pfSense
        await self._setup_ssh_connection()
        
        # Start log monitoring tasks
        for log_type in self.log_types:
            asyncio.create_task(self._monitor_log_type(log_type))
        
        # Start analysis task
        asyncio.create_task(self._analysis_loop())
        
        self.logger.info("Log Analyzer initialization completed")
    
    async def run(self):
        """Main execution loop."""
        self.logger.info("Log


 Analyzer Agent started")
        
        while self.is_running:
            try:
                # Perform periodic maintenance
                await self._cleanup_old_logs()
                await self._update_statistics()
                
                # Check SSH connection health
                if not self.ssh_connected:
                    await self._setup_ssh_connection()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.ssh_client:
            self.ssh_client.close()
        self.logger.info("Log Analyzer cleanup completed")
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        try:
            if message.message_type == 'log_analysis_request':
                await self._handle_log_analysis_request(message)
            elif message.message_type == 'task_assignment':
                await self._handle_task_assignment(message)
            else:
                self.logger.debug(f"Unhandled message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _setup_ssh_connection(self):
        """Setup SSH connection to pfSense."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to pfSense
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
    
    async def _monitor_log_type(self, log_type: str):
        """Monitor a specific log type."""
        log_paths = {
            'firewall': '/var/log/filter.log',
            'system': '/var/log/system.log',
            'dhcp': '/var/log/dhcpd.log',
            'vpn': '/var/log/openvpn.log'
        }
        
        log_path = log_paths.get(log_type)
        if not log_path:
            self.logger.warning(f"Unknown log type: {log_type}")
            return
        
        while self.is_running:
            try:
                if self.ssh_connected:
                    # Read new log entries
                    new_entries = await self._read_new_log_entries(log_path, log_type)
                    
                    # Process entries
                    for entry in new_entries:
                        await self._process_log_entry(entry, log_type)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring {log_type} logs: {e}")
                await asyncio.sleep(10)
    
    async def _read_new_log_entries(self, log_path: str, log_type: str) -> List[LogEntry]:
        """Read new log entries from pfSense."""
        if not self.ssh_connected:
            return []
        
        try:
            # Get current line count
            stdin, stdout, stderr = self.ssh_client.exec_command(f"wc -l {log_path}")
            current_lines = int(stdout.read().decode().split()[0])
            
            # Calculate new lines to read
            last_processed = self.processed_lines[log_type]
            if current_lines <= last_processed:
                return []
            
            new_lines = current_lines - last_processed
            
            # Read new lines
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"tail -n {new_lines} {log_path}"
            )
            
            raw_lines = stdout.read().decode().strip().split('\n')
            self.processed_lines[log_type] = current_lines
            
            # Parse log entries
            entries = []
            for line in raw_lines:
                if line.strip():
                    entry = self._parse_log_entry(line, log_type)
                    if entry:
                        entries.append(entry)
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Error reading log entries from {log_path}: {e}")
            return []
    
    def _parse_log_entry(self, raw_line: str, log_type: str) -> Optional[LogEntry]:
        """Parse a raw log line into a LogEntry object."""
        try:
            # Basic parsing - this would be more sophisticated in practice
            parts = raw_line.split(' ', 5)
            if len(parts) < 6:
                return None
            
            # Extract timestamp (assuming standard syslog format)
            timestamp_str = ' '.join(parts[:3])
            try:
                timestamp = datetime.strptime(
                    f"{datetime.now().year} {timestamp_str}",
                    "%Y %b %d %H:%M:%S"
                )
            except ValueError:
                timestamp = datetime.now()
            
            # Extract other fields
            source = parts[3] if len(parts) > 3 else 'unknown'
            level = 'info'  # Default level
            message = parts[5] if len(parts) > 5 else raw_line
            
            # Parse specific fields based on log type
            parsed_fields = self._parse_log_fields(message, log_type)
            
            return LogEntry(
                timestamp=timestamp,
                source=source,
                level=level,
                message=message,
                raw_line=raw_line,
                parsed_fields=parsed_fields
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing log line: {e}")
            return None
    
    def _parse_log_fields(self, message: str, log_type: str) -> Dict[str, Any]:
        """Parse specific fields from log message based on type."""
        fields = {}
        
        if log_type == 'firewall':
            # Parse firewall log fields
            patterns = {
                'action': r'(block|pass|reject)',
                'interface': r'on (\w+)',
                'protocol': r'proto (\w+)',
                'src_ip': r'(\d+\.\d+\.\d+\.\d+):\d+',
                'dst_ip': r'> (\d+\.\d+\.\d+\.\d+):\d+',
                'src_port': r'(\d+\.\d+\.\d+\.\d+):(\d+)',
                'dst_port': r'> \d+\.\d+\.\d+\.\d+:(\d+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, message)
                if match:
                    if field in ['src_port', 'dst_port']:
                        fields[field] = match.group(2) if field == 'src_port' else match.group(1)
                    else:
                        fields[field] = match.group(1)
        
        elif log_type == 'dhcp':
            # Parse DHCP log fields
            patterns = {
                'action': r'(DHCPACK|DHCPREQUEST|DHCPDISCOVER|DHCPNAK)',
                'ip_address': r'(\d+\.\d+\.\d+\.\d+)',
                'mac_address': r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})',
                'hostname': r'to (\w+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, message)
                if match:
                    fields[field] = match.group(1)
        
        return fields
    
    async def _process_log_entry(self, entry: LogEntry, log_type: str):
        """Process a single log entry."""
        # Add to buffer
        self.log_buffer[log_type].append(entry)
        self.analysis_stats['logs_processed'] += 1
        
        # Check against security patterns
        await self._check_security_patterns(entry, log_type)
        
        # Check for anomalies
        await self._check_anomaly_patterns(entry, log_type)
    
    async def _check_security_patterns(self, entry: LogEntry, log_type: str):
        """Check log entry against security patterns."""
        for pattern in self.security_patterns:
            if pattern.pattern.search(entry.message):
                self.analysis_stats['patterns_matched'] += 1
                
                # Generate security alert
                await self._generate_security_alert(entry, pattern, log_type)
    
    async def _check_anomaly_patterns(self, entry: LogEntry, log_type: str):
        """Check for anomalous patterns in log entries."""
        # Simple anomaly detection based on frequency
        if log_type == 'firewall' and 'src_ip' in entry.parsed_fields:
            src_ip = entry.parsed_fields['src_ip']
            
            # Count recent entries from this IP
            recent_entries = [
                e for e in self.log_buffer[log_type]
                if e.timestamp > datetime.now() - timedelta(minutes=5)
                and e.parsed_fields.get('src_ip') == src_ip
            ]
            
            # If more than 50 entries in 5 minutes, it's potentially suspicious
            if len(recent_entries) > 50:
                await self._generate_anomaly_alert(entry, 'high_frequency_access', log_type)
    
    async def _generate_security_alert(self, entry: LogEntry, pattern: LogPattern, log_type: str):
        """Generate a security alert."""
        alert_data = {
            'alert_type': 'security_pattern_match',
            'severity': pattern.severity,
            'pattern_name': pattern.name,
            'description': pattern.description,
            'log_type': log_type,
            'log_entry': {
                'timestamp': entry.timestamp.isoformat(),
                'source': entry.source,
                'message': entry.message,
                'parsed_fields': entry.parsed_fields
            },
            'recommended_action': pattern.action,
            'agent_id': self.agent_id
        }
        
        # Send alert
        await self.send_message(
            message_type='alert',
            topic='security.alerts',
            payload=alert_data,
            priority=3 if pattern.severity == 'high' else 2
        )
        
        self.analysis_stats['alerts_generated'] += 1
        self.logger.warning(f"Security alert: {pattern.name} - {entry.message[:100]}")
    
    async def _generate_anomaly_alert(self, entry: LogEntry, anomaly_type: str, log_type: str):
        """Generate an anomaly alert."""
        alert_data = {
            'alert_type': 'anomaly_detected',
            'severity': 'medium',
            'anomaly_type': anomaly_type,
            'description': f'Anomalous pattern detected in {log_type} logs',
            'log_type': log_type,
            'log_entry': {
                'timestamp': entry.timestamp.isoformat(),
                'source': entry.source,
                'message': entry.message,
                'parsed_fields': entry.parsed_fields
            },
            'agent_id': self.agent_id
        }
        
        # Send alert
        await self.send_message(
            message_type='alert',
            topic='security.anomalies',
            payload=alert_data,
            priority=2
        )
        
        self.analysis_stats['anomalies_detected'] += 1
        self.logger.info(f"Anomaly detected: {anomaly_type} - {entry.message[:100]}")
    
    async def _analysis_loop(self):
        """Periodic analysis of accumulated log data."""
        while self.is_running:
            try:
                # Perform batch analysis every minute
                await self._perform_batch_analysis()
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(self.analysis_interval)
    
    async def _perform_batch_analysis(self):
        """Perform batch analysis of recent log entries."""
        for log_type, entries in self.log_buffer.items():
            if not entries:
                continue
            
            # Get recent entries for analysis
            recent_entries = [
                e for e in entries
                if e.timestamp > datetime.now() - timedelta(minutes=self.analysis_interval / 60)
            ]
            
            if len(recent_entries) < 10:  # Need minimum entries for meaningful analysis
                continue
            
            # Prepare data for LLM analysis
            log_data = [
                {
                    'timestamp': entry.timestamp.isoformat(),
                    'message': entry.message,
                    'parsed_fields': entry.parsed_fields
                }
                for entry in recent_entries[-50:]  # Last 50 entries
            ]
            
            # Use LLM for advanced analysis
            try:
                llm_response = await self.llm_client.analyze_logs(log_data, log_type)
                
                # Process LLM recommendations
                if llm_response.suggested_actions:
                    await self._process_llm_recommendations(llm_response, log_type)
                    
            except Exception as e:
                self.logger.error(f"Error in LLM analysis: {e}")
    
    async def _process_llm_recommendations(self, llm_response, log_type: str):
        """Process recommendations from LLM analysis."""
        if llm_response.confidence > 0.7:  # High confidence threshold
            # Send findings to orchestrator
            await self.send_message(
                message_type='analysis_result',
                topic='system.analysis',
                payload={
                    'agent_id': self.agent_id,
                    'log_type': log_type,
                    'analysis_type': 'llm_batch_analysis',
                    'confidence': llm_response.confidence,
                    'findings': llm_response.response,
                    'recommendations': llm_response.suggested_actions,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    def _initialize_security_patterns(self) -> List[LogPattern]:
        """Initialize security detection patterns."""
        patterns = [
            LogPattern(
                name="brute_force_ssh",
                pattern=re.compile(r"Failed password for .* from \d+\.\d+\.\d+\.\d+"),
                severity="high",
                description="Potential SSH brute force attack detected",
                action="block_source_ip"
            ),
            LogPattern(
                name="port_scan",
                pattern=re.compile(r"block.*proto tcp.*flags.*"),
                severity="medium",
                description="Potential port scan activity detected",
                action="monitor_source_ip"
            ),
            LogPattern(
                name="dns_tunneling",
                pattern=re.compile(r"DNS.*query.*[a-zA-Z0-9]{20,}"),
                severity="high",
                description="Potential DNS tunneling detected",
                action="investigate_dns_traffic"
            ),
            LogPattern(
                name="unusual_outbound",
                pattern=re.compile(r"pass out.*proto tcp.*port (22|23|3389|5900)"),
                severity="medium",
                description="Unusual outbound connection on administrative port",
                action="verify_legitimate_access"
            ),
            LogPattern(
                name="dhcp_exhaustion",
                pattern=re.compile(r"DHCPNAK.*no free leases"),
                severity="high",
                description="DHCP pool exhaustion detected",
                action="investigate_dhcp_requests"
            )
        ]
        
        return patterns
    
    def _initialize_anomaly_patterns(self) -> List[LogPattern]:
        """Initialize anomaly detection patterns."""
        patterns = [
            LogPattern(
                name="high_connection_rate",
                pattern=re.compile(r".*"),  # Catch-all for frequency analysis
                severity="medium",
                description="High connection rate from single source",
                action="rate_limit_source"
            ),
            LogPattern(
                name="unusual_time_activity",
                pattern=re.compile(r".*"),  # Time-based analysis
                severity="low",
                description="Activity during unusual hours",
                action="log_for_review"
            )
        ]
        
        return patterns
    
    async def _handle_log_analysis_request(self, message: AgentMessage):
        """Handle specific log analysis requests."""
        request_data = message.payload
        log_type = request_data.get('log_type', 'firewall')
        analysis_type = request_data.get('analysis_type', 'pattern_match')
        
        if analysis_type == 'pattern_match':
            # Perform pattern matching on recent logs
            recent_entries = list(self.log_buffer[log_type])[-100:]  # Last 100 entries
            matches = []
            
            for entry in recent_entries:
                for pattern in self.security_patterns:
                    if pattern.pattern.search(entry.message):
                        matches.append({
                            'pattern': pattern.name,
                            'entry': entry.message,
                            'timestamp': entry.timestamp.isoformat()
                        })
            
            # Send results
            await self.send_message(
                message_type='analysis_result',
                topic=f'agent.{message.sender_id}',
                payload={
                    'request_id': request_data.get('request_id'),
                    'matches': matches,
                    'total_entries_analyzed': len(recent_entries)
                }
            )
    
    async def _handle_task_assignment(self, message: AgentMessage):
        """Handle task assignments from orchestrator."""
        task_data = message.payload
        task_type = task_data.get('task_type')
        
        if task_type == 'log_analysis':
            # Perform specific log analysis task
            result = await self._execute_log_analysis_task(task_data)
            
            # Send result back
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
    
    async def _execute_log_analysis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific log analysis task."""
        # This would implement specific analysis based on task requirements
        return {
            'analysis_completed': True,
            'entries_processed': self.analysis_stats['logs_processed'],
            'patterns_matched': self.analysis_stats['patterns_matched'],
            'alerts_generated': self.analysis_stats['alerts_generated']
        }
    
    async def _cleanup_old_logs(self):
        """Clean up old log entries from buffer."""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for log_type in self.log_buffer:
            # Remove entries older than 1 hour
            while (self.log_buffer[log_type] and 
                   self.log_buffer[log_type][0].timestamp < cutoff_time):
                self.log_buffer[log_type].popleft()
    
    async def _update_statistics(self):
        """Update and report statistics."""
        # Send statistics to orchestrator
        await self.send_message(
            message_type='statistics',
            topic='system.statistics',
            payload={
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'statistics': self.analysis_stats.copy(),
                'buffer_sizes': {
                    log_type: len(entries) 
                    for log_type, entries in self.log_buffer.items()
                },
                'timestamp': datetime.now().isoformat()
            }
        )

