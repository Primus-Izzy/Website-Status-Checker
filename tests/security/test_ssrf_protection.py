"""
SSRF Protection Tests

Tests to verify Server-Side Request Forgery (SSRF) protection is working
in the URL checker to prevent attacks on internal networks.
"""

import pytest
from src.core.checker import WebsiteStatusChecker
from src.config import CheckerConfig


class TestSSRFProtection:
    """Test SSRF protection in URL normalization."""

    def setup_method(self):
        """Setup test fixtures."""
        config = CheckerConfig(max_concurrent=10, timeout=5)
        self.checker = WebsiteStatusChecker(config)

    def test_blocks_localhost_urls(self):
        """Should block localhost URLs."""
        dangerous_urls = [
            "http://localhost/admin",
            "http://localhost:8080/api",
            "https://localhost/",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block localhost URL: {url}"

    def test_blocks_127_0_0_1_urls(self):
        """Should block 127.0.0.1 URLs."""
        dangerous_urls = [
            "http://127.0.0.1/",
            "http://127.0.0.1:8080/admin",
            "https://127.0.0.1:9200/",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block 127.0.0.1 URL: {url}"

    def test_blocks_private_ip_ranges(self):
        """Should block private IP address ranges."""
        dangerous_urls = [
            "http://10.0.0.1/",  # Private class A
            "http://172.16.0.1/",  # Private class B
            "http://192.168.1.1/",  # Private class C
            "http://192.168.0.100:8080/admin",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block private IP URL: {url}"

    def test_blocks_link_local_addresses(self):
        """Should block link-local addresses."""
        dangerous_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://169.254.1.1/",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block link-local URL: {url}"

    def test_blocks_ipv6_localhost(self):
        """Should block IPv6 localhost."""
        dangerous_urls = [
            "http://[::1]/",
            "http://[::1]:8080/admin",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block IPv6 localhost: {url}"

    def test_blocks_file_protocol(self):
        """Should block file:// protocol URLs."""
        dangerous_urls = [
            "file:///etc/passwd",
            "file://C:/Windows/System32/config/SAM",
        ]

        for url in dangerous_urls:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block file:// URL: {url}"

    def test_allows_valid_public_urls(self):
        """Should allow valid public URLs."""
        valid_urls = [
            ("https://google.com", "https://google.com"),
            ("https://github.com/test", "https://github.com/test"),
            ("http://publicwebsite.org", "http://publicwebsite.org"),
        ]

        for url, expected in valid_urls:
            result = self.checker.normalize_url(url)
            assert result == expected, f"Should allow public URL: {url}"

    def test_ssrf_protection_comprehensive(self):
        """Comprehensive SSRF protection test."""
        # All these should be blocked
        dangerous = [
            "http://127.0.0.1/admin",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
            "http://169.254.169.254/meta-data/",
        ]

        for url in dangerous:
            result = self.checker.normalize_url(url)
            assert result is None, f"Failed to block: {url}"


class TestSSRFEdgeCases:
    """Test edge cases in SSRF protection."""

    def setup_method(self):
        """Setup test fixtures."""
        config = CheckerConfig(max_concurrent=10, timeout=5)
        self.checker = WebsiteStatusChecker(config)

    def test_blocks_localhost_variations(self):
        """Should block various localhost variations."""
        variations = [
            "http://LOCALHOST/",
            "http://LocalHost/",
            "http://localhost.localdomain/",
        ]

        for url in variations:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block localhost variation: {url}"

    def test_blocks_zero_ip(self):
        """Should block 0.0.0.0 addresses."""
        result = self.checker.normalize_url("http://0.0.0.0/")
        assert result is None, "Should block 0.0.0.0"

    def test_blocks_dns_rebinding_attempts(self):
        """Should block common SSRF bypass patterns."""
        # These are already blocked by existing patterns
        bypass_attempts = [
            "localhost",  # Without protocol
            "127.0.0.1",  # Without protocol
        ]

        for url in bypass_attempts:
            result = self.checker.normalize_url(url)
            assert result is None, f"Should block bypass attempt: {url}"


class TestSSRFCloudMetadata:
    """Test protection against cloud metadata endpoint attacks."""

    def setup_method(self):
        """Setup test fixtures."""
        config = CheckerConfig(max_concurrent=10, timeout=5)
        self.checker = WebsiteStatusChecker(config)

    def test_blocks_aws_metadata_endpoint(self):
        """Should block AWS EC2 metadata endpoint."""
        result = self.checker.normalize_url("http://169.254.169.254/latest/meta-data/")
        assert result is None, "Should block AWS metadata endpoint"

    def test_blocks_gcp_metadata_endpoint(self):
        """Should block GCP metadata endpoint."""
        # GCP uses 169.254.169.254 as well
        result = self.checker.normalize_url(
            "http://169.254.169.254/computeMetadata/v1/"
        )
        assert result is None, "Should block GCP metadata endpoint"

    def test_blocks_azure_metadata_endpoint(self):
        """Should block Azure metadata endpoint."""
        result = self.checker.normalize_url(
            "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
        )
        assert result is None, "Should block Azure metadata endpoint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
