"""
SurrealDB ORM Helpers

This package provides ORM-like functionality for the SurrealDB Python client,
including model-based interfaces, helper functions, and bulk operations.
"""

from .connection.manager import DatabaseManager
from .connection.pool import AsyncConnectionPool, SyncConnectionPool
from .connection.single import AsyncSingleConnection, SyncSingleConnection
from .helpers.async_helpers import AsyncCRUDHelpers
from .helpers.sync_helpers import SyncCRUDHelpers
from .bulk.async_bulk import AsyncBulkOperations
from .bulk.sync_bulk import SyncBulkOperations
from .models.base import BaseModel, AsyncModel, SyncModel
from .models.fields import (
    Field,
    StringField,
    IntField,
    FloatField,
    BoolField,
    DateTimeField,
    RecordIDField,
    ListField,
    DictField,
)
from .exceptions import (
    SurrealORMError,
    ConnectionError,
    ModelError,
    ValidationError,
    BulkOperationError,
)
from .types import BulkResult, BulkUpdateItem
from .logger import get_logger, get_logger_with_catch, configure_logging, add_file_logging

__all__ = [
    # Connection Management
    "DatabaseManager",
    "AsyncConnectionPool",
    "SyncConnectionPool", 
    "AsyncSingleConnection",
    "SyncSingleConnection",
    
    # Helper Functions
    "AsyncCRUDHelpers",
    "SyncCRUDHelpers",
    
    # Bulk Operations
    "AsyncBulkOperations",
    "SyncBulkOperations",
    
    # Models
    "BaseModel",
    "AsyncModel", 
    "SyncModel",
    
    # Fields
    "Field",
    "StringField",
    "IntField",
    "FloatField",
    "BoolField",
    "DateTimeField",
    "RecordIDField",
    "ListField",
    "DictField",
    
    # Exceptions
    "SurrealORMError",
    "ConnectionError",
    "ModelError",
    "ValidationError",
    "BulkOperationError",
    
    # Types
    "BulkResult",
    "BulkUpdateItem",
    
    # Logging
    "get_logger",
    "get_logger_with_catch",
    "configure_logging",
    "add_file_logging",
]