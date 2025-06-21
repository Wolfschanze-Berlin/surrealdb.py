from typing import Optional, List, Dict, Any
from auth import get_password_hash, verify_password
from schemas import UserRegister, UserUpdate, ProfileCreate, ProfileUpdate
from datetime import datetime

class UserCRUD:
    """User CRUD operations."""
    
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, user: UserRegister) -> Dict[str, Any]:
        """Create a new user."""
        hashed_password = get_password_hash(user.password)
        
        result = await self.db.create("users", {
            "email": user.email,
            "username": user.username,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return result[0] if result else {}
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        result = await self.db.query("SELECT * FROM users WHERE email = $email", {"email": email})
        return result[0][0] if result and result[0] else None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        result = await self.db.query("SELECT * FROM users WHERE username = $username", {"username": username})
        return result[0][0] if result and result[0] else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        result = await self.db.select(user_id)
        return result if result else None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return user
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user information."""
        update_data = {}
        if user_update.email is not None:
            update_data["email"] = user_update.email
        if user_update.username is not None:
            update_data["username"] = user_update.username
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            result = await self.db.update(user_id, update_data)
            return result
        return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        result = await self.db.delete(user_id)
        return result is not None
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all users with pagination."""
        result = await self.db.query(f"SELECT * FROM users LIMIT {limit} START {skip}")
        return result[0] if result else []

class ProfileCRUD:
    """Profile CRUD operations."""
    
    def __init__(self, db):
        self.db = db
    
    async def create_profile(self, user_id: str, profile: ProfileCreate) -> Dict[str, Any]:
        """Create a new profile."""
        result = await self.db.create("profiles", {
            "user_id": user_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "phone": profile.phone,
            "location": profile.location,
            "website": profile.website,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return result[0] if result else {}
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get profile by user ID."""
        result = await self.db.query("SELECT * FROM profiles WHERE user_id = $user_id", {"user_id": user_id})
        return result[0][0] if result and result[0] else None
    
    async def update_profile(self, user_id: str, profile_update: ProfileUpdate) -> Optional[Dict[str, Any]]:
        """Update profile information."""
        # First get the profile
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return None
        
        update_data = {}
        if profile_update.first_name is not None:
            update_data["first_name"] = profile_update.first_name
        if profile_update.last_name is not None:
            update_data["last_name"] = profile_update.last_name
        if profile_update.bio is not None:
            update_data["bio"] = profile_update.bio
        if profile_update.avatar_url is not None:
            update_data["avatar_url"] = profile_update.avatar_url
        if profile_update.phone is not None:
            update_data["phone"] = profile_update.phone
        if profile_update.location is not None:
            update_data["location"] = profile_update.location
        if profile_update.website is not None:
            update_data["website"] = profile_update.website
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            result = await self.db.update(profile["id"], update_data)
            return result
        return profile
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete profile by user ID."""
        profile = await self.get_profile_by_user_id(user_id)
        if profile:
            result = await self.db.delete(profile["id"])
            return result is not None
        return False