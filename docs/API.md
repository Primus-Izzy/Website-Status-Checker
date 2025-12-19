# API Documentation

Complete reference for using Website Status Checker programmatically in your Python applications.

## Core Classes

### WebsiteStatusChecker

The main class for checking website status with concurrent processing and error handling.

#### Constructor

```python
WebsiteStatusChecker(
    max_concurrent: int = 100,
    timeout: int = 10,
    retry_count: int = 2,
    retry_delay: float = 1.0,
    backoff_factor: float = 1.5,
    respect_robots: bool = False,
    user_agent: str = None
)
```

**Parameters:**
- `max_concurrent`: Maximum number of concurrent HTTP requests
- `timeout`: Request timeout in seconds
- `retry_count`: Number of retry attempts for failed requests
- `retry_delay`: Initial delay between retries in seconds
- `backoff_factor`: Exponential backoff multiplier for retries
- `respect_robots`: Whether to respect robots.txt (reserved for future use)
- `user_agent`: Custom user agent string

#### Methods

##### `check_website(url: str) -> CheckResult`

Check a single website's status.

```python
import asyncio
from src.website_status_checker import WebsiteStatusChecker

async def check_single():
    checker = WebsiteStatusChecker()
    
    result = await checker.check_website("https://isrealoyarinde.com")
    
    print(f"Status: {result.status_result}")
    print(f"Status Code: {result.status_code}")
    print(f"Response Time: {result.response_time:.2f}s")
    
    await checker.close()

asyncio.run(check_single())
```

##### `check_websites_batch(urls: List[str]) -> List[CheckResult]`

Check multiple websites concurrently.

```python
import asyncio
from src.website_status_checker import WebsiteStatusChecker

async def check_multiple():
    urls = [
        "https://isrealoyarinde.com",
        "https://contentika.com", 
        "https://spinah.com",
        "https://invalid-site-12345.com"
    ]
    
    checker = WebsiteStatusChecker(max_concurrent=50)
    results = await checker.check_websites_batch(urls)
    
    for result in results:
        print(f"{result.url}: {result.status_result}")
    
    await checker.close()

asyncio.run(check_multiple())
```

##### `get_stats() -> CheckerStats`

Get current processing statistics.

```python
stats = checker.get_stats()
print(f"Total checked: {stats.total_checked}")
print(f"Success rate: {stats.success_rate:.2f}%")
print(f"Processing rate: {stats.checks_per_second:.2f} URLs/sec")
```

### BatchProcessor

High-level processor for handling large datasets with batch processing.

#### Constructor

```python
BatchProcessor(config: BatchConfig)
```

#### Methods

##### `process_file(input_file: Path, output_file: Path, url_column: str) -> ProcessingStats`

Process an entire file with automatic batch handling.

```python
import asyncio
from pathlib import Path
from src.batch_processor import BatchProcessor, BatchConfig

async def process_large_file():
    config = BatchConfig(
        batch_size=1000,
        max_concurrent=100,
        timeout=10,
        include_inactive=True
    )
    
    processor = BatchProcessor(config)
    
    stats = await processor.process_file(
        input_file=Path("websites.csv"),
        output_file=Path("results.csv"),
        url_column="url"
    )
    
    print(f"Processed: {stats.total_input_urls}")
    print(f"Active: {stats.active_websites}")
    print(f"Success Rate: {stats.success_rate:.2f}%")

asyncio.run(process_large_file())
```

##### `process_dataframe(df: pd.DataFrame, output_file: Path, url_column: str) -> ProcessingStats`

Process a pandas DataFrame directly.

```python
import asyncio
import pandas as pd
from pathlib import Path
from src.batch_processor import BatchProcessor, BatchConfig

async def process_dataframe():
    # Create sample DataFrame
    df = pd.DataFrame({
        'company': ['Google', 'GitHub', 'Stack Overflow'],
        'website': ['https://google.com', 'https://github.com', 'https://stackoverflow.com']
    })
    
    config = BatchConfig(batch_size=100, max_concurrent=50)
    processor = BatchProcessor(config)
    
    stats = await processor.process_dataframe(
        df=df,
        output_file=Path("dataframe_results.csv"),
        url_column="website"
    )
    
    print(f"Processed {stats.total_input_urls} URLs from DataFrame")

asyncio.run(process_dataframe())
```

