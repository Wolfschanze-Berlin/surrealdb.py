"""
Type definitions and aliases for SurrealDB ORM.
"""

from typing import TypeVar, Union, Dict, List, Any, Protocol, runtime_checkable
from dataclasses import dataclass
from surrealdb.data.types.record_id import RecordID

# Type variables
T = TypeVar('T', bound='BaseModel')

# Connection types - using forward references to avoid circular imports
ConnectionType = Union[
    'AsyncHttpSurrealConnection',
    'BlockingHttpSurrealConnection', 
    'AsyncWsSurrealConnection',
    'BlockingWsSurrealConnection'
]

PoolType = Union['AsyncConnectionPool', 'SyncConnectionPool']
WrapperType = Union['AsyncSingleConnection', 'SyncSingleConnection']

# Result types
@dataclass
class BulkUpdateItem:
    """Represents a single update operation in a bulk update."""
    record_id: Union[str, RecordID]
    data: Dict[str, Any]
    merge: bool = False

@dataclass 
class BulkResult:
    """Result of a bulk operation with success/error counts and details."""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]]
    results: List[Any]
    
    @property
    def total_count(self) -> int:
        """Total number of operations attempted."""
        return self.success_count + self.error_count
    
    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100.0

# Protocol definitions for connection interfaces
@runtime_checkable
class ConnectionProtocol(Protocol):
    """Protocol for connection wrappers."""
    
    async def execute_with_retry(self, operation) -> Any:
        """Execute operation with retry logic."""
        ...

@runtime_checkable
class SyncConnectionProtocol(Protocol):
    """Protocol for sync connection wrappers."""
    
    def execute_with_retry(self, operation) -> Any:
        """Execute operation with retry logic."""
        ...

# Query builder types
QueryFilter = Dict[str, Any]
QueryOptions = Dict[str, Any]

# Field value types
FieldValue = Union[str, int, float, bool, dict, list, RecordID, None]
ModelData = Dict[str, FieldValue]