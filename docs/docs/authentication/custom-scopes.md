---
sidebar_position: 6
---

# Custom Scopes

Learn how to create and manage custom authentication scopes in SurrealDB for advanced user management, role-based access control, and application-specific authentication logic.

## Overview

Custom scopes provide:

- **Flexible Authentication** - Define custom signin/signup logic
- **Role-Based Access** - Implement granular permissions
- **Business Logic** - Embed authentication rules
- **Multi-Tenant Support** - Isolate users by organization
- **Custom Fields** - Store application-specific user data

## Basic Custom Scope

### Simple User Scope

```python
from surrealdb import Surreal
from datetime import datetime

def create_basic_user_scope():
    """Create a basic user authentication scope"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Authenticate as root to define scope
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define basic user scope
        db.query("""
            DEFINE SCOPE user SESSION 24h
            SIGNUP ( 
                CREATE user SET 
                    email = $email, 
                    pass = crypto::argon2::generate($pass), 
                    name = $name,
                    created_at = time::now(),
                    active = true,
                    role = 'user'
            )
            SIGNIN ( 
                SELECT * FROM user 
                WHERE email = $email 
                AND crypto::argon2::compare(pass, $pass)
                AND active = true
            );
        """)
        
        print("✅ Basic user scope created")

def test_basic_scope():
    """Test the basic user scope"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Sign up new user
        signup_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        })
        
        print(f"✅ User signed up: {signup_token[:50]}...")
        
        # Sign in existing user
        signin_token = db.signin({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        
        print(f"✅ User signed in: {signin_token[:50]}...")
        
        # Get user info
        user_info = db.info()
        print(f"User info: {user_info}")
        
        return signin_token

# Create and test basic scope
create_basic_user_scope()
test_token = test_basic_scope()
```

## Advanced Custom Scopes

### Multi-Role Scope System

