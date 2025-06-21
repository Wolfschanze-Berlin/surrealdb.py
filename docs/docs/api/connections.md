---
sidebar_position: 1
---

# Connections API Reference

This reference provides detailed information about all connection classes and their methods in the SurrealDB Python SDK.

## Connection Classes

### Factory Functions

#### `Surreal(url: str)`

Auto-detecting factory function that returns the appropriate synchronous connection based on the URL scheme.

**Parameters:**
- `url` (str): Database connection URL

**Returns:**
- `BlockingWsSurrealConnection` for `ws://` or `wss://` URLs
- `BlockingHttpSurrealConnection` for `http://` or `https://` URLs

**Raises:**
- `ValueError`: If URL scheme is not supported

```python
from surrealdb import Surreal

# WebSocket connection
db = Surreal("ws://localhost:8000/rpc")

# HTTP connection  
db = Surreal("http://localhost:8000")
```

#### `AsyncSurreal(url: str)`

Auto-detecting factory function that returns the appropriate asynchronous connection based on the URL scheme.

**Parameters:**
- `url` (str): Database connection URL

**Returns:**
- `AsyncWsSurrealConnection` for `ws://` or `wss://` URLs
- `AsyncHttpSurrealConnection` for `http://` or `https://` URLs

**Raises:**
- `ValueError`: If URL scheme is not supported

```python
from surrealdb import AsyncSurreal

# Async WebSocket connection
db = AsyncSurreal("ws://localhost:8000/rpc")

# Async HTTP connection
db = AsyncSurreal("http://localhost:8000")
```

### WebSocket Connections

#### `BlockingWsSurrealConnection`

Synchronous WebSocket connection to SurrealDB.

**Constructor:**
```python
BlockingWsSurrealConnection(url: str)
```

