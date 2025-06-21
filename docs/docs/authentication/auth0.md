---
sidebar_position: 5
---

# Auth0 Integration

Learn how to integrate Auth0 with SurrealDB for enterprise-grade authentication. This guide covers Auth0 setup, JWT validation, and user management.

## Overview

Auth0 provides enterprise authentication features including:

- **Universal Login** - Centralized authentication experience
- **Social Connections** - Google, Facebook, GitHub, etc.
- **Enterprise Connections** - SAML, LDAP, Active Directory
- **Multi-Factor Authentication** - SMS, email, authenticator apps
- **User Management** - Admin dashboard and APIs
- **Security Features** - Anomaly detection, brute force protection

## Auth0 Setup

### 1. Create Auth0 Application

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Create a new application
3. Choose "Regular Web Application" or "Single Page Application"
4. Configure settings:
   - **Allowed Callback URLs**: `http://localhost:8080/callback`
   - **Allowed Logout URLs**: `http://localhost:8080/logout`
   - **Allowed Web Origins**: `http://localhost:8080`

### 2. Environment Configuration

```bash
# .env file
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_AUDIENCE=https://your-api-identifier
AUTH0_CALLBACK_URL=http://localhost:8080/callback
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NS=mycompany
SURREALDB_DB=production
```

## Basic Auth0 Integration

### Auth0 Handler Implementation

