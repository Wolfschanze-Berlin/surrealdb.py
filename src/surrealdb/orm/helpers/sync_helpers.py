"""
Sync CRUD helper functions for SurrealDB ORM.
"""

from typing import Union, Dict, Any, List, Optional
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table
from surrealdb.orm.types import SyncConnectionProtocol
from .base_helpers import BaseHelperMixin
from loguru import logger


@logger.catch
class SyncCRUDHelpers(BaseHelperMixin):
    """Sync CRUD helper functions."""
    
    def __init__(self, connection: SyncConnectionProtocol) -> None:
        """
        Initialize sync CRUD helpers.
        
        Args:
            connection: Connection wrapper with execute_with_retry method
        """
        self._connection = connection
    
    def insert_one(
        self,
        table: Union[str, Table],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a single record."""
        table_name = self._normalize_table(table)
        
        def operation(conn):
            return conn.create(table_name, data)
        
        result = self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    def insert_many(
        self,
        table: Union[str, Table],
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Insert multiple records."""
        table_name = self._normalize_table(table)
        
        def operation(conn):
            return conn.insert(table_name, data)
        
        return self._connection.execute_with_retry(operation)
    
    def update_one(
        self,
        record_id: Union[str, RecordID],
        data: Dict[str, Any],
        merge: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Update a single record by ID."""
        record_id_str = self._normalize_record_id(record_id)
        
        def operation(conn):
            if merge:
                return conn.merge(record_id_str, data)
            else:
                return conn.update(record_id_str, data)
        
        result = self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    def update_many(
        self,
        table: Union[str, Table],
        filter_query: str,
        data: Dict[str, Any],
        merge: bool = False
    ) -> List[Dict[str, Any]]:
        """Update multiple records using a filter query."""
        table_name = self._normalize_table(table)
        operation_type = "MERGE" if merge else "SET"
        
        set_clauses = []
        for key, value in data.items():
            set_clauses.append(f"{key} = {repr(value)}")
        set_clause = ", ".join(set_clauses)
        
        query = f"UPDATE {table_name} {operation_type} {{{set_clause}}} WHERE {filter_query}"
        
        def operation(conn):
            result = conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        return self._connection.execute_with_retry(operation)
    
    def upsert_one(
        self,
        record_id: Union[str, RecordID],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upsert a single record by ID."""
        record_id_str = self._normalize_record_id(record_id)
        
        def operation(conn):
            return conn.upsert(record_id_str, data)
        
        result = self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    def delete_one(
        self,
        record_id: Union[str, RecordID]
    ) -> bool:
        """Delete a single record by ID."""
        record_id_str = self._normalize_record_id(record_id)
        
        def operation(conn):
            return conn.delete(record_id_str)
        
        result = self._connection.execute_with_retry(operation)
        return result is not None
    
    def delete_many(
        self,
        table: Union[str, Table],
        filter_query: str
    ) -> int:
        """Delete multiple records using a filter query."""
        table_name = self._normalize_table(table)
        query = f"DELETE FROM {table_name} WHERE {filter_query}"
        
        def operation(conn):
            result = conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        result = self._connection.execute_with_retry(operation)
        return len(result) if isinstance(result, list) else 0
    
    def select_one(
        self,
        record_id: Union[str, RecordID]
    ) -> Optional[Dict[str, Any]]:
        """Select a single record by ID."""
        record_id_str = self._normalize_record_id(record_id)
        
        def operation(conn):
            return conn.select(record_id_str)
        
        result = self._connection.execute_with_retry(operation)
        return result[0] if isinstance(result, list) and result else result
    
    def select_many(
        self,
        table: Union[str, Table],
        filter_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Select multiple records with optional filtering."""
        table_name = self._normalize_table(table)
        
        if filter_query:
            query = f"SELECT * FROM {table_name} WHERE {filter_query}"
        else:
            query = f"SELECT * FROM {table_name}"
        
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" START {offset}"
        
        def operation(conn):
            result = conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        return self._connection.execute_with_retry(operation)
    
    def count(
        self,
        table: Union[str, Table],
        filter_query: Optional[str] = None
    ) -> int:
        """Count records in a table."""
        table_name = self._normalize_table(table)
        
        if filter_query:
            query = f"SELECT count() FROM {table_name} WHERE {filter_query} GROUP ALL"
        else:
            query = f"SELECT count() FROM {table_name} GROUP ALL"
        
        def operation(conn):
            result = conn.query(query)
            return result[0] if result and isinstance(result, list) else []
        
        result = self._connection.execute_with_retry(operation)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('count', 0)
        return 0
    
    def exists(
        self,
        record_id: Union[str, RecordID]
    ) -> bool:
        """Check if a record exists."""
        record_id_str = self._normalize_record_id(record_id)
        query = f"RETURN record::exists({repr(record_id_str)})"
        
        def operation(conn):
            result = conn.query(query)
            return result[0] if result and isinstance(result, list) else False
        
        result = self._connection.execute_with_retry(operation)
        return bool(result)