**Parameters:**
- `url` (str): WebSocket URL (ws:// or wss://)

**Attributes:**
- `url` (Url): Parsed URL object
- `raw_url` (str): Full WebSocket URL with /rpc endpoint
- `host` (Optional[str]): Server hostname
- `port` (Optional[int]): Server port
- `token` (Optional[str]): Authentication token
- `socket`: WebSocket connection object

```python
from surrealdb.connections import BlockingWsSurrealConnection

db = BlockingWsSurrealConnection("ws://localhost:8000/rpc")
```

#### `AsyncWsSurrealConnection`

Asynchronous WebSocket connection to SurrealDB.

**Constructor:**
```python
AsyncWsSurrealConnection(url: str)
```

**Parameters:**
- `url` (str): WebSocket URL (ws:// or wss://)

**Attributes:**
- `url` (Url): Parsed URL object
- `raw_url` (str): Full WebSocket URL with /rpc endpoint
- `host` (Optional[str]): Server hostname
- `port` (Optional[int]): Server port
- `token` (Optional[str]): Authentication token
- `socket`: WebSocket connection object
- `loop` (Optional[AbstractEventLoop]): Event loop
- `qry` (dict[str, Future]): Query futures
- `recv_task` (Optional[Task[None]]): Receive task
- `live_queues` (dict[str, list]): Live query queues

```python
from surrealdb.connections import AsyncWsSurrealConnection

db = AsyncWsSurrealConnection("ws://localhost:8000/rpc")
```

### HTTP Connections

#### `BlockingHttpSurrealConnection`

Synchronous HTTP connection to SurrealDB.

**Constructor:**
```python
BlockingHttpSurrealConnection(url: str)
```

**Parameters:**
- `url` (str): HTTP URL (http:// or https://)

```python
from surrealdb.connections import BlockingHttpSurrealConnection

db = BlockingHttpSurrealConnection("http://localhost:8000")
```

#### `AsyncHttpSurrealConnection`

Asynchronous HTTP connection to SurrealDB.

**Constructor:**
```python
AsyncHttpSurrealConnection(url: str)
```

**Parameters:**
- `url` (str): HTTP URL (http:// or https://)

```python
from surrealdb.connections import AsyncHttpSurrealConnection

db = AsyncHttpSurrealConnection("http://localhost:8000")
```

## Connection Management Methods

### `connect(url: str) -> None`

Establishes connection to the database server.

**Parameters:**
- `url` (str): Database connection URL

**Async Version:** `async def connect(url: str) -> None`

```python
# Synchronous
db.connect("ws://localhost:8000/rpc")

# Asynchronous
await db.connect("ws://localhost:8000/rpc")
```

### `close() -> None`

Closes the connection to the database server.

**Async Version:** `async def close() -> None`

```python
# Synchronous
db.close()

# Asynchronous
await db.close()
```

### `use(namespace: str, database: str) -> None`

Selects the namespace and database for subsequent operations.

**Parameters:**
- `namespace` (str): Namespace name
- `database` (str): Database name

**Async Version:** `async def use(namespace: str, database: str) -> None`

```python
# Synchronous
db.use("mycompany", "production")

# Asynchronous
await db.use("mycompany", "production")
```

## Authentication Methods

### `signin(vars: Dict) -> str`

Authenticates with the database using credentials.

**Parameters:**
- `vars` (Dict): Authentication variables

**Returns:**
- `str`: Authentication token (if applicable)

**Async Version:** `async def signin(vars: Dict) -> str`

**Authentication Types:**

#### Root User
```python
db.signin({
    "username": "root",
    "password": "root"
})
```

#### Namespace User
```python
db.signin({
    "namespace": "mycompany",
    "username": "admin", 
    "password": "admin123"
})
```

#### Database User
```python
db.signin({
    "namespace": "mycompany",
    "database": "production",
    "username": "user",
    "password": "user123"
})
```

#### Scope User
```python
db.signin({
    "namespace": "mycompany",
    "database": "production", 
    "scope": "user",
    "email": "user@example.com",
    "password": "password123"
})
```

### `signup(vars: Dict) -> str`

Creates a new user account with the specified scope.

**Parameters:**
- `vars` (Dict): Signup variables including scope definition

**Returns:**
- `str`: Authentication token

**Async Version:** `async def signup(vars: Dict) -> str`

```python
token = db.signup({
    "namespace": "mycompany",
    "database": "production",
    "scope": "user", 
    "email": "newuser@example.com",
    "password": "newpassword123",
    "name": "New User"
})
```

### `authenticate(token: str) -> None`

Authenticates using a JWT token.

**Parameters:**
- `token` (str): JWT authentication token

**Async Version:** `async def authenticate(token: str) -> None`

```python
db.authenticate("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...")
```

### `invalidate() -> None`

Invalidates the current authentication session.

**Async Version:** `async def invalidate() -> None`

```python
# Synchronous
db.invalidate()

# Asynchronous
await db.invalidate()
```

### `info() -> dict`

Returns information about the currently authenticated user.

**Returns:**
- `dict`: User information

**Async Version:** `async def info() -> dict`

```python
# Synchronous
user_info = db.info()

# Asynchronous
user_info = await db.info()
```

## CRUD Methods

### `select(thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]`

Retrieves records from the database.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier

**Returns:**
- `Union[List[dict], dict]`: Retrieved records

**Async Version:** `async def select(thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]`

```python
# Select all records from table
users = db.select("user")

# Select specific record
user = db.select("user:123")

# Using RecordID
from surrealdb.data import RecordID
user_id = RecordID("user", "123")
user = db.select(user_id)
```

### `create(thing: Union[str, RecordID, Table], data: Optional[Union[List[dict], dict]] = None) -> Union[List[dict], dict]`

Creates new records in the database.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier
- `data` (Optional[Union[List[dict], dict]]): Record data

**Returns:**
- `Union[List[dict], dict]`: Created records

**Async Version:** `async def create(...) -> Union[List[dict], dict]`

```python
# Create with auto-generated ID
user = db.create("user", {"name": "John", "age": 30})

# Create with specific ID
user = db.create("user:john", {"name": "John", "age": 30})
```

### `insert(table: Union[str, Table], data: Union[List[dict], dict]) -> Union[List[dict], dict]`

Inserts one or more records into a table.

**Parameters:**
- `table` (Union[str, Table]): Table name
- `data` (Union[List[dict], dict]): Record data

**Returns:**
- `Union[List[dict], dict]`: Inserted records

**Async Version:** `async def insert(...) -> Union[List[dict], dict]`

```python
# Insert single record
user = db.insert("user", {"name": "John"})

# Insert multiple records
users = db.insert("user", [
    {"name": "Alice"},
    {"name": "Bob"}
])
```

### `update(thing: Union[str, RecordID, Table], data: Optional[Dict] = None) -> Union[List[dict], dict]`

Updates records by replacing their content entirely.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier
- `data` (Optional[Dict]): New record data

**Returns:**
- `Union[List[dict], dict]`: Updated records

**Async Version:** `async def update(...) -> Union[List[dict], dict]`

```python
# Update specific record (replaces entire content)
user = db.update("user:john", {
    "name": "John Smith",
    "age": 31,
    "active": True
})
```

### `upsert(thing: Union[str, RecordID, Table], data: Optional[Dict] = None) -> Union[List[dict], dict]`

Inserts a record if it doesn't exist, or updates it if it does.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier
- `data` (Optional[Dict]): Record data

**Returns:**
- `Union[List[dict], dict]`: Upserted records

**Async Version:** `async def upsert(...) -> Union[List[dict], dict]`

```python
user = db.upsert("user:john", {
    "name": "John Doe",
    "age": 30,
    "active": True
})
```

### `merge(thing: Union[str, RecordID, Table], data: Optional[Dict] = None) -> Union[List[dict], dict]`

Merges data into existing records without replacing the entire content.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier
- `data` (Optional[Dict]): Data to merge

**Returns:**
- `Union[List[dict], dict]`: Merged records

**Async Version:** `async def merge(...) -> Union[List[dict], dict]`

```python
# Merge additional data
user = db.merge("user:john", {
    "last_login": "2023-01-01T12:00:00Z",
    "login_count": 5
})
```

### `patch(thing: Union[str, RecordID, Table], data: Optional[List[Dict]] = None) -> Union[List[dict], dict]`

Applies JSON Patch operations to records.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier
- `data` (Optional[List[Dict]]): JSON Patch operations

**Returns:**
- `Union[List[dict], dict]`: Patched records

**Async Version:** `async def patch(...) -> Union[List[dict], dict]`

```python
user = db.patch("user:john", [
    {"op": "replace", "path": "/age", "value": 32},
    {"op": "add", "path": "/tags", "value": ["developer"]},
    {"op": "remove", "path": "/temp_field"}
])
```

### `delete(thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]`

Deletes records from the database.

**Parameters:**
- `thing` (Union[str, RecordID, Table]): Table name or record identifier

**Returns:**
- `Union[List[dict], dict]`: Deleted records

**Async Version:** `async def delete(...) -> Union[List[dict], dict]`

```python
# Delete specific record
deleted = db.delete("user:john")

# Delete all records in table
deleted_all = db.delete("user")
```

### `insert_relation(table: Union[str, Table], data: Union[List[dict], dict]) -> Union[List[dict], dict]`

Inserts relation records between other records.

**Parameters:**
- `table` (Union[str, Table]): Relation table name
- `data` (Union[List[dict], dict]): Relation data

**Returns:**
- `Union[List[dict], dict]`: Created relations

**Async Version:** `async def insert_relation(...) -> Union[List[dict], dict]`

```python
relation = db.insert_relation("follows", {
    "in": "user:alice",
    "out": "user:bob",
    "since": "2023-01-01T00:00:00Z"
})
```

## Live Query Methods

### `live(table: Union[str, Table], diff: bool = False) -> UUID`

Starts a live query for a specified table.

**Parameters:**
- `table` (Union[str, Table]): Table name to monitor
- `diff` (bool): Whether to return diffs instead of full records

**Returns:**
- `UUID`: Live query identifier

**Async Version:** `async def live(...) -> UUID`

**Note:** Only available for WebSocket connections.

```python
# Start live query
live_id = db.live("user")

# Start live query with diff mode
live_id_diff = db.live("user", diff=True)
```

### `subscribe_live(query_uuid: Union[str, UUID]) -> Generator[dict, None, None]`

Subscribes to updates from a live query.

**Parameters:**
- `query_uuid` (Union[str, UUID]): Live query identifier

**Returns:**
- `Generator[dict, None, None]`: Stream of live updates

**Async Version:** `async def subscribe_live(...) -> AsyncGenerator[Dict, None]`

**Note:** Only available for WebSocket connections.

```python
# Synchronous
for update in db.subscribe_live(live_id):
    print(f"Live update: {update}")

# Asynchronous
async for update in db.subscribe_live(live_id):
    print(f"Live update: {update}")
```

### `kill(query_uuid: Union[str, UUID]) -> None`

Stops a live query.

**Parameters:**
- `query_uuid` (Union[str, UUID]): Live query identifier to stop

**Async Version:** `async def kill(...) -> None`

**Note:** Only available for WebSocket connections.

```python
# Synchronous
db.kill(live_id)

# Asynchronous
await db.kill(live_id)
```

## Variable Methods

### `let(key: str, value: Any) -> None`

Sets a variable that can be used in subsequent queries.

**Parameters:**
- `key` (str): Variable name
- `value` (Any): Variable value

**Async Version:** `async def let(key: str, value: Any) -> None`

```python
# Set simple variable
db.let("name", "John Doe")

# Set complex variable
db.let("user_data", {
    "name": "John Doe",
    "email": "john@example.com"
})
```

### `unset(key: str) -> None`

Removes a previously set variable.

**Parameters:**
- `key` (str): Variable name to remove

**Async Version:** `async def unset(key: str) -> None`

```python
db.unset("temp_var")
```

## Database Operation Methods

### `query(query: str, vars: Optional[Dict] = None) -> Union[List[dict], dict]`

Executes raw SurrealQL queries.

**Parameters:**
- `query` (str): SurrealQL query string
- `vars` (Optional[Dict]): Query variables

**Returns:**
- `Union[List[dict], dict]`: Query results

**Async Version:** `async def query(...) -> Union[List[dict], dict]`

```python
# Simple query
users = db.query("SELECT * FROM user")

# Query with variables
result = db.query(
    "SELECT * FROM user WHERE age > $min_age",
    {"min_age": 18}
)

# Complex query
result = db.query("""
    BEGIN TRANSACTION;
    CREATE user:john SET name = "John";
    CREATE user:jane SET name = "Jane";
    COMMIT TRANSACTION;
""")
```

### `version() -> str`

Returns the version of the SurrealDB server.

**Returns:**
- `str`: Server version

**Async Version:** `async def version() -> str`

```python
# Synchronous
version = db.version()

# Asynchronous
version = await db.version()
```

## Context Manager Support

All connection classes support context managers for automatic resource management.

### Synchronous Context Manager

```python
from surrealdb import Surreal

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    
    # Your database operations
    users = db.select("user")
    
# Connection automatically closed
```

### Asynchronous Context Manager

```python
import asyncio
from surrealdb import AsyncSurreal

async def main():
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"username": "root", "password": "root"})
        await db.use("myapp", "production")
        
        # Your async database operations
        users = await db.select("user")
        
    # Connection automatically closed

asyncio.run(main())
```

## Error Handling

All methods can raise the following exceptions:

### `SurrealDBMethodError`

Raised when a database operation fails.

```python
from surrealdb.errors import SurrealDBMethodError

try:
    user = db.create("user", {"name": "John"})
except SurrealDBMethodError as e:
    print(f"Database error: {e}")
```

### Connection Errors

Various connection-related errors can occur:

```python
import websockets.exceptions
import requests.exceptions

try:
    with Surreal("ws://localhost:8000/rpc") as db:
        # Your operations
        pass
except websockets.exceptions.ConnectionClosed:
    print("WebSocket connection closed")
except requests.exceptions.ConnectionError:
    print("HTTP connection error")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Type Hints

The SDK provides comprehensive type hints for better IDE support:

```python
from typing import Union, List, Dict, Optional, Any
from uuid import UUID
from surrealdb.data import RecordID, Table

# Method signatures include proper type hints
def select(self, thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]:
    pass

def create(
    self, 
    thing: Union[str, RecordID, Table], 
    data: Optional[Union[List[dict], dict]] = None
) -> Union[List[dict], dict]:
    pass
```

## Next Steps

- **[Methods API](./methods.md)** - Detailed method documentation
- **[Data Types API](./data-types.md)** - Data type reference
- **[Error Handling](./errors.md)** - Exception reference
- **[Examples](../examples/basic-crud.md)** - See the API in action

---

**Need API help?** Join our [Discord community](https://surrealdb.com/discord) for API-specific questions and support.