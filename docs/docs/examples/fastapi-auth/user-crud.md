---
sidebar_position: 3
---

# User CRUD Operations

This section demonstrates complete user management operations using FastAPI and SurrealDB, including advanced querying, filtering, and bulk operations.

## User Router Setup

### Router Configuration with Dependencies

```python
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from surrealdb import Surreal
from app.database import get_database
from app.auth.routes import get_current_user, get_admin_user
from app.models.user import UserModel
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse

router = APIRouter(prefix="/users", tags=["users"])

async def get_user_service(db: Surreal = Depends(get_database)) -> UserService:
    """Dependency to get user service"""
    return UserService(db)
```

## Create User Operations

### Admin User Creation

```python
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user (Admin only)
    
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Password (will be hashed)
    - **is_admin**: Admin privileges (optional, default: false)
    """
    
    try:
        # Check if user already exists using SurrealDB unique constraints
        existing_user = await user_service.user_model.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await user_service.user_model.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        import bcrypt
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user in SurrealDB
        new_user = await user_service.user_model.create_user(
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash
        )
        
        if user_data.is_admin:
            user_id = new_user["id"].split(":")[1]
            await user_service.user_model.update_user(user_id, {"is_admin": True})
            new_user["is_admin"] = True
        
        user_id = new_user["id"].split(":")[1]
        
        return UserResponse(
            id=user_id,
            email=new_user["email"],
            username=new_user["username"],
            is_active=new_user["is_active"],
            is_admin=new_user["is_admin"],
            created_at=new_user["created_at"],
            updated_at=new_user.get("updated_at")
        )
        
    except Exception as e:
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
```

### Bulk User Creation

```python
@router.post("/bulk", response_model=List[UserResponse])
async def create_users_bulk(
    users_data: List[UserCreate],
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create multiple users in bulk (Admin only)
    Uses SurrealDB batch operations for efficiency
    """
    
    if len(users_data) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 users can be created at once"
        )
    
    created_users = []
    failed_users = []
    
    # Prepare batch data for SurrealDB
    batch_data = []
    for user_data in users_data:
        import bcrypt
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        batch_data.append({
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": password_hash,
            "is_admin": user_data.is_admin or False,
            "is_active": True
        })
    
    # Execute batch creation using SurrealDB
    db = user_service.db
    try:
        # Use SurrealDB's batch insert capability
        result = await db.query("""
            FOR $user IN $users {
                CREATE user CONTENT $user
            }
        """, {"users": batch_data})
        
        # Process results
        if result and result[0]["result"]:
            for user_record in result[0]["result"]:
                if user_record:
                    user_id = user_record["id"].split(":")[1]
                    created_users.append(UserResponse(
                        id=user_id,
                        email=user_record["email"],
                        username=user_record["username"],
                        is_active=user_record["is_active"],
                        is_admin=user_record["is_admin"],
                        created_at=user_record["created_at"]
                    ))
        
        return created_users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk user creation failed: {str(e)}"
        )
```

## Read User Operations

### Get Single User

```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID
    Users can only access their own data unless they are admin
    """
    
    # Check if user is accessing their own data or is admin
    current_user_id = current_user["id"].split(":")[1]
    if user_id != current_user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = await user_service.user_model.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_id_clean = user["id"].split(":")[1]
    
    return UserResponse(
        id=user_id_clean,
        email=user["email"],
        username=user["username"],
        is_active=user["is_active"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
        updated_at=user.get("updated_at")
    )
```

### Get User with Profile

```python
@router.get("/{user_id}/profile", response_model=dict)
async def get_user_with_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user with profile information using SurrealDB relationships
    """
    
    # Check permissions
    current_user_id = current_user["id"].split(":")[1]
    if user_id != current_user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user_with_profile = await user_service.get_user_with_profile(user_id)
    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_with_profile
```

### List Users with Advanced Filtering

