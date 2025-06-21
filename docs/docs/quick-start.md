---
sidebar_position: 3
---

# Quick Start

Get up and running with SurrealDB Python SDK in minutes! This guide will walk you through creating your first SurrealDB application.

## Prerequisites

Before starting, make sure you have:

- ✅ Python 3.8+ installed
- ✅ SurrealDB Python SDK installed (`pip install surrealdb`)
- ✅ SurrealDB server running (see [Installation Guide](./installation.md))

## Your First SurrealDB Application

Let's build a simple application that manages a collection of users.

### Step 1: Import and Connect

```python
from surrealdb import Surreal

# Connect to SurrealDB
with Surreal("ws://localhost:8000/rpc") as db:
    # Authenticate
    db.signin({"username": "root", "password": "root"})
    
    # Select namespace and database
    db.use("quickstart", "users_app")
    
    print("✅ Connected to SurrealDB!")
```

### Step 2: Create Records

```python
from surrealdb import Surreal

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("quickstart", "users_app")
    
    # Create a single user
    user = db.create("user", {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "active": True,
        "tags": ["developer", "python"]
    })
    
    print(f"Created user: {user}")
    
    # Create multiple users at once
    users = db.insert("user", [
        {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 28,
            "active": True,
            "tags": ["designer", "ui/ux"]
        },
        {
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "age": 35,
            "active": False,
            "tags": ["manager", "team-lead"]
        }
    ])
    
    print(f"Created {len(users)} users")
```

### Step 3: Read Records

```python
from surrealdb import Surreal

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("quickstart", "users_app")
    
    # Select all users
    all_users = db.select("user")
    print(f"All users: {all_users}")
    
    # Select a specific user by ID
    if all_users:
        user_id = all_users[0]["id"]
        specific_user = db.select(user_id)
        print(f"Specific user: {specific_user}")
    
    # Query with SurrealQL
    active_users = db.query("SELECT * FROM user WHERE active = true")
    print(f"Active users: {active_users}")
```

### Step 4: Update Records

```python
from surrealdb import Surreal

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("quickstart", "users_app")
    
    # Update a specific user (replace entire record)
    updated_user = db.update("user:john", {
        "name": "John Doe Jr.",
        "email": "john.jr@example.com",
        "age": 31,
        "active": True,
        "tags": ["senior-developer", "python", "javascript"]
    })
    
    # Merge data (partial update)
    merged_user = db.merge("user:jane", {
        "age": 29,
        "tags": ["senior-designer", "ui/ux", "product"]
    })
    
    # Patch with JSON Patch operations
    patched_user = db.patch("user:bob", [
        {"op": "replace", "path": "/active", "value": True},
        {"op": "add", "path": "/tags/-", "value": "active-manager"}
    ])
    
    print("Users updated successfully!")
```

### Step 5: Delete Records

```python
from surrealdb import Surreal

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("quickstart", "users_app")
    
    # Delete a specific user
    deleted_user = db.delete("user:bob")
    print(f"Deleted user: {deleted_user}")
    
    # Delete all inactive users
    db.query("DELETE user WHERE active = false")
    
    print("Cleanup completed!")
```

## Complete Example

Here's a complete example that demonstrates all CRUD operations:

