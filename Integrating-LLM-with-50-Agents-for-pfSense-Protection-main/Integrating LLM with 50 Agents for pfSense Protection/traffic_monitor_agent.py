"""
Traffic Monitor Agent for pfSense Multi-Agent System

This agent specializes in monitoring network traffic patterns,
detecting anomalies, and analyzing bandwidth usage across interfaces.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import paramiko
from collections import defaultdict, deque
import re

from ..core.base_agent import BaseAgent, AgentConfig, AgentMessage
from ..llm_integration.llm_client import get_llm_client


@dataclass
class TrafficSample:
    """Represents a traffic measurement sample."""
    timestamp: datetime
    interface: str
    bytes_in: int
    bytes_out: int
    packets_in: int
    packets_out: int
    connections: int
    bandwidth_utilization: float


@dataclass
class ConnectionInfo:
    """Information about a network connection."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    state: str
    bytes_transferred: int


class TrafficMonitorAgent(BaseAgent):
    """
    Specialized agent for monitoring network traffic.
    
    Capabilities:
    - Real-time traffic monitoring across interfaces
    - Bandwidth utilization tracking
    - Connection state monitoring
    - Anomaly detection in traffic patterns
    - DDoS detection and mitigation recommendations
    - Performance bottleneck identification
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Monitoring configuration
        self.interfaces = ['wan', 'lan', 'opt1']  # Default interfaces
        self.sampling_interval = 30  # seconds
        self.bandwidth_threshold = 0.9  # 90% utilization threshold
        self.connection_threshold = 1000  # Max connections per interface
        
        # SSH connection for data collection
        self.ssh_client = None
        self.ssh_connected = False
        
        # Traffic data storage
        self.traffic_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1440))  # 24 hours at 1-minute intervals
        self.baseline_data: Dict[str, Dict] = {}
        self.current_connections: Dict[str, List[ConnectionInfo]] = defaultdict(list)
        
        # Anomaly detection
        self.anomaly_thresholds = {
            'bandwidth_spike': 3.0,  # 3x normal bandwidth
            'connection_spike': 2.0,  # 2x normal connections
            'unusual_ports': [22, 23, 135, 139, 445, 1433, 3389, 5900],
            'suspicious_protocols': ['icmp_flood', 'syn_flood']
        }
        
        # Statistics
        self.monitoring_stats = {
            'samples_collected': 0,
            'anomalies_detected': 0,
            'alerts_generated': 0,
            'interfaces_monitored': len(self.interfaces)
        }
        
        # LLM client
        self.llm_client = get_llm_client()
        
        self.logger.info(f"Traffic Monitor Agent initialized for interfaces: {self.interfaces}")
    
    async def initialize(self):
        """Initialize traffic monitor specific resources."""
        # Subscribe to traffic-related topics
        self.config.subscribed_topics = [
            'network.traffic.request',
            'system.tasks',
            'network.alerts'
        ]
        
        # Setup SSH connection
        await self._setup_ssh_connection()
        
        # Initialize baseline data
        await self._initialize_baseline_data()
        
        # Start monitoring tasks
        for interface in self.interfaces:
            asyncio.create_task(self._monitor_interface(interface))
        
        # Start analysis tasks
        asyncio.create_task(self._traffic_analysis_loop())
        asyncio.create_task(self._connection_monitoring_loop())
        
        self.logger.info("Traffic Monitor initialization completed")
    
    async def run(self):
        """Main execution loop."""
        self.logger.info("Traffic Monitor Agent started")
        
        while self.is_running:
            try:
                # Perform periodic maintenance
                await self._update_baseline_data()
                await self._cleanup_old_data()
                await self._update_statistics()
                
                # Check SSH connection health
                if not self.ssh_connected:
                    await self._setup_ssh_connection()
                
                await asyncio.sleep(60)  # Main loop every minute
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.ssh_client:
            self.ssh_client.close()
        self.logger.info("Traffic Monitor cleanup completed")
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        try:
            if message.message_type == 'traffic_analysis_request':
                await self._handle_traffic_analysis_request(message)
            elif message.message_type == 'task_assignment':
                await self._handle_task_assignment(message)
            elif message.message_type == 'bandwidth_alert':
                await self._handle_bandwidth_alert(message)
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
    
    async def _monitor_interface(self, interface: str):
        """Monitor traffic on a specific interface."""
        while self.is_running:
            try:
                if self.ssh_connected:
                    # Collect traffic sample
                    sample = await self._collect_traffic_sample(interface)
                    if sample:
                        # Store sample
                        self.traffic_history[interface].append(sample)
                        self.monitoring_stats['samples_collected'] += 1
                        
                        # Check for anomalies
                        await self._check_traffic_anomalies(sample, interface)
                
                await asyncio.sleep(self.sampling_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring interface {interface}: {e}")
                await asyncio.sleep(self.sampling_interval)
    
    async def _collect_traffic_sample(self, interface: str) -> Optional[TrafficSample]:
        """Collect traffic statistics for an interface."""
        if not self.ssh_connected:
            return None
        
        try:
            # Get interface statistics using netstat
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"netstat -I {interface} -b"
            )
            
            output = stdout.read().decode().strip()
            lines = output.split('\n')
            
            if len(lines) < 2:
                return None
            
            # Parse the statistics (simplified parsing)
            stats_line = lines[1].split()
            if len(stats_line) < 10:
                return None
            
            bytes_in = int(stats_line[6])
            packets_in = int(stats_line[4])
            bytes_out = int(stats_line[9])
            packets_out = int(stats_line[7])
            
            # Get connection count
            connections = await self._get_connection_count(interface)
            
            # Calculate bandwidth utilization (simplified)
            bandwidth_utilization = await self._calculate_bandwidth_utilization(
                interface, bytes_in + bytes_out
            )
            
            return TrafficSample(
                timestamp=datetime.now(),
                interface=interface,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                packets_in=packets_in,
                packets_out=packets_out,
                connections=connections,
                bandwidth_utilization=bandwidth_utilization
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting traffic sample for {interface}: {e}")
            return None
    
    async def _get_connection_count(self, interface: str) -> int:
        """Get the number of active connections on an interface."""
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "netstat -an | grep ESTABLISHED | wc -l"
            )
            
            count = int(stdout.read().decode().strip())
            return count
            
        except Exception as e:
            self.logger.debug(f"Error getting connection count: {e}")
            return 0
    
    async def _calculate_bandwidth_utilization(self, interface: str, total_bytes: int) -> float:
        """Calculate bandwidth utilization percentage."""
        try:
            # Get interface speed (simplified - would need more sophisticated detection)
            interface_speeds = {
                'wan': 1000000000,  # 1 Gbps
                'lan': 1000000000,  # 1 Gbps
                'opt1': 100000000   # 100 Mbps
            }
            
            max_speed = interface_speeds.get(interface, 1000000000)
            
            # Get previous sample for rate calculation
            if interface in self.traffic_history and self.traffic_history[interface]:
                prev_sample = self.traffic_history[interface][-1]
                time_diff = (datetime.now() - prev_sample.timestamp).total_seconds()
                
                if time_diff > 0:
                    byte_rate = (total_bytes - (prev_sample.bytes_in + prev_sample.bytes_out)) / time_diff
                    bit_rate = byte_rate * 8
                    utilization = (bit_rate / max_speed) * 100
                    return min(utilization, 100.0)
            
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Error calculating bandwidth utilization: {e}")
            return 0.0
    
    async def _check_traffic_anomalies(self, sample: TrafficSample, interface: str):
        """Check for traffic anomalies."""
        # Check bandwidth utilization
        if sample.bandwidth_utilization > self.bandwidth_threshold * 100:
            await self._generate_bandwidth_alert(sample, interface)
        
        # Check connection count
        if sample.connections > self.connection_threshold:
            await self._generate_connection_alert(sample, interface)
        
        # Check for traffic spikes
        await self._check_traffic_spikes(sample, interface)
    
    async def _check_traffic_spikes(self, sample: TrafficSample, interface: str):
        """Check for unusual traffic spikes."""
        if interface not in self.baseline_data:
            return
        
        baseline = self.baseline_data[interface]
        
        # Check for bandwidth spikes
        normal_bandwidth = baseline.get('avg_bandwidth_utilization', 10.0)
        if sample.bandwidth_utilization > normal_bandwidth * self.anomaly_thresholds['bandwidth_spike']:
            await self._generate_anomaly_alert(
                sample, interface, 'bandwidth_spike',
                f"Bandwidth utilization {sample.bandwidth_utilization:.1f}% is {sample.bandwidth_utilization/normal_bandwidth:.1f}x normal"
            )
        
        # Check for connection spikes
        normal_connections = baseline.get('avg_connections', 100)
        if sample.connections > normal_connections * self.anomaly_thresholds['connection_spike']:
            await self._generate_anomaly_alert(
                sample, interface, 'connection_spike',
                f"Connection count {sample.connections} is {sample.connections/normal_connections:.1f}x normal"
            )
    
    async def _generate_bandwidth_alert(self, sample: TrafficSample, interface: str):
        """Generate bandwidth utilization alert."""
        alert_data = {
            'alert_type': 'bandwidth_threshold_exceeded',
            'severity': 'high' if sample.bandwidth_utilization > 95 else 'medium',
            'interface': interface,
            'current_utilization': sample.bandwidth_utilization,
            'threshold': self.bandwidth_threshold * 100,
            'timestamp': sample.timestamp.isoformat(),
            'bytes_in': sample.bytes_in,
            'bytes_out': sample.bytes_out,
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='network.bandwidth_alerts',
            payload=alert_data,
            priority=3 if alert_data['severity'] == 'high' else 2
        )
        
        self.monitoring_stats['alerts_generated'] += 1
        self.logger.warning(f"Bandwidth alert on {interface}: {sample.bandwidth_utilization:.1f}%")
    
    async def _generate_connection_alert(self, sample: TrafficSample, interface: str):
        """Generate connection count alert."""
        alert_data = {
            'alert_type': 'connection_threshold_exceeded',
            'severity': 'medium',
            'interface': interface,
            'current_connections': sample.connections,
            'threshold': self.connection_threshold,
            'timestamp': sample.timestamp.isoformat(),
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='network.connection_alerts',
            payload=alert_data,
            priority=2
        )
        
        self.monitoring_stats['alerts_generated'] += 1
        self.logger.warning(f"Connection alert on {interface}: {sample.connections} connections")
    
    async def _generate_anomaly_alert(self, sample: TrafficSample, interface: str, 
                                    anomaly_type: str, description: str):
        """Generate traffic anomaly alert."""
        alert_data = {
            'alert_type': 'traffic_anomaly',
            'severity': 'medium',
            'anomaly_type': anomaly_type,
            'interface': interface,
            'description': description,
            'timestamp': sample.timestamp.isoformat(),
            'sample_data': {
                'bandwidth_utilization': sample.bandwidth_utilization,
                'connections': sample.connections,
                'bytes_in': sample.bytes_in,
                'bytes_out': sample.bytes_out
            },
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='network.anomalies',
            payload=alert_data,
            priority=2
        )
        
        self.monitoring_stats['anomalies_detected'] += 1
        self.logger.info(f"Traffic anomaly on {interface}: {description}")
    
    async def _traffic_analysis_loop(self):
        """Periodic traffic analysis using LLM."""
        while self.is_running:
            try:
                # Perform analysis every 5 minutes
                await self._perform_traffic_analysis()
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in traffic analysis loop: {e}")
                await asyncio.sleep(300)
    
    async def _perform_traffic_analysis(self):
        """Perform comprehensive traffic analysis."""
        for interface in self.interfaces:
            if interface not in self.traffic_history or not self.traffic_history[interface]:
                continue
            
            # Get recent samples
            recent_samples = list(self.traffic_history[interface])[-60:]  # Last hour
            if len(recent_samples) < 10:
                continue
            
            # Prepare data for LLM analysis
            traffic_data = {
                'interface': interface,
                'sample_count': len(recent_samples),
                'time_range': {
                    'start': recent_samples[0].timestamp.isoformat(),
                    'end': recent_samples[-1].timestamp.isoformat()
                },
                'statistics': {
                    'avg_bandwidth_utilization': sum(s.bandwidth_utilization for s in recent_samples) / len(recent_samples),
                    'max_bandwidth_utilization': max(s.bandwidth_utilization for s in recent_samples),
                    'avg_connections': sum(s.connections for s in recent_samples) / len(recent_samples),
                    'max_connections': max(s.connections for s in recent_samples),
                    'total_bytes_in': sum(s.bytes_in for s in recent_samples),
                    'total_bytes_out': sum(s.bytes_out for s in recent_samples)
                },
                'baseline': self.baseline_data.get(interface, {})
            }
            
            # Use LLM for analysis
            try:
                llm_response = await self.llm_client.analyze_traffic_pattern(
                    traffic_data=traffic_data,
                    baseline_data=self.baseline_data.get(interface)
                )
                
                # Process LLM recommendations
                if llm_response.confidence > 0.7:
                    await self._process_traffic_analysis_results(llm_response, interface)
                    
            except Exception as e:
                self.logger.error(f"Error in LLM traffic analysis: {e}")
    
    async def _process_traffic_analysis_results(self, llm_response, interface: str):
        """Process traffic analysis results from LLM."""
        # Send analysis results to orchestrator
        await self.send_message(
            message_type='analysis_result',
            topic='system.analysis',
            payload={
                'agent_id': self.agent_id,
                'analysis_type': 'traffic_pattern_analysis',
                'interface': interface,
                'confidence': llm_response.confidence,
                'findings': llm_response.response,
                'recommendations': llm_response.suggested_actions,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Generate alerts for high-priority findings
        if llm_response.confidence > 0.8 and llm_response.suggested_actions:
            await self.send_message(
                message_type='alert',
                topic='network.analysis_alerts',
                payload={
                    'alert_type': 'llm_traffic_analysis',
                    'severity': 'medium',
                    'interface': interface,
                    'description': f"LLM analysis identified potential issues: {llm_response.response[:200]}",
                    'recommendations': llm_response.suggested_actions,
                    'confidence': llm_response.confidence,
                    'agent_id': self.agent_id
                },
                priority=2
            )
    
    async def _connection_monitoring_loop(self):
        """Monitor active connections for suspicious activity."""
        while self.is_running:
            try:
                await self._monitor_connections()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in connection monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_connections(self):
        """Monitor active network connections."""
        if not self.ssh_connected:
            return
        
        try:
            # Get active connections
            stdin, stdout, stderr = self.ssh_client.exec_command(
                "netstat -an | grep ESTABLISHED"
            )
            
            output = stdout.read().decode().strip()
            connections = []
            
            for line in output.split('\n'):
                if line.strip():
                    conn_info = self._parse_connection_line(line)
                    if conn_info:
                        connections.append(conn_info)
            
            # Analyze connections for suspicious patterns
            await self._analyze_connections(connections)
            
        except Exception as e:
            self.logger.error(f"Error monitoring connections: {e}")
    
    def _parse_connection_line(self, line: str) -> Optional[ConnectionInfo]:
        """Parse a netstat connection line."""
        try:
            parts = line.split()
            if len(parts) < 6:
                return None
            
            protocol = parts[0]
            local_addr = parts[3]
            remote_addr = parts[4]
            state = parts[5] if len(parts) > 5 else 'UNKNOWN'
            
            # Parse addresses
            local_ip, local_port = self._parse_address(local_addr)
            remote_ip, remote_port = self._parse_address(remote_addr)
            
            return ConnectionInfo(
                src_ip=local_ip,
                dst_ip=remote_ip,
                src_port=local_port,
                dst_port=remote_port,
                protocol=protocol,
                state=state,
                bytes_transferred=0  # Would need additional parsing
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing connection line: {e}")
            return None
    
    def _parse_address(self, addr_str: str) -> Tuple[str, int]:
        """Parse IP:port address string."""
        try:
            if ':' in addr_str:
                ip, port = addr_str.rsplit(':', 1)
                return ip, int(port)
            else:
                return addr_str, 0
        except:
            return addr_str, 0
    
    async def _analyze_connections(self, connections: List[ConnectionInfo]):
        """Analyze connections for suspicious patterns."""
        # Group connections by source IP
        connections_by_ip = defaultdict(list)
        for conn in connections:
            connections_by_ip[conn.src_ip].append(conn)
        
        # Check for suspicious patterns
        for src_ip, conns in connections_by_ip.items():
            # Check for too many connections from single IP
            if len(conns) > 50:
                await self._generate_connection_anomaly_alert(
                    src_ip, 'high_connection_count', 
                    f"IP {src_ip} has {len(conns)} active connections"
                )
            
            # Check for connections to unusual ports
            unusual_ports = [conn for conn in conns if conn.dst_port in self.anomaly_thresholds['unusual_ports']]
            if unusual_ports:
                await self._generate_connection_anomaly_alert(
                    src_ip, 'unusual_port_access',
                    f"IP {src_ip} connecting to unusual ports: {[c.dst_port for c in unusual_ports]}"
                )
    
    async def _generate_connection_anomaly_alert(self, src_ip: str, anomaly_type: str, description: str):
        """Generate connection anomaly alert."""
        alert_data = {
            'alert_type': 'connection_anomaly',
            'severity': 'medium',
            'anomaly_type': anomaly_type,
            'source_ip': src_ip,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id
        }
        
        await self.send_message(
            message_type='alert',
            topic='network.connection_anomalies',
            payload=alert_data,
            priority=2
        )
        
        self.logger.info(f"Connection anomaly: {description}")
    
    async def _initialize_baseline_data(self):
        """Initialize baseline traffic data."""
        # This would typically load historical data
        # For now, we'll use default values
        for interface in self.interfaces:
            self.baseline_data[interface] = {
                'avg_bandwidth_utilization': 10.0,
                'avg_connections': 100,
                'avg_bytes_per_second': 1000000,
                'peak_hours': [9, 10, 11, 14, 15, 16],  # Business hours
                'baseline_established': datetime.now().isoformat()
            }
    
    async def _update_baseline_data(self):
        """Update baseline data based on recent traffic patterns."""
        for interface in self.interfaces:
            if interface not in self.traffic_history or len(self.traffic_history[interface]) < 100:
                continue
            
            # Calculate new baseline from recent data
            recent_samples = list(self.traffic_history[interface])[-1440:]  # Last 24 hours
            
            if recent_samples:
                self.baseline_data[interface].update({
                    'avg_bandwidth_utilization': sum(s.bandwidth_utilization for s in recent_samples) / len(recent_samples),
                    'avg_connections': sum(s.connections for s in recent_samples) / len(recent_samples),
                    'avg_bytes_per_second': sum(s.bytes_in + s.bytes_out for s in recent_samples) / len(recent_samples),
                    'last_updated': datetime.now().isoformat()
                })
    
    async def _cleanup_old_data(self):
        """Clean up old traffic data."""
        # Data is automatically cleaned up by deque maxlen
        # Additional cleanup could be implemented here
        pass
    
    async def _update_statistics(self):
        """Update and report statistics."""
        await self.send_message(
            message_type='statistics',
            topic='system.statistics',
            payload={
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'statistics': self.monitoring_stats.copy(),
                'interfaces_status': {
                    interface: {
                        'samples_count': len(self.traffic_history[interface]),
                        'last_sample': self.traffic_history[interface][-1].timestamp.isoformat() 
                                     if self.traffic_history[interface] else None
                    }
                    for interface in self.interfaces
                },
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _handle_traffic_analysis_request(self, message: AgentMessage):
        """Handle traffic analysis requests."""
        request_data = message.payload
        interface = request_data.get('interface', 'all')
        analysis_type = request_data.get('analysis_type', 'current_status')
        
        if analysis_type == 'current_status':
            # Return current traffic status
            status = {}
            
            if interface == 'all':
                for iface in self.interfaces:
                    if iface in self.traffic_history and self.traffic_history[iface]:
                        latest_sample = self.traffic_history[iface][-1]
                        status[iface] = {
                            'bandwidth_utilization': latest_sample.bandwidth_utilization,
                            'connections': latest_sample.connections,
                            'bytes_in': latest_sample.bytes_in,
                            'bytes_out': latest_sample.bytes_out,
                            'timestamp': latest_sample.timestamp.isoformat()
                        }
            else:
                if interface in self.traffic_history and self.traffic_history[interface]:
                    latest_sample = self.traffic_history[interface][-1]
                    status[interface] = {
                        'bandwidth_utilization': latest_sample.bandwidth_utilization,
                        'connections': latest_sample.connections,
                        'bytes_in': latest_sample.bytes_in,
                        'bytes_out': latest_sample.bytes_out,
                        'timestamp': latest_sample.timestamp.isoformat()
                    }
            
            # Send response
            await self.send_message(
                message_type='analysis_result',
                topic=f'agent.{message.sender_id}',
                payload={
                    'request_id': request_data.get('request_id'),
                    'traffic_status': status,
                    'baseline_data': self.baseline_data
                }
            )
    
    async def _handle_task_assignment(self, message: AgentMessage):
        """Handle task assignments from orchestrator."""
        task_data = message.payload
        task_type = task_data.get('task_type')
        
        if task_type == 'traffic_analysis':
            result = await self._execute_traffic_analysis_task(task_data)
            
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
    
    async def _execute_traffic_analysis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific traffic analysis task."""
        return {
            'analysis_completed': True,
            'interfaces_monitored': len(self.interfaces),
            'samples_collected': self.monitoring_stats['samples_collected'],
            'anomalies_detected': self.monitoring_stats['anomalies_detected'],
            'current_status': {
                interface: {
                    'sample_count': len(self.traffic_history[interface]),
                    'latest_utilization': self.traffic_history[interface][-1].bandwidth_utilization 
                                        if self.traffic_history[interface] else 0
                }
                for interface in self.interfaces
            }
        }
    
    async def _handle_bandwidth_alert(self, message: AgentMessage):
        """Handle bandwidth alerts from other agents."""
        alert_data = message.payload
        interface = alert_data.get('interface')
        
        if interface in self.interfaces:
            # Perform detailed analysis of the interface
            if interface in self.traffic_history and self.traffic_history[interface]:
                recent_samples = list(self.traffic_history[interface])[-10:]
                
                # Use LLM to analyze the bandwidth issue
                analysis_prompt = f"""
                Analyze this bandwidth alert and recent traffic data:
                
                Alert: {json.dumps(alert_data, indent=2)}
                
                Recent Traffic Samples: {json.dumps([
                    {
                        'timestamp': s.timestamp.isoformat(),
                        'bandwidth_utilization': s.bandwidth_utilization,
                        'connections': s.connections,
                        'bytes_in': s.bytes_in,
                        'bytes_out': s.bytes_out
                    } for s in recent_samples
                ], indent=2)}
                
                Please provide:
                1. Root cause analysis
                2. Immediate recommendations
                3. Long-term optimization suggestions
                """
                
                llm_response = await self.llm_client.general_query(
                    prompt=analysis_prompt,
                    context={'alert': alert_data, 'interface': interface},
                    agent_type='traffic_monitor'
                )
                
                # Send analysis back
                await self.send_message(
                    message_type='bandwidth_analysis_result',
                    topic=f'agent.{message.sender_id}',
                    payload={
                        'interface': interface,
                        'analysis': llm_response,
                        'agent_id': self.agent_id
                    }
                )

