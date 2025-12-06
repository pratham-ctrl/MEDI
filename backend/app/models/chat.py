"""Pydantic models for chat functionality"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: Optional[str] = None
    conversation_id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "role": "user",
                "content": "What are the side effects of Metformin?",
                "timestamp": "2025-10-17T10:30:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request for sending a chat message"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    user_id: str
    stream: bool = False  # Whether to use streaming response
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can I take aspirin with my diabetes medication?",
                "user_id": "user_456",
                "stream": False
            }
        }


class AgentInfo(BaseModel):
    """Information about which agent was used"""
    agent_name: str
    execution_time_ms: float


class SourceInfo(BaseModel):
    """Information about knowledge sources used"""
    source_name: str
    relevance_score: float
    content_snippet: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    conversation_id: str
    message_id: str
    response: str
    agents_used: List[AgentInfo] = []
    sources: List[SourceInfo] = []
    from_cache: bool = False
    total_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "message_id": "msg_789",
                "response": "Common side effects of Metformin include nausea, diarrhea...",
                "agents_used": [
                    {"agent_name": "drug_agent", "execution_time_ms": 450}
                ],
                "sources": [
                    {"source_name": "CDSCO Database", "relevance_score": 0.92}
                ],
                "from_cache": False,
                "total_time_ms": 1250,
                "timestamp": "2025-10-17T10:30:15Z"
            }
        }


class ConversationHistory(BaseModel):
    """Conversation history with messages"""
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    last_message_at: datetime
    message_count: int
    messages: List[ChatMessage]
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "user_id": "user_456",
                "title": "Questions about Metformin",
                "created_at": "2025-10-17T10:00:00Z",
                "last_message_at": "2025-10-17T10:30:00Z",
                "message_count": 8,
                "messages": []
            }
        }


class WebSocketMessageType(str, Enum):
    """WebSocket message types for streaming"""
    START = "start"
    THINKING = "thinking"
    CHUNK = "chunk"
    SOURCE = "source"
    AGENT = "agent"
    DONE = "done"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket message format for streaming"""
    type: WebSocketMessageType
    content: Optional[str] = None
    agent: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None
    full_response: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

