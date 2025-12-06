"""RAG Agent for retrieving relevant context from vector stores"""

import logging
from typing import List, Optional, Dict, Any
from app.utils.vector_store import (
    get_medical_knowledge_store,
    get_drug_database_store,
    get_user_documents_store,
    VectorSearchResult
)
from app.services.redis_cache import get_redis_service
from app.config import settings

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    Retrieval-Augmented Generation Agent
    Centralized agent for searching vector stores
    """
    
    def __init__(self):
        """Initialize RAG agent with vector stores"""
        self.medical_store = get_medical_knowledge_store()
        self.drug_store = get_drug_database_store()
        self.user_store = get_user_documents_store()
        self.redis_service = get_redis_service()
        logger.info("RAG Agent initialized")
    
    async def retrieve_medical_knowledge(
        self,
        query: str,
        top_k: int = None,
        use_cache: bool = True
    ) -> List[VectorSearchResult]:
        """
        Search medical knowledge base (WHO, ICMR guidelines)
        
        Args:
            query: Search query
            top_k: Number of results (default from settings)
            use_cache: Whether to use cached results
        
        Returns:
            List of VectorSearchResult objects
        """
        if top_k is None:
            top_k = settings.VECTOR_SEARCH_TOP_K
        
        try:
            # Check cache first
            if use_cache:
                cached = self.redis_service.get_cached_rag_results(f"medical:{query}")
                if cached:
                    logger.debug("Retrieved medical knowledge from cache")
                    return [VectorSearchResult(**r) for r in cached]
            
            # Search vector store
            logger.info(f"Searching medical knowledge for: {query[:50]}...")
            results = self.medical_store.search_similar(
                query=query,
                top_k=top_k,
                min_similarity=0.6  # Minimum relevance threshold
            )
            
            # Cache results
            if use_cache and results:
                cache_data = [
                    {
                        "document_id": r.document_id,
                        "chunk_index": r.chunk_index,
                        "content": r.content,
                        "similarity_score": r.similarity_score,
                        "metadata": r.metadata
                    }
                    for r in results
                ]
                self.redis_service.cache_rag_results(f"medical:{query}", cache_data)
            
            logger.info(f"Found {len(results)} relevant medical knowledge chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving medical knowledge: {str(e)}")
            return []
    
    async def retrieve_drug_information(
        self,
        drug_name: str,
        top_k: int = None,
        use_cache: bool = True
    ) -> List[VectorSearchResult]:
        """
        Search drug database for medicine information
        
        Args:
            drug_name: Medicine name
            top_k: Number of results
            use_cache: Whether to use cached results
        
        Returns:
            List of VectorSearchResult objects
        """
        if top_k is None:
            top_k = settings.VECTOR_SEARCH_TOP_K
        
        try:
            # Check cache
            if use_cache:
                cached = self.redis_service.get_cached_rag_results(f"drug:{drug_name}")
                if cached:
                    logger.debug(f"Retrieved drug info from cache: {drug_name}")
                    return [VectorSearchResult(**r) for r in cached]
            
            # Search drug store
            logger.info(f"Searching drug database for: {drug_name}")
            results = self.drug_store.search_similar(
                query=drug_name,
                top_k=top_k,
                min_similarity=0.5
            )
            
            # Cache results
            if use_cache and results:
                cache_data = [
                    {
                        "document_id": r.document_id,
                        "chunk_index": r.chunk_index,
                        "content": r.content,
                        "similarity_score": r.similarity_score,
                        "metadata": r.metadata
                    }
                    for r in results
                ]
                self.redis_service.cache_rag_results(f"drug:{drug_name}", cache_data)
            
            logger.info(f"Found {len(results)} relevant drug information chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving drug information: {str(e)}")
            return []
    
    async def retrieve_user_documents(
        self,
        user_id: str,
        query: str,
        top_k: int = None
    ) -> List[VectorSearchResult]:
        """
        Search user's personal documents (prescriptions)
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results
        
        Returns:
            List of VectorSearchResult objects
        """
        if top_k is None:
            top_k = settings.VECTOR_SEARCH_TOP_K
        
        try:
            logger.info(f"Searching user documents for user {user_id}")
            results = self.user_store.search_similar(
                query=query,
                top_k=top_k,
                user_id=user_id,
                min_similarity=0.4
            )
            
            logger.info(f"Found {len(results)} relevant user documents")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving user documents: {str(e)}")
            return []
    
    async def retrieve_disease_info(
        self,
        condition: str,
        top_k: int = None,
        use_cache: bool = True
    ) -> List[VectorSearchResult]:
        """
        Search for disease/condition information
        Uses medical knowledge base
        
        Args:
            condition: Disease or condition name
            top_k: Number of results
            use_cache: Whether to use cached results
        
        Returns:
            List of VectorSearchResult objects
        """
        # Use medical knowledge store with specific query format
        query = f"disease condition symptoms treatment {condition}"
        return await self.retrieve_medical_knowledge(query, top_k, use_cache)
    
    async def retrieve_treatment_guidelines(
        self,
        condition: str,
        top_k: int = None
    ) -> List[VectorSearchResult]:
        """
        Search for treatment guidelines for a condition
        
        Args:
            condition: Medical condition
            top_k: Number of results
        
        Returns:
            List of VectorSearchResult objects
        """
        query = f"treatment guidelines recommendations management {condition}"
        return await self.retrieve_medical_knowledge(query, top_k, use_cache=True)
    
    def format_context_for_llm(
        self,
        results: List[VectorSearchResult],
        max_length: int = 3000
    ) -> str:
        """
        Format RAG results into context for LLM
        
        Args:
            results: List of search results
            max_length: Maximum character length
        
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found in knowledge base."
        
        context_parts = []
        current_length = 0
        
        for idx, result in enumerate(results, 1):
            part = (
                f"[Source {idx}] (Relevance: {result.similarity_score:.2f})\n"
                f"{result.content}\n"
            )
            
            part_length = len(part)
            if current_length + part_length > max_length:
                break
            
            context_parts.append(part)
            current_length += part_length
        
        context = "\n---\n".join(context_parts)
        
        logger.debug(f"Formatted context with {len(context_parts)} sources ({current_length} chars)")
        return context


# Global RAG agent instance
_rag_agent = None


def get_rag_agent() -> RAGAgent:
    """Get or create the global RAG agent instance"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent()
    return _rag_agent

