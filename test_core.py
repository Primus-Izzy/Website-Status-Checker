#!/usr/bin/env python3
"""Test core functionality directly"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.checker import WebsiteStatusChecker
from src.core.batch import BatchProcessor, BatchConfig

async def test_single_url():
    """Test checking a single URL"""
    print("=" * 60)
    print("TEST 1: Single URL Check")
    print("=" * 60)

    checker = WebsiteStatusChecker(timeout=10, retry_count=1)

    test_urls = [
        "https://google.com",
        "https://github.com",
        "https://nonexistent-site-12345.com"
    ]

    for url in test_urls:
        print(f"\nChecking: {url}")
        result = await checker.check_website(url)
        print(f"  Status: {result.status_result}")
        print(f"  Code: {result.status_code}")
        print(f"  Response Time: {result.response_time:.2f}s")
        if result.error_message:
            print(f"  Error: {result.error_message}")

    await checker.close()
    print("\n[PASS] Single URL check completed")

async def test_batch_processing():
    """Test batch processing"""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Processing")
    print("=" * 60)

    config = BatchConfig(
        batch_size=10,
        max_concurrent=3,
        timeout=10,
        retry_count=1,
        include_inactive=True,
        include_errors=True
    )

    processor = BatchProcessor(config)

    input_file = Path("test_urls.csv")
    output_file = Path("test_results.csv")

    if not input_file.exists():
        print(f"[SKIP] Input file {input_file} not found")
        return

    print(f"\nProcessing: {input_file}")
    print(f"Output: {output_file}")

    try:
        stats = await processor.process_file(
            input_file=input_file,
            output_file=output_file,
            url_column="url"
        )

        total_processed = stats.active_websites + stats.inactive_websites + stats.error_websites
        print(f"\nResults:")
        print(f"  Total URLs: {stats.total_input_urls}")
        print(f"  Processed: {total_processed}")
        print(f"  Active: {stats.active_websites}")
        print(f"  Inactive: {stats.inactive_websites}")
        print(f"  Errors: {stats.error_websites}")
        print(f"  Success Rate: {stats.success_rate:.1f}%")
        print(f"  Processing Rate: {stats.processing_rate:.1f} URLs/sec")
        print(f"  Elapsed Time: {stats.elapsed_time:.1f}s")

        print(f"\n[PASS] Batch processing completed")

        # Verify output file
        if output_file.exists():
            import pandas as pd
            df = pd.read_csv(output_file)
            print(f"\nOutput file contains {len(df)} rows")
            print("\nSample results:")
            print(df[['url', 'status_result', 'status_code']].head())

    except Exception as e:
        print(f"\n[FAIL] Batch processing error: {e}")
        import traceback
        traceback.print_exc()

async def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("TEST 3: Error Handling")
    print("=" * 60)

    checker = WebsiteStatusChecker(timeout=5, retry_count=0)

    test_cases = [
        ("Invalid URL", "not-a-url"),
        ("Localhost", "localhost"),
        ("Invalid TLD", "test.invalid"),
        ("Empty", ""),
        ("None", None)
    ]

    for name, url in test_cases:
        print(f"\n{name}: {url}")
        result = await checker.check_website(url)
        print(f"  Status: {result.status_result}")
        if result.error_category:
            print(f"  Category: {result.error_category}")

    await checker.close()
    print("\n[PASS] Error handling test completed")

async def main():
    """Run all tests"""
    print("\n")
    print("*" * 60)
    print("  COMPREHENSIVE CORE FUNCTIONALITY TEST")
    print("*" * 60)

    try:
        await test_single_url()
        await test_batch_processing()
        await test_error_handling()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
