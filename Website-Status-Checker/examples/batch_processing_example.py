#!/usr/bin/env python3
"""
Batch Processing Example for Website Status Checker

This example demonstrates how to process large datasets efficiently
using the Website Status Checker with various configuration options.
"""

import asyncio
import pandas as pd
import time
from pathlib import Path
import logging

# Import the website status checker modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from batch_processor import BatchProcessor, BatchConfig
from website_status_checker import WebsiteStatusChecker


async def basic_batch_processing():
    """
    Basic batch processing example.
    Demonstrates simple processing of a CSV file.
    """
    print("=== Basic Batch Processing Example ===")
    
    # Create a simple configuration
    config = BatchConfig(
        batch_size=50,
        max_concurrent=20,
        timeout=10,
        include_inactive=True
    )
    
    # Create processor
    processor = BatchProcessor(config)
    
    # Process the sample file
    input_file = Path("sample_websites.csv")
    output_file = Path("basic_results.csv")
    
    if not input_file.exists():
        print(f"Sample file {input_file} not found. Please run this from the examples/ directory.")
        return
    
    print(f"Processing {input_file} -> {output_file}")
    
    start_time = time.time()
    stats = await processor.process_file(
        input_file=input_file,
        output_file=output_file,
        url_column="url"
    )
    
    processing_time = time.time() - start_time
    
    print(f"\\nResults:")
    print(f"  Total URLs: {stats.total_input_urls}")
    print(f"  Active websites: {stats.active_websites} ({stats.success_rate:.1f}%)")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Rate: {stats.processing_rate:.2f} URLs/second")


async def high_performance_processing():
    """
    High-performance processing example.
    Optimized for speed with large concurrent requests.
    """
    print("\\n=== High-Performance Processing Example ===")
    
    # High-performance configuration
    config = BatchConfig(
        batch_size=500,           # Large batches
        max_concurrent=100,       # High concurrency
        timeout=5,               # Fast timeout
        retry_count=1,           # Fewer retries for speed
        save_interval=2,         # Save frequently
        include_inactive=False   # Only active websites
    )
    
    processor = BatchProcessor(config)
    
    input_file = Path("sample_websites.csv")
    output_file = Path("high_performance_results.csv")
    
    print(f"High-performance processing: {input_file} -> {output_file}")
    
    start_time = time.time()
    stats = await processor.process_file(
        input_file=input_file,
        output_file=output_file,
        url_column="url"
    )
    
    processing_time = time.time() - start_time
    
    print(f"\\nResults:")
    print(f"  Active websites: {stats.active_websites}")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Rate: {stats.processing_rate:.2f} URLs/second")


async def comprehensive_processing():
    """
    Comprehensive processing example.
    Includes all types of results with detailed error handling.
    """
    print("\\n=== Comprehensive Processing Example ===")
    
    # Comprehensive configuration
    config = BatchConfig(
        batch_size=100,
        max_concurrent=50,
        timeout=15,              # Longer timeout for reliability
        retry_count=3,           # More retries
        include_inactive=True,   # Include inactive sites
        include_errors=True,     # Include error sites
        output_format='json'     # JSON output for detailed data
    )
    
    processor = BatchProcessor(config)
    
    input_file = Path("sample_websites.csv")
    output_file = Path("comprehensive_results.json")
    report_file = Path("comprehensive_report.json")
    
    print(f"Comprehensive processing: {input_file} -> {output_file}")
    
    start_time = time.time()
    stats = await processor.process_file(
        input_file=input_file,
        output_file=output_file,
        url_column="url"
    )
    
    processing_time = time.time() - start_time
    
    # Generate detailed report
    report = processor.generate_report(report_file)
    
    print(f"\\nResults:")
    print(f"  Total URLs: {stats.total_input_urls}")
    print(f"  Active: {stats.active_websites}")
    print(f"  Inactive: {stats.inactive_websites}")
    print(f"  Errors: {stats.error_websites}")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Report saved to: {report_file}")


async def dataframe_processing():
    """
    DataFrame processing example.
    Demonstrates processing data directly from a pandas DataFrame.
    """
    print("\\n=== DataFrame Processing Example ===")
    
    # Create sample DataFrame
    companies = [
        {"name": "Google", "website": "https://google.com", "industry": "Technology"},
        {"name": "GitHub", "website": "https://github.com", "industry": "Technology"},
        {"name": "Stack Overflow", "website": "https://stackoverflow.com", "industry": "Technology"},
        {"name": "Python Foundation", "website": "https://python.org", "industry": "Technology"},
        {"name": "Invalid Company", "website": "https://invalid-site-xyz-123.com", "industry": "Test"},
    ]
    
    df = pd.DataFrame(companies)
    print(f"Processing DataFrame with {len(df)} companies")
    
    config = BatchConfig(
        batch_size=10,
        max_concurrent=5,
        include_inactive=True,
        include_errors=True
    )
    
    processor = BatchProcessor(config)
    
    output_file = Path("dataframe_results.csv")
    
    stats = await processor.process_dataframe(
        df=df,
        output_file=output_file,
        url_column="website"
    )
    
    print(f"\\nResults:")
    print(f"  Active websites: {stats.active_websites}")
    print(f"  Success rate: {stats.success_rate:.1f}%")


