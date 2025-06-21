---
sidebar_position: 4
---

# GitHub SSO Integration

Learn how to implement GitHub OAuth authentication with SurrealDB. This guide covers the complete OAuth flow, user management, and security best practices.

## Overview

GitHub SSO provides secure authentication using GitHub accounts, perfect for:

- **Developer Tools** - Natural fit for developer-focused applications
- **Open Source Projects** - Leverage existing GitHub community
- **Team Applications** - Use GitHub organization membership
- **Social Authentication** - Reduce registration friction

## GitHub OAuth Setup

### 1. Register GitHub OAuth App

First, register your application with GitHub:

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the details:
   - **Application name**: Your app name
   - **Homepage URL**: `https://yourapp.com`
   - **Authorization callback URL**: `https://yourapp.com/auth/github/callback`
4. Note your `Client ID` and `Client Secret`

### 2. Environment Configuration

```bash
# .env file
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8080/auth/github/callback
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NS=mycompany
SURREALDB_DB=production
```

## Basic GitHub SSO Implementation

### GitHub OAuth Handler

```python
import os
import secrets
import urllib.parse
import requests
from datetime import datetime
from surrealdb import Surreal

class GitHubSSOHandler:
    """Handle GitHub OAuth authentication flow"""
    
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id or os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GITHUB_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("GITHUB_REDIRECT_URI")
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("GitHub OAuth credentials not configured")
        
        self.github_api_base = "https://api.github.com"
        self.github_oauth_base = "https://github.com/login/oauth"
        
        # SurrealDB configuration
        self.db_url = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
        self.namespace = os.getenv("SURREALDB_NS", "mycompany")
        self.database = os.getenv("SURREALDB_DB", "production")
    
    def generate_auth_url(self, scopes=None, state=None):
        """Generate GitHub OAuth authorization URL"""
        
        if scopes is None:
            scopes = ["user:email", "read:user"]
        
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "response_type": "code"
        }
        
        auth_url = f"{self.github_oauth_base}/authorize?" + urllib.parse.urlencode(params)
        
        print(f"🔗 GitHub OAuth URL: {auth_url}")
        print(f"🔑 State token: {state}")
        
        return auth_url, state
    
    def exchange_code_for_token(self, code, state):
        """Exchange authorization code for access token"""
        
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        
        headers = {"Accept": "application/json"}
        
        response = requests.post(
            f"{self.github_oauth_base}/access_token",
            data=token_data,
            headers=headers
        )
        
        if response.status_code == 200:
            token_info = response.json()
            
            if "error" in token_info:
                raise Exception(f"GitHub OAuth error: {token_info['error_description']}")
            
            access_token = token_info.get("access_token")
            
            if access_token:
                print("✅ GitHub access token obtained")
                return access_token
            else:
                raise Exception(f"No access token in response: {token_info}")
        else:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
    
    def get_github_user_info(self, access_token):
        """Get user information from GitHub API"""
        
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get user profile
        user_response = requests.get(f"{self.github_api_base}/user", headers=headers)
        
        if user_response.status_code != 200:
            raise Exception(f"Failed to get user info: {user_response.status_code}")
        
        user_data = user_response.json()
        
        # Get user emails
        emails_response = requests.get(f"{self.github_api_base}/user/emails", headers=headers)
        
        if emails_response.status_code == 200:
            emails = emails_response.json()
            primary_email = next((email["email"] for email in emails if email["primary"]), None)
            user_data["primary_email"] = primary_email
            user_data["verified_email"] = next((email["verified"] for email in emails if email["primary"]), False)
        
        # Get user organizations (optional)
        orgs_response = requests.get(f"{self.github_api_base}/user/orgs", headers=headers)
        
        if orgs_response.status_code == 200:
            orgs = orgs_response.json()
            user_data["organizations"] = [org["login"] for org in orgs]
        
        print(f"✅ GitHub user info retrieved: {user_data.get('login')}")
        return user_data
    
    def create_or_update_user(self, github_user):
        """Create or update user in SurrealDB"""
        
        with Surreal(self.db_url) as db:
            # Authenticate as admin to manage users
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Prepare user data
            user_data = {
                "email": github_user.get("primary_email") or github_user.get("email"),
                "name": github_user.get("name") or github_user.get("login"),
                "username": github_user.get("login"),
                "github_id": github_user.get("id"),
                "avatar_url": github_user.get("avatar_url"),
                "github_profile": github_user.get("html_url"),
                "bio": github_user.get("bio"),
                "location": github_user.get("location"),
                "company": github_user.get("company"),
                "blog": github_user.get("blog"),
                "public_repos": github_user.get("public_repos", 0),
                "followers": github_user.get("followers", 0),
                "following": github_user.get("following", 0),
                "organizations": github_user.get("organizations", []),
                "email_verified": github_user.get("verified_email", False),
                "provider": "github",
                "updated_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat()
            }
            
            # Check if user exists by GitHub ID or email
            existing_user = db.query(
                "SELECT * FROM user WHERE github_id = $github_id OR email = $email",
                {
                    "github_id": user_data["github_id"],
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
    
    def setup_github_scope(self):
        """Setup GitHub authentication scope in SurrealDB"""
        
        with Surreal(self.db_url) as db:
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Define GitHub scope
            db.query("""
                DEFINE SCOPE github SESSION 24h
                SIGNIN ( 
                    SELECT * FROM user 
                    WHERE provider = 'github' 
                    AND github_id = $github_id 
                    AND active != false
                );
            """)
            
            print("✅ GitHub scope defined")
    
    def authenticate_user(self, user):
        """Authenticate user and return SurrealDB token"""
        
        with Surreal(self.db_url) as db:
            db.use(self.namespace, self.database)
            
            try:
                # Sign in with GitHub scope
                token = db.signin({
                    "namespace": self.namespace,
                    "database": self.database,
                    "scope": "github",
                    "github_id": user["github_id"]
                })
                
                print("✅ SurrealDB authentication successful")
                return token
                
            except Exception as e:
                print(f"⚠️ Scope signin failed: {e}")
                
                # Fallback: create a session token manually
                # In production, implement proper scope-based authentication
                with Surreal(self.db_url) as admin_db:
                    admin_token = admin_db.signin({"username": "root", "password": "root"})
                    return admin_token
    
    def complete_oauth_flow(self, code, state):
        """Complete the OAuth flow and return authentication result"""
        
        try:
            # Exchange code for access token
            access_token = self.exchange_code_for_token(code, state)
            
            # Get user info from GitHub
            github_user = self.get_github_user_info(access_token)
            
            # Create/update user in SurrealDB
            user = self.create_or_update_user(github_user)
            
            # Authenticate user
            surrealdb_token = self.authenticate_user(user)
            
            return {
                "success": True,
                "user": user,
                "github_token": access_token,
                "surrealdb_token": surrealdb_token,
                "github_data": github_user
            }
            
        except Exception as e:
            print(f"❌ OAuth flow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user": None,
                "github_token": None,
                "surrealdb_token": None
            }

def basic_github_sso_example():
    """Basic GitHub SSO example"""
    
    # Initialize GitHub SSO handler
    github_sso = GitHubSSOHandler()
    
    # Setup GitHub scope
    github_sso.setup_github_scope()
    
    # Step 1: Generate authorization URL
    auth_url, state = github_sso.generate_auth_url()
    
    print("\n📋 GitHub SSO Flow:")
    print("1. Visit the authorization URL")
    print("2. Authorize the application")
    print("3. Copy the 'code' parameter from the callback URL")
    print("4. Use the code to complete authentication")
    print(f"\nAuthorization URL: {auth_url}")
    
    # In a real application, you'd redirect the user to auth_url
    # and handle the callback to get the code
    
    # For demo purposes, simulate the callback
    # In practice, you'd get these from the callback URL parameters
    print("\n⚠️ This is a demo - in production:")
    print("1. Redirect user to the authorization URL")
    print("2. Handle the callback to extract 'code' and 'state'")
    print("3. Call complete_oauth_flow(code, state)")
    
    return github_sso

# Run basic example
github_handler = basic_github_sso_example()
```

