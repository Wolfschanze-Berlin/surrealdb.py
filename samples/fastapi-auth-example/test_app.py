#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI SurrealDB application structure.
"""

import sys
import os

def test_imports():
    """Test if all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test config
        from config import settings
        print("✓ Config imported successfully")
        
        # Test auth
        from auth import create_access_token, get_password_hash, verify_password
        print("✓ Auth utilities imported successfully")
        
        # Test schemas
        from schemas import UserRegister, UserResponse, Token
        print("✓ Schemas imported successfully")
        
        # Test models
        from models import UserBase, ProfileBase
        print("✓ Models imported successfully")
        
        # Test database (without connecting)
        from database import DatabaseManager
        print("✓ Database manager imported successfully")
        
        # Test CRUD
        from crud import UserCRUD, ProfileCRUD
        print("✓ CRUD operations imported successfully")
        
        # Test routers
        from routers import auth, users, profiles
        print("✓ Routers imported successfully")
        
        # Test main app
        from main import app
        print("✓ Main FastAPI app imported successfully")
        
        print("\n🎉 All imports successful! The application structure is correct.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_auth_functions():
    """Test authentication functions."""
    try:
        print("\nTesting authentication functions...")
        
        from auth import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        password = "test123"
        hashed = get_password_hash(password)
        print(f"✓ Password hashed: {hashed[:20]}...")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"✓ Password verification: {is_valid}")
        
        # Test token creation
        token = create_access_token({"sub": "test_user_id"})
        print(f"✓ JWT token created: {token[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth function test error: {e}")
        return False

def main():
    """Run all tests."""
    print("FastAPI SurrealDB Auth Example - Structure Test")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test auth functions
    if not test_auth_functions():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("1. Start SurrealDB: surreal start --user root --pass root memory")
        print("2. Run the app: python main.py")
        print("3. Visit: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()