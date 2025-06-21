# SurrealDB Python SDK Data Types - Comprehensive Guide

This comprehensive guide provides real-world examples for all SurrealDB Python SDK data types. The examples demonstrate practical usage scenarios, best practices, and integration patterns.

## Table of Contents

### [Part 1: RecordID, Table, and Duration Examples](./data-types-examples.md)

#### RecordID Examples
- **User Management System**: Creating and managing user records with meaningful identifiers
- **E-commerce Order System**: Handling orders, products, and customer relationships
- **Content Management System**: Managing articles, authors, and comments with hierarchical relationships

#### Table Examples
- **Multi-tenant Application**: Dynamic table creation for different tenants
- **Dynamic Schema Management**: Managing tables with configurations and partitioning
- **Database Migration System**: Handling table creation, modification, and deletion

#### Duration Examples
- **Performance Monitoring System**: Tracking operation durations and thresholds
- **Task Scheduling System**: Scheduling one-time and recurring tasks
- **Rate Limiting System**: Implementing rate limits with time windows

### [Part 2: DateTime and Geometry Examples](./data-types-examples-part2.md)

#### DateTime Examples (Continued)
- **Audit Log System**: Comprehensive logging with timestamps and date ranges
- **Time Series Data Management**: Managing time-based data with statistics and downsampling

#### Geometry Examples
- **Location-Based Service**: Points, routes, and zones for geographic applications
- **Geographic Information System (GIS)**: Multi-layer spatial data management
- **Spatial Analysis System**: Point-in-polygon testing and geometric calculations

### [Part 3: Range Examples](./data-types-examples-part3.md)

#### Range Examples
- **Data Validation System**: Numeric and date range validation with inclusive/exclusive bounds
- **Time-based Access Control**: Managing access permissions with time and date ranges

### [Part 4: Future Examples](./data-types-examples-part4.md)

#### Future Examples
- **Asynchronous Task Management**: Managing task dependencies and results
- **Lazy Evaluation System**: Deferred computation with dependency tracking
- **Promise-like Async Operations**: Async operations with callbacks and error handling

## Quick Reference

### Data Type Import Statements

```python
# Core data types
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table
from surrealdb.data.types.duration import Duration
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from surrealdb.data.types.future import Future

# Geometry types
from surrealdb.data.types.geometry import (
    GeometryPoint, GeometryLine, GeometryPolygon,
    GeometryMultiPoint, GeometryMultiLine, GeometryMultiPolygon,
    GeometryCollection
)

# Range types
from surrealdb.data.types.range import Range, BoundIncluded, BoundExcluded
```

### Common Usage Patterns

#### Creating RecordIDs
```python
# Simple record ID
user_id = RecordID("users", "john_doe")

# With UUID
import uuid
order_id = RecordID("orders", str(uuid.uuid4()))

# Parsing from string
parsed_id = RecordID.parse("products:SKU-123")
```

#### Working with Durations
```python
# Create durations
short_duration = Duration.parse("30s")
long_duration = Duration.parse("2h")

# Access properties
seconds = duration.seconds
minutes = duration.minutes
hours = duration.hours
```

#### Geometry Operations
```python
# Create a point
point = GeometryPoint(-122.4194, 37.7749)

# Create a line
line = GeometryLine(
    GeometryPoint(-122.4194, 37.7749),
    GeometryPoint(-122.4098, 37.8085)
)

# Create a polygon
polygon = GeometryPolygon(line)
```

#### Range Validation
```python
# Inclusive range
age_range = Range(BoundIncluded(18), BoundIncluded(65))

# Mixed bounds
score_range = Range(BoundExcluded(0), BoundIncluded(100))
```

## Integration Examples

### Basic SurrealDB Integration

