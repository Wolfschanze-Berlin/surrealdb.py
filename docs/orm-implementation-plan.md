# SurrealDB Python ORM Helpers - Implementation Plan

## Overview

This document provides a detailed implementation plan for the SurrealDB Python ORM helpers, breaking down the work into manageable phases with specific tasks, dependencies, and deliverables.

## Implementation Strategy

### Development Approach
- **Incremental Development**: Build and test each component independently
- **Test-Driven Development**: Write tests before implementation
- **Backward Compatibility**: Ensure no breaking changes to existing SurrealDB client
- **Performance First**: Optimize for performance from the start
- **Documentation Driven**: Document APIs as they're developed

### Quality Gates
- All code must have 90%+ test coverage
- All public APIs must have comprehensive docstrings
- Performance benchmarks must show no regression
- All code must pass type checking with mypy
- All code must follow existing project style guidelines

## Phase 1: Core Infrastructure (Week 1-2)

### 1.1 Project Structure Setup

**Tasks:**
- [ ] Create ORM package structure under `src/surrealdb/orm/`
- [ ] Set up `__init__.py` files with proper imports
- [ ] Create base test structure under `tests/unit_tests/orm/`
- [ ] Update main `pyproject.toml` with ORM dependencies

**Files to Create:**
```
src/surrealdb/orm/__init__.py
src/surrealdb/orm/types.py
src/surrealdb/orm/exceptions.py
tests/unit_tests/orm/__init__.py
tests/unit_tests/orm/test_types.py
tests/unit_tests/orm/test_exceptions.py
```

**Acceptance Criteria:**
- Package imports correctly
- Basic type definitions are available
- Exception hierarchy is established
- Test infrastructure is functional

### 1.2 Type Definitions and Exceptions

**Implementation Order:**
1. **`src/surrealdb/orm/types.py`**
   ```python
   from typing import TypeVar, Union, Dict, List, Any, Optional, Protocol
   from dataclasses import dataclass
   from surrealdb.data.types.record_id import RecordID
   from surrealdb.data.types.table import Table
   
   # Type variables
   T = TypeVar('T', bound='BaseModel')
   
   # Connection types
   ConnectionType = Union[
       'AsyncHttpSurrealConnection',
       'BlockingHttpSurrealConnection', 
       'AsyncWsSurrealConnection',
       'BlockingWsSurrealConnection'
   ]
   
   # Result types
   @dataclass
   class BulkUpdateItem:
       record_id: Union[str, RecordID]
       data: Dict[str, Any]
       merge: bool = False
   
   @dataclass 
   class BulkResult:
       success_count: int
       error_count: int
       errors: List[Dict[str, Any]]
       results: List[Any]
       
   # Protocol definitions
   class ConnectionProtocol(Protocol):
       async def execute_with_retry(self, operation) -> Any: ...
   ```

2. **`src/surrealdb/orm/exceptions.py`**
   ```python
   from typing import List, Dict, Any
   from surrealdb.errors import SurrealDBMethodError
   
   class SurrealORMError(SurrealDBMethodError):
       """Base exception for ORM operations."""
       pass
   
   class ConnectionError(SurrealORMError):
       """Connection-related errors."""
       pass
   
   class ModelError(SurrealORMError):
       """Model-related errors."""
       pass
   
   class ValidationError(SurrealORMError):
       """Data validation errors."""
       pass
   
   class BulkOperationError(SurrealORMError):
       """Bulk operation errors with detailed error information."""
       
       def __init__(self, message: str, errors: List[Dict[str, Any]]) -> None:
           super().__init__(message)
           self.errors = errors
   ```

**Tests Required:**
- Exception inheritance and behavior
- Type annotation validation
- Dataclass functionality

### 1.3 Connection Management Foundation

**Implementation Order:**
1. **`src/surrealdb/orm/connection/__init__.py`**
2. **`src/surrealdb/orm/connection/single.py`**
3. **`src/surrealdb/orm/connection/pool.py`**
4. **`src/surrealdb/orm/connection/manager.py`**

**Key Implementation Details:**