```python
from surrealdb import Surreal

def create_advanced_user_scope():
    """Create advanced user scope with roles and permissions"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define role table first
        db.query("""
            DEFINE TABLE role SCHEMAFULL;
            DEFINE FIELD name ON TABLE role TYPE string;
            DEFINE FIELD permissions ON TABLE role TYPE array<string>;
            DEFINE FIELD description ON TABLE role TYPE string;
            DEFINE FIELD created_at ON TABLE role TYPE datetime DEFAULT time::now();
        """)
        
        # Create default roles
        db.query("""
            INSERT INTO role [
                {
                    name: 'admin',
                    permissions: ['read', 'write', 'delete', 'admin', 'manage_users'],
                    description: 'Full system access'
                },
                {
                    name: 'manager',
                    permissions: ['read', 'write', 'manage_team'],
                    description: 'Team management access'
                },
                {
                    name: 'user',
                    permissions: ['read', 'write_own'],
                    description: 'Standard user access'
                },
                {
                    name: 'viewer',
                    permissions: ['read'],
                    description: 'Read-only access'
                }
            ];
        """)
        
        # Define advanced user scope
        db.query("""
            DEFINE SCOPE user SESSION 24h
            SIGNUP ( 
                LET $role = (SELECT * FROM role WHERE name = ($role OR 'user') LIMIT 1);
                
                IF !$role {
                    THROW "Invalid role specified";
                };
                
                CREATE user SET 
                    email = $email, 
                    pass = crypto::argon2::generate($pass), 
                    name = $name,
                    role = $role[0].name,
                    permissions = $role[0].permissions,
                    department = $department,
                    phone = $phone,
                    created_at = time::now(),
                    updated_at = time::now(),
                    active = true,
                    email_verified = false,
                    last_login = NONE,
                    login_count = 0,
                    metadata = $metadata OR {}
            )
            SIGNIN ( 
                LET $user = (
                    SELECT * FROM user 
                    WHERE email = $email 
                    AND crypto::argon2::compare(pass, $pass)
                    AND active = true
                );
                
                IF !$user {
                    THROW "Invalid credentials or inactive user";
                };
                
                -- Update login tracking
                UPDATE $user[0].id SET 
                    last_login = time::now(),
                    login_count += 1,
                    updated_at = time::now();
                
                RETURN $user[0];
            );
        """)
        
        print("✅ Advanced user scope with roles created")

def create_organization_scope():
    """Create organization-specific scope"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define organization table
        db.query("""
            DEFINE TABLE organization SCHEMAFULL;
            DEFINE FIELD name ON TABLE organization TYPE string;
            DEFINE FIELD domain ON TABLE organization TYPE string;
            DEFINE FIELD settings ON TABLE organization TYPE object;
            DEFINE FIELD active ON TABLE organization TYPE bool DEFAULT true;
            DEFINE FIELD created_at ON TABLE organization TYPE datetime DEFAULT time::now();
        """)
        
        # Define organization scope
        db.query("""
            DEFINE SCOPE organization SESSION 8h
            SIGNUP (
                -- Verify organization exists and is active
                LET $org = (SELECT * FROM organization WHERE domain = $domain AND active = true LIMIT 1);
                
                IF !$org {
                    THROW "Organization not found or inactive";
                };
                
                -- Create user with organization context
                CREATE user SET 
                    email = $email,
                    pass = crypto::argon2::generate($pass),
                    name = $name,
                    organization = $org[0].id,
                    role = $role OR 'member',
                    department = $department,
                    created_at = time::now(),
                    active = true,
                    org_domain = $domain
            )
            SIGNIN (
                -- Verify organization and user
                LET $org = (SELECT * FROM organization WHERE domain = $domain AND active = true LIMIT 1);
                
                IF !$org {
                    THROW "Organization not found or inactive";
                };
                
                LET $user = (
                    SELECT * FROM user 
                    WHERE email = $email 
                    AND crypto::argon2::compare(pass, $pass)
                    AND organization = $org[0].id
                    AND active = true
                );
                
                IF !$user {
                    THROW "Invalid credentials or user not in organization";
                };
                
                UPDATE $user[0].id SET last_login = time::now();
                RETURN $user[0];
            );
        """)
        
        print("✅ Organization scope created")

def test_advanced_scopes():
    """Test advanced scope functionality"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Test user scope with role
        admin_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "admin@company.com",
            "password": "AdminPass123!",
            "name": "System Admin",
            "role": "admin",
            "department": "IT"
        })
        
        print(f"✅ Admin user created: {admin_token[:50]}...")
        
        # Test manager signup
        manager_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "user",
            "email": "manager@company.com",
            "password": "ManagerPass123!",
            "name": "Team Manager",
            "role": "manager",
            "department": "Sales",
            "metadata": {"team_size": 5, "region": "North"}
        })
        
        print(f"✅ Manager user created: {manager_token[:50]}...")
        
        # Get user info to verify roles
        user_info = db.info()
        print(f"Manager info: {user_info}")
        
        return admin_token, manager_token

# Create and test advanced scopes
create_advanced_user_scope()
create_organization_scope()
admin_token, manager_token = test_advanced_scopes()
```

## Permission-Based Access Control

### Granular Permissions System

