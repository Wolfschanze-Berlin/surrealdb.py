from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from database import get_db
from auth import extract_user_id_from_token
from crud import UserCRUD
from schemas import TokenData

# Security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user_id = extract_user_id_from_token(token)
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except Exception:
        raise credentials_exception
    
    user_crud = UserCRUD(db)
    user = await user_crud.get_user_by_id(token_data.user_id or "")
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user."""
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: dict = Depends(get_current_active_user)):
    """Get current admin user."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
):
    """Get current user if token is provided, otherwise return None."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = extract_user_id_from_token(token)
        if user_id is None:
            return None
        
        user_crud = UserCRUD(db)
        user = await user_crud.get_user_by_id(user_id)
        return user
    except Exception:
        return None