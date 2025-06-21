import sys
import os
from pathlib import Path
from loguru import logger
from config import settings

class LoggerService:
    """Centralized logging service using loguru."""
    
    def __init__(self):
        self._configured = False
        self.setup_logger()
    
    def setup_logger(self):
        """Configure loguru logger with custom settings."""
        if self._configured:
            return
        
        # Remove default handler
        logger.remove()
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Console handler with colored output
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG" if settings.DEBUG else "INFO",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler for all logs
        logger.add(
            log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # File handler for errors only
        logger.add(
            log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="10 MB",
            retention="90 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # File handler for access logs
        logger.add(
            log_dir / "access.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            filter=lambda record: record["extra"].get("access_log", False)
        )
        
        self._configured = True
        logger.info("Logger service initialized successfully")
    
    def get_logger(self, name: str | None = None):
        """Get a logger instance with optional name binding."""
        if name:
            return logger.bind(name=name)
        return logger
    
    def log_access(self, message: str, **kwargs):
        """Log access information."""
        logger.bind(access_log=True).info(message, **kwargs)
    
    def log_auth(self, message: str, user_id: str = None, **kwargs):
        """Log authentication events."""
        extra_data = {"auth_log": True}
        if user_id:
            extra_data["user_id"] = user_id
        logger.bind(**extra_data).info(message, **kwargs)
    
    def log_database(self, message: str, operation: str = None, **kwargs):
        """Log database operations."""
        extra_data = {"db_log": True}
        if operation:
            extra_data["operation"] = operation
        logger.bind(**extra_data).info(message, **kwargs)
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       response_time: float, user_id: str = None):
        """Log API request details."""
        extra_data = {
            "access_log": True,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time
        }
        if user_id:
            extra_data["user_id"] = user_id
        
        message = f"{method} {path} - {status_code} - {response_time:.3f}s"
        logger.bind(**extra_data).info(message)

# Global logger service instance
logger_service = LoggerService()

# Convenience functions for easy access
def get_logger(name: str = None):
    """Get a logger instance."""
    return logger_service.get_logger(name)

def log_access(message: str, **kwargs):
    """Log access information."""
    logger_service.log_access(message, **kwargs)

def log_auth(message: str, user_id: str = None, **kwargs):
    """Log authentication events."""
    logger_service.log_auth(message, user_id, **kwargs)

def log_database(message: str, operation: str = None, **kwargs):
    """Log database operations."""
    logger_service.log_database(message, operation, **kwargs)

def log_api_request(method: str, path: str, status_code: int, 
                   response_time: float, user_id: str = None):
    """Log API request details."""
    logger_service.log_api_request(method, path, status_code, response_time, user_id)