```python
@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search term for username or email"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    created_after: Optional[str] = Query(None, description="Filter users created after date (ISO format)"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    List users with advanced filtering and pagination
    Uses SurrealDB's powerful query capabilities
    """
    
    # Build dynamic SurrealDB query
    conditions = []
    params = {"skip": skip, "limit": limit}
    
    if is_active is not None:
        conditions.append("is_active = $is_active")
        params["is_active"] = is_active
    
    if search:
        conditions.append("""
            (string::lowercase(username) CONTAINS string::lowercase($search) 
             OR string::lowercase(email) CONTAINS string::lowercase($search))
        """)
        params["search"] = search
    
    if is_admin is not None:
        conditions.append("is_admin = $is_admin_filter")
        params["is_admin_filter"] = is_admin
    
    if created_after:
        conditions.append("created_at > $created_after")
        params["created_after"] = created_after
    
    where_clause = " AND ".join(conditions) if conditions else "true"
    order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
    
    # Execute query with count
    db = user_service.db
    result = await db.query(f"""
        SELECT * FROM user 
        WHERE {where_clause}
        {order_clause}
        LIMIT $limit START $skip;
        
        SELECT count() AS total FROM user WHERE {where_clause};
    """, params)
    
    users = result[0]["result"] if result and result[0]["result"] else []
    total_count = result[1]["result"][0]["total"] if result and len(result) > 1 and result[1]["result"] else 0
    
    # Convert to response format
    user_responses = []
    for user in users:
        user_id = user["id"].split(":")[1]
        user_responses.append(UserResponse(
            id=user_id,
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            is_admin=user["is_admin"],
            created_at=user["created_at"],
            updated_at=user.get("updated_at")
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total_count,
        skip=skip,
        limit=limit,
        has_more=skip + len(users) < total_count
    )
```

### Search Users with Full-Text Search

```python
@router.get("/search/advanced")
async def search_users_advanced(
    q: str = Query(..., min_length=2, description="Search query"),
    fields: List[str] = Query(["username", "email"], description="Fields to search in"),
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Advanced user search using SurrealDB's string functions
    Supports searching across multiple fields with relevance scoring
    """
    
    # Build search conditions for each field
    search_conditions = []
    for field in fields:
        if field in ["username", "email"]:
            search_conditions.append(f"string::lowercase({field}) CONTAINS string::lowercase($query)")
    
    if not search_conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid search fields"
        )
    
    search_clause = " OR ".join(search_conditions)
    
    db = user_service.db
    result = await db.query(f"""
        SELECT *,
               (CASE 
                WHEN string::lowercase(username) = string::lowercase($query) THEN 100
                WHEN string::lowercase(email) = string::lowercase($query) THEN 100
                WHEN string::starts_with(string::lowercase(username), string::lowercase($query)) THEN 80
                WHEN string::starts_with(string::lowercase(email), string::lowercase($query)) THEN 80
                ELSE 50
                END) AS relevance_score
        FROM user 
        WHERE is_active = true AND ({search_clause})
        ORDER BY relevance_score DESC, created_at DESC
        LIMIT 50
    """, {"query": q})
    
    users = result[0]["result"] if result and result[0]["result"] else []
    
    return {
        "query": q,
        "results": users,
        "total_found": len(users)
    }
```

## Update User Operations

### Update User Profile

```python
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user information
    Users can update their own data, admins can update any user
    """
    
    # Check permissions
    current_user_id = current_user["id"].split(":")[1]
    if user_id != current_user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get existing user
    existing_user = await user_service.user_model.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = {}
    
    if user_data.email and user_data.email != existing_user["email"]:
        # Check if new email is already taken
        email_exists = await user_service.user_model.get_user_by_email(user_data.email)
        if email_exists and email_exists["id"] != existing_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_data["email"] = user_data.email
    
    if user_data.username and user_data.username != existing_user["username"]:
        # Check if new username is already taken
        username_exists = await user_service.user_model.get_user_by_username(user_data.username)
        if username_exists and username_exists["id"] != existing_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_data["username"] = user_data.username
    
    # Only admins can change admin status and active status
    if current_user.get("is_admin", False):
        if user_data.is_admin is not None:
            update_data["is_admin"] = user_data.is_admin
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
    
    # Update password if provided
    if user_data.password:
        import bcrypt
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_data["password_hash"] = password_hash
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Update user in SurrealDB
    updated_user = await user_service.user_model.update_user(user_id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    user_id_clean = updated_user["id"].split(":")[1]
    
    return UserResponse(
        id=user_id_clean,
        email=updated_user["email"],
        username=updated_user["username"],
        is_active=updated_user["is_active"],
        is_admin=updated_user["is_admin"],
        created_at=updated_user["created_at"],
        updated_at=updated_user.get("updated_at")
    )
```

