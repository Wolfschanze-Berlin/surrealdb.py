---
sidebar_position: 3
---

# JWT Authentication

Learn how to use JSON Web Tokens (JWT) for stateless authentication with SurrealDB. This guide covers token generation, validation, and integration patterns.

## Overview

JWT authentication provides stateless, secure authentication that's perfect for:

- **Microservices** - Share authentication across services
- **API Authentication** - Secure REST/GraphQL APIs
- **Mobile Apps** - Offline-capable authentication
- **Single Page Applications** - Client-side token management

## Basic JWT Authentication

### Using Tokens from Signin

The simplest way to get a JWT token is from a successful signin operation.

```python
from surrealdb import Surreal

def get_jwt_token():
    """Get JWT token from signin"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Sign in to get a token
        token = db.signin({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "john.doe@example.com",
            "password": "SecurePassword123!"
        })
        
        print(f"✅ JWT token obtained: {token[:50]}...")
        return token

def authenticate_with_jwt(token):
    """Authenticate using existing JWT token"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate using JWT token
            db.authenticate(token)
            
            print("✅ JWT authentication successful")
            
            # Select namespace and database
            db.use("mycompany", "production")
            
            # Verify authentication
            user_info = db.info()
            print(f"JWT authenticated user: {user_info}")
            
            # Perform operations
            user_data = db.select("user")
            print(f"Accessed {len(user_data)} user records")
            
            return user_info
            
        except Exception as e:
            print(f"❌ JWT authentication failed: {e}")
            raise

# Example usage
token = get_jwt_token()
user_info = authenticate_with_jwt(token)
```

### Asynchronous JWT Authentication

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_jwt_authentication():
    """Async JWT authentication example"""
    
    # Get token from signin
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        token = await db.signin({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "john.doe@example.com",
            "password": "SecurePassword123!"
        })
        
        print(f"✅ Obtained JWT token: {token[:50]}...")
    
    # Use JWT token for authentication
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate using JWT token
            await db.authenticate(token)
            
            print("✅ Async JWT authentication successful")
            
            # Select namespace and database
            await db.use("mycompany", "production")
            
            # Verify authentication
            user_info = await db.info()
            print(f"JWT authenticated user: {user_info}")
            
            # Perform operations
            user_data = await db.select("user")
            print(f"Accessed {len(user_data)} user records")
            
            return token, user_info
            
        except Exception as e:
            print(f"❌ Async JWT authentication failed: {e}")
            raise

# Run async example
asyncio.run(async_jwt_authentication())
```

## JWT Token Management

### Token Storage and Retrieval

```python
import json
import os
from datetime import datetime, timedelta
from surrealdb import Surreal

