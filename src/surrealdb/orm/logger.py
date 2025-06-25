"""
Centralized logging configuration for SurrealDB ORM using loguru.
"""

import sys
from typing import Optional, Any
from loguru import logger


class ORMLogger:
    """Centralized logger for SurrealDB ORM operations."""
    
    _instance: Optional['ORMLogger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'ORMLogger':
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the logger if not already configured."""
        if not self._configured:
            self._setup_default_config()
            self._configured = True
    
    def _setup_default_config(self) -> None:
        """Setup default logging configuration with dev-friendly format."""
        # Remove default handler
        logger.remove()
        
        # Add console handler with dev-friendly format
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | "
                   "<level>{level: <5}</level> | "
                   "<blue>{name: <25}</blue> | "
                   "<cyan>{function: <15}</cyan> | "
                   "<level>{message}</level>",
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
    
    def configure(
        self,
        level: str = "INFO",
        format_string: Optional[str] = None,
        file_path: Optional[str] = None,
        rotation: Optional[str] = None,
        retention: Optional[str] = None,
        compression: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Configure the logger with custom settings.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_string: Custom format string for log messages
            file_path: Optional file path for file logging
            rotation: Log rotation setting (e.g., "500 MB", "1 day")
            retention: Log retention setting (e.g., "10 days", "1 week")
            compression: Compression format for rotated logs (e.g., "zip", "gz")
            **kwargs: Additional loguru configuration options
        """
        # Remove existing handlers
        logger.remove()
        
        # Default format if not provided
        if format_string is None:
            format_string = (
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <5}</level> | "
                "<blue>{name: <25}</blue> | "
                "<cyan>{function: <15}</cyan> | "
                "<level>{message}</level>"
            )
        
        # Console handler
        logger.add(
            sys.stderr,
            format=format_string,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            **kwargs
        )
        
        # File handler if specified
        if file_path:
            file_config = {
                "format": format_string,
                "level": level,
                "backtrace": True,
                "diagnose": True,
                **kwargs
            }
            
            if rotation:
                file_config["rotation"] = rotation
            if retention:
                file_config["retention"] = retention
            if compression:
                file_config["compression"] = compression
            
            logger.add(file_path, **file_config)
    
    def get_logger(self, name: str = "surrealdb.orm") -> 'logger':
        """
        Get a logger instance with the specified name.
        
        Args:
            name: Logger name (usually module name)
            
        Returns:
            Configured logger instance
        """
        return logger.bind(name=name)
    
    def get_logger_with_catch(self, name: str = "surrealdb.orm") -> 'logger':
        """
        Get a logger instance with automatic exception catching.
        
        Args:
            name: Logger name (usually module name)
            
        Returns:
            Configured logger instance with catch decorator
        """
        return logger.bind(name=name).catch()
    
    def set_level(self, level: str) -> None:
        """
        Set the logging level for all handlers.
        
        Args:
            level: New logging level
        """
        # Note: loguru doesn't support changing level of existing handlers
        # This would require reconfiguration
        logger.warning(f"To change level to {level}, please reconfigure the logger")
    
    def add_file_handler(
        self,
        file_path: str,
        level: str = "INFO",
        rotation: Optional[str] = None,
        retention: Optional[str] = None,
        compression: Optional[str] = None,
        format_string: Optional[str] = None
    ) -> None:
        """
        Add a file handler to the existing configuration.
        
        Args:
            file_path: Path to log file
            level: Logging level for this handler
            rotation: Log rotation setting
            retention: Log retention setting
            compression: Compression format
            format_string: Custom format string
        """
        if format_string is None:
            format_string = (
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "SurrealORM | "
                "{name}:{function}:{line} | "
                "{message}"
            )
        
        config = {
            "format": format_string,
            "level": level,
            "backtrace": True,
            "diagnose": True
        }
        
        if rotation:
            config["rotation"] = rotation
        if retention:
            config["retention"] = retention
        if compression:
            config["compression"] = compression
        
        logger.add(file_path, **config)
    
    def disable(self) -> None:
        """Disable all logging."""
        logger.disable("surrealdb.orm")
    
    def enable(self) -> None:
        """Enable logging."""
        logger.enable("surrealdb.orm")


# Global logger instance
_orm_logger = ORMLogger()

def get_logger(name: str = "surrealdb.orm") -> 'logger':
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Configured logger instance
    """
    return _orm_logger.get_logger(name)

def get_logger_with_catch(name: str = "surrealdb.orm") -> 'logger':
    """
    Get a configured logger instance with automatic exception catching.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Configured logger instance with catch decorator
    """
    return _orm_logger.get_logger_with_catch(name)

def configure_logging(**kwargs: Any) -> None:
    """
    Configure the global ORM logger.
    
    Args:
        **kwargs: Configuration options passed to ORMLogger.configure()
    """
    _orm_logger.configure(**kwargs)

def add_file_logging(file_path: str, **kwargs: Any) -> None:
    """
    Add file logging to the global ORM logger.
    
    Args:
        file_path: Path to log file
        **kwargs: Additional configuration options
    """
    _orm_logger.add_file_handler(file_path, **kwargs)