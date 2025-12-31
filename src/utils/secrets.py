"""
Secrets and Security Utilities

Provides utilities for secure secret generation, environment variable
validation, and security checks.
"""

import os
import secrets
import string
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret key.

    Args:
        length: Length of the secret key (default: 32)

    Returns:
        URL-safe base64-encoded secret key

    Example:
        >>> key = generate_secret_key()
        >>> len(key) >= 32
        True
    """
    return secrets.token_urlsafe(length)


def generate_password(length: int = 16, include_symbols: bool = True) -> str:
    """
    Generate a secure random password.

    Args:
        length: Password length (default: 16)
        include_symbols: Include special characters (default: True)

    Returns:
        Secure random password

    Example:
        >>> pwd = generate_password()
        >>> len(pwd) == 16
        True
    """
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += "!@#$%^&*-_=+"

    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def validate_secret_key(key: Optional[str], min_length: int = 32) -> tuple[bool, Optional[str]]:
    """
    Validate a secret key for security.

    Args:
        key: Secret key to validate
        min_length: Minimum required length

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_secret_key("short")
        (False, 'Secret key is too short (minimum 32 characters)')
        >>> validate_secret_key(generate_secret_key())
        (True, None)
    """
    if not key:
        return False, "Secret key is not set"

    if len(key) < min_length:
        return False, f"Secret key is too short (minimum {min_length} characters)"

    # Check for common weak keys
    weak_keys = [
        "secret",
        "password",
        "changeme",
        "your-secret-key-here",
        "your-secret-key-here-change-in-production",
        "default",
        "test",
    ]

    if key.lower() in weak_keys or any(weak in key.lower() for weak in weak_keys):
        return False, "Secret key appears to be a default/weak value"

    return True, None


def validate_environment(required_vars: Optional[List[str]] = None,
                        env: str = "development") -> tuple[bool, List[str]]:
    """
    Validate environment variables are properly set.

    Args:
        required_vars: List of required environment variable names
        env: Environment name (development, staging, production)

    Returns:
        Tuple of (all_valid, list_of_issues)

    Example:
        >>> os.environ["TEST_VAR"] = "value"
        >>> validate_environment(["TEST_VAR"])
        (True, [])
        >>> validate_environment(["MISSING_VAR"])
        (False, ['Required environment variable not set: MISSING_VAR'])
    """
    issues = []

    # Check required variables
    if required_vars:
        for var in required_vars:
            if var not in os.environ or not os.environ[var]:
                issues.append(f"Required environment variable not set: {var}")

    # Production-specific checks
    if env == "production":
        # Check SECRET_KEY in production
        if "SECRET_KEY" in os.environ:
            is_valid, error = validate_secret_key(os.environ["SECRET_KEY"])
            if not is_valid:
                issues.append(f"SECRET_KEY validation failed: {error}")

        # Check SSL verification is enabled
        if os.getenv("SSL_VERIFY_DEFAULT", "true").lower() != "true":
            issues.append("WARNING: SSL verification is disabled in production")

        # Check debug mode is off
        if os.getenv("DEBUG", "false").lower() == "true":
            issues.append("WARNING: Debug mode is enabled in production")

        # Check CORS origins don't use wildcards
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if "*" in allowed_origins:
            issues.append("CRITICAL: Wildcard (*) in ALLOWED_ORIGINS is not allowed in production")

    return len(issues) == 0, issues


def get_env_info() -> Dict[str, Any]:
    """
    Get environment information for debugging/logging.

    Returns:
        Dictionary with environment information (safe for logging)

    Example:
        >>> info = get_env_info()
        >>> 'env' in info
        True
    """
    return {
        "env": os.getenv("ENV", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "ssl_verify": os.getenv("SSL_VERIFY_DEFAULT", "true").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_concurrent": os.getenv("DEFAULT_CONCURRENT", "100"),
        "timeout": os.getenv("DEFAULT_TIMEOUT", "10"),
        "rate_limiting": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
    }


def check_file_permissions(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Check if a file has appropriate permissions.

    Args:
        file_path: Path to file to check

    Returns:
        Tuple of (is_safe, warning_message)
    """
    try:
        import stat

        # Check if file exists
        if not os.path.exists(file_path):
            return True, None

        # Get file stats
        st = os.stat(file_path)
        mode = st.st_mode

        # Check if file is world-readable (on Unix-like systems)
        if hasattr(stat, 'S_IROTH'):
            if mode & stat.S_IROTH:
                return False, f"File {file_path} is world-readable (potential security risk)"

        # Check if file is world-writable
        if hasattr(stat, 'S_IWOTH'):
            if mode & stat.S_IWOTH:
                return False, f"File {file_path} is world-writable (CRITICAL security risk)"

        return True, None

    except Exception as e:
        logger.warning(f"Could not check file permissions for {file_path}: {e}")
        return True, None


def sanitize_for_logging(value: str, is_secret: bool = False) -> str:
    """
    Sanitize values for safe logging.

    Args:
        value: Value to sanitize
        is_secret: Whether this is a secret value

    Returns:
        Sanitized value safe for logging

    Example:
        >>> sanitize_for_logging("my-secret-key", is_secret=True)
        '***...***'
        >>> sanitize_for_logging("normal-value")
        'normal-value'
    """
    if not value:
        return "<empty>"

    if is_secret:
        if len(value) <= 6:
            return "***"
        return f"{value[:3]}...{value[-3:]}"

    return value


def validate_url_safety(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL for safety (check for SSRF, etc.).

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_safe, warning_message)

    Example:
        >>> validate_url_safety("https://example.com")
        (True, None)
        >>> validate_url_safety("http://localhost")
        (False, 'URL points to localhost (potential SSRF)')
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Check for localhost/internal IPs
        dangerous_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "169.254.",  # Link-local
            "10.",       # Private IP
            "172.16.",   # Private IP
            "192.168.",  # Private IP
        ]

        hostname = parsed.hostname or parsed.netloc.lower()

        for dangerous in dangerous_hosts:
            if dangerous in hostname:
                return False, f"URL points to {dangerous} (potential SSRF)"

        # Check for file:// protocol
        if parsed.scheme == "file":
            return False, "file:// URLs are not allowed"

        return True, None

    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


if __name__ == "__main__":
    # Example usage
    print("Generated secret key:", generate_secret_key())
    print("Generated password:", generate_password())

    # Validate environment
    is_valid, issues = validate_environment()
    if is_valid:
        print("✓ Environment validation passed")
    else:
        print("✗ Environment validation failed:")
        for issue in issues:
            print(f"  - {issue}")

    # Show environment info
    print("\nEnvironment info:")
    for key, value in get_env_info().items():
        print(f"  {key}: {value}")
