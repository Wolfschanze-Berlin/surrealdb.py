"""
Async CRUD helper functions for SurrealDB ORM.
"""

from typing import Union, Dict, Any, List, Optional
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table
from surrealdb.orm.types import ConnectionProtocol
from .base_helpers import BaseHelperMixin
from loguru import logger


@logger.catch
class AsyncCRUDHelpers(BaseHelperMixin):
    """Async CRUD helper functions."""
    
    def __init__(self, connection: ConnectionProtocol) -> None:
        """
        Initialize async CRUD helpers.
        
        Args:
            connection: Connection wrapper with execute_with_retry method
        """
        self._connection = connection
    
    async def insert_one(
        self,
        table: Union[str, Table],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Insert a single record.
        
        Args:
            table: Table name or Table object
            data: Record data to insert
            
        Returns:
            Inserted record data
        """
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
        """
        Insert multiple records.
        
        Args:
            table: Table name or Table object
            data: List of record data to insert
            
        Returns:
            List of inserted record data
        """
        table_name = self._normalize_table(table)
        
        async def operation(conn):
            return await conn.insert(table_name, data)
        
        return await self._connection.execute_with_retry(operation)
    
    async def update_one(
        self,
        record_id: Union[str, RecordID],
        data: Dict[str, Any],
        merge: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Update a single record by ID.
        
        Args:
            record_id: Record ID to update
            data: Data to update
            merge: Whether to merge or replace data
            
        Returns:
            Updated record data or None if not found
        """
        record_id_str = self._normalize_record_id(record_id)
        
        async def operation(conn):
            if merge:
                return await conn.merge(record_id_str, data)
            else:
                return await conn.update(record_id_str, data)
        
        result = await self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    async def update_many(
        self,
        table: Union[str, Table],
        filter_query: str,
        data: Dict[str, Any],
        merge: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Update multiple records using a filter query.
        
        Args:
            table: Table name or Table object
            filter_query: SurrealQL WHERE clause
            data: Data to update
            merge: Whether to merge or replace data
            
        Returns:
            List of updated records
        """
        table_name = self._normalize_table(table)
        operation_type = "MERGE" if merge else "SET"
        
        # Build SET/MERGE clause
        set_clauses = []
        for key, value in data.items():
            set_clauses.append(f"{key} = {repr(value)}")
        set_clause = ", ".join(set_clauses)
        
        query = f"UPDATE {table_name} {operation_type} {{{set_clause}}} WHERE {filter_query}"
        
        async def operation(conn):
            result = await conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        return await self._connection.execute_with_retry(operation)
    
    async def upsert_one(
        self,
        record_id: Union[str, RecordID],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upsert a single record by ID.
        
        Args:
            record_id: Record ID to upsert
            data: Data to upsert
            
        Returns:
            Upserted record data
        """
        record_id_str = self._normalize_record_id(record_id)
        
        async def operation(conn):
            return await conn.upsert(record_id_str, data)
        
        result = await self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    async def upsert_many(
        self,
        table: Union[str, Table],
        data: List[Dict[str, Any]],
        key_field: str = "id"
    ) -> List[Dict[str, Any]]:
        """
        Upsert multiple records.
        
        Args:
            table: Table name or Table object
            data: List of record data to upsert
            key_field: Field to use as unique key
            
        Returns:
            List of upserted records
        """
        table_name = self._normalize_table(table)
        results = []
        
        for record in data:
            if key_field in record:
                record_id = f"{table_name}:{record[key_field]}"
                result = await self.upsert_one(record_id, record)
                results.append(result)
            else:
                # Insert if no key field
                result = await self.insert_one(table_name, record)
                results.append(result)
        
        return results
    
    async def delete_one(
        self,
        record_id: Union[str, RecordID]
    ) -> bool:
        """
        Delete a single record by ID.
        
        Args:
            record_id: Record ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        record_id_str = self._normalize_record_id(record_id)
        
        async def operation(conn):
            return await conn.delete(record_id_str)
        
        result = await self._connection.execute_with_retry(operation)
        return result is not None
    
    async def delete_many(
        self,
        table: Union[str, Table],
        filter_query: str
    ) -> int:
        """
        Delete multiple records using a filter query.
        
        Args:
            table: Table name or Table object
            filter_query: SurrealQL WHERE clause
            
        Returns:
            Number of deleted records
        """
        table_name = self._normalize_table(table)
        query = f"DELETE FROM {table_name} WHERE {filter_query}"
        
        async def operation(conn):
            result = await conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        result = await self._connection.execute_with_retry(operation)
        return len(result) if isinstance(result, list) else 0
    
    async def select_one(
        self,
        record_id: Union[str, RecordID]
    ) -> Optional[Dict[str, Any]]:
        """
        Select a single record by ID.
        
        Args:
            record_id: Record ID to select
            
        Returns:
            Record data or None if not found
        """
        record_id_str = self._normalize_record_id(record_id)
        
        async def operation(conn):
            return await conn.select(record_id_str)
        
        result = await self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    async def select_many(
        self,
        table: Union[str, Table],
        filter_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Select multiple records with optional filtering.
        
        Args:
            table: Table name or Table object
            filter_query: Optional SurrealQL WHERE clause
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of record data
        """
        table_name = self._normalize_table(table)
        
        if filter_query:
            query = f"SELECT * FROM {table_name} WHERE {filter_query}"
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
    
    async def count(
        self,
        table: Union[str, Table],
        filter_query: Optional[str] = None
    ) -> int:
        """
        Count records in a table.
        
        Args:
            table: Table name or Table object
            filter_query: Optional SurrealQL WHERE clause
            
        Returns:
            Number of records
        """
        table_name = self._normalize_table(table)
        
        if filter_query:
            query = f"SELECT count() FROM {table_name} WHERE {filter_query} GROUP ALL"
        else:
            query = f"SELECT count() FROM {table_name} GROUP ALL"
        
        async def operation(conn):
            result = await conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        result = await self._connection.execute_with_retry(operation)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('count', 0)
        return 0
    
    async def exists(
        self,
        record_id: Union[str, RecordID]
    ) -> bool:
        """
        Check if a record exists.
        
        Args:
            record_id: Record ID to check
            
        Returns:
            True if record exists, False otherwise
        """
        record_id_str = self._normalize_record_id(record_id)
        query = f"RETURN record::exists({repr(record_id_str)})"
        
        async def operation(conn):
            result = await conn.query(query)
            return result[0] if result and isinstance(result, list) else False
        
        result = await self._connection.execute_with_retry(operation)
        return bool(result)