"""
Error Tracking and Monitoring Utilities

Provides error tracking, reporting, and optional integration with external
monitoring services like Sentry. Includes error categorization, metrics,
and alerting capabilities.
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from collections import defaultdict
from threading import Lock
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for categorization."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    FILE_IO = "file_io"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


class ErrorMetrics:
    """Thread-safe error metrics collection."""

    def __init__(self):
        self._lock = Lock()
        self._error_counts = defaultdict(int)
        self._error_by_category = defaultdict(int)
        self._error_by_severity = defaultdict(int)
        self._first_seen = {}
        self._last_seen = {}

    def record_error(
        self,
        error_type: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type/class of the error
            category: Error category
            severity: Error severity level
        """
        with self._lock:
            now = datetime.utcnow().isoformat()

            self._error_counts[error_type] += 1
            self._error_by_category[category.value] += 1
            self._error_by_severity[severity.value] += 1

            if error_type not in self._first_seen:
                self._first_seen[error_type] = now
            self._last_seen[error_type] = now

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current error metrics.

        Returns:
            Dictionary containing error metrics
        """
        with self._lock:
            return {
                "total_errors": sum(self._error_counts.values()),
                "by_type": dict(self._error_counts),
                "by_category": dict(self._error_by_category),
                "by_severity": dict(self._error_by_severity),
                "unique_error_types": len(self._error_counts),
                "first_seen": dict(self._first_seen),
                "last_seen": dict(self._last_seen),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._error_counts.clear()
            self._error_by_category.clear()
            self._error_by_severity.clear()
            self._first_seen.clear()
            self._last_seen.clear()


class ErrorTracker:
    """
    Central error tracking and reporting system.

    Supports:
    - Error categorization and severity assignment
    - Metrics collection
    - Optional Sentry integration
    - Custom error handlers
    - Error rate limiting for repeated errors
    """

    def __init__(
        self,
        enable_sentry: bool = False,
        sentry_dsn: Optional[str] = None,
        environment: str = "development",
        release: Optional[str] = None
    ):
        """
        Initialize error tracker.

        Args:
            enable_sentry: Whether to enable Sentry integration
            sentry_dsn: Sentry DSN for error reporting
            environment: Environment name (development, staging, production)
            release: Application version/release identifier
        """
        self.logger = logging.getLogger(__name__)
        self.metrics = ErrorMetrics()
        self.environment = environment
        self.release = release
        self._custom_handlers: list[Callable] = []
        self._sentry_enabled = False

        # Initialize Sentry if enabled and DSN provided
        if enable_sentry and sentry_dsn:
            self._init_sentry(sentry_dsn)

    def _init_sentry(self, dsn: str) -> None:
        """
        Initialize Sentry SDK.

        Args:
            dsn: Sentry DSN
        """
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration

            sentry_logging = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )

            sentry_sdk.init(
                dsn=dsn,
                environment=self.environment,
                release=self.release,
                integrations=[sentry_logging],
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                profiles_sample_rate=0.1,  # 10% of transactions for profiling
                send_default_pii=False,  # Don't send personally identifiable information
            )

            self._sentry_enabled = True
            self.logger.info(f"Sentry error tracking initialized for {self.environment}")

        except ImportError:
            self.logger.warning(
                "Sentry SDK not installed. Install with: pip install sentry-sdk"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Sentry: {e}")

    def add_custom_handler(self, handler: Callable[[Exception, Dict[str, Any]], None]) -> None:
        """
        Add a custom error handler.

        Args:
            handler: Function that takes (exception, context) as arguments
        """
        self._custom_handlers.append(handler)

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Capture and track an exception.

        Args:
            exception: The exception to capture
            context: Additional context information
            category: Error category for classification
            severity: Error severity level
            extra: Extra metadata to attach
        """
        error_type = type(exception).__name__
        error_message = str(exception)

        # Record metrics
        self.metrics.record_error(error_type, category, severity)

        # Prepare context
        full_context = {
            "error_type": error_type,
            "error_message": error_message,
            "category": category.value,
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc(),
        }

        if context:
            full_context["context"] = context
        if extra:
            full_context["extra"] = extra

        # Log the error
        log_method = getattr(self.logger, severity.value, self.logger.error)
        log_method(
            f"[{category.value}] {error_type}: {error_message}",
            extra=full_context,
            exc_info=True
        )

        # Send to Sentry if enabled
        if self._sentry_enabled:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    # Set context
                    scope.set_tag("error_category", category.value)
                    scope.set_level(severity.value)

                    if context:
                        scope.set_context("custom", context)
                    if extra:
                        for key, value in extra.items():
                            scope.set_extra(key, value)

                    # Capture exception
                    sentry_sdk.capture_exception(exception)

            except Exception as e:
                self.logger.error(f"Failed to send error to Sentry: {e}")

        # Call custom handlers
        for handler in self._custom_handlers:
            try:
                handler(exception, full_context)
            except Exception as e:
                self.logger.error(f"Custom error handler failed: {e}")

    def capture_message(
        self,
        message: str,
        level: ErrorSeverity = ErrorSeverity.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Capture a message (non-exception event).

        Args:
            message: Message to capture
            level: Message severity level
            context: Additional context
        """
        # Log the message
        log_method = getattr(self.logger, level.value, self.logger.info)
        log_method(message, extra=context or {})

        # Send to Sentry if enabled
        if self._sentry_enabled:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    scope.set_level(level.value)
                    if context:
                        scope.set_context("custom", context)

                    sentry_sdk.capture_message(message, level=level.value)

            except Exception as e:
                self.logger.error(f"Failed to send message to Sentry: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current error metrics.

        Returns:
            Dictionary containing error metrics
        """
        return self.metrics.get_metrics()

    def reset_metrics(self) -> None:
        """Reset error metrics."""
        self.metrics.reset()


# Global error tracker instance
_global_tracker: Optional[ErrorTracker] = None


def initialize_error_tracking(
    enable_sentry: bool = False,
    sentry_dsn: Optional[str] = None,
    environment: str = "development",
    release: Optional[str] = None
) -> ErrorTracker:
    """
    Initialize global error tracking.

    Args:
        enable_sentry: Whether to enable Sentry integration
        sentry_dsn: Sentry DSN for error reporting
        environment: Environment name
        release: Application version

    Returns:
        ErrorTracker instance
    """
    global _global_tracker
    _global_tracker = ErrorTracker(
        enable_sentry=enable_sentry,
        sentry_dsn=sentry_dsn,
        environment=environment,
        release=release
    )
    return _global_tracker


def get_error_tracker() -> ErrorTracker:
    """
    Get the global error tracker instance.

    Returns:
        ErrorTracker instance

    Raises:
        RuntimeError: If error tracking hasn't been initialized
    """
    if _global_tracker is None:
        raise RuntimeError(
            "Error tracking not initialized. Call initialize_error_tracking() first."
        )
    return _global_tracker


def categorize_exception(exception: Exception) -> ErrorCategory:
    """
    Automatically categorize an exception based on its type.

    Args:
        exception: Exception to categorize

    Returns:
        ErrorCategory
    """
    import aiohttp
    import json

    exception_type = type(exception).__name__

    # Network errors
    if isinstance(exception, (
        aiohttp.ClientError,
        aiohttp.ServerTimeoutError,
        ConnectionError,
        TimeoutError,
    )):
        return ErrorCategory.NETWORK

    # Validation errors
    if isinstance(exception, (ValueError, TypeError, KeyError, AttributeError)):
        return ErrorCategory.VALIDATION

    # File I/O errors
    if isinstance(exception, (IOError, OSError, FileNotFoundError, PermissionError)):
        return ErrorCategory.FILE_IO

    # JSON/data parsing errors
    if isinstance(exception, (json.JSONDecodeError,)):
        return ErrorCategory.VALIDATION

    # Configuration errors
    if "config" in exception_type.lower() or "settings" in exception_type.lower():
        return ErrorCategory.CONFIGURATION

    return ErrorCategory.UNKNOWN


def get_error_severity(exception: Exception) -> ErrorSeverity:
    """
    Determine error severity based on exception type.

    Args:
        exception: Exception to evaluate

    Returns:
        ErrorSeverity
    """
    # Critical errors that should stop execution
    critical_exceptions = (
        SystemExit,
        KeyboardInterrupt,
        MemoryError,
    )

    if isinstance(exception, critical_exceptions):
        return ErrorSeverity.CRITICAL

    # Errors that indicate serious problems
    error_exceptions = (
        RuntimeError,
        ConnectionError,
        IOError,
    )

    if isinstance(exception, error_exceptions):
        return ErrorSeverity.ERROR

    # Warnings for non-critical issues
    warning_exceptions = (
        UserWarning,
        DeprecationWarning,
    )

    if isinstance(exception, warning_exceptions):
        return ErrorSeverity.WARNING

    # Default to ERROR for uncategorized exceptions
    return ErrorSeverity.ERROR
