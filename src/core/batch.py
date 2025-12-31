#!/usr/bin/env python3
"""
Batch Processor for Website Status Checker

Handles large-scale processing of website status checks with features like:
- Intelligent batch management and processing
- Progress tracking and resume capability
- Memory-efficient streaming processing
- Comprehensive error handling and recovery
- Real-time statistics and reporting
- Multi-format input/output support
"""

import asyncio
import pandas as pd
import logging
import time
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Tuple
from dataclasses import dataclass, asdict
import csv

from .checker import WebsiteStatusChecker, CheckResult, StatusResult
from ..utils.logging_config import get_logger, log_performance


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 1000
    max_concurrent: int = 100
    timeout: int = 10
    retry_count: int = 2
    save_interval: int = 10  # Save results every N batches
    resume_on_failure: bool = True
    output_format: str = 'csv'  # csv, json, xlsx
    include_inactive: bool = True
    include_errors: bool = False
    memory_efficient: bool = True
    verify_ssl: bool = True  # SSL certificate verification


@dataclass
class ProcessingStats:
    """Statistics for batch processing."""
    total_input_urls: int = 0
    batches_processed: int = 0
    total_batches: int = 0
    active_websites: int = 0
    inactive_websites: int = 0
    error_websites: int = 0
    processing_rate: float = 0.0
    estimated_completion: str = ""
    elapsed_time: float = 0.0
    
    @property
    def completion_percentage(self) -> float:
        if self.total_batches == 0:
            return 0.0
        return (self.batches_processed / self.total_batches) * 100
    
    @property
    def success_rate(self) -> float:
        total_processed = self.active_websites + self.inactive_websites + self.error_websites
        if total_processed == 0:
            return 0.0
        return (self.active_websites / total_processed) * 100


