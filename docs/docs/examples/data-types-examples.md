# SurrealDB Python SDK Data Types Examples

This guide provides comprehensive real-world examples for all SurrealDB Python SDK data types, demonstrating practical usage scenarios and best practices.

## RecordID Examples

The `RecordID` class represents a unique identifier for database records, combining a table name with a specific record identifier.

### Example 1: User Management System

```python
from surrealdb.data.types.record_id import RecordID

# Creating RecordIDs for a user management system
user_id = RecordID("users", "john_doe_123")
admin_id = RecordID("users", "admin_001")
profile_id = RecordID("profiles", "profile_456")

print(f"User ID: {user_id}")  # Output: users:john_doe_123
print(f"Admin ID: {admin_id}")  # Output: users:admin_001
print(f"Profile ID: {profile_id}")  # Output: profiles:profile_456

# Using RecordID in database operations
async def get_user_profile(db, user_record_id: RecordID):
    """Fetch user profile using RecordID"""
    result = await db.select(user_record_id)
    return result

# Parsing string representations back to RecordID objects
user_string = "users:jane_smith_789"
parsed_user_id = RecordID.parse(user_string)
print(f"Parsed user: {parsed_user_id.table_name}, ID: {parsed_user_id.id}")
```

### Example 2: E-commerce Order System

```python
from surrealdb.data.types.record_id import RecordID
import uuid

# E-commerce system with different ID types
order_id = RecordID("orders", str(uuid.uuid4()))
product_id = RecordID("products", "SKU-LAPTOP-001")
customer_id = RecordID("customers", 12345)

# Creating relationships between records
class OrderManager:
    def __init__(self):
        self.orders = {}
    
    def create_order(self, customer_record_id: RecordID, product_record_ids: list[RecordID]):
        """Create an order linking customer and products"""
        order_record_id = RecordID("orders", str(uuid.uuid4()))
        
        order_data = {
            "id": order_record_id,
            "customer": customer_record_id,
            "products": product_record_ids,
            "status": "pending"
        }
        
        self.orders[str(order_record_id)] = order_data
        return order_record_id
    
    def get_order_by_string(self, order_string: str) -> RecordID:
        """Parse order string and return RecordID"""
        try:
            return RecordID.parse(order_string)
        except ValueError as e:
            print(f"Invalid order format: {e}")
            return None

# Usage example
order_manager = OrderManager()
customer = RecordID("customers", "CUST_001")
products = [
    RecordID("products", "PROD_LAPTOP"),
    RecordID("products", "PROD_MOUSE")
]

new_order = order_manager.create_order(customer, products)
print(f"Created order: {new_order}")
```

### Example 3: Content Management System

```python
from surrealdb.data.types.record_id import RecordID
from datetime import datetime

# Content management with hierarchical relationships
class ContentManager:
    def __init__(self):
        self.content_hierarchy = {}
    
    def create_article(self, title: str, author_id: str, category_id: str):
        """Create article with author and category relationships"""
        article_slug = title.lower().replace(" ", "_").replace("-", "_")
        article_id = RecordID("articles", article_slug)
        author_record = RecordID("authors", author_id)
        category_record = RecordID("categories", category_id)
        
        article_data = {
            "id": article_id,
            "title": title,
            "author": author_record,
            "category": category_record,
            "created_at": datetime.now(),
            "status": "draft"
        }
        
        return article_data
    
    def create_comment(self, article_string: str, commenter_id: str, content: str):
        """Create comment linked to article"""
        article_id = RecordID.parse(article_string)
        comment_id = RecordID("comments", f"comment_{datetime.now().timestamp()}")
        commenter_record = RecordID("users", commenter_id)
        
        comment_data = {
            "id": comment_id,
            "article": article_id,
            "commenter": commenter_record,
            "content": content,
            "created_at": datetime.now()
        }
        
        return comment_data

# Usage
cms = ContentManager()
article = cms.create_article(
    "Getting Started with SurrealDB", 
    "tech_writer_001", 
    "tutorials"
)
print(f"Article ID: {article['id']}")
print(f"Author: {article['author']}")
print(f"Category: {article['category']}")

comment = cms.create_comment(
    "articles:getting_started_with_surrealdb",
    "user_123",
    "Great tutorial!"
)
print(f"Comment ID: {comment['id']}")
print(f"Article reference: {comment['article']}")
```