## Data Models

### CheckResult

Represents the result of checking a single website.

```python
@dataclass
class CheckResult:
    url: str                           # Original URL
    normalized_url: str                # Cleaned/standardized URL
    status_result: StatusResult        # active, inactive, error, timeout, invalid_url
    status_code: int                   # HTTP status code (200, 404, etc.)
    error_category: Optional[ErrorCategory]  # Type of error if failed
    error_message: str                 # Detailed error message
    response_time: float              # Time taken to check (seconds)
    timestamp: float                  # When the check occurred
    retry_count: int                  # Number of retries attempted
    final_url: str                    # URL after following redirects
```

### StatusResult Enum

```python
class StatusResult(Enum):
    ACTIVE = "active"           # Website returns HTTP 200
    INACTIVE = "inactive"       # Website returns non-200 HTTP
    ERROR = "error"            # Connection/DNS/SSL error
    TIMEOUT = "timeout"        # Request timed out
    INVALID_URL = "invalid_url" # URL format is invalid
```

### ErrorCategory Enum

```python
class ErrorCategory(Enum):
    DNS_ERROR = "dns_error"                    # DNS resolution failed
    CONNECTION_ERROR = "connection_error"      # Cannot connect to server
    SSL_ERROR = "ssl_error"                    # SSL/TLS certificate issues
    TIMEOUT_ERROR = "timeout_error"            # Request timed out
    HTTP_ERROR = "http_error"                  # HTTP-level errors
    INVALID_URL_ERROR = "invalid_url_error"    # URL format invalid
    UNKNOWN_ERROR = "unknown_error"            # Unknown error occurred
```

### BatchConfig

Configuration for batch processing.

```python
@dataclass
class BatchConfig:
    batch_size: int = 1000              # URLs per batch
    max_concurrent: int = 100           # Max concurrent requests
    timeout: int = 10                   # Request timeout seconds
    retry_count: int = 2                # Number of retries
    save_interval: int = 10             # Save every N batches
    resume_on_failure: bool = True      # Resume capability
    output_format: str = 'csv'          # Output format
    include_inactive: bool = True       # Include inactive sites
    include_errors: bool = False        # Include error sites
    memory_efficient: bool = True       # Memory optimization
```

### ProcessingStats

Statistics from batch processing.

```python
@dataclass
class ProcessingStats:
    total_input_urls: int = 0           # Total URLs to process
    batches_processed: int = 0          # Batches completed
    total_batches: int = 0              # Total number of batches
    active_websites: int = 0            # Active websites found
    inactive_websites: int = 0          # Inactive websites found
    error_websites: int = 0             # Error websites encountered
    processing_rate: float = 0.0        # URLs per second
    estimated_completion: str = ""       # ETA string
    elapsed_time: float = 0.0           # Total processing time
    
    @property
    def completion_percentage(self) -> float  # Progress percentage
    
    @property
    def success_rate(self) -> float           # Active website percentage
```

## Advanced Usage Examples

### Custom Configuration

```python
import asyncio
from src.website_status_checker import WebsiteStatusChecker

async def custom_configuration():
    # High-performance configuration
    checker = WebsiteStatusChecker(
        max_concurrent=300,
        timeout=5,
        retry_count=1,
        retry_delay=0.5,
        backoff_factor=2.0,
        user_agent="MyApp/1.0 Website Checker"
    )
    
    urls = ["https://example.com"] * 1000  # 1000 URLs
    
    results = await checker.check_websites_batch(urls)
    
    # Process results
    active_count = sum(1 for r in results if r.status_result.value == "active")
    print(f"Active websites: {active_count}/{len(results)}")
    
    await checker.close()

asyncio.run(custom_configuration())
```

