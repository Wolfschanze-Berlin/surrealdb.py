from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
from crud import UserCRUD
from dependencies import get_current_active_user, get_current_admin_user
from schemas import UserResponse, UserUpdate, UserList, MessageResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        is_active=current_user["is_active"],
        is_admin=current_user["is_admin"],
        created_at=current_user["created_at"],
        updated_at=current_user.get("updated_at")
    )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Update current user information."""
    user_crud = UserCRUD(db)
    
    # Check if email is being updated and already exists
    if user_update.email:
        existing_user = await user_crud.get_user_by_email(user_update.email)
        if existing_user and existing_user["id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if username is being updated and already exists
    if user_update.username:
        existing_user = await user_crud.get_user_by_username(user_update.username)
        if existing_user and existing_user["id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    updated_user = await user_crud.update_user(current_user["id"], user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        username=updated_user["username"],
        is_active=updated_user["is_active"],
        is_admin=updated_user["is_admin"],
        created_at=updated_user["created_at"],
        updated_at=updated_user.get("updated_at")
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user),
    db = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user_crud = UserCRUD(db)
    user = await user_crud.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        is_active=user["is_active"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
        updated_at=user.get("updated_at")
    )

@router.get("/", response_model=UserList)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin_user),
    db = Depends(get_db)
):
    """Get all users with pagination (admin only)."""
    user_crud = UserCRUD(db)
    users = await user_crud.get_all_users(skip=skip, limit=limit)
    
    user_responses = [
        UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            is_admin=user["is_admin"],
            created_at=user["created_at"],
            updated_at=user.get("updated_at")
        )
        for user in users
    ]
    
    return UserList(users=user_responses, total=len(user_responses))

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user),
    db = Depends(get_db)
):
    """Delete user by ID (admin only)."""
    user_crud = UserCRUD(db)
    
    # Check if user exists
    user = await user_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = await user_crud.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return {"message": "User deleted successfully"}