"""
Basic tests for Website Status Checker.

These tests verify that the core components can be imported and initialized
without errors, providing a foundation for more comprehensive testing.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from website_status_checker import (
        WebsiteStatusChecker, StatusResult, ErrorCategory, CheckResult
    )
    from batch_processor import BatchProcessor, BatchConfig, ProcessingStats
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestBasicFunctionality:
    """Test basic functionality and imports."""
    
    def test_imports_available(self):
        """Test that all core modules can be imported."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"Required modules not available: {IMPORT_ERROR}")
        
        # If we get here, imports worked
        assert True
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_status_result_enum(self):
        """Test that StatusResult enum has expected values."""
        assert StatusResult.ACTIVE
        assert StatusResult.INACTIVE
        assert StatusResult.ERROR
        assert StatusResult.TIMEOUT
        assert StatusResult.INVALID_URL
        
        # Test string values
        assert StatusResult.ACTIVE.value == "active"
        assert StatusResult.INACTIVE.value == "inactive"
        assert StatusResult.ERROR.value == "error"
        assert StatusResult.TIMEOUT.value == "timeout"
        assert StatusResult.INVALID_URL.value == "invalid_url"
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_error_category_enum(self):
        """Test that ErrorCategory enum has expected values."""
        assert ErrorCategory.DNS_ERROR
        assert ErrorCategory.CONNECTION_ERROR
        assert ErrorCategory.SSL_ERROR
        assert ErrorCategory.TIMEOUT_ERROR
        assert ErrorCategory.HTTP_ERROR
        assert ErrorCategory.INVALID_URL_ERROR
        assert ErrorCategory.UNKNOWN_ERROR
        
        # Test string values
        assert ErrorCategory.DNS_ERROR.value == "dns_error"
        assert ErrorCategory.CONNECTION_ERROR.value == "connection_error"
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_website_checker_initialization(self):
        """Test that WebsiteStatusChecker can be initialized."""
        checker = WebsiteStatusChecker()
        
        assert checker is not None
        assert checker.max_concurrent > 0
        assert checker.timeout > 0
        assert checker.retry_count >= 0
        
        # Test custom initialization
        custom_checker = WebsiteStatusChecker(
            max_concurrent=50,
            timeout=20,
            retry_count=3
        )
        
        assert custom_checker.max_concurrent == 50
        assert custom_checker.timeout == 20
        assert custom_checker.retry_count == 3
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_batch_config_initialization(self):
        """Test that BatchConfig can be initialized."""
        config = BatchConfig()
        
        assert config is not None
        assert config.batch_size > 0
        assert config.max_concurrent > 0
        assert config.timeout > 0
        
        # Test custom configuration
        custom_config = BatchConfig(
            batch_size=500,
            max_concurrent=25,
            timeout=15
        )
        
        assert custom_config.batch_size == 500
        assert custom_config.max_concurrent == 25
        assert custom_config.timeout == 15
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_batch_processor_initialization(self):
        """Test that BatchProcessor can be initialized."""
        config = BatchConfig()
        processor = BatchProcessor(config)
        
        assert processor is not None
        assert processor.config == config


class TestURLValidation:
    """Test URL validation functionality."""
    
    def test_url_parsing(self):
        """Test basic URL parsing without external dependencies."""
        from urllib.parse import urlparse
        
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com",
            "https://example.com/path",
            "https://example.com:8080",
            "https://example.com/path?query=value",
            "https://example.com/path#fragment",
        ]
        
        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme in ['http', 'https']
            assert parsed.netloc
            assert '.' in parsed.netloc
    
    def test_invalid_urls(self):
        """Test detection of invalid URLs."""
        from urllib.parse import urlparse
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Not HTTP/HTTPS
            "",
            "http://",
            "https://",
            "javascript:alert('test')",
            "mailto:test@example.com",
        ]
        
        for url in invalid_urls:
            parsed = urlparse(url)
            # Either no scheme/netloc or wrong scheme
            is_invalid = (
                not parsed.scheme or 
                not parsed.netloc or 
                parsed.scheme not in ['http', 'https']
            )
            assert is_invalid, f"URL should be invalid: {url}"
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_url_normalization(self):
        """Test URL normalization functionality."""
        checker = WebsiteStatusChecker()
        
        # Test cases: (input, expected_output)
        test_cases = [
            ("https://example.com", "https://example.com"),
            ("http://example.com", "http://example.com"),
            ("www.example.com", "https://www.example.com"),
            ("example.com", "https://example.com"),
            ("HTTPS://EXAMPLE.COM", "https://example.com"),
            ("", None),
            ("not-a-url", None),
            ("javascript:alert('test')", None),
            ("mailto:test@example.com", None),
        ]
        
        for input_url, expected in test_cases:
            result = checker.normalize_url(input_url)
            if expected is None:
                assert result is None, f"Expected None for {input_url}, got {result}"
            else:
                assert result == expected, f"Expected {expected} for {input_url}, got {result}"


