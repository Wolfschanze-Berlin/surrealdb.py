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
    
    # Create users table with schema
    await db.query("""
        DEFINE TABLE users SCHEMAFULL;
        DEFINE FIELD email ON TABLE users TYPE string ASSERT string::is::email($value);
        DEFINE FIELD username ON TABLE users TYPE string;
        DEFINE FIELD hashed_password ON TABLE users TYPE string;
        DEFINE FIELD is_active ON TABLE users TYPE bool DEFAULT true;
        DEFINE FIELD is_admin ON TABLE users TYPE bool DEFAULT false;
        DEFINE FIELD created_at ON TABLE users TYPE datetime DEFAULT time::now();
        DEFINE FIELD updated_at ON TABLE users TYPE datetime DEFAULT time::now();
        
        DEFINE INDEX users_email_idx ON TABLE users COLUMNS email UNIQUE;
        DEFINE INDEX users_username_idx ON TABLE users COLUMNS username UNIQUE;
    """)
    
    # Create profiles table with schema
    await db.query("""
        DEFINE TABLE profiles SCHEMAFULL;
        DEFINE FIELD user_id ON TABLE profiles TYPE record<users>;
        DEFINE FIELD first_name ON TABLE profiles TYPE option<string>;
        DEFINE FIELD last_name ON TABLE profiles TYPE option<string>;
        DEFINE FIELD bio ON TABLE profiles TYPE option<string>;
        DEFINE FIELD avatar_url ON TABLE profiles TYPE option<string>;
        DEFINE FIELD phone ON TABLE profiles TYPE option<string>;
        DEFINE FIELD location ON TABLE profiles TYPE option<string>;
        DEFINE FIELD website ON TABLE profiles TYPE option<string>;
        DEFINE FIELD created_at ON TABLE profiles TYPE datetime DEFAULT time::now();
        DEFINE FIELD updated_at ON TABLE profiles TYPE datetime DEFAULT time::now();
        
        DEFINE INDEX profiles_user_id_idx ON TABLE profiles COLUMNS user_id UNIQUE;
    """)
    
    print("Database tables and indexes created successfully")