class JWTTokenManager:
    """Manage JWT tokens with storage and validation"""
    
    def __init__(self, storage_file="jwt_tokens.json"):
        self.storage_file = storage_file
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load tokens: {e}")
        return {}
    
    def _save_tokens(self):
        """Save tokens to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")
    
    def store_token(self, user_id, token, expires_in_hours=24):
        """Store a JWT token with expiration"""
        expiry = datetime.now() + timedelta(hours=expires_in_hours)
        
        self.tokens[user_id] = {
            "token": token,
            "expires_at": expiry.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        self._save_tokens()
        print(f"✅ Token stored for user: {user_id}")
    
    def get_token(self, user_id):
        """Get valid token for user"""
        if user_id not in self.tokens:
            return None
        
        token_data = self.tokens[user_id]
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        
        if datetime.now() > expires_at:
            print(f"⚠️ Token expired for user: {user_id}")
            del self.tokens[user_id]
            self._save_tokens()
            return None
        
        return token_data["token"]
    
    def refresh_token(self, user_id, credentials, db_url="ws://localhost:8000/rpc"):
        """Refresh token for user"""
        try:
            with Surreal(db_url) as db:
                # Get new token
                new_token = db.signin(credentials)
                
                # Store new token
                self.store_token(user_id, new_token)
                
                print(f"✅ Token refreshed for user: {user_id}")
                return new_token
                
        except Exception as e:
            print(f"❌ Token refresh failed for {user_id}: {e}")
            raise
    
    def invalidate_token(self, user_id):
        """Invalidate stored token"""
        if user_id in self.tokens:
            del self.tokens[user_id]
            self._save_tokens()
            print(f"✅ Token invalidated for user: {user_id}")

# Example usage
def token_management_example():
    """Example of JWT token management"""
    
    token_manager = JWTTokenManager()
    
    # User credentials
    user_creds = {
        "namespace": "mycompany",
        "database": "production",
        "scope": "user",
        "email": "john.doe@example.com",
        "password": "SecurePassword123!"
    }
    
    user_id = "john.doe@example.com"
    
    # Try to get existing token
    existing_token = token_manager.get_token(user_id)
    
    if existing_token:
        print(f"✅ Using existing token for {user_id}")
        token = existing_token
    else:
        print(f"🔄 Getting new token for {user_id}")
        token = token_manager.refresh_token(user_id, user_creds)
    
    # Use token for authentication
    with Surreal("ws://localhost:8000/rpc") as db:
        db.authenticate(token)
        db.use("mycompany", "production")
        
        user_info = db.info()
        print(f"Authenticated as: {user_info['email']}")
    
    return token_manager

# Run example
token_manager = token_management_example()
```

## External JWT Integration

### Validating External JWT Tokens

```python
import jwt
import requests
from datetime import datetime, timedelta
from surrealdb import Surreal

class ExternalJWTValidator:
    """Validate and integrate external JWT tokens"""
    
    def __init__(self, secret_key, algorithm="HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def validate_external_jwt(self, token):
        """Validate external JWT token"""
        try:
            # Decode and validate token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            print(f"✅ External JWT valid for: {payload.get('email', 'unknown')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print("❌ External JWT token expired")
            raise
        except jwt.InvalidTokenError as e:
            print(f"❌ External JWT token invalid: {e}")
            raise
    
    def create_surrealdb_user(self, jwt_payload, db_url="ws://localhost:8000/rpc"):
        """Create or update user in SurrealDB from JWT payload"""
        
        with Surreal(db_url) as db:
            # Authenticate as admin to manage users
            db.signin({"username": "root", "password": "root"})
            db.use("mycompany", "production")
            
            # Extract user data from JWT
            user_data = {
                "email": jwt_payload.get("email"),
                "name": jwt_payload.get("name"),
                "external_id": jwt_payload.get("sub"),
                "provider": jwt_payload.get("iss", "external"),
                "roles": jwt_payload.get("roles", ["user"]),
                "updated_at": datetime.now().isoformat()
            }
            
            # Check if user exists
            existing_user = db.query(
                "SELECT * FROM user WHERE email = $email",
                {"email": user_data["email"]}
            )
            
            if existing_user:
                # Update existing user
                user_id = existing_user[0]["id"]
                updated_user = db.merge(user_id, user_data)
                print(f"✅ Updated user: {updated_user[0]['email']}")
                return updated_user[0]
            else:
                # Create new user
                new_user = db.create("user", user_data)
                print(f"✅ Created user: {new_user[0]['email']}")
                return new_user[0]
    
    def get_surrealdb_token(self, user, db_url="ws://localhost:8000/rpc"):
        """Get SurrealDB token for external user"""
        
        with Surreal(db_url) as db:
            db.use("mycompany", "production")
            
            try:
                # Try scope-based authentication
                token = db.signin({
                    "namespace": "mycompany",
                    "database": "production",
                    "scope": "user",
                    "email": user["email"],
                    "external_auth": True
                })
                
                print("✅ SurrealDB token obtained via scope")
                return token
                
            except Exception as e:
                print(f"⚠️ Scope auth failed, using admin token: {e}")
                
                # Fallback: use admin authentication
                admin_token = db.signin({"username": "root", "password": "root"})
                return admin_token

def external_jwt_example():
    """Example of external JWT integration"""
    
    # Create external JWT token (simulated)
    external_payload = {
        "sub": "external_user_123",
        "email": "external@example.com",
        "name": "External User",
        "iss": "external_provider",
        "roles": ["user", "premium"],
        "exp": datetime.now() + timedelta(hours=1)
    }
    
    secret_key = "your_external_jwt_secret"
    external_token = jwt.encode(external_payload, secret_key, algorithm='HS256')
    
    # Validate and integrate
    validator = ExternalJWTValidator(secret_key)
    
    try:
        # Validate external token
        payload = validator.validate_external_jwt(external_token)
        
        # Create/update user in SurrealDB
        user = validator.create_surrealdb_user(payload)
        
        # Get SurrealDB token
        surrealdb_token = validator.get_surrealdb_token(user)
        
        # Use SurrealDB token
        with Surreal("ws://localhost:8000/rpc") as db:
            db.authenticate(surrealdb_token)
            db.use("mycompany", "production")
            
            user_info = db.info()
            print(f"✅ External user authenticated: {user_info}")
        
        return surrealdb_token
        
    except Exception as e:
        print(f"❌ External JWT integration failed: {e}")
        raise

# Run example
external_token = external_jwt_example()
```

## JWT Service Class

### Complete JWT Authentication Service

```python
import jwt
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from surrealdb import Surreal

class JWTAuthService:
    """Complete JWT authentication service"""
    
    def __init__(self, db_url: str, namespace: str, database: str):
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
        self.token_cache = {}
    
    def authenticate_user(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return token info"""
        
        try:
            with Surreal(self.db_url) as db:
                # Authenticate user
                token = db.signin(credentials)
                
                if not credentials.get("scope"):
                    db.use(self.namespace, self.database)
                
                # Get user info
                user_info = db.info()
                
                # Cache token
                user_id = user_info.get("id") or user_info.get("email")
                if user_id:
                    self.token_cache[user_id] = {
                        "token": token,
                        "user_info": user_info,
                        "created_at": datetime.now(),
                        "credentials": credentials
                    }
                
                return {
                    "success": True,
                    "token": token,
                    "user_info": user_info,
                    "expires_in": 24 * 3600  # 24 hours in seconds
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "token": None,
                "user_info": None
            }
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        
        try:
            with Surreal(self.db_url) as db:
                # Try to authenticate with token
                db.authenticate(token)
                db.use(self.namespace, self.database)
                
                # Get current user info
                user_info = db.info()
                
                if user_info:
                    return {
                        "valid": True,
                        "user_info": user_info
                    }
                else:
                    return {
                        "valid": False,
                        "error": "No user info returned"
                    }
                    
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def refresh_token(self, user_id: str) -> Dict[str, Any]:
        """Refresh token for user"""
        
        if user_id not in self.token_cache:
            return {
                "success": False,
                "error": "No cached credentials for user"
            }
        
        cached_data = self.token_cache[user_id]
        credentials = cached_data["credentials"]
        
        # Re-authenticate to get new token
        return self.authenticate_user(credentials)
    
    def invalidate_token(self, user_id: str) -> bool:
        """Invalidate cached token"""
        
        if user_id in self.token_cache:
            del self.token_cache[user_id]
            return True
        return False
    
    def get_authenticated_connection(self, token: str):
        """Get authenticated database connection"""
        
        validation = self.validate_token(token)
        
        if not validation["valid"]:
            raise Exception(f"Invalid token: {validation['error']}")
        
        db = Surreal(self.db_url)
        db.authenticate(token)
        db.use(self.namespace, self.database)
        
        return db
    
    def execute_with_token(self, token: str, operation):
        """Execute operation with token authentication"""
        
        try:
            with self.get_authenticated_connection(token) as db:
                return {
                    "success": True,
                    "data": operation(db)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def jwt_service_example():
    """Example using JWT authentication service"""
    
    # Initialize service
    auth_service = JWTAuthService(
        db_url="ws://localhost:8000/rpc",
        namespace="mycompany",
        database="production"
    )
    
    # User credentials
    user_creds = {
        "namespace": "mycompany",
        "database": "production",
        "scope": "user",
        "email": "john.doe@example.com",
        "password": "SecurePassword123!"
    }
    
    # Authenticate user
    auth_result = auth_service.authenticate_user(user_creds)
    
    if auth_result["success"]:
        token = auth_result["token"]
        user_info = auth_result["user_info"]
        
        print(f"✅ User authenticated: {user_info['email']}")
        print(f"Token: {token[:50]}...")
        
        # Validate token
        validation = auth_service.validate_token(token)
        print(f"Token valid: {validation['valid']}")
        
        # Execute operation with token
        def get_user_data(db):
            return db.query("SELECT * FROM user WHERE id = $auth;")
        
        result = auth_service.execute_with_token(token, get_user_data)
        
        if result["success"]:
            print(f"✅ Operation successful: {len(result['data'])} records")
        else:
            print(f"❌ Operation failed: {result['error']}")
        
        # Refresh token
        user_id = user_info.get("id") or user_info.get("email")
        refresh_result = auth_service.refresh_token(user_id)
        
        if refresh_result["success"]:
            print("✅ Token refreshed successfully")
        
        return auth_service
    else:
        print(f"❌ Authentication failed: {auth_result['error']}")
        return None

# Run example
auth_service = jwt_service_example()
```

## API Integration Patterns

### REST API with JWT

```python
from flask import Flask, request, jsonify
from functools import wraps
from surrealdb import Surreal

app = Flask(__name__)

class APIAuthService:
    """JWT authentication for REST API"""
    
    def __init__(self, db_url, namespace, database):
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
    
    def authenticate_request(self, token):
        """Authenticate API request with JWT token"""
        
        try:
            with Surreal(self.db_url) as db:
                db.authenticate(token)
                db.use(self.namespace, self.database)
                
                user_info = db.info()
                return {"valid": True, "user": user_info}
                
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Initialize auth service
auth_service = APIAuthService(
    "ws://localhost:8000/rpc",
    "mycompany", 
    "production"
)

def require_auth(f):
    """Decorator to require JWT authentication"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401
        
        try:
            # Extract token (format: "Bearer <token>")
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({"error": "Invalid authorization header"}), 401
        
        # Validate token
        auth_result = auth_service.authenticate_request(token)
        
        if not auth_result["valid"]:
            return jsonify({"error": "Invalid token"}), 401
        
        # Add user info to request context
        request.current_user = auth_result["user"]
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint"""
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        with Surreal(auth_service.db_url) as db:
            token = db.signin({
                "namespace": auth_service.namespace,
                "database": auth_service.database,
                "scope": "user",
                "email": email,
                "password": password
            })
            
            db.use(auth_service.namespace, auth_service.database)
            user_info = db.info()
            
            return jsonify({
                "token": token,
                "user": user_info,
                "expires_in": 24 * 3600
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile (requires authentication)"""
    
    return jsonify({
        "user": request.current_user
    })

@app.route('/api/users', methods=['GET'])
@require_auth
def get_users():
    """Get users (requires authentication)"""
    
    try:
        # Get token from request
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        with Surreal(auth_service.db_url) as db:
            db.authenticate(token)
            db.use(auth_service.namespace, auth_service.database)
            
            users = db.select("user")
            
            return jsonify({
                "users": users,
                "count": len(users)
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## Best Practices

### Security Considerations

```python
import os
import secrets
from datetime import datetime, timedelta

class SecureJWTHandler:
    """Secure JWT handling with best practices"""
    
    def __init__(self):
        # Use environment variables for secrets
        self.jwt_secret = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)
        self.token_expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        self.refresh_threshold_hours = int(os.getenv("JWT_REFRESH_THRESHOLD", "6"))
    
    def should_refresh_token(self, token_created_at):
        """Check if token should be refreshed"""
        
        threshold = datetime.now() - timedelta(hours=self.refresh_threshold_hours)
        return token_created_at < threshold
    
    def secure_token_storage(self, user_id, token):
        """Securely store token (implement based on your needs)"""
        
        # Options:
        # 1. Encrypted database storage
        # 2. Redis with expiration
        # 3. Secure HTTP-only cookies
        # 4. Encrypted local storage
        
        # Example: Redis storage
        # redis_client.setex(f"jwt:{user_id}", self.token_expiry_hours * 3600, token)
        
        print(f"Token stored securely for user: {user_id}")
    
    def validate_token_security(self, token):
        """Additional security validation"""
        
        # Check token format
        if not token or len(token) < 50:
            raise Exception("Invalid token format")
        
        # Check for suspicious patterns
        if "null" in token or "undefined" in token:
            raise Exception("Suspicious token content")
        
        return True

# Security best practices checklist
def security_checklist():
    """JWT security best practices"""
    
    practices = [
        "✅ Use HTTPS/WSS in production",
        "✅ Store JWT secret in environment variables",
        "✅ Implement token expiration",
        "✅ Use secure token storage",
        "✅ Validate tokens on every request",
        "✅ Implement token refresh mechanism",
        "✅ Log authentication events",
        "✅ Use strong passwords for user accounts",
        "✅ Implement rate limiting",
        "✅ Monitor for suspicious activity"
    ]
    
    print("JWT Security Best Practices:")
    for practice in practices:
        print(f"  {practice}")

security_checklist()
```

## Next Steps

You now understand JWT authentication with SurrealDB. Continue with:

- **[GitHub SSO](./github-sso.md)** - OAuth integration with GitHub
- **[Auth0 Integration](./auth0.md)** - Enterprise SSO
- **[Custom Scopes](./custom-scopes.md)** - Advanced user management

## Common Issues

### Issue: "Token expired"

**Solution:**
```python
# Implement automatic token refresh
def auto_refresh_token(auth_service, user_id, token):
    validation = auth_service.validate_token(token)
    if not validation["valid"] and "expired" in validation["error"]:
        return auth_service.refresh_token(user_id)
    return {"success": True, "token": token}
```

### Issue: "Invalid token format"

**Solution:**
```python
# Validate token format before use
def validate_token_format(token):
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string")
    
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    
    return True
```

Ready for SSO integration? Continue with [GitHub SSO](./github-sso.md).