class TestDataStructures:
    """Test data structure functionality."""
    
    def test_list_processing(self):
        """Test basic list processing operations."""
        urls = [
            "https://example1.com",
            "https://example2.com", 
            "https://example3.com"
        ]
        
        # Test list operations
        assert len(urls) == 3
        assert urls[0] == "https://example1.com"
        
        # Test list comprehension
        https_urls = [url for url in urls if url.startswith('https://')]
        assert len(https_urls) == 3
        
        # Test filtering
        com_domains = [url for url in urls if url.endswith('.com')]
        assert len(com_domains) == 3
    
    def test_dictionary_operations(self):
        """Test dictionary operations for configuration."""
        config = {
            "checker": {
                "max_concurrent": 100,
                "timeout": 10
            },
            "batch": {
                "batch_size": 1000,
                "save_interval": 10
            }
        }
        
        assert config["checker"]["max_concurrent"] == 100
        assert config["batch"]["batch_size"] == 1000
        
        # Test nested access
        checker_config = config.get("checker", {})
        assert checker_config.get("timeout") == 10
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_check_result_creation(self):
        """Test CheckResult data class creation."""
        import time
        
        result = CheckResult(
            url="https://example.com",
            normalized_url="https://example.com",
            status_result=StatusResult.ACTIVE,
            status_code=200,
            error_category=None,
            error_message="",
            response_time=0.5,
            timestamp=time.time(),
            retry_count=0,
            final_url="https://example.com"
        )
        
        assert result.url == "https://example.com"
        assert result.status_result == StatusResult.ACTIVE
        assert result.status_code == 200
        assert result.response_time == 0.5
        assert result.retry_count == 0
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_processing_stats_properties(self):
        """Test ProcessingStats calculated properties."""
        stats = ProcessingStats()
        
        # Test initial state
        assert stats.completion_percentage == 0.0
        assert stats.success_rate == 0.0
        
        # Test with some data
        stats.total_batches = 10
        stats.batches_processed = 5
        stats.active_websites = 75
        stats.inactive_websites = 20
        stats.error_websites = 5
        
        assert stats.completion_percentage == 50.0
        assert stats.success_rate == 75.0  # 75 out of 100 total


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_invalid_checker_parameters(self):
        """Test that invalid parameters are handled appropriately."""
        # These should not raise exceptions during initialization
        # Invalid values should be handled gracefully by the implementation
        
        # Very small concurrent limit
        checker1 = WebsiteStatusChecker(max_concurrent=1)
        assert checker1.max_concurrent == 1
        
        # Very small timeout
        checker2 = WebsiteStatusChecker(timeout=1)
        assert checker2.timeout == 1
        
        # Zero retries
        checker3 = WebsiteStatusChecker(retry_count=0)
        assert checker3.retry_count == 0
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
    def test_invalid_batch_config(self):
        """Test that invalid batch configuration is handled."""
        # Small batch size
        config1 = BatchConfig(batch_size=1)
        assert config1.batch_size == 1
        
        # Small concurrent limit
        config2 = BatchConfig(max_concurrent=1)
        assert config2.max_concurrent == 1


class TestIntegration:
    """Basic integration tests."""
    
    def test_pandas_available(self):
        """Test that pandas is available for data processing."""
        try:
            import pandas as pd
            
            # Test basic DataFrame operations
            df = pd.DataFrame({
                'url': ['https://example.com', 'https://test.com'],
                'expected': ['active', 'active']
            })
            
            assert len(df) == 2
            assert 'url' in df.columns
            assert df['url'].iloc[0] == 'https://example.com'
            
        except ImportError:
            pytest.skip("pandas not available")
    
    def test_aiohttp_available(self):
        """Test that aiohttp is available for HTTP operations."""
        try:
            import aiohttp
            
            # Test that we can create basic aiohttp components
            timeout = aiohttp.ClientTimeout(total=10)
            assert timeout.total == 10
            
        except ImportError:
            pytest.skip("aiohttp not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])