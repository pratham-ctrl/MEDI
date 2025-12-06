"""Orchestrator Agent for routing queries to specialized agents"""

import logging
import json
from typing import Dict, Any, Optional, List
from app.agents.base_agent import BaseAgent
from app.utils.prompts import PROMPTS, EMERGENCY_KEYWORDS, EMERGENCY_RESPONSE
from app.config import settings

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Routes queries to appropriate specialized agents
    Uses GPT-4 for intelligent query analysis and routing
    """
    
    def __init__(self):
        super().__init__(
            agent_name="orchestrator",
            system_prompt=PROMPTS["orchestrator"],
            temperature=settings.ORCHESTRATOR_TEMPERATURE,
            max_tokens=500
        )
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze query and determine which agents to route to
        
        Args:
            query: User query
            context: Optional context (user history, etc.)
        
        Returns:
            Dict with routing decisions
        """
        try:
            # Check for emergency keywords first
            if self._is_emergency(query):
                logger.warning(f"Emergency query detected: {query[:50]}")
                return {
                    "is_emergency": True,
                    "agents": [],
                    "reasoning": "Emergency situation detected",
                    "emergency_response": EMERGENCY_RESPONSE
                }
            
            # Build messages for LLM
            messages = self._build_messages(query)
            
            # Call GPT-4 for routing decision
            response_text = await self._call_llm(messages)
            
            # Parse JSON response
            try:
                routing_decision = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse routing decision: {response_text}")
                # Fallback to medical_qa_agent
                routing_decision = {
                    "agents": ["medical_qa_agent"],
                    "reasoning": "Fallback due to parsing error"
                }
            
            # Validate agents
            valid_agents = [
                "medical_qa_agent",
                "drug_agent",
                "doctor_agent",
                "document_agent"
            ]
            routing_decision["agents"] = [
                agent for agent in routing_decision.get("agents", [])
                if agent in valid_agents
            ]
            
            # Ensure at least one agent
            if not routing_decision["agents"]:
                routing_decision["agents"] = ["medical_qa_agent"]
                routing_decision["reasoning"] = "Default to medical Q&A"
            
            logger.info(
                f"Routing to: {routing_decision['agents']} - "
                f"Reason: {routing_decision.get('reasoning', 'N/A')}"
            )
            
            return {
                "is_emergency": False,
                **routing_decision
            }
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            # Fallback routing
            return {
                "is_emergency": False,
                "agents": ["medical_qa_agent"],
                "reasoning": f"Error occurred: {str(e)}"
            }
    
    def _is_emergency(self, query: str) -> bool:
        """Check if query contains emergency keywords"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in EMERGENCY_KEYWORDS)
    
    async def synthesize_responses(
        self,
        query: str,
        agent_responses: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize responses from multiple agents into a coherent answer
        
        Args:
            query: Original user query
            agent_responses: List of responses from different agents
        
        Returns:
            Synthesized response
        """
        if len(agent_responses) == 1:
            return agent_responses[0].get("content", "")
        
        # Create context from multiple agent responses
        responses_context = "\n\n".join([
            f"From {resp.get('agent', 'unknown')}:\n{resp.get('content', '')}"
            for resp in agent_responses
        ])
        
        synthesis_prompt = f"""You are synthesizing responses from multiple medical agents.
Combine the following responses into a single, coherent answer to the user's question.
Maintain all important information, warnings, and disclaimers.

User Question: {query}

Agent Responses:
{responses_context}

Synthesized Answer:"""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that combines multiple responses."},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        try:
            synthesized = await self._call_llm(messages, temperature=0.3)
            return synthesized
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}")
            # Fallback: return first response
            return agent_responses[0].get("content", "") if agent_responses else ""


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator

