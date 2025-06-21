---
sidebar_position: 4
---

# Profile Management

This section demonstrates profile CRUD operations with SurrealDB relationships, showing how to manage user profiles that are linked to user accounts through SurrealDB's powerful relationship system.

## Profile Router Setup

### Router Configuration with Relationships

```python
# app/routers/profiles.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
from surrealdb import Surreal
from app.database import get_database
from app.auth.routes import get_current_user, get_admin_user
from app.models.profile import ProfileModel
from app.models.user import UserModel
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, ProfileListResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])

async def get_profile_model(db: Surreal = Depends(get_database)) -> ProfileModel:
    """Dependency to get profile model"""
    return ProfileModel(db)

async def get_user_model(db: Surreal = Depends(get_database)) -> UserModel:
    """Dependency to get user model"""
    return UserModel(db)
```

## Create Profile Operations

### Create User Profile

```python
@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Create a profile for the current user
    Uses SurrealDB relationships to link profile to user
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    # Check if profile already exists
    existing_profile = await profile_model.get_profile_by_user_id(current_user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )
    
    # Prepare profile data
    profile_dict = profile_data.dict(exclude_unset=True)
    
    try:
        # Create profile with user relationship
        new_profile = await profile_model.create_profile(current_user_id, profile_dict)
        
        if not new_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile"
            )
        
        profile_id = new_profile["id"].split(":")[1]
        
        return ProfileResponse(
            id=profile_id,
            user_id=current_user_id,
            first_name=new_profile.get("first_name"),
            last_name=new_profile.get("last_name"),
            bio=new_profile.get("bio"),
            avatar_url=new_profile.get("avatar_url"),
            date_of_birth=new_profile.get("date_of_birth"),
            created_at=new_profile["created_at"],
            updated_at=new_profile.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )
```

### Create Profile for Specific User (Admin)

```python
@router.post("/user/{user_id}", response_model=ProfileResponse)
async def create_profile_for_user(
    user_id: str,
    profile_data: ProfileCreate,
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model),
    user_model: UserModel = Depends(get_user_model)
):
    """
    Create a profile for a specific user (Admin only)
    """
    
    # Verify user exists
    user = await user_model.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if profile already exists
    existing_profile = await profile_model.get_profile_by_user_id(user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )
    
    profile_dict = profile_data.dict(exclude_unset=True)
    
    try:
        new_profile = await profile_model.create_profile(user_id, profile_dict)
        
        profile_id = new_profile["id"].split(":")[1]
        
        return ProfileResponse(
            id=profile_id,
            user_id=user_id,
            first_name=new_profile.get("first_name"),
            last_name=new_profile.get("last_name"),
            bio=new_profile.get("bio"),
            avatar_url=new_profile.get("avatar_url"),
            date_of_birth=new_profile.get("date_of_birth"),
            created_at=new_profile["created_at"],
            updated_at=new_profile.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )
```

## Read Profile Operations

### Get Current User's Profile

```python
@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Get the current user's profile
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    profile = await profile_model.get_profile_by_user_id(current_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile_id = profile["id"].split(":")[1]
    user_id = profile["user"]["id"].split(":")[1] if isinstance(profile["user"], dict) else current_user_id
    
    return ProfileResponse(
        id=profile_id,
        user_id=user_id,
        first_name=profile.get("first_name"),
        last_name=profile.get("last_name"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
        date_of_birth=profile.get("date_of_birth"),
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at")
    )
```

### Get Profile by User ID

```python
@router.get("/user/{user_id}", response_model=ProfileResponse)
async def get_profile_by_user_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Get profile by user ID
    Users can only access their own profile unless they are admin
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    # Check permissions
    if user_id != current_user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    profile = await profile_model.get_profile_by_user_id(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile_id = profile["id"].split(":")[1]
    
    return ProfileResponse(
        id=profile_id,
        user_id=user_id,
        first_name=profile.get("first_name"),
        last_name=profile.get("last_name"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
        date_of_birth=profile.get("date_of_birth"),
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at")
    )
```

### List All Profiles with User Information

```python
@router.get("/", response_model=ProfileListResponse)
async def list_profiles(
    skip: int = Query(0, ge=0, description="Number of profiles to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of profiles to return"),
    search: Optional[str] = Query(None, description="Search in names and bio"),
    has_avatar: Optional[bool] = Query(None, description="Filter by avatar presence"),
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    List all profiles with user information (Admin only)
    Uses SurrealDB relationships to include user data
    """
    
    db = profile_model.db
    
    # Build dynamic query
    conditions = ["user.is_active = true"]
    params = {"skip": skip, "limit": limit}
    
    if search:
        conditions.append("""
            (string::lowercase(first_name) CONTAINS string::lowercase($search) 
             OR string::lowercase(last_name) CONTAINS string::lowercase($search)
             OR string::lowercase(bio) CONTAINS string::lowercase($search))
        """)
        params["search"] = search
    
    if has_avatar is not None:
        if has_avatar:
            conditions.append("avatar_url IS NOT NULL AND avatar_url != ''")
        else:
            conditions.append("(avatar_url IS NULL OR avatar_url = '')")
    
    where_clause = " AND ".join(conditions)
    
    try:
        # Get profiles with user information and count
        result = await db.query(f"""
            SELECT *,
                   user.username,
                   user.email,
                   user.is_admin,
                   user.created_at AS user_created_at
            FROM profile 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT $limit START $skip;
            
            SELECT count() AS total FROM profile WHERE {where_clause};
        """, params)
        
        profiles = result[0]["result"] if result and result[0]["result"] else []
        total_count = result[1]["result"][0]["total"] if result and len(result) > 1 and result[1]["result"] else 0
        
        # Convert to response format
        profile_responses = []
        for profile in profiles:
            profile_id = profile["id"].split(":")[1]
            user_id = profile["user"]["id"].split(":")[1] if isinstance(profile["user"], dict) else profile["user"].split(":")[1]
            
            profile_responses.append(ProfileResponse(
                id=profile_id,
                user_id=user_id,
                username=profile.get("username"),
                email=profile.get("email"),
                first_name=profile.get("first_name"),
                last_name=profile.get("last_name"),
                bio=profile.get("bio"),
                avatar_url=profile.get("avatar_url"),
                date_of_birth=profile.get("date_of_birth"),
                created_at=profile["created_at"],
                updated_at=profile.get("updated_at")
            ))
        
        return ProfileListResponse(
            profiles=profile_responses,
            total=total_count,
            skip=skip,
            limit=limit,
            has_more=skip + len(profiles) < total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )
```

### Advanced Profile Search

```python
@router.get("/search")
async def search_profiles(
    q: str = Query(..., min_length=2, description="Search query"),
    age_min: Optional[int] = Query(None, ge=0, le=120, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=120, description="Maximum age"),
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Advanced profile search with age filtering
    Uses SurrealDB's date functions for age calculation
    """
    
    db = profile_model.db
    
    # Build search conditions
    conditions = [
        "user.is_active = true",
        """(string::lowercase(first_name) CONTAINS string::lowercase($query) 
            OR string::lowercase(last_name) CONTAINS string::lowercase($query)
            OR string::lowercase(bio) CONTAINS string::lowercase($query))"""
    ]
    params = {"query": q}
    
    # Add age filters using SurrealDB date functions
    if age_min is not None:
        conditions.append("date_of_birth <= time::now() - duration::from::years($age_min)")
        params["age_min"] = age_min
    
    if age_max is not None:
        conditions.append("date_of_birth >= time::now() - duration::from::years($age_max)")
        params["age_max"] = age_max
    
    where_clause = " AND ".join(conditions)
    
    try:
        result = await db.query(f"""
            SELECT *,
                   user.username,
                   user.email,
                   math::floor(time::diff(date_of_birth, time::now()) / duration::from::years(1)) AS age,
                   (CASE 
                    WHEN string::lowercase(first_name) CONTAINS string::lowercase($query) THEN 80
                    WHEN string::lowercase(last_name) CONTAINS string::lowercase($query) THEN 80
                    WHEN string::lowercase(bio) CONTAINS string::lowercase($query) THEN 60
                    ELSE 40
                    END) AS relevance_score
            FROM profile 
            WHERE {where_clause}
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT 50
        """, params)
        
        profiles = result[0]["result"] if result and result[0]["result"] else []
        
        return {
            "query": q,
            "filters": {
                "age_min": age_min,
                "age_max": age_max
            },
            "results": profiles,
            "total_found": len(profiles)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
```

## Update Profile Operations

### Update Current User's Profile

```python
@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Update the current user's profile
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    # Check if profile exists
    existing_profile = await profile_model.get_profile_by_user_id(current_user_id)
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile first."
        )
    
    # Prepare update data
    update_data = profile_data.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        updated_profile = await profile_model.update_profile(current_user_id, update_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        profile_id = updated_profile["id"].split(":")[1]
        
        return ProfileResponse(
            id=profile_id,
            user_id=current_user_id,
            first_name=updated_profile.get("first_name"),
            last_name=updated_profile.get("last_name"),
            bio=updated_profile.get("bio"),
            avatar_url=updated_profile.get("avatar_url"),
            date_of_birth=updated_profile.get("date_of_birth"),
            created_at=updated_profile["created_at"],
            updated_at=updated_profile.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )
```

### Update Profile by User ID (Admin)

```python
@router.put("/user/{user_id}", response_model=ProfileResponse)
async def update_profile_by_user_id(
    user_id: str,
    profile_data: ProfileUpdate,
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Update profile by user ID (Admin only)
    """
    
    existing_profile = await profile_model.get_profile_by_user_id(user_id)
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    update_data = profile_data.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        updated_profile = await profile_model.update_profile(user_id, update_data)
        
        profile_id = updated_profile["id"].split(":")[1]
        
        return ProfileResponse(
            id=profile_id,
            user_id=user_id,
            first_name=updated_profile.get("first_name"),
            last_name=updated_profile.get("last_name"),
            bio=updated_profile.get("bio"),
            avatar_url=updated_profile.get("avatar_url"),
            date_of_birth=updated_profile.get("date_of_birth"),
            created_at=updated_profile["created_at"],
            updated_at=updated_profile.get("updated_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )
```

## Avatar Management

### Upload Avatar

```python
@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Upload avatar for current user's profile
    This example shows the structure - actual file storage would need implementation
    """
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    current_user_id = current_user["id"].split(":")[1]
    
    # Check if profile exists
    existing_profile = await profile_model.get_profile_by_user_id(current_user_id)
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile first."
        )
    
    try:
        # In a real implementation, you would:
        # 1. Save file to storage (S3, local filesystem, etc.)
        # 2. Generate URL for the stored file
        # 3. Update profile with the URL
        
        # For this example, we'll simulate a URL
        avatar_url = f"https://example.com/avatars/{current_user_id}/{file.filename}"
        
        # Update profile with avatar URL
        updated_profile = await profile_model.update_profile(current_user_id, {
            "avatar_url": avatar_url
        })
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )

@router.delete("/me/avatar")
async def remove_avatar(
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Remove avatar from current user's profile
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    try:
        updated_profile = await profile_model.update_profile(current_user_id, {
            "avatar_url": None
        })
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": "Avatar removed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove avatar: {str(e)}"
        )
```

## Delete Profile Operations

### Delete Current User's Profile

```python
@router.delete("/me")
async def delete_my_profile(
    current_user: dict = Depends(get_current_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Delete the current user's profile
    """
    
    current_user_id = current_user["id"].split(":")[1]
    
    success = await profile_model.delete_profile(current_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {"message": "Profile deleted successfully"}

@router.delete("/user/{user_id}")
async def delete_profile_by_user_id(
    user_id: str,
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Delete profile by user ID (Admin only)
    """
    
    success = await profile_model.delete_profile(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {"message": "Profile deleted successfully"}
```

## Profile Analytics

### Profile Statistics

```python
@router.get("/stats/overview")
async def get_profile_statistics(
    admin_user: dict = Depends(get_admin_user),
    profile_model: ProfileModel = Depends(get_profile_model)
):
    """
    Get comprehensive profile statistics using SurrealDB aggregation
    """
    
    db = profile_model.db
    
    try:
        result = await db.query("""
            SELECT 
                count() AS total_profiles,
                count(avatar_url IS NOT NULL AND avatar_url != '') AS profiles_with_avatar,
                count(bio IS NOT NULL AND bio != '') AS profiles_with_bio,
                count(date_of_birth IS NOT NULL) AS profiles_with_dob
            FROM profile;
            
            SELECT 
                math::floor(time::diff(date_of_birth, time::now()) / duration::from::years(1)) AS age_group,
                count() AS count
            FROM profile 
            WHERE date_of_birth IS NOT NULL
            GROUP BY age_group
            ORDER BY age_group;
        """)
        
        general_stats = result[0]["result"][0] if result and result[0]["result"] else {}
        age_distribution = result[1]["result"] if result and len(result) > 1 and result[1]["result"] else []
        
        return {
            "general_statistics": general_stats,
            "age_distribution": age_distribution,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
```

## Pydantic Schemas

### Profile Schemas

```python
# app/schemas/profile.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class ProfileCreate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    @property
    def full_name(self) -> Optional[str]:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name

class ProfileListResponse(BaseModel):
    profiles: List[ProfileResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
```

This profile management system demonstrates SurrealDB's relationship capabilities, allowing profiles to be seamlessly linked to users while providing comprehensive CRUD operations, search functionality, and analytics through SurrealDB's powerful query language.