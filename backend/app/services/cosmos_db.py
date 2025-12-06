"""Azure Cosmos DB Service for chat history storage"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from app.config import settings

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Singleton service for Azure Cosmos DB operations"""
    
    _instance = None
    _client: Optional[CosmosClient] = None
    _database = None
    _conversations_container = None
    _messages_container = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Cosmos DB client and containers"""
        if self._client is None:
            self._client = CosmosClient(
                url=settings.COSMOS_ENDPOINT,
                credential=settings.COSMOS_KEY
            )
            logger.info("Cosmos DB client initialized")
            self._setup_database()
    
    def _setup_database(self):
        """Setup database and containers"""
        try:
            # Create or get database
            self._database = self._client.create_database_if_not_exists(
                id=settings.COSMOS_DATABASE
            )
            logger.info(f"Database '{settings.COSMOS_DATABASE}' ready")
            
            # Create or get conversations container
            self._conversations_container = self._database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER_CONVERSATIONS,
                partition_key=PartitionKey(path="/user_id")
            )
            logger.info(f"Container '{settings.COSMOS_CONTAINER_CONVERSATIONS}' ready")
            
            # Create or get messages container
            self._messages_container = self._database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER_MESSAGES,
                partition_key=PartitionKey(path="/conversation_id")
            )
            logger.info(f"Container '{settings.COSMOS_CONTAINER_MESSAGES}' ready")
            
        except Exception as e:
            logger.error(f"Error setting up Cosmos DB: {str(e)}")
            raise
    
    # ====== Conversation Operations ======
    
    def create_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation
        
        Args:
            conversation_id: Unique conversation ID
            user_id: User ID
            title: Optional conversation title
        
        Returns:
            Created conversation document
        """
        try:
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or "New Conversation",
                "created_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat(),
                "message_count": 0,
                "status": "active"
            }
            
            created = self._conversations_container.create_item(body=conversation)
            logger.info(f"Created conversation: {conversation_id}")
            return created
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    def get_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (partition key)
        
        Returns:
            Conversation document or None if not found
        """
        try:
            conversation = self._conversations_container.read_item(
                item=conversation_id,
                partition_key=user_id
            )
            return conversation
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            raise
    
    def list_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List all conversations for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
        
        Returns:
            List of conversation documents
        """
        try:
            query = f"""
                SELECT * FROM c 
                WHERE c.user_id = @user_id 
                ORDER BY c.last_message_at DESC 
                OFFSET 0 LIMIT {limit}
            """
            
            items = list(self._conversations_container.query_items(
                query=query,
                parameters=[{"name": "@user_id", "value": user_id}],
                enable_cross_partition_query=False,
                partition_key=user_id
            ))
            
            logger.debug(f"Retrieved {len(items)} conversations for user {user_id}")
            return items
            
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            raise
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a conversation
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (partition key)
            updates: Dictionary of fields to update
        
        Returns:
            Updated conversation document
        """
        try:
            # Get existing conversation
            conversation = self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise ValueError(f"Conversation not found: {conversation_id}")
            
            # Apply updates
            conversation.update(updates)
            
            # Replace in database
            updated = self._conversations_container.replace_item(
                item=conversation_id,
                body=conversation
            )
            
            logger.debug(f"Updated conversation: {conversation_id}")
            return updated
            
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            raise
    
    # ====== Message Operations ======
    
    def create_message(
        self,
        message_id: str,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new message
        
        Args:
            message_id: Unique message ID
            conversation_id: Conversation ID (partition key)
            user_id: User ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata (agents used, sources, etc.)
        
        Returns:
            Created message document
        """
        try:
            message = {
                "id": message_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            created = self._messages_container.create_item(body=message)
            
            # Update conversation's last_message_at and message_count
            self.update_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                updates={
                    "last_message_at": message["timestamp"],
                    "message_count": self._get_message_count(conversation_id)
                }
            )
            
            logger.info(f"Created message: {message_id}")
            return created
            
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
        
        Returns:
            List of message documents
        """
        try:
            query = f"""
                SELECT * FROM c 
                WHERE c.conversation_id = @conversation_id 
                ORDER BY c.timestamp ASC 
                OFFSET {offset} LIMIT {limit}
            """
            
            items = list(self._messages_container.query_items(
                query=query,
                parameters=[{"name": "@conversation_id", "value": conversation_id}],
                enable_cross_partition_query=False,
                partition_key=conversation_id
            ))
            
            logger.debug(f"Retrieved {len(items)} messages for conversation {conversation_id}")
            return items
            
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            raise
    
    def _get_message_count(self, conversation_id: str) -> int:
        """Get total message count for a conversation"""
        try:
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.conversation_id = @conversation_id
            """
            
            result = list(self._messages_container.query_items(
                query=query,
                parameters=[{"name": "@conversation_id", "value": conversation_id}],
                enable_cross_partition_query=True
            ))
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.warning(f"Error counting messages: {str(e)}")
            return 0
    
    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (partition key)
        
        Returns:
            True if deleted successfully
        """
        try:
            # Delete all messages first
            messages = self.get_conversation_messages(conversation_id, limit=1000)
            for message in messages:
                self._messages_container.delete_item(
                    item=message["id"],
                    partition_key=conversation_id
                )
            
            # Delete conversation
            self._conversations_container.delete_item(
                item=conversation_id,
                partition_key=user_id
            )
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise


# Global service instance
_cosmos_service = None


def get_cosmos_service() -> CosmosDBService:
    """Get or create the global Cosmos DB service instance"""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
    return _cosmos_service

