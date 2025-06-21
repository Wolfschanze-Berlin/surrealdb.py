---
sidebar_position: 2
---

# WebSocket Connections

WebSocket connections provide full-duplex communication with SurrealDB, enabling real-time features like live queries and persistent connections. This guide covers everything you need to know about using WebSocket connections effectively.

## Overview

WebSocket connections offer several advantages over HTTP:

- **Persistent Connection**: Single connection for multiple operations
- **Real-time Communication**: Bidirectional data flow
- **Live Queries**: Real-time data synchronization
- **Lower Latency**: No connection overhead for subsequent requests
- **Server Push**: Server can initiate communication

## Connection Classes

### Synchronous WebSocket

```python
from surrealdb import Surreal
from surrealdb.connections import BlockingWsSurrealConnection

# Using factory function (recommended)
db = Surreal("ws://localhost:8000/rpc")

# Using class directly
db = BlockingWsSurrealConnection("ws://localhost:8000/rpc")
```

### Asynchronous WebSocket

```python
from surrealdb import AsyncSurreal
from surrealdb.connections import AsyncWsSurrealConnection

# Using factory function (recommended)
db = AsyncSurreal("ws://localhost:8000/rpc")

# Using class directly
db = AsyncWsSurrealConnection("ws://localhost:8000/rpc")
```

## Basic Usage

### Synchronous Example

```python
from surrealdb import Surreal

# Connect using context manager
with Surreal("ws://localhost:8000/rpc") as db:
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

# Connection automatically closed
```

### Asynchronous Example

```python
import asyncio
from surrealdb import AsyncSurreal

async def main():
    # Connect using async context manager
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
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

## Live Queries

Live queries are one of the most powerful features of WebSocket connections, allowing real-time data synchronization.

### Basic Live Query

```python
from surrealdb import Surreal
import threading
import time

def live_query_example():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("realtime", "app")
        
        # Start live query
        live_id = db.live("user")
        print(f"Started live query: {live_id}")
        
        # Subscribe to live updates in a separate thread
        def listen_for_updates():
            try:
                for update in db.subscribe_live(live_id):
                    print(f"Live update received: {update}")
            except Exception as e:
                print(f"Live query error: {e}")
        
        # Start listening thread
        listener_thread = threading.Thread(target=listen_for_updates)
        listener_thread.daemon = True
        listener_thread.start()
        
        # Simulate data changes
        for i in range(5):
            time.sleep(2)
            user = db.create("user", {
                "name": f"User {i}",
                "created_at": time.time()
            })
            print(f"Created user: {user[0]['id']}")
        
        # Stop live query
        db.kill(live_id)
        print("Live query stopped")

live_query_example()
```

### Async Live Query

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_live_query_example():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("realtime", "app")
        
        # Start live query
        live_id = await db.live("user")
        print(f"Started live query: {live_id}")
        
        # Create a task to listen for updates
        async def listen_for_updates():
            try:
                async for update in db.subscribe_live(live_id):
                    print(f"Live update received: {update}")
            except Exception as e:
                print(f"Live query error: {e}")
        
        # Start listening task
        listener_task = asyncio.create_task(listen_for_updates())
        
        # Simulate data changes
        for i in range(5):
            await asyncio.sleep(2)
            user = await db.create("user", {
                "name": f"User {i}",
                "created_at": asyncio.get_event_loop().time()
            })
            print(f"Created user: {user[0]['id']}")
        
        # Stop live query
        await db.kill(live_id)
        listener_task.cancel()
        
        try:
            await listener_task
        except asyncio.CancelledError:
            print("Live query listener cancelled")

asyncio.run(async_live_query_example())
```

### Live Query with Diff Mode

```python
from surrealdb import Surreal

def live_query_with_diff():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("realtime", "app")
        
        # Start live query with diff mode
        live_id = db.live("user", diff=True)
        print(f"Started live query with diff: {live_id}")
        
        def listen_for_diffs():
            for update in db.subscribe_live(live_id):
                print(f"Diff update: {update}")
                # Update contains JSON Patch operations instead of full records
        
        import threading
        listener = threading.Thread(target=listen_for_diffs)
        listener.daemon = True
        listener.start()
        
        # Create and modify records
        user = db.create("user", {"name": "Test User", "age": 25})
        user_id = user[0]["id"]
        
        # Update will generate diff
        db.merge(user_id, {"age": 26})
        
        # Patch will generate diff
        db.patch(user_id, [
            {"op": "add", "path": "/email", "value": "test@example.com"}
        ])
        
        import time
        time.sleep(2)
        
        db.kill(live_id)

live_query_with_diff()
```

