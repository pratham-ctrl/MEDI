"""Redis Cache Service for caching queries and data"""

import logging
import json
import hashlib
from typing import Any, Optional
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Singleton service for Redis caching operations"""
    
    _instance = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Redis client"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    ssl=True,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_keepalive=True
                )
                logger.info("Redis client initialized")
                self._test_connection()
            except Exception as e:
                logger.warning(f"Redis initialization failed: {str(e)} - Running without cache")
                self._redis_client = None
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self._redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)} - Cache will be disabled")
            self._redis_client = None
    
    def _generate_key(self, prefix: str, value: str) -> str:
        """Generate a cache key with MD5 hash"""
        hash_value = hashlib.md5(value.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)
        
        Returns:
            True if successful
        """
        if not self._redis_client:
            return False
            
        try:
            serialized = json.dumps(value)
            if ttl:
                self._redis_client.setex(key, ttl, serialized)
            else:
                self._redis_client.set(key, serialized)
            
            logger.debug(f"Cached: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        if not self._redis_client:
            return None
            
        try:
            value = self._redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted
        """
        if not self._redis_client:
            return False
            
        try:
            deleted = self._redis_client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        if not self._redis_client:
            return False
            
        try:
            return self._redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence: {str(e)}")
            return False
    
    # ====== Specialized Cache Methods ======
    
    def cache_chat_response(
        self,
        query: str,
        response: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache a chat response"""
        if ttl is None:
            ttl = settings.CACHE_TTL_CHAT_RESPONSE
        
        key = self._generate_key("chat", query)
        return self.set(key, response, ttl)
    
    def get_cached_chat_response(self, query: str) -> Optional[dict]:
        """Get cached chat response"""
        key = self._generate_key("chat", query)
        return self.get(key)
    
    def cache_drug_info(
        self,
        drug_name: str,
        drug_info: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache drug information"""
        if ttl is None:
            ttl = settings.CACHE_TTL_DRUG_INFO
        
        key = f"drug:{drug_name.lower()}"
        return self.set(key, drug_info, ttl)
    
    def get_cached_drug_info(self, drug_name: str) -> Optional[dict]:
        """Get cached drug information"""
        key = f"drug:{drug_name.lower()}"
        return self.get(key)
    
    def cache_rag_results(
        self,
        query: str,
        results: list,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache RAG search results"""
        if ttl is None:
            ttl = settings.CACHE_TTL_RAG_RESULTS
        
        key = self._generate_key("rag", query)
        return self.set(key, results, ttl)
    
    def get_cached_rag_results(self, query: str) -> Optional[list]:
        """Get cached RAG results"""
        key = self._generate_key("rag", query)
        return self.get(key)
    
    def cache_user_session(
        self,
        session_id: str,
        session_data: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache user session"""
        if ttl is None:
            ttl = settings.CACHE_TTL_USER_SESSION
        
        key = f"session:{session_id}"
        return self.set(key, session_data, ttl)
    
    def get_user_session(self, session_id: str) -> Optional[dict]:
        """Get cached user session"""
        key = f"session:{session_id}"
        return self.get(key)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Redis pattern (e.g., 'drug:*')
        
        Returns:
            Number of keys deleted
        """
        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                deleted = self._redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {str(e)}")
            return 0
    
    def get_stats(self) -> dict:
        """Get Redis cache statistics"""
        try:
            info = self._redis_client.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) * 100
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {str(e)}")
            return {}


# Global service instance
_redis_service = None


def get_redis_service() -> RedisCacheService:
    """Get or create the global Redis service instance"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisCacheService()
    return _redis_service

