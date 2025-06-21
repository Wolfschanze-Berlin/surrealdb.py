---
sidebar_position: 4
---

# Async vs Sync Connections

Understanding when to use asynchronous versus synchronous connections is crucial for building efficient SurrealDB applications. This guide provides a comprehensive comparison and helps you choose the right approach.

## Overview

The SurrealDB Python SDK provides both synchronous (blocking) and asynchronous (non-blocking) interfaces:

- **Synchronous**: Traditional blocking operations, simpler to understand and use
- **Asynchronous**: Non-blocking operations, better for concurrent workloads and web applications

## Quick Comparison

| Aspect | Synchronous | Asynchronous |
|--------|-------------|--------------|
| **Execution Model** | Blocking | Non-blocking |
| **Concurrency** | Sequential | Concurrent |
| **Memory Usage** | Lower | Higher |
| **CPU Efficiency** | Lower | Higher |
| **Learning Curve** | Easier | Steeper |
| **Use Cases** | Scripts, simple apps | Web apps, high concurrency |
| **Error Handling** | Simpler | More complex |
| **Debugging** | Easier | More challenging |

## Synchronous Connections

### When to Use Synchronous

**✅ Choose synchronous when:**

- Building simple scripts or command-line tools
- Learning SurrealDB or prototyping
- Working with sequential operations
- Integrating with synchronous frameworks
- Debugging and development
- Low concurrency requirements

### Synchronous Examples

#### Basic Usage

```python
from surrealdb import Surreal

# Simple synchronous operation
def sync_example():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        # Operations execute one after another
        users = db.select("user")
        print(f"Found {len(users)} users")
        
        for user in users:
            # Each operation waits for the previous to complete
            updated = db.merge(user["id"], {"last_seen": "now"})
            print(f"Updated user: {updated[0]['id']}")

sync_example()
```

#### Sequential Processing

```python
from surrealdb import Surreal
import time

def sequential_processing():
    """Process data sequentially - simple and predictable"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("processing", "data")
        
        # Create test data
        data_items = [
            {"name": f"Item {i}", "value": i * 10}
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Process each item sequentially
        results = []
        for item in data_items:
            # Create record
            created = db.create("item", item)
            
            # Process the record
            processed = db.merge(created[0]["id"], {
                "processed": True,
                "processed_at": time.time()
            })
            
            results.append(processed[0])
            print(f"Processed item: {processed[0]['name']}")
        
        total_time = time.time() - start_time
        print(f"Sequential processing completed in {total_time:.2f}s")
        
        return results

sequential_processing()
```

#### Error Handling (Sync)

```python
from surrealdb import Surreal
from surrealdb.errors import SurrealDBMethodError

def sync_error_handling():
    """Simple error handling with synchronous operations"""
    
    try:
        with Surreal("ws://localhost:8000/rpc") as db:
            db.signin({"username": "root", "password": "root"})
            db.use("myapp", "production")
            
            # Simple try-catch for each operation
            try:
                user = db.create("user", {"name": "Test User"})
                print(f"Created user: {user}")
            except SurrealDBMethodError as e:
                print(f"Failed to create user: {e}")
            
            try:
                users = db.select("user")
                print(f"Retrieved {len(users)} users")
            except SurrealDBMethodError as e:
                print(f"Failed to retrieve users: {e}")
                
    except Exception as e:
        print(f"Connection error: {e}")

sync_error_handling()
```

## Asynchronous Connections

### When to Use Asynchronous

**✅ Choose asynchronous when:**

- Building web applications (FastAPI, Django Async, etc.)
- Handling high concurrency
- Maximizing performance and resource utilization
- Working with other async libraries
- I/O-bound operations
- Real-time applications

### Asynchronous Examples

#### Basic Usage

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_example():
    """Basic asynchronous operation"""
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        # Operations can be awaited
        users = await db.select("user")
        print(f"Found {len(users)} users")
        
        # Can process concurrently
        tasks = [
            db.merge(user["id"], {"last_seen": "now"})
            for user in users
        ]
        
        # Wait for all updates to complete concurrently
        results = await asyncio.gather(*tasks)
        print(f"Updated {len(results)} users concurrently")

asyncio.run(async_example())
```

#### Concurrent Processing

```python
import asyncio
import time
from surrealdb import AsyncSurreal

