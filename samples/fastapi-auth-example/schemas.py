from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Token schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data for validation."""
    user_id: Optional[str] = None

# Authentication schemas
class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str

# User schemas
class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: EmailStr
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserUpdate(BaseModel):
    """User update request."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class UserList(BaseModel):
    """User list response."""
    users: list[UserResponse]
    total: int

# Profile schemas
class ProfileResponse(BaseModel):
    """Profile response schema."""
    id: str
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProfileCreate(BaseModel):
    """Profile creation request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class ProfileUpdate(BaseModel):
    """Profile update request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

# Generic response schemas
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str