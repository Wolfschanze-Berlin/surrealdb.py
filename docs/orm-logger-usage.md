# SurrealDB ORM Centralized Logging

The SurrealDB ORM includes a centralized logging system using loguru for better log management and formatting.

## Basic Usage

```python
from surrealdb.orm import get_logger, configure_logging

# Get a logger instance
logger = get_logger("my_app")

# Log messages
logger.info("Starting application")
logger.warning("This is a warning")
logger.error("An error occurred")
```

## Configuration

### Basic Configuration

```python
from surrealdb.orm import configure_logging

# Configure with custom level and format
configure_logging(
    level="DEBUG",
    format_string="<green>{time}</green> | <level>{level}</level> | {message}"
)
```

### File Logging

```python
from surrealdb.orm import configure_logging, add_file_logging

# Configure with file output
configure_logging(
    level="INFO",
    file_path="logs/surrealdb_orm.log",
    rotation="500 MB",
    retention="10 days",
    compression="zip"
)

# Or add file logging to existing configuration
add_file_logging(
    "logs/debug.log",
    level="DEBUG",
    rotation="1 day"
)
```

## Advanced Configuration

```python
from surrealdb.orm import configure_logging

# Full configuration with all options
configure_logging(
    level="INFO",
    format_string=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "<level>{message}</level>"
    ),
    file_path="logs/app.log",
    rotation="100 MB",
    retention="1 week",
    compression="gz"
)
```

## Usage in ORM Components

The ORM components automatically use the centralized logger:

```python
from surrealdb.orm import DatabaseManager, AsyncCRUDHelpers, configure_logging

# Configure logging first
configure_logging(level="DEBUG", file_path="logs/orm.log")

# Use ORM components - they will automatically log using the configured logger
db_manager = DatabaseManager(
    url="http://localhost:8000",
    namespace="test",
    database="test"
)

helpers = AsyncCRUDHelpers(await db_manager.get_connection())
# All operations will be logged with the configured format
```

## Logger Features

- **Colored console output** for better readability
- **Structured logging** with consistent format
- **File rotation** to manage log file sizes
- **Log retention** to automatically clean old logs
- **Compression** for archived log files
- **Singleton pattern** ensures consistent configuration across the application
- **Module-specific loggers** for better traceability

## Default Format

The default log format includes:
- Timestamp (green)
- Log level (colored by level)
- Module name (cyan)
- Function and line number (cyan)
- Message (colored by level)

Example output:
```
2025-01-22 01:25:30 | INFO     | SurrealORM | surrealdb.orm.connection.pool:acquire:95 | Connection acquired from pool
2025-01-22 01:25:30 | WARNING  | SurrealORM | surrealdb.orm.connection.single:execute_with_retry:58 | Operation failed, retrying in 1.0s: Connection timeout