```python
import os
import json
import jwt
import requests
from datetime import datetime
from urllib.parse import urlencode, quote_plus
from surrealdb import Surreal

class Auth0Handler:
    """Handle Auth0 authentication integration"""
    
    def __init__(self, domain=None, client_id=None, client_secret=None, audience=None):
        self.domain = domain or os.getenv("AUTH0_DOMAIN")
        self.client_id = client_id or os.getenv("AUTH0_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AUTH0_CLIENT_SECRET")
        self.audience = audience or os.getenv("AUTH0_AUDIENCE")
        
        if not all([self.domain, self.client_id, self.client_secret]):
            raise ValueError("Auth0 configuration incomplete")
        
        self.auth0_base = f"https://{self.domain}"
        self.callback_url = os.getenv("AUTH0_CALLBACK_URL", "http://localhost:8080/callback")
        
        # SurrealDB configuration
        self.db_url = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
        self.namespace = os.getenv("SURREALDB_NS", "mycompany")
        self.database = os.getenv("SURREALDB_DB", "production")
        
        # Cache for JWKS
        self._jwks_cache = None
        self._jwks_cache_time = None
    
    def get_authorization_url(self, state=None, scope="openid profile email"):
        """Generate Auth0 authorization URL"""
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": scope,
            "state": state or "default_state"
        }
        
        if self.audience:
            params["audience"] = self.audience
        
        auth_url = f"{self.auth0_base}/authorize?" + urlencode(params, quote_via=quote_plus)
        
        print(f"🔗 Auth0 authorization URL: {auth_url}")
        return auth_url
    
    def exchange_code_for_tokens(self, code):
        """Exchange authorization code for tokens"""
        
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.callback_url
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(
            f"{self.auth0_base}/oauth/token",
            data=token_data,
            headers=headers
        )
        
        if response.status_code == 200:
            tokens = response.json()
            print("✅ Auth0 tokens obtained")
            return tokens
        else:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
    
    def get_jwks(self):
        """Get Auth0 JSON Web Key Set (JWKS)"""
        
        # Cache JWKS for 1 hour
        if (self._jwks_cache and self._jwks_cache_time and 
            (datetime.now() - self._jwks_cache_time).seconds < 3600):
            return self._jwks_cache
        
        jwks_url = f"{self.auth0_base}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        
        if response.status_code == 200:
            self._jwks_cache = response.json()
            self._jwks_cache_time = datetime.now()
            return self._jwks_cache
        else:
            raise Exception(f"Failed to get JWKS: {response.status_code}")
    
    def verify_jwt_token(self, token):
        """Verify Auth0 JWT token"""
        
        try:
            # Get the public key
            jwks = self.get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            # Find the correct key
            key = None
            for jwk in jwks["keys"]:
                if jwk["kid"] == key_id:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break
            
            if not key:
                raise Exception("Unable to find appropriate key")
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"{self.auth0_base}/"
            )
            
            print(f"✅ Auth0 token verified for user: {payload.get('email', 'unknown')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print("❌ Auth0 token expired")
            raise
        except jwt.InvalidTokenError as e:
            print(f"❌ Auth0 token invalid: {e}")
            raise
    
    def get_user_info(self, access_token):
        """Get user information from Auth0"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(f"{self.auth0_base}/userinfo", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Auth0 user info retrieved: {user_info.get('email', 'unknown')}")
            return user_info
        else:
            raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")
    
    def create_or_update_user(self, auth0_user):
        """Create or update user in SurrealDB"""
        
        with Surreal(self.db_url) as db:
            # Authenticate as admin
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Prepare user data
            user_data = {
                "email": auth0_user.get("email"),
                "name": auth0_user.get("name"),
                "nickname": auth0_user.get("nickname"),
                "auth0_id": auth0_user.get("sub"),
                "picture": auth0_user.get("picture"),
                "email_verified": auth0_user.get("email_verified", False),
                "locale": auth0_user.get("locale"),
                "updated_at": auth0_user.get("updated_at"),
                "provider": "auth0",
                "last_login": datetime.now().isoformat(),
                "metadata": {
                    "app_metadata": auth0_user.get("app_metadata", {}),
                    "user_metadata": auth0_user.get("user_metadata", {})
                }
            }
            
            # Extract custom claims
            for key, value in auth0_user.items():
                if key.startswith("https://") or key.startswith("http://"):
                    # Custom claims are usually namespaced
                    claim_name = key.split("/")[-1]
                    user_data[f"custom_{claim_name}"] = value
            
            # Check if user exists
            existing_user = db.query(
                "SELECT * FROM user WHERE auth0_id = $auth0_id OR email = $email",
                {
                    "auth0_id": user_data["auth0_id"],
                    "email": user_data["email"]
                }
            )
            
            if existing_user:
                # Update existing user
                user_id = existing_user[0]["id"]
                updated_user = db.merge(user_id, user_data)
                print(f"✅ Updated existing user: {updated_user[0]['email']}")
                return updated_user[0]
            else:
                # Create new user
                new_user = db.create("user", user_data)
                print(f"✅ Created new user: {new_user[0]['email']}")
                return new_user[0]
    
    def setup_auth0_scope(self):
        """Setup Auth0 authentication scope in SurrealDB"""
        
        with Surreal(self.db_url) as db:
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Define Auth0 scope
            db.query("""
                DEFINE SCOPE auth0 SESSION 24h
                SIGNIN ( 
                    SELECT * FROM user 
                    WHERE provider = 'auth0' 
                    AND auth0_id = $auth0_id 
                    AND email_verified = true
                );
            """)
            
            print("✅ Auth0 scope defined")
    
    def authenticate_user(self, user):
        """Authenticate user and return SurrealDB token"""
        
        with Surreal(self.db_url) as db:
            db.use(self.namespace, self.database)
            
            try:
                # Sign in with Auth0 scope
                token = db.signin({
                    "namespace": self.namespace,
                    "database": self.database,
                    "scope": "auth0",
                    "auth0_id": user["auth0_id"]
                })
                
                print("✅ SurrealDB authentication successful")
                return token
                
            except Exception as e:
                print(f"⚠️ Scope signin failed: {e}")
                
                # Fallback for demo purposes
                admin_token = db.signin({"username": "root", "password": "root"})
                return admin_token
    
    def complete_auth0_flow(self, code):
        """Complete Auth0 authentication flow"""
        
        try:
            # Exchange code for tokens
            tokens = self.exchange_code_for_tokens(code)
            
            # Get user info
            if "access_token" in tokens:
                user_info = self.get_user_info(tokens["access_token"])
            else:
                # Decode ID token if no access token
                user_info = self.verify_jwt_token(tokens["id_token"])
            
            # Create/update user in SurrealDB
            user = self.create_or_update_user(user_info)
            
            # Authenticate user
            surrealdb_token = self.authenticate_user(user)
            
            return {
                "success": True,
                "user": user,
                "auth0_tokens": tokens,
                "surrealdb_token": surrealdb_token,
                "user_info": user_info
            }
            
        except Exception as e:
            print(f"❌ Auth0 flow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def basic_auth0_example():
    """Basic Auth0 integration example"""
    
    # Initialize Auth0 handler
    auth0_handler = Auth0Handler()
    
    # Setup Auth0 scope
    auth0_handler.setup_auth0_scope()
    
    # Generate authorization URL
    auth_url = auth0_handler.get_authorization_url(state="demo_state")
    
    print("\n📋 Auth0 Integration Flow:")
    print("1. Visit the authorization URL")
    print("2. Complete Auth0 login")
    print("3. Copy the 'code' parameter from the callback URL")
    print("4. Use the code to complete authentication")
    print(f"\nAuthorization URL: {auth_url}")
    
    return auth0_handler

# Run basic example
auth0_handler = basic_auth0_example()
```