## Web Application Integration

### Flask Web App with GitHub SSO

```python
from flask import Flask, request, redirect, session, jsonify, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")

# Initialize GitHub SSO handler
github_sso = GitHubSSOHandler()

@app.route('/')
def home():
    """Home page with login option"""
    
    if 'user' in session:
        user = session['user']
        return render_template_string("""
        <h1>Welcome, {{ user.name }}!</h1>
        <img src="{{ user.avatar_url }}" width="100" height="100">
        <p>Email: {{ user.email }}</p>
        <p>GitHub: <a href="{{ user.github_profile }}">{{ user.username }}</a></p>
        <p>Organizations: {{ user.organizations | join(', ') }}</p>
        <a href="/logout">Logout</a>
        """, user=user)
    else:
        return render_template_string("""
        <h1>GitHub SSO Demo</h1>
        <a href="/auth/github">Login with GitHub</a>
        """)

@app.route('/auth/github')
def github_login():
    """Initiate GitHub OAuth flow"""
    
    # Generate authorization URL
    auth_url, state = github_sso.generate_auth_url()
    
    # Store state in session for validation
    session['oauth_state'] = state
    
    # Redirect to GitHub
    return redirect(auth_url)

@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    
    # Get parameters from callback
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return f"GitHub OAuth error: {error}", 400
    
    if not code or not state:
        return "Missing code or state parameter", 400
    
    # Validate state
    if state != session.get('oauth_state'):
        return "Invalid state parameter", 400
    
    # Complete OAuth flow
    result = github_sso.complete_oauth_flow(code, state)
    
    if result["success"]:
        # Store user info in session
        session['user'] = result["user"]
        session['surrealdb_token'] = result["surrealdb_token"]
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        
        return redirect('/')
    else:
        return f"Authentication failed: {result['error']}", 500

@app.route('/logout')
def logout():
    """Logout user"""
    
    session.clear()
    return redirect('/')

@app.route('/api/profile')
def api_profile():
    """API endpoint to get user profile"""
    
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "user": session['user'],
        "authenticated": True
    })

@app.route('/api/data')
def api_data():
    """API endpoint that requires authentication"""
    
    if 'surrealdb_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Use SurrealDB token to fetch data
        with Surreal(github_sso.db_url) as db:
            db.authenticate(session['surrealdb_token'])
            db.use(github_sso.namespace, github_sso.database)
            
            # Get user's data
            user_data = db.query("SELECT * FROM user WHERE id = $auth;")
            
            return jsonify({
                "data": user_data,
                "message": "Data fetched successfully"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
```

