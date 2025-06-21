"""
Exception classes for SurrealDB ORM operations.
"""

from typing import List, Dict, Any
from surrealdb.errors import SurrealDBMethodError


class SurrealORMError(SurrealDBMethodError):
    """Base exception for all ORM operations."""
    pass


class ConnectionError(SurrealORMError):
    """Raised when connection-related errors occur."""
    pass


class ModelError(SurrealORMError):
    """Raised when model-related errors occur."""
    pass


class ValidationError(SurrealORMError):
    """Raised when data validation fails."""
    pass


class BulkOperationError(SurrealORMError):
    """Raised when bulk operations encounter errors."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]]) -> None:
        super().__init__(message)
        self.errors = errors
        self.error_count = len(errors)
    
    def __str__(self) -> str:
        return f"{self.message} ({self.error_count} errors)"