async def concurrent_processing():
    """Process data concurrently - faster and more efficient"""
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("processing", "data")
        
        # Create test data
        data_items = [
            {"name": f"Item {i}", "value": i * 10}
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Process items concurrently
        async def process_item(item):
            # Create record
            created = await db.create("item", item)
            
            # Process the record
            processed = await db.merge(created[0]["id"], {
                "processed": True,
                "processed_at": time.time()
            })
            
            print(f"Processed item: {processed[0]['name']}")
            return processed[0]
        
        # Run all processing tasks concurrently
        tasks = [process_item(item) for item in data_items]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        print(f"Concurrent processing completed in {total_time:.2f}s")
        
        return results

asyncio.run(concurrent_processing())
```

#### Error Handling (Async)

```python
import asyncio
from surrealdb import AsyncSurreal
from surrealdb.errors import SurrealDBMethodError

async def async_error_handling():
    """Error handling with asynchronous operations"""
    
    try:
        async with AsyncSurreal("ws://localhost:8000/rpc") as db:
            await db.signin({"username": "root", "password": "root"})
            await db.use("myapp", "production")
            
            # Handle errors in concurrent operations
            async def safe_create_user(name):
                try:
                    user = await db.create("user", {"name": name})
                    return {"success": True, "user": user}
                except SurrealDBMethodError as e:
                    return {"success": False, "error": str(e)}
            
            # Process multiple operations with error handling
            tasks = [
                safe_create_user(f"User {i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Task {i} failed with exception: {result}")
                elif result["success"]:
                    print(f"Task {i} succeeded: {result['user'][0]['id']}")
                else:
                    print(f"Task {i} failed: {result['error']}")
                    
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(async_error_handling())
```

## Performance Comparison

### Benchmark Example

```python
import asyncio
import time
from surrealdb import Surreal, AsyncSurreal

def sync_benchmark():
    """Benchmark synchronous operations"""
    
    start_time = time.time()
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("benchmark", "sync")
        
        # Clean up
        db.query("DELETE user")
        
        # Sequential operations
        for i in range(10):
            user = db.create("user", {
                "name": f"Sync User {i}",
                "email": f"sync{i}@example.com"
            })
            
            # Update the user
            db.merge(user[0]["id"], {"active": True})
    
    return time.time() - start_time

async def async_benchmark():
    """Benchmark asynchronous operations"""
    
    start_time = time.time()
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("benchmark", "async")
        
        # Clean up
        await db.query("DELETE user")
        
        # Concurrent operations
        async def create_and_update_user(i):
            user = await db.create("user", {
                "name": f"Async User {i}",
                "email": f"async{i}@example.com"
            })
            
            # Update the user
            return await db.merge(user[0]["id"], {"active": True})
        
        # Run all operations concurrently
        tasks = [create_and_update_user(i) for i in range(10)]
        await asyncio.gather(*tasks)
    
    return time.time() - start_time

def run_benchmarks():
    """Compare sync vs async performance"""
    
    print("Running performance benchmarks...")
    
    # Run sync benchmark
    sync_time = sync_benchmark()
    print(f"Synchronous: {sync_time:.3f}s")
    
    # Run async benchmark
    async_time = asyncio.run(async_benchmark())
    print(f"Asynchronous: {async_time:.3f}s")
    
    # Calculate improvement
    if async_time < sync_time:
        improvement = (sync_time - async_time) / sync_time * 100
        print(f"Async is {improvement:.1f}% faster")
    else:
        degradation = (async_time - sync_time) / sync_time * 100
        print(f"Async is {degradation:.1f}% slower")

run_benchmarks()
```

## Real-World Use Cases

### Web Application Example

#### FastAPI with Async SurrealDB

```python
from fastapi import FastAPI, HTTPException
from surrealdb import AsyncSurreal
import asyncio

app = FastAPI()

# Database connection pool
class DatabasePool:
    def __init__(self, url, size=10):
        self.url = url
        self.size = size
        self.connections = asyncio.Queue(maxsize=size)
        self.initialized = False
    
    async def initialize(self):
        """Initialize connection pool"""
        if self.initialized:
            return
        
        for _ in range(self.size):
            db = AsyncSurreal(self.url)
            await db.signin({"username": "root", "password": "root"})
            await db.use("webapp", "production")
            await self.connections.put(db)
        
        self.initialized = True
    
    async def get_connection(self):
        """Get connection from pool"""
        if not self.initialized:
            await self.initialize()
        return await self.connections.get()
    
    async def return_connection(self, db):
        """Return connection to pool"""
        await self.connections.put(db)

# Global connection pool
db_pool = DatabasePool("ws://localhost:8000/rpc")

@app.get("/users")
async def get_users():
    """Get all users - async endpoint"""
    db = await db_pool.get_connection()
    try:
        users = await db.select("user")
        return {"users": users}
    finally:
        await db_pool.return_connection(db)

@app.post("/users")
async def create_user(user_data: dict):
    """Create user - async endpoint"""
    db = await db_pool.get_connection()
    try:
        user = await db.create("user", user_data)
        return {"user": user[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db_pool.return_connection(db)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get specific user - async endpoint"""
    db = await db_pool.get_connection()
    try:
        user = await db.select(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": user[0]}
    finally:
        await db_pool.return_connection(db)

# Run with: uvicorn main:app --reload
```

#### Flask with Sync SurrealDB

```python
from flask import Flask, request, jsonify
from surrealdb import Surreal

app = Flask(__name__)

# Simple database service
class DatabaseService:
    def __init__(self, url):
        self.url = url
        self.credentials = {"username": "root", "password": "root"}
    
    def get_connection(self):
        db = Surreal(self.url)
        db.signin(self.credentials)
        db.use("webapp", "production")
        return db

db_service = DatabaseService("ws://localhost:8000/rpc")

@app.route("/users", methods=["GET"])
def get_users():
    """Get all users - sync endpoint"""
    with db_service.get_connection() as db:
        users = db.select("user")
        return jsonify({"users": users})

@app.route("/users", methods=["POST"])
def create_user():
    """Create user - sync endpoint"""
    user_data = request.json
    
    with db_service.get_connection() as db:
        try:
            user = db.create("user", user_data)
            return jsonify({"user": user[0]})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Get specific user - sync endpoint"""
    with db_service.get_connection() as db:
        user = db.select(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user[0]})

# Run with: flask run
```

### Data Processing Pipeline

#### Async Pipeline

```python
import asyncio
from surrealdb import AsyncSurreal

async def async_data_pipeline():
    """Async data processing pipeline"""
    
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("pipeline", "async")
        
        # Stage 1: Extract data concurrently
        async def extract_data(source):
            # Simulate data extraction
            await asyncio.sleep(0.1)
            return {"source": source, "data": f"data_from_{source}"}
        
        sources = ["api", "file", "database", "stream"]
        extract_tasks = [extract_data(source) for source in sources]
        raw_data = await asyncio.gather(*extract_tasks)
        
        print(f"Extracted {len(raw_data)} data sources")
        
        # Stage 2: Transform data concurrently
        async def transform_data(item):
            # Simulate data transformation
            await asyncio.sleep(0.1)
            return {
                "source": item["source"],
                "transformed_data": item["data"].upper(),
                "processed": True
            }
        
        transform_tasks = [transform_data(item) for item in raw_data]
        transformed_data = await asyncio.gather(*transform_tasks)
        
        print(f"Transformed {len(transformed_data)} items")
        
        # Stage 3: Load data concurrently
        async def load_data(item):
            return await db.create("processed_data", item)
        
        load_tasks = [load_data(item) for item in transformed_data]
        results = await asyncio.gather(*load_tasks)
        
        print(f"Loaded {len(results)} records to database")
        
        return results

asyncio.run(async_data_pipeline())
```

#### Sync Pipeline

```python
import time
from surrealdb import Surreal

def sync_data_pipeline():
    """Sync data processing pipeline"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("pipeline", "sync")
        
        # Stage 1: Extract data sequentially
        def extract_data(source):
            # Simulate data extraction
            time.sleep(0.1)
            return {"source": source, "data": f"data_from_{source}"}
        
        sources = ["api", "file", "database", "stream"]
        raw_data = [extract_data(source) for source in sources]
        
        print(f"Extracted {len(raw_data)} data sources")
        
        # Stage 2: Transform data sequentially
        def transform_data(item):
            # Simulate data transformation
            time.sleep(0.1)
            return {
                "source": item["source"],
                "transformed_data": item["data"].upper(),
                "processed": True
            }
        
        transformed_data = [transform_data(item) for item in raw_data]
        
        print(f"Transformed {len(transformed_data)} items")
        
        # Stage 3: Load data sequentially
        def load_data(item):
            return db.create("processed_data", item)
        
        results = [load_data(item) for item in transformed_data]
        
        print(f"Loaded {len(results)} records to database")
        
        return results

sync_data_pipeline()
```

## Migration Guide

### From Sync to Async

```python
# Before (Synchronous)
from surrealdb import Surreal

def sync_function():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        users = db.select("user")
        for user in users:
            updated = db.merge(user["id"], {"last_seen": "now"})
        
        return users

# After (Asynchronous)
import asyncio
from surrealdb import AsyncSurreal

async def async_function():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        users = await db.select("user")
        
        # Concurrent updates
        tasks = [
            db.merge(user["id"], {"last_seen": "now"})
            for user in users
        ]
        await asyncio.gather(*tasks)
        
        return users

# Usage
result = asyncio.run(async_function())
```

### From Async to Sync

```python
# Before (Asynchronous)
import asyncio
from surrealdb import AsyncSurreal

async def async_function():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        users = await db.select("user")
        return users

# After (Synchronous)
from surrealdb import Surreal

def sync_function():
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("myapp", "production")
        
        users = db.select("user")
        return users

# Usage
result = sync_function()
```

## Decision Matrix

### Choose Synchronous When:

| Scenario | Reason |
|----------|--------|
| **Simple scripts** | Easier to write and debug |
| **Learning/Prototyping** | Lower complexity |
| **Sequential processing** | Natural fit for step-by-step operations |
| **Legacy integration** | Existing sync codebase |
| **Low concurrency** | Few simultaneous operations |

### Choose Asynchronous When:

| Scenario | Reason |
|----------|--------|
| **Web applications** | Handle multiple requests concurrently |
| **High throughput** | Process many operations simultaneously |
| **I/O-bound tasks** | Maximize resource utilization |
| **Real-time features** | Better for live queries and events |
| **Modern frameworks** | FastAPI, Django Async, etc. |

## Best Practices

### Synchronous Best Practices

```python
from surrealdb import Surreal

# ✅ Use context managers
with Surreal("ws://localhost:8000/rpc") as db:
    # Your operations here
    pass

# ✅ Handle errors appropriately
try:
    with Surreal("ws://localhost:8000/rpc") as db:
        result = db.select("user")
except Exception as e:
    print(f"Error: {e}")

# ✅ Reuse connections when possible
db = Surreal("ws://localhost:8000/rpc")
try:
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    
    # Multiple operations on same connection
    users = db.select("user")
    posts = db.select("post")
finally:
    db.close()
```

### Asynchronous Best Practices

```python
import asyncio
from surrealdb import AsyncSurreal

# ✅ Use async context managers
async def good_async_pattern():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        # Your operations here

# ✅ Handle errors in concurrent operations
async def safe_concurrent_operations():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        async def safe_operation(data):
            try:
                return await db.create("user", data)
            except Exception as e:
                return {"error": str(e)}
        
        tasks = [safe_operation({"name": f"User {i}"}) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

# ✅ Use connection pooling for high-load applications
class AsyncConnectionPool:
    def __init__(self, url, size=10):
        self.url = url
        self.pool = asyncio.Queue(maxsize=size)
        self.initialized = False
    
    async def get_connection(self):
        if not self.initialized:
            await self._initialize()
        return await self.pool.get()
    
    async def return_connection(self, db):
        await self.pool.put(db)
```

## Common Pitfalls

### ❌ Don't Mix Sync and Async

```python
# ❌ Wrong - mixing sync and async
import asyncio
from surrealdb import Surreal, AsyncSurreal

async def bad_mixing():
    # Don't use sync connection in async function
    with Surreal("ws://localhost:8000/rpc") as db:  # Blocks event loop
        db.signin({"username": "root", "password": "root"})
        return db.select("user")

# ✅ Correct - use async connection in async function
async def good_async():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        return await db.select("user")
```

### ❌ Don't Forget Error Handling

```python
# ❌ Wrong - no error handling in concurrent operations
async def bad_error_handling():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        # If one fails, all fail
        tasks = [db.create("user", {"name": f"User {i}"}) for i in range(5)]
        results = await asyncio.gather(*tasks)  # Will raise on first error

# ✅ Correct - handle errors gracefully
async def good_error_handling():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        # Handle errors individually
        tasks = [db.create("user", {"name": f"User {i}"}) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i} failed: {result}")
```

## Next Steps

- **[Core Methods](../methods/overview.md)** - Learn about available database operations
- **[Live Queries](../methods/live-queries.md)** - Master real-time features (async recommended)
- **[Performance Guide](../advanced/performance.md)** - Optimize your chosen approach
- **[Best Practices](../advanced/best-practices.md)** - Follow proven patterns

---

**Need help choosing?** Join our [Discord community](https://surrealdb.com/discord) for personalized advice on sync vs async patterns.