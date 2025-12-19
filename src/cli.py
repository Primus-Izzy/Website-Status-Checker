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

from website_status_checker import WebsiteStatusChecker
from batch_processor import BatchProcessor, BatchConfig


def setup_logging(verbose: bool = False, debug: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""
    
    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce aiohttp logging noise
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


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
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
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
        # Validate arguments
        validate_arguments(args)
        
        # Setup logging
        if not args.quiet:
            setup_logging(
                verbose=args.verbose,
                debug=args.debug,
                log_file=args.log_file
            )
            print_banner()
        
        logger = logging.getLogger(__name__)
        
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
            memory_efficient=args.memory_efficient
        )
        
        # Display configuration
        if not args.quiet:
            logger.info("Processing Configuration:")
            logger.info(f"  Input file: {args.input_file}")
            logger.info(f"  Output file: {args.output}")
            logger.info(f"  URL column: {args.url_column}")
            logger.info(f"  Batch size: {config.batch_size}")
            logger.info(f"  Concurrent requests: {config.max_concurrent}")
            logger.info(f"  Timeout: {config.timeout}s")
            logger.info(f"  Retry count: {config.retry_count}")
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