## Advanced WebSocket Features

### Connection State Management

```python
from surrealdb import Surreal

class DatabaseManager:
    def __init__(self, url):
        self.url = url
        self.db = None
        self.connected = False
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.db = Surreal(self.url)
            self.db.signin({"username": "root", "password": "root"})
            self.db.use("myapp", "production")
            self.connected = True
            print("✅ Connected to SurrealDB")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.db:
            self.db.close()
            self.connected = False
            print("🔌 Disconnected from SurrealDB")
    
    def ensure_connected(self):
        """Ensure connection is active"""
        if not self.connected:
            self.connect()
    
    def execute_query(self, query, vars=None):
        """Execute query with connection check"""
        self.ensure_connected()
        try:
            return self.db.query(query, vars)
        except Exception as e:
            print(f"Query failed: {e}")
            self.connected = False
            raise

# Usage
db_manager = DatabaseManager("ws://localhost:8000/rpc")
db_manager.connect()

try:
    result = db_manager.execute_query("SELECT * FROM user")
    print(f"Query result: {result}")
finally:
    db_manager.disconnect()
```

### Reconnection Logic

```python
import time
from surrealdb import Surreal

class ReconnectingDatabase:
    def __init__(self, url, max_retries=5, retry_delay=2):
        self.url = url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.db = None
    
    def connect_with_retry(self):
        """Connect with automatic retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.db = Surreal(self.url)
                self.db.signin({"username": "root", "password": "root"})
                self.db.use("myapp", "production")
                print(f"✅ Connected on attempt {attempt + 1}")
                return True
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print("🚫 Max retries reached")
                    return False
    
    def execute_with_retry(self, operation):
        """Execute operation with retry on connection failure"""
        for attempt in range(self.max_retries):
            try:
                if not self.db:
                    if not self.connect_with_retry():
                        raise Exception("Failed to establish connection")
                
                return operation(self.db)
            except Exception as e:
                print(f"Operation failed on attempt {attempt + 1}: {e}")
                self.db = None  # Reset connection
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise

# Usage
db = ReconnectingDatabase("ws://localhost:8000/rpc")

def get_users(db_conn):
    return db_conn.select("user")

try:
    users = db.execute_with_retry(get_users)
    print(f"Retrieved {len(users)} users")
except Exception as e:
    print(f"Failed to retrieve users: {e}")
```

### Multiple Live Queries

```python
from surrealdb import Surreal
import threading
import time

def multiple_live_queries():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("realtime", "app")
        
        # Start multiple live queries
        user_live_id = db.live("user")
        post_live_id = db.live("post")
        comment_live_id = db.live("comment")
        
        print(f"Started live queries:")
        print(f"  Users: {user_live_id}")
        print(f"  Posts: {post_live_id}")
        print(f"  Comments: {comment_live_id}")
        
        # Handle updates for each table
        def handle_user_updates():
            for update in db.subscribe_live(user_live_id):
                print(f"👤 User update: {update}")
        
        def handle_post_updates():
            for update in db.subscribe_live(post_live_id):
                print(f"📝 Post update: {update}")
        
        def handle_comment_updates():
            for update in db.subscribe_live(comment_live_id):
                print(f"💬 Comment update: {update}")
        
        # Start listener threads
        threads = [
            threading.Thread(target=handle_user_updates, daemon=True),
            threading.Thread(target=handle_post_updates, daemon=True),
            threading.Thread(target=handle_comment_updates, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Simulate data changes
        time.sleep(1)
        
        # Create test data
        user = db.create("user", {"name": "Test User"})
        post = db.create("post", {"title": "Test Post", "author": user[0]["id"]})
        comment = db.create("comment", {"text": "Test Comment", "post": post[0]["id"]})
        
        time.sleep(2)
        
        # Stop all live queries
        db.kill(user_live_id)
        db.kill(post_live_id)
        db.kill(comment_live_id)
        
        print("All live queries stopped")

multiple_live_queries()
```

## WebSocket Configuration

### URL Formats

```python
# Local development
"ws://localhost:8000/rpc"

# Custom port
"ws://localhost:9000/rpc"

# Remote server
"ws://db.mycompany.com/rpc"

# Secure WebSocket (SSL/TLS)
"wss://secure-db.mycompany.com/rpc"

# With authentication in URL (not recommended)
"ws://username:password@localhost:8000/rpc"
```

