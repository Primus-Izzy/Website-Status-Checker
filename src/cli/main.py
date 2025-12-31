#!/usr/bin/env python3
"""
Website Status Checker - Command Line Interface

A comprehensive CLI for checking website status at scale with features:
- Batch processing of large datasets (100K+ URLs)
- Concurrent processing with configurable limits
- Progress tracking and resume capability
- Multiple input/output formats
- Comprehensive error handling and reporting
- Performance optimization and monitoring
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from ..core.checker import WebsiteStatusChecker
from ..core.batch import BatchProcessor, BatchConfig
from ..config import get_app_config
from ..utils.secrets import validate_environment, get_env_info
from ..utils.logging_config import setup_logging as setup_structured_logging, get_logger


def setup_logging(verbose: bool = False, debug: bool = False, log_file: Optional[str] = None, json_format: bool = False):
    """
    Setup logging configuration using structured logging.

    Args:
        verbose: Enable verbose (INFO level) logging
        debug: Enable debug logging
        log_file: Optional log file path
        json_format: Use JSON format for logs
    """
    # Determine log level
    if debug:
        level = "DEBUG"
    elif verbose:
        level = "INFO"
    else:
        level = "WARNING"

    # Determine log format
    log_format = "json" if json_format else "text"

    # Setup structured logging
    setup_structured_logging(
        log_level=level,
        log_format=log_format,
        log_file=log_file,
        enable_console=True
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    
    parser = argparse.ArgumentParser(
        description='Website Status Checker - Check if websites are active at scale',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  python cli.py input.csv --output results.csv
  
  # High-performance processing
  python cli.py large_dataset.csv --output results.csv --concurrent 200 --batch-size 2000
  
  # Debug mode with detailed logging
  python cli.py input.csv --output results.csv --verbose --debug --log-file debug.log
  
  # Include inactive and error websites in results
  python cli.py input.csv --output results.csv --include-inactive --include-errors
  
  # Process specific column from Excel file
  python cli.py companies.xlsx --output active_companies.csv --url-column "Website URL"
  
  # Resume interrupted processing
  python cli.py input.csv --output results.csv --resume
        '''
    )
    
    # Input/Output arguments
    parser.add_argument(
        'input_file',
        type=str,
        help='Input file path (CSV, Excel, or text file with URLs)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='website_status_results.csv',
        help='Output file path (default: website_status_results.csv)'
    )
    
    parser.add_argument(
        '--url-column',
        type=str,
        default='url',
        help='Column name containing URLs (default: url)'
    )
    
    parser.add_argument(
        '--report',
        type=str,
        help='Generate processing report to specified file'
    )
    
    # Processing configuration
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Number of URLs per batch (default: 1000)'
    )
    
    parser.add_argument(
        '--concurrent',
        type=int,
        default=100,
        help='Maximum concurrent requests (default: 100)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    parser.add_argument(
        '--retry-count',
        type=int,
        default=2,
        help='Number of retry attempts (default: 2)'
    )
    
    parser.add_argument(
        '--save-interval',
        type=int,
        default=10,
        help='Save results every N batches (default: 10)'
    )
    
    # Output filtering
    parser.add_argument(
        '--include-inactive',
        action='store_true',
        help='Include inactive websites in results'
    )
    
    parser.add_argument(
        '--include-errors',
        action='store_true',
        help='Include error websites in results'
    )
    
    parser.add_argument(
        '--active-only',
        action='store_true',
        help='Only output active websites (overrides other include options)'
    )
    
    # Performance options
    parser.add_argument(
        '--memory-efficient',
        action='store_true',
        help='Enable memory-efficient processing for large files'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume interrupted processing'
    )
    
    # Output format
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'xlsx'],
        default='csv',
        help='Output format (default: csv)'
    )
    
    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Save logs to file'
    )

    parser.add_argument(
        '--json-logs',
        action='store_true',
        help='Output logs in JSON format (useful for log aggregation)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    # Security options
    parser.add_argument(
        '--disable-ssl-verify',
        action='store_true',
        help='Disable SSL certificate verification (SECURITY RISK - use only for testing)'
    )

    return parser


def validate_arguments(args) -> None:
    """Validate command line arguments."""
    
    # Check input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {args.input_file}")
    
    # Check input file format
    supported_extensions = {'.csv', '.xlsx', '.xls', '.txt'}
    if input_path.suffix.lower() not in supported_extensions:
        raise ValueError(f"Unsupported input format. Supported: {', '.join(supported_extensions)}")
    
    # Validate numeric arguments
    if args.batch_size < 1:
        raise ValueError("Batch size must be at least 1")
    
    if args.concurrent < 1:
        raise ValueError("Concurrent requests must be at least 1")
    
    if args.timeout < 1:
        raise ValueError("Timeout must be at least 1 second")
    
    if args.retry_count < 0:
        raise ValueError("Retry count cannot be negative")
    
    # Validate output format matches output file extension if specified
    output_path = Path(args.output)
    if output_path.suffix.lower():
        format_map = {'.csv': 'csv', '.json': 'json', '.xlsx': 'xlsx', '.xls': 'xlsx'}
        inferred_format = format_map.get(output_path.suffix.lower())
        if inferred_format and inferred_format != args.format:
            print(f"Warning: Output format '{args.format}' doesn't match file extension. Using '{inferred_format}'")
            args.format = inferred_format


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Website Status Checker                    ║
║              High-Performance URL Status Validation         ║
║                        Version 1.0.0                        ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """Main CLI entry point."""

    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Load application configuration
        app_config = get_app_config()

        # Validate arguments
        validate_arguments(args)

        # Setup logging
        if not args.quiet:
            setup_logging(
                verbose=args.verbose,
                debug=args.debug,
                log_file=args.log_file,
                json_format=args.json_logs
            )
            if not args.json_logs:  # Only print banner in text mode
                print_banner()

        logger = get_logger(__name__)

        # Validate environment for production
        if app_config.is_production:
            is_valid, issues = validate_environment(env="production")
            if not is_valid:
                logger.error("Production environment validation failed:")
                for issue in issues:
                    logger.error(f"  - {issue}")
                if any("CRITICAL" in issue for issue in issues):
                    logger.error("Critical issues detected. Exiting.")
                    return 1

        # Log environment info in debug mode
        if args.debug:
            logger.debug("Environment configuration:")
            for key, value in get_env_info().items():
                logger.debug(f"  {key}: {value}")

        # Validate production config
        if app_config.is_production:
            config_issues = app_config.validate_production_config()
            if config_issues:
                logger.warning("Production configuration warnings:")
                for issue in config_issues:
                    logger.warning(f"  - {issue}")
        
        # Warn if SSL verification is disabled
        if args.disable_ssl_verify:
            logger.warning("⚠️  SSL VERIFICATION DISABLED - This is a security risk!")

        # Create batch configuration
        config = BatchConfig(
            batch_size=args.batch_size,
            max_concurrent=args.concurrent,
            timeout=args.timeout,
            retry_count=args.retry_count,
            save_interval=args.save_interval,
            resume_on_failure=args.resume,
            output_format=args.format,
            include_inactive=args.include_inactive and not args.active_only,
            include_errors=args.include_errors and not args.active_only,
            memory_efficient=args.memory_efficient,
            verify_ssl=not args.disable_ssl_verify
        )
        
        # Display configuration
        if not args.quiet:
            logger.info("Processing Configuration:")
            logger.info(f"  Environment: {app_config.env}")
            logger.info(f"  Input file: {args.input_file}")
            logger.info(f"  Output file: {args.output}")
            logger.info(f"  URL column: {args.url_column}")
            logger.info(f"  Batch size: {config.batch_size}")
            logger.info(f"  Concurrent requests: {config.max_concurrent}")
            logger.info(f"  Timeout: {config.timeout}s")
            logger.info(f"  Retry count: {config.retry_count}")
            logger.info(f"  SSL verification: {config.verify_ssl}")
            logger.info(f"  Output format: {config.output_format}")
            logger.info(f"  Include inactive: {config.include_inactive}")
            logger.info(f"  Include errors: {config.include_errors}")
            logger.info("")
        
        # Create batch processor
        processor = BatchProcessor(config)
        
        # Process file
        start_time = time.time()
        stats = await processor.process_file(
            input_file=Path(args.input_file),
            output_file=Path(args.output),
            url_column=args.url_column
        )
        
        processing_time = time.time() - start_time
        
        # Print final results
        if not args.quiet:
            print("\n" + "="*80)
            print("PROCESSING COMPLETE!")
            print("="*80)
            print(f"Total URLs processed: {stats.total_input_urls:,}")
            print(f"Active websites found: {stats.active_websites:,} ({stats.success_rate:.2f}%)")
            print(f"Inactive websites: {stats.inactive_websites:,}")
            print(f"Error websites: {stats.error_websites:,}")
            print(f"Processing time: {processing_time/60:.2f} minutes")
            print(f"Average rate: {stats.processing_rate:.2f} URLs/second")
            print(f"Results saved to: {args.output}")
        
        # Generate report if requested
        if args.report:
            report = processor.generate_report(Path(args.report))
            if not args.quiet:
                print(f"Report saved to: {args.report}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        if args.debug if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        print(f"Fatal error: {e}")
        return 1


def cli_entry_point():
    """Entry point for console script."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    cli_entry_point()