**SingleConnectionWrapper:**
```python
import asyncio
import logging
from typing import Callable, Any, Union, Optional
from surrealdb.connections.async_http import AsyncHttpSurrealConnection
from surrealdb.connections.blocking_http import BlockingHttpSurrealConnection
from surrealdb.orm.exceptions import ConnectionError

class AsyncSingleConnection:
    def __init__(
        self,
        connection: Union[AsyncHttpSurrealConnection, 'AsyncWsSurrealConnection'],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        self._connection = connection
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._logger = logging.getLogger(__name__)
    
    async def execute_with_retry(self, operation: Callable) -> Any:
        """Execute operation with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return await operation(self._connection)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    self._logger.warning(f"Operation failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    self._logger.error(f"Operation failed after {self._max_retries} retries: {e}")
        
        raise ConnectionError(f"Operation failed after {self._max_retries} retries") from last_exception
```

**Tests Required:**
- Connection wrapper functionality
- Retry logic with various failure scenarios
- Error handling and logging

## Phase 2: Helper Functions (Week 3-4)

### 2.1 Base Helper Infrastructure

**Implementation Order:**
1. **`src/surrealdb/orm/helpers/base_helpers.py`**
2. **`src/surrealdb/orm/helpers/async_helpers.py`**
3. **`src/surrealdb/orm/helpers/sync_helpers.py`**

**Base Helper Implementation:**
```python
from typing import Union, Dict, Any, List, Optional
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table
from surrealdb.orm.exceptions import SurrealORMError

class BaseHelperMixin:
    """Common functionality for CRUD helpers."""
    
    @staticmethod
    def _normalize_table(table: Union[str, Table]) -> str:
        """Convert table input to string."""
        return str(table) if isinstance(table, Table) else table
    
    @staticmethod
    def _normalize_record_id(record_id: Union[str, RecordID]) -> str:
        """Convert record ID input to string."""
        return str(record_id) if isinstance(record_id, RecordID) else record_id
    
    @staticmethod
    def _build_filter_query(table: str, filter_kwargs: Dict[str, Any]) -> str:
        """Build SurrealQL WHERE clause from filter kwargs."""
        if not filter_kwargs:
            return f"SELECT * FROM {table}"
        
        conditions = []
        for key, value in filter_kwargs.items():
            if key.endswith('__gte'):
                field = key[:-5]
                conditions.append(f"{field} >= {value}")
            elif key.endswith('__lte'):
                field = key[:-5]
                conditions.append(f"{field} <= {value}")
            elif key.endswith('__gt'):
                field = key[:-4]
                conditions.append(f"{field} > {value}")
            elif key.endswith('__lt'):
                field = key[:-4]
                conditions.append(f"{field} < {value}")
            else:
                conditions.append(f"{key} = {repr(value)}")
        
        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table} WHERE {where_clause}"
```

### 2.2 Async CRUD Helpers

**Key Methods Implementation:**
```python
class AsyncCRUDHelpers(BaseHelperMixin):
    def __init__(self, connection: 'ConnectionProtocol') -> None:
        self._connection = connection
    
    async def insert_one(
        self,
        table: Union[str, Table],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a single record."""
        table_name = self._normalize_table(table)
        
        async def operation(conn):
            return await conn.create(table_name, data)
        
        result = await self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    async def insert_many(
        self,
        table: Union[str, Table],
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Insert multiple records."""
        table_name = self._normalize_table(table)
        
        async def operation(conn):
            return await conn.insert(table_name, data)
        
        return await self._connection.execute_with_retry(operation)
    
    async def select_many(
        self,
        table: Union[str, Table],
        filter_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Select multiple records with optional filtering."""
        table_name = self._normalize_table(table)
        
        if filter_query:
            query = filter_query
        else:
            query = f"SELECT * FROM {table_name}"
        
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" START {offset}"
        
        async def operation(conn):
            result = await conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        return await self._connection.execute_with_retry(operation)
```

**Tests Required:**
- All CRUD operations with various data types
- Error handling for invalid inputs
- Integration with connection wrappers
- Performance benchmarks

## Phase 3: Model System (Week 5-7)

### 3.1 Field System

**Implementation Order:**
1. **`src/surrealdb/orm/models/fields.py`**

