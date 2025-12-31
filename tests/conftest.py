"""
Pytest Configuration and Shared Fixtures

Provides common fixtures and configuration for all test modules.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
import tempfile
import shutil

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.checker import WebsiteStatusChecker, CheckResult, StatusResult
from src.core.batch import BatchProcessor, BatchConfig
from src.config import AppConfig, CheckerConfig
import pandas as pd


# ==============================================================================
# Pytest Configuration
# ==============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


# ==============================================================================
# Event Loop Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==============================================================================
# Temporary Directory Fixtures
# ==============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


# ==============================================================================
# Configuration Fixtures
# ==============================================================================

@pytest.fixture
def test_config() -> AppConfig:
    """Create a test application configuration."""
    # Set test environment variables
    os.environ["ENV"] = "development"
    os.environ["DEBUG"] = "true"
    os.environ["SSL_VERIFY_DEFAULT"] = "true"

    return AppConfig()


@pytest.fixture
def checker_config() -> CheckerConfig:
    """Create a test checker configuration."""
    return CheckerConfig(
        max_concurrent=10,
        timeout=5,
        retry_count=1,
        verify_ssl=True
    )


@pytest.fixture
def batch_config() -> BatchConfig:
    """Create a test batch configuration."""
    return BatchConfig(
        batch_size=10,
        max_concurrent=5,
        timeout=5,
        retry_count=1,
        verify_ssl=True
    )


# ==============================================================================
# Checker Fixtures
# ==============================================================================

@pytest.fixture
async def checker() -> AsyncGenerator[WebsiteStatusChecker, None]:
    """Create a WebsiteStatusChecker instance for testing."""
    checker = WebsiteStatusChecker(
        max_concurrent=10,
        timeout=5,
        retry_count=1,
        verify_ssl=True
    )
    yield checker
    # Cleanup
    await checker.close()


@pytest.fixture
async def checker_no_ssl() -> AsyncGenerator[WebsiteStatusChecker, None]:
    """Create a WebsiteStatusChecker with SSL verification disabled."""
    checker = WebsiteStatusChecker(
        max_concurrent=10,
        timeout=5,
        retry_count=1,
        verify_ssl=False
    )
    yield checker
    await checker.close()


# ==============================================================================
# Batch Processor Fixtures
# ==============================================================================

@pytest.fixture
def batch_processor(batch_config: BatchConfig) -> BatchProcessor:
    """Create a BatchProcessor instance for testing."""
    return BatchProcessor(batch_config)


# ==============================================================================
# Sample Data Fixtures
# ==============================================================================

@pytest.fixture
def sample_urls() -> list[str]:
    """Provide a list of sample URLs for testing."""
    return [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.python.org",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
    ]


@pytest.fixture
def invalid_urls() -> list[str]:
    """Provide a list of invalid URLs for testing."""
    return [
        "not-a-url",
        "http://",
        "ftp://example.com",
        "javascript:alert('test')",
        "mailto:test@example.com",
        "",
        "localhost",
        "example",
    ]


@pytest.fixture
def mixed_urls() -> list[str]:
    """Provide a mix of valid and invalid URLs."""
    return [
        "https://www.google.com",
        "not-a-url",
        "https://httpbin.org/status/200",
        "http://",
        "www.github.com",
        "example.com",
    ]


# ==============================================================================
# CSV Test Data Fixtures
# ==============================================================================

@pytest.fixture
def sample_csv_file(temp_dir: Path) -> Path:
    """Create a sample CSV file with URLs."""
    csv_file = temp_dir / "test_urls.csv"

    df = pd.DataFrame({
        "url": [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.python.org",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
        ]
    })

    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def large_csv_file(temp_dir: Path) -> Path:
    """Create a large CSV file for performance testing."""
    csv_file = temp_dir / "large_urls.csv"

    # Create 1000 URLs
    urls = [f"https://example{i}.com" for i in range(1000)]
    df = pd.DataFrame({"url": urls})

    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def invalid_csv_file(temp_dir: Path) -> Path:
    """Create a CSV file with invalid URLs."""
    csv_file = temp_dir / "invalid_urls.csv"

    df = pd.DataFrame({
        "url": [
            "not-a-url",
            "http://",
            "ftp://example.com",
            "javascript:alert('test')",
        ]
    })

    df.to_csv(csv_file, index=False)
    return csv_file


# ==============================================================================
# Mock Response Fixtures
# ==============================================================================

@pytest.fixture
def mock_check_result() -> CheckResult:
    """Create a mock CheckResult for testing."""
    return CheckResult(
        url="https://example.com",
        normalized_url="https://example.com",
        status_result=StatusResult.ACTIVE,
        status_code=200,
        error_category=None,
        error_message="",
        response_time=0.5,
        timestamp=1234567890.0,
        retry_count=0,
        final_url="https://example.com"
    )


@pytest.fixture
def mock_error_result() -> CheckResult:
    """Create a mock error CheckResult for testing."""
    from src.core.checker import ErrorCategory

    return CheckResult(
        url="https://nonexistent.example",
        normalized_url="https://nonexistent.example",
        status_result=StatusResult.ERROR,
        status_code=0,
        error_category=ErrorCategory.DNS_ERROR,
        error_message="DNS resolution failed",
        response_time=2.0,
        timestamp=1234567890.0,
        retry_count=2,
        final_url=""
    )


# ==============================================================================
# Environment Variable Fixtures
# ==============================================================================

@pytest.fixture
def clean_env():
    """Clean environment variables for testing."""
    # Store original env vars
    original_env = os.environ.copy()

    # Clear relevant env vars
    test_vars = [
        "ENV", "DEBUG", "SSL_VERIFY_DEFAULT", "DEFAULT_CONCURRENT",
        "DEFAULT_TIMEOUT", "SECRET_KEY", "ALLOWED_ORIGINS"
    ]

    for var in test_vars:
        os.environ.pop(var, None)

    yield

    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def production_env(clean_env):
    """Set up production environment variables."""
    os.environ["ENV"] = "production"
    os.environ["DEBUG"] = "false"
    os.environ["SSL_VERIFY_DEFAULT"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-with-sufficient-length-for-production"
    os.environ["ALLOWED_ORIGINS"] = "https://example.com"
    yield


# ==============================================================================
# FastAPI Test Client Fixtures
# ==============================================================================

@pytest.fixture
def test_client():
    """Create a test client for FastAPI application."""
    from fastapi.testclient import TestClient
    from gui.main import app

    return TestClient(app)


# ==============================================================================
# Helper Functions
# ==============================================================================

def create_test_csv(file_path: Path, urls: list[str], column_name: str = "url") -> None:
    """
    Helper function to create a test CSV file.

    Args:
        file_path: Path to CSV file
        urls: List of URLs to include
        column_name: Name of the URL column
    """
    df = pd.DataFrame({column_name: urls})
    df.to_csv(file_path, index=False)


def assert_check_result_valid(result: CheckResult) -> None:
    """
    Helper function to assert CheckResult is valid.

    Args:
        result: CheckResult to validate
    """
    assert result is not None
    assert isinstance(result, CheckResult)
    assert result.url is not None
    assert isinstance(result.status_result, StatusResult)
    assert isinstance(result.status_code, int)
    assert isinstance(result.response_time, (int, float))
    assert isinstance(result.timestamp, (int, float))
    assert isinstance(result.retry_count, int)


# Make helper functions available to all tests
pytest.create_test_csv = create_test_csv
pytest.assert_check_result_valid = assert_check_result_valid
