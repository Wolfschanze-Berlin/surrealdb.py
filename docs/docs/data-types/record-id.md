---
sidebar_position: 2
---

# Record ID

Record IDs are unique identifiers for records in SurrealDB. They consist of a table name and an identifier, providing a way to reference specific records across your database. The Python SDK provides the `RecordID` class to work with these identifiers efficiently.

## Overview

A Record ID in SurrealDB has the format `table:identifier`, where:
- **table**: The name of the table containing the record
- **identifier**: A unique identifier within that table (string, number, or complex type)

## RecordID Class

### Constructor

```python
from surrealdb.data import RecordID

# Create a RecordID
record_id = RecordID(table_name="user", identifier="john_doe")
print(record_id)  # Output: user:john_doe
```

### Class Definition

```python
class RecordID:
    def __init__(self, table_name: str, identifier) -> None:
        """
        Create a new RecordID instance.
        
        Args:
            table_name: The table name
            identifier: The record identifier (can be string, number, etc.)
        """
        self.table_name = table_name
        self.id = identifier
```

## Creating Record IDs

### Basic Usage

```python
from surrealdb.data import RecordID

# String identifier
user_id = RecordID("user", "john_doe")
print(f"User ID: {user_id}")  # user:john_doe

# Numeric identifier
product_id = RecordID("product", 12345)
print(f"Product ID: {product_id}")  # product:12345

# Complex identifier
session_id = RecordID("session", "abc123-def456-ghi789")
print(f"Session ID: {session_id}")  # session:abc123-def456-ghi789
```

### Using with Database Operations

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    
    # Create record with specific ID
    user_id = RecordID("user", "john_doe")
    user = db.create(user_id, {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    })
    
    print(f"Created user: {user[0]['id']}")
    
    # Select record by ID
    retrieved_user = db.select(user_id)
    print(f"Retrieved user: {retrieved_user[0]['name']}")
    
    # Update record by ID
    updated_user = db.merge(user_id, {"age": 31})
    print(f"Updated user age: {updated_user[0]['age']}")
```

## Parsing Record IDs

### From String

```python
from surrealdb.data import RecordID

# Parse from string format
record_str = "user:john_doe"
parsed_id = RecordID.parse(record_str)

print(f"Table: {parsed_id.table_name}")  # user
print(f"ID: {parsed_id.id}")             # john_doe
print(f"Full ID: {parsed_id}")           # user:john_doe
```

### Error Handling

```python
from surrealdb.data import RecordID

try:
    # Valid format
    valid_id = RecordID.parse("user:john_doe")
    print(f"Parsed: {valid_id}")
    
    # Invalid format (missing colon)
    invalid_id = RecordID.parse("user_john_doe")
    
except ValueError as e:
    print(f"Parse error: {e}")
    # Output: Parse error: invalid string provided for parse. 
    #         the expected string format is "table_name:record_id"
```

## Working with Record IDs in Queries

### Direct Usage

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    
    # Create some users
    alice_id = RecordID("user", "alice")
    bob_id = RecordID("user", "bob")
    
    alice = db.create(alice_id, {"name": "Alice", "role": "admin"})
    bob = db.create(bob_id, {"name": "Bob", "role": "user"})
    
    # Use Record IDs in relationships
    project_id = RecordID("project", "website_redesign")
    project = db.create(project_id, {
        "name": "Website Redesign",
        "owner": alice_id,      # Reference to Alice
        "team": [alice_id, bob_id]  # Array of Record IDs
    })
    
    print(f"Created project: {project[0]['name']}")
    print(f"Owner: {project[0]['owner']}")
    print(f"Team: {project[0]['team']}")
```

### In SurrealQL Queries

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("myapp", "production")
    
    # Use Record ID in query variables
    user_id = RecordID("user", "john_doe")
    
    result = db.query(
        "SELECT * FROM project WHERE owner = $user_id",
        {"user_id": user_id}
    )
    
    print(f"Projects owned by {user_id}: {len(result)}")
    
    # Complex query with multiple Record IDs
    team_ids = [
        RecordID("user", "alice"),
        RecordID("user", "bob"),
        RecordID("user", "charlie")
    ]
    
    team_projects = db.query(
        "SELECT * FROM project WHERE owner IN $team_members",
        {"team_members": team_ids}
    )
    
    print(f"Team projects: {len(team_projects)}")