### Bulk Update Users

```python
@router.patch("/bulk")
async def bulk_update_users(
    user_ids: List[str],
    update_data: dict,
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Bulk update multiple users (Admin only)
    Uses SurrealDB's batch update capabilities
    """
    
    if len(user_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 users can be updated at once"
        )
    
    # Validate update fields
    allowed_fields = ["is_active", "is_admin"]
    filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Add timestamp
    filtered_update["updated_at"] = datetime.utcnow().isoformat()
    
    # Execute bulk update using SurrealDB
    db = user_service.db
    user_records = [f"user:{uid}" for uid in user_ids]
    
    try:
        result = await db.query("""
            FOR $user_id IN $user_ids {
                UPDATE $user_id MERGE $update_data
            }
        """, {
            "user_ids": user_records,
            "update_data": filtered_update
        })
        
        updated_count = len(result[0]["result"]) if result and result[0]["result"] else 0
        
        return {
            "message": f"Successfully updated {updated_count} users",
            "updated_count": updated_count,
            "requested_count": len(user_ids)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )
```

## Delete User Operations

### Soft Delete User

```python
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Soft delete user (set is_active to false)
    Users can delete their own account, admins can delete any user
    """
    
    # Check permissions
    current_user_id = current_user["id"].split(":")[1]
    if user_id != current_user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prevent self-deletion for admins if they're the only admin
    if current_user.get("is_admin", False) and user_id == current_user_id:
        db = user_service.db
        admin_count = await db.query("SELECT count() AS total FROM user WHERE is_admin = true AND is_active = true")
        if admin_count and admin_count[0]["result"][0]["total"] <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user"
            )
    
    success = await user_service.user_model.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User successfully deleted"}
```

### Hard Delete User (Admin Only)

```python
@router.delete("/{user_id}/permanent")
async def permanently_delete_user(
    user_id: str,
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Permanently delete user and all related data (Admin only)
    This will cascade delete profiles, sessions, and other related records
    """
    
    db = user_service.db
    
    try:
        # Delete in order: sessions, profiles, then user
        await db.query("""
            DELETE FROM session WHERE user = $user_record;
            DELETE FROM profile WHERE user = $user_record;
            DELETE FROM $user_record;
        """, {"user_record": f"user:{user_id}"})
        
        return {"message": "User permanently deleted with all related data"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
```

## User Statistics and Analytics

### User Statistics Endpoint

```python
@router.get("/stats/overview")
async def get_user_statistics(
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get comprehensive user statistics using SurrealDB aggregation
    """
    
    stats = await user_service.get_user_statistics()
    
    return {
        "user_stats": stats["users"],
        "profile_stats": stats["profiles"],
        "session_stats": stats["sessions"],
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/stats/activity")
async def get_user_activity_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    admin_user: dict = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user activity statistics over time
    """
    
    db = user_service.db
    result = await db.query("""
        SELECT 
            time::format(created_at, '%Y-%m-%d') AS date,
            count() AS registrations
        FROM user 
        WHERE created_at > time::now() - duration::from::days($days)
        GROUP BY date
        ORDER BY date DESC
    """, {"days": days})
    
    activity_data = result[0]["result"] if result and result[0]["result"] else []
    
    return {
        "period_days": days,
        "daily_registrations": activity_data,
        "total_in_period": sum(day["registrations"] for day in activity_data)
    }
```

## Pydantic Schemas

### User Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: str
    updated_at: Optional[str] = None

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
```

This comprehensive user CRUD system leverages SurrealDB's powerful querying capabilities, relationship handling, and data validation features while providing a clean FastAPI interface for user management operations.