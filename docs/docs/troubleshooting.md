---
sidebar_position: 8
---

# Troubleshooting

This guide helps you diagnose and resolve common issues when using the SurrealDB Python SDK. Find solutions to frequent problems and learn how to debug your applications effectively.

## Common Issues

### Connection Problems

#### Issue: `ConnectionError: Connection refused`

**Symptoms:**
```python
ConnectionError: [Errno 61] Connection refused
```

**Causes & Solutions:**

1. **SurrealDB server not running**
   ```bash
   # Check if SurrealDB is running
   curl http://localhost:8000/health
   
   # Start SurrealDB
   surreal start --log trace --user root --pass root memory
   ```

2. **Wrong URL or port**
   ```python
   # ❌ Wrong
   db = Surreal("ws://localhost:3000/rpc")
   
   # ✅ Correct (default port is 8000)
   db = Surreal("ws://localhost:8000/rpc")
   ```

3. **Firewall blocking connection**
   ```bash
   # Check if port is accessible
   telnet localhost 8000
   ```

#### Issue: `Invalid URI` or `Unsupported protocol`

**Symptoms:**
```python
ValueError: Unsupported protocol in URL: http://localhost:8000/rpc. Use 'ws://' or 'http://'.
```

**Solutions:**

1. **Use correct URL scheme**
   ```python
   # ❌ Wrong - HTTP URL with /rpc endpoint
   db = Surreal("http://localhost:8000/rpc")
   
   # ✅ Correct options
   db = Surreal("ws://localhost:8000/rpc")    # WebSocket
   db = Surreal("http://localhost:8000")      # HTTP
   ```

2. **Check URL format**
   ```python
   # Valid URL formats
   valid_urls = [
       "ws://localhost:8000/rpc",
       "wss://secure.example.com/rpc",
       "http://localhost:8000",
       "https://api.example.com"
   ]
   ```

#### Issue: WebSocket connection drops

**Symptoms:**
```python
websockets.exceptions.ConnectionClosed: received 1000 (OK); no close frame received
```

**Solutions:**

1. **Implement reconnection logic**
   ```python
   import time
   from surrealdb import Surreal
   
   def connect_with_retry(url, max_retries=5):
       for attempt in range(max_retries):
           try:
               db = Surreal(url)
               db.signin({"username": "root", "password": "root"})
               return db
           except Exception as e:
               print(f"Connection attempt {attempt + 1} failed: {e}")
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
               else:
                   raise
   ```

2. **Handle connection state**
   ```python
   class RobustConnection:
       def __init__(self, url):
           self.url = url
           self.db = None
           self.connected = False
       
       def ensure_connected(self):
           if not self.connected:
               self.connect()
       
       def connect(self):
           try:
               self.db = Surreal(self.url)
               self.db.signin({"username": "root", "password": "root"})
               self.connected = True
           except Exception as e:
               self.connected = False
               raise
       
       def execute(self, operation):
           self.ensure_connected()
           try:
               return operation(self.db)
           except Exception as e:
               self.connected = False
               raise
   ```

### Authentication Issues

#### Issue: `Authentication failed`

**Symptoms:**
```python
SurrealDBMethodError: Authentication failed
```

**Solutions:**

1. **Check credentials**
   ```python
   # ❌ Wrong credentials
   db.signin({"username": "admin", "password": "wrong"})
   
   # ✅ Correct credentials
   db.signin({"username": "root", "password": "root"})
   ```

2. **Verify authentication level**
   ```python
   # Root level (full access)
   db.signin({"username": "root", "password": "root"})
   
   # Namespace level
   db.signin({
       "namespace": "mycompany",
       "username": "admin",
       "password": "admin123"
   })
   
   # Database level
   db.signin({
       "namespace": "mycompany", 
       "database": "production",
       "username": "user",
       "password": "user123"
   })
   ```

3. **Check scope authentication**
   ```python
   # Ensure scope exists and is properly configured
   db.signin({
       "namespace": "mycompany",
       "database": "production",
       "scope": "user",  # Must exist in database
       "email": "user@example.com",
       "password": "password123"
   })
   ```

#### Issue: `Token expired` or `Invalid token`

**Solutions:**

1. **Refresh authentication**
   ```python
   def refresh_auth(db, credentials):
       try:
           db.signin(credentials)
       except Exception as e:
           print(f"Re-authentication failed: {e}")
           raise
   
   # Use in your application
   try:
       result = db.select("user")
   except SurrealDBMethodError as e:
       if "token" in str(e).lower():
           refresh_auth(db, {"username": "root", "password": "root"})
           result = db.select("user")  # Retry
   ```