## Advanced GitHub Integration

### Organization-Based Access Control

```python
from surrealdb import Surreal

class GitHubOrgHandler(GitHubSSOHandler):
    """GitHub SSO with organization-based access control"""
    
    def __init__(self, allowed_orgs=None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_orgs = allowed_orgs or []
    
    def check_organization_membership(self, access_token, username):
        """Check if user is member of allowed organizations"""
        
        if not self.allowed_orgs:
            return True  # No org restrictions
        
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        user_orgs = []
        
        # Get user's organizations
        orgs_response = requests.get(f"{self.github_api_base}/user/orgs", headers=headers)
        
        if orgs_response.status_code == 200:
            orgs = orgs_response.json()
            user_orgs = [org["login"] for org in orgs]
        
        # Check if user is in any allowed org
        allowed_membership = any(org in self.allowed_orgs for org in user_orgs)
        
        print(f"User orgs: {user_orgs}")
        print(f"Allowed orgs: {self.allowed_orgs}")
        print(f"Access granted: {allowed_membership}")
        
        return allowed_membership, user_orgs
    
    def get_team_memberships(self, access_token, org):
        """Get user's team memberships in an organization"""
        
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get user's teams in the organization
        teams_response = requests.get(
            f"{self.github_api_base}/user/teams",
            headers=headers
        )
        
        if teams_response.status_code == 200:
            teams = teams_response.json()
            org_teams = [
                team["name"] for team in teams 
                if team["organization"]["login"] == org
            ]
            return org_teams
        
        return []
    
    def create_or_update_user_with_org_data(self, github_user, access_token):
        """Create/update user with organization and team data"""
        
        # Check organization membership
        has_access, user_orgs = self.check_organization_membership(
            access_token, 
            github_user["login"]
        )
        
        if not has_access:
            raise Exception(f"User not member of allowed organizations: {self.allowed_orgs}")
        
        # Get team memberships for allowed orgs
        team_memberships = {}
        for org in user_orgs:
            if org in self.allowed_orgs:
                teams = self.get_team_memberships(access_token, org)
                team_memberships[org] = teams
        
        with Surreal(self.db_url) as db:
            db.signin({"username": "root", "password": "root"})
            db.use(self.namespace, self.database)
            
            # Enhanced user data with org/team info
            user_data = {
                "email": github_user.get("primary_email") or github_user.get("email"),
                "name": github_user.get("name") or github_user.get("login"),
                "username": github_user.get("login"),
                "github_id": github_user.get("id"),
                "avatar_url": github_user.get("avatar_url"),
                "github_profile": github_user.get("html_url"),
                "organizations": user_orgs,
                "allowed_organizations": [org for org in user_orgs if org in self.allowed_orgs],
                "team_memberships": team_memberships,
                "access_level": self.determine_access_level(user_orgs, team_memberships),
                "provider": "github",
                "updated_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat()
            }
            
            # Check if user exists
            existing_user = db.query(
                "SELECT * FROM user WHERE github_id = $github_id",
                {"github_id": user_data["github_id"]}
            )
            
            if existing_user:
                user_id = existing_user[0]["id"]
                updated_user = db.merge(user_id, user_data)
                print(f"✅ Updated user with org data: {updated_user[0]['email']}")
                return updated_user[0]
            else:
                new_user = db.create("user", user_data)
                print(f"✅ Created user with org data: {new_user[0]['email']}")
                return new_user[0]
    
    def determine_access_level(self, user_orgs, team_memberships):
        """Determine user access level based on org/team membership"""
        
        # Define access levels based on your needs
        if any("admin" in teams for teams in team_memberships.values()):
            return "admin"
        elif any("maintainer" in teams for teams in team_memberships.values()):
            return "maintainer"
        elif any(org in self.allowed_orgs for org in user_orgs):
            return "member"
        else:
            return "guest"
    
    def complete_oauth_flow_with_org_check(self, code, state):
        """Complete OAuth flow with organization access control"""
        
        try:
            # Exchange code for access token
            access_token = self.exchange_code_for_token(code, state)
            
            # Get user info from GitHub
            github_user = self.get_github_user_info(access_token)
            
            # Create/update user with org data (includes access check)
            user = self.create_or_update_user_with_org_data(github_user, access_token)
            
            # Authenticate user
            surrealdb_token = self.authenticate_user(user)
            
            return {
                "success": True,
                "user": user,
                "github_token": access_token,
                "surrealdb_token": surrealdb_token,
                "access_level": user["access_level"]
            }
            
        except Exception as e:
            print(f"❌ OAuth flow with org check failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def org_based_access_example():
    """Example with organization-based access control"""
    
    # Initialize with allowed organizations
    org_handler = GitHubOrgHandler(
        allowed_orgs=["mycompany", "mycompany-dev"],
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        redirect_uri=os.getenv("GITHUB_REDIRECT_URI")
    )
    
    print("✅ GitHub SSO with organization access control initialized")
    print(f"Allowed organizations: {org_handler.allowed_orgs}")
    
    # Generate auth URL
    auth_url, state = org_handler.generate_auth_url(
        scopes=["user:email", "read:user", "read:org"]
    )
    
    print(f"\nAuthorization URL (with org access): {auth_url}")
    
    return org_handler

# Run org-based example
org_handler = org_based_access_example()
```

