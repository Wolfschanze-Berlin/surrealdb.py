import asyncio
from typing import Optional, Any
from surrealdb import Surreal
from config import settings

class DatabaseManager:
    """SurrealDB connection manager."""
    
    def __init__(self):
        self.db: Optional[Surreal] = None
        self._connected = False
    
    async def connect(self) -> Surreal:
        """Connect to SurrealDB."""
        if self.db is None or not self._connected:
            self.db = Surreal(settings.SURREALDB_URL)
            await self.db.connect()
            await self.db.signin({
                "user": settings.SURREALDB_USERNAME,
                "pass": settings.SURREALDB_PASSWORD
            })
            await self.db.use(settings.SURREALDB_NAMESPACE, settings.SURREALDB_DATABASE)
            self._connected = True
        return self.db
    
    async def disconnect(self):
        """Disconnect from SurrealDB."""
        if self.db and self._connected:
            await self.db.close()
            self._connected = False
            self.db = None
    
    async def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected and self.db is not None

# Global database manager instance
db_manager = DatabaseManager()

async def get_db() -> Surreal:
    """Dependency to get database connection."""
    return await db_manager.connect()

async def init_database():
    """Initialize database with tables and indexes."""
    db = await db_manager.connect()
    
    # Create conversations table with schema
    await db.query("""
        DEFINE TABLE conversations SCHEMAFULL;
        DEFINE FIELD title ON TABLE conversations TYPE string;
        DEFINE FIELD user_id ON TABLE conversations TYPE option<string>;
        DEFINE FIELD created_at ON TABLE conversations TYPE datetime DEFAULT time::now();
        DEFINE FIELD updated_at ON TABLE conversations TYPE datetime DEFAULT time::now();
        DEFINE FIELD is_active ON TABLE conversations TYPE bool DEFAULT true;
        
        DEFINE INDEX conversations_user_id_idx ON TABLE conversations COLUMNS user_id;
        DEFINE INDEX conversations_created_at_idx ON TABLE conversations COLUMNS created_at;
    """)
    
    # Create messages table with schema
    await db.query("""
        DEFINE TABLE messages SCHEMAFULL;
        DEFINE FIELD conversation_id ON TABLE messages TYPE record<conversations>;
        DEFINE FIELD role ON TABLE messages TYPE string ASSERT $value IN ['user', 'assistant', 'system'];
        DEFINE FIELD content ON TABLE messages TYPE string;
        DEFINE FIELD tokens_used ON TABLE messages TYPE option<int>;
        DEFINE FIELD model ON TABLE messages TYPE option<string>;
        DEFINE FIELD created_at ON TABLE messages TYPE datetime DEFAULT time::now();
        
        DEFINE INDEX messages_conversation_id_idx ON TABLE messages COLUMNS conversation_id;
        DEFINE INDEX messages_created_at_idx ON TABLE messages COLUMNS created_at;
        DEFINE INDEX messages_role_idx ON TABLE messages COLUMNS role;
    """)
    
    print("Database tables and indexes created successfully")