## Web Application Integration

### Flask App with Auth0

```python
from flask import Flask, request, redirect, session, jsonify, render_template_string
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")

# Initialize OAuth
oauth = OAuth(app)

# Configure Auth0
auth0 = oauth.register(
    'auth0',
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid profile email'
    }
)

# Initialize Auth0 handler
auth0_handler = Auth0Handler()

@app.route('/')
def home():
    """Home page"""
    
    if 'user' in session:
        user = session['user']
        return render_template_string("""
        <h1>Welcome, {{ user.name }}!</h1>
        <img src="{{ user.picture }}" width="100" height="100">
        <p>Email: {{ user.email }} 
           {% if user.email_verified %}✅{% else %}❌{% endif %}
        </p>
        <p>Auth0 ID: {{ user.auth0_id }}</p>
        <p>Last Login: {{ user.last_login }}</p>
        <a href="/logout">Logout</a>
        <br><br>
        <a href="/api/profile">View API Profile</a>
        """, user=user)
    else:
        return render_template_string("""
        <h1>Auth0 Integration Demo</h1>
        <a href="/login">Login with Auth0</a>
        """)

@app.route('/login')
def login():
    """Initiate Auth0 login"""
    
    redirect_uri = request.url_root.rstrip('/') + '/callback'
    return auth0.authorize_redirect(redirect_uri)

@app.route('/callback')
def callback():
    """Handle Auth0 callback"""
    
    try:
        # Get token from Auth0
        token = auth0.authorize_access_token()
        
        # Get user info
        user_info = token.get('userinfo')
        if not user_info:
            user_info = auth0.parse_id_token(token)
        
        # Complete Auth0 flow with SurrealDB
        result = auth0_handler.complete_auth0_flow_with_userinfo(user_info)
        
        if result["success"]:
            # Store user info in session
            session['user'] = result["user"]
            session['surrealdb_token'] = result["surrealdb_token"]
            session['auth0_tokens'] = result["auth0_tokens"]
            
            return redirect('/')
        else:
            return f"Authentication failed: {result['error']}", 500
            
    except Exception as e:
        return f"Callback error: {str(e)}", 500

@app.route('/logout')
def logout():
    """Logout user"""
    
    session.clear()
    
    # Redirect to Auth0 logout
    logout_url = f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?" + urlencode({
        'returnTo': request.url_root,
        'client_id': os.getenv('AUTH0_CLIENT_ID')
    })
    
    return redirect(logout_url)

@app.route('/api/profile')
def api_profile():
    """API endpoint to get user profile"""
    
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "user": session['user'],
        "authenticated": True,
        "provider": "auth0"
    })

@app.route('/api/secure-data')
def secure_data():
    """Secure API endpoint"""
    
    if 'surrealdb_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Use SurrealDB token to fetch data
        with Surreal(auth0_handler.db_url) as db:
            db.authenticate(session['surrealdb_token'])
            db.use(auth0_handler.namespace, auth0_handler.database)
            
            # Get user's data
            user_data = db.query("SELECT * FROM user WHERE id = $auth;")
            
            return jsonify({
                "data": user_data,
                "message": "Secure data accessed successfully"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
```

## Advanced Auth0 Features

### Role-Based Access Control