2. **Handle token expiration**
   ```python
   import time
   
   class TokenManager:
       def __init__(self, db, credentials):
           self.db = db
           self.credentials = credentials
           self.last_auth = 0
           self.auth_timeout = 3600  # 1 hour
       
       def ensure_authenticated(self):
           current_time = time.time()
           if current_time - self.last_auth > self.auth_timeout:
               self.db.signin(self.credentials)
               self.last_auth = current_time
   ```

### Query Issues

#### Issue: `Table or record not found`

**Symptoms:**
```python
SurrealDBMethodError: Table 'users' not found
```

**Solutions:**

1. **Check namespace and database**
   ```python
   # Ensure you're using the correct namespace/database
   db.use("correct_namespace", "correct_database")
   
   # List available tables
   tables = db.query("INFO FOR DB")
   print("Available tables:", tables)
   ```

2. **Verify table name**
   ```python
   # ❌ Wrong table name
   users = db.select("users")  # Table might be "user" not "users"
   
   # ✅ Check actual table name
   users = db.select("user")
   ```

3. **Create table if needed**
   ```python
   # Tables are created automatically when you insert data
   user = db.create("user", {"name": "First User"})
   ```

#### Issue: `Invalid SurrealQL syntax`

**Symptoms:**
```python
SurrealDBMethodError: Parse error: unexpected token 'SELCT'
```

**Solutions:**

1. **Check query syntax**
   ```python
   # ❌ Typo in query
   result = db.query("SELCT * FROM user")
   
   # ✅ Correct syntax
   result = db.query("SELECT * FROM user")
   ```

2. **Use query validation**
   ```python
   def safe_query(db, query, variables=None):
       try:
           return db.query(query, variables)
       except SurrealDBMethodError as e:
           print(f"Query error: {e}")
           print(f"Query: {query}")
           print(f"Variables: {variables}")
           raise
   ```

3. **Use parameterized queries**
   ```python
   # ❌ String concatenation (error-prone)
   name = "John"
   result = db.query(f"SELECT * FROM user WHERE name = '{name}'")
   
   # ✅ Parameterized query (safe)
   result = db.query("SELECT * FROM user WHERE name = $name", {"name": name})
   ```

### Data Type Issues

#### Issue: `Type conversion errors`

**Symptoms:**
```python
TypeError: Object of type 'datetime' is not JSON serializable
```

**Solutions:**

1. **Convert datetime objects**
   ```python
   from datetime import datetime
   
   # ❌ Raw datetime object
   user = db.create("user", {"created_at": datetime.now()})
   
   # ✅ Convert to ISO string
   user = db.create("user", {"created_at": datetime.now().isoformat()})
   ```

2. **Use SurrealDB data types**
   ```python
   from surrealdb.data import RecordID, Duration
   from surrealdb.data.types import GeometryPoint
   
   # Use appropriate types
   user = db.create("user", {
       "name": "John",
       "manager": RecordID("user", "admin"),
       "location": GeometryPoint(-122.4194, 37.7749),
       "session_timeout": Duration.parse("30m")
   })
   ```

#### Issue: `RecordID parsing errors`

**Symptoms:**
```python
ValueError: invalid string provided for parse. the expected string format is "table_name:record_id"
```

**Solutions:**

1. **Check RecordID format**
   ```python
   from surrealdb.data import RecordID
   
   # ❌ Invalid format
   try:
       record_id = RecordID.parse("user_123")  # Missing colon
   except ValueError as e:
       print(f"Parse error: {e}")
   
   # ✅ Correct format
   record_id = RecordID.parse("user:123")
   ```

2. **Validate before parsing**
   ```python
   def safe_parse_record_id(record_str):
       if ":" not in record_str:
           raise ValueError(f"Invalid RecordID format: {record_str}")
       return RecordID.parse(record_str)
   ```

### Performance Issues

#### Issue: Slow query performance

**Solutions:**

1. **Use indexes**
   ```python
   # Create indexes for frequently queried fields
   db.query("DEFINE INDEX user_email ON user FIELDS email UNIQUE")
   db.query("DEFINE INDEX user_age ON user FIELDS age")
   ```

2. **Optimize queries**
   ```python
   # ❌ Inefficient - selects all fields
   users = db.query("SELECT * FROM user WHERE age > 25")
   
   # ✅ Efficient - select only needed fields
   users = db.query("SELECT id, name, email FROM user WHERE age > 25")
   ```

