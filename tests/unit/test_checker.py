"""
Unit Tests for WebsiteStatusChecker

Comprehensive tests for the core website status checking functionality including:
- URL normalization
- SSL verification
- Error handling
- Retry logic
- Status detection
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import ssl

from src.core.checker import (
    WebsiteStatusChecker,
    CheckResult,
    StatusResult,
    ErrorCategory,
    CheckerStats
)


@pytest.mark.unit
class TestWebsiteStatusCheckerInitialization:
    """Test WebsiteStatusChecker initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        checker = WebsiteStatusChecker()

        assert checker.max_concurrent == 100
        assert checker.timeout == 10
        assert checker.retry_count == 2
        assert checker.verify_ssl is True  # Should default to True

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        checker = WebsiteStatusChecker(
            max_concurrent=50,
            timeout=15,
            retry_count=3,
            verify_ssl=False
        )

        assert checker.max_concurrent == 50
        assert checker.timeout == 15
        assert checker.retry_count == 3
        assert checker.verify_ssl is False

    def test_init_ssl_verification_warning(self, caplog):
        """Test that disabling SSL verification logs a warning."""
        import logging
        caplog.set_level(logging.WARNING)

        checker = WebsiteStatusChecker(verify_ssl=False)

        assert any("SSL CERTIFICATE VERIFICATION DISABLED" in record.message
                  for record in caplog.records)

    def test_ssl_context_creation_secure(self):
        """Test SSL context creation with verification enabled."""
        checker = WebsiteStatusChecker(verify_ssl=True)

        assert checker.ssl_context is not None
        assert checker.ssl_context.check_hostname is True
        assert checker.ssl_context.verify_mode == ssl.CERT_REQUIRED

    def test_ssl_context_creation_insecure(self):
        """Test SSL context creation with verification disabled."""
        checker = WebsiteStatusChecker(verify_ssl=False)

        assert checker.ssl_context is not None
        assert checker.ssl_context.check_hostname is False
        assert checker.ssl_context.verify_mode == ssl.CERT_NONE