```python
from surrealdb import Surreal

class Auth0RBACHandler(Auth0Handler):
    """Auth0 handler with Role-Based Access Control"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.role_mapping = {
            "admin": ["read", "write", "delete", "admin"],
            "manager": ["read", "write", "manage_team"],
            "user": ["read", "write_own"],
            "viewer": ["read"]
        }
    
    def get_user_roles_from_auth0(self, user_info):
        """Extract user roles from Auth0 user info"""
        
        # Check for roles in different locations
        roles = []
        
        # Custom claims (namespace format)
        for key, value in user_info.items():
            if "roles" in key.lower():
                if isinstance(value, list):
                    roles.extend(value)
                elif isinstance(value, str):
                    roles.append(value)
        
        # App metadata
        app_metadata = user_info.get("app_metadata", {})
        if "roles" in app_metadata:
            roles.extend(app_metadata["roles"])
        
        # User metadata
        user_metadata = user_info.get("user_metadata", {})
        if "roles" in user_metadata:
            roles.extend(user_metadata["roles"])
        
        # Default role if none found
        if not roles:
            roles = ["user"]
        
        return list(set(roles))  # Remove duplicates
    
    def calculate_permissions(self, roles):
        """Calculate permissions based on roles"""
        
        permissions = set()
        
        for role in roles:
            if role in self.role_mapping:
                permissions.update(self.role_mapping[role])
        
        return list(permissions)
    
    def create_or_update_user_with_rbac(self, auth0_user):
        """Create/update user with role-based access control"""
        
        # Get user roles
        roles = self.get_user_roles_from_auth0(auth0_user)
        permissions = self.calculate_permissions(roles)
        
        with Surreal(self.db_url) as db:
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Enhanced user data with RBAC
            user_data = {
                "email": auth0_user.get("email"),
                "name": auth0_user.get("name"),
                "auth0_id": auth0_user.get("sub"),
                "picture": auth0_user.get("picture"),
                "email_verified": auth0_user.get("email_verified", False),
                "roles": roles,
                "permissions": permissions,
                "access_level": self.determine_access_level(roles),
                "provider": "auth0",
                "last_login": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Check if user exists
            existing_user = db.query(
                "SELECT * FROM user WHERE auth0_id = $auth0_id",
                {"auth0_id": user_data["auth0_id"]}
            )
            
            if existing_user:
                user_id = existing_user[0]["id"]
                updated_user = db.merge(user_id, user_data)
                print(f"✅ Updated user with RBAC: {updated_user[0]['email']}")
                return updated_user[0]
            else:
                new_user = db.create("user", user_data)
                print(f"✅ Created user with RBAC: {new_user[0]['email']}")
                return new_user[0]
    
    def determine_access_level(self, roles):
        """Determine overall access level"""
        
        if "admin" in roles:
            return "admin"
        elif "manager" in roles:
            return "manager"
        elif "user" in roles:
            return "user"
        else:
            return "viewer"
    
    def setup_rbac_scope(self):
        """Setup RBAC scope in SurrealDB"""
        
        with Surreal(self.db_url) as db:
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Define RBAC scope
            db.query("""
                DEFINE SCOPE auth0_rbac SESSION 24h
                SIGNIN ( 
                    SELECT * FROM user 
                    WHERE provider = 'auth0' 
                    AND auth0_id = $auth0_id 
                    AND email_verified = true
                    AND array::len(roles) > 0
                );
            """)
            
            # Define permission-based table access
            db.query("""
                DEFINE TABLE secure_data SCHEMAFULL
                PERMISSIONS 
                    FOR select WHERE 'read' IN $auth.permissions
                    FOR create, update WHERE 'write' IN $auth.permissions
                    FOR delete WHERE 'delete' IN $auth.permissions;
            """)
            
            print("✅ RBAC scope and permissions defined")

def rbac_example():
    """Example with Role-Based Access Control"""
    
    # Initialize RBAC handler
    rbac_handler = Auth0RBACHandler()
    
    # Setup RBAC scope
    rbac_handler.setup_rbac_scope()
    
    print("✅ Auth0 RBAC handler initialized")
    print(f"Role mapping: {rbac_handler.role_mapping}")
    
    # Simulate user with roles
    mock_user_info = {
        "sub": "auth0|123456789",
        "email": "admin@example.com",
        "name": "Admin User",
        "email_verified": True,
        "https://myapp.com/roles": ["admin", "manager"]
    }
    
    # Process user with RBAC
    user = rbac_handler.create_or_update_user_with_rbac(mock_user_info)
    print(f"User roles: {user['roles']}")
    print(f"User permissions: {user['permissions']}")
    print(f"Access level: {user['access_level']}")
    
    return rbac_handler

# Run RBAC example
rbac_handler = rbac_example()
```

### Multi-Factor Authentication

