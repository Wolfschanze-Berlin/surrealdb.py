import openai
from typing import List, Dict, Any, Optional
from config import settings
from pydantic import BaseModel
from surrealdb import Surreal
from models import (
    ChatHistoryRequest, ChatHistoryResponse,
    ConversationCreate, MessageCreate, Message, Conversation
)
from crud import ConversationCRUD, MessageCRUD
import logging
import uuid

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    conversation_history: List[ChatMessage] = []
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    usage: Dict[str, Any]
    model: str
    conversation_history: List[ChatMessage]

class ChatService:
    """OpenAI ChatGPT service with SurrealDB integration."""
    
    def __init__(self):
        """Initialize the chat service."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using OpenAI API."""
        try:
            # Build messages for OpenAI API
            messages = []
            
            # Add conversation history
            for msg in request.conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": request.message
            })
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content
            
            # Update conversation history
            updated_history = request.conversation_history.copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            updated_history.append(ChatMessage(role="assistant", content=assistant_message))
            
            return ChatResponse(
                response=assistant_message,
                usage=response.usage,
                model=response.model,
                conversation_history=updated_history
            )
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    async def simple_chat(self, message: str) -> str:
        """Simple chat without conversation history."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": message}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in simple chat: {str(e)}")
            raise
    
    async def chat_with_history(self, db: Surreal, request: ChatHistoryRequest) -> ChatHistoryResponse:
        """Chat with conversation history stored in database."""
        try:
            conversation_id = request.conversation_id
            
            # Create new conversation if not provided
            if not conversation_id:
                conversation_create = ConversationCreate(
                    title=f"Chat - {request.message[:50]}...",
                    user_id=request.user_id
                )
                conversation = await ConversationCRUD.create(db, conversation_create)
                conversation_id = conversation.id
            else:
                conversation = await ConversationCRUD.get(db, conversation_id)
                if not conversation:
                    raise ValueError("Conversation not found")
            
            # Get conversation history
            messages = await MessageCRUD.get_by_conversation(db, conversation_id)
            
            # Build OpenAI messages
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            openai_messages.append({
                "role": "user",
                "content": request.message
            })
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=openai_messages,
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.get("total_tokens", 0)
            
            # Save user message to database
            user_message_create = MessageCreate(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                tokens_used=response.usage.get("prompt_tokens", 0),
                model=self.model
            )
            user_message = await MessageCRUD.create(db, user_message_create)
            
            # Save assistant message to database
            assistant_message_create = MessageCreate(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message,
                tokens_used=response.usage.get("completion_tokens", 0),
                model=self.model
            )
            assistant_message_obj = await MessageCRUD.create(db, assistant_message_create)
            
            # Update conversation timestamp
            from models import ConversationUpdate
            await ConversationCRUD.update(db, conversation_id, ConversationUpdate())
            
            # Get updated conversation
            updated_conversation = await ConversationCRUD.get(db, conversation_id)
            
            return ChatHistoryResponse(
                conversation_id=conversation_id,
                message=user_message,
                response=assistant_message_obj,
                conversation=updated_conversation
            )
            
        except Exception as e:
            logger.error(f"Error in chat with history: {str(e)}")
            raise

# Global chat service instance
chat_service = ChatService()