### Connection Parameters

```python
from surrealdb.connections import BlockingWsSurrealConnection

# Basic connection
db = BlockingWsSurrealConnection("ws://localhost:8000/rpc")

# The SDK handles WebSocket-specific parameters internally
# Additional configuration is done through method calls
```

## Error Handling

### Connection Errors

```python
from surrealdb import Surreal
import websockets.exceptions

def handle_websocket_errors():
    try:
        with Surreal("ws://localhost:8000/rpc") as db:
            db.signin({"username": "root", "password": "root"})
            db.use("myapp", "production")
            
            # Your operations here
            result = db.select("user")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")
    except websockets.exceptions.InvalidURI as e:
        print(f"Invalid WebSocket URI: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

handle_websocket_errors()
```

### Live Query Error Handling

```python
from surrealdb import Surreal
import threading

def robust_live_query():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("realtime", "app")
        
        live_id = db.live("user")
        
        def safe_live_listener():
            try:
                for update in db.subscribe_live(live_id):
                    try:
                        # Process update safely
                        print(f"Processing update: {update}")
                        # Your update processing logic here
                    except Exception as e:
                        print(f"Error processing update: {e}")
                        # Continue listening despite processing errors
            except Exception as e:
                print(f"Live query listener error: {e}")
            finally:
                print("Live query listener stopped")
        
        listener_thread = threading.Thread(target=safe_live_listener)
        listener_thread.daemon = True
        listener_thread.start()
        
        # Your application logic
        import time
        time.sleep(10)
        
        # Clean shutdown
        try:
            db.kill(live_id)
        except Exception as e:
            print(f"Error stopping live query: {e}")

robust_live_query()
```

## Performance Optimization

### Connection Reuse

```python
from surrealdb import Surreal

class WebSocketService:
    def __init__(self, url):
        self.db = Surreal(url)
        self.db.signin({"username": "root", "password": "root"})
        self.db.use("myapp", "production")
    
    def get_user(self, user_id):
        return self.db.select(user_id)
    
    def create_user(self, data):
        return self.db.create("user", data)
    
    def update_user(self, user_id, data):
        return self.db.merge(user_id, data)
    
    def close(self):
        self.db.close()

# Reuse single connection for multiple operations
service = WebSocketService("ws://localhost:8000/rpc")

try:
    # Multiple operations on same connection
    user1 = service.create_user({"name": "John"})
    user2 = service.create_user({"name": "Jane"})
    
    updated = service.update_user(user1[0]["id"], {"active": True})
    
    all_users = service.get_user("user")
    print(f"Total users: {len(all_users)}")
    
finally:
    service.close()
```

### Batch Operations

```python
from surrealdb import Surreal

def batch_operations():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Batch insert multiple records
        users_data = [
            {"name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
        
        # Single operation for multiple records
        users = db.insert("user", users_data)
        print(f"Created {len(users)} users in batch")
        
        # Batch query with transaction
        result = db.query("""
            BEGIN TRANSACTION;
            
            CREATE post:1 SET title = "Post 1", author = user:1;
            CREATE post:2 SET title = "Post 2", author = user:2;
            CREATE post:3 SET title = "Post 3", author = user:3;
            
            COMMIT TRANSACTION;
        """)
        
        print(f"Batch transaction completed: {len(result)} operations")

batch_operations()
```

## Best Practices

### ✅ Do

- Use context managers for automatic connection cleanup
- Implement proper error handling for connection failures
- Use live queries for real-time features
- Reuse connections for multiple operations
- Handle live query errors gracefully
- Use diff mode for large datasets with frequent updates

### ❌ Don't

- Leave WebSocket connections open indefinitely
- Ignore connection state in long-running applications
- Create new connections for each operation
- Block the main thread with synchronous live queries
- Forget to stop live queries when done
- Mix blocking and non-blocking operations

## Next Steps

- **[HTTP Connections](./http.md)** - Learn about HTTP connection alternatives
- **[Async vs Sync](./async-vs-sync.md)** - Choose the right execution model
- **[Live Queries Guide](../methods/live-queries.md)** - Master real-time features
- **[Performance Tips](../advanced/performance.md)** - Optimize your WebSocket usage

---

**Need help?** Join our [Discord community](https://surrealdb.com/discord) for WebSocket-specific questions and support.