3. **Use LIMIT and pagination**
   ```python
   # ❌ Loads all records
   all_users = db.select("user")
   
   # ✅ Use pagination
   page_size = 50
   page = 1
   users = db.query(
       "SELECT * FROM user ORDER BY id LIMIT $limit START $start",
       {"limit": page_size, "start": (page - 1) * page_size}
   )
   ```

#### Issue: Memory usage too high

**Solutions:**

1. **Process data in batches**
   ```python
   def process_large_table(db, table_name, batch_size=1000):
       offset = 0
       while True:
           batch = db.query(
               f"SELECT * FROM {table_name} ORDER BY id LIMIT {batch_size} START {offset}"
           )
           if not batch:
               break
           
           # Process batch
           for record in batch:
               # Your processing logic
               pass
           
           offset += batch_size
   ```

2. **Use streaming for live queries**
   ```python
   def stream_live_updates(db, table_name):
       live_id = db.live(table_name)
       try:
           for update in db.subscribe_live(live_id):
               # Process update immediately
               process_update(update)
               # Don't accumulate updates in memory
       finally:
           db.kill(live_id)
   ```

### Async/Await Issues

#### Issue: `RuntimeError: This event loop is already running`

**Solutions:**

1. **Use proper async context**
   ```python
   import asyncio
   from surrealdb import AsyncSurreal
   
   # ❌ Wrong - mixing sync and async
   async def wrong_way():
       db = AsyncSurreal("ws://localhost:8000/rpc")
       # This will cause issues
   
   # ✅ Correct - proper async usage
   async def correct_way():
       async with AsyncSurreal("ws://localhost:8000/rpc") as db:
           await db.signin({"username": "root", "password": "root"})
           users = await db.select("user")
   ```

2. **Don't mix sync and async**
   ```python
   # ❌ Wrong - using sync connection in async function
   async def mixed_wrong():
       db = Surreal("ws://localhost:8000/rpc")  # Sync connection
       users = db.select("user")  # This blocks the event loop
   
   # ✅ Correct - use async connection
   async def async_correct():
       async with AsyncSurreal("ws://localhost:8000/rpc") as db:
           await db.signin({"username": "root", "password": "root"})
           users = await db.select("user")
   ```

#### Issue: `Task was destroyed but it is pending`

**Solutions:**

1. **Properly handle async tasks**
   ```python
   import asyncio
   
   async def handle_live_query():
       async with AsyncSurreal("ws://localhost:8000/rpc") as db:
           await db.signin({"username": "root", "password": "root"})
           
           live_id = await db.live("user")
           
           try:
               async for update in db.subscribe_live(live_id):
                   print(f"Update: {update}")
           except asyncio.CancelledError:
               print("Live query cancelled")
           finally:
               await db.kill(live_id)
   
   # Proper task management
   async def main():
       task = asyncio.create_task(handle_live_query())
       
       # Let it run for a while
       await asyncio.sleep(10)
       
       # Cancel gracefully
       task.cancel()
       try:
           await task
       except asyncio.CancelledError:
           print("Task cancelled successfully")
   ```

## Debugging Techniques

### Enable Logging

```python
import logging
from surrealdb import Surreal

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_connection():
    try:
        with Surreal("ws://localhost:8000/rpc") as db:
            logger.debug("Attempting to connect...")
            
            db.signin({"username": "root", "password": "root"})
            logger.debug("Authentication successful")
            
            db.use("debug", "test")
            logger.debug("Namespace and database selected")
            
            users = db.select("user")
            logger.debug(f"Retrieved {len(users)} users")
            
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
```

### Connection Testing

```python
def test_connection(url):
    """Test connection and basic operations"""
    
    print(f"Testing connection to: {url}")
    
    try:
        # Test connection
        with Surreal(url) as db:
            print("✅ Connection established")
            
            # Test authentication
            db.signin({"username": "root", "password": "root"})
            print("✅ Authentication successful")
            
            # Test namespace/database
            db.use("test", "test")
            print("✅ Namespace/database selected")
            
            # Test basic query
            result = db.query("SELECT * FROM user LIMIT 1")
            print(f"✅ Query successful: {len(result)} records")
            
            # Test version
            version = db.version()
            print(f"✅ Server version: {version}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

# Test different connection types
test_connection("ws://localhost:8000/rpc")
test_connection("http://localhost:8000")
```

