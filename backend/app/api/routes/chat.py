"""Chat API routes with REST and WebSocket support"""

import logging
import uuid
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from app.models.chat import ChatRequest, ChatResponse, ConversationHistory, WebSocketMessage, WebSocketMessageType
from app.agents.orchestrator import get_orchestrator
from app.agents.medical_qa_agent import get_medical_qa_agent
from app.agents.drug_agent import get_drug_agent
from app.agents.doctor_agent import get_doctor_agent
from app.services.cosmos_db import get_cosmos_service
from app.services.redis_cache import get_redis_service
from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a chat message (REST endpoint)
    
    Args:
        request: Chat request with message
        current_user: Authenticated user
    
    Returns:
        Chat response with agent results
    """
    try:
        start_time = time.time()
        logger.info(f"Chat message from user {request.user_id}: {request.message[:50]}...")
        
        # Check cache first
        redis_service = get_redis_service()
        cached = redis_service.get_cached_chat_response(request.message)
        if cached:
            logger.info("Returning cached response")
            return ChatResponse(
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                message_id=str(uuid.uuid4()),
                response=cached["response"],
                agents_used=cached.get("agents_used", []),
                sources=cached.get("sources", []),
                from_cache=True,
                total_time_ms=(time.time() - start_time) * 1000
            )
        
        # Get or create conversation
        cosmos_service = get_cosmos_service()
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            cosmos_service.create_conversation(
                conversation_id=conversation_id,
                user_id=request.user_id
            )
        
        # Route query through orchestrator
        orchestrator = get_orchestrator()
        routing = await orchestrator.process(request.message)
        
        # Check for emergency
        if routing.get("is_emergency"):
            response_text = routing["emergency_response"]
            agents_used = []
            sources = []
        else:
            # Call appropriate agents
            agent_responses = await _call_agents(
                routing["agents"],
                request.message,
                {"user_id": request.user_id}
            )
            
            # Synthesize responses
            if len(agent_responses) > 1:
                response_text = await orchestrator.synthesize_responses(
                    request.message,
                    agent_responses
                )
            else:
                response_text = agent_responses[0].get("content", "") if agent_responses else "I apologize, I couldn't process your request."
            
            # Collect agents used and sources
            agents_used = [{"agent_name": r["agent"], "execution_time_ms": 0} for r in agent_responses]
            sources = []
            for r in agent_responses:
                sources.extend(r.get("sources", []))
        
        # Save to Cosmos DB
        message_id = str(uuid.uuid4())
        cosmos_service.create_message(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=request.user_id,
            role="user",
            content=request.message
        )
        
        response_message_id = str(uuid.uuid4())
        cosmos_service.create_message(
            message_id=response_message_id,
            conversation_id=conversation_id,
            user_id=request.user_id,
            role="assistant",
            content=response_text,
            metadata={"agents_used": [a["agent_name"] for a in agents_used]}
        )
        
        # Cache response
        redis_service.cache_chat_response(request.message, {
            "response": response_text,
            "agents_used": agents_used,
            "sources": sources
        })
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Chat response generated in {total_time:.2f}ms")
        
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=response_message_id,
            response=response_text,
            agents_used=agents_used,
            sources=sources,
            from_cache=False,
            total_time_ms=total_time
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time streaming chat
    
    Args:
        websocket: WebSocket connection
        conversation_id: Conversation identifier
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established: {conversation_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            user_message = data.get("message")
            user_id = data.get("user_id")
            
            if not user_message or not user_id:
                await websocket.send_json(
                    WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        error="Missing message or user_id"
                    ).dict()
                )
                continue
            
            logger.info(f"WebSocket message from {user_id}: {user_message[:50]}...")
            
            # Send start message
            await websocket.send_json(
                WebSocketMessage(type=WebSocketMessageType.START).dict()
            )
            
            # Route through orchestrator
            orchestrator = get_orchestrator()
            routing = await orchestrator.process(user_message)
            
            # Send thinking message with agents
            await websocket.send_json(
                WebSocketMessage(
                    type=WebSocketMessageType.THINKING,
                    metadata={"agents": routing.get("agents", [])}
                ).dict()
            )
            
            # Process with agents (streaming not implemented yet - would need async streaming)
            agent_responses = await _call_agents(
                routing.get("agents", ["medical_qa_agent"]),
                user_message,
                {"user_id": user_id}
            )
            
            # Get full response
            if len(agent_responses) > 1:
                full_response = await orchestrator.synthesize_responses(user_message, agent_responses)
            else:
                full_response = agent_responses[0].get("content", "") if agent_responses else ""
            
            # Send response in chunks (simulated streaming)
            words = full_response.split()
            for i in range(0, len(words), 5):  # Send 5 words at a time
                chunk = " ".join(words[i:i+5])
                await websocket.send_json(
                    WebSocketMessage(
                        type=WebSocketMessageType.CHUNK,
                        content=chunk + " "
                    ).dict()
                )
            
            # Send done message
            await websocket.send_json(
                WebSocketMessage(
                    type=WebSocketMessageType.DONE,
                    full_response=full_response
                ).dict()
            )
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json(
                WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    error=str(e)
                ).dict()
            )
        except:
            pass


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get conversation history
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
    
    Returns:
        Conversation history with messages
    """
    try:
        cosmos_service = get_cosmos_service()
        
        # Get conversation
        conversation = cosmos_service.get_conversation(conversation_id, current_user["user_id"])
        if not conversation:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages
        messages = cosmos_service.get_conversation_messages(conversation_id)
        
        # Format response
        from app.models.chat import ChatMessage, MessageRole
        chat_messages = [
            ChatMessage(
                conversation_id=msg["conversation_id"],
                role=MessageRole(msg["role"]),
                content=msg["content"],
                timestamp=msg["timestamp"],
                metadata=msg.get("metadata")
            )
            for msg in messages
        ]
        
        return ConversationHistory(
            conversation_id=conversation["id"],
            user_id=conversation["user_id"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            last_message_at=conversation["last_message_at"],
            message_count=conversation["message_count"],
            messages=chat_messages
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise


@router.post("/new")
async def create_conversation(
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new conversation
    
    Args:
        current_user: Authenticated user
    
    Returns:
        New conversation ID
    """
    try:
        conversation_id = str(uuid.uuid4())
        
        cosmos_service = get_cosmos_service()
        cosmos_service.create_conversation(
            conversation_id=conversation_id,
            user_id=current_user["user_id"]
        )
        
        logger.info(f"Created new conversation: {conversation_id}")
        return {"conversation_id": conversation_id}
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise


async def _call_agents(
    agent_names: list,
    query: str,
    context: Dict
) -> list:
    """Call specified agents and return their responses"""
    agent_map = {
        "medical_qa_agent": get_medical_qa_agent(),
        "drug_agent": get_drug_agent(),
        "doctor_agent": get_doctor_agent()
    }
    
    responses = []
    for agent_name in agent_names:
        if agent_name in agent_map:
            agent = agent_map[agent_name]
            response = await agent.process(query, context)
            responses.append(response)
    
    return responses

