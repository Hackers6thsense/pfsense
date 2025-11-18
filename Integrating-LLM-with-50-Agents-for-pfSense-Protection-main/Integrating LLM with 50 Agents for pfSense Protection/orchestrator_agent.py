"""
Orchestrator Agent for pfSense Multi-Agent System

This agent serves as the central coordinator for the multi-agent system.
It manages agent lifecycle, task assignment, and global system coordination.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .base_agent import BaseAgent, AgentConfig, AgentMessage
from ..llm_integration.llm_client import get_llm_client


@dataclass
class AgentRegistration:
    """Information about a registered agent."""
    agent_id: str
    agent_type: str
    name: str
    capabilities: List[str]
    status: str  # 'active', 'inactive', 'error'
    last_heartbeat: datetime
    stats: Dict[str, Any]
    config: Dict[str, Any]


@dataclass
class SystemTask:
    """Represents a task that can be assigned to agents."""
    task_id: str
    task_type: str
    description: str
    priority: int
    assigned_agents: List[str]
    status: str  # 'pending', 'assigned', 'in_progress', 'completed', 'failed'
    created_at: datetime
    deadline: Optional[datetime]
    payload: Dict[str, Any]
    results: Dict[str, Any]


class OrchestratorAgent(BaseAgent):
    """
    Central orchestrator agent that coordinates the multi-agent system.
    
    Responsibilities:
    - Agent registration and lifecycle management
    - Task assignment and coordination
    - System health monitoring
    - Global decision making with LLM integration
    - Alert aggregation and escalation
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Agent registry
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # Task management
        self.active_tasks: Dict[str, SystemTask] = {}
        self.task_queue: List[SystemTask] = []
        
        # System state
        self.system_health = {
            'overall_status': 'healthy',
            'active_agents': 0,
            'failed_agents': 0,
            'active_alerts': 0,
            'last_update': datetime.now()
        }
        
        # LLM client for decision making
        self.llm_client = get_llm_client()
        
        # Configuration
        self.heartbeat_timeout = timedelta(seconds=config.heartbeat_interval * 3)
        self.task_assignment_interval = 10  # seconds
        
        self.logger.info("Orchestrator Agent initialized")
    
    async def initialize(self):
        """Initialize orchestrator-specific resources."""
        # Subscribe to all system topics for monitoring
        self.config.subscribed_topics = [
            'system.heartbeat',
            'system.agent_registration',
            'system.alerts',
            'system.tasks',
            'security.events',
            'network.anomalies',
            'pfsense.logs'
        ]
        
        # Start orchestrator-specific tasks
        asyncio.create_task(self._health_monitor_loop())
        asyncio.create_task(self._task_assignment_loop())
        asyncio.create_task(self._system_analysis_loop())
        
        self.logger.info("Orchestrator initialization completed")
    
    async def run(self):
        """Main orchestrator execution loop."""
        self.logger.info("Orchestrator agent started")
        
        while self.is_running:
            try:
                # Perform periodic system maintenance
                await self._cleanup_stale_agents()
                await self._update_system_health()
                await self._process_pending_tasks()
                
                # Wait before next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in orchestrator main loop: {e}")
                await asyncio.sleep(5)
    
    async def cleanup(self):
        """Cleanup orchestrator resources."""
        self.logger.info("Orchestrator cleanup completed")
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        try:
            if message.message_type == 'heartbeat':
                await self._handle_heartbeat(message)
            elif message.message_type == 'agent_registration':
                await self._handle_agent_registration(message)
            elif message.message_type == 'alert':
                await self._handle_alert(message)
            elif message.message_type == 'task_result':
                await self._handle_task_result(message)
            elif message.message_type == 'agent_request':
                await self._handle_agent_request(message)
            else:
                self.logger.debug(f"Unhandled message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _handle_heartbeat(self, message: AgentMessage):
        """Handle agent heartbeat messages."""
        agent_id = message.payload.get('agent_id')
        if not agent_id:
            return
        
        if agent_id in self.registered_agents:
            # Update existing agent
            agent_reg = self.registered_agents[agent_id]
            agent_reg.last_heartbeat = datetime.now()
            agent_reg.status = message.payload.get('status', 'active')
            agent_reg.stats = message.payload.get('stats', {})
        else:
            # Register new agent from heartbeat
            self.registered_agents[agent_id] = AgentRegistration(
                agent_id=agent_id,
                agent_type=message.payload.get('agent_type', 'unknown'),
                name=message.payload.get('name', agent_id),
                capabilities=message.payload.get('capabilities', []),
                status=message.payload.get('status', 'active'),
                last_heartbeat=datetime.now(),
                stats=message.payload.get('stats', {}),
                config={}
            )
            
            self.logger.info(f"Auto-registered agent {agent_id} from heartbeat")
    
    async def _handle_agent_registration(self, message: AgentMessage):
        """Handle explicit agent registration."""
        payload = message.payload
        agent_id = payload.get('agent_id')
        
        if not agent_id:
            self.logger.warning("Received registration without agent_id")
            return
        
        # Register or update agent
        self.registered_agents[agent_id] = AgentRegistration(
            agent_id=agent_id,
            agent_type=payload.get('agent_type', 'unknown'),
            name=payload.get('name', agent_id),
            capabilities=payload.get('capabilities', []),
            status='active',
            last_heartbeat=datetime.now(),
            stats=payload.get('stats', {}),
            config=payload.get('config', {})
        )
        
        # Update capability mapping
        self.agent_capabilities[agent_id] = payload.get('capabilities', [])
        
        self.logger.info(f"Registered agent {agent_id} ({payload.get('agent_type')})")
        
        # Send registration confirmation
        await self.send_message(
            message_type='registration_confirmed',
            topic=f'agent.{agent_id}',
            payload={
                'agent_id': agent_id,
                'orchestrator_id': self.agent_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _handle_alert(self, message: AgentMessage):
        """Handle alert messages from agents."""
        alert_data = message.payload
        severity = alert_data.get('severity', 'medium')
        
        self.logger.warning(f"Alert from {message.sender_id}: {alert_data.get('description', 'No description')}")
        
        # Use LLM to analyze the alert and determine response
        if severity in ['high', 'critical']:
            llm_response = await self.llm_client.recommend_incident_response(
                incident_data=alert_data,
                severity=severity
            )
            
            # Create response task based on LLM recommendations
            if llm_response.suggested_actions:
                await self._create_response_task(alert_data, llm_response.suggested_actions)
        
        # Forward critical alerts to administrators
        if severity == 'critical':
            await self._escalate_alert(alert_data)
    
    async def _handle_task_result(self, message: AgentMessage):
        """Handle task completion results."""
        task_id = message.payload.get('task_id')
        if task_id not in self.active_tasks:
            return
        
        task = self.active_tasks[task_id]
        task.results[message.sender_id] = message.payload.get('result', {})
        task.status = message.payload.get('status', 'completed')
        
        self.logger.info(f"Task {task_id} result received from {message.sender_id}")
        
        # Check if all assigned agents have reported
        if len(task.results) >= len(task.assigned_agents):
            await self._finalize_task(task)
    
    async def _handle_agent_request(self, message: AgentMessage):
        """Handle requests from agents for assistance or resources."""
        request_type = message.payload.get('request_type')
        
        if request_type == 'llm_analysis':
            # Agent requesting LLM analysis
            prompt = message.payload.get('prompt', '')
            context = message.payload.get('context', {})
            
            llm_response = await self.llm_client.general_query(
                prompt=prompt,
                context=context,
                agent_type=message.payload.get('agent_type', 'unknown')
            )
            
            # Send response back to requesting agent
            await self.send_message(
                message_type='llm_response',
                topic=f'agent.{message.sender_id}',
                payload={
                    'request_id': message.payload.get('request_id'),
                    'response': llm_response
                }
            )
        
        elif request_type == 'agent_collaboration':
            # Agent requesting collaboration with other agents
            await self._facilitate_agent_collaboration(message)
    
    async def _health_monitor_loop(self):
        """Monitor system and agent health."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check for stale agents
                stale_agents = []
                for agent_id, agent_reg in self.registered_agents.items():
                    if current_time - agent_reg.last_heartbeat > self.heartbeat_timeout:
                        stale_agents.append(agent_id)
                        agent_reg.status = 'inactive'
                
                if stale_agents:
                    self.logger.warning(f"Detected {len(stale_agents)} stale agents: {stale_agents}")
                
                # Update system health metrics
                await self._update_system_health()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(30)
    
    async def _task_assignment_loop(self):
        """Assign tasks to appropriate agents."""
        while self.is_running:
            try:
                if self.task_queue:
                    task = self.task_queue.pop(0)
                    await self._assign_task(task)
                
                await asyncio.sleep(self.task_assignment_interval)
                
            except Exception as e:
                self.logger.error(f"Error in task assignment: {e}")
                await asyncio.sleep(self.task_assignment_interval)
    
    async def _system_analysis_loop(self):
        """Perform periodic system analysis using LLM."""
        while self.is_running:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Use LLM to analyze overall system health
                analysis_prompt = f"""
                Analyze the current system state and provide recommendations:
                
                System Metrics:
                {json.dumps(system_metrics, indent=2)}
                
                Please assess:
                1. Overall system health
                2. Potential issues or concerns
                3. Optimization opportunities
                4. Recommended actions
                """
                
                llm_response = await self.llm_client.general_query(
                    prompt=analysis_prompt,
                    context={'system_metrics': system_metrics},
                    agent_type='orchestrator'
                )
                
                self.logger.info(f"System analysis: {llm_response}")
                
                # Wait 5 minutes before next analysis
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in system analysis: {e}")
                await asyncio.sleep(300)
    
    async def _assign_task(self, task: SystemTask):
        """Assign a task to appropriate agents."""
        # Find agents with required capabilities
        suitable_agents = []
        for agent_id, capabilities in self.agent_capabilities.items():
            if agent_id in self.registered_agents and self.registered_agents[agent_id].status == 'active':
                # Check if agent has required capabilities for this task
                if self._agent_suitable_for_task(capabilities, task):
                    suitable_agents.append(agent_id)
        
        if not suitable_agents:
            self.logger.warning(f"No suitable agents found for task {task.task_id}")
            task.status = 'failed'
            return
        
        # Select agents based on task requirements and load balancing
        selected_agents = self._select_agents_for_task(suitable_agents, task)
        task.assigned_agents = selected_agents
        task.status = 'assigned'
        
        # Send task to selected agents
        for agent_id in selected_agents:
            await self.send_message(
                message_type='task_assignment',
                topic=f'agent.{agent_id}',
                payload={
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'description': task.description,
                    'priority': task.priority,
                    'deadline': task.deadline.isoformat() if task.deadline else None,
                    'payload': task.payload
                }
            )
        
        self.active_tasks[task.task_id] = task
        self.logger.info(f"Assigned task {task.task_id} to agents: {selected_agents}")
    
    def _agent_suitable_for_task(self, capabilities: List[str], task: SystemTask) -> bool:
        """Check if an agent is suitable for a task based on capabilities."""
        # This is a simplified implementation - in practice, you'd have more sophisticated matching
        task_requirements = {
            'log_analysis': ['log_parsing', 'pattern_recognition'],
            'traffic_monitoring': ['network_analysis', 'traffic_inspection'],
            'security_scan': ['vulnerability_scanning', 'security_analysis'],
            'alert_processing': ['alert_handling', 'notification'],
            'remediation': ['firewall_management', 'network_control']
        }
        
        required_caps = task_requirements.get(task.task_type, [])
        return any(cap in capabilities for cap in required_caps) if required_caps else True
    
    def _select_agents_for_task(self, suitable_agents: List[str], task: SystemTask) -> List[str]:
        """Select the best agents for a task based on load balancing and capabilities."""
        # Simple selection based on current load (number of active tasks)
        agent_loads = {}
        for agent_id in suitable_agents:
            load = sum(1 for t in self.active_tasks.values() if agent_id in t.assigned_agents)
            agent_loads[agent_id] = load
        
        # Sort by load and select based on task requirements
        sorted_agents = sorted(suitable_agents, key=lambda x: agent_loads[x])
        
        # For now, select up to 3 agents for redundancy
        max_agents = min(3, len(sorted_agents))
        return sorted_agents[:max_agents]
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        active_agents = sum(1 for a in self.registered_agents.values() if a.status == 'active')
        inactive_agents = sum(1 for a in self.registered_agents.values() if a.status == 'inactive')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(self.registered_agents),
            'active_agents': active_agents,
            'inactive_agents': inactive_agents,
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'system_health': self.system_health,
            'agent_types': {
                agent_type: sum(1 for a in self.registered_agents.values() if a.agent_type == agent_type)
                for agent_type in set(a.agent_type for a in self.registered_agents.values())
            }
        }
    
    async def _update_system_health(self):
        """Update overall system health status."""
        active_agents = sum(1 for a in self.registered_agents.values() if a.status == 'active')
        failed_agents = sum(1 for a in self.registered_agents.values() if a.status in ['inactive', 'error'])
        
        # Determine overall status
        if active_agents == 0:
            overall_status = 'critical'
        elif failed_agents > active_agents * 0.3:  # More than 30% failed
            overall_status = 'degraded'
        elif failed_agents > 0:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        self.system_health.update({
            'overall_status': overall_status,
            'active_agents': active_agents,
            'failed_agents': failed_agents,
            'active_alerts': len([t for t in self.active_tasks.values() if t.task_type == 'alert_response']),
            'last_update': datetime.now()
        })
    
    async def _cleanup_stale_agents(self):
        """Remove agents that haven't sent heartbeats."""
        current_time = datetime.now()
        stale_agents = []
        
        for agent_id, agent_reg in list(self.registered_agents.items()):
            if current_time - agent_reg.last_heartbeat > self.heartbeat_timeout * 2:
                stale_agents.append(agent_id)
        
        for agent_id in stale_agents:
            del self.registered_agents[agent_id]
            if agent_id in self.agent_capabilities:
                del self.agent_capabilities[agent_id]
            self.logger.info(f"Removed stale agent {agent_id}")
    
    async def _create_response_task(self, alert_data: Dict[str, Any], actions: List[str]):
        """Create a response task based on alert and recommended actions."""
        task_id = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = SystemTask(
            task_id=task_id,
            task_type='alert_response',
            description=f"Response to alert: {alert_data.get('description', 'Unknown alert')}",
            priority=4 if alert_data.get('severity') == 'critical' else 3,
            assigned_agents=[],
            status='pending',
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(minutes=15),
            payload={
                'alert_data': alert_data,
                'recommended_actions': actions
            },
            results={}
        )
        
        self.task_queue.append(task)
        self.logger.info(f"Created response task {task_id}")
    
    async def _escalate_alert(self, alert_data: Dict[str, Any]):
        """Escalate critical alerts to administrators."""
        # This would integrate with notification systems
        self.logger.critical(f"CRITICAL ALERT ESCALATION: {alert_data}")
        
        # Send to alert processing agents
        await self.send_message(
            message_type='critical_alert',
            topic='alerts.critical',
            payload=alert_data,
            priority=4
        )
    
    async def _facilitate_agent_collaboration(self, message: AgentMessage):
        """Facilitate collaboration between agents."""
        collaboration_type = message.payload.get('collaboration_type')
        target_capabilities = message.payload.get('required_capabilities', [])
        
        # Find agents with required capabilities
        collaborating_agents = []
        for agent_id, capabilities in self.agent_capabilities.items():
            if any(cap in capabilities for cap in target_capabilities):
                collaborating_agents.append(agent_id)
        
        # Create collaboration group
        collaboration_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Notify all participating agents
        for agent_id in collaborating_agents:
            await self.send_message(
                message_type='collaboration_invite',
                topic=f'agent.{agent_id}',
                payload={
                    'collaboration_id': collaboration_id,
                    'initiator': message.sender_id,
                    'type': collaboration_type,
                    'participants': collaborating_agents,
                    'context': message.payload.get('context', {})
                }
            )
    
    async def _finalize_task(self, task: SystemTask):
        """Finalize a completed task."""
        self.logger.info(f"Task {task.task_id} completed with {len(task.results)} results")
        
        # Analyze results with LLM if needed
        if task.task_type in ['security_analysis', 'incident_response']:
            analysis_prompt = f"""
            Analyze the task results and provide a summary:
            
            Task: {task.description}
            Results: {json.dumps(task.results, indent=2)}
            
            Please provide:
            1. Summary of findings
            2. Overall assessment
            3. Any follow-up actions needed
            """
            
            llm_summary = await self.llm_client.general_query(
                prompt=analysis_prompt,
                context={'task': asdict(task)},
                agent_type='orchestrator'
            )
            
            task.results['llm_summary'] = llm_summary
        
        # Remove from active tasks
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'orchestrator_id': self.agent_id,
            'system_health': self.system_health,
            'registered_agents': {
                agent_id: asdict(agent_reg) 
                for agent_id, agent_reg in self.registered_agents.items()
            },
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'agent_capabilities': self.agent_capabilities,
            'timestamp': datetime.now().isoformat()
        }

