"""Drug Agent for medicine information"""

import logging
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.agents.rag_agent import get_rag_agent
from app.services.sql_database import get_sql_service
from app.services.redis_cache import get_redis_service
from app.utils.prompts import PROMPTS
from app.config import settings

logger = logging.getLogger(__name__)


class DrugAgent(BaseAgent):
    """
    Drug Agent - Provides comprehensive medicine information
    Uses SQL database + RAG for drug information
    """
    
    def __init__(self):
        super().__init__(
            agent_name="drug_agent",
            system_prompt=PROMPTS["drug_agent"],
            temperature=settings.DRUG_AGENT_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS_RESPONSE
        )
        self.rag_agent = get_rag_agent()
        self.sql_service = get_sql_service()
        self.redis_service = get_redis_service()
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process drug-related query
        
        Args:
            query: User's drug query
            context: Optional context
        
        Returns:
            Response with drug information
        """
        try:
            logger.info(f"Processing drug query: {query[:50]}...")
            
            # Extract drug name (simplified - in production use NER)
            drug_name = self._extract_drug_name(query)
            
            # Check cache first
            cached = self.redis_service.get_cached_drug_info(drug_name)
            if cached:
                logger.debug(f"Retrieved drug info from cache: {drug_name}")
                return self._format_response(
                    content=cached.get("content", ""),
                    sources=cached.get("sources", []),
                    add_disclaimer=True
                )
            
            # Get structured data from SQL
            sql_data = self._get_drug_from_sql(drug_name)
            
            # Get additional context from RAG
            rag_results = await self.rag_agent.retrieve_drug_information(drug_name)
            rag_context = self.rag_agent.format_context_for_llm(rag_results)
            
            # Combine SQL and RAG context
            combined_context = self._combine_context(sql_data, rag_context)
            
            # Build messages
            messages = self._build_messages(
                user_query=query,
                context=combined_context
            )
            
            # Generate response
            response_content = await self._call_llm(messages)
            
            # Extract sources
            sources = self._extract_sources(rag_results)
            if sql_data:
                sources.append({
                    "document_id": "sql_drug_database",
                    "similarity_score": 1.0,
                    "content_snippet": "CDSCO Drug Database"
                })
            
            # Format response
            response = self._format_response(
                content=response_content,
                sources=sources,
                add_disclaimer=True
            )
            
            # Cache the response
            self.redis_service.cache_drug_info(drug_name, response)
            
            logger.info(f"Drug information generated for: {drug_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error in Drug Agent: {str(e)}")
            return self._format_response(
                content="I apologize, but I encountered an error retrieving drug information. Please try again.",
                add_disclaimer=False
            )
    
    def _extract_drug_name(self, query: str) -> str:
        """
        Extract drug name from query (simplified version)
        In production, use NER or more sophisticated extraction
        """
        # Simple approach: look for capitalized words or common drug patterns
        words = query.split()
        for word in words:
            if word[0].isupper() and len(word) > 3:
                return word
        return query
    
    def _get_drug_from_sql(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Get drug information from SQL database"""
        try:
            drugs = self.sql_service.search_drugs(drug_name, limit=1)
            if drugs:
                drug_id = drugs[0]["drug_id"]
                return self.sql_service.get_drug_info(drug_id)
            return None
        except Exception as e:
            logger.warning(f"Error querying SQL for drug: {str(e)}")
            return None
    
    def _combine_context(
        self,
        sql_data: Optional[Dict[str, Any]],
        rag_context: str
    ) -> str:
        """Combine SQL and RAG context"""
        context_parts = []
        
        if sql_data:
            sql_context = f"""
Structured Drug Information:
- Generic Name: {sql_data.get('generic_name')}
- Brand Names: {', '.join(sql_data.get('brand_names', []))}
- Category: {sql_data.get('category')}
- Uses: {', '.join(sql_data.get('uses', []))}
- Adult Dosage: {sql_data.get('dosage_adult')}
- Common Side Effects: {', '.join([se.get('effect', '') for se in sql_data.get('side_effects_common', [])])}
"""
            context_parts.append(sql_context)
        
        if rag_context:
            context_parts.append(f"\nAdditional Context:\n{rag_context}")
        
        return "\n\n".join(context_parts)


# Global agent instance
_drug_agent = None


def get_drug_agent() -> DrugAgent:
    """Get or create the global Drug agent instance"""
    global _drug_agent
    if _drug_agent is None:
        _drug_agent = DrugAgent()
    return _drug_agent

