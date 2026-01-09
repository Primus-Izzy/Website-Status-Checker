"""Process controller for orchestrating URL checking with async bridge."""

import asyncio
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Callable, Dict
from dataclasses import dataclass, asdict

# Import core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.batch import BatchProcessor, BatchConfig
from src.core.checker import CheckResult, StatusResult


@dataclass
class ProcessingStats:
    """Statistics for processing."""
    total_urls: int = 0
    processed: int = 0
    active: int = 0
    inactive: int = 0
    errors: int = 0
    processing_rate: float = 0.0
    elapsed_time: float = 0.0
    start_time: float = 0.0


class DesktopBatchProcessor(BatchProcessor):
    """Extended BatchProcessor with progress callbacks for desktop GUI."""

    def __init__(self, config: BatchConfig, progress_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(config)
        self.progress_queue = progress_queue
        self.stop_event = stop_event
        self.stats = ProcessingStats()
        self.last_update_time = 0.0

    async def process_file_with_progress(
        self,
        input_file: Path,
        output_file: Path,
        url_column: str = 'url'
    ):
        """
        Process file with progress updates.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            url_column: Name of column containing URLs

        Returns:
            ProcessingStats object
        """
        self.logger.info(f"Starting desktop batch processing: {input_file} -> {output_file}")

        try:
            # Count total URLs
            url_count = await self._count_urls(input_file, url_column)
            self.stats.total_urls = url_count
            self.stats.start_time = time.time()

            # Send started message
            self._send_progress("started", {
                "total_urls": url_count
            })

            # Process batches
            batch_num = 0
            async for batch_urls in self._read_batches(input_file, url_column):
                batch_num += 1

                # Check for stop signal
                if self.stop_event.is_set():
                    self._send_progress("stopped", {})
                    break

                # Process batch
                results = await self.checker.check_websites_batch(batch_urls)

                # Update statistics
                self._update_stats(results)

                # Send batch progress
                self._send_batch_progress(batch_num)

                # Save results
                await self._save_results(results, output_file, append=batch_num > 1)

                await asyncio.sleep(0.01)  # Small delay for responsiveness

            # Send completion
            self.stats.elapsed_time = time.time() - self.stats.start_time
            self._send_progress("complete", {
                "stats": asdict(self.stats)
            })

            return self.stats

        except Exception as e:
            self.logger.exception("Error in desktop batch processing")
            self._send_progress("error", {
                "message": str(e),
                "exception": str(type(e).__name__)
            })
            raise

        finally:
            await self.checker.close()

    async def _count_urls(self, input_file: Path, url_column: str) -> int:
        """Count total URLs in file."""
        import pandas as pd

        try:
            if input_file.suffix.lower() == '.csv':
                df = pd.read_csv(input_file)
            else:
                df = pd.read_excel(input_file)

            if url_column not in df.columns:
                raise ValueError(f"Column '{url_column}' not found in file")

            return len(df)

        except Exception as e:
            raise Exception(f"Error counting URLs: {str(e)}")

    async def _read_batches(self, input_file: Path, url_column: str):
        """Read file in batches."""
        import pandas as pd

        try:
            if input_file.suffix.lower() == '.csv':
                df = pd.read_csv(input_file)
            else:
                df = pd.read_excel(input_file)

            if url_column not in df.columns:
                raise ValueError(f"Column '{url_column}' not found in file")

            urls = df[url_column].tolist()

            # Yield batches
            for i in range(0, len(urls), self.config.batch_size):
                batch = urls[i:i + self.config.batch_size]
                yield batch

        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    async def _save_results(self, results: list, output_file: Path, append: bool = False):
        """Save results to file."""
        import pandas as pd

        try:
            # Convert results to dictionaries
            results_data = []
            for result in results:
                result_dict = {
                    'url': result.url,
                    'status': result.status_result.value if hasattr(result.status_result, 'value') else str(result.status_result),
                    'status_code': result.status_code if result.status_code else '',
                    'response_time': result.response_time * 1000 if result.response_time else 0,  # Convert to ms
                    'error': result.error_message if result.error_message else '',
                    'final_url': result.final_url if result.final_url else result.url
                }
                results_data.append(result_dict)

            df = pd.DataFrame(results_data)

            # Save based on format
            if output_file.suffix.lower() == '.csv':
                mode = 'a' if append else 'w'
                header = not append
                df.to_csv(output_file, mode=mode, header=header, index=False)
            else:
                # For Excel, we need to handle appending differently
                if append and output_file.exists():
                    existing_df = pd.read_excel(output_file)
                    df = pd.concat([existing_df, df], ignore_index=True)
                df.to_excel(output_file, index=False)

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")

    def _update_stats(self, results: list):
        """Update statistics from batch results."""
        for result in results:
            self.stats.processed += 1

            status = result.status_result if hasattr(result, 'status_result') else None

            if status == StatusResult.ACTIVE:
                self.stats.active += 1
            elif status == StatusResult.INACTIVE:
                self.stats.inactive += 1
            else:
                self.stats.errors += 1

        # Calculate rate
        elapsed = time.time() - self.stats.start_time
        if elapsed > 0:
            self.stats.processing_rate = self.stats.processed / elapsed
        self.stats.elapsed_time = elapsed

    def _send_batch_progress(self, batch_num: int):
        """Send batch completion progress."""
        # Throttle updates to max 10/sec
        current_time = time.time()
        if current_time - self.last_update_time < 0.1:
            return
        self.last_update_time = current_time

        # Calculate progress percentage
        progress = (self.stats.processed / self.stats.total_urls * 100) if self.stats.total_urls > 0 else 0

        # Calculate ETA
        if self.stats.processing_rate > 0:
            remaining = self.stats.total_urls - self.stats.processed
            eta = remaining / self.stats.processing_rate
        else:
            eta = -1

        self._send_progress("batch_complete", {
            "batch_num": batch_num,
            "processed": self.stats.processed,
            "total": self.stats.total_urls,
            "active": self.stats.active,
            "inactive": self.stats.inactive,
            "errors": self.stats.errors,
            "processing_rate": self.stats.processing_rate,
            "elapsed_time": self.stats.elapsed_time,
            "eta": eta,
            "progress": progress
        })

    def _send_progress(self, msg_type: str, data: dict):
        """Send progress message to queue."""
        try:
            self.progress_queue.put({
                "type": msg_type,
                "data": data,
                "timestamp": time.time()
            }, block=False)
        except queue.Full:
            pass  # Skip if queue is full


class ProcessController:
    """Controller for managing URL processing."""

    def __init__(self):
        self.progress_queue = queue.Queue(maxsize=100)
        self.stop_event = threading.Event()
        self.processing_thread: Optional[threading.Thread] = None
        self.is_processing = False

        # Callbacks
        self.on_progress_callback: Optional[Callable[[dict], None]] = None
        self.on_complete_callback: Optional[Callable[[dict], None]] = None
        self.on_error_callback: Optional[Callable[[str], None]] = None

    def start_processing(
        self,
        input_file: Path,
        output_file: Path,
        config: dict
    ):
        """
        Start processing URLs in background thread.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            config: Configuration dictionary
        """
        if self.is_processing:
            raise RuntimeError("Processing already in progress")

        # Clear stop event
        self.stop_event.clear()

        # Create batch config
        batch_config = BatchConfig(
            batch_size=config.get('batch_size', 1000),
            max_concurrent=config.get('concurrent', 100),
            timeout=config.get('timeout', 10),
            retry_count=config.get('retry_count', 2),
            include_inactive=config.get('include_inactive', True),
            include_errors=config.get('include_errors', False),
            memory_efficient=True,
            verify_ssl=config.get('verify_ssl', True)
        )

        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_in_thread,
            args=(input_file, output_file, config.get('url_column', 'url'), batch_config),
            daemon=True
        )
        self.is_processing = True
        self.processing_thread.start()

    def _process_in_thread(
        self,
        input_file: Path,
        output_file: Path,
        url_column: str,
        config: BatchConfig
    ):
        """Run processing in background thread."""
        try:
            # Create processor
            processor = DesktopBatchProcessor(config, self.progress_queue, self.stop_event)

            # Run async processing
            asyncio.run(
                processor.process_file_with_progress(input_file, output_file, url_column)
            )

        except Exception as e:
            self.progress_queue.put({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": time.time()
            })

        finally:
            self.is_processing = False

    def stop_processing(self):
        """Stop processing."""
        self.stop_event.set()

    def get_progress_update(self) -> Optional[dict]:
        """Get progress update from queue (non-blocking)."""
        try:
            return self.progress_queue.get_nowait()
        except queue.Empty:
            return None

    def is_running(self) -> bool:
        """Check if processing is running."""
        return self.is_processing
