"""Medical Q&A Agent for general health questions"""

import logging
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.agents.rag_agent import get_rag_agent
from app.utils.prompts import PROMPTS
from app.config import settings

logger = logging.getLogger(__name__)


class MedicalQAAgent(BaseAgent):
    """
    Medical Q&A Agent - Answers general health questions
    Uses RAG to retrieve relevant medical knowledge
    """
    
    def __init__(self):
        super().__init__(
            agent_name="medical_qa_agent",
            system_prompt=PROMPTS["medical_qa"],
            temperature=settings.MEDICAL_QA_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS_RESPONSE
        )
        self.rag_agent = get_rag_agent()
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process medical question with RAG
        
        Args:
            query: User's medical question
            context: Optional context
        
        Returns:
            Response with medical information
        """
        try:
            logger.info(f"Processing medical Q&A: {query[:50]}...")
            
            # Retrieve relevant medical knowledge
            rag_results = await self.rag_agent.retrieve_medical_knowledge(query)
            
            # Format context for LLM
            rag_context = self.rag_agent.format_context_for_llm(rag_results)
            
            # Build messages
            messages = self._build_messages(
                user_query=query,
                context=rag_context,
                conversation_history=context.get("history") if context else None
            )
            
            # Generate response
            response_content = await self._call_llm(messages)
            
            # Extract sources
            sources = self._extract_sources(rag_results)
            
            # Format final response
            response = self._format_response(
                content=response_content,
                sources=sources,
                add_disclaimer=True
            )
            
            logger.info("Medical Q&A response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in Medical Q&A Agent: {str(e)}")
            return self._format_response(
                content="I apologize, but I encountered an error processing your medical question. Please try again.",
                add_disclaimer=False
            )


# Global agent instance
_medical_qa_agent = None


def get_medical_qa_agent() -> MedicalQAAgent:
    """Get or create the global Medical Q&A agent instance"""
    global _medical_qa_agent
    if _medical_qa_agent is None:
        _medical_qa_agent = MedicalQAAgent()
    return _medical_qa_agent

