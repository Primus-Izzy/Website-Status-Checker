"""Processor Service - Integrates with core BatchProcessor for GUI"""

import asyncio
from pathlib import Path
from typing import Callable, Optional
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.batch import BatchProcessor, BatchConfig
from src.core.checker import CheckResult
from gui.models.schemas import ProcessingConfig, JobStatus
from gui.services.job_manager import JobManager
from gui.services.file_handler import FileHandler


class ProcessorService:
    """
    Service that bridges GUI and core processing engine.

    Manages background processing jobs and provides progress callbacks.
    """

    def __init__(self, job_manager: JobManager, file_handler: FileHandler):
        self.job_manager = job_manager
        self.file_handler = file_handler

    async def process_job(self, job_id: str, config: ProcessingConfig):
        """
        Background task to process a job.

        Args:
            job_id: Unique job identifier
            config: Processing configuration
        """
        try:
            # Update job status
            await self.job_manager.update_progress(job_id, status=JobStatus.PROCESSING)

            # Get uploaded file
            file_path = self.file_handler.get_upload_path(job_id)

            # Get output path
            output_path = self.file_handler.get_export_path(job_id, "csv")

            # Create batch configuration
            batch_config = BatchConfig(
                batch_size=config.batch_size,
                max_concurrent=config.concurrent,
                timeout=config.timeout,
                retry_count=config.retry_count,
                include_inactive=config.include_inactive,
                include_errors=config.include_errors,
                memory_efficient=True
            )

            # Create custom batch processor with progress callback
            processor = CustomBatchProcessor(
                batch_config,
                progress_callback=self._create_progress_callback(job_id)
            )

            # Process file
            stats = await processor.process_file(
                file_path,
                output_path,
                config.url_column
            )

            # Mark as complete
            await self.job_manager.update_progress(
                job_id,
                status=JobStatus.COMPLETED,
                processed_urls=stats.active_websites + stats.inactive_websites + stats.error_websites
            )

        except Exception as e:
            # Mark as failed
            await self.job_manager.update_progress(
                job_id,
                status=JobStatus.FAILED
            )
            await self.job_manager.add_error(job_id, str(e))

    def _create_progress_callback(self, job_id: str) -> Callable:
        """
        Create a progress callback for BatchProcessor.

        Args:
            job_id: Job identifier

        Returns:
            Async callback function
        """
        async def callback(batch_num: int, total_batches: int, results: list):
            """Progress callback invoked after each batch"""
            # Count results by status
            from src.core.checker import StatusResult

            active = sum(1 for r in results if r.status_result == StatusResult.ACTIVE)
            inactive = sum(1 for r in results if r.status_result == StatusResult.INACTIVE)
            errors = sum(1 for r in results if r.status_result in [StatusResult.ERROR, StatusResult.TIMEOUT])

            # Update job progress
            await self.job_manager.update_progress(
                job_id,
                current_batch=batch_num,
                total_batches=total_batches,
                active_count=active,
                inactive_count=inactive,
                error_count=errors,
                processed_urls=batch_num * len(results)
            )

        return callback


class CustomBatchProcessor(BatchProcessor):
    """
    Extended BatchProcessor with progress callback support.

    Calls a callback function after each batch is processed.
    """

    def __init__(self, config: BatchConfig, progress_callback: Optional[Callable] = None):
        super().__init__(config)
        self.progress_callback = progress_callback

    async def process_file(self, input_file: Path, output_file: Path, url_column: str = 'url'):
        """
        Process file with progress callbacks.

        Overrides parent method to add callback invocations.
        """
        self.logger.info(f"Starting batch processing: {input_file} -> {output_file}")

        try:
            # Count total URLs for statistics
            if not self.config.memory_efficient:
                try:
                    import pandas as pd
                    if input_file.suffix.lower() == '.csv':
                        df = pd.read_csv(input_file)
                        self.stats.total_input_urls = len(df)
                    elif input_file.suffix.lower() in ['.xlsx', '.xls']:
                        df = pd.read_excel(input_file)
                        self.stats.total_input_urls = len(df)
                except Exception as e:
                    self.logger.warning(f"Could not count total URLs: {e}")

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

                # Call progress callback
                if self.progress_callback:
                    await self.progress_callback(batch_num, self.stats.total_batches, results)

                # Print progress
                if batch_num % max(1, self.stats.total_batches // 20) == 0 or batch_num == self.stats.total_batches:
                    self.print_progress()

                # Brief pause
                await asyncio.sleep(0.1)

            # Final statistics
            self.logger.info("Batch processing completed!")
            self.print_progress()

            return self.stats

        except Exception as e:
            self.logger.error(f"Error during batch processing: {e}")
            raise
        finally:
            await self.checker.close()
