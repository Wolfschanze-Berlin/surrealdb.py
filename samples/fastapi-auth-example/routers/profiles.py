from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from crud import ProfileCRUD
from dependencies import get_current_active_user
from schemas import ProfileResponse, ProfileCreate, ProfileUpdate, MessageResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Get current user's profile."""
    profile_crud = ProfileCRUD(db)
    profile = await profile_crud.get_profile_by_user_id(current_user["id"])
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileResponse(
        id=profile["id"],
        user_id=profile["user_id"],
        first_name=profile.get("first_name"),
        last_name=profile.get("last_name"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
        phone=profile.get("phone"),
        location=profile.get("location"),
        website=profile.get("website"),
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at")
    )

@router.put("/me", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Update current user's profile."""
    profile_crud = ProfileCRUD(db)
    
    updated_profile = await profile_crud.update_profile(current_user["id"], profile_update)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return ProfileResponse(
        id=updated_profile["id"],
        user_id=updated_profile["user_id"],
        first_name=updated_profile.get("first_name"),
        last_name=updated_profile.get("last_name"),
        bio=updated_profile.get("bio"),
        avatar_url=updated_profile.get("avatar_url"),
        phone=updated_profile.get("phone"),
        location=updated_profile.get("location"),
        website=updated_profile.get("website"),
        created_at=updated_profile["created_at"],
        updated_at=updated_profile.get("updated_at")
    )

@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Create profile for current user."""
    profile_crud = ProfileCRUD(db)
    
    # Check if profile already exists
    existing_profile = await profile_crud.get_profile_by_user_id(current_user["id"])
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists"
        )
    
    profile = await profile_crud.create_profile(current_user["id"], profile_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )
    
    return ProfileResponse(
        id=profile["id"],
        user_id=profile["user_id"],
        first_name=profile.get("first_name"),
        last_name=profile.get("last_name"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
        phone=profile.get("phone"),
        location=profile.get("location"),
        website=profile.get("website"),
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at")
    )

@router.get("/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: str,
    db = Depends(get_db)
):
    """Get user profile by user ID (public endpoint)."""
    profile_crud = ProfileCRUD(db)
    profile = await profile_crud.get_profile_by_user_id(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileResponse(
        id=profile["id"],
        user_id=profile["user_id"],
        first_name=profile.get("first_name"),
        last_name=profile.get("last_name"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
        phone=profile.get("phone"),
        location=profile.get("location"),
        website=profile.get("website"),
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at")
    )