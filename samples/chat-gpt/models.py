from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageBase(BaseModel):
    """Base message model."""
    role: str
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None

class MessageCreate(MessageBase):
    """Message creation model."""
    conversation_id: str

class MessageUpdate(BaseModel):
    """Message update model."""
    content: Optional[str] = None
    tokens_used: Optional[int] = None

class MessageInDB(MessageBase):
    """Message model as stored in database."""
    id: str
    conversation_id: str
    created_at: datetime

class Message(MessageBase):
    """Message model for API responses."""
    id: str
    conversation_id: str
    created_at: datetime

class ConversationBase(BaseModel):
    """Base conversation model."""
    title: str
    user_id: Optional[str] = None
    is_active: bool = True

class ConversationCreate(ConversationBase):
    """Conversation creation model."""
    pass

class ConversationUpdate(BaseModel):
    """Conversation update model."""
    title: Optional[str] = None
    is_active: Optional[bool] = None

class ConversationInDB(ConversationBase):
    """Conversation model as stored in database."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class Conversation(ConversationBase):
    """Conversation model for API responses."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List[Message]] = []

class ConversationWithMessages(Conversation):
    """Conversation model with messages included."""
    messages: List[Message]

class ChatHistoryRequest(BaseModel):
    """Request model for chat with history."""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class ChatHistoryResponse(BaseModel):
    """Response model for chat with history."""
    conversation_id: str
    message: Message
    response: Message
    conversation: Conversation