#!/usr/bin/env python3
"""
End-to-End Real-World Test
Tests complete workflow with realistic data
"""

import asyncio
import sys
from pathlib import Path
import json
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.batch import BatchProcessor, BatchConfig

async def end_to_end_test():
    """Complete end-to-end test with real-world data"""

    print("=" * 70)
    print("END-TO-END REAL-WORLD TEST".center(70))
    print("=" * 70)

    # Configuration
    print("\n[STEP 1] Configuring batch processor...")
    config = BatchConfig(
        batch_size=5,  # Small batches for testing
        max_concurrent=5,
        timeout=10,
        retry_count=2,
        include_inactive=True,
        include_errors=True,
        verify_ssl=True
    )
    print(f"  - Batch size: {config.batch_size}")
    print(f"  - Concurrent: {config.max_concurrent}")
    print(f"  - Timeout: {config.timeout}s")
    print("  [OK] Configuration complete")

    # Input file
    input_file = Path("real_world_test.csv")
    if not input_file.exists():
        print(f"\n[FAIL] Input file not found: {input_file}")
        return False

    print(f"\n[STEP 2] Loading input file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"  - Total URLs: {len(df)}")
    print(f"  - Sample URLs:")
    for url in df['url'].head(3):
        print(f"    * {url}")
    print("  [OK] Input file loaded")

    # Process with CSV output
    print("\n[STEP 3] Processing URLs (CSV export)...")
    output_csv = Path("real_world_results.csv")

    processor = BatchProcessor(config)

    try:
        stats = await processor.process_file(
            input_file=input_file,
            output_file=output_csv,
            url_column="url"
        )

        total_processed = stats.active_websites + stats.inactive_websites + stats.error_websites

        print(f"\n  Results:")
        print(f"    Total URLs: {stats.total_input_urls}")
        print(f"    Processed: {total_processed}")
        print(f"    Active: {stats.active_websites} ({stats.active_websites/total_processed*100:.1f}%)")
        print(f"    Inactive: {stats.inactive_websites}")
        print(f"    Errors: {stats.error_websites}")
        print(f"    Processing Rate: {stats.processing_rate:.1f} URLs/sec")
        print(f"    Elapsed Time: {stats.elapsed_time:.1f}s")
        print("  [OK] Processing complete")

    except Exception as e:
        print(f"\n  [FAIL] Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verify CSV output
    print("\n[STEP 4] Verifying CSV output...")
    if not output_csv.exists():
        print("  [FAIL] CSV file not created")
        return False

    df_results = pd.read_csv(output_csv)
    print(f"  - Output rows: {len(df_results)}")
    print(f"  - Columns: {list(df_results.columns)}")
    print("  [OK] CSV output verified")

    # Sample results
    print("\n[STEP 5] Sample results:")
    print("\n  Active websites:")
    active = df_results[df_results['status_result'].str.contains('ACTIVE', na=False)].head(3)
    for _, row in active.iterrows():
        print(f"    * {row['url']} -> {row['status_code']} ({row['response_time']:.2f}s)")

    print("\n  Error cases:")
    errors = df_results[df_results['status_result'].str.contains('ERROR|INVALID', na=False)].head(3)
    for _, row in errors.iterrows():
        error_msg = row['error_message'][:50] if pd.notna(row['error_message']) else 'N/A'
        print(f"    * {row['url']} -> {error_msg}")

    # Process with JSON output
    print("\n[STEP 6] Testing JSON export...")
    output_json = Path("real_world_results.json")

    processor2 = BatchProcessor(config)

    try:
        await processor2.process_file(
            input_file=input_file,
            output_file=output_json,
            url_column="url"
        )

        if output_json.exists():
            with open(output_json) as f:
                json_data = json.load(f)
            print(f"  - JSON records: {len(json_data)}")
            print("  [OK] JSON export verified")
        else:
            print("  [FAIL] JSON file not created")
            return False

    except Exception as e:
        print(f"  [FAIL] JSON export error: {e}")
        return False

    # Final summary
    print("\n" + "=" * 70)
    print("END-TO-END TEST SUMMARY".center(70))
    print("=" * 70)
    print("\nTest Components:")
    print("  [OK] Configuration")
    print("  [OK] File loading")
    print("  [OK] Batch processing")
    print("  [OK] CSV export")
    print("  [OK] JSON export")
    print("  [OK] Data verification")
    print("  [OK] Error handling")

    print(f"\nPerformance:")
    print(f"  Processed: {total_processed} URLs")
    print(f"  Time: {stats.elapsed_time:.1f}s")
    print(f"  Rate: {stats.processing_rate:.1f} URLs/sec")
    print(f"  Success: {stats.active_websites}/{total_processed} ({stats.active_websites/total_processed*100:.1f}%)")

    print("\nOutput Files:")
    print(f"  CSV: {output_csv} ({output_csv.stat().st_size:,} bytes)")
    print(f"  JSON: {output_json} ({output_json.stat().st_size:,} bytes)")

    print("\n" + "=" * 70)
    print("[SUCCESS] END-TO-END TEST PASSED".center(70))
    print("=" * 70)

    return True

if __name__ == "__main__":
    result = asyncio.run(end_to_end_test())
    sys.exit(0 if result else 1)
