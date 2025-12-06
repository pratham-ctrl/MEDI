"""Azure OpenAI Service Client for GPT-4 and Embeddings"""

import logging
from typing import List, Optional, AsyncIterator
from openai import AzureOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from app.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Singleton service for Azure OpenAI interactions"""
    
    _instance = None
    _sync_client: Optional[AzureOpenAI] = None
    _async_client: Optional[AsyncAzureOpenAI] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Azure OpenAI clients"""
        if self._sync_client is None:
            self._sync_client = AzureOpenAI(
                api_key=settings.OPENAI_GPT_API_KEY,
                api_version=settings.OPENAI_GPT_API_VERSION,
                azure_endpoint=settings.OPENAI_GPT_ENDPOINT
            )
            logger.info("Azure OpenAI sync client initialized")
        
        if self._async_client is None:
            self._async_client = AsyncAzureOpenAI(
                api_key=settings.OPENAI_GPT_API_KEY,
                api_version=settings.OPENAI_GPT_API_VERSION,
                azure_endpoint=settings.OPENAI_GPT_ENDPOINT
            )
            logger.info("Azure OpenAI async client initialized")
    
    def generate_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ChatCompletion:
        """
        Generate a chat completion (synchronous)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for the API
        
        Returns:
            ChatCompletion object
        """
        try:
            response = self._sync_client.chat.completions.create(
                model=settings.OPENAI_GPT4_DEPLOYMENT,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            logger.debug(f"Generated completion with {response.usage.total_tokens} tokens")
            return response
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            raise
    
    async def agenerate_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ChatCompletion:
        """
        Generate a chat completion (asynchronous)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for the API
        
        Returns:
            ChatCompletion object
        """
        try:
            response = await self._async_client.chat.completions.create(
                model=settings.OPENAI_GPT4_DEPLOYMENT,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            logger.debug(f"Generated async completion with {response.usage.total_tokens} tokens")
            return response
        except Exception as e:
            logger.error(f"Error generating async completion: {str(e)}")
            raise
    
    async def agenerate_completion_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        Generate a streaming chat completion (asynchronous)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for the API
        
        Yields:
            ChatCompletionChunk objects as they arrive
        """
        try:
            stream = await self._async_client.chat.completions.create(
                model=settings.OPENAI_GPT4_DEPLOYMENT,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating streaming completion: {str(e)}")
            raise
    
    def generate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts (synchronous)
        
        Args:
            texts: List of text strings to embed
            **kwargs: Additional parameters for the API
        
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        try:
            response = self._sync_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_DEPLOYMENT,
                input=texts,
                **kwargs
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def agenerate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts (asynchronous)
        
        Args:
            texts: List of text strings to embed
            **kwargs: Additional parameters for the API
        
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        try:
            response = await self._async_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_DEPLOYMENT,
                input=texts,
                **kwargs
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} async embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating async embeddings: {str(e)}")
            raise
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in a text string
        
        Args:
            text: Text to count tokens for
            model: Model name (defaults to GPT-4)
        
        Returns:
            Number of tokens
        """
        try:
            import tiktoken
            
            if model is None:
                model = settings.OPENAI_GPT4_DEPLOYMENT
            
            encoding = tiktoken.encoding_for_model(model)
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4


# Global service instance
_openai_service = None


def get_openai_service() -> AzureOpenAIService:
    """Get or create the global Azure OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = AzureOpenAIService()
    return _openai_service