```python
from surrealdb import Surreal
from datetime import datetime

def main():
    """Complete CRUD example with SurrealDB"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        # Connect and authenticate
        db.signin({"username": "root", "password": "root"})
        db.use("quickstart", "blog_app")
        
        print("🚀 Starting SurrealDB Quick Start Example")
        
        # 1. CREATE - Add blog posts
        print("\n📝 Creating blog posts...")
        
        posts = db.insert("post", [
            {
                "title": "Getting Started with SurrealDB",
                "content": "SurrealDB is an amazing database...",
                "author": "John Doe",
                "published": True,
                "created_at": datetime.now().isoformat(),
                "tags": ["database", "tutorial"]
            },
            {
                "title": "Python and SurrealDB",
                "content": "Learn how to use SurrealDB with Python...",
                "author": "Jane Smith",
                "published": False,
                "created_at": datetime.now().isoformat(),
                "tags": ["python", "database", "sdk"]
            }
        ])
        
        print(f"✅ Created {len(posts)} posts")
        
        # 2. READ - Fetch posts
        print("\n📖 Reading posts...")
        
        all_posts = db.select("post")
        print(f"📊 Total posts: {len(all_posts)}")
        
        published_posts = db.query(
            "SELECT * FROM post WHERE published = $published",
            {"published": True}
        )
        print(f"📰 Published posts: {len(published_posts)}")
        
        # 3. UPDATE - Modify posts
        print("\n✏️ Updating posts...")
        
        if all_posts:
            post_id = all_posts[0]["id"]
            
            # Update with merge (partial update)
            updated_post = db.merge(post_id, {
                "published": True,
                "updated_at": datetime.now().isoformat()
            })
            
            print(f"✅ Updated post: {updated_post[0]['title']}")
        
        # 4. ADVANCED QUERIES
        print("\n🔍 Advanced queries...")
        
        # Query with aggregation
        stats = db.query("""
            SELECT 
                count() as total_posts,
                count(published = true) as published_count,
                array::unique(array::flatten(tags)) as all_tags
            FROM post
        """)
        
        print(f"📈 Blog stats: {stats[0]}")
        
        # Query with relationships
        db.query("""
            CREATE author:john SET name = "John Doe", email = "john@example.com";
            CREATE author:jane SET name = "Jane Smith", email = "jane@example.com";
            
            RELATE author:john->wrote->post WHERE author = "John Doe";
            RELATE author:jane->wrote->post WHERE author = "Jane Smith";
        """)
        
        authors_with_posts = db.query("""
            SELECT *, ->wrote->post as posts 
            FROM author
        """)
        
        print(f"👥 Authors with posts: {len(authors_with_posts)}")
        
        # 5. CLEANUP
        print("\n🧹 Cleaning up...")
        
        db.query("DELETE post")
        db.query("DELETE author")
        db.query("DELETE wrote")
        
        print("✅ Cleanup completed!")
        
    print("\n🎉 Quick start example completed successfully!")

if __name__ == "__main__":
    main()
```

## Async Version

For asynchronous applications, use `AsyncSurreal`:

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_example():
    """Async version of the quick start example"""
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("quickstart", "async_app")
        
        # Create
        user = await db.create("user", {
            "name": "Async User",
            "email": "async@example.com"
        })
        
        # Read
        users = await db.select("user")
        print(f"Users: {users}")
        
        # Update
        updated = await db.merge(user[0]["id"], {"active": True})
        
        # Delete
        await db.delete("user")
        
        print("Async example completed!")

# Run the async example
asyncio.run(async_example())
```

## Using Context Managers

The SDK supports context managers for automatic connection management:

```python
from surrealdb import Surreal

# Automatic connection and cleanup
with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("test", "test")
    
    # Your database operations here
    result = db.query("SELECT * FROM user")
    
# Connection is automatically closed when exiting the context
```

## Error Handling

Always handle potential errors:

```python
from surrealdb import Surreal
from surrealdb.errors import SurrealDBMethodError

try:
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("test", "test")
        
        result = db.create("user", {"name": "Test User"})
        print(f"Success: {result}")
        
except SurrealDBMethodError as e:
    print(f"SurrealDB error: {e}")
except ConnectionError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

Now that you've completed the quick start:

1. **[Learn about Connection Types](./connections/overview.md)** - Understand WebSocket vs HTTP connections
2. **[Explore Core Methods](./methods/overview.md)** - Deep dive into all available operations
3. **[Work with Data Types](./data-types/overview.md)** - Learn about SurrealDB's rich data types
4. **[Check out Examples](./examples/basic-crud.md)** - See more real-world examples
5. **[Read Best Practices](./advanced/best-practices.md)** - Learn how to build production-ready applications

## Common Patterns

### Configuration Management

```python
import os
from surrealdb import Surreal

# Use environment variables for configuration
DB_URL = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
DB_USER = os.getenv("SURREALDB_USER", "root")
DB_PASS = os.getenv("SURREALDB_PASS", "root")
DB_NAMESPACE = os.getenv("SURREALDB_NAMESPACE", "production")
DB_DATABASE = os.getenv("SURREALDB_DATABASE", "myapp")

with Surreal(DB_URL) as db:
    db.signin({"username": DB_USER, "password": DB_PASS})
    db.use(DB_NAMESPACE, DB_DATABASE)
    # Your application logic here
```

### Connection Pooling Pattern

```python
class DatabaseManager:
    def __init__(self, url, credentials, namespace, database):
        self.url = url
        self.credentials = credentials
        self.namespace = namespace
        self.database = database
    
    def get_connection(self):
        db = Surreal(self.url)
        db.signin(self.credentials)
        db.use(self.namespace, self.database)
        return db

# Usage
db_manager = DatabaseManager(
    "ws://localhost:8000/rpc",
    {"username": "root", "password": "root"},
    "myapp",
    "production"
)

with db_manager.get_connection() as db:
    # Your operations here
    pass
```

Ready to build amazing applications with SurrealDB! 🚀