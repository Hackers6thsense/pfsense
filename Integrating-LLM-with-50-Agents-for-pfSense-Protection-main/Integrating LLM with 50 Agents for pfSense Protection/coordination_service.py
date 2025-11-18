"""
Coordination Service for pfSense Multi-Agent System

This service handles complex coordination tasks between agents,
including task distribution, resource allocation, and collaborative problem-solving.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from ..core.base_agent import AgentMessage
from ..llm_integration.llm_client import get_llm_client


class CoordinationState(Enum):
    """States for coordination sessions."""
    INITIATED = "initiated"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CoordinationSession:
    """Represents a coordination session between agents."""
    session_id: str
    initiator_id: str
    participant_ids: List[str]
    coordination_type: str
    objective: str
    state: CoordinationState
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime]
    context: Dict[str, Any]
    results: Dict[str, Any]
    messages: List[Dict[str, Any]]


@dataclass
class ResourceRequest:
    """Request for shared resources."""
    request_id: str
    requester_id: str
    resource_type: str
    resource_id: str
    priority: int
    duration: Optional[int]  # seconds
    justification: str
    created_at: datetime


@dataclass
class CollaborationGroup:
    """Group of agents collaborating on a task."""
    group_id: str
    leader_id: str
    member_ids: List[str]
    task_type: str
    created_at: datetime
    status: str
    shared_context: Dict[str, Any]


class CoordinationService:
    """
    Service for coordinating complex interactions between agents.
    
    Responsibilities:
    - Managing coordination sessions
    - Resource allocation and conflict resolution
    - Task distribution and load balancing
    - Collaborative problem-solving facilitation
    - Consensus building and decision making
    - Performance monitoring and optimization
    """
    
    def __init__(self, message_broker):
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        
        # Active coordination sessions
        self.active_sessions: Dict[str, CoordinationSession] = {}
        
        # Resource management
        self.resource_requests: Dict[str, ResourceRequest] = {}
        self.resource_allocations: Dict[str, str] = {}  # resource_id -> agent_id
        self.available_resources: Set[str] = set()
        
        # Collaboration groups
        self.collaboration_groups: Dict[str, CollaborationGroup] = {}
        
        # Agent capabilities and load tracking
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.agent_load: Dict[str, int] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
        # LLM client for decision making
        self.llm_client = get_llm_client()
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        self.logger.info("Coordination Service initialized")
    
    async def start(self):
        """Start the coordination service."""
        self.logger.info("Starting Coordination Service")
        
        # Start background tasks
        self._start_background_tasks()
        
        # Register message handlers with broker
        await self._register_message_handlers()
    
    async def stop(self):
        """Stop the coordination service."""
        self.logger.info("Stopping Coordination Service")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Complete or cancel active sessions
        for session in self.active_sessions.values():
            if session.state in [CoordinationState.INITIATED, CoordinationState.PLANNING, CoordinationState.EXECUTING]:
                session.state = CoordinationState.CANCELLED
                await self._notify_session_participants(session, 'session_cancelled')
    
    async def _register_message_handlers(self):
        """Register message handlers with the message broker."""
        # This would integrate with the message broker's routing system
        # For now, we'll assume messages are routed to this service
        pass
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Session monitoring
        task = asyncio.create_task(self._session_monitor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Resource management
        task = asyncio.create_task(self._resource_manager())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Performance monitoring
        task = asyncio.create_task(self._performance_monitor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def initiate_coordination(self, 
                                  initiator_id: str,
                                  coordination_type: str,
                                  objective: str,
                                  required_capabilities: List[str],
                                  context: Dict[str, Any] = None,
                                  deadline: Optional[datetime] = None) -> str:
        """
        Initiate a coordination session.
        
        Args:
            initiator_id: ID of the agent initiating coordination
            coordination_type: Type of coordination (e.g., 'incident_response', 'analysis_collaboration')
            objective: Description of what needs to be accomplished
            required_capabilities: List of capabilities needed from participants
            context: Additional context information
            deadline: Optional deadline for completion
            
        Returns:
            Session ID of the created coordination session
        """
        session_id = str(uuid.uuid4())
        
        # Find suitable participants
        participants = await self._find_suitable_participants(
            required_capabilities, 
            exclude=[initiator_id]
        )
        
        if not participants:
            self.logger.warning(f"No suitable participants found for coordination: {coordination_type}")
            return None
        
        # Create coordination session
        session = CoordinationSession(
            session_id=session_id,
            initiator_id=initiator_id,
            participant_ids=participants,
            coordination_type=coordination_type,
            objective=objective,
            state=CoordinationState.INITIATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deadline=deadline,
            context=context or {},
            results={},
            messages=[]
        )
        
        self.active_sessions[session_id] = session
        
        # Notify participants
        await self._notify_session_participants(session, 'coordination_invitation')
        
        self.logger.info(f"Coordination session {session_id} initiated by {initiator_id}")
        return session_id
    
    async def _find_suitable_participants(self, 
                                        required_capabilities: List[str],
                                        exclude: List[str] = None,
                                        max_participants: int = 5) -> List[str]:
        """Find agents suitable for coordination based on capabilities."""
        exclude = exclude or []
        suitable_agents = []
        
        # Get agent information from message broker
        connected_agents = self.message_broker.connected_agents
        
        for agent_id, agent_conn in connected_agents.items():
            if agent_id in exclude or agent_conn.status != 'active':
                continue
            
            # Check capabilities
            agent_caps = self.agent_capabilities.get(agent_id, [])
            if any(cap in agent_caps for cap in required_capabilities):
                # Consider agent load
                current_load = self.agent_load.get(agent_id, 0)
                suitable_agents.append((agent_id, current_load))
        
        # Sort by load (prefer less loaded agents)
        suitable_agents.sort(key=lambda x: x[1])
        
        # Return up to max_participants
        return [agent_id for agent_id, _ in suitable_agents[:max_participants]]
    
    async def _notify_session_participants(self, session: CoordinationSession, message_type: str):
        """Notify all participants about session events."""
        notification_payload = {
            'session_id': session.session_id,
            'coordination_type': session.coordination_type,
            'objective': session.objective,
            'state': session.state.value,
            'initiator_id': session.initiator_id,
            'participant_ids': session.participant_ids,
            'context': session.context,
            'deadline': session.deadline.isoformat() if session.deadline else None
        }
        
        # Notify all participants
        all_participants = [session.initiator_id] + session.participant_ids
        
        for participant_id in all_participants:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='coordination_service',
                recipient_id=participant_id,
                message_type=message_type,
                topic=f'agent.{participant_id}',
                payload=notification_payload,
                timestamp=datetime.now(),
                priority=2
            )
            
            await self.message_broker._send_message(message)
    
    async def handle_coordination_response(self, message: AgentMessage):
        """Handle responses to coordination invitations."""
        payload = message.payload
        session_id = payload.get('session_id')
        response = payload.get('response')  # 'accept', 'decline', 'busy'
        
        if session_id not in self.active_sessions:
            self.logger.warning(f"Received response for unknown session: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        # Record response
        session.messages.append({
            'timestamp': datetime.now().isoformat(),
            'agent_id': message.sender_id,
            'message_type': 'coordination_response',
            'content': {'response': response}
        })
        
        if response == 'accept':
            self.logger.info(f"Agent {message.sender_id} accepted coordination session {session_id}")
            
            # Check if we have enough participants
            accepted_count = sum(1 for msg in session.messages 
                               if msg.get('content', {}).get('response') == 'accept')
            
            if accepted_count >= len(session.participant_ids) // 2:  # Majority accepted
                await self._start_coordination_planning(session)
        
        elif response == 'decline':
            self.logger.info(f"Agent {message.sender_id} declined coordination session {session_id}")
            
            # Remove from participants
            if message.sender_id in session.participant_ids:
                session.participant_ids.remove(message.sender_id)
            
            # Find replacement if needed
            if len(session.participant_ids) < 2:
                await self._find_replacement_participants(session)
    
    async def _start_coordination_planning(self, session: CoordinationSession):
        """Start the planning phase of coordination."""
        session.state = CoordinationState.PLANNING
        session.updated_at = datetime.now()
        
        # Use LLM to create coordination plan
        planning_prompt = f"""
        Create a coordination plan for the following scenario:
        
        Objective: {session.objective}
        Coordination Type: {session.coordination_type}
        Participants: {len(session.participant_ids)} agents
        Context: {json.dumps(session.context, indent=2)}
        Deadline: {session.deadline.isoformat() if session.deadline else 'None'}
        
        Please provide:
        1. Step-by-step coordination plan
        2. Role assignments for participants
        3. Communication protocol
        4. Success criteria
        5. Contingency plans
        
        Format as JSON with clear structure.
        """
        
        try:
            llm_response = await self.llm_client.general_query(
                prompt=planning_prompt,
                context={'session': asdict(session)},
                agent_type='coordination_service'
            )
            
            # Parse and store the plan
            session.context['coordination_plan'] = llm_response
            
            # Notify participants about the plan
            await self._notify_session_participants(session, 'coordination_plan')
            
            # Move to execution phase
            await self._start_coordination_execution(session)
            
        except Exception as e:
            self.logger.error(f"Error creating coordination plan: {e}")
            session.state = CoordinationState.FAILED
            await self._notify_session_participants(session, 'coordination_failed')
    
    async def _start_coordination_execution(self, session: CoordinationSession):
        """Start the execution phase of coordination."""
        session.state = CoordinationState.EXECUTING
        session.updated_at = datetime.now()
        
        # Assign specific tasks to participants
        await self._assign_coordination_tasks(session)
        
        # Start monitoring execution
        asyncio.create_task(self._monitor_coordination_execution(session))
    
    async def _assign_coordination_tasks(self, session: CoordinationSession):
        """Assign specific tasks to coordination participants."""
        # This would parse the coordination plan and assign tasks
        # For now, we'll send a generic task assignment
        
        for i, participant_id in enumerate(session.participant_ids):
            task_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='coordination_service',
                recipient_id=participant_id,
                message_type='coordination_task',
                topic=f'agent.{participant_id}',
                payload={
                    'session_id': session.session_id,
                    'task_id': f"{session.session_id}_task_{i}",
                    'task_description': f"Coordination task {i+1} for {session.objective}",
                    'role': f"participant_{i+1}",
                    'context': session.context
                },
                timestamp=datetime.now(),
                priority=3
            )
            
            await self.message_broker._send_message(task_message)
    
    async def _monitor_coordination_execution(self, session: CoordinationSession):
        """Monitor the execution of a coordination session."""
        timeout = session.deadline or (datetime.now() + timedelta(hours=1))
        
        while session.state == CoordinationState.EXECUTING and datetime.now() < timeout:
            # Check for completion
            completed_tasks = sum(1 for msg in session.messages 
                                if msg.get('message_type') == 'task_completed')
            
            if completed_tasks >= len(session.participant_ids):
                await self._complete_coordination_session(session)
                break
            
            await asyncio.sleep(30)  # Check every 30 seconds
        
        # Handle timeout
        if session.state == CoordinationState.EXECUTING and datetime.now() >= timeout:
            session.state = CoordinationState.FAILED
            session.results['failure_reason'] = 'timeout'
            await self._notify_session_participants(session, 'coordination_timeout')
    
    async def _complete_coordination_session(self, session: CoordinationSession):
        """Complete a coordination session."""
        session.state = CoordinationState.COMPLETED
        session.updated_at = datetime.now()
        
        # Collect results from participants
        results = {}
        for msg in session.messages:
            if msg.get('message_type') == 'task_result':
                agent_id = msg.get('agent_id')
                results[agent_id] = msg.get('content', {})
        
        session.results = results
        
        # Use LLM to analyze overall results
        analysis_prompt = f"""
        Analyze the results of this coordination session:
        
        Objective: {session.objective}
        Results: {json.dumps(results, indent=2)}
        
        Please provide:
        1. Success assessment
        2. Key achievements
        3. Areas for improvement
        4. Lessons learned
        """
        
        try:
            analysis = await self.llm_client.general_query(
                prompt=analysis_prompt,
                context={'session': asdict(session)},
                agent_type='coordination_service'
            )
            
            session.results['analysis'] = analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing coordination results: {e}")
        
        # Notify participants of completion
        await self._notify_session_participants(session, 'coordination_completed')
        
        self.logger.info(f"Coordination session {session.session_id} completed successfully")
    
    async def handle_coordination_message(self, message: AgentMessage):
        """Handle coordination-related messages."""
        message_type = message.message_type
        
        if message_type == 'coordination_response':
            await self.handle_coordination_response(message)
        elif message_type == 'task_completed':
            await self._handle_task_completion(message)
        elif message_type == 'coordination_update':
            await self._handle_coordination_update(message)
        elif message_type == 'resource_request':
            await self._handle_resource_request(message)
        elif message_type == 'collaboration_request':
            await self._handle_collaboration_request(message)
    
    async def _handle_task_completion(self, message: AgentMessage):
        """Handle task completion messages."""
        payload = message.payload
        session_id = payload.get('session_id')
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Record completion
            session.messages.append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': message.sender_id,
                'message_type': 'task_completed',
                'content': payload
            })
            
            self.logger.info(f"Task completed by {message.sender_id} in session {session_id}")
    
    async def _handle_coordination_update(self, message: AgentMessage):
        """Handle coordination update messages."""
        payload = message.payload
        session_id = payload.get('session_id')
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Record update
            session.messages.append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': message.sender_id,
                'message_type': 'coordination_update',
                'content': payload
            })
            
            # Forward update to other participants
            for participant_id in session.participant_ids:
                if participant_id != message.sender_id:
                    update_message = AgentMessage(
                        id=str(uuid.uuid4()),
                        sender_id='coordination_service',
                        recipient_id=participant_id,
                        message_type='coordination_update',
                        topic=f'agent.{participant_id}',
                        payload=payload,
                        timestamp=datetime.now()
                    )
                    
                    await self.message_broker._send_message(update_message)
    
    async def _handle_resource_request(self, message: AgentMessage):
        """Handle resource allocation requests."""
        payload = message.payload
        
        request = ResourceRequest(
            request_id=str(uuid.uuid4()),
            requester_id=message.sender_id,
            resource_type=payload.get('resource_type'),
            resource_id=payload.get('resource_id'),
            priority=payload.get('priority', 1),
            duration=payload.get('duration'),
            justification=payload.get('justification', ''),
            created_at=datetime.now()
        )
        
        self.resource_requests[request.request_id] = request
        
        # Check if resource is available
        if request.resource_id in self.available_resources:
            # Allocate resource
            self.resource_allocations[request.resource_id] = request.requester_id
            self.available_resources.remove(request.resource_id)
            
            # Notify requester
            response_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='coordination_service',
                recipient_id=request.requester_id,
                message_type='resource_allocated',
                topic=f'agent.{request.requester_id}',
                payload={
                    'request_id': request.request_id,
                    'resource_id': request.resource_id,
                    'allocated': True,
                    'duration': request.duration
                },
                timestamp=datetime.now()
            )
            
            await self.message_broker._send_message(response_message)
            
            # Schedule resource release if duration specified
            if request.duration:
                asyncio.create_task(self._schedule_resource_release(request))
        
        else:
            # Resource not available, add to queue or deny
            response_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='coordination_service',
                recipient_id=request.requester_id,
                message_type='resource_denied',
                topic=f'agent.{request.requester_id}',
                payload={
                    'request_id': request.request_id,
                    'resource_id': request.resource_id,
                    'allocated': False,
                    'reason': 'Resource currently in use'
                },
                timestamp=datetime.now()
            )
            
            await self.message_broker._send_message(response_message)
    
    async def _schedule_resource_release(self, request: ResourceRequest):
        """Schedule automatic resource release."""
        await asyncio.sleep(request.duration)
        
        # Release resource
        if request.resource_id in self.resource_allocations:
            del self.resource_allocations[request.resource_id]
            self.available_resources.add(request.resource_id)
            
            # Notify agent
            release_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='coordination_service',
                recipient_id=request.requester_id,
                message_type='resource_released',
                topic=f'agent.{request.requester_id}',
                payload={
                    'resource_id': request.resource_id,
                    'reason': 'Duration expired'
                },
                timestamp=datetime.now()
            )
            
            await self.message_broker._send_message(release_message)
    
    async def _handle_collaboration_request(self, message: AgentMessage):
        """Handle collaboration group requests."""
        payload = message.payload
        collaboration_type = payload.get('collaboration_type')
        required_skills = payload.get('required_skills', [])
        
        # Find suitable collaborators
        collaborators = await self._find_suitable_participants(
            required_skills,
            exclude=[message.sender_id],
            max_participants=4
        )
        
        if collaborators:
            # Create collaboration group
            group_id = str(uuid.uuid4())
            group = CollaborationGroup(
                group_id=group_id,
                leader_id=message.sender_id,
                member_ids=collaborators,
                task_type=collaboration_type,
                created_at=datetime.now(),
                status='active',
                shared_context=payload.get('context', {})
            )
            
            self.collaboration_groups[group_id] = group
            
            # Notify all members
            for member_id in [message.sender_id] + collaborators:
                collab_message = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id='coordination_service',
                    recipient_id=member_id,
                    message_type='collaboration_formed',
                    topic=f'agent.{member_id}',
                    payload={
                        'group_id': group_id,
                        'leader_id': group.leader_id,
                        'members': group.member_ids,
                        'task_type': collaboration_type,
                        'context': group.shared_context
                    },
                    timestamp=datetime.now()
                )
                
                await self.message_broker._send_message(collab_message)
    
    async def _session_monitor(self):
        """Monitor active coordination sessions."""
        while True:
            try:
                current_time = datetime.now()
                
                # Check for expired sessions
                expired_sessions = []
                for session_id, session in self.active_sessions.items():
                    if session.deadline and current_time > session.deadline:
                        if session.state in [CoordinationState.INITIATED, CoordinationState.PLANNING, CoordinationState.EXECUTING]:
                            expired_sessions.append(session_id)
                
                # Handle expired sessions
                for session_id in expired_sessions:
                    session = self.active_sessions[session_id]
                    session.state = CoordinationState.FAILED
                    session.results['failure_reason'] = 'deadline_exceeded'
                    await self._notify_session_participants(session, 'coordination_expired')
                
                # Clean up completed sessions older than 1 hour
                completed_cutoff = current_time - timedelta(hours=1)
                completed_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if session.state in [CoordinationState.COMPLETED, CoordinationState.FAILED, CoordinationState.CANCELLED]
                    and session.updated_at < completed_cutoff
                ]
                
                for session_id in completed_sessions:
                    del self.active_sessions[session_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in session monitor: {e}")
                await asyncio.sleep(60)
    
    async def _resource_manager(self):
        """Manage resource allocation and cleanup."""
        while True:
            try:
                # Clean up old resource requests
                cutoff_time = datetime.now() - timedelta(hours=1)
                old_requests = [
                    req_id for req_id, req in self.resource_requests.items()
                    if req.created_at < cutoff_time
                ]
                
                for req_id in old_requests:
                    del self.resource_requests[req_id]
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in resource manager: {e}")
                await asyncio.sleep(300)
    
    async def _performance_monitor(self):
        """Monitor agent performance in coordination tasks."""
        while True:
            try:
                # Analyze completed sessions for performance metrics
                for session in self.active_sessions.values():
                    if session.state == CoordinationState.COMPLETED:
                        await self._analyze_session_performance(session)
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(600)
    
    async def _analyze_session_performance(self, session: CoordinationSession):
        """Analyze performance metrics for a completed session."""
        # Calculate metrics like response time, task completion rate, etc.
        session_duration = (session.updated_at - session.created_at).total_seconds()
        
        for participant_id in [session.initiator_id] + session.participant_ids:
            if participant_id not in self.agent_performance:
                self.agent_performance[participant_id] = {
                    'sessions_participated': 0,
                    'avg_response_time': 0,
                    'success_rate': 0,
                    'collaboration_score': 0
                }
            
            perf = self.agent_performance[participant_id]
            perf['sessions_participated'] += 1
            
            # Update other metrics based on session data
            # This would be more sophisticated in practice
    
    async def _find_replacement_participants(self, session: CoordinationSession):
        """Find replacement participants for a coordination session."""
        # This would implement logic to find new participants
        # when original participants decline or become unavailable
        pass
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """Get current coordination service status."""
        return {
            'active_sessions': len(self.active_sessions),
            'resource_requests': len(self.resource_requests),
            'collaboration_groups': len(self.collaboration_groups),
            'available_resources': len(self.available_resources),
            'agent_performance': self.agent_performance,
            'session_states': {
                state.value: len([s for s in self.active_sessions.values() if s.state == state])
                for state in CoordinationState
            }
        }

