"""
Unit Tests for Configuration Module

Tests for configuration loading, validation, and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch

from src.config import (
    CheckerConfig,
    BatchConfig,
    LoggingConfig,
    AppConfig,
    get_app_config,
    load_env_file
)


@pytest.mark.unit
class TestCheckerConfig:
    """Test CheckerConfig functionality."""

    def test_default_values(self, clean_env):
        """Test default configuration values."""
        config = CheckerConfig()

        assert config.max_concurrent == 100
        assert config.timeout == 10
        assert config.retry_count == 2
        assert config.verify_ssl is True

    def test_env_var_override(self, clean_env):
        """Test that environment variables override defaults."""
        os.environ["DEFAULT_CONCURRENT"] = "200"
        os.environ["DEFAULT_TIMEOUT"] = "15"
        os.environ["SSL_VERIFY_DEFAULT"] = "false"

        config = CheckerConfig()

        assert config.max_concurrent == 200
        assert config.timeout == 15
        assert config.verify_ssl is False

    def test_validation_max_concurrent_too_low(self, clean_env):
        """Test validation rejects max_concurrent < 1."""
        os.environ["DEFAULT_CONCURRENT"] = "0"

        with pytest.raises(ValueError, match="max_concurrent must be at least 1"):
            CheckerConfig()

    def test_validation_max_concurrent_too_high(self, clean_env):
        """Test validation rejects max_concurrent > 10000."""
        os.environ["DEFAULT_CONCURRENT"] = "20000"

        with pytest.raises(ValueError, match="max_concurrent cannot exceed 10000"):
            CheckerConfig()

    def test_validation_timeout_too_low(self, clean_env):
        """Test validation rejects timeout < 1."""
        os.environ["DEFAULT_TIMEOUT"] = "0"

        with pytest.raises(ValueError, match="timeout must be at least 1"):
            CheckerConfig()

    def test_validation_retry_count_negative(self, clean_env):
        """Test validation rejects negative retry_count."""
        os.environ["DEFAULT_RETRY_COUNT"] = "-1"

        with pytest.raises(ValueError, match="retry_count cannot be negative"):
            CheckerConfig()


@pytest.mark.unit
class TestAppConfig:
    """Test AppConfig functionality."""

    def test_default_environment(self, clean_env):
        """Test default environment is development."""
        config = AppConfig()

        assert config.env == "development"
        assert config.is_development is True
        assert config.is_production is False

    def test_production_environment(self, clean_env):
        """Test production environment configuration."""
        os.environ["ENV"] = "production"

        config = AppConfig()

        assert config.env == "production"
        assert config.is_production is True
        assert config.is_development is False

    def test_invalid_environment(self, clean_env):
        """Test invalid environment value is rejected."""
        os.environ["ENV"] = "invalid"

        with pytest.raises(ValueError, match="env must be one of"):
            AppConfig()

    def test_production_validation_ssl_disabled(self, production_env):
        """Test production validation catches disabled SSL."""
        os.environ["SSL_VERIFY_DEFAULT"] = "false"

        config = AppConfig()
        issues = config.validate_production_config()

        assert any("SSL verification is disabled" in issue for issue in issues)

    def test_production_validation_debug_enabled(self, production_env):
        """Test production validation catches debug mode."""
        os.environ["DEBUG"] = "true"

        config = AppConfig()
        issues = config.validate_production_config()

        assert any("Debug mode is enabled" in issue for issue in issues)


@pytest.mark.unit
class TestLoggingConfig:
    """Test LoggingConfig functionality."""

    def test_default_log_level(self, clean_env):
        """Test default log level."""
        config = LoggingConfig()

        assert config.log_level == "INFO"

    def test_log_level_normalization(self, clean_env):
        """Test log level is normalized to uppercase."""
        os.environ["LOG_LEVEL"] = "debug"

        config = LoggingConfig()

        assert config.log_level == "DEBUG"

    def test_invalid_log_level(self, clean_env):
        """Test invalid log level is rejected."""
        os.environ["LOG_LEVEL"] = "INVALID"

        with pytest.raises(ValueError, match="log_level must be one of"):
            LoggingConfig()

    def test_invalid_log_format(self, clean_env):
        """Test invalid log format is rejected."""
        os.environ["LOG_FORMAT"] = "invalid"

        with pytest.raises(ValueError, match="log_format must be one of"):
            LoggingConfig()


@pytest.mark.unit
class TestEnvFileLoading:
    """Test .env file loading."""

    def test_load_env_file(self, temp_dir, clean_env):
        """Test loading environment variables from .env file."""
        env_file = temp_dir / ".env"
        env_file.write_text("""
# Test environment file
ENV=production
DEBUG=false
DEFAULT_CONCURRENT=200
        """)

        load_env_file(str(env_file))

        assert os.getenv("ENV") == "production"
        assert os.getenv("DEBUG") == "false"
        assert os.getenv("DEFAULT_CONCURRENT") == "200"

    def test_load_env_file_with_quotes(self, temp_dir, clean_env):
        """Test loading env file with quoted values."""
        env_file = temp_dir / ".env"
        env_file.write_text("""
SECRET_KEY="quoted-value"
ALLOWED_ORIGINS='single-quoted'
        """)

        load_env_file(str(env_file))

        assert os.getenv("SECRET_KEY") == "quoted-value"
        assert os.getenv("ALLOWED_ORIGINS") == "single-quoted"

    def test_load_nonexistent_env_file(self, clean_env):
        """Test loading non-existent .env file doesn't error."""
        # Should not raise an exception
        load_env_file("nonexistent.env")
