"""
Base helper functionality for SurrealDB ORM CRUD operations.
"""

from typing import Union, Dict, Any, List
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.table import Table


class BaseHelperMixin:
    """Common functionality for CRUD helpers."""
    
    @staticmethod
    def _normalize_table(table: Union[str, Table]) -> str:
        """
        Convert table input to string.
        
        Args:
            table: Table name as string or Table object
            
        Returns:
            Table name as string
        """
        return str(table) if isinstance(table, Table) else table
    
    @staticmethod
    def _normalize_record_id(record_id: Union[str, RecordID]) -> str:
        """
        Convert record ID input to string.
        
        Args:
            record_id: Record ID as string or RecordID object
            
        Returns:
            Record ID as string
        """
        return str(record_id) if isinstance(record_id, RecordID) else record_id
    
    @staticmethod
    def _build_filter_query(table: str, filter_kwargs: Dict[str, Any]) -> str:
        """
        Build SurrealQL WHERE clause from filter kwargs.
        
        Args:
            table: Table name
            filter_kwargs: Filter conditions
            
        Returns:
            Complete SELECT query with WHERE clause
        """
        if not filter_kwargs:
            return f"SELECT * FROM {table}"
        
        conditions = []
        for key, value in filter_kwargs.items():
            if key.endswith('__gte'):
                field = key[:-5]
                conditions.append(f"{field} >= {repr(value)}")
            elif key.endswith('__lte'):
                field = key[:-5]
                conditions.append(f"{field} <= {repr(value)}")
            elif key.endswith('__gt'):
                field = key[:-4]
                conditions.append(f"{field} > {repr(value)}")
            elif key.endswith('__lt'):
                field = key[:-4]
                conditions.append(f"{field} < {repr(value)}")
            elif key.endswith('__ne'):
                field = key[:-4]
                conditions.append(f"{field} != {repr(value)}")
            elif key.endswith('__in'):
                field = key[:-4]
                if isinstance(value, (list, tuple)):
                    value_list = ', '.join(repr(v) for v in value)
                    conditions.append(f"{field} IN [{value_list}]")
                else:
                    conditions.append(f"{field} = {repr(value)}")
            elif key.endswith('__contains'):
                field = key[:-10]
                conditions.append(f"{field} CONTAINS {repr(value)}")
            else:
                conditions.append(f"{key} = {repr(value)}")
        
        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table} WHERE {where_clause}"
    
    @staticmethod
    def _build_update_query(
        table: str, 
        filter_kwargs: Dict[str, Any], 
        update_data: Dict[str, Any],
        merge: bool = False
    ) -> str:
        """
        Build SurrealQL UPDATE query.
        
        Args:
            table: Table name
            filter_kwargs: Filter conditions
            update_data: Data to update
            merge: Whether to merge or replace
            
        Returns:
            Complete UPDATE query
        """
        operation = "MERGE" if merge else "SET"
        
        # Build SET/MERGE clause
        set_clauses = []
        for key, value in update_data.items():
            set_clauses.append(f"{key} = {repr(value)}")
        set_clause = ", ".join(set_clauses)
        
        # Build WHERE clause
        if filter_kwargs:
            conditions = []
            for key, value in filter_kwargs.items():
                conditions.append(f"{key} = {repr(value)}")
            where_clause = " AND ".join(conditions)
            return f"UPDATE {table} {operation} {{{set_clause}}} WHERE {where_clause}"
        else:
            return f"UPDATE {table} {operation} {{{set_clause}}}"
    
    @staticmethod
    def _build_delete_query(table: str, filter_kwargs: Dict[str, Any]) -> str:
        """
        Build SurrealQL DELETE query.
        
        Args:
            table: Table name
            filter_kwargs: Filter conditions
            
        Returns:
            Complete DELETE query
        """
        if filter_kwargs:
            conditions = []
            for key, value in filter_kwargs.items():
                conditions.append(f"{key} = {repr(value)}")
            where_clause = " AND ".join(conditions)
            return f"DELETE FROM {table} WHERE {where_clause}"
        else:
            return f"DELETE FROM {table}"