```python
from surrealdb import Surreal

def create_permission_system():
    """Create comprehensive permission system"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define permission table
        db.query("""
            DEFINE TABLE permission SCHEMAFULL;
            DEFINE FIELD name ON TABLE permission TYPE string;
            DEFINE FIELD resource ON TABLE permission TYPE string;
            DEFINE FIELD action ON TABLE permission TYPE string;
            DEFINE FIELD description ON TABLE permission TYPE string;
        """)
        
        # Create permissions
        db.query("""
            INSERT INTO permission [
                { name: 'users.read', resource: 'users', action: 'read', description: 'Read user data' },
                { name: 'users.write', resource: 'users', action: 'write', description: 'Create/update users' },
                { name: 'users.delete', resource: 'users', action: 'delete', description: 'Delete users' },
                { name: 'posts.read', resource: 'posts', action: 'read', description: 'Read posts' },
                { name: 'posts.write', resource: 'posts', action: 'write', description: 'Create/update posts' },
                { name: 'posts.delete', resource: 'posts', action: 'delete', description: 'Delete posts' },
                { name: 'admin.system', resource: 'system', action: 'admin', description: 'System administration' }
            ];
        """)
        
        # Define role-permission mapping table
        db.query("""
            DEFINE TABLE role_permission SCHEMAFULL;
            DEFINE FIELD role ON TABLE role_permission TYPE string;
            DEFINE FIELD permission ON TABLE role_permission TYPE string;
        """)
        
        # Map permissions to roles
        db.query("""
            INSERT INTO role_permission [
                { role: 'admin', permission: 'users.read' },
                { role: 'admin', permission: 'users.write' },
                { role: 'admin', permission: 'users.delete' },
                { role: 'admin', permission: 'posts.read' },
                { role: 'admin', permission: 'posts.write' },
                { role: 'admin', permission: 'posts.delete' },
                { role: 'admin', permission: 'admin.system' },
                
                { role: 'manager', permission: 'users.read' },
                { role: 'manager', permission: 'users.write' },
                { role: 'manager', permission: 'posts.read' },
                { role: 'manager', permission: 'posts.write' },
                
                { role: 'user', permission: 'posts.read' },
                { role: 'user', permission: 'posts.write' },
                
                { role: 'viewer', permission: 'posts.read' }
            ];
        """)
        
        # Define permission-aware scope
        db.query("""
            DEFINE SCOPE rbac SESSION 24h
            SIGNUP (
                LET $role_perms = (
                    SELECT permission FROM role_permission WHERE role = ($role OR 'user')
                );
                
                CREATE user SET 
                    email = $email,
                    pass = crypto::argon2::generate($pass),
                    name = $name,
                    role = $role OR 'user',
                    permissions = $role_perms.permission,
                    created_at = time::now(),
                    active = true
            )
            SIGNIN (
                LET $user = (
                    SELECT * FROM user 
                    WHERE email = $email 
                    AND crypto::argon2::compare(pass, $pass)
                    AND active = true
                );
                
                IF !$user {
                    THROW "Invalid credentials";
                };
                
                -- Refresh permissions based on current role
                LET $role_perms = (
                    SELECT permission FROM role_permission WHERE role = $user[0].role
                );
                
                UPDATE $user[0].id SET 
                    permissions = $role_perms.permission,
                    last_login = time::now();
                
                RETURN $user[0];
            );
        """)
        
        print("✅ Permission system created")

def create_resource_tables_with_permissions():
    """Create tables with permission-based access"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define posts table with permissions
        db.query("""
            DEFINE TABLE post SCHEMAFULL
            PERMISSIONS 
                FOR select WHERE 'posts.read' IN $auth.permissions
                FOR create WHERE 'posts.write' IN $auth.permissions
                FOR update WHERE 'posts.write' IN $auth.permissions OR id = $auth.id
                FOR delete WHERE 'posts.delete' IN $auth.permissions OR author = $auth.id;
                
            DEFINE FIELD title ON TABLE post TYPE string;
            DEFINE FIELD content ON TABLE post TYPE string;
            DEFINE FIELD author ON TABLE post TYPE record(user);
            DEFINE FIELD created_at ON TABLE post TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE post TYPE datetime DEFAULT time::now();
        """)
        
        # Define user management table
        db.query("""
            DEFINE TABLE user_profile SCHEMAFULL
            PERMISSIONS 
                FOR select WHERE 'users.read' IN $auth.permissions OR id = $auth.id
                FOR create WHERE 'users.write' IN $auth.permissions
                FOR update WHERE 'users.write' IN $auth.permissions OR id = $auth.id
                FOR delete WHERE 'users.delete' IN $auth.permissions;
                
            DEFINE FIELD user ON TABLE user_profile TYPE record(user);
            DEFINE FIELD bio ON TABLE user_profile TYPE string;
            DEFINE FIELD avatar ON TABLE user_profile TYPE string;
            DEFINE FIELD social_links ON TABLE user_profile TYPE object;
        """)
        
        print("✅ Resource tables with permissions created")

def test_permission_system():
    """Test permission-based access control"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Create users with different roles
        admin_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "rbac",
            "email": "admin@test.com",
            "password": "AdminPass123!",
            "name": "Admin User",
            "role": "admin"
        })
        
        user_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "rbac",
            "email": "user@test.com",
            "password": "UserPass123!",
            "name": "Regular User",
            "role": "user"
        })
        
        print("✅ RBAC users created")
        
        # Test admin permissions
        db.authenticate(admin_token)
        admin_info = db.info()
        print(f"Admin permissions: {admin_info['permissions']}")
        
        # Admin can create posts
        admin_post = db.create("post", {
            "title": "Admin Post",
            "content": "This is an admin post",
            "author": admin_info["id"]
        })
        print(f"✅ Admin created post: {admin_post[0]['id']}")
        
        # Test user permissions
        db.authenticate(user_token)
        user_info = db.info()
        print(f"User permissions: {user_info['permissions']}")
        
        # User can create posts
        user_post = db.create("post", {
            "title": "User Post",
            "content": "This is a user post",
            "author": user_info["id"]
        })
        print(f"✅ User created post: {user_post[0]['id']}")
        
        # User can read posts
        posts = db.select("post")
        print(f"✅ User can read {len(posts)} posts")
        
        return admin_token, user_token

# Create and test permission system
create_permission_system()
create_resource_tables_with_permissions()
admin_token, user_token = test_permission_system()
```

