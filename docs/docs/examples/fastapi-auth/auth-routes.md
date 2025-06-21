---
sidebar_position: 2
---

# Authentication Routes

This section covers the FastAPI authentication endpoints that integrate with SurrealDB for user management and JWT token handling.

## Authentication Router Setup

### Router Configuration

```python
# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from surrealdb import Surreal
from app.database import get_database
from app.auth.auth_handler import AuthHandler
from app.models.user import UserModel
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
import bcrypt

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

async def get_auth_handler(db: Surreal = Depends(get_database)) -> AuthHandler:
    """Dependency to get authentication handler"""
    return AuthHandler(db)

async def get_user_model(db: Surreal = Depends(get_database)) -> UserModel:
    """Dependency to get user model"""
    return UserModel(db)
```

## Registration Endpoint

### User Registration with SurrealDB

```python
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: RegisterRequest,
    user_model: UserModel = Depends(get_user_model),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Register a new user with SurrealDB validation
    
    - **email**: Valid email address (validated by SurrealDB schema)
    - **username**: Unique username
    - **password**: Password (will be hashed)
    - **confirm_password**: Password confirmation
    """
    
    # Validate password confirmation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if user already exists (SurrealDB unique constraints will also catch this)
    existing_user = await user_model.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = await user_model.get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        # Create user in SurrealDB
        new_user = await user_model.create_user(
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash
        )
        
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Extract user ID from SurrealDB record ID
        user_id = new_user["id"].split(":")[1]
        
        # Create access token
        access_token = auth_handler.create_access_token(user_id, new_user["username"])
        
        # Store session in SurrealDB
        await auth_handler.store_session(user_id, access_token)
        
        return UserResponse(
            id=user_id,
            email=new_user["email"],
            username=new_user["username"],
            is_active=new_user["is_active"],
            is_admin=new_user["is_admin"],
            created_at=new_user["created_at"],
            access_token=access_token
        )
        
    except Exception as e:
        # Handle SurrealDB constraint violations
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
```

## Login Endpoint

### User Authentication with SurrealDB

```python
@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: LoginRequest,
    user_model: UserModel = Depends(get_user_model),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Authenticate user and return JWT token
    
    - **email_or_username**: Email address or username
    - **password**: User password
    """
    
    # Try to find user by email first, then username
    user = await user_model.get_user_by_email(login_data.email_or_username)
    if not user:
        user = await user_model.get_user_by_username(login_data.email_or_username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is active
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Extract user ID from SurrealDB record ID
    user_id = user["id"].split(":")[1]
    
    # Create access token
    access_token = auth_handler.create_access_token(user_id, user["username"])
    
    # Store session in SurrealDB
    session = await auth_handler.store_session(user_id, access_token)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            is_admin=user["is_admin"],
            created_at=user["created_at"]
        )
    )
```

## Token Verification and User Info

### Current User Endpoint

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: AuthHandler = Depends(get_auth_handler),
    user_model: UserModel = Depends(get_user_model)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token
    Verifies token against SurrealDB session storage
    """
    
    token = credentials.credentials
    token_data = await auth_handler.verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get fresh user data from SurrealDB
    user = await user_model.get_user_by_id(token_data["user_id"])
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    user_id = current_user["id"].split(":")[1]
    
    return UserResponse(
        id=user_id,
        email=current_user["email"],
        username=current_user["username"],
        is_active=current_user["is_active"],
        is_admin=current_user["is_admin"],
        created_at=current_user["created_at"],
        updated_at=current_user.get("updated_at")
    )
```

## Logout and Session Management

### Logout Endpoint

```python
@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Logout user by revoking the current session in SurrealDB
    """
    
    token = credentials.credentials
    success = await auth_handler.revoke_session(token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout"
        )
    
    return {"message": "Successfully logged out"}

@router.post("/logout-all")
async def logout_all_sessions(
    current_user: dict = Depends(get_current_user),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Logout from all sessions by revoking all user sessions in SurrealDB
    """
    
    user_id = current_user["id"].split(":")[1]
    success = await auth_handler.revoke_all_user_sessions(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout from all sessions"
        )
    
    return {"message": "Successfully logged out from all sessions"}
```

## Token Refresh

### Refresh Token Endpoint

```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: AuthHandler = Depends(get_auth_handler),
    user_model: UserModel = Depends(get_user_model)
):
    """
    Refresh JWT token if current token is valid
    Creates new session in SurrealDB and revokes old one
    """
    
    token = credentials.credentials
    token_data = await auth_handler.verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user data
    user = await user_model.get_user_by_id(token_data["user_id"])
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old session
    await auth_handler.revoke_session(token)
    
    # Create new token
    user_id = user["id"].split(":")[1]
    new_access_token = auth_handler.create_access_token(user_id, user["username"])
    
    # Store new session
    await auth_handler.store_session(user_id, new_access_token)
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            is_admin=user["is_admin"],
            created_at=user["created_at"]
        )
    )
```

## Admin Authentication

### Admin-Only Dependency

```python
async def get_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to ensure current user is an admin
    """
    
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

@router.get("/admin/sessions")
async def get_active_sessions(
    admin_user: dict = Depends(get_admin_user),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Admin endpoint to view all active sessions
    Uses SurrealDB query to get session statistics
    """
    
    db = auth_handler.db
    result = await db.query("""
        SELECT 
            user.username,
            user.email,
            created_at,
            expires_at,
            count() OVER() AS total_sessions
        FROM session 
        WHERE expires_at > time::now()
        ORDER BY created_at DESC
    """)
    
    return {
        "active_sessions": result[0]["result"] if result and result[0]["result"] else [],
        "total_count": len(result[0]["result"]) if result and result[0]["result"] else 0
    }

@router.delete("/admin/cleanup-sessions")
async def cleanup_expired_sessions(
    admin_user: dict = Depends(get_admin_user),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Admin endpoint to clean up expired sessions from SurrealDB
    """
    
    cleaned_count = await auth_handler.cleanup_expired_sessions()
    
    return {
        "message": f"Cleaned up {cleaned_count} expired sessions",
        "cleaned_count": cleaned_count
    }
```

## Pydantic Schemas

### Authentication Schemas

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

class LoginRequest(BaseModel):
    email_or_username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: str
    updated_at: Optional[str] = None
    access_token: Optional[str] = None

    class Config:
        from_attributes = True
```

## Error Handling

### Custom Exception Handlers

```python
# app/auth/exceptions.py
from fastapi import HTTPException, status

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class UserNotFoundError(HTTPException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class UserExistsError(HTTPException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
```

## Usage Examples

### Testing Authentication Endpoints

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "securepassword123",
       "confirm_password": "securepassword123"
     }'

# Login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email_or_username": "user@example.com",
       "password": "securepassword123"
     }'

# Get current user info (requires token)
curl -X GET "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Logout
curl -X POST "http://localhost:8000/auth/logout" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

The authentication system provides secure user management with SurrealDB handling data persistence, constraints, and relationships while FastAPI manages the HTTP layer and JWT token operations.