#!/usr/bin/env python3
"""
API Usage Examples for Website Status Checker

This file contains comprehensive examples showing how to use the
Website Status Checker programmatically in your Python applications.
"""

import asyncio
import pandas as pd
import json
import time
from pathlib import Path
import logging

# Import the website status checker modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.checker import WebsiteStatusChecker, StatusResult, ErrorCategory
from src.core.batch import BatchProcessor, BatchConfig


async def basic_single_url_check():
    """
    Example 1: Basic single URL checking.
    Shows how to check individual websites.
    """
    print("=== Example 1: Basic Single URL Check ===")
    
    checker = WebsiteStatusChecker()
    
    # Check a single URL
    result = await checker.check_website("https://isrealoyarinde.com")
    
    print(f"URL: {result.url}")
    print(f"Status: {result.status_result.value}")
    print(f"HTTP Code: {result.status_code}")
    print(f"Response Time: {result.response_time:.3f} seconds")
    print(f"Final URL: {result.final_url}")
    
    await checker.close()


async def batch_url_checking():
    """
    Example 2: Batch URL checking.
    Shows how to check multiple URLs concurrently.
    """
    print("\\n=== Example 2: Batch URL Checking ===")
    
    urls = [
        "https://isrealoyarinde.com",
        "https://contentika.com", 
        "https://spinah.com",
        "https://httpstat.us/404",  # Will return 404
        "https://invalid-site-12345.com",  # Will fail
    ]
    
    checker = WebsiteStatusChecker(max_concurrent=10)
    
    print(f"Checking {len(urls)} URLs...")
    
    start_time = time.time()
    results = await checker.check_websites_batch(urls)
    elapsed_time = time.time() - start_time
    
    print(f"\\nResults (completed in {elapsed_time:.2f} seconds):")
    for result in results:
        status_emoji = {
            "active": "✅",
            "inactive": "⚠️",
            "error": "❌",
            "timeout": "⏰",
            "invalid_url": "🔧"
        }.get(result.status_result.value, "❓")
        
        print(f"  {status_emoji} {result.url} - {result.status_result.value} (HTTP {result.status_code})")
    
    await checker.close()


async def error_handling_example():
    """
    Example 3: Comprehensive error handling.
    Shows how to handle different types of errors.
    """
    print("\\n=== Example 3: Error Handling ===")
    
    problematic_urls = [
        "https://isrealoyarinde.com",           # Should work
        "https://httpstat.us/500",              # HTTP error
        "https://httpstat.us/timeout",          # Timeout
        "https://nonexistent-domain-xyz.com",   # DNS error
        "not-a-valid-url",                      # Invalid URL
        "https://expired.badssl.com",           # SSL error
    ]
    
    checker = WebsiteStatusChecker(timeout=5, retry_count=1)
    
    results = await checker.check_websites_batch(problematic_urls)
    
    print("\\nError Analysis:")
    
    # Categorize results
    active_count = 0
    error_categories = {}
    
    for result in results:
        if result.status_result == StatusResult.ACTIVE:
            active_count += 1
            print(f"✅ {result.url} - Working fine")
        else:
            error_type = result.error_category.value if result.error_category else "http_error"
            error_categories[error_type] = error_categories.get(error_type, 0) + 1
            print(f"❌ {result.url} - {error_type}: {result.error_message[:50]}")
    
    print(f"\\nSummary: {active_count}/{len(problematic_urls)} active")
    print("Error distribution:", error_categories)
    
    await checker.close()


async def custom_configuration_example():
    """
    Example 4: Custom configuration options.
    Shows how to customize the checker behavior.
    """
    print("\\n=== Example 4: Custom Configuration ===")
    
    # High-performance configuration
    fast_checker = WebsiteStatusChecker(
        max_concurrent=100,
        timeout=5,
        retry_count=1,
        retry_delay=0.5,
        user_agent="MyApp/1.0 FastChecker"
    )
    
    # Conservative configuration
    reliable_checker = WebsiteStatusChecker(
        max_concurrent=20,
        timeout=30,
        retry_count=3,
        retry_delay=2.0,
        backoff_factor=2.0,
        user_agent="MyApp/1.0 ReliableChecker"
    )
    
    test_urls = ["https://httpstat.us/200?sleep=100"] * 10
    
    # Test fast configuration
    print("Testing fast configuration...")
    start_time = time.time()
    fast_results = await fast_checker.check_websites_batch(test_urls)
    fast_time = time.time() - start_time
    
    # Test reliable configuration  
    print("Testing reliable configuration...")
    start_time = time.time()
    reliable_results = await reliable_checker.check_websites_batch(test_urls)
    reliable_time = time.time() - start_time
    
    print(f"\\nPerformance Comparison:")
    print(f"  Fast config: {fast_time:.2f} seconds")
    print(f"  Reliable config: {reliable_time:.2f} seconds")
    print(f"  Speed difference: {reliable_time/fast_time:.1f}x")
    
    await fast_checker.close()
    await reliable_checker.close()