### Error Handling

```python
import asyncio
from src.website_status_checker import WebsiteStatusChecker, StatusResult, ErrorCategory

async def error_handling_example():
    checker = WebsiteStatusChecker()
    
    urls = [
        "https://google.com",           # Should work
        "https://invalid-site-xyz.com", # DNS error
        "https://httpstat.us/404",      # HTTP error
        "not-a-url"                     # Invalid URL
    ]
    
    results = await checker.check_websites_batch(urls)
    
    for result in results:
        if result.status_result == StatusResult.ACTIVE:
            print(f"✅ {result.url} is active (HTTP {result.status_code})")
        elif result.status_result == StatusResult.ERROR:
            print(f"❌ {result.url} failed: {result.error_category.value} - {result.error_message}")
        elif result.status_result == StatusResult.TIMEOUT:
            print(f"⏰ {result.url} timed out after {result.response_time:.2f}s")
        elif result.status_result == StatusResult.INVALID_URL:
            print(f"🔧 {result.url} has invalid URL format")
    
    await checker.close()

asyncio.run(error_handling_example())
```

### Progress Monitoring

```python
import asyncio
import time
from src.website_status_checker import WebsiteStatusChecker

async def progress_monitoring():
    checker = WebsiteStatusChecker(max_concurrent=100)
    
    # Large list of URLs
    urls = [f"https://example.com?test={i}" for i in range(5000)]
    
    print(f"Starting check of {len(urls)} URLs...")
    start_time = time.time()
    
    # Process in chunks with progress updates
    chunk_size = 1000
    total_active = 0
    
    for i in range(0, len(urls), chunk_size):
        chunk_urls = urls[i:i+chunk_size]
        
        chunk_results = await checker.check_websites_batch(chunk_urls)
        chunk_active = sum(1 for r in chunk_results if r.status_result.value == "active")
        total_active += chunk_active
        
        elapsed = time.time() - start_time
        processed = i + len(chunk_urls)
        rate = processed / elapsed
        
        print(f"Progress: {processed}/{len(urls)} ({processed/len(urls)*100:.1f}%) "
              f"Active: {total_active} Rate: {rate:.1f} URLs/sec")
    
    await checker.close()

asyncio.run(progress_monitoring())
```

### Integration with Web Framework (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
from src.website_status_checker import WebsiteStatusChecker

app = FastAPI()
checker = WebsiteStatusChecker()

class URLRequest(BaseModel):
    urls: List[str]

class URLResult(BaseModel):
    url: str
    status: str
    status_code: int
    response_time: float
    error_message: str

