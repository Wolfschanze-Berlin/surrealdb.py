from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from chat_service import chat_service, ChatRequest, ChatResponse
from database import get_db
from models import (
    ChatHistoryRequest, ChatHistoryResponse,
    ConversationCreate, ConversationUpdate, Conversation, ConversationWithMessages,
    MessageCreate, Message
)
from crud import ConversationCRUD, MessageCRUD
from surrealdb import Surreal
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.post("/completion", response_model=ChatResponse)
async def chat_completion(request: ChatRequest) -> ChatResponse:
    """
    Generate a chat completion with conversation history.
    
    - **message**: The user's message
    - **conversation_history**: Previous messages in the conversation
    - **max_tokens**: Maximum tokens to generate (optional)
    - **temperature**: Sampling temperature (optional)
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        response = await chat_service.chat_completion(request)
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.post("/simple")
async def simple_chat(message: Dict[str, str]) -> Dict[str, Any]:
    """
    Simple chat endpoint without conversation history.
    
    - **message**: The user's message as {"message": "your text here"}
    """
    try:
        user_message = message.get("message", "").strip()
        
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        response = await chat_service.simple_chat(user_message)
        
        return {
            "message": user_message,
            "response": response,
            "model": chat_service.model
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in simple chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get information about available models."""
    return {
        "current_model": chat_service.model,
        "max_tokens": chat_service.max_tokens,
        "temperature": chat_service.temperature,
        "available_models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview"
        ]
    }

@router.post("/history", response_model=ChatHistoryResponse)
async def chat_with_history(
    request: ChatHistoryRequest,
    db: Surreal = Depends(get_db)
) -> ChatHistoryResponse:
    """
    Chat with conversation history stored in database.
    
    - **message**: The user's message
    - **conversation_id**: ID of existing conversation (optional, creates new if not provided)
    - **user_id**: User ID for the conversation (optional)
    - **max_tokens**: Maximum tokens to generate (optional)
    - **temperature**: Sampling temperature (optional)
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        response = await chat_service.chat_with_history(db, request)
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat with history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation: ConversationCreate,
    db: Surreal = Depends(get_db)
) -> Conversation:
    """Create a new conversation."""
    try:
        return await ConversationCRUD.create(db, conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    db: Surreal = Depends(get_db)
) -> ConversationWithMessages:
    """Get a conversation with its messages."""
    try:
        conversation = await ConversationCRUD.get_with_messages(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )

@router.get("/conversations/user/{user_id}", response_model=List[Conversation])
async def get_user_conversations(
    user_id: str,
    limit: int = 50,
    db: Surreal = Depends(get_db)
) -> List[Conversation]:
    """Get conversations for a user."""
    try:
        return await ConversationCRUD.get_by_user(db, user_id, limit)
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    conversation: ConversationUpdate,
    db: Surreal = Depends(get_db)
) -> Conversation:
    """Update a conversation."""
    try:
        updated_conversation = await ConversationCRUD.update(db, conversation_id, conversation)
        if not updated_conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return updated_conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Surreal = Depends(get_db)
) -> Dict[str, str]:
    """Delete a conversation (soft delete)."""
    try:
        success = await ConversationCRUD.delete(db, conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )

@router.get("/messages/{message_id}", response_model=Message)
async def get_message(
    message_id: str,
    db: Surreal = Depends(get_db)
) -> Message:
    """Get a message by ID."""
    try:
        message = await MessageCRUD.get(db, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message"
        )

@router.get("/status")
async def chat_service_status() -> Dict[str, Any]:
    """Get chat service status."""
    return {
        "status": "active",
        "model": chat_service.model,
        "service": "openai-chatgpt"
    }