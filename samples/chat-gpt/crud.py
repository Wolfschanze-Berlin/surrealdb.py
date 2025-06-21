from typing import List, Optional
from datetime import datetime
from surrealdb import Surreal
from models import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationWithMessages,
    Message, MessageCreate, MessageUpdate
)
import uuid

class ConversationCRUD:
    """CRUD operations for conversations."""
    
    @staticmethod
    async def create(db: Surreal, conversation: ConversationCreate) -> Conversation:
        """Create a new conversation."""
        conversation_id = f"conversations:{uuid.uuid4()}"
        
        result = await db.create(conversation_id, {
            "title": conversation.title,
            "user_id": conversation.user_id,
            "is_active": conversation.is_active,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return Conversation(
            id=result[0]["id"],
            title=result[0]["title"],
            user_id=result[0].get("user_id"),
            is_active=result[0]["is_active"],
            created_at=datetime.fromisoformat(result[0]["created_at"]),
            updated_at=datetime.fromisoformat(result[0]["updated_at"]) if result[0].get("updated_at") else None
        )
    
    @staticmethod
    async def get(db: Surreal, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        result = await db.select(conversation_id)
        
        if not result:
            return None
        
        return Conversation(
            id=result[0]["id"],
            title=result[0]["title"],
            user_id=result[0].get("user_id"),
            is_active=result[0]["is_active"],
            created_at=datetime.fromisoformat(result[0]["created_at"]),
            updated_at=datetime.fromisoformat(result[0]["updated_at"]) if result[0].get("updated_at") else None
        )
    
    @staticmethod
    async def get_with_messages(db: Surreal, conversation_id: str) -> Optional[ConversationWithMessages]:
        """Get a conversation with its messages."""
        conversation = await ConversationCRUD.get(db, conversation_id)
        if not conversation:
            return None
        
        messages = await MessageCRUD.get_by_conversation(db, conversation_id)
        
        return ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages
        )
    
    @staticmethod
    async def get_by_user(db: Surreal, user_id: str, limit: int = 50) -> List[Conversation]:
        """Get conversations by user ID."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = $user_id AND is_active = true 
            ORDER BY updated_at DESC 
            LIMIT $limit
        """
        
        result = await db.query(query, {"user_id": user_id, "limit": limit})
        
        conversations = []
        for conv in result[0]["result"]:
            conversations.append(Conversation(
                id=conv["id"],
                title=conv["title"],
                user_id=conv.get("user_id"),
                is_active=conv["is_active"],
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"]) if conv.get("updated_at") else None
            ))
        
        return conversations
    
    @staticmethod
    async def update(db: Surreal, conversation_id: str, conversation: ConversationUpdate) -> Optional[Conversation]:
        """Update a conversation."""
        update_data = {}
        if conversation.title is not None:
            update_data["title"] = conversation.title
        if conversation.is_active is not None:
            update_data["is_active"] = conversation.is_active
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = await db.update(conversation_id, update_data)
        
        if not result:
            return None
        
        return Conversation(
            id=result[0]["id"],
            title=result[0]["title"],
            user_id=result[0].get("user_id"),
            is_active=result[0]["is_active"],
            created_at=datetime.fromisoformat(result[0]["created_at"]),
            updated_at=datetime.fromisoformat(result[0]["updated_at"]) if result[0].get("updated_at") else None
        )
    
    @staticmethod
    async def delete(db: Surreal, conversation_id: str) -> bool:
        """Delete a conversation (soft delete)."""
        result = await db.update(conversation_id, {
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return bool(result)

class MessageCRUD:
    """CRUD operations for messages."""
    
    @staticmethod
    async def create(db: Surreal, message: MessageCreate) -> Message:
        """Create a new message."""
        message_id = f"messages:{uuid.uuid4()}"
        
        result = await db.create(message_id, {
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "tokens_used": message.tokens_used,
            "model": message.model,
            "created_at": datetime.utcnow().isoformat()
        })
        
        return Message(
            id=result[0]["id"],
            conversation_id=result[0]["conversation_id"],
            role=result[0]["role"],
            content=result[0]["content"],
            tokens_used=result[0].get("tokens_used"),
            model=result[0].get("model"),
            created_at=datetime.fromisoformat(result[0]["created_at"])
        )
    
    @staticmethod
    async def get_by_conversation(db: Surreal, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation."""
        query = """
            SELECT * FROM messages 
            WHERE conversation_id = $conversation_id 
            ORDER BY created_at ASC
        """
        
        result = await db.query(query, {"conversation_id": conversation_id})
        
        messages = []
        for msg in result[0]["result"]:
            messages.append(Message(
                id=msg["id"],
                conversation_id=msg["conversation_id"],
                role=msg["role"],
                content=msg["content"],
                tokens_used=msg.get("tokens_used"),
                model=msg.get("model"),
                created_at=datetime.fromisoformat(msg["created_at"])
            ))
        
        return messages
    
    @staticmethod
    async def get(db: Surreal, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        result = await db.select(message_id)
        
        if not result:
            return None
        
        return Message(
            id=result[0]["id"],
            conversation_id=result[0]["conversation_id"],
            role=result[0]["role"],
            content=result[0]["content"],
            tokens_used=result[0].get("tokens_used"),
            model=result[0].get("model"),
            created_at=datetime.fromisoformat(result[0]["created_at"])
        )
    
    @staticmethod
    async def update(db: Surreal, message_id: str, message: MessageUpdate) -> Optional[Message]:
        """Update a message."""
        update_data = {}
        if message.content is not None:
            update_data["content"] = message.content
        if message.tokens_used is not None:
            update_data["tokens_used"] = message.tokens_used
        
        result = await db.update(message_id, update_data)
        
        if not result:
            return None
        
        return Message(
            id=result[0]["id"],
            conversation_id=result[0]["conversation_id"],
            role=result[0]["role"],
            content=result[0]["content"],
            tokens_used=result[0].get("tokens_used"),
            model=result[0].get("model"),
            created_at=datetime.fromisoformat(result[0]["created_at"])
        )
    
    @staticmethod
    async def delete(db: Surreal, message_id: str) -> bool:
        """Delete a message."""
        result = await db.delete(message_id)
        return bool(result)