```

## Record ID Relationships

### One-to-One Relationships

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("relationships", "demo")
    
    # Create user
    user_id = RecordID("user", "john")
    user = db.create(user_id, {
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # Create profile with reference to user
    profile_id = RecordID("profile", "john_profile")
    profile = db.create(profile_id, {
        "user": user_id,  # One-to-one relationship
        "bio": "Software developer",
        "avatar": "https://example.com/avatar.jpg"
    })
    
    # Query with relationship
    result = db.query("""
        SELECT *, user.* as user_details 
        FROM profile 
        WHERE id = $profile_id
    """, {"profile_id": profile_id})
    
    print(f"Profile with user details: {result[0]}")
```

### One-to-Many Relationships

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("relationships", "demo")
    
    # Create author
    author_id = RecordID("author", "jane_doe")
    author = db.create(author_id, {
        "name": "Jane Doe",
        "email": "jane@example.com"
    })
    
    # Create multiple posts by the same author
    post_ids = []
    for i in range(3):
        post_id = RecordID("post", f"post_{i}")
        post = db.create(post_id, {
            "title": f"Post {i + 1}",
            "content": f"Content for post {i + 1}",
            "author": author_id  # Reference to author
        })
        post_ids.append(post_id)
    
    # Query posts by author
    author_posts = db.query("""
        SELECT * FROM post WHERE author = $author_id
    """, {"author_id": author_id})
    
    print(f"Posts by {author['name']}: {len(author_posts)}")
```

### Many-to-Many Relationships

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("relationships", "demo")
    
    # Create users
    alice_id = RecordID("user", "alice")
    bob_id = RecordID("user", "bob")
    charlie_id = RecordID("user", "charlie")
    
    db.create(alice_id, {"name": "Alice"})
    db.create(bob_id, {"name": "Bob"})
    db.create(charlie_id, {"name": "Charlie"})
    
    # Create projects with multiple team members
    project1_id = RecordID("project", "website")
    project2_id = RecordID("project", "mobile_app")
    
    db.create(project1_id, {
        "name": "Website Project",
        "team": [alice_id, bob_id]  # Many-to-many via array
    })
    
    db.create(project2_id, {
        "name": "Mobile App Project",
        "team": [bob_id, charlie_id]  # Bob is on both projects
    })
    
    # Query projects for a specific user
    bob_projects = db.query("""
        SELECT * FROM project WHERE $user_id IN team
    """, {"user_id": bob_id})
    
    print(f"Bob's projects: {len(bob_projects)}")
```

## Advanced Record ID Usage

### Dynamic Record ID Generation

```python
from surrealdb import Surreal
from surrealdb.data import RecordID
import uuid
from datetime import datetime

def generate_record_id(table: str, prefix: str = None) -> RecordID:
    """Generate a unique Record ID with optional prefix"""
    
    if prefix:
        identifier = f"{prefix}_{uuid.uuid4().hex[:8]}"
    else:
        identifier = uuid.uuid4().hex
    
    return RecordID(table, identifier)

def generate_timestamped_id(table: str) -> RecordID:
    """Generate a Record ID with timestamp"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_part = uuid.uuid4().hex[:8]
    identifier = f"{timestamp}_{unique_part}"
    
    return RecordID(table, identifier)

# Usage
with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("advanced", "ids")
    
    # Generate unique IDs
    session_id = generate_record_id("session", "sess")
    log_id = generate_timestamped_id("log")
    
    # Create records with generated IDs
    session = db.create(session_id, {
        "user": "john_doe",
        "started_at": datetime.now().isoformat()
    })
    
    log_entry = db.create(log_id, {
        "level": "INFO",
        "message": "User session started",
        "session": session_id
    })
    
    print(f"Created session: {session_id}")
    print(f"Created log entry: {log_id}")
```

