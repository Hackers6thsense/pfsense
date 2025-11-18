"""
Base Agent Class for pfSense Multi-Agent System

This module defines the base agent class that all specialized agents will inherit from.
It provides common functionality for communication, logging, configuration, and lifecycle management.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import aiohttp
import pika
from pika.adapters.asyncio_connection import AsyncioConnection


@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication."""
    id: str
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast messages
    message_type: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    agent_type: str
    name: str
    description: str
    enabled: bool = True
    log_level: str = "INFO"
    heartbeat_interval: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    rabbitmq_url: str = "amqp://localhost:5672"
    llm_api_url: str = "http://localhost:8000/api/llm"
    pfsense_host: str = "localhost"
    pfsense_ssh_port: int = 22
    pfsense_username: str = "admin"
    subscribed_topics: List[str] = None
    
    def __post_init__(self):
        if self.subscribed_topics is None:
            self.subscribed_topics = []


class BaseAgent(ABC):
    """
    Base class for all agents in the pfSense multi-agent system.
    
    Provides common functionality for:
    - Message communication via RabbitMQ
    - LLM integration
    - Logging and monitoring
    - Configuration management
    - Lifecycle management (start, stop, health checks)
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.name = config.name
        self.is_running = False
        self.is_healthy = True
        self.last_heartbeat = None
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Communication components
        self.connection = None
        self.channel = None
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue = asyncio.Queue()
        
        # Threading for async operations
        self.loop = None
        self.thread = None
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'start_time': None,
            'last_activity': None
        }
        
        self.logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent."""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_id} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start(self):
        """Start the agent and its background tasks."""
        if self.is_running:
            self.logger.warning("Agent is already running")
            return
        
        self.logger.info(f"Starting agent {self.agent_id}")
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        try:
            # Initialize communication
            await self._setup_communication()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._message_processor())
            
            # Call agent-specific initialization
            await self.initialize()
            
            # Start main agent loop
            await self.run()
            
        except Exception as e:
            self.logger.error(f"Error starting agent: {e}")
            self.is_healthy = False
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        self.logger.info(f"Stopping agent {self.agent_id}")
        self.is_running = False
        
        try:
            # Call agent-specific cleanup
            await self.cleanup()
            
            # Close communication
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
                
        except Exception as e:
            self.logger.error(f"Error stopping agent: {e}")
    
    async def _setup_communication(self):
        """Setup RabbitMQ connection and channels."""
        try:
            # Connect to RabbitMQ
            connection_params = pika.URLParameters(self.config.rabbitmq_url)
            self.connection = await AsyncioConnection.create(connection_params)
            self.channel = await self.connection.channel()
            
            # Declare exchanges and queues
            await self.channel.exchange_declare(
                exchange='pfsense_agents',
                exchange_type='topic',
                durable=True
            )
            
            # Create agent-specific queue
            queue_name = f"agent.{self.agent_id}"
            await self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Bind to subscribed topics
            for topic in self.config.subscribed_topics:
                await self.channel.queue_bind(
                    exchange='pfsense_agents',
                    queue=queue_name,
                    routing_key=topic
                )
            
            # Start consuming messages
            await self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._on_message_received
            )
            
            self.logger.info("Communication setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication: {e}")
            raise
    
    async def _on_message_received(self, channel, method, properties, body):
        """Handle incoming messages."""
        try:
            message = AgentMessage.from_json(body.decode())
            self.stats['messages_received'] += 1
            self.stats['last_activity'] = datetime.now()
            
            self.logger.debug(f"Received message: {message.message_type} from {message.sender_id}")
            
            # Add to processing queue
            await self.message_queue.put(message)
            
            # Acknowledge message
            await channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
            self.stats['errors'] += 1
            await channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    async def _message_processor(self):
        """Process messages from the queue."""
        while self.is_running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Handle the message
                await self.handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in message processor: {e}")
                self.stats['errors'] += 1
    
    async def send_message(self, 
                          message_type: str,
                          topic: str,
                          payload: Dict[str, Any],
                          recipient_id: Optional[str] = None,
                          priority: int = 1):
        """Send a message to other agents."""
        try:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                topic=topic,
                payload=payload,
                timestamp=datetime.now(),
                priority=priority
            )
            
            # Publish to RabbitMQ
            await self.channel.basic_publish(
                exchange='pfsense_agents',
                routing_key=topic,
                body=message.to_json().encode(),
                properties=pika.BasicProperties(
                    priority=priority,
                    timestamp=int(time.time())
                )
            )
            
            self.stats['messages_sent'] += 1
            self.stats['last_activity'] = datetime.now()
            
            self.logger.debug(f"Sent message: {message_type} to topic {topic}")
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            self.stats['errors'] += 1
            raise
    
    async def query_llm(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Query the LLM for analysis or decision making."""
        try:
            payload = {
                'prompt': prompt,
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'context': context or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.llm_api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        self.logger.error(f"LLM query failed with status {response.status}")
                        return ""
                        
        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            return ""
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages."""
        while self.is_running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    async def send_heartbeat(self):
        """Send heartbeat message."""
        self.last_heartbeat = datetime.now()
        
        payload = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'status': 'healthy' if self.is_healthy else 'unhealthy',
            'stats': self.stats.copy(),
            'timestamp': self.last_heartbeat.isoformat()
        }
        
        await self.send_message(
            message_type='heartbeat',
            topic='system.heartbeat',
            payload=payload
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'name': self.name,
            'is_running': self.is_running,
            'is_healthy': self.is_healthy,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'stats': self.stats.copy(),
            'config': asdict(self.config)
        }
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def initialize(self):
        """Initialize agent-specific resources."""
        pass
    
    @abstractmethod
    async def run(self):
        """Main agent execution loop."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup agent-specific resources."""
        pass
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        pass

