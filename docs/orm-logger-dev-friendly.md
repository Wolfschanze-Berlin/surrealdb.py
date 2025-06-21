# SurrealDB ORM Dev-Friendly Logging

The SurrealDB ORM includes a centralized logging system using loguru with dev-friendly formatting and automatic exception handling.

## Key Features

### 🎨 **Dev-Friendly Format**
- **Short timestamps** (HH:mm:ss) for quick scanning
- **Fixed-width columns** for perfect alignment
- **Compact log levels** (5 chars max)
- **Colorized output** for better visual distinction
- **DEBUG level by default** for development

### 🛡️ **Automatic Exception Handling**
- **@logger.catch decorators** on all important classes
- **Full stack traces** automatically logged
- **No manual exception handling** needed

## Quick Start

```python
from surrealdb.orm import get_logger, configure_logging

# Basic usage - dev-friendly by default
logger = get_logger("my_app")
logger.info("Application started")
logger.debug("Debug information")
logger.error("Something went wrong")
```

## Dev-Friendly Output Format

```
14:25:30 | INFO  | surrealdb.orm.connection | acquire         | Connection acquired from pool
14:25:31 | WARN  | surrealdb.orm.single     | execute_retry   | Operation failed, retrying in 1.0s
14:25:32 | ERROR | surrealdb.orm.helpers    | insert_one      | Failed to insert record: timeout
14:25:33 | DEBUG | my_app                   | process_data    | Processing 150 records
```

**Format breakdown:**
- `14:25:30` - Short timestamp for quick scanning
- `INFO` - Compact log level (5 chars, color-coded)
- `surrealdb.orm.connection` - Module name (25 chars, aligned)
- `acquire` - Function name (15 chars, aligned)
- `Connection acquired...` - Log message

## Configuration

### Development Configuration (Default)
```python
from surrealdb.orm import configure_logging

# Already optimized for development - no config needed!
# But you can customize:
configure_logging(
    level="DEBUG",  # See everything during development
    format_string=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <5}</level> | "
        "<blue>{name: <25}</blue> | "
        "<cyan>{function: <15}</cyan> | "
        "<level>{message}</level>"
    )
)
```

### Production Configuration
```python
# For production, use longer timestamps and file output
configure_logging(
    level="INFO",
    file_path="logs/app.log",
    rotation="100 MB",
    retention="7 days",
    format_string=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "<level>{message}</level>"
    )
)
```

## Automatic Exception Handling

### Classes with @logger.catch

All important ORM classes are decorated with `@logger.catch` for automatic exception logging:

- ✅ `AsyncSingleConnection` / `SyncSingleConnection`
- ✅ `AsyncConnectionPool` / `SyncConnectionPool` 
- ✅ `DatabaseManager`
- ✅ `AsyncCRUDHelpers` / `SyncCRUDHelpers`

### What this means:

```python
from surrealdb.orm import DatabaseManager

# Any exception in DatabaseManager methods will be automatically logged
# with full stack trace - no try/catch needed!
db_manager = DatabaseManager("http://localhost:8000", "test", "test")

# If this fails, you'll see a detailed error log automatically
connection = await db_manager.get_connection()
```

### Manual Exception Catching

```python
from surrealdb.orm import get_logger_with_catch

# Get logger with catch decorator for your own functions
logger = get_logger_with_catch("my_module")

@logger.catch
def my_function():
    # Any exception here will be automatically logged
    raise ValueError("Something went wrong")
```

## Advanced Usage

### Multiple Log Levels
```python
from surrealdb.orm import get_logger

logger = get_logger("my_app")

logger.debug("Detailed debug info")      # Gray
logger.info("General information")       # Blue  
logger.warning("Warning message")        # Yellow
logger.error("Error occurred")           # Red
logger.critical("Critical failure")      # Bright Red
```

### Structured Logging
```python
logger.info("User action", extra={
    "user_id": 123,
    "action": "login",
    "ip": "192.168.1.1"
})
```

### File + Console Logging
```python
from surrealdb.orm import configure_logging, add_file_logging

# Console logging (dev-friendly format)
configure_logging(level="DEBUG")

# Add file logging (production format)
add_file_logging(
    "logs/debug.log",
    level="DEBUG",
    rotation="50 MB",
    format_string="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
)
```

## Benefits for Development

1. **🔍 Easy Scanning**: Fixed-width columns make logs easy to read
2. **⚡ Quick Timestamps**: Short format for rapid development cycles  
3. **🎯 Automatic Errors**: No need to wrap everything in try/catch
4. **🌈 Color Coding**: Instant visual feedback on log levels
5. **📊 Structured**: Consistent format across all ORM components
6. **🔧 Configurable**: Easy to switch between dev and production modes

## Tips

- **Keep default settings** for development - they're optimized for you!
- **Use file logging** in production with longer timestamps
- **Let @logger.catch handle exceptions** - don't wrap everything manually
- **Use structured logging** for complex data
- **Configure once** at app startup - all ORM components will use it