```python
class Auth0MFAHandler(Auth0Handler):
    """Auth0 handler with MFA support"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mfa_required_roles = ["admin", "manager"]
    
    def check_mfa_requirement(self, user_roles):
        """Check if MFA is required for user"""
        
        return any(role in self.mfa_required_roles for role in user_roles)
    
    def verify_mfa_token(self, id_token):
        """Verify MFA was completed"""
        
        try:
            payload = self.verify_jwt_token(id_token)
            
            # Check for MFA claim
            amr = payload.get("amr", [])  # Authentication Methods References
            
            mfa_methods = ["mfa", "otp", "sms", "totp"]
            mfa_completed = any(method in amr for method in mfa_methods)
            
            return {
                "mfa_completed": mfa_completed,
                "auth_methods": amr,
                "payload": payload
            }
            
        except Exception as e:
            return {
                "mfa_completed": False,
                "error": str(e)
            }
    
    def enforce_mfa_policy(self, user_info, id_token):
        """Enforce MFA policy based on user roles"""
        
        # Get user roles
        roles = self.get_user_roles_from_auth0(user_info)
        
        # Check if MFA is required
        mfa_required = self.check_mfa_requirement(roles)
        
        if mfa_required:
            # Verify MFA was completed
            mfa_result = self.verify_mfa_token(id_token)
            
            if not mfa_result["mfa_completed"]:
                raise Exception(
                    f"MFA required for roles {roles} but not completed. "
                    f"Auth methods: {mfa_result.get('auth_methods', [])}"
                )
            
            print(f"✅ MFA verified for user with roles: {roles}")
        
        return {
            "mfa_required": mfa_required,
            "mfa_completed": mfa_result.get("mfa_completed", False) if mfa_required else None,
            "roles": roles
        }

def mfa_example():
    """Example with MFA enforcement"""
    
    mfa_handler = Auth0MFAHandler()
    
    print("✅ Auth0 MFA handler initialized")
    print(f"MFA required for roles: {mfa_handler.mfa_required_roles}")
    
    return mfa_handler

# Run MFA example
mfa_handler = mfa_example()
```

## Management API Integration

### Auth0 Management API

```python
import requests
from datetime import datetime, timedelta

class Auth0ManagementAPI:
    """Auth0 Management API integration"""
    
    def __init__(self, domain, client_id, client_secret, audience=None):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience or f"https://{domain}/api/v2/"
        self.base_url = f"https://{domain}/api/v2"
        
        self.access_token = None
        self.token_expires_at = None
    
    def get_management_token(self):
        """Get Management API access token"""
        
        # Check if token is still valid
        if (self.access_token and self.token_expires_at and 
            datetime.now() < self.token_expires_at):
            return self.access_token
        
        # Request new token
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience
        }
        
        response = requests.post(
            f"https://{self.domain}/oauth/token",
            json=token_data
        )
        
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            
            # Calculate expiration (subtract 5 minutes for safety)
            expires_in = token_info.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            print("✅ Management API token obtained")
            return self.access_token
        else:
            raise Exception(f"Failed to get management token: {response.status_code}")
    
    def get_user(self, user_id):
        """Get user by ID"""
        
        token = self.get_management_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{self.base_url}/users/{user_id}", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user: {response.status_code}")
    
    def update_user_metadata(self, user_id, user_metadata=None, app_metadata=None):
        """Update user metadata"""
        
        token = self.get_management_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        data = {}
        if user_metadata:
            data["user_metadata"] = user_metadata
        if app_metadata:
            data["app_metadata"] = app_metadata
        
        response = requests.patch(
            f"{self.base_url}/users/{user_id}",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ User metadata updated for {user_id}")
            return response.json()
        else:
            raise Exception(f"Failed to update user: {response.status_code}")
    
    def assign_roles_to_user(self, user_id, role_ids):
        """Assign roles to user"""
        
        token = self.get_management_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        data = {"roles": role_ids}
        
        response = requests.post(
            f"{self.base_url}/users/{user_id}/roles",
            json=data,
            headers=headers
        )
        
        if response.status_code == 204:
            print(f"✅ Roles assigned to user {user_id}")
        else:
            raise Exception(f"Failed to assign roles: {response.status_code}")
    
    def get_user_roles(self, user_id):
        """Get user's roles"""
        
        token = self.get_management_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{self.base_url}/users/{user_id}/roles", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user roles: {