@app.post("/check-urls", response_model=List[URLResult])
async def check_urls(request: URLRequest):
    """Check multiple URLs and return their status."""
    
    if len(request.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs per request")
    
    try:
        results = await checker.check_websites_batch(request.urls)
        
        return [
            URLResult(
                url=result.url,
                status=result.status_result.value,
                status_code=result.status_code,
                response_time=result.response_time,
                error_message=result.error_message
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    await checker.close()
```

### Integration with Celery

```python
from celery import Celery
import asyncio
from src.website_status_checker import WebsiteStatusChecker

app = Celery('website_checker')

@app.task
def check_websites_task(urls):
    """Celery task for checking websites asynchronously."""
    
    async def check_async():
        checker = WebsiteStatusChecker()
        results = await checker.check_websites_batch(urls)
        await checker.close()
        
        return [
            {
                'url': result.url,
                'status': result.status_result.value,
                'status_code': result.status_code,
                'response_time': result.response_time
            }
            for result in results
        ]
    
    return asyncio.run(check_async())

# Usage
# result = check_websites_task.delay(['https://example.com', 'https://google.com'])
# print(result.get())
```

### Streaming Results

```python
import asyncio
import json
from src.website_status_checker import WebsiteStatusChecker

async def streaming_results():
    """Process URLs and stream results as they complete."""
    
    checker = WebsiteStatusChecker()
    
    urls = [f"https://httpstat.us/200?sleep={i*100}" for i in range(10)]
    
    # Create semaphore for controlled concurrency
    semaphore = asyncio.Semaphore(5)
    
    async def check_and_stream(url):
        async with semaphore:
            result = await checker.check_website(url)
            
            # Stream result immediately
            result_data = {
                'url': result.url,
                'status': result.status_result.value,
                'timestamp': result.timestamp,
                'response_time': result.response_time
            }
            
            print(f"RESULT: {json.dumps(result_data)}")
            return result
    
    # Process all URLs concurrently but stream results as they complete
    tasks = [check_and_stream(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    print(f"\\nCompleted {len(results)} checks")
    await checker.close()

asyncio.run(streaming_results())
```

### Custom Output Processors

```python
import asyncio
from dataclasses import asdict
from src.batch_processor import BatchProcessor, BatchConfig
from pathlib import Path

class CustomOutputProcessor(BatchProcessor):
    """Custom processor with specialized output handling."""
    
    def save_results_batch(self, results, output_file, append=True):
        """Override to implement custom output format."""
        
        # Filter for only active websites
        active_results = [r for r in results if r.status_result.value == "active"]
        
        if not active_results:
            return
        
        # Custom CSV format with only essential columns
        import csv
        
        mode = 'a' if append and output_file.exists() else 'w'
        
        with open(output_file, mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not append or not output_file.exists():
                writer.writerow(['url', 'final_url', 'response_time', 'timestamp'])
            
            for result in active_results:
                writer.writerow([
                    result.url,
                    result.final_url,
                    f"{result.response_time:.3f}",
                    int(result.timestamp)
                ])

async def custom_processing():
    config = BatchConfig(batch_size=500, include_inactive=False)
    processor = CustomOutputProcessor(config)
    
    await processor.process_file(
        input_file=Path("websites.csv"),
        output_file=Path("active_only.csv"),
        url_column="url"
    )

asyncio.run(custom_processing())
```

## Performance Considerations

### Memory Usage

For large datasets, use memory-efficient processing:

```python
# Memory-efficient configuration
config = BatchConfig(
    batch_size=500,           # Smaller batches
    memory_efficient=True,    # Stream processing
    save_interval=5           # Save frequently
)
```

### Concurrency Tuning

Optimize concurrent requests based on your system:

```python
# Conservative (good for slower systems)
checker = WebsiteStatusChecker(max_concurrent=50, timeout=20)

# Aggressive (for fast systems with good network)
checker = WebsiteStatusChecker(max_concurrent=500, timeout=5)

# Balanced (recommended starting point)
checker = WebsiteStatusChecker(max_concurrent=100, timeout=10)
```

### Error Recovery

Implement robust error recovery:

```python
async def robust_checking():
    checker = WebsiteStatusChecker(
        retry_count=3,
        retry_delay=2.0,
        backoff_factor=2.0
    )
    
    try:
        results = await checker.check_websites_batch(urls)
    except Exception as e:
        print(f"Batch failed: {e}")
        # Implement fallback logic
    finally:
        await checker.close()
```

## Testing

### Unit Testing Example

```python
import pytest
import asyncio
from src.website_status_checker import WebsiteStatusChecker, StatusResult

@pytest.mark.asyncio
async def test_check_valid_website():
    checker = WebsiteStatusChecker()
    
    result = await checker.check_website("https://httpbin.org/status/200")
    
    assert result.status_result == StatusResult.ACTIVE
    assert result.status_code == 200
    assert result.response_time > 0
    
    await checker.close()

@pytest.mark.asyncio
async def test_check_invalid_website():
    checker = WebsiteStatusChecker()
    
    result = await checker.check_website("https://this-domain-does-not-exist-12345.com")
    
    assert result.status_result == StatusResult.ERROR
    assert "dns_error" in str(result.error_category).lower()
    
    await checker.close()
```

This API documentation covers the core functionality. For more examples and advanced usage patterns, check the `examples/` directory in the repository.