async def progress_monitoring_example():
    """
    Example 5: Progress monitoring.
    Shows how to monitor progress during long-running operations.
    """
    print("\\n=== Example 5: Progress Monitoring ===")
    
    # Create a larger list of URLs for demonstration
    base_urls = [
        "https://httpstat.us/200",
        "https://httpbin.org/delay/1",
        "https://httpstat.us/404",
        "https://httpstat.us/500"
    ]
    
    # Multiply to create more URLs
    urls = [f"{url}?test={i}" for url in base_urls for i in range(25)]  # 100 URLs
    
    checker = WebsiteStatusChecker(max_concurrent=20)
    
    print(f"Monitoring progress for {len(urls)} URLs...")
    
    # Process in chunks to show progress
    chunk_size = 20
    total_active = 0
    start_time = time.time()
    
    for i in range(0, len(urls), chunk_size):
        chunk_urls = urls[i:i + chunk_size]
        chunk_start = time.time()
        
        results = await checker.check_websites_batch(chunk_urls)
        
        chunk_time = time.time() - chunk_start
        chunk_active = sum(1 for r in results if r.status_result == StatusResult.ACTIVE)
        total_active += chunk_active
        
        processed = i + len(chunk_urls)
        elapsed_total = time.time() - start_time
        
        progress_pct = (processed / len(urls)) * 100
        rate = processed / elapsed_total if elapsed_total > 0 else 0
        eta_seconds = (len(urls) - processed) / rate if rate > 0 else 0
        eta_minutes = eta_seconds / 60
        
        print(f"  Progress: {processed:>3}/{len(urls)} ({progress_pct:>5.1f}%) | "
              f"Active: {total_active:>3} | "
              f"Rate: {rate:>5.1f} URLs/sec | "
              f"ETA: {eta_minutes:>4.1f}min")
    
    total_time = time.time() - start_time
    print(f"\\nCompleted: {total_active}/{len(urls)} active in {total_time:.2f} seconds")
    
    await checker.close()


async def integration_with_pandas():
    """
    Example 6: Integration with pandas DataFrame.
    Shows how to work with pandas DataFrames.
    """
    print("\\n=== Example 6: Pandas Integration ===")
    
    # Create sample business data
    companies_data = {
        'company_name': [
            'Google Inc.',
            'GitHub Inc.',
            'Stack Overflow',
            'Python Foundation',
            'Invalid Company',
            'Timeout Test Co.'
        ],
        'website': [
            'https://google.com',
            'https://github.com',
            'https://stackoverflow.com', 
            'https://python.org',
            'https://invalid-company-xyz.com',
            'https://httpstat.us/200?sleep=5000'
        ],
        'industry': [
            'Technology',
            'Technology', 
            'Technology',
            'Non-profit',
            'Test',
            'Test'
        ]
    }
    
    df = pd.DataFrame(companies_data)
    print(f"Processing {len(df)} companies from DataFrame...")
    
    checker = WebsiteStatusChecker(timeout=3, retry_count=1)
    
    # Extract URLs and check them
    urls = df['website'].tolist()
    results = await checker.check_websites_batch(urls)
    
    # Add results back to DataFrame
    df['website_status'] = [r.status_result.value for r in results]
    df['response_time'] = [r.response_time for r in results]
    df['status_code'] = [r.status_code for r in results]
    df['is_active'] = [r.status_result == StatusResult.ACTIVE for r in results]
    
    print("\\nResults DataFrame:")
    print(df[['company_name', 'website_status', 'status_code', 'response_time']].to_string())
    
    # Filter for active companies
    active_companies = df[df['is_active'] == True]
    print(f"\\nActive companies: {len(active_companies)}/{len(df)}")
    
    # Save results
    output_file = "companies_with_status.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    
    await checker.close()


async def streaming_results_example():
    """
    Example 7: Streaming results as they complete.
    Shows how to process results as they become available.
    """
    print("\\n=== Example 7: Streaming Results ===")
    
    urls = [f"https://httpstat.us/200?sleep={i*200}" for i in range(1, 11)]
    
    checker = WebsiteStatusChecker()
    
    print("Streaming results as they complete...")
    print("(URLs have artificial delays from 200ms to 2000ms)")
    
    async def check_and_report(url, index):
        result = await checker.check_website(url)
        
        status_emoji = "✅" if result.status_result == StatusResult.ACTIVE else "❌"
        print(f"  {status_emoji} [{index:>2}] {url} - {result.response_time:.3f}s")
        
        return result
    
    # Start all checks concurrently
    start_time = time.time()
    tasks = [check_and_report(url, i) for i, url in enumerate(urls, 1)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    active_count = sum(1 for r in results if r.status_result == StatusResult.ACTIVE)
    
    print(f"\\nAll {len(results)} checks completed in {total_time:.2f} seconds")
    print(f"Active websites: {active_count}/{len(results)}")
    
    await checker.close()


async def json_output_example():
    """
    Example 8: JSON output processing.
    Shows how to work with JSON output format.
    """
    print("\\n=== Example 8: JSON Output Processing ===")
    
    urls = [
        "https://google.com",
        "https://github.com",
        "https://invalid-site.com"
    ]
    
    checker = WebsiteStatusChecker()
    results = await checker.check_websites_batch(urls)
    
    # Convert results to JSON-serializable format
    json_results = []
    for result in results:
        json_result = {
            'url': result.url,
            'normalized_url': result.normalized_url,
            'status': result.status_result.value,
            'status_code': result.status_code,
            'error_category': result.error_category.value if result.error_category else None,
            'error_message': result.error_message,
            'response_time': round(result.response_time, 3),
            'timestamp': result.timestamp,
            'retry_count': result.retry_count,
            'final_url': result.final_url
        }
        json_results.append(json_result)
    
    # Save as JSON
    output_file = "api_example_results.json"
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"Results saved to {output_file}")
    print("\\nSample JSON output:")
    print(json.dumps(json_results[0], indent=2))
    
    await checker.close()


