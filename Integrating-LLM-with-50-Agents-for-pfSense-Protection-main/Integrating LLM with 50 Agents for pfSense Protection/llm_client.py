"""
LLM Integration Client for pfSense Multi-Agent System

This module provides a client for interacting with Large Language Models
to enhance agent decision-making and analysis capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import aiohttp
import openai
from openai import AsyncOpenAI


@dataclass
class LLMRequest:
    """Structure for LLM requests."""
    prompt: str
    agent_id: str
    agent_type: str
    context: Dict[str, Any]
    max_tokens: int = 1000
    temperature: float = 0.7
    model: str = "gpt-4"


@dataclass
class LLMResponse:
    """Structure for LLM responses."""
    response: str
    confidence: float
    reasoning: str
    suggested_actions: List[str]
    metadata: Dict[str, Any]


class LLMClient:
    """
    Client for interacting with Large Language Models.
    
    Supports OpenAI API and can be extended for other LLM providers.
    Provides specialized methods for security analysis, threat detection,
    and decision-making in the context of pfSense network monitoring.
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # System prompts for different types of analysis
        self.system_prompts = {
            'security_analysis': """
You are a cybersecurity expert analyzing network security events from a pfSense firewall.
Your role is to:
1. Analyze security events and logs for potential threats
2. Assess the severity and impact of security incidents
3. Recommend appropriate response actions
4. Provide clear, actionable insights

Always respond with structured analysis including:
- Threat assessment (severity: low/medium/high/critical)
- Potential impact
- Recommended actions
- Confidence level in your assessment
""",
            
            'traffic_analysis': """
You are a network traffic analysis expert working with pfSense firewall data.
Your role is to:
1. Analyze network traffic patterns for anomalies
2. Identify potential performance issues or bottlenecks
3. Detect unusual communication patterns
4. Recommend optimization or security measures

Provide structured analysis including:
- Traffic pattern assessment
- Anomaly detection results
- Performance implications
- Recommended actions
""",
            
            'log_analysis': """
You are a log analysis expert specializing in pfSense firewall logs.
Your role is to:
1. Parse and interpret various log formats
2. Identify patterns and correlations across log entries
3. Detect anomalies and potential issues
4. Summarize findings and recommend actions

Provide structured analysis including:
- Log pattern summary
- Identified issues or anomalies
- Correlation analysis
- Recommended follow-up actions
""",
            
            'incident_response': """
You are an incident response expert for network security.
Your role is to:
1. Assess security incidents and their severity
2. Recommend immediate response actions
3. Suggest containment and mitigation strategies
4. Provide step-by-step response procedures

Provide structured response including:
- Incident severity assessment
- Immediate actions required
- Containment strategies
- Long-term mitigation recommendations
"""
        }
    
    async def analyze_security_event(self, 
                                   event_data: Dict[str, Any],
                                   agent_context: Dict[str, Any] = None) -> LLMResponse:
        """
        Analyze a security event using LLM.
        
        Args:
            event_data: Security event information
            agent_context: Additional context from the requesting agent
            
        Returns:
            LLMResponse with analysis results
        """
        prompt = self._build_security_analysis_prompt(event_data, agent_context)
        
        return await self._query_llm(
            prompt=prompt,
            system_prompt=self.system_prompts['security_analysis'],
            analysis_type='security_analysis'
        )
    
    async def analyze_traffic_pattern(self,
                                    traffic_data: Dict[str, Any],
                                    baseline_data: Dict[str, Any] = None) -> LLMResponse:
        """
        Analyze network traffic patterns for anomalies.
        
        Args:
            traffic_data: Current traffic statistics and patterns
            baseline_data: Historical baseline for comparison
            
        Returns:
            LLMResponse with traffic analysis results
        """
        prompt = self._build_traffic_analysis_prompt(traffic_data, baseline_data)
        
        return await self._query_llm(
            prompt=prompt,
            system_prompt=self.system_prompts['traffic_analysis'],
            analysis_type='traffic_analysis'
        )
    
    async def analyze_logs(self,
                          log_entries: List[Dict[str, Any]],
                          log_type: str = 'firewall') -> LLMResponse:
        """
        Analyze log entries for patterns and anomalies.
        
        Args:
            log_entries: List of log entries to analyze
            log_type: Type of logs (firewall, system, vpn, etc.)
            
        Returns:
            LLMResponse with log analysis results
        """
        prompt = self._build_log_analysis_prompt(log_entries, log_type)
        
        return await self._query_llm(
            prompt=prompt,
            system_prompt=self.system_prompts['log_analysis'],
            analysis_type='log_analysis'
        )
    
    async def recommend_incident_response(self,
                                        incident_data: Dict[str, Any],
                                        severity: str = 'medium') -> LLMResponse:
        """
        Get incident response recommendations.
        
        Args:
            incident_data: Information about the security incident
            severity: Incident severity level
            
        Returns:
            LLMResponse with incident response recommendations
        """
        prompt = self._build_incident_response_prompt(incident_data, severity)
        
        return await self._query_llm(
            prompt=prompt,
            system_prompt=self.system_prompts['incident_response'],
            analysis_type='incident_response'
        )
    
    async def general_query(self,
                           prompt: str,
                           context: Dict[str, Any] = None,
                           agent_type: str = 'general') -> str:
        """
        Make a general query to the LLM.
        
        Args:
            prompt: The question or request
            context: Additional context information
            agent_type: Type of agent making the request
            
        Returns:
            String response from the LLM
        """
        full_prompt = f"""
Context: {json.dumps(context, indent=2) if context else 'None'}
Agent Type: {agent_type}

Query: {prompt}

Please provide a clear, actionable response based on the context and your expertise in network security and pfSense firewall management.
"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a network security expert specializing in pfSense firewall management and network monitoring."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error in general LLM query: {e}")
            return f"Error processing query: {str(e)}"
    
    def _build_security_analysis_prompt(self, 
                                      event_data: Dict[str, Any],
                                      agent_context: Dict[str, Any] = None) -> str:
        """Build prompt for security event analysis."""
        return f"""
