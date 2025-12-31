"""
Core Application Configuration Module

Manages environment-based configuration for the CLI and core checker
with validation and secure defaults.
"""

import os
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CheckerConfig:
    """Configuration for website status checker."""

    # Performance settings
    max_concurrent: int = field(default_factory=lambda: int(os.getenv("DEFAULT_CONCURRENT", "100")))
    timeout: int = field(default_factory=lambda: int(os.getenv("DEFAULT_TIMEOUT", "10")))
    retry_count: int = field(default_factory=lambda: int(os.getenv("DEFAULT_RETRY_COUNT", "2")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("DEFAULT_RETRY_DELAY", "1.0")))
    backoff_factor: float = field(default_factory=lambda: float(os.getenv("DEFAULT_BACKOFF_FACTOR", "1.5")))

    # Security settings
    verify_ssl: bool = field(default_factory=lambda: os.getenv("SSL_VERIFY_DEFAULT", "true").lower() == "true")

    # User agent
    user_agent: Optional[str] = field(default_factory=lambda: os.getenv("USER_AGENT"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if self.max_concurrent > 10000:
            raise ValueError("max_concurrent cannot exceed 10000 (too many connections)")

        if self.timeout < 1:
            raise ValueError("timeout must be at least 1 second")
        if self.timeout > 300:
            raise ValueError("timeout cannot exceed 300 seconds (5 minutes)")

        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative")
        if self.retry_count > 10:
            raise ValueError("retry_count cannot exceed 10 (too many retries)")

        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")

        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1.0")


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    # Batch settings
    batch_size: int = field(default_factory=lambda: int(os.getenv("DEFAULT_BATCH_SIZE", "1000")))
    save_interval: int = field(default_factory=lambda: int(os.getenv("DEFAULT_SAVE_INTERVAL", "10")))
    memory_efficient: bool = field(default_factory=lambda: os.getenv("MEMORY_EFFICIENT", "true").lower() == "true")

    # Output settings
    include_inactive: bool = field(default_factory=lambda: os.getenv("INCLUDE_INACTIVE", "true").lower() == "true")
    include_errors: bool = field(default_factory=lambda: os.getenv("INCLUDE_ERRORS", "false").lower() == "true")

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.batch_size > 100000:
            raise ValueError("batch_size cannot exceed 100000 (memory concerns)")

        if self.save_interval < 1:
            raise ValueError("save_interval must be at least 1")


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "text"))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of: {allowed_levels}")

        allowed_formats = ["text", "json"]
        if self.log_format.lower() not in allowed_formats:
            raise ValueError(f"log_format must be one of: {allowed_formats}")

        # Normalize log level to uppercase
        self.log_level = self.log_level.upper()


@dataclass
class AppConfig:
    """Main application configuration."""

    # Environment
    env: str = field(default_factory=lambda: os.getenv("ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Component configs
    checker: CheckerConfig = field(default_factory=CheckerConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Progress tracking
    progress_file: str = field(default_factory=lambda: os.getenv("PROGRESS_FILE", "website_check_progress.json"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        allowed_envs = ["development", "staging", "production"]
        if self.env not in allowed_envs:
            raise ValueError(f"env must be one of: {allowed_envs}")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.env == "development"

    def validate_production_config(self) -> list[str]:
        """
        Validate configuration for production deployment.

        Returns:
            List of validation warnings/errors
        """
        issues = []

        if self.is_production:
            # Check if debug is enabled
            if self.debug:
                issues.append("WARNING: Debug mode is enabled in production")

            # Check if SSL verification is disabled
            if not self.checker.verify_ssl:
                issues.append("CRITICAL: SSL verification is disabled in production")

            # Check concurrent connections
            if self.checker.max_concurrent > 1000:
                issues.append(f"WARNING: Very high concurrent connections ({self.checker.max_concurrent})")

            # Check timeout
            if self.checker.timeout < 5:
                issues.append(f"WARNING: Very short timeout ({self.checker.timeout}s) may cause false negatives")

        return issues


def load_env_file(env_file: str = ".env") -> None:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file
    """
    env_path = Path(env_file)
    if not env_path.exists():
        return

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable if not already set
                if key not in os.environ:
                    os.environ[key] = value


def get_config() -> AppConfig:
    """
    Get application configuration.

    Loads configuration from environment variables and .env file.

    Returns:
        AppConfig instance
    """
    # Try to load .env file
    load_env_file()

    # Create and return config
    return AppConfig()


# Singleton instance
_config: Optional[AppConfig] = None


def get_app_config() -> AppConfig:
    """
    Get singleton application configuration instance.

    Returns:
        AppConfig instance
    """
    global _config
    if _config is None:
        _config = get_config()
    return _config
