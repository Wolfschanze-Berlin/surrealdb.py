"""
Single connection wrapper with retry logic for SurrealDB ORM.
"""

import asyncio
from typing import Callable, Any, Union, Optional
from surrealdb.connections.async_http import AsyncHttpSurrealConnection
from surrealdb.connections.blocking_http import BlockingHttpSurrealConnection
from surrealdb.connections.async_ws import AsyncWsSurrealConnection
from surrealdb.connections.blocking_ws import BlockingWsSurrealConnection
from surrealdb.orm.exceptions import ConnectionError
from surrealdb.orm.logger import get_logger
from loguru import logger


@logger.catch
class AsyncSingleConnection:
    """Async single connection wrapper with retry logic."""
    
    def __init__(
        self,
        connection: Union[AsyncHttpSurrealConnection, AsyncWsSurrealConnection],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Initialize async single connection wrapper.
        
        Args:
            connection: The SurrealDB connection to wrap
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self._connection = connection
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._logger = get_logger("surrealdb.orm.connection.single")
    
    async def execute_with_retry(self, operation: Callable) -> Any:
        """
        Execute operation with exponential backoff retry.
        
        Args:
            operation: Callable that takes connection as argument
            
        Returns:
            Result of the operation
            
        Raises:
            ConnectionError: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return await operation(self._connection)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    self._logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self._max_retries + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self._logger.error(
                        f"Operation failed after {self._max_retries + 1} attempts: {e}"
                    )
        
        raise ConnectionError(
            f"Operation failed after {self._max_retries + 1} attempts"
        ) from last_exception
    
    async def ensure_connected(self) -> None:
        """Ensure the connection is active."""
        try:
            # Try a simple operation to check connection
            async def check_operation(conn):
                return await conn.version()
            
            await self.execute_with_retry(check_operation)
        except Exception as e:
            raise ConnectionError(f"Connection check failed: {e}") from e
    
    async def close(self) -> None:
        """Close the underlying connection."""
        try:
            await self._connection.close()
        except Exception as e:
            self._logger.warning(f"Error closing connection: {e}")
    
    @property
    def connection(self) -> Union[AsyncHttpSurrealConnection, AsyncWsSurrealConnection]:
        """Get the underlying connection."""
        return self._connection


@logger.catch
class SyncSingleConnection:
    """Sync single connection wrapper with retry logic."""
    
    def __init__(
        self,
        connection: Union[BlockingHttpSurrealConnection, BlockingWsSurrealConnection],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Initialize sync single connection wrapper.
        
        Args:
            connection: The SurrealDB connection to wrap
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self._connection = connection
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._logger = get_logger("surrealdb.orm.connection.single")
    
    def execute_with_retry(self, operation: Callable) -> Any:
        """
        Execute operation with exponential backoff retry.
        
        Args:
            operation: Callable that takes connection as argument
            
        Returns:
            Result of the operation
            
        Raises:
            ConnectionError: If operation fails after all retries
        """
        import time
        last_exception = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return operation(self._connection)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    self._logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self._max_retries + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self._logger.error(
                        f"Operation failed after {self._max_retries + 1} attempts: {e}"
                    )
        
        raise ConnectionError(
            f"Operation failed after {self._max_retries + 1} attempts"
        ) from last_exception
    
    def ensure_connected(self) -> None:
        """Ensure the connection is active."""
        try:
            # Try a simple operation to check connection
            def check_operation(conn):
                return conn.version()
            
            self.execute_with_retry(check_operation)
        except Exception as e:
            raise ConnectionError(f"Connection check failed: {e}") from e
    
    def close(self) -> None:
        """Close the underlying connection."""
        try:
            self._connection.close()
        except Exception as e:
            self._logger.warning(f"Error closing connection: {e}")
    
    @property
    def connection(self) -> Union[BlockingHttpSurrealConnection, BlockingWsSurrealConnection]:
        """Get the underlying connection."""
        return self._connection