### Record ID Validation

```python
from surrealdb.data import RecordID
import re

def validate_record_id(record_id: RecordID) -> list[str]:
    """Validate a Record ID according to business rules"""
    
    errors = []
    
    # Check table name format
    if not re.match(r'^[a-z][a-z0-9_]*$', record_id.table_name):
        errors.append("Table name must start with lowercase letter and contain only lowercase letters, numbers, and underscores")
    
    # Check identifier format
    identifier = str(record_id.id)
    if len(identifier) < 1:
        errors.append("Identifier cannot be empty")
    elif len(identifier) > 100:
        errors.append("Identifier cannot exceed 100 characters")
    
    # Check for reserved table names
    reserved_tables = ["system", "admin", "root"]
    if record_id.table_name in reserved_tables:
        errors.append(f"Table name '{record_id.table_name}' is reserved")
    
    return errors

# Usage
test_ids = [
    RecordID("user", "john_doe"),           # Valid
    RecordID("User", "john_doe"),           # Invalid: uppercase table
    RecordID("user", ""),                   # Invalid: empty identifier
    RecordID("system", "config"),           # Invalid: reserved table
    RecordID("user_profile", "valid_id"),   # Valid
]

for record_id in test_ids:
    errors = validate_record_id(record_id)
    if errors:
        print(f"❌ {record_id}: {', '.join(errors)}")
    else:
        print(f"✅ {record_id}: Valid")
```

### Record ID Collections

```python
from surrealdb import Surreal
from surrealdb.data import RecordID
from typing import List, Dict

class RecordIDCollection:
    """Utility class for managing collections of Record IDs"""
    
    def __init__(self):
        self.ids: List[RecordID] = []
    
    def add(self, table: str, identifier) -> RecordID:
        """Add a new Record ID to the collection"""
        record_id = RecordID(table, identifier)
        self.ids.append(record_id)
        return record_id
    
    def get_by_table(self, table: str) -> List[RecordID]:
        """Get all Record IDs for a specific table"""
        return [rid for rid in self.ids if rid.table_name == table]
    
    def get_by_identifier(self, identifier) -> List[RecordID]:
        """Get all Record IDs with a specific identifier"""
        return [rid for rid in self.ids if rid.id == identifier]
    
    def group_by_table(self) -> Dict[str, List[RecordID]]:
        """Group Record IDs by table"""
        groups = {}
        for rid in self.ids:
            if rid.table_name not in groups:
                groups[rid.table_name] = []
            groups[rid.table_name].append(rid)
        return groups
    
    def to_strings(self) -> List[str]:
        """Convert all Record IDs to string format"""
        return [str(rid) for rid in self.ids]

# Usage
collection = RecordIDCollection()

# Add various Record IDs
collection.add("user", "alice")
collection.add("user", "bob")
collection.add("project", "website")
collection.add("project", "mobile_app")
collection.add("task", "alice")  # Same identifier, different table

# Query collections
user_ids = collection.get_by_table("user")
alice_ids = collection.get_by_identifier("alice")
grouped = collection.group_by_table()

print(f"User IDs: {[str(rid) for rid in user_ids]}")
print(f"Alice IDs: {[str(rid) for rid in alice_ids]}")
print(f"Grouped: {grouped}")

# Use with database
with Surreal("ws://localhost:8000/rpc") as db:
    db.signin({"username": "root", "password": "root"})
    db.use("collections", "demo")
    
    # Batch operations with Record ID collection
    for table, ids in grouped.items():
        print(f"Processing {len(ids)} records in table '{table}'")
        
        # Example: Delete all records in collection
        for record_id in ids:
            try:
                deleted = db.delete(record_id)
                print(f"  Deleted: {record_id}")
            except Exception as e:
                print(f"  Failed to delete {record_id}: {e}")
```

## Record ID Comparison and Equality

### Equality Operations

