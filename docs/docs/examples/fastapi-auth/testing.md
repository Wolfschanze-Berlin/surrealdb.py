---
sidebar_position: 7
---

# Testing SurrealDB Operations

This section demonstrates comprehensive testing strategies for FastAPI applications using SurrealDB, including unit tests, integration tests, and end-to-end testing with real-time features.

## Test Configuration and Setup

### Test Database Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from surrealdb import Surreal
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
from app.database import db_manager
from app.config import settings

# Test database settings
TEST_DB_CONFIG = {
    "url": "memory://",  # Use in-memory database for tests
    "namespace": "test_namespace",
    "database": "test_database",
    "username": "root",
    "password": "root"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[Surreal, None]:
    """Create a test database connection for each test function."""
    db = Surreal()
    await db.connect(TEST_DB_CONFIG["url"])
    await db.signin({
        "user": TEST_DB_CONFIG["username"],
        "pass": TEST_DB_CONFIG["password"]
    })
    await db.use(TEST_DB_CONFIG["namespace"], TEST_DB_CONFIG["database"])
    
    # Initialize test schema
    await initialize_test_schema(db)
    
    yield db
    
    # Cleanup
    await db.close()

async def initialize_test_schema(db: Surreal):
    """Initialize database schema for testing"""
    await db.query("""
        -- Define user table
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
        
        -- Define profile table
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
        
        -- Define session table
        DEFINE TABLE session SCHEMAFULL;
        DEFINE FIELD user ON TABLE session TYPE record(user);
        DEFINE FIELD token_hash ON TABLE session TYPE string;
        DEFINE FIELD expires_at ON TABLE session TYPE datetime;
        DEFINE FIELD created_at ON TABLE session TYPE datetime DEFAULT time::now();
        DEFINE INDEX token_hash_idx ON TABLE session COLUMNS token_hash;
        DEFINE INDEX user_sessions ON TABLE session COLUMNS user;
    """)

@pytest.fixture
async def test_client(test_db: Surreal) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override"""
    
    async def override_get_database():
        return test_db
    
    app.dependency_overrides[db_manager.connect] = override_get_database
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(test_db: Surreal) -> dict:
    """Create a test user"""
    import bcrypt
    
    password_hash = bcrypt.hashpw("testpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    result = await test_db.create("user", {
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": password_hash,
        "is_active": True,
        "is_admin": False
    })
    
    return result[0] if result else None

@pytest.fixture
async def test_admin_user(test_db: Surreal) -> dict:
    """Create a test admin user"""
    import bcrypt
    
    password_hash = bcrypt.hashpw("adminpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    result = await test_db.create("user", {
        "email": "admin@example.com",
        "username": "adminuser",
        "password_hash": password_hash,
        "is_active": True,
        "is_admin": True
    })
    
    return result[0] if result else None

@pytest.fixture
async def auth_headers(test_client: AsyncClient, test_user: dict) -> dict:
    """Get authentication headers for test user"""
    
    login_data = {
        "email_or_username": "test@example.com",
        "password": "testpassword123"
    }
    
    response = await test_client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_auth_headers(test_client: AsyncClient, test_admin_user: dict) -> dict:
    """Get authentication headers for admin user"""
    
    login_data = {
        "email_or_username": "admin@example.com",
        "password": "adminpassword123"
    }
    
    response = await test_client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Authentication Tests

### User Registration and Login Tests

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

class TestAuthentication:
    
    async def test_user_registration_success(self, test_client: AsyncClient):
        """Test successful user registration"""
        
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
        
        response = await test_client.post("/auth/register", json=registration_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "access_token" in data
    
    async def test_user_registration_duplicate_email(self, test_client: AsyncClient, test_user: dict):
        """Test registration with duplicate email"""
        
        registration_data = {
            "email": "test@example.com",  # Same as test_user
            "username": "differentuser",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
        
        response = await test_client.post("/auth/register", json=registration_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_user_registration_password_mismatch(self, test_client: AsyncClient):
        """Test registration with password mismatch"""
        
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "confirm_password": "differentpassword123"
        }
        
        response = await test_client.post("/auth/register", json=registration_data)
        
        assert response.status_code == 400
        assert "do not match" in response.json()["detail"].lower()
    
    async def test_user_login_success(self, test_client: AsyncClient, test_user: dict):
        """Test successful user login"""
        
        login_data = {
            "email_or_username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert data["user"]["email"] == "test@example.com"
    
    async def test_user_login_invalid_credentials(self, test_client: AsyncClient, test_user: dict):
        """Test login with invalid credentials"""
        
        login_data = {
            "email_or_username": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = await test_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    async def test_get_current_user(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting current user information"""
        
        response = await test_client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    async def test_logout_success(self, test_client: AsyncClient, auth_headers: dict):
        """Test successful logout"""
        
        response = await test_client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully logged out" in response.json()["message"].lower()
    
    async def test_token_refresh(self, test_client: AsyncClient, auth_headers: dict):
        """Test token refresh"""
        
        response = await test_client.post("/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
```

## User CRUD Tests

### User Management Tests

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient

class TestUserCRUD:
    
    async def test_create_user_admin_only(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test user creation by admin"""
        
        user_data = {
            "email": "created@example.com",
            "username": "createduser",
            "password": "securepassword123",
            "is_admin": False
        }
        
        response = await test_client.post("/users/", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "created@example.com"
        assert data["username"] == "createduser"
        assert data["is_admin"] is False
    
    async def test_create_user_non_admin_forbidden(self, test_client: AsyncClient, auth_headers: dict):
        """Test user creation by non-admin user (should fail)"""
        
        user_data = {
            "email": "created@example.com",
            "username": "createduser",
            "password": "securepassword123"
        }
        
        response = await test_client.post("/users/", json=user_data, headers=auth_headers)
        
        assert response.status_code == 403
    
    async def test_get_user_self(self, test_client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test user getting their own information"""
        
        user_id = test_user["id"].split(":")[1]
        response = await test_client.get(f"/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    async def test_get_user_other_forbidden(self, test_client: AsyncClient, auth_headers: dict, test_admin_user: dict):
        """Test user getting another user's information (should fail)"""
        
        admin_user_id = test_admin_user["id"].split(":")[1]
        response = await test_client.get(f"/users/{admin_user_id}", headers=auth_headers)
        
        assert response.status_code == 403
    
    async def test_list_users_admin_only(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test listing users (admin only)"""
        
        response = await test_client.get("/users/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
    
    async def test_update_user_self(self, test_client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test user updating their own information"""
        
        user_id = test_user["id"].split(":")[1]
        update_data = {
            "username": "updatedusername"
        }
        
        response = await test_client.put(f"/users/{user_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedusername"
    
    async def test_search_users_admin(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test user search functionality"""
        
        response = await test_client.get("/users/search/advanced?q=test", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_found" in data
    
    async def test_delete_user_soft_delete(self, test_client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test soft delete of user"""
        
        user_id = test_user["id"].split(":")[1]
        response = await test_client.delete(f"/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"].lower()
```

## Profile Tests

### Profile Management Tests

```python
# tests/test_profiles.py
import pytest
from httpx import AsyncClient
from datetime import date

class TestProfileCRUD:
    
    async def test_create_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test profile creation"""
        
        profile_data = {
            "first_name": "Test",
            "last_name": "User",
            "bio": "This is a test user profile",
            "date_of_birth": "1990-01-01"
        }
        
        response = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["bio"] == "This is a test user profile"
    
    async def test_create_duplicate_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test creating duplicate profile (should fail)"""
        
        # Create first profile
        profile_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        response1 = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create second profile (should fail)
        response2 = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    async def test_get_my_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting current user's profile"""
        
        # Create profile first
        profile_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        create_response = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Get profile
        response = await test_client.get("/profiles/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
    
    async def test_update_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test profile update"""
        
        # Create profile first
        profile_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        create_response = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Update profile
        update_data = {
            "bio": "Updated bio information"
        }
        
        response = await test_client.put("/profiles/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio information"
    
    async def test_list_profiles_admin(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test listing all profiles (admin only)"""
        
        response = await test_client.get("/profiles/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert "total" in data
    
    async def test_search_profiles_admin(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test profile search"""
        
        response = await test_client.get("/profiles/search?q=test", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_found" in data
    
    async def test_delete_profile(self, test_client: AsyncClient, auth_headers: dict):
        """Test profile deletion"""
        
        # Create profile first
        profile_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        create_response = await test_client.post("/profiles/", json=profile_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Delete profile
        response = await test_client.delete("/profiles/me", headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"].lower()
```

## Database Operation Tests

### SurrealDB-Specific Tests

```python
# tests/test_database_operations.py
import pytest
from surrealdb import Surreal
from app.models.user import UserModel
from app.models.profile import ProfileModel
from app.services.user_service import UserService

class TestDatabaseOperations:
    
    async def test_user_model_create(self, test_db: Surreal):
        """Test user model creation"""
        
        user_model = UserModel(test_db)
        
        user_data = {
            "email": "model@example.com",
            "username": "modeluser",
            "password_hash": "hashed_password"
        }
        
        user = await user_model.create_user(**user_data)
        
        assert user is not None
        assert user["email"] == "model@example.com"
        assert user["username"] == "modeluser"
        assert user["is_active"] is True
    
    async def test_user_model_get_by_email(self, test_db: Surreal):
        """Test getting user by email"""
        
        user_model = UserModel(test_db)
        
        # Create user first
        await user_model.create_user(
            email="findme@example.com",
            username="findmeuser",
            password_hash="hashed_password"
        )
        
        # Find user
        found_user = await user_model.get_user_by_email("findme@example.com")
        
        assert found_user is not None
        assert found_user["email"] == "findme@example.com"
        assert found_user["username"] == "findmeuser"
    
    async def test_user_model_update(self, test_db: Surreal):
        """Test user model update"""
        
        user_model = UserModel(test_db)
        
        # Create user
        user = await user_model.create_user(
            email="update@example.com",
            username="updateuser",
            password_hash="hashed_password"
        )
        
        user_id = user["id"].split(":")[1]
        
        # Update user
        updated_user = await user_model.update_user(user_id, {
            "username": "updatedusername"
        })
        
        assert updated_user is not None
        assert updated_user["username"] == "updatedusername"
    
    async def test_profile_model_with_relationship(self, test_db: Surreal):
        """Test profile model with user relationship"""
        
        user_model = UserModel(test_db)
        profile_model = ProfileModel(test_db)
        
        # Create user first
        user = await user_model.create_user(
            email="profile@example.com",
            username="profileuser",
            password_hash="hashed_password"
        )
        
        user_id = user["id"].split(":")[1]
        
        # Create profile
        profile_data = {
            "first_name": "Profile",
            "last_name": "User",
            "bio": "Test profile"
        }
        
        profile = await profile_model.create_profile(user_id, profile_data)
        
        assert profile is not None
        assert profile["first_name"] == "Profile"
        assert profile["last_name"] == "User"
        
        # Test getting profile with user data
        profile_with_user = await profile_model.get_profile_by_user_id(user_id)
        
        assert profile_with_user is not None
        assert "user" in profile_with_user
    
    async def test_complex_query_operations(self, test_db: Surreal):
        """Test complex SurrealDB queries"""
        
        user_service = UserService(test_db)
        
        # Create multiple users
        users_data = [
            {"email": "user1@example.com", "username": "user1", "password_hash": "hash1"},
            {"email": "user2@example.com", "username": "user2", "password_hash": "hash2"},
            {"email": "admin@example.com", "username": "admin", "password_hash": "hash3", "is_admin": True}
        ]
        
        for user_data in users_data:
            await user_service.user_model.create_user(**user_data)
        
        # Test search functionality
        search_results = await user_service.user_model.search_users("user")
        
        assert len(search_results) >= 2
        assert any(user["username"] == "user1" for user in search_results)
        assert any(user["username"] == "user2" for user in search_results)
    
    async def test_transaction_operations(self, test_db: Surreal):
        """Test transaction handling"""
        
        try:
            # Start transaction
            await test_db.query("BEGIN TRANSACTION")
            
            # Create user within transaction
            result = await test_db.create("user", {
                "email": "transaction@example.com",
                "username": "transactionuser",
                "password_hash": "hashed_password",
                "is_active": True,
                "is_admin": False
            })
            
            assert result is not None
            
            # Commit transaction
            await test_db.query("COMMIT TRANSACTION")
            
            # Verify user exists
            user = await test_db.query("SELECT * FROM user WHERE email = 'transaction@example.com'")
            assert len(user[0]["result"]) == 1
            
        except Exception as e:
            # Rollback on error
            await test_db.query("CANCEL TRANSACTION")
            raise e
    
    async def test_live_query_setup(self, test_db: Surreal):
        """Test live query functionality"""
        
        changes_received = []
        
        def handle_change(change):
            changes_received.append(change)
        
        # Set up live query
        live_id = await test_db.live("user", callback=handle_change)
        
        assert live_id is not None
        
        # Create a user to trigger the live query
        await test_db.create("user", {
            "email": "live@example.com",
            "username": "liveuser",
            "password_hash": "hashed_password"
        })
        
        # Give some time for the live query to process
        import asyncio
        await asyncio.sleep(0.1)
        
        # Kill the live query
        await test_db.kill(live_id)
        
        # Note: In a real test, you might need to wait longer or use proper
        # synchronization to ensure the live query callback is triggered
```

## Integration Tests

### End-to-End API Tests

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient

class TestIntegration:
    
    async def test_complete_user_workflow(self, test_client: AsyncClient):
        """Test complete user registration, login, profile creation workflow"""
        
        # 1. Register user
        registration_data = {
            "email": "workflow@example.com",
            "username": "workflowuser",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
        
        register_response = await test_client.post("/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get user info
        user_response = await test_client.get("/auth/me", headers=headers)
        assert user_response.status_code == 200
        assert user_response.json()["email"] == "workflow@example.com"
        
        # 3. Create profile
        profile_data = {
            "first_name": "Workflow",
            "last_name": "User",
            "bio": "Integration test user"
        }
        
        profile_response = await test_client.post("/profiles/", json=profile_data, headers=headers)
        assert profile_response.status_code == 201
        
        # 4. Update profile
        update_data = {
            "bio": "Updated integration test user"
        }
        
        update_response = await test_client.put("/profiles/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        assert update_response.json()["bio"] == "Updated integration test user"
        
        # 5. Logout
        logout_response = await test_client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
    
    async def test_admin_user_management_workflow(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test admin user management workflow"""
        
        # 1. Create user as admin
        user_data = {
            "email": "managed@example.com",
            "username": "manageduser",
            "password": "securepassword123"
        }
        
        create_response = await test_client.post("/users/", json=user_data, headers=admin_auth_headers)
        assert create_response.status_code == 201
        
        user_id = create_response.json()["id"]
        
        # 2. List users
        list_response = await test_client.get("/users/", headers=admin_auth_headers)
        assert list_response.status_code == 200
        assert any(user["id"] == user_id for user in list_response.json()["users"])
        
        # 3. Update user
        update_data = {
            "is_admin": True
        }
        
        update_response = await test_client.put(f"/users/{user_id}", json=update_data, headers=admin_auth_headers)
        assert update_response.status_code == 200
        assert update_response.json()["is_admin"] is True
        
        # 4. Search users
        search_response = await test_client.get("/users/search/advanced?q=managed", headers=admin_auth_headers)
        assert search_response.status_code == 200
        assert len(search_response.json()["results"]) > 0
        
        # 5. Get user statistics
        stats_response = await test_client.get("/users/stats/overview", headers=admin_auth_headers)
        assert stats_response.status_code == 200
        assert "user_stats" in stats_response.json()
```

## Performance Tests

### Load Testing with SurrealDB

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from httpx import AsyncClient

class TestPerformance:
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, test_client: AsyncClient, admin_auth_headers: dict):
        """Test concurrent user creation performance"""
        
        async def create_user(index: int):
            user_data = {
                "email": f"perf{index}@example.com",
                "username": f"perfuser{index}",
                "password": "securepassword123"
            }
            
            start_time = time.time()
            response = await test_client.post("/users/", json=user_data, headers=admin_auth_headers)
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "duration": end_time - start_time,
                "index": index
            }
        
        # Create 10 users concurrently
        tasks = [create_user(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all users were created successfully
        successful_creations = [r for r in results if r["status_code"] == 201]
        assert len(successful_creations) == 10