"""Display formatting utilities."""

from datetime import timedelta


def format_time(seconds: float) -> str:
    """
    Format seconds to HH:MM:SS.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 0:
        return "--:--:--"

    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_rate(rate: float) -> str:
    """
    Format processing rate.

    Args:
        rate: URLs per second

    Returns:
        Formatted rate string
    """
    if rate < 0:
        return "0.0 URLs/sec"
    return f"{rate:.1f} URLs/sec"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage.

    Args:
        value: Current value
        total: Total value

    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"


def format_number(number: int) -> str:
    """
    Format number with thousand separators.

    Args:
        number: Number to format

    Returns:
        Formatted number string
    """
    return f"{number:,}"


def format_response_time(milliseconds: float) -> str:
    """
    Format response time in milliseconds.

    Args:
        milliseconds: Response time in ms

    Returns:
        Formatted response time string
    """
    if milliseconds < 0:
        return "-"
    elif milliseconds < 1000:
        return f"{milliseconds:.0f} ms"
    else:
        return f"{milliseconds / 1000:.2f} s"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