## Multi-Tenant Scopes

### Tenant Isolation

```python
from surrealdb import Surreal

def create_multi_tenant_system():
    """Create multi-tenant authentication system"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define tenant table
        db.query("""
            DEFINE TABLE tenant SCHEMAFULL;
            DEFINE FIELD name ON TABLE tenant TYPE string;
            DEFINE FIELD domain ON TABLE tenant TYPE string;
            DEFINE FIELD subdomain ON TABLE tenant TYPE string;
            DEFINE FIELD settings ON TABLE tenant TYPE object;
            DEFINE FIELD plan ON TABLE tenant TYPE string DEFAULT 'basic';
            DEFINE FIELD active ON TABLE tenant TYPE bool DEFAULT true;
            DEFINE FIELD created_at ON TABLE tenant TYPE datetime DEFAULT time::now();
            
            DEFINE INDEX tenant_domain ON TABLE tenant COLUMNS domain UNIQUE;
            DEFINE INDEX tenant_subdomain ON TABLE tenant COLUMNS subdomain UNIQUE;
        """)
        
        # Create sample tenants
        db.query("""
            INSERT INTO tenant [
                {
                    name: 'Acme Corp',
                    domain: 'acme.com',
                    subdomain: 'acme',
                    plan: 'enterprise',
                    settings: {
                        max_users: 1000,
                        features: ['sso', 'audit_logs', 'custom_branding']
                    }
                },
                {
                    name: 'StartupXYZ',
                    domain: 'startupxyz.com',
                    subdomain: 'startupxyz',
                    plan: 'pro',
                    settings: {
                        max_users: 100,
                        features: ['team_management', 'analytics']
                    }
                }
            ];
        """)
        
        # Define tenant scope
        db.query("""
            DEFINE SCOPE tenant SESSION 24h
            SIGNUP (
                -- Verify tenant exists and is active
                LET $tenant = (
                    SELECT * FROM tenant 
                    WHERE (domain = $tenant_domain OR subdomain = $tenant_subdomain)
                    AND active = true 
                    LIMIT 1
                );
                
                IF !$tenant {
                    THROW "Tenant not found or inactive";
                };
                
                -- Check user limit
                LET $user_count = (
                    SELECT count() FROM user 
                    WHERE tenant = $tenant[0].id 
                    GROUP ALL
                )[0].count;
                
                IF $user_count >= $tenant[0].settings.max_users {
                    THROW "User limit reached for tenant";
                };
                
                -- Create user with tenant context
                CREATE user SET 
                    email = $email,
                    pass = crypto::argon2::generate($pass),
                    name = $name,
                    tenant = $tenant[0].id,
                    tenant_domain = $tenant[0].domain,
                    role = $role OR 'user',
                    department = $department,
                    created_at = time::now(),
                    active = true
            )
            SIGNIN (
                -- Verify tenant
                LET $tenant = (
                    SELECT * FROM tenant 
                    WHERE (domain = $tenant_domain OR subdomain = $tenant_subdomain)
                    AND active = true 
                    LIMIT 1
                );
                
                IF !$tenant {
                    THROW "Tenant not found or inactive";
                };
                
                -- Verify user belongs to tenant
                LET $user = (
                    SELECT * FROM user 
                    WHERE email = $email 
                    AND crypto::argon2::compare(pass, $pass)
                    AND tenant = $tenant[0].id
                    AND active = true
                );
                
                IF !$user {
                    THROW "Invalid credentials or user not in tenant";
                };
                
                UPDATE $user[0].id SET last_login = time::now();
                RETURN $user[0];
            );
        """)
        
        print("✅ Multi-tenant system created")

def create_tenant_isolated_tables():
    """Create tables with tenant isolation"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("mycompany", "production")
        
        # Define tenant-isolated data table
        db.query("""
            DEFINE TABLE tenant_data SCHEMAFULL
            PERMISSIONS 
                FOR select, create, update, delete WHERE tenant = $auth.tenant;
                
            DEFINE FIELD tenant ON TABLE tenant_data TYPE record(tenant);
            DEFINE FIELD name ON TABLE tenant_data TYPE string;
            DEFINE FIELD data ON TABLE tenant_data TYPE object;
            DEFINE FIELD created_by ON TABLE tenant_data TYPE record(user);
            DEFINE FIELD created_at ON TABLE tenant_data TYPE datetime DEFAULT time::now();
        """)
        
        # Define tenant-specific posts
        db.query("""
            DEFINE TABLE tenant_post SCHEMAFULL
            PERMISSIONS 
                FOR select, create, update WHERE tenant = $auth.tenant
                FOR delete WHERE tenant = $auth.tenant AND (author = $auth.id OR $auth.role = 'admin');
                
            DEFINE FIELD tenant ON TABLE tenant_post TYPE record(tenant);
            DEFINE FIELD title ON TABLE tenant_post TYPE string;
            DEFINE FIELD content ON TABLE tenant_post TYPE string;
            DEFINE FIELD author ON TABLE tenant_post TYPE record(user);
            DEFINE FIELD created_at ON TABLE tenant_post TYPE datetime DEFAULT time::now();
        """)
        
        print("✅ Tenant-isolated tables created")

def test_multi_tenant_system():
    """Test multi-tenant functionality"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.use("mycompany", "production")
        
        # Create users in different tenants
        acme_user_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "tenant",
            "tenant_domain": "acme.com",
            "email": "user@acme.com",
            "password": "AcmePass123!",
            "name": "Acme User",
            "role": "user"
        })
        
        startup_user_token = db.signup({
            "namespace": "mycompany",
            "database": "production",
            "scope": "tenant",
            "tenant_subdomain": "startupxyz",
            "email": "user@startupxyz.com",
            "password": "StartupPass123!",
            "name": "Startup User",
            "role": "user"
        })
        
        print("✅ Multi-tenant users created")
        
        # Test tenant isolation
        db.authenticate(acme_user_token)
        acme_info = db.info()
        print(f"Acme user tenant: {acme_info['tenant_domain']}")
        
        # Create tenant-specific data
        acme_post = db.create("tenant_post", {
            "tenant": acme_info["tenant"],
            "title": "Acme Post",
            "content": "This is an Acme post",
            "author": acme_info["id"]
        })
        print(f"✅ Acme post created: {acme_post[0]['id']}")
        
        # Switch to startup user
        db.authenticate(startup_user_token)
        startup_info = db.info()
        print(f"Startup user tenant: {startup_info['tenant_domain']}")
        
        # Startup user can't see Acme posts
        startup_posts = db.select("tenant_post")
        print(f"Startup user sees {len(startup_posts)} posts (should be 0)")
        
        # Create startup post
        startup_post = db.create("tenant_post", {
            "tenant": startup_info["tenant"],
            "title": "Startup Post",
            "content": "This is a startup post",
            "author": startup_info["id"]
        })
        print(f"✅ Startup post created: {startup_post[0]['id']}")
        
        return acme_user_token, startup_user_token

# Create and test multi-tenant system
create_multi_tenant_system()
create_tenant_isolated_tables()
acme_token, startup_token = test_multi_tenant_system()
```

