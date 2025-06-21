---
sidebar_position: 3
---

# HTTP Connections

HTTP connections provide a simple, stateless way to interact with SurrealDB using the familiar request-response pattern. This guide covers everything you need to know about using HTTP connections effectively.

## Overview

HTTP connections offer several advantages for certain use cases:

- **Stateless Operations**: Each request is independent
- **Simple Architecture**: Standard HTTP request-response pattern
- **Load Balancer Friendly**: Easy to distribute across multiple servers
- **Caching Support**: Leverage HTTP caching mechanisms
- **Firewall Friendly**: Uses standard HTTP/HTTPS ports
- **REST-like Interface**: Familiar to web developers

## Connection Classes

### Synchronous HTTP

```python
from surrealdb import Surreal
from surrealdb.connections import BlockingHttpSurrealConnection

# Using factory function (recommended)
db = Surreal("http://localhost:8000")

# Using class directly
db = BlockingHttpSurrealConnection("http://localhost:8000")
```

### Asynchronous HTTP

```python
from surrealdb import AsyncSurreal
from surrealdb.connections import AsyncHttpSurrealConnection

# Using factory function (recommended)
db = AsyncSurreal("http://localhost:8000")

# Using class directly
db = AsyncHttpSurrealConnection("http://localhost:8000")
```

## Basic Usage

### Synchronous Example

```python
from surrealdb import Surreal

# Connect using context manager
with Surreal("http://localhost:8000") as db:
    # Authenticate
    db.signin({"username": "root", "password": "root"})
    
    # Select namespace and database
    db.use("myapp", "production")
    
    # Perform operations
    users = db.select("user")
    print(f"Found {len(users)} users")
    
    # Create new record
    new_user = db.create("user", {
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    print(f"Created user: {new_user}")

# Each operation creates a new HTTP request
```

### Asynchronous Example

```python
import asyncio
from surrealdb import AsyncSurreal

async def main():
    # Connect using async context manager
    async with AsyncSurreal("http://localhost:8000") as db:
        # Authenticate
        await db.signin({"username": "root", "password": "root"})
        
        # Select namespace and database
        await db.use("myapp", "production")
        
        # Perform operations
        users = await db.select("user")
        print(f"Found {len(users)} users")
        
        # Create new record
        new_user = await db.create("user", {
            "name": "Jane Doe",
            "email": "jane@example.com"
        })
        
        print(f"Created user: {new_user}")

# Run async function
asyncio.run(main())
```

## HTTP-Specific Features

### Stateless Operations

Unlike WebSocket connections, HTTP connections are stateless. Each operation is a separate HTTP request:

```python
from surrealdb import Surreal

def demonstrate_stateless_nature():
    # Each operation is independent
    db = Surreal("http://localhost:8000")
    
    # Operation 1: Authenticate and query
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    users = db.select("user")
    print(f"Operation 1: {len(users)} users")
    
    # Operation 2: Need to authenticate again for new "session"
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    new_user = db.create("user", {"name": "Test User"})
    print(f"Operation 2: Created {new_user}")
    
    # The SDK handles authentication state internally,
    # but each method call is a separate HTTP request

demonstrate_stateless_nature()
```

### Request-Response Pattern

```python
from surrealdb import Surreal
import time

def demonstrate_request_response():
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Each method call = one HTTP request
        start_time = time.time()
        
        # Request 1: SELECT
        users = db.select("user")
        print(f"Request 1 completed in {time.time() - start_time:.3f}s")
        
        # Request 2: CREATE
        start_time = time.time()
        new_user = db.create("user", {"name": "HTTP User"})
        print(f"Request 2 completed in {time.time() - start_time:.3f}s")
        
        # Request 3: UPDATE
        start_time = time.time()
        updated = db.merge(new_user[0]["id"], {"active": True})
        print(f"Request 3 completed in {time.time() - start_time:.3f}s")

demonstrate_request_response()
```

## Advanced HTTP Features

### Concurrent HTTP Requests

With async HTTP connections, you can make concurrent requests:

```python
import asyncio
from surrealdb import AsyncSurreal

async def concurrent_http_operations():
    async with AsyncSurreal("http://localhost:8000") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        # Define multiple operations
        async def create_user(name, email):
            return await db.create("user", {"name": name, "email": email})
        
        async def get_user_count():
            users = await db.select("user")
            return len(users)
        
        async def create_post(title, content):
            return await db.create("post", {"title": title, "content": content})
        
        # Execute operations concurrently
        start_time = asyncio.get_event_loop().time()
        
        results = await asyncio.gather(
            create_user("Alice", "alice@example.com"),
            create_user("Bob", "bob@example.com"),
            create_post("Post 1", "Content 1"),
            create_post("Post 2", "Content 2"),
            get_user_count()
        )
        
        end_time = asyncio.get_event_loop().time()
        
        print(f"Completed 5 concurrent operations in {end_time - start_time:.3f}s")
        print(f"Results: {len(results)} operations completed")

asyncio.run(concurrent_http_operations())
```

### Batch Operations with HTTP

