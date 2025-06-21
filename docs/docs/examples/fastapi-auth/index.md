---
sidebar_position: 1
---

# FastAPI Authentication with SurrealDB

This comprehensive guide demonstrates building a FastAPI application with JWT authentication and CRUD operations using SurrealDB as the primary database. Focus is on SurrealDB integration patterns, data modeling, and efficient query operations.

## Overview

A FastAPI application showcasing:
- SurrealDB connection management and configuration
- User authentication with JWT tokens stored in SurrealDB
- Advanced SurrealDB queries for user and profile management
- SurrealDB-specific data types and relationships
- Real-time features using SurrealDB live queries
- Efficient data modeling with SurrealDB records

## Project Structure

```
fastapi-auth-example/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # SurrealDB configuration
│   ├── database.py            # SurrealDB connection management
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_handler.py    # JWT with SurrealDB storage
│   │   └── routes.py          # Authentication endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User SurrealDB model
│   │   └── profile.py        # Profile SurrealDB model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py           # Pydantic schemas
│   │   └── auth.py           # Auth schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py   # SurrealDB user operations
│   │   └── profile_service.py # SurrealDB profile operations
│   └── routers/
│       ├── __init__.py
│       ├── users.py          # User CRUD with SurrealDB
│       └── profiles.py       # Profile CRUD with SurrealDB
├── requirements.txt
└── README.md
```

## SurrealDB Configuration

### Database Connection Setup

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    surrealdb_url: str = "ws://localhost:8000/rpc"
    surrealdb_namespace: str = "fastapi_auth"
    surrealdb_database: str = "main"
    surrealdb_username: str = "root"
    surrealdb_password: str = "root"
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour

    class Config:
        env_file = ".env"

settings = Settings()
```

### SurrealDB Connection Manager

```python
# app/database.py
from surrealdb import Surreal
from app.config import settings
import asyncio
from typing import Optional

