---
sidebar_position: 2
---

# Basic Authentication

Learn how to authenticate with SurrealDB using email and password credentials. This covers all authentication levels from root users to application scopes.

## Root User Authentication

Root users have complete access to the SurrealDB instance and can manage all namespaces and databases.

### Synchronous Root Authentication

```python
from surrealdb import Surreal

def root_authentication_example():
    """Basic root user authentication"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate as root user
            token = db.signin({
                "username": "root",
                "password": "root"
            })
            
            print("✅ Root authentication successful")
            print(f"Token: {token[:50]}..." if token else "No token returned")
            
            # Root users can access any namespace/database
            db.use("mycompany", "production")
            
            # Verify authentication
            user_info = db.info()
            print(f"Authenticated as: {user_info}")
            
            # Get server version (admin operation)
            version = db.version()
            print(f"SurrealDB version: {version}")
            
            return token
            
        except Exception as e:
            print(f"❌ Root authentication failed: {e}")
            raise

# Run example
root_token = root_authentication_example()
```

### Asynchronous Root Authentication

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_root_authentication():
    """Async root user authentication"""
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate as root user
            token = await db.signin({
                "username": "root",
                "password": "root"
            })
            
            print("✅ Async root authentication successful")
            
            # Select namespace and database
            await db.use("mycompany", "production")
            
            # Verify authentication
            user_info = await db.info()
            print(f"Authenticated as: {user_info}")
            
            # Perform operations
            users = await db.select("user")
            print(f"Found {len(users)} users")
            
            return token
            
        except Exception as e:
            print(f"❌ Async root authentication failed: {e}")
            raise

# Run async example
asyncio.run(async_root_authentication())
```

## Namespace User Authentication

Namespace users can access all databases within a specific namespace.

### Creating Namespace Users

```python
from surrealdb import Surreal

def create_namespace_user():
    """Create a namespace user (requires root access)"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Authenticate as root to create users
        db.signin({"username": "root", "password": "root"})
        
        # Create namespace user with OWNER role
        db.query("""
            DEFINE USER namespace_admin ON NAMESPACE mycompany 
            PASSWORD 'secure_ns_password123' 
            ROLES OWNER;
        """)
        
        print("✅ Namespace user 'namespace_admin' created")
        
        # Create namespace user with EDITOR role
        db.query("""
            DEFINE USER namespace_editor ON NAMESPACE mycompany 
            PASSWORD 'editor_password123' 
            ROLES EDITOR;
        """)
        
        print("✅ Namespace user 'namespace_editor' created")

def namespace_authentication_example():
    """Authenticate as namespace user"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate as namespace user
            token = db.signin({
                "namespace": "mycompany",
                "username": "namespace_admin",
                "password": "secure_ns_password123"
            })
            
            print("✅ Namespace authentication successful")
            
            # Can access any database in this namespace
            db.use("mycompany", "production")
            
            # Verify access
            user_info = db.info()
            print(f"Namespace user info: {user_info}")
            
            # Can create databases in this namespace
            db.query("DEFINE DATABASE new_db;")
            print("✅ Created new database in namespace")
            
            return token
            
        except Exception as e:
            print(f"❌ Namespace authentication failed: {e}")
            raise

# Setup and test
create_namespace_user()
namespace_token = namespace_authentication_example()
```

## Database User Authentication

Database users have access to a specific database within a namespace.

### Creating Database Users

```python
from surrealdb import Surreal

def create_database_user():
    """Create a database user (requires namespace or root access)"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Authenticate as root
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Create database user with OWNER role
        db.query("""
            DEFINE USER db_admin ON DATABASE 
            PASSWORD 'secure_db_password123' 
            ROLES OWNER;
        """)
        
        print("✅ Database user 'db_admin' created")
        
        # Create database user with EDITOR role
        db.query("""
            DEFINE USER db_editor ON DATABASE 
            PASSWORD 'editor_db_password123' 
            ROLES EDITOR;
        """)
        
        print("✅ Database user 'db_editor' created")

def database_authentication_example():
    """Authenticate as database user"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Authenticate as database user
            token = db.signin({
                "namespace": "mycompany",
                "database": "production",
                "username": "db_admin",
                "password": "secure_db_password123"
            })
            
            print("✅ Database authentication successful")
            
            # Already connected to the specific database
            user_info = db.info()
            print(f"Database user info: {user_info}")
            
            # Can perform database operations
            tables = db.query("INFO FOR DB;")
            print(f"Database info: {tables}")
            
            # Can create tables
            db.query("""
                DEFINE TABLE user SCHEMAFULL
                PERMISSIONS 
                    FOR select, update WHERE id = $auth
                    FOR create, delete WHERE $auth.role = 'admin';
            """)
            
            print("✅ Created user table with permissions")
            
            return token
            
        except Exception as e:
            print(f"❌ Database authentication failed: {e}")
            raise