```python
from surrealdb import Surreal

def batch_http_operations():
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Batch insert (single HTTP request)
        users_data = [
            {"name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(10)
        ]
        
        users = db.insert("user", users_data)
        print(f"Batch created {len(users)} users in one request")
        
        # Complex query (single HTTP request)
        result = db.query("""
            -- Multiple operations in one request
            LET $user_count = (SELECT count() FROM user GROUP ALL)[0].count;
            LET $recent_users = SELECT * FROM user ORDER BY id DESC LIMIT 5;
            
            RETURN {
                total_users: $user_count,
                recent_users: $recent_users
            };
        """)
        
        print(f"Complex query result: {result}")

batch_http_operations()
```

### HTTP Authentication Patterns

```python
from surrealdb import Surreal

class HTTPDatabaseService:
    def __init__(self, url, credentials):
        self.url = url
        self.credentials = credentials
        self.namespace = None
        self.database = None
    
    def setup_session(self, namespace, database):
        """Setup namespace and database for subsequent operations"""
        self.namespace = namespace
        self.database = database
    
    def execute_operation(self, operation):
        """Execute operation with automatic authentication"""
        with Surreal(self.url) as db:
            # Authenticate for each operation
            db.signin(self.credentials)
            
            if self.namespace and self.database:
                db.use(self.namespace, self.database)
            
            return operation(db)
    
    def get_users(self):
        def operation(db):
            return db.select("user")
        return self.execute_operation(operation)
    
    def create_user(self, data):
        def operation(db):
            return db.create("user", data)
        return self.execute_operation(operation)
    
    def update_user(self, user_id, data):
        def operation(db):
            return db.merge(user_id, data)
        return self.execute_operation(operation)

# Usage
service = HTTPDatabaseService(
    "http://localhost:8000",
    {"username": "root", "password": "root"}
)

service.setup_session("myapp", "production")

# Each method call is a separate HTTP request with authentication
users = service.get_users()
new_user = service.create_user({"name": "HTTP Service User"})
updated = service.update_user(new_user[0]["id"], {"active": True})

print(f"Service operations completed: {len(users)} users")
```

## HTTP Configuration

### URL Formats

```python
# Local development
"http://localhost:8000"

# Custom port
"http://localhost:9000"

# Remote server
"http://api.mycompany.com"

# Secure HTTP (SSL/TLS)
"https://secure-api.mycompany.com"

# With path (if SurrealDB is behind a proxy)
"https://api.mycompany.com/surrealdb"
```

### HTTPS and SSL

```python
from surrealdb import Surreal

# HTTPS connection
with Surreal("https://secure-db.mycompany.com") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("secure", "app")
    
    # All requests use HTTPS
    result = db.select("user")
    print(f"Secure request completed: {len(result)} records")
```

### Custom Headers and Configuration

```python
# Note: The current SDK doesn't expose HTTP headers directly,
# but you can work with the underlying connection if needed

from surrealdb.connections import BlockingHttpSurrealConnection

# For advanced HTTP configuration, you might need to extend the connection class
class CustomHttpConnection(BlockingHttpSurrealConnection):
    def __init__(self, url, headers=None):
        super().__init__(url)
        self.custom_headers = headers or {}
    
    # Override methods to add custom headers if needed
    # This is an advanced use case

# Basic usage remains the same
db = CustomHttpConnection("http://localhost:8000")
```

## Error Handling

### HTTP-Specific Errors

```python
from surrealdb import Surreal
import requests.exceptions

def handle_http_errors():
    try:
        with Surreal("http://localhost:8000") as db:
            db.signin({"username": "root", "password": "root"})
            db.use("myapp", "production")
            
            # Your operations here
            result = db.select("user")
            
    except requests.exceptions.ConnectionError as e:
        print(f"HTTP connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"HTTP timeout: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

handle_http_errors()
```

### Retry Logic for HTTP

```python
import time
from surrealdb import Surreal

class RetryableHTTPService:
    def __init__(self, url, max_retries=3, retry_delay=1):
        self.url = url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute_with_retry(self, operation):
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                with Surreal(self.url) as db:
                    db.signin({"username": "root", "password": "root"})
                    db.use("myapp", "production")
                    return operation(db)
                    
            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"All {self.max_retries} attempts failed")
        
        raise last_exception
    
    def get_users(self):
        def operation(db):
            return db.select("user")
        return self.execute_with_retry(operation)

# Usage
service = RetryableHTTPService("http://localhost:8000")

try:
    users = service.get_users()
    print(f"Retrieved {len(users)} users")
except Exception as e:
    print(f"Failed after retries: {e}")
```

## Performance Considerations

### Connection Overhead

```python
import time
from surrealdb import Surreal

def measure_http_overhead():
    """Demonstrate HTTP connection overhead"""
    
    # Multiple separate connections (higher overhead)
    start_time = time.time()
    
    for i in range(5):
        with Surreal("http://localhost:8000") as db:
            db.signin({"username": "root", "password": "root"})
            db.use("myapp", "production")
            users = db.select("user")
    
    separate_time = time.time() - start_time
    print(f"5 separate connections: {separate_time:.3f}s")
    
    # Single connection, multiple operations (lower overhead)
    start_time = time.time()
    
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        for i in range(5):
            users = db.select("user")
    
    single_time = time.time() - start_time
    print(f"1 connection, 5 operations: {single_time:.3f}s")
    print(f"Overhead reduction: {((separate_time - single_time) / separate_time * 100):.1f}%")

measure_http_overhead()
```

