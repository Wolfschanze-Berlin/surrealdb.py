from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    """User creation model."""
    password: str

class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """User model as stored in database."""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class User(UserBase):
    """User model for API responses."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProfileBase(BaseModel):
    """Base profile model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class ProfileCreate(ProfileBase):
    """Profile creation model."""
    pass

class ProfileUpdate(ProfileBase):
    """Profile update model."""
    pass

class ProfileInDB(ProfileBase):
    """Profile model as stored in database."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class Profile(ProfileBase):
    """Profile model for API responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None