## Scope Management Utilities

### Scope Administration Tools

```python
from surrealdb import Surreal
from typing import List, Dict, Any

class ScopeManager:
    """Utility class for managing custom scopes"""
    
    def __init__(self, db_url: str, namespace: str, database: str):
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
    
    def get_admin_connection(self):
        """Get admin database connection"""
        db = Surreal(self.db_url)
        db.signin({"username": "root", "password": "root"})
        db.use(self.namespace, self.database)
        return db
    
    def list_scopes(self) -> List[Dict[str, Any]]:
        """List all defined scopes"""
        
        with self.get_admin_connection() as db:
            result = db.query("INFO FOR DB;")
            
            scopes = []
            if result and "scopes" in result[0]:
                for scope_name, scope_info in result[0]["scopes"].items():
                    scopes.append({
                        "name": scope_name,
                        "session": scope_info.get("session"),
                        "signup": bool(scope_info.get("signup")),
                        "signin": bool(scope_info.get("signin"))
                    })
            
            return scopes
    
    def create_scope(self, name: str, session_duration: str, signup_logic: str, signin_logic: str):
        """Create a new scope"""
        
        with self.get_admin_connection() as db:
            scope_definition = f"""
                DEFINE SCOPE {name} SESSION {session_duration}
                SIGNUP ({signup_logic})
                SIGNIN ({signin_logic});
            """
            
            db.query(scope_definition)
            print(f"✅ Scope '{name}' created")
    
    def delete_scope(self, name: str):
        """Delete a scope"""
        
        with self.get_admin_connection() as db:
            db.query(f"REMOVE SCOPE {name};")
            print(f"✅ Scope '{name}' deleted")
    
    def test_scope_signup(self, scope_name: str, signup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test scope signup functionality"""
        
        try:
            with Surreal(self.db_url) as db:
                db.use(self.namespace, self.database)
                
                signup_params = {
                    "namespace": self.namespace,
                    "database": self.database,
                    "scope": scope_name,
                    **signup_data
                }
                
                token = db.signup(signup_params)
                
                return {
                    "success": True,
                    "token": token,
                    "message": f"Signup successful for scope '{scope_name}'"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Signup failed for scope '{scope_name}'"
            }
    
    def test_scope_signin(self, scope_name: str, signin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test scope signin functionality"""
        
        try:
            with Surreal(self.db_url) as db:
                db.use(self.namespace, self.database)
                
                signin_params = {
                    "namespace": self.namespace,
                    "database": self.database,
                    "scope": scope_name,
                    **signin_data
                }
                
                token = db.signin(signin_params)
                user_info = db.info()
                
                return {
                    "success": True,
                    "token": token,
                    "user_info": user_info,
                    "message": f"Signin successful for scope '{scope_name}'"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Signin failed for scope '{scope_name}'"
            }
    
    def get_scope_users(self, scope_name: str) -> List[Dict[str, Any]]:
        """Get users for a specific scope"""
        
        with self.get_admin_connection() as db:
            # This assumes users have a 'scope' field or similar identifier
            users = db.query(f"SELECT * FROM user WHERE scope = '{scope_name}' OR provider = '{scope_name}';")
            return users
    
    def cleanup_inactive_users(self, scope_name: str, days_inactive: int = 30):
        """Clean up inactive users from a scope"""
        
        with self.get_admin_connection() as db:
            cutoff_date = f"time::now() - {days_inactive}d"
            
            result = db.query(f"""
                DELETE FROM user 
                WHERE (scope = '{scope_name}' OR provider = '{scope_name}')
                AND (last_login < {cutoff_date} OR last_login IS NONE)
                AND