# Setup and test
create_database_user()
db_token = database_authentication_example()
```

## Scope User Authentication

Scope users are application end-users with custom authentication logic.

### Setting Up User Scope

```python
from surrealdb import Surreal

def setup_user_scope():
    """Setup user scope for application authentication"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Authenticate as root to setup scope
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define user scope with email/password authentication
        db.query("""
            DEFINE SCOPE user SESSION 24h
            SIGNUP ( 
                CREATE user SET 
                    email = $email, 
                    pass = crypto::argon2::generate($pass), 
                    name = $name, 
                    role = 'user',
                    created_at = time::now(),
                    active = true
            )
            SIGNIN ( 
                SELECT * FROM user 
                WHERE email = $email 
                AND crypto::argon2::compare(pass, $pass)
                AND active = true
            );
        """)
        
        print("✅ User scope defined with signup/signin logic")
        
        # Define admin scope
        db.query("""
            DEFINE SCOPE admin SESSION 8h
            SIGNIN ( 
                SELECT * FROM user 
                WHERE email = $email 
                AND crypto::argon2::compare(pass, $pass)
                AND role = 'admin'
                AND active = true
            );
        """)
        
        print("✅ Admin scope defined")

def user_signup_example():
    """Sign up new user with scope authentication"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Select namespace and database
            db.use("mycompany", "production")
            
            # Sign up new user
            token = db.signup({
                "namespace": "mycompany",
                "database": "production",
                "scope": "user",
                "email": "john.doe@example.com",
                "password": "SecurePassword123!",
                "name": "John Doe"
            })
            
            print("✅ User signup successful")
            print(f"User token: {token[:50]}..." if token else "No token returned")
            
            # Verify user creation
            user_info = db.info()
            print(f"New user info: {user_info}")
            
            return token
            
        except Exception as e:
            print(f"❌ User signup failed: {e}")
            raise

def user_signin_example():
    """Sign in existing user with scope authentication"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        try:
            # Select namespace and database
            db.use("mycompany", "production")
            
            # Sign in existing user
            token = db.signin({
                "namespace": "mycompany",
                "database": "production",
                "scope": "user",
                "email": "john.doe@example.com",
                "password": "SecurePassword123!"
            })
            
            print("✅ User signin successful")
            print(f"User token: {token[:50]}..." if token else "No token returned")
            
            # Verify authentication
            user_info = db.info()
            print(f"Signed in user: {user_info}")
            
            # User can access their own data
            user_data = db.query("SELECT * FROM user WHERE id = $auth;")
            print(f"User's own data: {user_data}")
            
            return token
            
        except Exception as e:
            print(f"❌ User signin failed: {e}")
            raise

# Setup and test scope authentication
setup_user_scope()
signup_token = user_signup_example()
signin_token = user_signin_example()
```

## Advanced Scope Examples

### Multi-Role Scope System

```python
from surrealdb import Surreal

def setup_multi_role_scope():
    """Setup scope with multiple user roles"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define comprehensive user scope
        db.query("""
            DEFINE SCOPE user SESSION 24h
            SIGNUP ( 
                CREATE user SET 
                    email = $email, 
                    pass = crypto::argon2::generate($pass), 
                    name = $name,
                    role = $role OR 'user',
                    department = $department,
                    permissions = $permissions OR ['read'],
                    created_at = time::now(),
                    active = true,
                    last_login = NONE
            )
            SIGNIN ( 
                LET $user = (
                    SELECT * FROM user 
                    WHERE email = $email 
                    AND crypto::argon2::compare(pass, $pass)
                    AND active = true
                );
                
                IF $user {
                    UPDATE $user.id SET last_login = time::now();
                    RETURN $user;
                } ELSE {
                    THROW "Invalid credentials or inactive user";
                };
            );
        """)
        
        print("✅ Multi-role user scope defined")

def create_admin_user():
    """Create an admin user through scope signup"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Sign up admin user
        admin_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "admin@company.com",
            "password": "AdminPassword123!",
            "name": "System Administrator",
            "role": "admin",
            "department": "IT",
            "permissions": ["read", "write", "delete", "admin"]
        })
        
        print("✅ Admin user created")
        return admin_token

def create_manager_user():
    """Create a manager user through scope signup"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Sign up manager user
        manager_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "manager@company.com",
            "password": "ManagerPassword123!",
            "name": "Department Manager",
            "role": "manager",
            "department": "Sales",
            "permissions": ["read", "write", "manage_team"]
        })
        
        print("✅ Manager user created")
        return manager_token

# Setup multi-role system
setup_multi_role_scope()
admin_token = create_admin_user()
manager_token = create_manager_user()
```

## Error Handling and Best Practices

### Robust Authentication Function

```python
from surrealdb import Surreal
import os
import logging

