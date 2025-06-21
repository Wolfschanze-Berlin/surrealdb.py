from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table

if TYPE_CHECKING:
    from surrealdb.connections.async_http import AsyncHttpSurrealConnection
    from surrealdb.connections.async_ws import AsyncWsSurrealConnection
    from surrealdb.connections.blocking_http import BlockingHttpSurrealConnection
    from surrealdb.connections.blocking_ws import BlockingWsSurrealConnection

AsyncConnectionType = Union[
    "AsyncHttpSurrealConnection", 
    "AsyncWsSurrealConnection"
]
SyncConnectionType = Union[
    "BlockingHttpSurrealConnection", 
    "BlockingWsSurrealConnection"
]


class AsyncTransaction:
    """
    Async transaction context manager for SurrealDB operations.
    
    Provides a Pythonic way to handle database transactions with automatic
    commit on success and rollback on exceptions.
    
    Example:
        async with db.transaction() as tx:
            await tx.create("user:john", {"name": "John"})
            await tx.create("user:jane", {"name": "Jane"})
            # Auto-commit on success, auto-rollback on exception
    """
    
    def __init__(self, connection: AsyncConnectionType):
        self.connection = connection
        self._in_transaction = False
    
    async def __aenter__(self) -> "AsyncTransaction":
        """Enter the transaction context."""
        await self.connection.begin_transaction()
        self._in_transaction = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the transaction context."""
        if not self._in_transaction:
            return
            
        try:
            if exc_type is None:
                # No exception, commit the transaction
                await self.connection.commit_transaction()
            else:
                # Exception occurred, rollback the transaction
                await self.connection.rollback_transaction()
        finally:
            self._in_transaction = False
    
    # Delegate all CRUD operations to the connection
    async def query(self, query: str, vars: Optional[dict] = None) -> Union[List[dict], dict]:
        """Execute a query within the transaction."""
        return await self.connection.query(query, vars)
    
    async def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[Union[Union[List[dict], dict], dict]] = None,
    ) -> Union[List[dict], dict]:
        """Create a record within the transaction."""
        return await self.connection.create(thing, data)
    
    async def delete(self, thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]:
        """Delete a record within the transaction."""
        return await self.connection.delete(thing)
    
    async def insert(
        self, table: Union[str, Table], data: Union[List[dict], dict]
    ) -> Union[List[dict], dict]:
        """Insert records within the transaction."""
        return await self.connection.insert(table, data)
    
    async def merge(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Merge data into a record within the transaction."""
        return await self.connection.merge(thing, data)
    
    async def patch(
        self, thing: Union[str, RecordID, Table], data: Optional[List[Dict]] = None
    ) -> Union[List[dict], dict]:
        """Patch a record within the transaction."""
        return await self.connection.patch(thing, data)
    
    async def select(self, thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]:
        """Select records within the transaction."""
        return await self.connection.select(thing)
    
    async def update(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Update a record within the transaction."""
        return await self.connection.update(thing, data)
    
    async def upsert(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Upsert a record within the transaction."""
        return await self.connection.upsert(thing, data)


class SyncTransaction:
    """
    Sync transaction context manager for SurrealDB operations.
    
    Provides a Pythonic way to handle database transactions with automatic
    commit on success and rollback on exceptions.
    
    Example:
        with db.transaction() as tx:
            tx.create("user:john", {"name": "John"})
            tx.create("user:jane", {"name": "Jane"})
            # Auto-commit on success, auto-rollback on exception
    """
    
    def __init__(self, connection: SyncConnectionType):
        self.connection = connection
        self._in_transaction = False
    
    def __enter__(self) -> "SyncTransaction":
        """Enter the transaction context."""
        self.connection.begin_transaction()
        self._in_transaction = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the transaction context."""
        if not self._in_transaction:
            return
            
        try:
            if exc_type is None:
                # No exception, commit the transaction
                self.connection.commit_transaction()
            else:
                # Exception occurred, rollback the transaction
                self.connection.rollback_transaction()
        finally:
            self._in_transaction = False
    
    # Delegate all CRUD operations to the connection
    def query(self, query: str, vars: Optional[dict] = None) -> Union[List[dict], dict]:
        """Execute a query within the transaction."""
        return self.connection.query(query, vars)
    
    def create(
        self,
        thing: Union[str, RecordID, Table],
        data: Optional[Union[Union[List[dict], dict], dict]] = None,
    ) -> Union[List[dict], dict]:
        """Create a record within the transaction."""
        return self.connection.create(thing, data)
    
    def delete(self, thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]:
        """Delete a record within the transaction."""
        return self.connection.delete(thing)
    
    def insert(
        self, table: Union[str, Table], data: Union[List[dict], dict]
    ) -> Union[List[dict], dict]:
        """Insert records within the transaction."""
        return self.connection.insert(table, data)
    
    def merge(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Merge data into a record within the transaction."""
        return self.connection.merge(thing, data)
    
    def patch(
        self, thing: Union[str, RecordID, Table], data: Optional[List[Dict]] = None
    ) -> Union[List[dict], dict]:
        """Patch a record within the transaction."""
        return self.connection.patch(thing, data)
    
    def select(self, thing: Union[str, RecordID, Table]) -> Union[List[dict], dict]:
        """Select records within the transaction."""
        return self.connection.select(thing)
    
    def update(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Update a record within the transaction."""
        return self.connection.update(thing, data)
    
    def upsert(
        self, thing: Union[str, RecordID, Table], data: Optional[Dict] = None
    ) -> Union[List[dict], dict]:
        """Upsert a record within the transaction."""
        return self.connection.upsert(thing, data)