## Table Examples

The `Table` class represents a database table by its name, useful for dynamic table operations.

### Example 1: Multi-tenant Application

```python
from surrealdb.data.types.table import Table

class MultiTenantManager:
    def __init__(self):
        self.tenant_tables = {}
    
    def get_tenant_table(self, tenant_id: str, base_table: str) -> Table:
        """Generate tenant-specific table names"""
        tenant_table_name = f"{tenant_id}_{base_table}"
        return Table(tenant_table_name)
    
    def setup_tenant_tables(self, tenant_id: str):
        """Setup all required tables for a tenant"""
        base_tables = ["users", "orders", "products", "invoices"]
        tenant_tables = {}
        
        for base_table in base_tables:
            tenant_table = self.get_tenant_table(tenant_id, base_table)
            tenant_tables[base_table] = tenant_table
            print(f"Created table: {tenant_table}")
        
        self.tenant_tables[tenant_id] = tenant_tables
        return tenant_tables

# Usage
tenant_manager = MultiTenantManager()
company_a_tables = tenant_manager.setup_tenant_tables("company_a")
company_b_tables = tenant_manager.setup_tenant_tables("company_b")

# Access tenant-specific tables
users_table_a = company_a_tables["users"]  # company_a_users
users_table_b = company_b_tables["users"]  # company_b_users

print(f"Company A users table: {users_table_a}")
print(f"Company B users table: {users_table_b}")
print(f"Tables are different: {users_table_a != users_table_b}")
```

### Example 2: Dynamic Schema Management

```python
from surrealdb.data.types.table import Table
from enum import Enum

class TableType(Enum):
    USERS = "users"
    PRODUCTS = "products"
    ORDERS = "orders"
    ANALYTICS = "analytics"
    LOGS = "logs"

class SchemaManager:
    def __init__(self):
        self.tables = {}
        self.table_configs = {}
    
    def register_table(self, table_type: TableType, config: dict = None):
        """Register a table with optional configuration"""
        table = Table(table_type.value)
        self.tables[table_type] = table
        self.table_configs[table_type] = config or {}
        return table
    
    def get_table(self, table_type: TableType) -> Table:
        """Get registered table"""
        return self.tables.get(table_type)
    
    def create_partitioned_table(self, base_table_type: TableType, partition_key: str) -> Table:
        """Create partitioned table based on key"""
        base_table = self.get_table(base_table_type)
        partitioned_name = f"{base_table.table_name}_{partition_key}"
        return Table(partitioned_name)
    
    def get_time_partitioned_table(self, table_type: TableType, year: int, month: int) -> Table:
        """Create time-partitioned table"""
        base_table = self.get_table(table_type)
        partition_suffix = f"{year}_{month:02d}"
        partitioned_name = f"{base_table.table_name}_{partition_suffix}"
        return Table(partitioned_name)

# Usage
schema_manager = SchemaManager()

# Register base tables
schema_manager.register_table(TableType.USERS, {"indexed_fields": ["email", "username"]})
schema_manager.register_table(TableType.ORDERS, {"partitioned": True})
schema_manager.register_table(TableType.ANALYTICS, {"time_partitioned": True})

# Get base tables
users_table = schema_manager.get_table(TableType.USERS)
orders_table = schema_manager.get_table(TableType.ORDERS)

# Create partitioned tables
orders_2024 = schema_manager.create_partitioned_table(TableType.ORDERS, "2024")
analytics_jan_2024 = schema_manager.get_time_partitioned_table(TableType.ANALYTICS, 2024, 1)
analytics_feb_2024 = schema_manager.get_time_partitioned_table(TableType.ANALYTICS, 2024, 2)

print(f"Base users table: {users_table}")
print(f"Orders 2024 table: {orders_2024}")
print(f"Analytics Jan 2024: {analytics_jan_2024}")
print(f"Analytics Feb 2024: {analytics_feb_2024}")
```

