"""Doctor Agent for treatment suggestions"""

import logging
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.agents.rag_agent import get_rag_agent
from app.services.sql_database import get_sql_service
from app.utils.prompts import PROMPTS
from app.config import settings

logger = logging.getLogger(__name__)


class DoctorAgent(BaseAgent):
    """
    Doctor Agent - Provides treatment suggestions and health recommendations
    Strict safety guidelines to avoid diagnosis/prescription
    """
    
    def __init__(self):
        super().__init__(
            agent_name="doctor_agent",
            system_prompt=PROMPTS["doctor_agent"],
            temperature=settings.DOCTOR_AGENT_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS_RESPONSE
        )
        self.rag_agent = get_rag_agent()
        self.sql_service = get_sql_service()
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process treatment/recommendation query
        
        Args:
            query: User's query about treatment
            context: Optional context including user_id
        
        Returns:
            Response with treatment suggestions
        """
        try:
            logger.info(f"Processing doctor query: {query[:50]}...")
            
            # Extract condition/symptom from query
            condition = self._extract_condition(query)
            
            # Get treatment guidelines from RAG
            treatment_results = await self.rag_agent.retrieve_treatment_guidelines(condition)
            rag_context = self.rag_agent.format_context_for_llm(treatment_results)
            
            # Get user's prescription history if available
            user_context = ""
            if context and context.get("user_id"):
                user_prescriptions = self._get_user_prescriptions(context["user_id"])
                if user_prescriptions:
                    user_context = f"\n\nUser's Current Medications:\n{user_prescriptions}"
            
            # Combine contexts
            full_context = rag_context + user_context
            
            # Build messages
            messages = self._build_messages(
                user_query=query,
                context=full_context
            )
            
            # Generate response
            response_content = await self._call_llm(messages)
            
            # Extract sources
            sources = self._extract_sources(treatment_results)
            
            # Format response with strong disclaimer
            response = self._format_response(
                content=response_content + "\n\n⚠️ **Important**: These are general suggestions only. Please consult your doctor for personalized medical advice and treatment.",
                sources=sources,
                add_disclaimer=True
            )
            
            logger.info("Doctor agent response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in Doctor Agent: {str(e)}")
            return self._format_response(
                content="I apologize, but I encountered an error. For treatment advice, please consult a qualified healthcare professional.",
                add_disclaimer=False
            )
    
    def _extract_condition(self, query: str) -> str:
        """Extract medical condition from query (simplified)"""
        # In production, use NER for better extraction
        return query
    
    def _get_user_prescriptions(self, user_id: str) -> str:
        """Get user's recent prescriptions"""
        try:
            prescriptions = self.sql_service.list_user_prescriptions(user_id, limit=5)
            if not prescriptions:
                return ""
            
            # Format prescriptions
            medicines_list = []
            for rx in prescriptions:
                extracted = rx.get("extracted_data", {})
                if extracted and "medicines" in extracted:
                    for med in extracted["medicines"]:
                        medicines_list.append(f"- {med.get('name', 'Unknown')}")
            
            return "\n".join(medicines_list) if medicines_list else ""
            
        except Exception as e:
            logger.warning(f"Error fetching user prescriptions: {str(e)}")
            return ""


# Global agent instance
_doctor_agent = None


def get_doctor_agent() -> DoctorAgent:
    """Get or create the global Doctor agent instance"""
    global _doctor_agent
    if _doctor_agent is None:
        _doctor_agent = DoctorAgent()
    return _doctor_agent