### Query Debugging

```python
def debug_query(db, query, variables=None):
    """Debug query execution with detailed logging"""
    
    print(f"Executing query: {query}")
    if variables:
        print(f"Variables: {variables}")
    
    try:
        start_time = time.time()
        result = db.query(query, variables)
        end_time = time.time()
        
        print(f"✅ Query successful")
        print(f"   Execution time: {end_time - start_time:.3f}s")
        print(f"   Result count: {len(result) if isinstance(result, list) else 1}")
        print(f"   Result preview: {str(result)[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        print(f"   Query: {query}")
        print(f"   Variables: {variables}")
        raise
```

### Live Query Debugging

```python
import threading
import time

def debug_live_query(db, table_name, duration=10):
    """Debug live query functionality"""
    
    print(f"Starting live query debug for table: {table_name}")
    
    try:
        # Start live query
        live_id = db.live(table_name)
        print(f"✅ Live query started: {live_id}")
        
        # Track updates
        update_count = 0
        
        def listen_for_updates():
            nonlocal update_count
            try:
                for update in db.subscribe_live(live_id):
                    update_count += 1
                    print(f"📡 Live update #{update_count}: {update}")
            except Exception as e:
                print(f"❌ Live query error: {e}")
        
        # Start listener thread
        listener = threading.Thread(target=listen_for_updates, daemon=True)
        listener.start()
        
        # Generate test updates
        print(f"Generating test updates for {duration} seconds...")
        for i in range(duration):
            try:
                test_record = db.create(table_name, {
                    "test_field": f"test_value_{i}",
                    "timestamp": time.time()
                })
                print(f"📝 Created test record: {test_record[0]['id']}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Failed to create test record: {e}")
        
        # Stop live query
        time.sleep(1)
        db.kill(live_id)
        print(f"🛑 Live query stopped")
        print(f"📊 Total updates received: {update_count}")
        
    except Exception as e:
        print(f"❌ Live query debug failed: {e}")
```

## Environment-Specific Issues

### Docker Issues

**Issue: Cannot connect to SurrealDB in Docker**

```bash
# Check if container is running
docker ps | grep surrealdb

# Check container logs
docker logs <container_name>

# Ensure port mapping
docker run -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root memory
```

### Network Issues

**Issue: Connection works locally but not remotely**

1. **Check firewall settings**
2. **Verify network configuration**
3. **Use correct external IP/domain**

```python
# ❌ Wrong - using localhost for remote connection
db = Surreal("ws://localhost:8000/rpc")

# ✅ Correct - using actual server address
db = Surreal("ws://your-server.com:8000/rpc")
```

### SSL/TLS Issues

**Issue: SSL certificate errors**

```python
# For development only - disable SSL verification
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Better solution - use proper certificates in production
db = Surreal("wss://secure-server.com/rpc")
```

## Getting Help

### Collect Debug Information

When reporting issues, include:

1. **Python version**: `python --version`
2. **SDK version**: `pip show surrealdb`
3. **SurrealDB version**: Check server logs or use `db.version()`
4. **Operating system**: Windows/macOS/Linux
5. **Connection type**: WebSocket/HTTP, sync/async
6. **Error messages**: Full stack trace
7. **Minimal reproduction code**

### Debug Information Script

```python
import sys
import platform
from surrealdb import Surreal

def collect_debug_info():
    """Collect system and SDK information for debugging"""
    
    print("=== Debug Information ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    
    try:
        import surrealdb
        print(f"SurrealDB SDK version: {surrealdb.__version__}")
    except:
        print("SurrealDB SDK version: Unknown")
    
    # Test connection
    try:
        with Surreal("ws://localhost:8000/rpc") as db:
            db.signin({"username": "root", "password": "root"})
            version = db.version()
            print(f"SurrealDB server version: {version}")
    except Exception as e:
        print(f"Server connection failed: {e}")
    
    print("========================")

collect_debug_info()
```

### Community Resources

- **Discord**: [https://surrealdb.com/discord](https://surrealdb.com/discord)
- **GitHub Issues**: [https://github.com/surrealdb/surrealdb.py/issues](https://github.com/surrealdb/surrealdb.py/issues)
- **Documentation**: [https://surrealdb.com/docs](https://surrealdb.com/docs)
- **Stack Overflow**: Tag questions with `surrealdb` and `python`

---

**Still having issues?** Join our [Discord community](https://surrealdb.com/discord) for real-time help and support.