class SurrealDBManager:
    def __init__(self):
        self.db: Optional[Surreal] = None
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> Surreal:
        """Establish connection to SurrealDB"""
        async with self._connection_lock:
            if self.db is None:
                self.db = Surreal()
                await self.db.connect(settings.surrealdb_url)
                await self.db.signin({
                    "user": settings.surrealdb_username,
                    "pass": settings.surrealdb_password
                })
                await self.db.use(
                    settings.surrealdb_namespace, 
                    settings.surrealdb_database
                )
                await self._initialize_schema()
            return self.db
    
    async def _initialize_schema(self):
        """Initialize database schema and indexes"""
        # Define user table with constraints
        await self.db.query("""
            DEFINE TABLE user SCHEMAFULL;
            DEFINE FIELD email ON TABLE user TYPE string ASSERT string::is::email($value);
            DEFINE FIELD username ON TABLE user TYPE string;
            DEFINE FIELD password_hash ON TABLE user TYPE string;
            DEFINE FIELD is_active ON TABLE user TYPE bool DEFAULT true;
            DEFINE FIELD is_admin ON TABLE user TYPE bool DEFAULT false;
            DEFINE FIELD created_at ON TABLE user TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE user TYPE datetime DEFAULT time::now();
            DEFINE INDEX unique_email ON TABLE user COLUMNS email UNIQUE;
            DEFINE INDEX unique_username ON TABLE user COLUMNS username UNIQUE;
        """)
        
        # Define profile table with user relationship
        await self.db.query("""
            DEFINE TABLE profile SCHEMAFULL;
            DEFINE FIELD user ON TABLE profile TYPE record(user);
            DEFINE FIELD first_name ON TABLE profile TYPE string;
            DEFINE FIELD last_name ON TABLE profile TYPE string;
            DEFINE FIELD bio ON TABLE profile TYPE string;
            DEFINE FIELD avatar_url ON TABLE profile TYPE string;
            DEFINE FIELD date_of_birth ON TABLE profile TYPE datetime;
            DEFINE FIELD created_at ON TABLE profile TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE profile TYPE datetime DEFAULT time::now();
            DEFINE INDEX unique_user ON TABLE profile COLUMNS user UNIQUE;
        """)
        
        # Define session table for JWT token management
        await self.db.query("""
            DEFINE TABLE session SCHEMAFULL;
            DEFINE FIELD user ON TABLE session TYPE record(user);
            DEFINE FIELD token_hash ON TABLE session TYPE string;
            DEFINE FIELD expires_at ON TABLE session TYPE datetime;
            DEFINE FIELD created_at ON TABLE session TYPE datetime DEFAULT time::now();
            DEFINE INDEX token_hash_idx ON TABLE session COLUMNS token_hash;
            DEFINE INDEX user_sessions ON TABLE session COLUMNS user;
        """)
    
    async def disconnect(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            self.db = None

# Global database manager instance
db_manager = SurrealDBManager()

async def get_database() -> Surreal:
    """Dependency to get database connection"""
    return await db_manager.connect()
```

## Data Models with SurrealDB

### User Model

```python
# app/models/user.py
from typing import Optional, List
from datetime import datetime
from surrealdb import Surreal
from app.database import get_database

class UserModel:
    def __init__(self, db: Surreal):
        self.db = db
    
    async def create_user(self, email: str, username: str, password_hash: str) -> dict:
        """Create a new user in SurrealDB"""
        result = await self.db.create("user", {
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        return result[0] if result else None
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Retrieve user by email using SurrealDB query"""
        result = await self.db.query(
            "SELECT * FROM user WHERE email = $email LIMIT 1",
            {"email": email}
        )
        return result[0]["result"][0] if result and result[0]["result"] else None
    
    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Retrieve user by username"""
        result = await self.db.query(
            "SELECT * FROM user WHERE username = $username LIMIT 1",
            {"username": username}
        )
        return result[0]["result"][0] if result and result[0]["result"] else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Retrieve user by ID"""
        result = await self.db.select(f"user:{user_id}")
        return result if result else None
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[dict]:
        """Update user with SurrealDB merge operation"""
        update_data["updated_at"] = datetime.utcnow().isoformat()
        result = await self.db.merge(f"user:{user_id}", update_data)
        return result if result else None
    
    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user by setting is_active to false"""
        result = await self.db.merge(f"user:{user_id}", {
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        })
        return bool(result)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all active users with pagination"""
        result = await self.db.query(
            "SELECT * FROM user WHERE is_active = true ORDER BY created_at DESC LIMIT $limit START $skip",
            {"limit": limit, "skip": skip}
        )
        return result[0]["result"] if result and result[0]["result"] else []
    
    async def search_users(self, search_term: str) -> List[dict]:
        """Search users by username or email using SurrealDB string functions"""
        result = await self.db.query("""
            SELECT * FROM user 
            WHERE is_active = true 
            AND (string::lowercase(username) CONTAINS string::lowercase($term) 
                 OR string::lowercase(email) CONTAINS string::lowercase($term))
            ORDER BY created_at DESC
        """, {"term": search_term})
        return result[0]["result"] if result and result[0]["result"] else []
```

### Profile Model with Relationships

```python
# app/models/profile.py
from typing import Optional
from datetime import datetime
from surrealdb import Surreal

class ProfileModel:
    def __init__(self, db: Surreal):
        self.db = db
    
    async def create_profile(self, user_id: str, profile_data: dict) -> dict:
        """Create user profile with relationship to user"""
        profile_data.update({
            "user": f"user:{user_id}",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        result = await self.db.create("profile", profile_data)
        return result[0] if result else None
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[dict]:
        """Get profile with user data using SurrealDB relationship"""
        result = await self.db.query("""
            SELECT *, user.* FROM profile 
            WHERE user = $user_record
        """, {"user_record": f"user:{user_id}"})
        return result[0]["result"][0] if result and result[0]["result"] else None
    
    async def update_profile(self, user_id: str, update_data: dict) -> Optional[dict]:
        """Update profile by user ID"""
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # First find the profile
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return None
        
        # Update the profile
        result = await self.db.merge(profile["id"], update_data)
        return result if result else None
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete profile by user ID"""
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        await self.db.delete(profile["id"])
        return True
    
    async def get_profiles_with_users(self, skip: int = 0, limit: int = 100) -> list:
        """Get all profiles with user information"""
        result = await self.db.query("""
            SELECT *, user.username, user.email, user.is_active 
            FROM profile 
            WHERE user.is_active = true
            ORDER BY created_at DESC 
            LIMIT $limit START $skip
        """, {"limit": limit, "skip": skip})
        return result[0]["result"] if result and result[0]["result"] else []
```

## Authentication with SurrealDB

### JWT Token Management

```python
# app/auth/auth_handler.py
import jwt
from datetime import datetime, timedelta
from typing import Optional
from surrealdb import Surreal
from app.config import settings
import hashlib

class AuthHandler:
    def __init__(self, db: Surreal):
        self.db = db
    
    def create_access_token(self, user_id: str, username: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(seconds=settings.jwt_expiration),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    async def store_session(self, user_id: str, token: str) -> dict:
        """Store session in SurrealDB"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_expiration)
        
        session_data = {
            "user": f"user:{user_id}",
            "token_hash": token_hash,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = await self.db.create("session", session_data)
        return result[0] if result else None
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and check session in SurrealDB"""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Check if session exists and is valid
            result = await self.db.query("""
                SELECT *, user.* FROM session 
                WHERE token_hash = $token_hash 
                AND expires_at > $now 
                AND user.is_active = true
            """, {
                "token_hash": token_hash,
                "now": datetime.utcnow().isoformat()
            })
            
            if result and result[0]["result"]:
                return {
                    "user_id": payload["user_id"],
                    "username": payload["username"],
                    "session": result[0]["result"][0]
                }
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def revoke_session(self, token: str) -> bool:
        """Revoke session by deleting from SurrealDB"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await self.db.query(
            "DELETE FROM session WHERE token_hash = $token_hash",
            {"token_hash": token_hash}
        )
        return bool(result)
    
    async def revoke_all_user_sessions(self, user_id: str) -> bool:
        """Revoke all sessions for a user"""
        result = await self.db.query(
            "DELETE FROM session WHERE user = $user_record",
            {"user_record": f"user:{user_id}"}
        )
        return bool(result)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        result = await self.db.query(
            "DELETE FROM session WHERE expires_at < $now",
            {"now": datetime.utcnow().isoformat()}
        )
        return len(result[0]["result"]) if result and result[0]["result"] else 0
```

## Advanced SurrealDB Queries

### Complex User Queries

```python
# app/services/user_service.py
from typing import List, Optional, Dict
from surrealdb import Surreal
from app.models.user import UserModel
from app.models.profile import ProfileModel

class UserService:
    def __init__(self, db: Surreal):
        self.db = db
        self.user_model = UserModel(db)
        self.profile_model = ProfileModel(db)
    
    async def get_user_with_profile(self, user_id: str) -> Optional[Dict]:
        """Get user with profile using SurrealDB relationship query"""
        result = await self.db.query("""
            SELECT *,
                   (SELECT * FROM profile WHERE user = $user_record)[0] AS profile
            FROM user 
            WHERE id = $user_record AND is_active = true
        """, {"user_record": f"user:{user_id}"})
        
        return result[0]["result"][0] if result and result[0]["result"] else None
    
    async def get_users_with_profiles(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all users with their profiles"""
        result = await self.db.query("""
            SELECT *,
                   (SELECT * FROM profile WHERE user = $parent.id)[0] AS profile
            FROM user 
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT $limit START $skip
        """, {"limit": limit, "skip": skip})
        
        return result[0]["result"] if result and result[0]["result"] else []
    
    async def get_user_statistics(self) -> Dict:
        """Get user statistics using SurrealDB aggregation"""
        result = await self.db.query("""
            SELECT 
                count() AS total_users,
                count(is_active = true) AS active_users,
                count(is_admin = true) AS admin_users,
                count(created_at > time::now() - 30d) AS recent_users
            FROM user;
            
            SELECT count() AS total_profiles FROM profile;
            
            SELECT count() AS active_sessions 
            FROM session 
            WHERE expires_at > time::now();
        """)
        
        return {
            "users": result[0]["result"][0] if result[0]["result"] else {},
            "profiles": result[1]["result"][0] if result[1]["result"] else {},
            "sessions": result[2]["result"][0] if result[2]["result"] else {}
        }
    
    async def search_users_advanced(self, 
                                  search_term: str = None,
                                  is_admin: bool = None,
                                  created_after: str = None) -> List[Dict]:
        """Advanced user search with multiple filters"""
        conditions = ["is_active = true"]
        params = {}
        
        if search_term:
            conditions.append("""
                (string::lowercase(username) CONTAINS string::lowercase($search_term) 
                 OR string::lowercase(email) CONTAINS string::lowercase($search_term))
            """)
            params["search_term"] = search_term
        
        if is_admin is not None:
            conditions.append("is_admin = $is_admin")
            params["is_admin"] = is_admin
        
        if created_after:
            conditions.append("created_at > $created_after")
            params["created_after"] = created_after
        
        where_clause = " AND ".join(conditions)
        
        result = await self.db.query(f"""
            SELECT *,
                   (SELECT * FROM profile WHERE user = $parent.id)[0] AS profile
            FROM user 
            WHERE {where_clause}
            ORDER BY created_at DESC
        """, params)
        
        return result[0]["result"] if result and result[0]["result"] else []
```

## Real-time Features with SurrealDB

### Live Queries for Real-time Updates

```python
# app/services/realtime_service.py
from surrealdb import Surreal
from typing import AsyncGenerator, Dict
import asyncio

class RealtimeService:
    def __init__(self, db: Surreal):
        self.db = db
    
    async def live_user_updates(self) -> AsyncGenerator[Dict, None]:
        """Live query for user updates"""
        async for update in self.db.live("user"):
            if update["action"] in ["CREATE", "UPDATE", "DELETE"]:
                yield {
                    "action": update["action"],
                    "table": "user",
                    "data": update["result"]
                }
    
    async def live_profile_updates(self) -> AsyncGenerator[Dict, None]:
        """Live query for profile updates"""
        async for update in self.db.live("profile"):
            if update["action"] in ["CREATE", "UPDATE", "DELETE"]:
                yield {
                    "action": update["action"],
                    "table": "profile",
                    "data": update["result"]
                }
    
    async def live_session_monitoring(self) -> AsyncGenerator[Dict, None]:
        """Monitor active sessions in real-time"""
        async for update in self.db.live("session"):
            yield {
                "action": update["action"],
                "table": "session",
                "session_data": update["result"]
            }
```

## Next Steps

Continue with the following sections:
- [Authentication Routes](./auth-routes.md) - FastAPI endpoints for authentication
- [User CRUD Operations](./user-crud.md) - Complete user management endpoints
- [Profile Management](./profile-management.md) - Profile CRUD with relationships
- [Advanced Queries](./advanced-queries.md) - Complex SurrealDB query patterns
- [Real-time Features](./realtime.md) - WebSocket integration with live queries
- [Testing](./testing.md) - Testing SurrealDB operations