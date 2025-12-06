"""Base Agent class for all AI agents"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
from app.services.azure_openai import get_openai_service
from app.utils.prompts import MEDICAL_DISCLAIMER

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    Provides common functionality for LLM interactions
    """
    
    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent
            system_prompt: System prompt for the agent
            temperature: LLM temperature setting
            max_tokens: Maximum tokens in response
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.openai_service = get_openai_service()
        logger.info(f"Initialized agent: {agent_name}")
    
    @abstractmethod
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query and return a response
        Must be implemented by subclasses
        
        Args:
            query: User query
            context: Optional context (user history, retrieved docs, etc.)
        
        Returns:
            Dict with response and metadata
        """
        pass
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call the LLM with messages
        
        Args:
            messages: List of message dicts
            temperature: Override temperature
            max_tokens: Override max tokens
        
        Returns:
            LLM response text
        """
        try:
            start_time = time.time()
            
            response = await self.openai_service.agenerate_completion(
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            elapsed = (time.time() - start_time) * 1000  # ms
            logger.debug(f"{self.agent_name} LLM call took {elapsed:.2f}ms")
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling LLM in {self.agent_name}: {str(e)}")
            raise
    
    async def _call_llm_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Call the LLM with streaming response
        
        Args:
            messages: List of message dicts
            temperature: Override temperature
            max_tokens: Override max tokens
        
        Yields:
            Response chunks as they arrive
        """
        try:
            stream = await self.openai_service.agenerate_completion_stream(
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming LLM call in {self.agent_name}: {str(e)}")
            raise
    
    def _format_response(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        add_disclaimer: bool = True
    ) -> Dict[str, Any]:
        """
        Format agent response with metadata
        
        Args:
            content: Response content
            sources: Optional list of sources used
            add_disclaimer: Whether to add medical disclaimer
        
        Returns:
            Formatted response dict
        """
        response = {
            "agent": self.agent_name,
            "content": content,
            "sources": sources or []
        }
        
        if add_disclaimer:
            response["content"] += MEDICAL_DISCLAIMER
        
        return response
    
    def _build_messages(
        self,
        user_query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Build messages array for LLM
        
        Args:
            user_query: User's query
            context: Optional context from RAG
            conversation_history: Optional previous messages
        
        Returns:
            List of message dicts
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Build user message with context
        user_message = user_query
        if context:
            user_message = f"Context:\n{context}\n\nUser Question: {user_query}"
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _extract_sources(
        self,
        rag_results: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract source information from RAG results
        
        Args:
            rag_results: List of VectorSearchResult objects
        
        Returns:
            List of source dicts
        """
        sources = []
        for result in rag_results:
            sources.append({
                "document_id": result.document_id,
                "similarity_score": result.similarity_score,
                "content_snippet": result.content[:150] + "..." if len(result.content) > 150 else result.content
            })
        return sources

