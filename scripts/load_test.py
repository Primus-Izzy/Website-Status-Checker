#!/usr/bin/env python3
"""
Load Testing Script for Website Status Checker

Simple load testing to verify system performance and capacity.
"""

import argparse
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class LoadTestResult:
    """Results from a load test run"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index]

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[index]

    @property
    def requests_per_second(self) -> float:
        if self.duration == 0:
            return 0.0
        return self.total_requests / self.duration


async def make_request(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    headers: dict = None,
    data: dict = None
) -> tuple:
    """Make a single HTTP request and return timing and status"""
    start_time = time.time()
    try:
        async with session.request(method, url, headers=headers, json=data) as response:
            await response.read()  # Read response body
            elapsed = time.time() - start_time
            return response.status, elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        return 0, elapsed, str(e)


async def run_load_test(
    url: str,
    num_requests: int,
    concurrency: int,
    method: str = "GET",
    headers: dict = None,
    data: dict = None
) -> LoadTestResult:
    """Run load test with specified parameters"""
    result = LoadTestResult()
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_request(session):
        async with semaphore:
            return await make_request(session, url, method, headers, data)

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [bounded_request(session) for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks)

    result.duration = time.time() - start_time
    result.total_requests = num_requests

    for status, elapsed, error in responses:
        result.response_times.append(elapsed)

        if error:
            result.failed_requests += 1
            result.errors.append(error)
        elif 200 <= status < 300:
            result.successful_requests += 1
            result.status_codes[status] = result.status_codes.get(status, 0) + 1
        else:
            result.failed_requests += 1
            result.status_codes[status] = result.status_codes.get(status, 0) + 1

    return result


def print_results(result: LoadTestResult):
    """Print load test results in a formatted manner"""
    print("\n" + "="*60)
    print("Load Test Results")
    print("="*60)

    print(f"\nTotal Requests:      {result.total_requests}")
    print(f"Successful:          {result.successful_requests}")
    print(f"Failed:              {result.failed_requests}")
    print(f"Success Rate:        {result.success_rate:.2f}%")
    print(f"Duration:            {result.duration:.2f}s")
    print(f"Requests/sec:        {result.requests_per_second:.2f}")

    print(f"\nResponse Times:")
    print(f"  Average:           {result.avg_response_time*1000:.2f}ms")
    print(f"  P95:               {result.p95_response_time*1000:.2f}ms")
    print(f"  P99:               {result.p99_response_time*1000:.2f}ms")
    if result.response_times:
        print(f"  Min:               {min(result.response_times)*1000:.2f}ms")
        print(f"  Max:               {max(result.response_times)*1000:.2f}ms")

    if result.status_codes:
        print(f"\nStatus Codes:")
        for status, count in sorted(result.status_codes.items()):
            print(f"  {status}:               {count}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)} total):")
        # Show first 5 unique errors
        unique_errors = list(set(result.errors))[:5]
        for error in unique_errors:
            print(f"  - {error}")

    # Performance Assessment
    print(f"\nPerformance Assessment:")
    if result.success_rate >= 99:
        print("  ✅ Success rate: Excellent")
    elif result.success_rate >= 95:
        print("  ⚠️  Success rate: Good")
    else:
        print("  ❌ Success rate: Poor")

    if result.avg_response_time < 0.1:
        print("  ✅ Avg latency: Excellent (<100ms)")
    elif result.avg_response_time < 0.5:
        print("  ⚠️  Avg latency: Good (<500ms)")
    else:
        print("  ❌ Avg latency: Poor (>500ms)")

    if result.p95_response_time < 1.0:
        print("  ✅ P95 latency: Excellent (<1s)")
    elif result.p95_response_time < 2.0:
        print("  ⚠️  P95 latency: Good (<2s)")
    else:
        print("  ❌ P95 latency: Poor (>2s)")

    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Load test Website Status Checker API"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/health",
        help="URL to test (default: http://localhost:8000/health)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of requests (default: 100)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)"
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST"],
        help="HTTP method (default: GET)"
    )
    parser.add_argument(
        "--api-key",
        help="API key for authenticated requests"
    )

    args = parser.parse_args()

    headers = {}
    if args.api_key:
        headers["X-API-Key"] = args.api_key

    print(f"\n🔥 Starting Load Test")
    print(f"URL:          {args.url}")
    print(f"Requests:     {args.requests}")
    print(f"Concurrency:  {args.concurrency}")
    print(f"Method:       {args.method}")
    if args.api_key:
        print(f"API Key:      {'*' * 10}...{args.api_key[-4:]}")
    print()

    # Run the load test
    result = asyncio.run(run_load_test(
        url=args.url,
        num_requests=args.requests,
        concurrency=args.concurrency,
        method=args.method,
        headers=headers
    ))

    # Print results
    print_results(result)

    # Exit code based on success
    if result.success_rate >= 95 and result.p95_response_time < 2.0:
        print("✅ Load test PASSED\n")
        return 0
    else:
        print("❌ Load test FAILED\n")
        return 1


if __name__ == "__main__":
    exit(main())