def authenticate_user(credentials, connection_url=None):
    """Robust user authentication with error handling"""
    
    url = connection_url or os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
    
    try:
        with Surreal(url) as db:
            # Attempt authentication
            token = db.signin(credentials)
            
            # Verify authentication worked
            user_info = db.info()
            
            if not user_info:
                raise Exception("Authentication succeeded but no user info returned")
            
            logging.info(f"User authenticated: {user_info.get('email', 'unknown')}")
            
            return {
                "success": True,
                "token": token,
                "user_info": user_info
            }
            
    except Exception as e:
        logging.error(f"Authentication failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "token": None,
            "user_info": None
        }

def safe_database_operation(credentials, operation):
    """Safely execute database operation with authentication"""
    
    auth_result = authenticate_user(credentials)
    
    if not auth_result["success"]:
        raise Exception(f"Authentication failed: {auth_result['error']}")
    
    try:
        with Surreal(os.getenv("SURREALDB_URL")) as db:
            db.authenticate(auth_result["token"])
            
            # Execute the operation
            result = operation(db)
            
            return {
                "success": True,
                "data": result,
                "user": auth_result["user_info"]
            }
            
    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

# Example usage
def example_safe_operations():
    """Example of safe authentication and operations"""
    
    # User credentials
    user_creds = {
        "namespace": "mycompany",
        "database": "production",
        "scope": "user",
        "email": "john.doe@example.com",
        "password": "SecurePassword123!"
    }
    
    # Define operation
    def get_user_profile(db):
        return db.query("SELECT * FROM user WHERE id = $auth;")
    
    # Execute safely
    result = safe_database_operation(user_creds, get_user_profile)
    
    if result["success"]:
        print(f"✅ Operation successful for user: {result['user']['email']}")
        print(f"Profile data: {result['data']}")
    else:
        print(f"❌ Operation failed: {result['error']}")

# Run example
example_safe_operations()
```

## Configuration Management

### Environment-Based Configuration

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AuthConfig:
    """Authentication configuration"""
    url: str
    namespace: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    scope: Optional[str] = None
    email: Optional[str] = None

def load_auth_config() -> AuthConfig:
    """Load authentication configuration from environment"""
    
    return AuthConfig(
        url=os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
        namespace=os.getenv("SURREALDB_NS", "myapp"),
        database=os.getenv("SURREALDB_DB", "production"),
        username=os.getenv("SURREALDB_USER"),
        password=os.getenv("SURREALDB_PASS"),
        scope=os.getenv("SURREALDB_SCOPE"),
        email=os.getenv("SURREALDB_EMAIL")
    )

def authenticate_with_config(config: AuthConfig) -> dict:
    """Authenticate using configuration"""
    
    with Surreal(config.url) as db:
        if config.scope:
            # Scope authentication
            credentials = {
                "namespace": config.namespace,
                "database": config.database,
                "scope": config.scope,
                "email": config.email,
                "password": config.password
            }
        else:
            # System user authentication
            credentials = {
                "username": config.username,
                "password": config.password
            }
        
        token = db.signin(credentials)
        
        if not config.scope:
            db.use(config.namespace, config.database)
        
        user_info = db.info()
        
        return {
            "token": token,
            "user_info": user_info,
            "config": config
        }

# Example usage
config = load_auth_config()
auth_result = authenticate_with_config(config)
print(f"✅ Authenticated with config: {auth_result['user_info']}")
```

## Next Steps

Now that you understand basic authentication, explore more advanced topics:

- **[JWT Authentication](./jwt-auth.md)** - Token-based authentication
- **[GitHub SSO](./github-sso.md)** - OAuth integration
- **[Auth0 Integration](./auth0.md)** - Enterprise SSO
- **[Custom Scopes](./custom-scopes.md)** - Advanced user management

## Common Issues and Solutions

### Issue: "Authentication failed"

**Cause:** Incorrect credentials or user doesn't exist

**Solution:**
```python
# Verify user exists and credentials are correct
try:
    token = db.signin(credentials)
except Exception as e:
    if "authentication failed" in str(e).lower():
        print("Check username/password or create user first")
    raise
```

### Issue: "Scope not found"

**Cause:** Scope hasn't been defined

**Solution:**
```python
# Define scope before using it
db.query("""
    DEFINE SCOPE user SESSION 24h
    SIGNIN (SELECT * FROM user WHERE email = $email AND pass = $pass);
""")
```

### Issue: "Permission denied"

**Cause:** User doesn't have required permissions

**Solution:**
```python
# Check user permissions
user_info = db.info()
print(f"User permissions: {user_info}")

# Use appropriate user level for operation
```

Ready for more advanced authentication? Continue with [JWT Authentication](./jwt-auth.md).