async def performance_comparison():
    """
    Example 9: Performance comparison.
    Shows how different configurations affect performance.
    """
    print("\\n=== Example 9: Performance Comparison ===")
    
    test_urls = ["https://httpstat.us/200"] * 50
    
    configurations = [
        ("Low Concurrency", {"max_concurrent": 10, "timeout": 10}),
        ("Medium Concurrency", {"max_concurrent": 25, "timeout": 10}),
        ("High Concurrency", {"max_concurrent": 50, "timeout": 10}),
        ("Fast Timeout", {"max_concurrent": 25, "timeout": 3}),
        ("Slow Timeout", {"max_concurrent": 25, "timeout": 20}),
    ]
    
    print(f"Testing {len(test_urls)} URLs with different configurations:")
    
    results_summary = []
    
    for config_name, config_params in configurations:
        checker = WebsiteStatusChecker(**config_params)
        
        start_time = time.time()
        results = await checker.check_websites_batch(test_urls)
        elapsed_time = time.time() - start_time
        
        active_count = sum(1 for r in results if r.status_result == StatusResult.ACTIVE)
        rate = len(test_urls) / elapsed_time
        
        results_summary.append({
            'configuration': config_name,
            'time': elapsed_time,
            'rate': rate,
            'active': active_count,
            'params': config_params
        })
        
        print(f"  {config_name:>18}: {elapsed_time:>6.2f}s ({rate:>6.1f} URLs/sec) - {active_count} active")
        
        await checker.close()
    
    # Find best performer
    fastest = min(results_summary, key=lambda x: x['time'])
    print(f"\\nFastest configuration: {fastest['configuration']} ({fastest['time']:.2f}s)")


async def large_scale_simulation():
    """
    Example 10: Large-scale processing simulation.
    Simulates processing a large dataset efficiently.
    """
    print("\\n=== Example 10: Large-Scale Processing Simulation ===")
    
    # Simulate a large dataset
    base_domains = [
        "httpstat.us", "httpbin.org", "example.com", 
        "google.com", "github.com"
    ]
    
    # Create 500 URLs for simulation
    simulated_urls = []
    for domain in base_domains:
        for i in range(100):
            simulated_urls.append(f"https://{domain}?test={i}")
    
    print(f"Simulating processing of {len(simulated_urls)} URLs...")
    
    # Use batch processor for large-scale processing
    config = BatchConfig(
        batch_size=50,
        max_concurrent=30,
        timeout=5,
        retry_count=1,
        include_inactive=True,
        save_interval=5
    )
    
    processor = BatchProcessor(config)
    
    # Create DataFrame and process
    df = pd.DataFrame({'url': simulated_urls})
    
    start_time = time.time()
    stats = await processor.process_dataframe(
        df=df,
        output_file=Path("large_scale_simulation.csv"),
        url_column="url"
    )
    
    processing_time = time.time() - start_time
    
    print(f"\\nLarge-Scale Processing Results:")
    print(f"  Total URLs processed: {stats.total_input_urls:,}")
    print(f"  Active websites: {stats.active_websites:,}")
    print(f"  Inactive websites: {stats.inactive_websites:,}")
    print(f"  Error websites: {stats.error_websites:,}")
    print(f"  Success rate: {stats.success_rate:.2f}%")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Processing rate: {stats.processing_rate:.2f} URLs/second")
    print(f"  Results saved to: large_scale_simulation.csv")


async def main():
    """
    Run all API usage examples.
    """
    print("Website Status Checker - API Usage Examples")
    print("=" * 60)
    
    # Setup basic logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    examples = [
        basic_single_url_check,
        batch_url_checking,
        error_handling_example,
        custom_configuration_example,
        progress_monitoring_example,
        integration_with_pandas,
        streaming_results_example,
        json_output_example,
        performance_comparison,
        large_scale_simulation
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
        except Exception as e:
            print(f"\\n❌ Example {i} failed: {e}")
        
        if i < len(examples):
            print("\\n" + "-" * 60)
    
    print("\\n" + "=" * 60)
    print("All API examples completed!")
    print("\\nGenerated files:")
    print("  - companies_with_status.csv")
    print("  - api_example_results.json")
    print("  - large_scale_simulation.csv")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()