**Field Implementation:**
```python
from typing import Any, Optional, Type, Union
from datetime import datetime
from surrealdb.data.types.record_id import RecordID

class Field:
    """Base field class."""
    
    def __init__(
        self,
        default: Any = None,
        required: bool = False,
        description: Optional[str] = None
    ) -> None:
        self.default = default
        self.required = required
        self.description = description
        self.name: Optional[str] = None  # Set by metaclass
    
    def to_python(self, value: Any) -> Any:
        """Convert database value to Python value."""
        return value
    
    def to_database(self, value: Any) -> Any:
        """Convert Python value to database value."""
        return value
    
    def validate(self, value: Any) -> None:
        """Validate field value."""
        if self.required and value is None:
            raise ValueError(f"Field '{self.name}' is required")

class StringField(Field):
    def __init__(self, max_length: Optional[int] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Field '{self.name}' must be a string")
        if self.max_length and len(str(value)) > self.max_length:
            raise ValueError(f"Field '{self.name}' exceeds max length of {self.max_length}")

class DateTimeField(Field):
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def to_database(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value
```

### 3.2 Model Metaclass

**Implementation:**
```python
class ModelMeta(type):
    """Metaclass for processing model fields and setup."""
    
    def __new__(cls, name, bases, attrs):
        # Skip processing for base classes
        if name in ('BaseModel', 'AsyncModel', 'SyncModel'):
            return super().__new__(cls, name, bases, attrs)
        
        # Extract fields
        fields = {}
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
                attrs.pop(key)  # Remove from class attributes
        
        # Set up table name if not specified
        if 'table_name' not in attrs:
            attrs['table_name'] = name.lower()
        
        attrs['_fields'] = fields
        return super().__new__(cls, name, bases, attrs)
```

### 3.3 Base Model Classes

**Implementation:**
```python
class BaseModel(metaclass=ModelMeta):
    """Base model class."""
    
    table_name: str
    _fields: Dict[str, Field]
    _connection: Optional['ConnectionProtocol'] = None
    
    def __init__(self, **kwargs) -> None:
        self._data = {}
        self._original_data = {}
        
        # Set field values
        for field_name, field in self._fields.items():
            if field_name in kwargs:
                value = kwargs[field_name]
            elif field.default is not None:
                value = field.default() if callable(field.default) else field.default
            else:
                value = None
            
            field.validate(value)
            self._data[field_name] = field.to_python(value)
            self._original_data[field_name] = value
    
    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            return self._data.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_') or name in ('table_name',):
            super().__setattr__(name, value)
        elif name in self._fields:
            field = self._fields[name]
            field.validate(value)
            self._data[name] = field.to_python(value)
        else:
            super().__setattr__(name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for field_name, field in self._fields.items():
            value = self._data.get(field_name)
            if value is not None:
                result[field_name] = field.to_database(value)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary."""
        return cls(**data)
```

**Tests Required:**
- Field validation and conversion
- Metaclass field processing
- Model instantiation and attribute access
- Dictionary conversion methods

## Phase 4: Bulk Operations (Week 8-9)

### 4.1 Bulk Operation Infrastructure

**Implementation:**
```python
from typing import List, Dict, Any, Union
import asyncio
from surrealdb.orm.types import BulkResult, BulkUpdateItem
from surrealdb.orm.exceptions import BulkOperationError

class AsyncBulkOperations:
    def __init__(
        self,
        connection: 'ConnectionProtocol',
        batch_size: int = 1000,
        max_retries: int = 3,
        parallel_batches: int = 5
    ) -> None:
        self._connection = connection
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._parallel_batches = parallel_batches
    
    async def bulk_insert(
        self,
        table: Union[str, Table],
        data: List[Dict[str, Any]],
        ignore_errors: bool = False
    ) -> BulkResult:
        """Bulk insert with batching and error handling."""
        table_name = self._normalize_table(table)
        batches = self._create_batches(data)
        
        results = []
        errors = []
        success_count = 0
        
        # Process batches in parallel
        semaphore = asyncio.Semaphore(self._parallel_batches)
        
        async def process_batch(batch):
            async with semaphore:
                try:
                    async def operation(conn):
                        return await conn.insert(table_name, batch)
                    
                    result = await self._connection.execute_with_retry(operation)
                    return result, None
                except Exception as e:
                    if ignore_errors:
                        return None, str(e)
                    raise
        
        tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result, error in batch_results:
            if error:
                errors.append({"error": error})
            else:
                results.extend(result if isinstance(result, list) else [result])
                success_count += len(result) if isinstance(result, list) else 1
        
        return BulkResult(
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            results=results
        )
    
    def _create_batches(self, data: List[Any]) -> List[List[Any]]:
        """Split data into batches."""
        return [
            data[i:i + self._batch_size]
            for i in range(0, len(data), self._batch_size)
        ]
```