### Async Concurrency Benefits

```python
import asyncio
import time
from surrealdb import AsyncSurreal

async def compare_sync_vs_async():
    """Compare synchronous vs asynchronous HTTP performance"""
    
    # Simulate synchronous operations
    def sync_operations():
        start_time = time.time()
        
        for i in range(5):
            with Surreal("http://localhost:8000") as db:
                db.signin({"username": "root", "password": "root"})
                db.use("myapp", "production")
                users = db.select("user")
        
        return time.time() - start_time
    
    # Asynchronous operations
    async def async_operations():
        start_time = time.time()
        
        async def single_operation():
            async with AsyncSurreal("http://localhost:8000") as db:
                await db.signin({"username": "root", "password": "root"})
                await db.use("myapp", "production")
                return await db.select("user")
        
        # Run operations concurrently
        tasks = [single_operation() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        return time.time() - start_time
    
    # Compare performance
    sync_time = sync_operations()
    async_time = await async_operations()
    
    print(f"Synchronous: {sync_time:.3f}s")
    print(f"Asynchronous: {async_time:.3f}s")
    print(f"Async speedup: {(sync_time / async_time):.1f}x")

asyncio.run(compare_sync_vs_async())
```

## HTTP vs WebSocket Comparison

### When to Choose HTTP

```python
from surrealdb import Surreal

# ✅ Good for HTTP: Simple CRUD operations
def simple_crud_operations():
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("api", "users")
        
        # Create
        user = db.create("user", {"name": "API User"})
        
        # Read
        users = db.select("user")
        
        # Update
        updated = db.merge(user[0]["id"], {"active": True})
        
        # Delete
        deleted = db.delete(user[0]["id"])
        
        return {"created": user, "updated": updated, "deleted": deleted}

# ✅ Good for HTTP: Stateless microservices
class UserService:
    def __init__(self):
        self.db_url = "http://localhost:8000"
        self.credentials = {"username": "root", "password": "root"}
    
    def create_user(self, user_data):
        with Surreal(self.db_url) as db:
            db.signin(self.credentials)
            db.use("microservice", "users")
            return db.create("user", user_data)
    
    def get_user(self, user_id):
        with Surreal(self.db_url) as db:
            db.signin(self.credentials)
            db.use("microservice", "users")
            return db.select(user_id)

# ❌ Not ideal for HTTP: Real-time features
def realtime_not_ideal_for_http():
    # HTTP cannot do live queries
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("realtime", "app")
        
        # This would raise an error - live queries need WebSocket
        try:
            live_id = db.live("user")  # Not supported over HTTP
        except Exception as e:
            print(f"Live queries not supported over HTTP: {e}")
```

## Best Practices

### ✅ Do

- Use HTTP for simple request-response operations
- Leverage async HTTP for concurrent operations
- Implement retry logic for network failures
- Use batch operations to reduce request count
- Choose HTTP for stateless microservices
- Use HTTPS in production environments

### ❌ Don't

- Use HTTP for real-time features (use WebSocket instead)
- Create new connections for each operation unnecessarily
- Ignore HTTP error codes and status
- Forget to handle network timeouts
- Use HTTP for applications requiring live queries
- Store sensitive data in HTTP URLs

## Migration from WebSocket to HTTP

If you need to migrate from WebSocket to HTTP:

```python
# Before (WebSocket)
from surrealdb import Surreal

def websocket_version():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Live queries work
        live_id = db.live("user")
        # ... live query logic
        
        return db.select("user")

# After (HTTP)
def http_version():
    with Surreal("http://localhost:8000") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Live queries removed - use polling instead
        # live_id = db.live("user")  # Remove this
        
        return db.select("user")

# Polling alternative for real-time updates
import time
import threading

def polling_alternative():
    def poll_for_changes():
        last_count = 0
        while True:
            with Surreal("http://localhost:8000") as db:
                db.signin({"username": "root", "password": "root"})
                db.use("myapp", "production")
                
                users = db.select("user")
                current_count = len(users)
                
                if current_count != last_count:
                    print(f"User count changed: {last_count} -> {current_count}")
                    last_count = current_count
                
                time.sleep(5)  # Poll every 5 seconds
    
    # Start polling in background thread
    poll_thread = threading.Thread(target=poll_for_changes, daemon=True)
    poll_thread.start()
```

## Next Steps

- **[Async vs Sync](./async-vs-sync.md)** - Choose the right execution model
- **[WebSocket Connections](./websocket.md)** - Compare with WebSocket features
- **[Core Methods](../methods/overview.md)** - Learn about available operations
- **[Performance Guide](../advanced/performance.md)** - Optimize HTTP usage

---

**Need help?** Join our [Discord community](https://surrealdb.com/discord) for HTTP-specific questions and support.