## Security Best Practices

### Secure GitHub SSO Implementation

```python
import hashlib
import hmac
import time
from datetime import datetime, timedelta

class SecureGitHubSSO(GitHubSSOHandler):
    """Secure GitHub SSO with additional security measures"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        self.rate_limit_window = 300  # 5 minutes
        self.max_attempts = 5
        self.attempt_tracking = {}
    
    def generate_secure_state(self, user_session_id=None):
        """Generate cryptographically secure state parameter"""
        
        timestamp = str(int(time.time()))
        random_data = secrets.token_urlsafe(32)
        
        # Include session ID if available
        if user_session_id:
            state_data = f"{timestamp}:{user_session_id}:{random_data}"
        else:
            state_data = f"{timestamp}:{random_data}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.client_secret.encode(),
            state_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{state_data}:{signature}"
    
    def validate_state(self, state, user_session_id=None):
        """Validate state parameter"""
        
        try:
            parts = state.split(':')
            if len(parts) < 3:
                return False
            
            signature = parts[-1]
            state_data = ':'.join(parts[:-1])
            
            # Verify signature
            expected_signature = hmac.new(
                self.client_secret.encode(),
                state_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check timestamp (state should not be older than 10 minutes)
            timestamp = int(parts[0])
            if time.time() - timestamp > 600:  # 10 minutes
                return False
            
            # Validate session ID if provided
            if user_session_id and len(parts) >= 4:
                if parts[1] != user_session_id:
                    return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def check_rate_limit(self, identifier):
        """Check rate limiting for authentication attempts"""
        
        now = time.time()
        
        # Clean old attempts
        self.attempt_tracking = {
            k: v for k, v in self.attempt_tracking.items()
            if now - v["first_attempt"] < self.rate_limit_window
        }
        
        if identifier in self.attempt_tracking:
            attempts = self.attempt_tracking[identifier]
            
            if attempts["count"] >= self.max_attempts:
                time_left = self.rate_limit_window - (now - attempts["first_attempt"])
                raise Exception(f"Rate limit exceeded. Try again in {int(time_left)} seconds")
            
            attempts["count"] += 1
            attempts["last_attempt"] = now
        else:
            self.attempt_tracking[identifier] = {
                "count": 1,
                "first_attempt": now,
                "last_attempt": now
            }
    
    def log_security_event(self, event_type, details):
        """Log security events"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "source": "github_sso"
        }
        
        # In production, send to your logging system
        print(f"🔒 Security Event: {log_entry}")
        
        # Store in SurrealDB for audit trail
        try:
            with Surreal(self.db_url) as db:
                db.signin({"username": "root", "password": "root"})
                db.use(self.namespace, self.database)
                db.create("security_log", log_entry)
        except Exception as e:
            print(f"Failed to log security event: {e}")
    
    def secure_complete_oauth_flow(self, code, state, user_session_id=None, client_ip=None):
        """Secure OAuth flow with additional validation"""
        
        try:
            # Rate limiting
            identifier = client_ip or "unknown"
            self.check_rate_limit(identifier)
            
            # Validate state
            if not self.validate_state(state, user_session_id):
                self.log_security_event("invalid_state", {
                    "state": state[:20] + "...",
                    "client_ip": client_ip,
                    "session_id": user_session_id
                })
                raise Exception("Invalid or expired state parameter")
            
            # Complete OAuth flow
            result = self.complete_oauth_flow(code, state)
            
            if result["success"]:
                self.log_security_event("successful_login", {
                    "user_id": result["user"]["id"],
                    "username": result["user"]["username"],
                    "client_ip": client_ip
                })
            else:
                self.log_security_event("failed_login", {
                    "error": result["error"],
                    "client_ip": client_ip
                })
            
            return result
            
        except Exception as e:
            self.log_security_event("oauth_error", {
                "error": str(e),
                "client_ip": client_ip
            })
            raise
    
    def verify_webhook_signature(self, payload, signature):
        """Verify GitHub webhook signature"""
        
        if not self.webhook_secret:
            raise Exception("Webhook secret not configured")
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha1
        ).hexdigest()
        
        expected_signature = f"sha1={expected_signature}"
        
        return hmac.compare_digest(signature, expected_signature)

def security_best_practices():
    """Security best practices for GitHub SSO"""
    
    practices = [
        "✅ Use HTTPS for all OAuth redirects",
        "✅ Validate state parameter with HMAC",
        "✅ Implement rate limiting",
        "✅ Log all authentication events",
        "✅ Use secure session management",
        "✅ Validate webhook signatures",
        "✅ Implement CSRF protection",
        "✅ Use minimal required scopes",
        "✅ Regularly rotate client secrets",
        "✅ Monitor for suspicious activity"
    ]
    
    print("GitHub SSO Security Best Practices:")
    for practice in practices:
        print(f"  {practice}")

security_best_practices()
```

## Testing and Development

### GitHub SSO Testing Setup

```python
import unittest
from unittest.mock import patch, MagicMock

class TestGitHubSSO(unittest.TestCase):
    """Test GitHub SSO implementation"""
    
    def setUp(self):
        self.github_sso = GitHubSSOHandler(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback"
        )
    
    def test_generate_auth_url(self):
        """Test authorization URL generation"""
        
        auth_url, state = self.github_sso.generate_auth_url()