### Example 3: Database Migration System

```python
from surrealdb.data.types.table import Table
from typing import List, Dict

class MigrationManager:
    def __init__(self):
        self.migrations = []
        self.applied_migrations = set()
    
    def add_migration(self, version: str, tables_to_create: List[str], 
                     tables_to_modify: List[str] = None, 
                     tables_to_drop: List[str] = None):
        """Add a database migration"""
        migration = {
            "version": version,
            "create_tables": [Table(name) for name in tables_to_create],
            "modify_tables": [Table(name) for name in (tables_to_modify or [])],
            "drop_tables": [Table(name) for name in (tables_to_drop or [])]
        }
        self.migrations.append(migration)
    
    def get_migration_tables(self, version: str) -> Dict[str, List[Table]]:
        """Get tables affected by a specific migration"""
        for migration in self.migrations:
            if migration["version"] == version:
                return {
                    "create": migration["create_tables"],
                    "modify": migration["modify_tables"],
                    "drop": migration["drop_tables"]
                }
        return {}
    
    def simulate_migration(self, version: str):
        """Simulate migration execution"""
        tables = self.get_migration_tables(version)
        
        print(f"Migration {version}:")
        
        if tables.get("create"):
            print("  Creating tables:")
            for table in tables["create"]:
                print(f"    - {table}")
        
        if tables.get("modify"):
            print("  Modifying tables:")
            for table in tables["modify"]:
                print(f"    - {table}")
        
        if tables.get("drop"):
            print("  Dropping tables:")
            for table in tables["drop"]:
                print(f"    - {table}")

# Usage
migration_manager = MigrationManager()

# Add migrations
migration_manager.add_migration(
    "v1.0.0",
    tables_to_create=["users", "profiles", "sessions"]
)

migration_manager.add_migration(
    "v1.1.0",
    tables_to_create=["orders", "order_items"],
    tables_to_modify=["users"]
)

migration_manager.add_migration(
    "v1.2.0",
    tables_to_create=["analytics_events"],
    tables_to_modify=["orders", "users"],
    tables_to_drop=["old_sessions"]
)

# Simulate migrations
migration_manager.simulate_migration("v1.0.0")
migration_manager.simulate_migration("v1.1.0")
migration_manager.simulate_migration("v1.2.0")
```

## Duration Examples

The `Duration` class represents time intervals with nanosecond precision, supporting various time units.

### Example 1: Performance Monitoring System

```python
from surrealdb.data.types.duration import Duration
import time
from typing import Dict, List

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[Duration]] = {}
        self.thresholds: Dict[str, Duration] = {}
    
    def set_threshold(self, operation: str, threshold_str: str):
        """Set performance threshold for an operation"""
        self.thresholds[operation] = Duration.parse(threshold_str)
    
    def record_operation(self, operation: str, duration: Duration):
        """Record operation duration"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
    
    def check_threshold_violation(self, operation: str, duration: Duration) -> bool:
        """Check if operation exceeded threshold"""
        threshold = self.thresholds.get(operation)
        if threshold:
            return duration.elapsed > threshold.elapsed
        return False
    
    def get_average_duration(self, operation: str) -> Duration:
        """Calculate average duration for an operation"""
        durations = self.metrics.get(operation, [])
        if not durations:
            return Duration(0)
        
        total_elapsed = sum(d.elapsed for d in durations)
        avg_elapsed = total_elapsed // len(durations)
        return Duration(avg_elapsed)
    
    def get_performance_report(self, operation: str) -> dict:
        """Generate performance report for an operation"""
        durations = self.metrics.get(operation, [])
        if not durations:
            return {"operation": operation, "status": "no_data"}
        
        avg_duration = self.get_average_duration(operation)
        max_duration = max(durations, key=lambda d: d.elapsed)
        min_duration = min(durations, key=lambda d: d.elapsed)
        
        return {
            "operation": operation,
            "count": len(durations),
            "average": avg_duration.to_string(),
            "maximum": max_duration.to_string(),
            "minimum": min_duration.to_string(),
            "threshold": self.thresholds.get(operation, Duration(0)).to_string()
        }

# Usage
monitor = PerformanceMonitor()

# Set thresholds
monitor.set_threshold("database_query", "100ms")
monitor.set_threshold("api_request", "500ms")
monitor.set_threshold("file_upload", "5s")

# Simulate recording operations
operations = [
    ("database_query", Duration.parse("50ms")),
    ("database_query", Duration.parse("120ms")),  # Exceeds threshold
    ("database_query", Duration.parse("80ms")),
    ("api_request", Duration.parse("300ms")),
    ("api_request", Duration.parse("600ms")),  # Exceeds threshold
    ("file_upload", Duration.parse("3s")),
    ("file_upload", Duration.parse("7s")),  # Exceeds threshold
]

for operation, duration in operations:
    monitor.record_operation(operation, duration)
    if monitor.check_threshold_violation(operation, duration):
        print(f"⚠️  {operation} exceeded threshold: {duration.to_string()}")

# Generate reports
for operation in ["database_query", "api_request", "file_upload"]:
    report = monitor.get_performance_report(operation)
    print(f"\n📊 Performance Report for {operation}:")
    for key, value in report.items():
        print(f"  {key}: {value}")
```