```python
from surrealdb.data import RecordID

# Create Record IDs
id1 = RecordID("user", "john")
id2 = RecordID("user", "john")
id3 = RecordID("user", "jane")
id4 = RecordID("profile", "john")

# Test equality
print(f"id1 == id2: {id1 == id2}")  # True (same table and identifier)
print(f"id1 == id3: {id1 == id3}")  # False (different identifier)
print(f"id1 == id4: {id1 == id4}")  # False (different table)

# String representation
print(f"str(id1): {str(id1)}")      # user:john
print(f"repr(id1): {repr(id1)}")    # RecordID(table_name=user, record_id=john)
```

### Sorting Record IDs

```python
from surrealdb.data import RecordID

# Create a list of Record IDs
record_ids = [
    RecordID("user", "charlie"),
    RecordID("project", "alpha"),
    RecordID("user", "alice"),
    RecordID("task", "beta"),
    RecordID("user", "bob"),
]

# Sort by string representation
sorted_ids = sorted(record_ids, key=str)
print("Sorted Record IDs:")
for rid in sorted_ids:
    print(f"  {rid}")

# Sort by table, then by identifier
def sort_key(rid: RecordID):
    return (rid.table_name, str(rid.id))

table_sorted = sorted(record_ids, key=sort_key)
print("\nSorted by table, then identifier:")
for rid in table_sorted:
    print(f"  {rid}")
```

## Best Practices

### ✅ Do

- Use meaningful table names and identifiers
- Validate Record IDs before database operations
- Use the `RecordID.parse()` method for string inputs
- Leverage Record IDs for relationships between records
- Use consistent naming conventions for identifiers

### ❌ Don't

- Use spaces or special characters in table names
- Create overly long identifiers
- Mix different identifier formats within the same table
- Ignore validation errors when parsing Record IDs
- Use reserved words as table names

### Naming Conventions

```python
from surrealdb.data import RecordID

# ✅ Good naming conventions
good_ids = [
    RecordID("user", "john_doe"),
    RecordID("user_profile", "john_doe_profile"),
    RecordID("project", "website_redesign_2024"),
    RecordID("task", "implement_auth_system"),
    RecordID("session", "sess_abc123def456"),
]

# ❌ Poor naming conventions
poor_ids = [
    # RecordID("User", "john doe"),        # Uppercase table, space in ID
    # RecordID("user-profile", "john"),    # Hyphen in table name
    # RecordID("123table", "id"),          # Table starts with number
    # RecordID("user", ""),                # Empty identifier
]

print("Good Record ID examples:")
for rid in good_ids:
    print(f"  {rid}")
```

## Error Handling

### Common Errors and Solutions

```python
from surrealdb import Surreal
from surrealdb.data import RecordID
from surrealdb.errors import SurrealDBMethodError

def safe_record_operations():
    """Demonstrate safe Record ID operations with error handling"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("error_handling", "demo")
        
        try:
            # Safe Record ID creation
            user_id = RecordID("user", "test_user")
            
            # Safe record creation
            user = db.create(user_id, {"name": "Test User"})
            print(f"✅ Created user: {user_id}")
            
            # Safe record retrieval
            retrieved = db.select(user_id)
            if retrieved:
                print(f"✅ Retrieved user: {retrieved[0]['name']}")
            else:
                print(f"⚠️ User not found: {user_id}")
            
            # Safe record deletion
            deleted = db.delete(user_id)
            print(f"✅ Deleted user: {user_id}")
            
        except ValueError as e:
            print(f"❌ Record ID error: {e}")
        except SurrealDBMethodError as e:
            print(f"❌ Database error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

safe_record_operations()
```

## Next Steps

- **[Table Types](./table.md)** - Learn about table references
- **[Geometry Types](./geometry.md)** - Work with spatial data
- **[Duration](./duration.md)** - Handle time intervals
- **[Examples](../examples/basic-crud.md)** - See Record IDs in action

---

**Need help with Record IDs?** Join our [Discord community](https://surrealdb.com/discord) for support and best practices.