"""
Database manager for SurrealDB ORM.
"""

from typing import Union, Optional, Dict, Any
from .pool import AsyncConnectionPool, SyncConnectionPool
from .single import AsyncSingleConnection, SyncSingleConnection
from surrealdb import AsyncSurreal, Surreal
from loguru import logger


@logger.catch
class DatabaseManager:
    """Main entry point for ORM operations with connection management."""
    
    def __init__(
        self,
        url: str,
        namespace: str,
        database: str,
        auth_params: Optional[Dict[str, Any]] = None,
        pool_size: int = 10,
        use_pool: bool = True,
        max_retries: int = 3
    ) -> None:
        """
        Initialize database manager.
        
        Args:
            url: SurrealDB connection URL
            namespace: Database namespace
            database: Database name
            auth_params: Authentication parameters
            pool_size: Maximum number of connections in pool
            use_pool: Whether to use connection pooling
            max_retries: Maximum retry attempts for operations
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._auth_params = auth_params
        self._pool_size = pool_size
        self._use_pool = use_pool
        self._max_retries = max_retries
        
        # Connection instances
        self._async_pool: Optional[AsyncConnectionPool] = None
        self._sync_pool: Optional[SyncConnectionPool] = None
        self._async_single: Optional[AsyncSingleConnection] = None
        self._sync_single: Optional[SyncSingleConnection] = None
    
    async def get_connection(self) -> Union[AsyncConnectionPool, AsyncSingleConnection]:
        """
        Get async connection (pool or single).
        
        Returns:
            Async connection pool or single connection wrapper
        """
        if self._use_pool:
            if self._async_pool is None:
                self._async_pool = AsyncConnectionPool(
                    url=self._url,
                    namespace=self._namespace,
                    database=self._database,
                    auth_params=self._auth_params,
                    pool_size=self._pool_size,
                    max_retries=self._max_retries
                )
            return self._async_pool
        else:
            if self._async_single is None:
                # Create raw connection
                raw_conn = AsyncSurreal(self._url)
                
                # Authenticate if needed
                if self._auth_params:
                    await raw_conn.signin(self._auth_params)
                
                # Select namespace and database
                await raw_conn.use(self._namespace, self._database)
                
                # Wrap in single connection
                self._async_single = AsyncSingleConnection(
                    connection=raw_conn,
                    max_retries=self._max_retries
                )
            return self._async_single
    
    def get_sync_connection(self) -> Union[SyncConnectionPool, SyncSingleConnection]:
        """
        Get sync connection (pool or single).
        
        Returns:
            Sync connection pool or single connection wrapper
        """
        if self._use_pool:
            if self._sync_pool is None:
                self._sync_pool = SyncConnectionPool(
                    url=self._url,
                    namespace=self._namespace,
                    database=self._database,
                    auth_params=self._auth_params,
                    pool_size=self._pool_size,
                    max_retries=self._max_retries
                )
            return self._sync_pool
        else:
            if self._sync_single is None:
                # Create raw connection
                raw_conn = Surreal(self._url)
                
                # Authenticate if needed
                if self._auth_params:
                    raw_conn.signin(self._auth_params)
                
                # Select namespace and database
                raw_conn.use(self._namespace, self._database)
                
                # Wrap in single connection
                self._sync_single = SyncSingleConnection(
                    connection=raw_conn,
                    max_retries=self._max_retries
                )
            return self._sync_single
    
    async def close(self) -> None:
        """Close async connections."""
        if self._async_pool:
            await self._async_pool.close_all()
            self._async_pool = None
        
        if self._async_single:
            await self._async_single.close()
            self._async_single = None
    
    def close_sync(self) -> None:
        """Close sync connections."""
        if self._sync_pool:
            self._sync_pool.close_all()
            self._sync_pool = None
        
        if self._sync_single:
            self._sync_single.close()
            self._sync_single = None
    
    @property
    def url(self) -> str:
        """Get the connection URL."""
        return self._url
    
    @property
    def namespace(self) -> str:
        """Get the namespace."""
        return self._namespace
    
    @property
    def database(self) -> str:
        """Get the database name."""
        return self._database
    
    @property
    def using_pool(self) -> bool:
        """Check if using connection pooling."""
        return self._use_pool