@pytest.mark.unit
class TestURLNormalization:
    """Test URL normalization functionality."""

    def test_normalize_valid_https_url(self):
        """Test normalization of valid HTTPS URLs."""
        checker = WebsiteStatusChecker()

        url = "https://example.com"
        normalized = checker.normalize_url(url)

        assert normalized == "https://example.com"

    def test_normalize_valid_http_url(self):
        """Test normalization of valid HTTP URLs."""
        checker = WebsiteStatusChecker()

        url = "http://example.com"
        normalized = checker.normalize_url(url)

        assert normalized == "http://example.com"

    def test_normalize_www_prefix(self):
        """Test normalization of URLs with www prefix."""
        checker = WebsiteStatusChecker()

        url = "www.example.com"
        normalized = checker.normalize_url(url)

        assert normalized == "https://www.example.com"

    def test_normalize_without_protocol(self):
        """Test normalization of URLs without protocol."""
        checker = WebsiteStatusChecker()

        url = "example.com"
        normalized = checker.normalize_url(url)

        assert normalized == "https://example.com"

    def test_normalize_uppercase_to_lowercase_domain(self):
        """Test that domains are normalized to lowercase."""
        checker = WebsiteStatusChecker()

        url = "https://EXAMPLE.COM"
        normalized = checker.normalize_url(url)

        assert normalized == "https://example.com"

    def test_normalize_with_path(self):
        """Test normalization preserves paths."""
        checker = WebsiteStatusChecker()

        url = "https://example.com/path/to/page"
        normalized = checker.normalize_url(url)

        assert normalized == "https://example.com/path/to/page"

    @pytest.mark.parametrize("invalid_url", [
        None,
        "",
        "   ",
        "nan",
        "null",
        "localhost",
        "example.local",
        "test.com",  # test TLD
        "mailto:test@example.com",
        "ftp://example.com",
        "javascript:alert('test')",
        "file:///etc/passwd",
    ])
    def test_normalize_invalid_urls_returns_none(self, invalid_url):
        """Test that invalid URLs return None."""
        checker = WebsiteStatusChecker()

        normalized = checker.normalize_url(invalid_url)

        assert normalized is None

    def test_normalize_with_invalid_tld(self):
        """Test URLs with invalid TLDs."""
        checker = WebsiteStatusChecker()

        # TLD must be at least 2 characters and alphabetic
        assert checker.normalize_url("example.1") is None
        assert checker.normalize_url("example.a") is None
        assert checker.normalize_url("example.123") is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestCheckWebsite:
    """Test single website checking functionality."""

    async def test_check_invalid_url_returns_invalid_result(self):
        """Test that invalid URLs return INVALID_URL status."""
        checker = WebsiteStatusChecker()

        result = await checker.check_website("not-a-url")

        assert result.status_result == StatusResult.INVALID_URL
        assert result.error_category == ErrorCategory.INVALID_URL_ERROR
        assert result.status_code == 0

    async def test_check_website_marks_as_checked(self):
        """Test that checked URLs are added to checked_urls set."""
        checker = WebsiteStatusChecker()

        # Mock the session to avoid actual HTTP request
        with patch.object(checker, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.url = "https://example.com"
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await checker.check_website("https://example.com")

            assert "https://example.com" in checker.checked_urls

    async def test_check_duplicate_url_returns_error(self):
        """Test that duplicate URLs are detected."""
        checker = WebsiteStatusChecker()

        # Add URL to checked set
        checker.checked_urls.add("https://example.com")

        result = await checker.check_website("https://example.com")

        assert result.status_result == StatusResult.ERROR
        assert "Already processed" in result.error_message

    async def test_check_website_success_200(self):
        """Test successful website check (200 status)."""
        checker = WebsiteStatusChecker()

        with patch.object(checker, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.url = "https://example.com"
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await checker.check_website("https://example.com")

            assert result.status_result == StatusResult.ACTIVE
            assert result.status_code == 200
            assert result.error_category is None

    async def test_check_website_inactive_404(self):
        """Test inactive website (404 status)."""
        checker = WebsiteStatusChecker()

        with patch.object(checker, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.url = "https://example.com"
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await checker.check_website("https://example.com")

            assert result.status_result == StatusResult.INACTIVE
            assert result.status_code == 404
            assert result.error_category == ErrorCategory.HTTP_ERROR

    async def test_check_website_timeout(self):
        """Test website check timeout."""
        checker = WebsiteStatusChecker(retry_count=0)

        with patch.object(checker, 'session') as mock_session:
            mock_session.get.side_effect = asyncio.TimeoutError()

            result = await checker.check_website("https://example.com")

            assert result.status_result == StatusResult.TIMEOUT
            assert result.error_category == ErrorCategory.TIMEOUT_ERROR

    async def test_check_website_dns_error(self):
        """Test DNS resolution error."""
        checker = WebsiteStatusChecker(retry_count=0)

        with patch.object(checker, 'session') as mock_session:
            mock_session.get.side_effect = aiohttp.ClientConnectorError(
                connection_key=None,
                os_error=OSError("name or service not known")
            )

            result = await checker.check_website("https://nonexistent.example")

            assert result.status_result == StatusResult.ERROR
            assert result.error_category == ErrorCategory.DNS_ERROR

    async def test_check_website_ssl_error(self):
        """Test SSL certificate error."""
        checker = WebsiteStatusChecker(retry_count=0, verify_ssl=True)

        with patch.object(checker, 'session') as mock_session:
            mock_session.get.side_effect = aiohttp.ClientSSLError(
                connection_key=None,
                certificate_error=ssl.SSLError("certificate verify failed")
            )

            result = await checker.check_website("https://example.com")

            assert result.status_result == StatusResult.ERROR
            assert result.error_category == ErrorCategory.SSL_ERROR


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryLogic:
    """Test retry logic and exponential backoff."""

    async def test_retry_on_failure(self):
        """Test that failures are retried."""
        checker = WebsiteStatusChecker(retry_count=2, retry_delay=0.1)

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.url = "https://example.com"
            return mock_response

        with patch.object(checker, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.side_effect = mock_get

            result = await checker.check_website("https://example.com")

            # Should succeed on third attempt
            assert result.status_result == StatusResult.ACTIVE
            assert result.retry_count == 2

    async def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        checker = WebsiteStatusChecker(retry_count=2)

        with patch.object(checker, 'session') as mock_session:
            mock_session.get.side_effect = asyncio.TimeoutError()

            result = await checker.check_website("https://example.com")

            assert result.status_result == StatusResult.TIMEOUT
            assert result.retry_count == 2


@pytest.mark.unit
class TestCheckerStats:
    """Test CheckerStats functionality."""

    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = CheckerStats()

        assert stats.total_checked == 0
        assert stats.active_found == 0
        assert stats.inactive_found == 0
        assert stats.errors == 0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = CheckerStats(
            total_checked=100,
            active_found=75
        )

        assert stats.success_rate == 75.0

    def test_success_rate_zero_division(self):
        """Test success rate when no URLs checked."""
        stats = CheckerStats()

        assert stats.success_rate == 0.0

    def test_checks_per_second_calculation(self):
        """Test checks per second calculation."""
        stats = CheckerStats(
            total_checked=100,
            total_time=10.0
        )

        assert stats.checks_per_second == 10.0


@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchChecking:
    """Test batch checking functionality."""

    async def test_check_websites_batch(self):
        """Test checking multiple websites concurrently."""
        checker = WebsiteStatusChecker(max_concurrent=5)

        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]

        with patch.object(checker, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.url = "https://example.com"
            mock_session.get.return_value.__aenter__.return_value = mock_response

            results = await checker.check_websites_batch(urls)

            assert len(results) == 3
            assert all(isinstance(r, CheckResult) for r in results)

    async def test_batch_respects_concurrency_limit(self):
        """Test that batch processing respects concurrency limits."""
        checker = WebsiteStatusChecker(max_concurrent=2)

        urls = ["https://example.com" for _ in range(10)]

        with patch.object(checker, 'check_website') as mock_check:
            mock_check.return_value = CheckResult(
                url="https://example.com",
                normalized_url="https://example.com",
                status_result=StatusResult.ACTIVE,
                status_code=200,
                error_category=None,
                error_message="",
                response_time=0.1,
                timestamp=1234567890.0,
                retry_count=0,
                final_url="https://example.com"
            )

            results = await checker.check_websites_batch(urls)

            assert len(results) == 10


@pytest.mark.unit
@pytest.mark.asyncio
class TestSessionManagement:
    """Test session creation and management."""

    async def test_create_session(self):
        """Test session creation."""
        checker = WebsiteStatusChecker()

        await checker.create_session()

        assert checker.session is not None
        assert isinstance(checker.session, aiohttp.ClientSession)

        await checker.close()

    async def test_close_session(self):
        """Test session cleanup."""
        checker = WebsiteStatusChecker()
        await checker.create_session()

        await checker.close()

        assert checker.session is None


@pytest.mark.unit
class TestCheckResult:
    """Test CheckResult data class."""

    def test_check_result_creation(self):
        """Test CheckResult creation."""
        result = CheckResult(
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

        assert result.url == "https://example.com"
        assert result.status_result == StatusResult.ACTIVE
        assert result.status_code == 200
        assert result.response_time == 0.5
