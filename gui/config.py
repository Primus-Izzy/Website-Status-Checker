"""
GUI Configuration Module

Manages environment-based configuration for the web interface with
security-focused defaults and validation.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    For production deployment, set these in .env file or system environment.
    """

    # Environment
    env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Application
    app_name: str = Field(default="Website Status Checker", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="Secret key for sessions")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload (development only)")

    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins (comma-separated in env)"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")

    # File Upload Configuration
    max_upload_size_mb: int = Field(default=100, description="Maximum upload size in MB")
    upload_dir: str = Field(default="gui/uploads", description="Upload directory path")
    export_dir: str = Field(default="gui/exports", description="Export directory path")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_uploads_per_minute: int = Field(default=100, description="Upload requests per minute per IP")
    rate_limit_requests_per_hour: int = Field(default=1000, description="Total requests per hour per IP")

    # SSL/TLS Configuration
    ssl_verify_default: bool = Field(default=True, description="Default SSL verification setting")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="text", description="Log format: text or json")
    log_file: str = Field(default="", description="Log file path (empty for stdout only)")

    # Authentication
    admin_api_key: str = Field(default="", description="Admin API key for managing API keys")

    # Database (for future use)
    database_url: str = Field(default="sqlite:///./jobs.db", description="Database connection URL")

    # Job Management
    job_retention_hours: int = Field(default=24, description="Hours to retain completed jobs")
    max_concurrent_jobs: int = Field(default=10, description="Maximum concurrent processing jobs")

    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")

    # Error Tracking
    enable_error_tracking: bool = Field(default=True, description="Enable error tracking")
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")
    sentry_environment: str = Field(default="", description="Sentry environment (defaults to env)")
    sentry_traces_sample_rate: float = Field(default=0.1, description="Sentry traces sample rate")

    # Security Headers
    enable_security_headers: bool = Field(default=True, description="Enable security headers")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from string or list."""
        if isinstance(v, str):
            # Split comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("env")
    @classmethod
    def validate_env(cls, v):
        """Validate environment value."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"env must be one of: {allowed_envs}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"log_level must be one of: {allowed_levels}")
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        allowed_formats = ["text", "json"]
        if v not in allowed_formats:
            raise ValueError(f"log_format must be one of: {allowed_formats}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def get_cors_config(self) -> dict:
        """
        Get CORS configuration based on environment.

        Returns:
            Dictionary with CORS configuration
        """
        if self.is_production:
            # Strict CORS in production
            return {
                "allow_origins": self.allowed_origins,
                "allow_credentials": self.allow_credentials,
                "allow_methods": ["GET", "POST", "PUT", "DELETE"],
                "allow_headers": ["*"],
                "max_age": 600,
            }
        else:
            # More permissive in development
            return {
                "allow_origins": self.allowed_origins + ["http://localhost:*"],
                "allow_credentials": self.allow_credentials,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            }

    def validate_production_config(self) -> List[str]:
        """
        Validate configuration for production deployment.

        Returns:
            List of validation warnings/errors
        """
        issues = []

        if self.is_production:
            # Check for wildcard origins
            if "*" in self.allowed_origins:
                issues.append("CRITICAL: Wildcard '*' in allowed_origins is not allowed in production")

            # Check for localhost in origins
            localhost_origins = [o for o in self.allowed_origins if "localhost" in o]
            if localhost_origins:
                issues.append(f"WARNING: Localhost origins in production: {localhost_origins}")

            # Check if debug is enabled
            if self.debug:
                issues.append("WARNING: Debug mode is enabled in production")

            # Check if SSL verification is disabled
            if not self.ssl_verify_default:
                issues.append("WARNING: SSL verification is disabled by default")

            # Check if default secret key is being used
            if len(self.secret_key) < 32:
                issues.append("CRITICAL: Secret key is too short (minimum 32 characters)")

            # Check rate limiting
            if not self.rate_limit_enabled:
                issues.append("WARNING: Rate limiting is disabled")

        return issues


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.

    Returns:
        Settings instance
    """
    return settings