### Example 2: Task Scheduling System

```python
from surrealdb.data.types.duration import Duration
from datetime import datetime, timedelta
from typing import Optional

class TaskScheduler:
    def __init__(self):
        self.tasks = {}
        self.recurring_tasks = {}
    
    def schedule_task(self, task_id: str, delay: Duration, task_func=None):
        """Schedule a task to run after a delay"""
        execute_at = datetime.now() + timedelta(seconds=delay.seconds)
        
        self.tasks[task_id] = {
            "delay": delay,
            "execute_at": execute_at,
            "function": task_func,
            "status": "scheduled"
        }
        
        print(f"Task '{task_id}' scheduled to run in {delay.to_string()}")
    
    def schedule_recurring_task(self, task_id: str, interval: Duration, task_func=None):
        """Schedule a recurring task"""
        next_run = datetime.now() + timedelta(seconds=interval.seconds)
        
        self.recurring_tasks[task_id] = {
            "interval": interval,
            "next_run": next_run,
            "function": task_func,
            "run_count": 0
        }
        
        print(f"Recurring task '{task_id}' scheduled every {interval.to_string()}")
    
    def get_task_info(self, task_id: str) -> Optional[dict]:
        """Get information about a scheduled task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            time_remaining = task["execute_at"] - datetime.now()
            remaining_duration = Duration.parse(f"{int(time_remaining.total_seconds())}s")
            
            return {
                "type": "one_time",
                "delay": task["delay"].to_string(),
                "time_remaining": remaining_duration.to_string(),
                "status": task["status"]
            }
        
        elif task_id in self.recurring_tasks:
            task = self.recurring_tasks[task_id]
            time_to_next = task["next_run"] - datetime.now()
            next_duration = Duration.parse(f"{int(time_to_next.total_seconds())}s")
            
            return {
                "type": "recurring",
                "interval": task["interval"].to_string(),
                "time_to_next": next_duration.to_string(),
                "run_count": task["run_count"]
            }
        
        return None

# Usage
scheduler = TaskScheduler()

# Schedule various tasks with different durations
scheduler.schedule_task("backup_database", Duration.parse("1h"))
scheduler.schedule_task("send_notifications", Duration.parse("30m"))
scheduler.schedule_task("cleanup_temp_files", Duration.parse("2h"))

# Schedule recurring tasks
scheduler.schedule_recurring_task("health_check", Duration.parse("5m"))
scheduler.schedule_recurring_task("log_rotation", Duration.parse("1d"))
scheduler.schedule_recurring_task("cache_cleanup", Duration.parse("6h"))

# Check task information
for task_id in ["backup_database", "health_check", "log_rotation"]:
    info = scheduler.get_task_info(task_id)
    if info:
        print(f"\n📋 Task: {task_id}")
        for key, value in info.items():
            print(f"  {key}: {value}")
```

