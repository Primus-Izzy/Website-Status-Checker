#!/usr/bin/env python3
"""
Website Status Checker - Core Module

A high-performance asynchronous website status checker designed for processing
large numbers of URLs efficiently. Uses aiohttp for concurrent HTTP requests
and includes advanced error handling, retry mechanisms, and progress tracking.

Features:
- Concurrent HTTP status checking with configurable limits
- Smart URL normalization and validation  
- Automatic retry logic with exponential backoff
- Progress tracking and resume capability
- Comprehensive error categorization
- Memory-efficient batch processing
- SSL/TLS handling for various certificate issues
- Rate limiting and respectful crawling
"""

import asyncio
import aiohttp
import ssl
import time
import json
import logging
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, asdict

# Import SSRF protection
from src.utils.secrets import validate_url_safety
from enum import Enum
import pandas as pd


class StatusResult(Enum):
    """Enumeration for website status results."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_URL = "invalid_url"


class ErrorCategory(Enum):
    """Enumeration for error categories."""
    DNS_ERROR = "dns_error"
    CONNECTION_ERROR = "connection_error"
    SSL_ERROR = "ssl_error"
    TIMEOUT_ERROR = "timeout_error"
    HTTP_ERROR = "http_error"
    INVALID_URL_ERROR = "invalid_url_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class CheckResult:
    """Data class representing the result of checking a single website."""
    url: str
    normalized_url: str
    status_result: StatusResult
    status_code: int
    error_category: Optional[ErrorCategory]
    error_message: str
    response_time: float
    timestamp: float
    retry_count: int
    final_url: str  # URL after redirects


@dataclass
class CheckerStats:
    """Data class for tracking checker statistics."""
    total_checked: int = 0
    active_found: int = 0
    inactive_found: int = 0
    errors: int = 0
    timeouts: int = 0
    invalid_urls: int = 0
    start_time: float = 0
    total_time: float = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_checked == 0:
            return 0.0
        return (self.active_found / self.total_checked) * 100
    
    @property
    def checks_per_second(self) -> float:
        """Calculate checks per second."""
        if self.total_time == 0:
            return 0.0
        return self.total_checked / self.total_time


class WebsiteStatusChecker:
    """
    High-performance asynchronous website status checker.
    
    This class provides concurrent HTTP status checking capabilities with
    comprehensive error handling, retry logic, and progress tracking.
    """
    
    def __init__(
        self,
        max_concurrent: int = 100,
        timeout: int = 10,
        retry_count: int = 2,
        retry_delay: float = 1.0,
        backoff_factor: float = 1.5,
        respect_robots: bool = False,
        user_agent: str = None,
        verify_ssl: bool = True
    ):
        """
        Initialize the website status checker.

        Args:
            max_concurrent: Maximum number of concurrent requests
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts for failed requests
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Exponential backoff multiplier for retries
            respect_robots: Whether to respect robots.txt (not implemented)
            user_agent: Custom user agent string
            verify_ssl: Whether to verify SSL certificates (default: True)
                       WARNING: Disabling SSL verification is a security risk and
                       should only be used for testing or compatibility with legacy systems.
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.respect_robots = respect_robots
        self.verify_ssl = verify_ssl
        
        # Default user agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WebsiteStatusChecker/1.0"
        )
        
        # Session and SSL context
        self.session: Optional[aiohttp.ClientSession] = None
        self.ssl_context = self._create_ssl_context()

        # Statistics tracking
        self.stats = CheckerStats(start_time=time.time())

        # Progress tracking
        self.progress_file = "website_check_progress.json"
        self.checked_urls: Set[str] = set()

        # Logging
        self.logger = logging.getLogger(__name__)

        # Warn if SSL verification is disabled
        if not self.verify_ssl:
            self.logger.warning(
                "⚠️  SSL CERTIFICATE VERIFICATION DISABLED - This is a SECURITY RISK! "
                "Only use this for testing or with legacy systems. "
                "Man-in-the-middle attacks are possible."
            )
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context based on verify_ssl setting.

        Returns:
            SSL context configured for secure or permissive operation
        """
        if self.verify_ssl:
            # Secure default: verify certificates
            return ssl.create_default_context()
        else:
            # Permissive context for legacy sites (SECURITY RISK!)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            # Allow weak ciphers for compatibility with older sites
            ssl_context.set_ciphers("ALL:@SECLEVEL=0")
            return ssl_context
    
    async def create_session(self) -> None:
        """Create aiohttp session with optimized settings."""
        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=min(5, self.timeout),
            sock_read=self.timeout
        )
        
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=min(10, self.max_concurrent // 10),
            ssl=self.ssl_context,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
            use_dns_cache=True,
            ttl_dns_cache=300,
            family=0  # Support both IPv4 and IPv6
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1'
            },
            raise_for_status=False
        )
    
    def normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize and validate URL.
        
        Args:
            url: Raw URL string to normalize
            
        Returns:
            Normalized URL string or None if invalid
        """
        if not url or pd.isna(url):
            return None
        
        url = str(url).strip()
        
        if not url:
            return None
        
        # Skip obviously invalid entries
        invalid_patterns = [
            'nan', 'null', 'none', 'n/a', 'tbd', 'coming soon', 'under construction',
            'pending', 'private', 'confidential', 'internal', 'localhost',
            'example.com', 'test.com', 'sample.com', 'domain.com'
        ]
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in invalid_patterns):
            return None
        
        # Skip non-HTTP protocols
        if url_lower.startswith(('mailto:', 'tel:', 'ftp:', 'file:', 'javascript:', 'data:')):
            return None
        
        # Handle common URL formats
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            elif '.' in url and len(url.split('.')) >= 2:
                # Check if it looks like a domain
                if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
                    url = 'https://' + url
                else:
                    return None
            else:
                return None
        
        # Basic validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc or '.' not in parsed.netloc:
                return None
            
            # Remove invalid TLDs
            if parsed.netloc.endswith(('.local', '.test', '.invalid', '.localhost')):
                return None
            
            # Check for valid TLD
            tld = parsed.netloc.split('.')[-1].lower()
            if len(tld) < 2 or not tld.isalpha():
                return None
            
            # Reconstruct clean URL
            clean_url = f"{parsed.scheme}://{parsed.netloc.lower()}"
            if parsed.path and parsed.path != '/':
                clean_url += parsed.path

            # SSRF Protection: Validate URL safety
            is_safe, warning = validate_url_safety(clean_url)
            if not is_safe:
                self.logger.warning(f"Blocked unsafe URL '{url}': {warning}")
                return None

            return clean_url

        except (ValueError, AttributeError) as e:
            self.logger.debug(f"URL normalization failed for '{url}': {e}")
            return None
    
    async def check_website(self, url: str) -> CheckResult:
        """
        Check a single website's status with retry logic.
        
        Args:
            url: URL to check
            
        Returns:
            CheckResult object with status information
        """
        start_time = time.time()
        normalized_url = self.normalize_url(url)
        
        if not normalized_url:
            self.stats.invalid_urls += 1
            return CheckResult(
                url=url,
                normalized_url="",
                status_result=StatusResult.INVALID_URL,
                status_code=0,
                error_category=ErrorCategory.INVALID_URL_ERROR,
                error_message="Invalid URL format",
                response_time=0,
                timestamp=start_time,
                retry_count=0,
                final_url=""
            )
        
        # Check if already processed
        if normalized_url in self.checked_urls:
            return CheckResult(
                url=url,
                normalized_url=normalized_url,
                status_result=StatusResult.ERROR,
                status_code=0,
                error_category=ErrorCategory.UNKNOWN_ERROR,
                error_message="Already processed",
                response_time=0,
                timestamp=start_time,
                retry_count=0,
                final_url=""
            )
        
        for attempt in range(self.retry_count + 1):
            try:
                if not self.session:
                    await self.create_session()
                
                async with self.session.get(
                    normalized_url,
                    allow_redirects=True,
                    ssl=self.ssl_context
                ) as response:
                    response_time = time.time() - start_time
                    
                    # Update statistics
                    self.stats.total_checked += 1
                    self.checked_urls.add(normalized_url)
                    
                    if response.status == 200:
                        self.stats.active_found += 1
                        return CheckResult(
                            url=url,
                            normalized_url=normalized_url,
                            status_result=StatusResult.ACTIVE,
                            status_code=response.status,
                            error_category=None,
                            error_message="",
                            response_time=response_time,
                            timestamp=start_time,
                            retry_count=attempt,
                            final_url=str(response.url)
                        )
                    else:
                        self.stats.inactive_found += 1
                        return CheckResult(
                            url=url,
                            normalized_url=normalized_url,
                            status_result=StatusResult.INACTIVE,
                            status_code=response.status,
                            error_category=ErrorCategory.HTTP_ERROR,
                            error_message=f"HTTP {response.status}",
                            response_time=response_time,
                            timestamp=start_time,
                            retry_count=attempt,
                            final_url=str(response.url)
                        )
            
            except asyncio.TimeoutError:
                if attempt == self.retry_count:
                    self.stats.timeouts += 1
                    return CheckResult(
                        url=url,
                        normalized_url=normalized_url,
                        status_result=StatusResult.TIMEOUT,
                        status_code=0,
                        error_category=ErrorCategory.TIMEOUT_ERROR,
                        error_message="Request timeout",
                        response_time=time.time() - start_time,
                        timestamp=start_time,
                        retry_count=attempt,
                        final_url=""
                    )
                await asyncio.sleep(self.retry_delay * (self.backoff_factor ** attempt))
            
            except aiohttp.ClientConnectorError as e:
                if attempt == self.retry_count:
                    self.stats.errors += 1
                    error_category = ErrorCategory.DNS_ERROR if "name or service not known" in str(e).lower() else ErrorCategory.CONNECTION_ERROR
                    return CheckResult(
                        url=url,
                        normalized_url=normalized_url,
                        status_result=StatusResult.ERROR,
                        status_code=0,
                        error_category=error_category,
                        error_message=f"Connection error: {str(e)[:100]}",
                        response_time=time.time() - start_time,
                        timestamp=start_time,
                        retry_count=attempt,
                        final_url=""
                    )
                await asyncio.sleep(self.retry_delay * (self.backoff_factor ** attempt))
            
            except aiohttp.ClientSSLError as e:
                if attempt == self.retry_count:
                    self.stats.errors += 1
                    return CheckResult(
                        url=url,
                        normalized_url=normalized_url,
                        status_result=StatusResult.ERROR,
                        status_code=0,
                        error_category=ErrorCategory.SSL_ERROR,
                        error_message=f"SSL error: {str(e)[:100]}",
                        response_time=time.time() - start_time,
                        timestamp=start_time,
                        retry_count=attempt,
                        final_url=""
                    )
                await asyncio.sleep(self.retry_delay * (self.backoff_factor ** attempt))
            
            except Exception as e:
                if attempt == self.retry_count:
                    self.stats.errors += 1
                    return CheckResult(
                        url=url,
                        normalized_url=normalized_url,
                        status_result=StatusResult.ERROR,
                        status_code=0,
                        error_category=ErrorCategory.UNKNOWN_ERROR,
                        error_message=f"Unknown error: {str(e)[:100]}",
                        response_time=time.time() - start_time,
                        timestamp=start_time,
                        retry_count=attempt,
                        final_url=""
                    )
                await asyncio.sleep(self.retry_delay * (self.backoff_factor ** attempt))
        
        # This should never be reached
        return CheckResult(
            url=url,
            normalized_url=normalized_url,
            status_result=StatusResult.ERROR,
            status_code=0,
            error_category=ErrorCategory.UNKNOWN_ERROR,
            error_message="Max retries exceeded",
            response_time=time.time() - start_time,
            timestamp=start_time,
            retry_count=self.retry_count,
            final_url=""
        )
    
    async def check_websites_batch(self, urls: List[str]) -> List[CheckResult]:
        """
        Check multiple websites concurrently.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            List of CheckResult objects
        """
        if not self.session:
            await self.create_session()
        
        # Create semaphore for controlling concurrency
        semaphore = asyncio.Semaphore(min(self.max_concurrent, len(urls)))
        
        async def check_with_semaphore(url: str) -> CheckResult:
            async with semaphore:
                return await self.check_website(url)
        
        # Execute all checks concurrently
        tasks = [check_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(CheckResult(
                    url=urls[i],
                    normalized_url="",
                    status_result=StatusResult.ERROR,
                    status_code=0,
                    error_category=ErrorCategory.UNKNOWN_ERROR,
                    error_message=f"Exception: {str(result)[:100]}",
                    response_time=0,
                    timestamp=time.time(),
                    retry_count=0,
                    final_url=""
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def save_progress(self, processed_batches: List[str], current_batch: str = None) -> None:
        """Save progress to file for resume capability."""
        progress = {
            'processed_batches': processed_batches,
            'current_batch': current_batch,
            'stats': asdict(self.stats),
            'checked_urls_count': len(self.checked_urls),
            'timestamp': time.time()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except (IOError, OSError, json.JSONEncodeError) as e:
            self.logger.error(f"Could not save progress to {self.progress_file}: {e}")
            self.logger.debug(f"Progress data: {progress}", exc_info=True)
    
    def load_progress(self) -> Tuple[List[str], Optional[str]]:
        """Load progress from file."""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                return progress.get('processed_batches', []), progress.get('current_batch')
        except FileNotFoundError:
            self.logger.debug(f"Progress file not found: {self.progress_file}")
            return [], None
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Could not load progress from {self.progress_file}: {e}")
            self.logger.warning("Starting fresh without resume data")
            return [], None
    
    def get_stats(self) -> CheckerStats:
        """Get current statistics."""
        self.stats.total_time = time.time() - self.stats.start_time
        return self.stats
    
    def print_stats(self) -> None:
        """Print current statistics."""
        stats = self.get_stats()
        self.logger.info(
            f"Stats: {stats.total_checked} checked, "
            f"{stats.active_found} active ({stats.success_rate:.1f}%), "
            f"{stats.checks_per_second:.1f} checks/sec, "
            f"Runtime: {stats.total_time/60:.1f}min"
        )
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None