**Tests Required:**
- Batch processing with various sizes
- Error handling and recovery
- Parallel processing performance
- Memory usage optimization

## Phase 5: Integration and Testing (Week 10-11)

### 5.1 Integration Tests

**Test Categories:**
1. **End-to-End Model Operations**
   - Model CRUD with real database
   - Complex queries and relationships
   - Performance under load

2. **Connection Management**
   - Pool behavior under concurrent load
   - Connection failure and recovery
   - Resource cleanup

3. **Bulk Operations**
   - Large dataset processing
   - Memory usage patterns
   - Error recovery scenarios

### 5.2 Performance Benchmarks

**Benchmark Suite:**
```python
import asyncio
import time
from typing import List, Dict, Any

class ORMBenchmarks:
    async def benchmark_insert_performance(self):
        """Compare ORM vs direct client insert performance."""
        # Test with 1K, 10K, 100K records
        
    async def benchmark_query_performance(self):
        """Compare ORM vs direct client query performance."""
        
    async def benchmark_bulk_operations(self):
        """Test bulk operation performance and memory usage."""
        
    async def benchmark_connection_pooling(self):
        """Test connection pool efficiency."""
```

### 5.3 Documentation

**Documentation Tasks:**
- [ ] API reference documentation
- [ ] Getting started guide
- [ ] Migration guide from direct client usage
- [ ] Performance tuning guide
- [ ] Best practices documentation

## Phase 6: Finalization (Week 12)

### 6.1 Package Integration

**Tasks:**
- [ ] Update main `__init__.py` with ORM exports
- [ ] Add ORM examples to existing samples
- [ ] Update README with ORM usage
- [ ] Version compatibility testing

### 6.2 Release Preparation

**Tasks:**
- [ ] Final code review and cleanup
- [ ] Performance regression testing
- [ ] Documentation review
- [ ] Release notes preparation

## Development Guidelines

### Code Style
- Follow existing project conventions
- Use type hints for all public APIs
- Comprehensive docstrings with examples
- Meaningful variable and function names

### Testing Strategy
- Unit tests for all components
- Integration tests with real database
- Performance benchmarks
- Error scenario testing

### Performance Requirements
- ORM overhead should be < 10% vs direct client
- Memory usage should scale linearly with data size
- Connection pooling should improve concurrent performance

### Error Handling
- Graceful degradation on connection failures
- Detailed error messages with context
- Proper exception hierarchy
- Logging for debugging

## Risk Mitigation

### Technical Risks
1. **Performance Impact**: Continuous benchmarking and optimization
2. **Memory Leaks**: Careful resource management and testing
3. **Connection Issues**: Robust retry and recovery mechanisms

### Integration Risks
1. **Breaking Changes**: Comprehensive backward compatibility testing
2. **Version Conflicts**: Careful dependency management
3. **API Consistency**: Regular API review sessions

## Success Metrics

### Functional Metrics
- All planned features implemented and tested
- 90%+ test coverage achieved
- Zero critical bugs in release candidate

### Performance Metrics
- < 10% performance overhead vs direct client
- Successful handling of 100K+ record operations
- Stable memory usage under load

### Quality Metrics
- All code passes type checking
- Documentation completeness score > 95%
- User acceptance testing passed

This implementation plan provides a structured approach to building the SurrealDB ORM helpers while maintaining high quality standards and ensuring successful integration with the existing codebase.