```python
from surrealdb import Surreal
from surrealdb.data.types import RecordID, Duration, GeometryPoint

async def create_user_with_types():
    db = Surreal("ws://localhost:8000/rpc")
    await db.connect()
    await db.use("example", "example")
    
    # Create user with typed data
    user_id = RecordID("users", "alice_123")
    location = GeometryPoint(-122.4194, 37.7749)
    session_timeout = Duration.parse("1h")
    
    result = await db.create(user_id, {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "location": location,
        "session_timeout": session_timeout,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return result
```

### Advanced Query Examples

```python
async def advanced_queries():
    db = Surreal("ws://localhost:8000/rpc")
    await db.connect()
    await db.use("example", "example")
    
    # Query with geometry
    nearby_users = await db.query("""
        SELECT * FROM users 
        WHERE geo::distance(location, $center) < $radius
    """, {
        "center": GeometryPoint(-122.4194, 37.7749),
        "radius": 1000  # meters
    })
    
    # Query with duration
    active_sessions = await db.query("""
        SELECT * FROM sessions 
        WHERE created_at > (time::now() - $timeout)
    """, {
        "timeout": Duration.parse("30m")
    })
    
    return nearby_users, active_sessions
```

## Best Practices Summary

### 1. Type Safety
- Always validate input data before creating typed objects
- Use try-catch blocks when parsing string representations
- Implement proper error handling for all operations

### 2. Performance Considerations
- Cache computed geometry operations when possible
- Use appropriate precision for duration calculations
- Consider using lazy evaluation for expensive computations

### 3. Database Integration
- Use typed objects consistently throughout your application
- Leverage SurrealDB's native support for these data types
- Implement proper serialization/deserialization patterns

### 4. Error Handling
```python
try:
    record_id = RecordID.parse(user_input)
except ValueError as e:
    print(f"Invalid record ID format: {e}")
    # Handle error appropriately

try:
    duration = Duration.parse(time_string)
except (ValueError, TypeError) as e:
    print(f"Invalid duration: {e}")
    # Use default or prompt for correction
```

### 5. Testing Strategies
- Create unit tests for all data type operations
- Test edge cases and boundary conditions
- Validate serialization/deserialization round-trips
- Test integration with actual SurrealDB instances

## Real-World Application Scenarios

### E-commerce Platform
- **RecordID**: Product SKUs, order numbers, customer IDs
- **Duration**: Shipping times, return windows, session timeouts
- **Geometry**: Store locations, delivery zones, customer addresses
- **Range**: Price ranges, age restrictions, date availability

### IoT Data Management
- **DateTime**: Sensor timestamps, event logging
- **Duration**: Measurement intervals, alert timeouts
- **Geometry**: Device locations, coverage areas
- **Future**: Async sensor data processing

### Content Management
- **RecordID**: Article IDs, author profiles, category references
- **DateTime**: Publication dates, last modified timestamps
- **Range**: Content visibility periods, access restrictions
- **Table**: Dynamic content categorization

### Financial Services
- **RecordID**: Account numbers, transaction IDs
- **Duration**: Transaction timeouts, session durations
- **Range**: Credit limits, date ranges for statements
- **Future**: Async transaction processing

## Troubleshooting Common Issues

### RecordID Issues
```python
# Problem: Invalid string format
try:
    record_id = RecordID.parse("invalid_format")
except ValueError:
    # Solution: Validate format before parsing
    if ":" in user_input:
        record_id = RecordID.parse(user_input)
    else:
        print("RecordID must be in format 'table:id'")
```

### Duration Precision
```python
# Problem: Precision loss in calculations
duration = Duration.parse("1.5s")
# Solution: Use nanosecond precision when needed
precise_duration = Duration(1500000000)  # 1.5 seconds in nanoseconds
```

### Geometry Coordinate Systems
```python
# Problem: Mixing coordinate systems
# Solution: Always use consistent coordinate system (longitude, latitude)
point = GeometryPoint(-122.4194, 37.7749)  # longitude first, then latitude
```

This comprehensive guide provides everything you need to effectively use SurrealDB Python SDK data types in real-world applications. Each example is designed to be practical, runnable, and demonstrate best practices for production use.