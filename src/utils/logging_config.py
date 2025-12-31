"""
Structured Logging Configuration

Provides JSON-formatted logging for production and human-readable logs for development.
Includes correlation IDs, request tracking, and log rotation.
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback


class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON for structured logging.

    Useful for log aggregation systems like ELK, Splunk, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add custom extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "correlation_id", "user_id",
                "request_id", "duration_ms"
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class CorrelationFilter(logging.Filter):
    """
    Add correlation ID to log records for request tracking.
    """

    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize correlation filter.

        Args:
            correlation_id: Correlation ID to add to all logs
        """
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to record.

        Args:
            record: Log record

        Returns:
            Always True (don't filter out)
        """
        if not hasattr(record, "correlation_id") and self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB
    backup_count: int = 10,
    enable_console: bool = True
) -> None:
    """
    Setup application logging with structured format support.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type (text or json)
        log_file: Optional log file path
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(
    name: str,
    correlation_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> logging.LoggerAdapter:
    """
    Get a logger with optional correlation ID and extra context.

    Args:
        name: Logger name
        correlation_id: Optional correlation ID for request tracking
        extra: Optional extra context to include in all logs

    Returns:
        LoggerAdapter with context

    Example:
        >>> logger = get_logger(__name__, correlation_id="abc-123")
        >>> logger.info("Processing request")
    """
    logger = logging.getLogger(name)

    # Add correlation filter if provided
    if correlation_id:
        logger.addFilter(CorrelationFilter(correlation_id))

    # Wrap in LoggerAdapter if extra context provided
    if extra:
        return logging.LoggerAdapter(logger, extra)

    return logging.LoggerAdapter(logger, {})


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with full context.

    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom message
        extra: Optional extra context
    """
    logger.error(
        message,
        exc_info=True,
        extra=extra or {},
        stack_info=True
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        extra: Optional extra context
    """
    log_data = {"operation": operation, "duration_ms": duration_ms}
    if extra:
        log_data.update(extra)

    logger.info(
        f"{operation} completed in {duration_ms:.2f}ms",
        extra=log_data
    )


class LogContext:
    """
    Context manager for adding temporary log context.

    Example:
        >>> with LogContext(logger, correlation_id="abc-123"):
        ...     logger.info("This will include correlation_id")
    """

    def __init__(
        self,
        logger: logging.Logger,
        **context
    ):
        """
        Initialize log context.

        Args:
            logger: Logger instance
            **context: Context key-value pairs
        """
        self.logger = logger
        self.context = context
        self.filters = []

    def __enter__(self):
        """Add context filters."""
        for key, value in self.context.items():
            filter_obj = type(f'{key}Filter', (logging.Filter,), {
                'filter': lambda self, record: setattr(record, key, value) or True
            })()
            self.filters.append(filter_obj)
            self.logger.addFilter(filter_obj)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove context filters."""
        for filter_obj in self.filters:
            self.logger.removeFilter(filter_obj)