class BatchProcessor:
    """
    High-performance batch processor for website status checking.
    
    Designed to handle large datasets (100K+ URLs) efficiently with
    memory management, progress tracking, and fault tolerance.
    """
    
    def __init__(self, config: BatchConfig):
        """
        Initialize batch processor.

        Args:
            config: BatchConfig object with processing settings
        """
        self.config = config
        self.correlation_id = str(uuid.uuid4())
        self.logger = get_logger(__name__, correlation_id=self.correlation_id)
        self.checker = WebsiteStatusChecker(
            max_concurrent=config.max_concurrent,
            timeout=config.timeout,
            retry_count=config.retry_count,
            verify_ssl=config.verify_ssl
        )
        self.stats = ProcessingStats()
        self.start_time = time.time()

        self.logger.info(
            "Batch processor initialized",
            extra={
                "batch_size": config.batch_size,
                "max_concurrent": config.max_concurrent,
                "timeout": config.timeout,
                "verify_ssl": config.verify_ssl,
            }
        )
        
    def read_input_file(self, input_file: Path, url_column: str = 'url') -> Iterator[List[str]]:
        """
        Read input file in batches to manage memory efficiently.
        
        Args:
            input_file: Path to input file (CSV, Excel, or text)
            url_column: Column name containing URLs
            
        Yields:
            Batches of URLs as lists
        """
        try:
            file_ext = input_file.suffix.lower()
            
            if file_ext == '.csv':
                # Use pandas for CSV with chunking
                chunk_iter = pd.read_csv(
                    input_file, 
                    chunksize=self.config.batch_size,
                    usecols=[url_column] if url_column else None
                )
                
                for chunk in chunk_iter:
                    if url_column in chunk.columns:
                        urls = chunk[url_column].dropna().astype(str).tolist()
                        if urls:
                            yield urls
                    else:
                        self.logger.error(f"Column '{url_column}' not found in {input_file}")
                        break
                        
            elif file_ext in ['.xlsx', '.xls']:
                # Read Excel file in chunks
                df = pd.read_excel(input_file)
                if url_column not in df.columns:
                    self.logger.error(f"Column '{url_column}' not found in {input_file}")
                    return
                
                urls = df[url_column].dropna().astype(str).tolist()
                self.stats.total_input_urls = len(urls)
                
                # Yield in batches
                for i in range(0, len(urls), self.config.batch_size):
                    batch = urls[i:i + self.config.batch_size]
                    if batch:
                        yield batch
                        
            elif file_ext == '.txt':
                # Text file with one URL per line
                urls = []
                with open(input_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            urls.append(url)
                            if len(urls) >= self.config.batch_size:
                                yield urls
                                urls = []
                
                if urls:  # Yield remaining URLs
                    yield urls
                    
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

        except ValueError as e:
            # Handle missing columns gracefully
            if "Usecols do not match columns" in str(e) or "not found" in str(e):
                self.logger.error(f"Error reading input file {input_file}: {e}")
                return  # Return empty (no yields)
            else:
                raise
        except Exception as e:
            self.logger.error(f"Error reading input file {input_file}: {e}")
            raise
    
    def save_results_batch(
        self, 
        results: List[CheckResult], 
        output_file: Path, 
        append: bool = True
    ) -> None:
        """
        Save batch results to output file.
        
        Args:
            results: List of CheckResult objects
            output_file: Path to output file
            append: Whether to append to existing file
        """
        try:
            # Filter results based on configuration
            filtered_results = []
            for result in results:
                if result.status_result == StatusResult.ACTIVE:
                    filtered_results.append(result)
                elif result.status_result == StatusResult.INACTIVE and self.config.include_inactive:
                    filtered_results.append(result)
                elif result.status_result in [StatusResult.ERROR, StatusResult.TIMEOUT] and self.config.include_errors:
                    filtered_results.append(result)
            
            if not filtered_results:
                return
            
            file_ext = output_file.suffix.lower()
            
            if file_ext == '.csv':
                # Convert to DataFrame
                df = pd.DataFrame([asdict(result) for result in filtered_results])
                
                # Convert enums to strings
                df['status_result'] = df['status_result'].astype(str)
                df['error_category'] = df['error_category'].astype(str)
                
                # Save to CSV
                mode = 'a' if append and output_file.exists() else 'w'
                header = not (append and output_file.exists())
                df.to_csv(output_file, mode=mode, index=False, header=header)
                
            elif file_ext == '.json':
                # Save as JSON
                data = [asdict(result) for result in filtered_results]
                
                if append and output_file.exists():
                    # Load existing data and append
                    try:
                        with open(output_file, 'r') as f:
                            existing_data = json.load(f)
                        data = existing_data + data
                    except (json.JSONDecodeError, IOError) as e:
                        self.logger.warning(f"Could not load existing JSON file for append: {e}")
                        # Continue with new data only
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
            elif file_ext in ['.xlsx', '.xls']:
                # Save as Excel
                df = pd.DataFrame([asdict(result) for result in filtered_results])
                df['status_result'] = df['status_result'].astype(str)
                df['error_category'] = df['error_category'].astype(str)
                
                if append and output_file.exists():
                    # Load existing Excel and append
                    try:
                        existing_df = pd.read_excel(output_file)
                        df = pd.concat([existing_df, df], ignore_index=True)
                    except (pd.errors.ParserError, IOError, ValueError) as e:
                        self.logger.warning(f"Could not load existing Excel file for append: {e}")
                        # Continue with new data only
                
                df.to_excel(output_file, index=False)
                
            else:
                raise ValueError(f"Unsupported output format: {file_ext}")
                
        except Exception as e:
            self.logger.error(f"Error saving results to {output_file}: {e}")
    
    def update_stats(self, results: List[CheckResult]) -> None:
        """Update processing statistics."""
        for result in results:
            if result.status_result == StatusResult.ACTIVE:
                self.stats.active_websites += 1
            elif result.status_result == StatusResult.INACTIVE:
                self.stats.inactive_websites += 1
            else:
                self.stats.error_websites += 1
        
        self.stats.elapsed_time = time.time() - self.start_time
        
        # Calculate processing rate
        total_processed = (
            self.stats.active_websites + 
            self.stats.inactive_websites + 
            self.stats.error_websites
        )
        
        if self.stats.elapsed_time > 0:
            self.stats.processing_rate = total_processed / self.stats.elapsed_time
        
        # Estimate completion time
        if self.stats.processing_rate > 0 and self.stats.total_input_urls > 0:
            remaining_urls = self.stats.total_input_urls - total_processed
            estimated_seconds = remaining_urls / self.stats.processing_rate
            hours, remainder = divmod(int(estimated_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stats.estimated_completion = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def print_progress(self) -> None:
        """Print current progress statistics."""
        total_processed = (
            self.stats.active_websites + 
            self.stats.inactive_websites + 
            self.stats.error_websites
        )
        
        self.logger.info(
            f"Progress: {self.stats.batches_processed}/{self.stats.total_batches} batches "
            f"({self.stats.completion_percentage:.1f}%) | "
            f"Processed: {total_processed:,}/{self.stats.total_input_urls:,} URLs | "
            f"Active: {self.stats.active_websites:,} ({self.stats.success_rate:.1f}%) | "
            f"Rate: {self.stats.processing_rate:.1f} URLs/sec | "
            f"ETA: {self.stats.estimated_completion}"
        )
    
    async def process_file(
        self, 
        input_file: Path, 
        output_file: Path,
        url_column: str = 'url'
    ) -> ProcessingStats:
        """
        Process entire file with batch processing.
        
        Args:
            input_file: Input file path
            output_file: Output file path
            url_column: Column name containing URLs
            
        Returns:
            Final processing statistics
        """
        self.logger.info(f"Starting batch processing: {input_file} -> {output_file}")
        
        try:
            # Count total URLs for statistics
            if not self.config.memory_efficient:
                try:
                    if input_file.suffix.lower() == '.csv':
                        df = pd.read_csv(input_file)
                        self.stats.total_input_urls = len(df)
                    elif input_file.suffix.lower() in ['.xlsx', '.xls']:
                        df = pd.read_excel(input_file)
                        self.stats.total_input_urls = len(df)
                    else:
                        with open(input_file, 'r', encoding='utf-8') as f:
                            self.stats.total_input_urls = sum(1 for line in f if line.strip())
                except (pd.errors.ParserError, IOError, UnicodeDecodeError) as e:
                    self.logger.warning(f"Could not count total URLs: {e}")
                    self.logger.debug(f"Will proceed with batch processing without total count")
            
            # Calculate total batches
            if self.stats.total_input_urls > 0:
                self.stats.total_batches = (
                    self.stats.total_input_urls + self.config.batch_size - 1
                ) // self.config.batch_size
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Process batches
            batch_num = 0
            for batch_urls in self.read_input_file(input_file, url_column):
                batch_num += 1
                
                self.logger.info(f"Processing batch {batch_num}/{self.stats.total_batches} ({len(batch_urls)} URLs)")
                
                # Check websites in this batch
                results = await self.checker.check_websites_batch(batch_urls)
                
                # Save results
                self.save_results_batch(results, output_file, append=batch_num > 1)
                
                # Update statistics
                self.stats.batches_processed = batch_num
                self.update_stats(results)
                
                # Print progress
                if batch_num % max(1, self.stats.total_batches // 20) == 0 or batch_num == self.stats.total_batches:
                    self.print_progress()
                
                # Save progress periodically
                if batch_num % self.config.save_interval == 0:
                    self.checker.save_progress([str(batch_num)], str(batch_num))
                
                # Brief pause to prevent overwhelming servers
                await asyncio.sleep(0.1)
            
            # Final statistics
            self.stats.elapsed_time = time.time() - self.start_time
            duration_ms = self.stats.elapsed_time * 1000

            # Log performance metrics
            log_performance(
                self.logger,
                "batch_processing",
                duration_ms,
                extra={
                    "total_urls": self.stats.total_input_urls,
                    "active_websites": self.stats.active_websites,
                    "inactive_websites": self.stats.inactive_websites,
                    "error_websites": self.stats.error_websites,
                    "processing_rate": self.stats.processing_rate,
                    "batches_processed": self.stats.batches_processed,
                }
            )

            self.logger.info("Batch processing completed!")
            self.print_progress()

            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error during batch processing: {e}")
            raise
        finally:
            await self.checker.close()
    
    async def process_dataframe(
        self, 
        df: pd.DataFrame, 
        output_file: Path,
        url_column: str = 'url'
    ) -> ProcessingStats:
        """
        Process DataFrame directly.
        
        Args:
            df: Input DataFrame
            output_file: Output file path
            url_column: Column name containing URLs
            
        Returns:
            Processing statistics
        """
        if url_column not in df.columns:
            raise ValueError(f"Column '{url_column}' not found in DataFrame")
        
        urls = df[url_column].dropna().astype(str).tolist()
        self.stats.total_input_urls = len(urls)
        self.stats.total_batches = (len(urls) + self.config.batch_size - 1) // self.config.batch_size
        
        self.logger.info(f"Processing DataFrame with {len(urls)} URLs")
        
        try:
            # Process in batches
            for i in range(0, len(urls), self.config.batch_size):
                batch_urls = urls[i:i + self.config.batch_size]
                batch_num = (i // self.config.batch_size) + 1
                
                self.logger.info(f"Processing batch {batch_num}/{self.stats.total_batches}")
                
                # Check websites
                results = await self.checker.check_websites_batch(batch_urls)
                
                # Save results
                self.save_results_batch(results, output_file, append=batch_num > 1)
                
                # Update statistics
                self.stats.batches_processed = batch_num
                self.update_stats(results)
                
                # Print progress
                if batch_num % max(1, self.stats.total_batches // 20) == 0:
                    self.print_progress()
                
                await asyncio.sleep(0.1)
            
            self.print_progress()
            return self.stats
            
        finally:
            await self.checker.close()
    
    def generate_report(self, output_file: Path) -> Dict:
        """
        Generate comprehensive processing report.
        
        Args:
            output_file: Path to save report
            
        Returns:
            Report dictionary
        """
        report = {
            'processing_summary': {
                'total_input_urls': self.stats.total_input_urls,
                'active_websites': self.stats.active_websites,
                'inactive_websites': self.stats.inactive_websites,
                'error_websites': self.stats.error_websites,
                'success_rate': f"{self.stats.success_rate:.2f}%",
                'processing_time': f"{self.stats.elapsed_time/60:.2f} minutes",
                'processing_rate': f"{self.stats.processing_rate:.2f} URLs/second"
            },
            'configuration': asdict(self.config),
            'checker_stats': asdict(self.checker.get_stats()),
            'timestamp': time.time()
        }
        
        # Save report as JSON
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Processing report saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
        
        return report