### Example 3: Rate Limiting System

```python
from surrealdb.data.types.duration import Duration
from datetime import datetime, timedelta
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self):
        self.limits = {}
        self.requests = defaultdict(deque)
    
    def set_rate_limit(self, identifier: str, max_requests: int, window: Duration):
        """Set rate limit for an identifier"""
        self.limits[identifier] = {
            "max_requests": max_requests,
            "window": window,
            "window_seconds": window.seconds
        }
    
    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """Check if request is allowed under rate limit"""
        if identifier not in self.limits:
            return True, {"status": "no_limit"}
        
        limit_config = self.limits[identifier]
        window_seconds = limit_config["window_seconds"]
        max_requests = limit_config["max_requests"]
        
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        # Remove old requests outside the window
        request_times = self.requests[identifier]
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        current_count = len(request_times)
        allowed = current_count < max_requests
        
        if allowed:
            request_times.append(now)
        
        # Calculate reset time
        if request_times:
            oldest_request = request_times[0]
            reset_time = oldest_request + timedelta(seconds=window_seconds)
            time_to_reset = reset_time - now
            reset_duration = Duration.parse(f"{int(time_to_reset.total_seconds())}s")
        else:
            reset_duration = Duration(0)
        
        return allowed, {
            "allowed": allowed,
            "current_count": current_count,
            "max_requests": max_requests,
            "window": limit_config["window"].to_string(),
            "reset_in": reset_duration.to_string(),
            "remaining": max_requests - current_count if allowed else 0
        }

# Usage
rate_limiter = RateLimiter()

# Set different rate limits
rate_limiter.set_rate_limit("api_user_123", 100, Duration.parse("1h"))
rate_limiter.set_rate_limit("api_user_456", 1000, Duration.parse("1d"))
rate_limiter.set_rate_limit("guest_user", 10, Duration.parse("1m"))

# Simulate API requests
def simulate_requests(user_id: str, num_requests: int):
    print(f"\n🔄 Simulating {num_requests} requests for {user_id}")
    
    for i in range(num_requests):
        allowed, info = rate_limiter.is_allowed(user_id)
        
        if allowed:
            print(f"  ✅ Request {i+1}: Allowed (Remaining: {info['remaining']})")
        else:
            print(f"  ❌ Request {i+1}: Rate limited (Reset in: {info['reset_in']})")
            break

# Test rate limiting
simulate_requests("guest_user", 15)  # Should hit limit quickly
simulate_requests("api_user_123", 5)  # Should be fine

# Check current status
for user_id in ["guest_user", "api_user_123"]:
    allowed, info = rate_limiter.is_allowed(user_id)
    print(f"\n📊 Rate limit status for {user_id}:")
    for key, value in info.items():
        print(f"  {key}: {value}")
```

## DateTime Examples

The `IsoDateTimeWrapper` class handles ISO 8601 datetime strings for database operations.

### Example 1: Event Management System

