"""
Message Broker for pfSense Multi-Agent System

This module provides a centralized message broker that handles
communication between agents, message routing, and system coordination.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
import aiohttp
from aiohttp import web
import aioredis
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
import uuid

from ..core.base_agent import AgentMessage


@dataclass
class MessageRoute:
    """Defines a message routing rule."""
    topic_pattern: str
    target_agents: List[str]
    priority: int
    conditions: Dict[str, Any]


@dataclass
class AgentConnection:
    """Information about a connected agent."""
    agent_id: str
    agent_type: str
    connection_time: datetime
    last_heartbeat: datetime
    subscribed_topics: List[str]
    message_count: int
    status: str  # 'active', 'inactive', 'error'


class MessageBroker:
    """
    Centralized message broker for the multi-agent system.
    
    Responsibilities:
    - Message routing and delivery
    - Agent connection management
    - Topic-based publish/subscribe
    - Message persistence and replay
    - Load balancing and failover
    - System-wide coordination
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection management
        self.connected_agents: Dict[str, AgentConnection] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = {}  # topic -> set of agent_ids
        
        # Message routing
        self.routing_rules: List[MessageRoute] = []
        self.message_handlers: Dict[str, Callable] = {}
        
        # RabbitMQ connection
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        
        # Redis for caching and persistence
        self.redis_client = None
        
        # HTTP server for REST API
        self.app = web.Application()
        self.setup_routes()
        
        # Statistics
        self.stats = {
            'messages_routed': 0,
            'agents_connected': 0,
            'topics_active': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        self.logger.info("Message Broker initialized")
    
    async def start(self):
        """Start the message broker."""
        self.logger.info("Starting Message Broker")
        
        try:
            # Initialize connections
            await self._setup_rabbitmq()
            await self._setup_redis()
            
            # Start background tasks
            self._start_background_tasks()
            
            # Start HTTP server
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.config.get('http_port', 8080))
            await site.start()
            
            self.logger.info(f"Message Broker started on port {self.config.get('http_port', 8080)}")
            
        except Exception as e:
            self.logger.error(f"Error starting Message Broker: {e}")
            raise
    
    async def stop(self):
        """Stop the message broker."""
        self.logger.info("Stopping Message Broker")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close connections
        if self.rabbitmq_channel:
            await self.rabbitmq_channel.close()
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def setup_routes(self):
        """Setup HTTP API routes."""
        self.app.router.add_post('/api/messages/send', self.handle_send_message)
        self.app.router.add_get('/api/agents', self.handle_get_agents)
        self.app.router.add_get('/api/topics', self.handle_get_topics)
        self.app.router.add_get('/api/stats', self.handle_get_stats)
        self.app.router.add_post('/api/agents/register', self.handle_agent_registration)
        self.app.router.add_post('/api/agents/{agent_id}/subscribe', self.handle_topic_subscription)
        self.app.router.add_get('/api/messages/{agent_id}', self.handle_get_messages)
        
        # Enable CORS
        self.app.middlewares.append(self._cors_middleware)
    
    async def _cors_middleware(self, request, handler):
        """CORS middleware for HTTP API."""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    async def _setup_rabbitmq(self):
        """Setup RabbitMQ connection."""
        try:
            rabbitmq_url = self.config.get('rabbitmq_url', 'amqp://localhost:5672')
            connection_params = pika.URLParameters(rabbitmq_url)
            
            self.rabbitmq_connection = await AsyncioConnection.create(connection_params)
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            
            # Declare main exchange
            await self.rabbitmq_channel.exchange_declare(
                exchange='pfsense_agents',
                exchange_type='topic',
                durable=True
            )
            
            # Setup message consumption
            await self._setup_message_consumption()
            
            self.logger.info("RabbitMQ connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup RabbitMQ: {e}")
            raise
    
    async def _setup_redis(self):
        """Setup Redis connection."""
        try:
            redis_url = self.config.get('redis_url', 'redis://localhost:6379')
            self.redis_client = await aioredis.from_url(redis_url)
            
            # Test connection
            await self.redis_client.ping()
            
            self.logger.info("Redis connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Redis: {e}")
            # Redis is optional, continue without it
            self.redis_client = None
    
    async def _setup_message_consumption(self):
        """Setup message consumption from RabbitMQ."""
        # Create broker queue for system messages
        broker_queue = 'message_broker'
        await self.rabbitmq_channel.queue_declare(queue=broker_queue, durable=True)
        
        # Bind to system topics
        system_topics = [
            'system.agent_registration',
            'system.heartbeat',
            'system.coordination',
            'system.broadcast'
        ]
        
        for topic in system_topics:
            await self.rabbitmq_channel.queue_bind(
                exchange='pfsense_agents',
                queue=broker_queue,
                routing_key=topic
            )
        
        # Start consuming
        await self.rabbitmq_channel.basic_consume(
            queue=broker_queue,
            on_message_callback=self._on_message_received
        )
    
    async def _on_message_received(self, channel, method, properties, body):
        """Handle incoming messages."""
        try:
            message = AgentMessage.from_json(body.decode())
            await self._process_broker_message(message)
            
            # Acknowledge message
            await channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    async def _process_broker_message(self, message: AgentMessage):
        """Process messages received by the broker."""
        if message.message_type == 'agent_registration':
            await self._handle_agent_registration(message)
        elif message.message_type == 'heartbeat':
            await self._handle_agent_heartbeat(message)
        elif message.message_type == 'coordination_request':
            await self._handle_coordination_request(message)
        elif message.message_type == 'broadcast':
            await self._handle_broadcast_message(message)
        else:
            # Route message to appropriate agents
            await self._route_message(message)
    
    async def _handle_agent_registration(self, message: AgentMessage):
        """Handle agent registration."""
        agent_data = message.payload
        agent_id = agent_data.get('agent_id')
        
        if not agent_id:
            self.logger.warning("Received registration without agent_id")
            return
        
        # Register agent
        self.connected_agents[agent_id] = AgentConnection(
            agent_id=agent_id,
            agent_type=agent_data.get('agent_type', 'unknown'),
            connection_time=datetime.now(),
            last_heartbeat=datetime.now(),
            subscribed_topics=agent_data.get('subscribed_topics', []),
            message_count=0,
            status='active'
        )
        
        # Update subscriptions
        for topic in agent_data.get('subscribed_topics', []):
            if topic not in self.agent_subscriptions:
                self.agent_subscriptions[topic] = set()
            self.agent_subscriptions[topic].add(agent_id)
        
        self.stats['agents_connected'] = len(self.connected_agents)
        self.stats['topics_active'] = len(self.agent_subscriptions)
        
        self.logger.info(f"Agent registered: {agent_id} ({agent_data.get('agent_type')})")
        
        # Store in Redis if available
        if self.redis_client:
            await self.redis_client.hset(
                'agents',
                agent_id,
                json.dumps(asdict(self.connected_agents[agent_id]), default=str)
            )
    
    async def _handle_agent_heartbeat(self, message: AgentMessage):
        """Handle agent heartbeat."""
        agent_id = message.payload.get('agent_id')
        
        if agent_id in self.connected_agents:
            self.connected_agents[agent_id].last_heartbeat = datetime.now()
            self.connected_agents[agent_id].status = message.payload.get('status', 'active')
    
    async def _handle_coordination_request(self, message: AgentMessage):
        """Handle coordination requests between agents."""
        request_type = message.payload.get('request_type')
        
        if request_type == 'find_agents':
            # Find agents matching criteria
            criteria = message.payload.get('criteria', {})
            matching_agents = self._find_matching_agents(criteria)
            
            # Send response
            response_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id='message_broker',
                recipient_id=message.sender_id,
                message_type='coordination_response',
                topic=f'agent.{message.sender_id}',
                payload={
                    'request_id': message.payload.get('request_id'),
                    'matching_agents': matching_agents
                },
                timestamp=datetime.now()
            )
            
            await self._send_message(response_message)
        
        elif request_type == 'broadcast_to_type':
            # Broadcast message to all agents of specific type
            target_type = message.payload.get('target_type')
            broadcast_payload = message.payload.get('broadcast_payload', {})
            
            target_agents = [
                agent_id for agent_id, agent_conn in self.connected_agents.items()
                if agent_conn.agent_type == target_type
            ]
            
            for agent_id in target_agents:
                broadcast_message = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id=message.sender_id,
                    recipient_id=agent_id,
                    message_type='broadcast',
                    topic=f'agent.{agent_id}',
                    payload=broadcast_payload,
                    timestamp=datetime.now()
                )
                
                await self._send_message(broadcast_message)
    
    async def _handle_broadcast_message(self, message: AgentMessage):
        """Handle broadcast messages."""
        target_filter = message.payload.get('target_filter', {})
        broadcast_payload = message.payload.get('payload', {})
        
        # Find target agents based on filter
        target_agents = []
        
        if 'agent_type' in target_filter:
            target_agents = [
                agent_id for agent_id, agent_conn in self.connected_agents.items()
                if agent_conn.agent_type == target_filter['agent_type']
            ]
        else:
            target_agents = list(self.connected_agents.keys())
        
        # Send to all target agents
        for agent_id in target_agents:
            if agent_id != message.sender_id:  # Don't send back to sender
                broadcast_message = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id=message.sender_id,
                    recipient_id=agent_id,
                    message_type='broadcast',
                    topic=f'agent.{agent_id}',
                    payload=broadcast_payload,
                    timestamp=datetime.now()
                )
                
                await self._send_message(broadcast_message)
    
    def _find_matching_agents(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find agents matching given criteria."""
        matching_agents = []
        
        for agent_id, agent_conn in self.connected_agents.items():
            match = True
            
            if 'agent_type' in criteria and agent_conn.agent_type != criteria['agent_type']:
                match = False
            
            if 'status' in criteria and agent_conn.status != criteria['status']:
                match = False
            
            if 'subscribed_to' in criteria:
                topic = criteria['subscribed_to']
                if topic not in agent_conn.subscribed_topics:
                    match = False
            
            if match:
                matching_agents.append({
                    'agent_id': agent_id,
                    'agent_type': agent_conn.agent_type,
                    'status': agent_conn.status,
                    'subscribed_topics': agent_conn.subscribed_topics,
                    'last_heartbeat': agent_conn.last_heartbeat.isoformat()
                })
        
        return matching_agents
    
    async def _route_message(self, message: AgentMessage):
        """Route message to appropriate agents."""
        self.stats['messages_routed'] += 1
        
        # If message has specific recipient, route directly
        if message.recipient_id:
            await self._send_message_to_agent(message, message.recipient_id)
            return
        
        # Route based on topic subscriptions
        topic = message.topic
        if topic in self.agent_subscriptions:
            for agent_id in self.agent_subscriptions[topic]:
                if agent_id != message.sender_id:  # Don't send back to sender
                    await self._send_message_to_agent(message, agent_id)
        
        # Apply custom routing rules
        for rule in self.routing_rules:
            if self._topic_matches_pattern(topic, rule.topic_pattern):
                for agent_id in rule.target_agents:
                    if agent_id in self.connected_agents and agent_id != message.sender_id:
                        await self._send_message_to_agent(message, agent_id)
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches routing pattern."""
        # Simple wildcard matching
        if pattern == '*':
            return True
        
        if pattern.endswith('*'):
            return topic.startswith(pattern[:-1])
        
        return topic == pattern
    
    async def _send_message_to_agent(self, message: AgentMessage, agent_id: str):
        """Send message to specific agent."""
        try:
            # Update message recipient
            message.recipient_id = agent_id
            
            # Send via RabbitMQ
            await self.rabbitmq_channel.basic_publish(
                exchange='pfsense_agents',
                routing_key=f'agent.{agent_id}',
                body=message.to_json().encode(),
                properties=pika.BasicProperties(
                    priority=message.priority,
                    timestamp=int(message.timestamp.timestamp())
                )
            )
            
            # Update agent message count
            if agent_id in self.connected_agents:
                self.connected_agents[agent_id].message_count += 1
            
            # Store in Redis for persistence if available
            if self.redis_client:
                await self.redis_client.lpush(
                    f'messages:{agent_id}',
                    message.to_json()
                )
                # Keep only last 1000 messages
                await self.redis_client.ltrim(f'messages:{agent_id}', 0, 999)
            
        except Exception as e:
            self.logger.error(f"Error sending message to agent {agent_id}: {e}")
            self.stats['errors'] += 1
    
    async def _send_message(self, message: AgentMessage):
        """Send message through the broker."""
        await self._route_message(message)
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Agent health monitoring
        task = asyncio.create_task(self._agent_health_monitor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Statistics reporting
        task = asyncio.create_task(self._statistics_reporter())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Message cleanup
        task = asyncio.create_task(self._message_cleanup())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _agent_health_monitor(self):
        """Monitor agent health and remove stale agents."""
        while True:
            try:
                current_time = datetime.now()
                stale_agents = []
                
                for agent_id, agent_conn in self.connected_agents.items():
                    # Consider agent stale if no heartbeat for 5 minutes
                    if current_time - agent_conn.last_heartbeat > timedelta(minutes=5):
                        stale_agents.append(agent_id)
                        agent_conn.status = 'inactive'
                
                # Remove very stale agents (no heartbeat for 30 minutes)
                for agent_id, agent_conn in list(self.connected_agents.items()):
                    if current_time - agent_conn.last_heartbeat > timedelta(minutes=30):
                        await self._remove_agent(agent_id)
                
                if stale_agents:
                    self.logger.warning(f"Detected {len(stale_agents)} stale agents")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in agent health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _remove_agent(self, agent_id: str):
        """Remove agent from broker."""
        if agent_id in self.connected_agents:
            # Remove from subscriptions
            for topic, subscribers in self.agent_subscriptions.items():
                subscribers.discard(agent_id)
            
            # Remove empty topics
            empty_topics = [topic for topic, subscribers in self.agent_subscriptions.items() if not subscribers]
            for topic in empty_topics:
                del self.agent_subscriptions[topic]
            
            # Remove agent
            del self.connected_agents[agent_id]
            
            # Update statistics
            self.stats['agents_connected'] = len(self.connected_agents)
            self.stats['topics_active'] = len(self.agent_subscriptions)
            
            self.logger.info(f"Removed stale agent: {agent_id}")
            
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.hdel('agents', agent_id)
                await self.redis_client.delete(f'messages:{agent_id}')
    
    async def _statistics_reporter(self):
        """Report broker statistics periodically."""
        while True:
            try:
                # Update runtime statistics
                uptime = datetime.now() - self.stats['start_time']
                
                stats_message = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id='message_broker',
                    recipient_id=None,
                    message_type='broker_statistics',
                    topic='system.statistics',
                    payload={
                        'broker_stats': self.stats.copy(),
                        'uptime_seconds': uptime.total_seconds(),
                        'connected_agents': len(self.connected_agents),
                        'active_topics': len(self.agent_subscriptions),
                        'agent_types': {
                            agent_type: len([a for a in self.connected_agents.values() if a.agent_type == agent_type])
                            for agent_type in set(a.agent_type for a in self.connected_agents.values())
                        }
                    },
                    timestamp=datetime.now()
                )
                
                await self._send_message(stats_message)
                
                await asyncio.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in statistics reporter: {e}")
                await asyncio.sleep(300)
    
    async def _message_cleanup(self):
        """Clean up old messages and data."""
        while True:
            try:
                if self.redis_client:
                    # Clean up old message queues
                    for agent_id in self.connected_agents:
                        # Keep only last 1000 messages per agent
                        await self.redis_client.ltrim(f'messages:{agent_id}', 0, 999)
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                self.logger.error(f"Error in message cleanup: {e}")
                await asyncio.sleep(3600)
    
    # HTTP API Handlers
    
    async def handle_send_message(self, request):
        """Handle HTTP message sending."""
        try:
            data = await request.json()
            
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id=data.get('sender_id', 'http_client'),
                recipient_id=data.get('recipient_id'),
                message_type=data.get('message_type', 'http_message'),
                topic=data.get('topic', 'system.http'),
                payload=data.get('payload', {}),
                timestamp=datetime.now(),
                priority=data.get('priority', 1)
            )
            
            await self._send_message(message)
            
            return web.json_response({
                'status': 'success',
                'message_id': message.id
            })
            
        except Exception as e:
            self.logger.error(f"Error handling send message: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_get_agents(self, request):
        """Handle get agents request."""
        try:
            agents_data = []
            
            for agent_id, agent_conn in self.connected_agents.items():
                agents_data.append({
                    'agent_id': agent_id,
                    'agent_type': agent_conn.agent_type,
                    'status': agent_conn.status,
                    'connection_time': agent_conn.connection_time.isoformat(),
                    'last_heartbeat': agent_conn.last_heartbeat.isoformat(),
                    'subscribed_topics': agent_conn.subscribed_topics,
                    'message_count': agent_conn.message_count
                })
            
            return web.json_response({
                'agents': agents_data,
                'total_count': len(agents_data)
            })
            
        except Exception as e:
            self.logger.error(f"Error handling get agents: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_get_topics(self, request):
        """Handle get topics request."""
        try:
            topics_data = []
            
            for topic, subscribers in self.agent_subscriptions.items():
                topics_data.append({
                    'topic': topic,
                    'subscriber_count': len(subscribers),
                    'subscribers': list(subscribers)
                })
            
            return web.json_response({
                'topics': topics_data,
                'total_count': len(topics_data)
            })
            
        except Exception as e:
            self.logger.error(f"Error handling get topics: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_get_stats(self, request):
        """Handle get statistics request."""
        try:
            uptime = datetime.now() - self.stats['start_time']
            
            return web.json_response({
                'broker_stats': self.stats.copy(),
                'uptime_seconds': uptime.total_seconds(),
                'connected_agents': len(self.connected_agents),
                'active_topics': len(self.agent_subscriptions),
                'agent_types': {
                    agent_type: len([a for a in self.connected_agents.values() if a.agent_type == agent_type])
                    for agent_type in set(a.agent_type for a in self.connected_agents.values())
                }
            })
            
        except Exception as e:
            self.logger.error(f"Error handling get stats: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_agent_registration(self, request):
        """Handle agent registration via HTTP."""
        try:
            data = await request.json()
            
            registration_message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id=data.get('agent_id', 'unknown'),
                recipient_id=None,
                message_type='agent_registration',
                topic='system.agent_registration',
                payload=data,
                timestamp=datetime.now()
            )
            
            await self._handle_agent_registration(registration_message)
            
            return web.json_response({
                'status': 'success',
                'message': 'Agent registered successfully'
            })
            
        except Exception as e:
            self.logger.error(f"Error handling agent registration: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_topic_subscription(self, request):
        """Handle topic subscription via HTTP."""
        try:
            agent_id = request.match_info['agent_id']
            data = await request.json()
            topics = data.get('topics', [])
            
            if agent_id in self.connected_agents:
                # Update agent subscriptions
                self.connected_agents[agent_id].subscribed_topics.extend(topics)
                
                # Update topic subscriptions
                for topic in topics:
                    if topic not in self.agent_subscriptions:
                        self.agent_subscriptions[topic] = set()
                    self.agent_subscriptions[topic].add(agent_id)
                
                return web.json_response({
                    'status': 'success',
                    'message': f'Subscribed to {len(topics)} topics'
                })
            else:
                return web.json_response({
                    'status': 'error',
                    'error': 'Agent not found'
                }, status=404)
                
        except Exception as e:
            self.logger.error(f"Error handling topic subscription: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def handle_get_messages(self, request):
        """Handle get messages for agent."""
        try:
            agent_id = request.match_info['agent_id']
            limit = int(request.query.get('limit', 100))
            
            if not self.redis_client:
                return web.json_response({
                    'status': 'error',
                    'error': 'Message persistence not available'
                }, status=503)
            
            # Get messages from Redis
            messages = await self.redis_client.lrange(f'messages:{agent_id}', 0, limit - 1)
            
            message_data = []
            for msg_json in messages:
                try:
                    message = AgentMessage.from_json(msg_json.decode())
                    message_data.append({
                        'id': message.id,
                        'sender_id': message.sender_id,
                        'message_type': message.message_type,
                        'topic': message.topic,
                        'timestamp': message.timestamp.isoformat(),
                        'payload': message.payload
                    })
                except Exception as e:
                    self.logger.debug(f"Error parsing stored message: {e}")
            
            return web.json_response({
                'messages': message_data,
                'count': len(message_data)
            })
            
        except Exception as e:
            self.logger.error(f"Error handling get messages: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)


# Factory function for creating message broker
def create_message_broker(config: Dict[str, Any]) -> MessageBroker:
    """Create and configure a message broker instance."""
    return MessageBroker(config)