async def custom_checker_example():
    """
    Custom checker configuration example.
    Demonstrates advanced configuration of the underlying checker.
    """
    print("\\n=== Custom Checker Configuration Example ===")
    
    # Create custom checker with specific settings
    checker = WebsiteStatusChecker(
        max_concurrent=25,
        timeout=20,
        retry_count=2,
        retry_delay=2.0,
        backoff_factor=2.0,
        user_agent="MyCustomApp/1.0 WebsiteChecker"
    )
    
    # Test URLs with different expected outcomes
    test_urls = [
        "https://google.com",              # Should be active
        "https://httpstat.us/404",         # Should be inactive (404)
        "https://httpstat.us/500",         # Should be inactive (500)
        "https://httpstat.us/timeout",     # Should timeout
        "https://invalid-domain-xyz.com",   # Should have DNS error
        "not-a-url-at-all",               # Should be invalid URL
    ]
    
    print(f"Testing {len(test_urls)} URLs with custom configuration")
    
    results = await checker.check_websites_batch(test_urls)
    
    print("\\nDetailed Results:")
    for result in results:
        status_emoji = {
            "active": "✅",
            "inactive": "⚠️",
            "error": "❌",
            "timeout": "⏰",
            "invalid_url": "🔧"
        }.get(result.status_result.value, "❓")
        
        print(f"  {status_emoji} {result.url[:50]:<50} | "
              f"{result.status_result.value:<12} | "
              f"HTTP {result.status_code:>3} | "
              f"{result.response_time:>6.2f}s")
        
        if result.error_message:
            print(f"      Error: {result.error_message[:60]}")
    
    # Print statistics
    stats = checker.get_stats()
    print(f"\\nChecker Statistics:")
    print(f"  Total checked: {stats.total_checked}")
    print(f"  Active found: {stats.active_found}")
    print(f"  Success rate: {stats.success_rate:.1f}%")
    print(f"  Processing rate: {stats.checks_per_second:.2f} URLs/sec")
    
    await checker.close()


async def memory_efficient_processing():
    """
    Memory-efficient processing example.
    Optimized for processing large files with limited memory.
    """
    print("\\n=== Memory-Efficient Processing Example ===")
    
    # Memory-optimized configuration
    config = BatchConfig(
        batch_size=100,          # Smaller batches
        max_concurrent=25,       # Lower concurrency
        timeout=10,
        memory_efficient=True,   # Enable memory optimization
        save_interval=2,         # Save frequently
        include_inactive=True
    )
    
    processor = BatchProcessor(config)
    
    input_file = Path("sample_websites.csv")
    output_file = Path("memory_efficient_results.csv")
    
    print(f"Memory-efficient processing: {input_file} -> {output_file}")
    print("This configuration is optimized for large datasets with limited memory")
    
    start_time = time.time()
    stats = await processor.process_file(
        input_file=input_file,
        output_file=output_file,
        url_column="url"
    )
    
    processing_time = time.time() - start_time
    
    print(f"\\nResults:")
    print(f"  Processing completed successfully with minimal memory usage")
    print(f"  Active websites: {stats.active_websites}")
    print(f"  Processing time: {processing_time:.2f} seconds")


async def error_recovery_example():
    """
    Error recovery and resilience example.
    Demonstrates how the system handles various error conditions.
    """
    print("\\n=== Error Recovery Example ===")
    
    # Create a mix of URLs with known issues
    problematic_urls = [
        "https://httpstat.us/200?sleep=1000",     # Very slow response
        "https://httpstat.us/503",                # Service unavailable
        "https://expired.badssl.com",             # SSL certificate expired
        "https://wrong.host.badssl.com",          # SSL hostname mismatch
        "https://10.255.255.1",                   # Private IP (should fail)
        "https://doesnotexist12345.com",          # DNS failure
        "invalid-url-format",                     # Invalid URL
        "",                                       # Empty URL
    ]
    
    # Configuration with good error recovery
    config = BatchConfig(
        batch_size=5,
        max_concurrent=3,
        timeout=5,               # Short timeout for demo
        retry_count=2,           # Retry failed requests
        include_errors=True,     # Include error results
        include_inactive=True
    )
    
    # Create a temporary DataFrame
    df = pd.DataFrame({"url": problematic_urls})
    
    processor = BatchProcessor(config)
    output_file = Path("error_recovery_results.csv")
    
    print(f"Testing error recovery with {len(problematic_urls)} problematic URLs")
    
    try:
        stats = await processor.process_file(
            input_file=Path("temp_problematic.csv"),  # We'll process the DataFrame instead
            output_file=output_file,
            url_column="url"
        )
    except:
        # Process DataFrame directly instead
        stats = await processor.process_dataframe(
            df=df,
            output_file=output_file,
            url_column="url"
        )
    
    print(f"\\nError Recovery Results:")
    print(f"  Total processed: {len(problematic_urls)}")
    print(f"  Active: {stats.active_websites}")
    print(f"  Inactive: {stats.inactive_websites}")
    print(f"  Errors: {stats.error_websites}")
    print(f"  System handled all error conditions gracefully")


async def main():
    """
    Main function that runs all examples.
    """
    # Setup logging for the examples
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Website Status Checker - Batch Processing Examples")
    print("=" * 60)
    
    # Run all examples
    await basic_batch_processing()
    await high_performance_processing()
    await comprehensive_processing()
    await dataframe_processing()
    await custom_checker_example()
    await memory_efficient_processing()
    await error_recovery_example()
    
    print("\\n" + "=" * 60)
    print("All examples completed!")
    print("\\nCheck the generated output files:")
    print("  - basic_results.csv")
    print("  - high_performance_results.csv")
    print("  - comprehensive_results.json")
    print("  - comprehensive_report.json")
    print("  - dataframe_results.csv")
    print("  - memory_efficient_results.csv")
    print("  - error_recovery_results.csv")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()