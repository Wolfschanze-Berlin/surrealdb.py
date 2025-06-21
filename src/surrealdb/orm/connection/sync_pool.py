"""
Sync connection pool for SurrealDB ORM.
"""

import time
import threading
from typing import Callable, Any, Optional, Dict, List
from contextlib import contextmanager
from queue import Queue, Empty
from surrealdb.connections.blocking_http import BlockingHttpSurrealConnection
from surrealdb.connections.blocking_ws import BlockingWsSurrealConnection
from surrealdb.connections.url import Url, UrlScheme
from surrealdb.orm.exceptions import ConnectionError
from surrealdb.orm.logger import get_logger
from loguru import logger


@logger.catch
class SyncConnectionPool:
    """Sync connection pool for SurrealDB connections."""
    
    def __init__(
        self,
        url: str,
        namespace: str,
        database: str,
        auth_params: Optional[Dict[str, Any]] = None,
        pool_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Initialize sync connection pool.
        
        Args:
            url: SurrealDB connection URL
            namespace: Database namespace
            database: Database name
            auth_params: Authentication parameters
            pool_size: Maximum number of connections in pool
            max_retries: Maximum retry attempts for operations
            retry_delay: Base delay between retries
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._auth_params = auth_params or {}
        self._pool_size = pool_size
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._logger = get_logger("surrealdb.orm.connection.sync_pool")
        
        # Pool management
        self._pool: List[Any] = []
        self._available: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._closed = False
        
        # Determine connection type
        parsed_url = Url(url)
        if parsed_url.scheme in (UrlScheme.HTTP, UrlScheme.HTTPS):
            self._connection_class = BlockingHttpSurrealConnection
        elif parsed_url.scheme in (UrlScheme.WS, UrlScheme.WSS):
            self._connection_class = BlockingWsSurrealConnection
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
    
    def _create_connection(self) -> Any:
        """Create and configure a new connection."""
        try:
            connection = self._connection_class(self._url)
            
            # Authenticate if parameters provided
            if self._auth_params:
                connection.signin(self._auth_params)
            
            # Select namespace and database
            connection.use(self._namespace, self._database)
            
            return connection
        except Exception as e:
            self._logger.error(f"Failed to create connection: {e}")
            raise ConnectionError(f"Failed to create connection: {e}") from e
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool."""
        with self._lock:
            if self._pool:
                return  # Already initialized
            
            self._logger.info(f"Initializing connection pool with {self._pool_size} connections")
            
            for _ in range(self._pool_size):
                try:
                    connection = self._create_connection()
                    self._pool.append(connection)
                    self._available.put(connection)
                except Exception as e:
                    self._logger.error(f"Failed to initialize connection: {e}")
                    # Continue with fewer connections rather than failing completely
    
    def acquire(self) -> Any:
        """
        Acquire a connection from the pool.
        
        Returns:
            A SurrealDB connection
            
        Raises:
            ConnectionError: If unable to acquire connection
        """
        if self._closed:
            raise ConnectionError("Connection pool is closed")
        
        # Initialize pool if needed
        if not self._pool:
            self._initialize_pool()
        
        try:
            # Wait for available connection with timeout
            connection = self._available.get(timeout=30.0)
            
            # Verify connection is still valid
            try:
                connection.version()
                return connection
            except Exception as e:
                self._logger.warning(f"Connection validation failed, creating new one: {e}")
                # Create replacement connection
                new_connection = self._create_connection()
                return new_connection
                
        except Empty:
            raise ConnectionError("Timeout waiting for available connection")
        except Exception as e:
            raise ConnectionError(f"Failed to acquire connection: {e}") from e
    
    def release(self, connection: Any) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        if self._closed:
            try:
                connection.close()
            except Exception:
                pass
            return
        
        try:
            # Verify connection is still valid before returning to pool
            connection.version()
            self._available.put(connection)
        except Exception as e:
            self._logger.warning(f"Released connection is invalid, discarding: {e}")
            try:
                connection.close()
            except Exception:
                pass
            
            # Create replacement connection if pool is not full
            try:
                if self._available.qsize() < self._pool_size:
                    new_connection = self._create_connection()
                    self._available.put(new_connection)
            except Exception as e:
                self._logger.error(f"Failed to create replacement connection: {e}")
    
    @contextmanager
    def connection(self):
        """Context manager for acquiring and releasing connections."""
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)
    
    def execute_with_connection(self, operation: Callable) -> Any:
        """
        Execute operation with a pooled connection.
        
        Args:
            operation: Callable that takes connection as argument
            
        Returns:
            Result of the operation
        """
        with self.connection() as conn:
            return self._execute_with_retry(operation, conn)
    
    def _execute_with_retry(self, operation: Callable, connection: Any) -> Any:
        """Execute operation with retry logic."""
        last_exception = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return operation(connection)
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
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            self._closed = True
            
            # Close all connections
            while not self._available.empty():
                try:
                    connection = self._available.get_nowait()
                    connection.close()
                except Empty:
                    break
                except Exception as e:
                    self._logger.warning(f"Error closing connection: {e}")
            
            self._pool.clear()
            self._logger.info("Connection pool closed")
    
    @property
    def pool_size(self) -> int:
        """Get the configured pool size."""
        return self._pool_size
    
    @property
    def available_connections(self) -> int:
        """Get the number of available connections."""
        return self._available.qsize()
    
    @property
    def is_closed(self) -> bool:
        """Check if the pool is closed."""
        return self._closed