```python
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from datetime import datetime, timezone, timedelta
import json

class EventManager:
    def __init__(self):
        self.events = {}
        self.timezone_offset = timezone.utc
    
    def create_event(self, event_id: str, title: str, start_time: datetime, 
                    duration_hours: int = 1, timezone_name: str = "UTC"):
        """Create an event with datetime handling"""
        # Ensure datetime is timezone-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Convert to ISO format for SurrealDB
        start_iso = IsoDateTimeWrapper(start_time.isoformat())
        end_iso = IsoDateTimeWrapper(end_time.isoformat())
        created_iso = IsoDateTimeWrapper(datetime.now(timezone.utc).isoformat())
        
        event_data = {
            "id": event_id,
            "title": title,
            "start_time": start_iso,
            "end_time": end_iso,
            "created_at": created_iso,
            "timezone": timezone_name,
            "duration_hours": duration_hours
        }
        
        self.events[event_id] = event_data
        return event_data
    
    def get_events_in_range(self, start_date: datetime, end_date: datetime):
        """Get events within a date range"""
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        
        matching_events = []
        for event in self.events.values():
            event_start = event["start_time"].dt
            if start_iso <= event_start <= end_iso:
                matching_events.append(event)
        
        return matching_events
    
    def update_event_time(self, event_id: str, new_start_time: datetime):
        """Update event start time"""
        if event_id not in self.events:
            return None
        
        event = self.events[event_id]
        duration = event["duration_hours"]
        
        # Ensure timezone awareness
        if new_start_time.tzinfo is None:
            new_start_time = new_start_time.replace(tzinfo=timezone.utc)
        
        new_end_time = new_start_time + timedelta(hours=duration)
        
        # Update with new ISO datetime wrappers
        event["start_time"] = IsoDateTimeWrapper(new_start_time.isoformat())
        event["end_time"] = IsoDateTimeWrapper(new_end_time.isoformat())
        event["updated_at"] = IsoDateTimeWrapper(datetime.now(timezone.utc).isoformat())
        
        return event

# Usage
event_manager = EventManager()

# Create events with different timezones
utc_time = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
pst_time = datetime(2024, 6, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=-8)))
est_time = datetime(2024, 6, 15, 16, 45, 0, tzinfo=timezone(timedelta(hours=-5)))

# Create events
meeting_event = event_manager.create_event(
    "meeting_001", 
    "Team Standup", 
    utc_time, 
    duration_hours=1
)

conference_event = event_manager.create_event(
    "conf_001", 
    "Tech Conference", 
    pst_time, 
    duration_hours=8, 
    timezone_name="PST"
)

webinar_event = event_manager.create_event(
    "webinar_001", 
    "SurrealDB Workshop", 
    est_time, 
    duration_hours=2, 
    timezone_name="EST"
)

# Display events
print("📅 Created Events:")
for event_id, event in event_manager.events.items():
    print(f"\n{event['title']} ({event_id}):")
    print(f"  Start: {event['start_time'].dt}")
    print(f"  End: {event['end_time'].dt}")
    print(f"  Created: {event['created_at'].dt}")
    print(f"  Timezone: {event['timezone']}")

# Update an event
new_time = datetime(2024, 6, 15, 15, 0, 0, tzinfo=timezone.utc)
updated_event = event_manager.update_event_time("meeting_001", new_time)
if updated_event:
    print(f"\n✅ Updated meeting time:")
    print(f"  New start: {updated_event['start_time'].dt}")
    print(f"  Updated at: {updated_event['updated_at'].dt}")
```

### Example 2: Audit Log System

```python
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List

class AuditAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"

class AuditLogger:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.session_logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def log_action(self, user_id: str, action: AuditAction, resource: str, 
                  details: Dict[str, Any] = None, session_id: str = None):
        """Log an audit action with timestamp"""
        timestamp = IsoDateTimeWrapper(datetime.now(timezone.utc).isoformat())
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action.value,
            "resource": resource,
            "details": details or {},
            "session_id": session_id
        }
        
        self.logs.append(log_entry)
        
        # Also track by session if provided
        if session_id:
            if session_id not in self.session_logs:
                self.session_logs[session_id] = []
            self.session_logs[session_id].append(log_entry)
        
        return log_entry
    
    def get_user_activity(self, user_id: str, start_date: datetime = None, 
                         end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get user activity within date range"""
        user_logs = [log for log in self.logs if log["user_id"] == user_id]
        
        if start_date or end_date:
            filtered_logs = []
            start_iso = start_date.isoformat() if start_date else None
            end_iso = end_date.isoformat() if end_date else None
            
            for log in user_logs:
                log_time = log["timestamp"].dt
                
                if start_iso and log_time < start_iso:
                    continue
                if end_iso and log_time > end_iso:
                    continue
                
                filtered_logs.append(log)
            
            return filtered_logs
        
        return user_logs
    
    def get_session_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all activity for a session"""
        return self.session_logs.get(session_id, [])
    
    def generate_activity_report(self, user_id: str, days_back: int = 7) -> Dict[str, Any]:
        """Generate activity report for user"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date -