Analyze the following security event:

Event Data:
{json.dumps(event_data, indent=2)}

Agent Context:
{json.dumps(agent_context, indent=2) if agent_context else 'None'}

Please provide a comprehensive security analysis including:
1. Threat assessment and severity level
2. Potential attack vectors or vulnerabilities exploited
3. Immediate risks and potential impact
4. Recommended response actions (prioritized)
5. Indicators to monitor for related activity
6. Your confidence level in this assessment

Format your response as structured JSON with the following fields:
- threat_level: (low/medium/high/critical)
- attack_type: (description of potential attack)
- impact_assessment: (description of potential impact)
- recommended_actions: (array of prioritized actions)
- monitoring_indicators: (array of things to watch for)
- confidence: (0.0-1.0)
- reasoning: (explanation of your analysis)
"""
    
    def _build_traffic_analysis_prompt(self,
                                     traffic_data: Dict[str, Any],
                                     baseline_data: Dict[str, Any] = None) -> str:
        """Build prompt for traffic pattern analysis."""
        return f"""
Analyze the following network traffic data:

Current Traffic Data:
{json.dumps(traffic_data, indent=2)}

Baseline Data (for comparison):
{json.dumps(baseline_data, indent=2) if baseline_data else 'No baseline available'}

Please provide a comprehensive traffic analysis including:
1. Traffic pattern assessment
2. Anomaly detection (compared to baseline if available)
3. Performance implications
4. Security concerns (if any)
5. Recommended actions or optimizations
6. Confidence in your analysis

Format your response as structured JSON with the following fields:
- pattern_assessment: (description of traffic patterns)
- anomalies_detected: (array of detected anomalies)
- performance_impact: (assessment of performance implications)
- security_concerns: (array of potential security issues)
- recommended_actions: (array of recommended actions)
- confidence: (0.0-1.0)
- reasoning: (explanation of your analysis)
"""
    
    def _build_log_analysis_prompt(self,
                                 log_entries: List[Dict[str, Any]],
                                 log_type: str) -> str:
        """Build prompt for log analysis."""
        return f"""
Analyze the following {log_type} log entries:

Log Entries:
{json.dumps(log_entries, indent=2)}

Please provide a comprehensive log analysis including:
1. Pattern identification and summary
2. Anomalies or unusual events detected
3. Correlation analysis between entries
4. Security implications (if any)
5. Recommended follow-up actions
6. Confidence in your analysis

Format your response as structured JSON with the following fields:
- pattern_summary: (summary of identified patterns)
- anomalies: (array of detected anomalies)
- correlations: (array of correlated events)
- security_implications: (array of security concerns)
- recommended_actions: (array of recommended actions)
- confidence: (0.0-1.0)
- reasoning: (explanation of your analysis)
"""
    
    def _build_incident_response_prompt(self,
                                      incident_data: Dict[str, Any],
                                      severity: str) -> str:
        """Build prompt for incident response recommendations."""
        return f"""
Provide incident response recommendations for the following security incident:

Incident Data:
{json.dumps(incident_data, indent=2)}

Incident Severity: {severity}

Please provide comprehensive incident response guidance including:
1. Immediate actions required (first 15 minutes)
2. Short-term containment strategies (first hour)
3. Investigation and analysis steps
4. Long-term mitigation and prevention measures
5. Communication and reporting requirements
6. Recovery procedures

Format your response as structured JSON with the following fields:
- immediate_actions: (array of actions for first 15 minutes)
- containment_strategies: (array of containment measures)
- investigation_steps: (array of investigation procedures)
- mitigation_measures: (array of long-term prevention measures)
- communication_plan: (communication and reporting guidance)
- recovery_procedures: (steps for system recovery)
- confidence: (0.0-1.0)
- reasoning: (explanation of your recommendations)
"""
    
    async def _query_llm(self,
                        prompt: str,
                        system_prompt: str,
                        analysis_type: str) -> LLMResponse:
        """
        Internal method to query the LLM and parse structured responses.
        
        Args:
            prompt: The analysis prompt
            system_prompt: System prompt for context
            analysis_type: Type of analysis being performed
            
        Returns:
            LLMResponse with parsed results
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            # Try to parse as JSON for structured responses
            try:
                parsed_response = json.loads(response_text)
                
                return LLMResponse(
                    response=response_text,
                    confidence=parsed_response.get('confidence', 0.8),
                    reasoning=parsed_response.get('reasoning', ''),
                    suggested_actions=parsed_response.get('recommended_actions', []),
                    metadata={
                        'analysis_type': analysis_type,
                        'parsed_data': parsed_response,
                        'model_used': 'gpt-4'
                    }
                )
                
            except json.JSONDecodeError:
                # If not JSON, return as plain text response
                return LLMResponse(
                    response=response_text,
                    confidence=0.7,
                    reasoning="Plain text response from LLM",
                    suggested_actions=[],
                    metadata={
                        'analysis_type': analysis_type,
                        'model_used': 'gpt-4'
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            return LLMResponse(
                response=f"Error: {str(e)}",
                confidence=0.0,
                reasoning="LLM query failed",
                suggested_actions=[],
                metadata={'error': str(e)}
            )


# Singleton instance for global access
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

