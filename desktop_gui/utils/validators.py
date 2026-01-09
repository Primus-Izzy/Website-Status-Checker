"""Input validation utilities."""

from pathlib import Path
from typing import Tuple, Optional


def validate_batch_size(value: int) -> Tuple[bool, Optional[str]]:
    """
    Validate batch size.

    Args:
        value: Batch size to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, "Batch size must be an integer"

    if value < 100:
        return False, "Batch size must be at least 100"

    if value > 10000:
        return False, "Batch size cannot exceed 10,000"

    return True, None


def validate_concurrent(value: int) -> Tuple[bool, Optional[str]]:
    """
    Validate concurrent requests.

    Args:
        value: Concurrent requests to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, "Concurrent requests must be an integer"

    if value < 1:
        return False, "Concurrent requests must be at least 1"

    if value > 500:
        return False, "Concurrent requests cannot exceed 500"

    return True, None


def validate_timeout(value: int) -> Tuple[bool, Optional[str]]:
    """
    Validate timeout.

    Args:
        value: Timeout to validate (in seconds)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, "Timeout must be an integer"

    if value < 5:
        return False, "Timeout must be at least 5 seconds"

    if value > 120:
        return False, "Timeout cannot exceed 120 seconds"

    return True, None


def validate_retry_count(value: int) -> Tuple[bool, Optional[str]]:
    """
    Validate retry count.

    Args:
        value: Retry count to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, "Retry count must be an integer"

    if value < 0:
        return False, "Retry count cannot be negative"

    if value > 10:
        return False, "Retry count cannot exceed 10"

    return True, None


def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file path.

    Args:
        file_path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path cannot be empty"

    path = Path(file_path)

    if not path.exists():
        return False, f"File not found: {file_path}"

    if not path.is_file():
        return False, f"Path is not a file: {file_path}"

    if not path.suffix.lower() in ['.csv', '.xlsx', '.xls', '.txt']:
        return False, f"Unsupported file format: {path.suffix}"

    return True, None


def validate_column_name(column_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate column name.

    Args:
        column_name: Column name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not column_name:
        return False, "Column name cannot be empty"

    if len(column_name) > 100:
        return False, "Column name too long (max 100 characters)"

    return True, None
