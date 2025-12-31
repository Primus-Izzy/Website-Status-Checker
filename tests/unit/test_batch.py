"""
Unit Tests for Batch Processor

Tests for batch processing functionality including file reading, result saving,
and statistics tracking.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.core.batch import (
    BatchProcessor,
    BatchConfig,
    ProcessingStats
)
from src.core.checker import CheckResult, StatusResult


@pytest.mark.unit
class TestBatchConfig:
    """Test BatchConfig functionality."""

    def test_default_values(self):
        """Test default batch configuration values."""
        config = BatchConfig()

        assert config.batch_size == 1000
        assert config.max_concurrent == 100
        assert config.timeout == 10
        assert config.retry_count == 2
        assert config.verify_ssl is True

    def test_custom_values(self):
        """Test custom batch configuration."""
        config = BatchConfig(
            batch_size=500,
            max_concurrent=50,
            timeout=15,
            verify_ssl=False
        )

        assert config.batch_size == 500
        assert config.max_concurrent == 50
        assert config.timeout == 15
        assert config.verify_ssl is False


@pytest.mark.unit
class TestProcessingStats:
    """Test ProcessingStats functionality."""

    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = ProcessingStats()

        assert stats.total_input_urls == 0
        assert stats.batches_processed == 0
        assert stats.active_websites == 0

    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation."""
        stats = ProcessingStats(
            total_batches=10,
            batches_processed=5
        )

        assert stats.completion_percentage == 50.0

    def test_completion_percentage_zero_division(self):
        """Test completion percentage with zero total."""
        stats = ProcessingStats()

        assert stats.completion_percentage == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = ProcessingStats(
            active_websites=75,
            inactive_websites=20,
            error_websites=5
        )

        assert stats.success_rate == 75.0

    def test_success_rate_zero_division(self):
        """Test success rate with no websites processed."""
        stats = ProcessingStats()

        assert stats.success_rate == 0.0


@pytest.mark.unit
class TestBatchProcessorInitialization:
    """Test BatchProcessor initialization."""

    def test_initialization(self):
        """Test processor initialization."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        assert processor.config == config
        assert processor.checker is not None
        assert processor.stats is not None

    def test_checker_inherits_config(self):
        """Test that checker inherits configuration."""
        config = BatchConfig(
            max_concurrent=50,
            timeout=15,
            verify_ssl=False
        )
        processor = BatchProcessor(config)

        assert processor.checker.max_concurrent == 50
        assert processor.checker.timeout == 15
        assert processor.checker.verify_ssl is False


@pytest.mark.unit
class TestFileReading:
    """Test file reading functionality."""

    def test_read_csv_file(self, sample_csv_file):
        """Test reading CSV file."""
        config = BatchConfig(batch_size=10)
        processor = BatchProcessor(config)

        batches = list(processor.read_input_file(sample_csv_file))

        assert len(batches) > 0
        assert all(isinstance(batch, list) for batch in batches)
        assert all(isinstance(url, str) for batch in batches for url in batch)

    def test_read_csv_with_custom_column(self, temp_dir):
        """Test reading CSV with custom column name."""
        csv_file = temp_dir / "custom.csv"
        df = pd.DataFrame({
            "website": ["https://example1.com", "https://example2.com"]
        })
        df.to_csv(csv_file, index=False)

        config = BatchConfig()
        processor = BatchProcessor(config)

        batches = list(processor.read_input_file(csv_file, url_column="website"))

        assert len(batches) == 1
        assert len(batches[0]) == 2

    def test_read_csv_batching(self, temp_dir):
        """Test that CSV is properly batched."""
        csv_file = temp_dir / "large.csv"
        # Create 25 URLs with batch size of 10
        urls = [f"https://example{i}.com" for i in range(25)]
        df = pd.DataFrame({"url": urls})
        df.to_csv(csv_file, index=False)

        config = BatchConfig(batch_size=10)
        processor = BatchProcessor(config)

        batches = list(processor.read_input_file(csv_file))

        # Should create 3 batches: 10, 10, 5
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5

    def test_read_nonexistent_file(self):
        """Test reading non-existent file raises error."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        with pytest.raises(Exception):
            list(processor.read_input_file(Path("nonexistent.csv")))

    def test_read_file_missing_column(self, temp_dir):
        """Test reading file with missing URL column."""
        csv_file = temp_dir / "no_url.csv"
        df = pd.DataFrame({"other_column": ["value1", "value2"]})
        df.to_csv(csv_file, index=False)

        config = BatchConfig()
        processor = BatchProcessor(config)

        batches = list(processor.read_input_file(csv_file, url_column="url"))

        # Should handle gracefully (empty or error logged)
        assert len(batches) == 0


@pytest.mark.unit
class TestResultSaving:
    """Test result saving functionality."""

    def test_save_results_csv(self, temp_dir, mock_check_result):
        """Test saving results to CSV."""
        config = BatchConfig(output_format='csv')
        processor = BatchProcessor(config)

        output_file = temp_dir / "results.csv"
        results = [mock_check_result]

        processor.save_results_batch(results, output_file, append=False)

        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 1
        assert "url" in df.columns

    def test_save_results_append(self, temp_dir, mock_check_result):
        """Test appending results to existing file."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        output_file = temp_dir / "results.csv"

        # Save first batch
        processor.save_results_batch([mock_check_result], output_file, append=False)

        # Append second batch
        processor.save_results_batch([mock_check_result], output_file, append=True)

        df = pd.read_csv(output_file)
        assert len(df) == 2

    def test_save_results_filters_inactive(self, temp_dir, mock_check_result, mock_error_result):
        """Test that inactive results are filtered when configured."""
        config = BatchConfig(include_inactive=False, include_errors=False)
        processor = BatchProcessor(config)

        output_file = temp_dir / "results.csv"
        results = [mock_check_result, mock_error_result]  # One active, one error

        processor.save_results_batch(results, output_file, append=False)

        df = pd.read_csv(output_file)
        assert len(df) == 1  # Only active result

    def test_save_results_includes_all(self, temp_dir, mock_check_result, mock_error_result):
        """Test that all results are saved when configured."""
        config = BatchConfig(include_inactive=True, include_errors=True)
        processor = BatchProcessor(config)

        output_file = temp_dir / "results.csv"
        results = [mock_check_result, mock_error_result]

        processor.save_results_batch(results, output_file, append=False)

        df = pd.read_csv(output_file)
        assert len(df) == 2


@pytest.mark.unit
class TestStatsUpdating:
    """Test statistics updating functionality."""

    def test_update_stats_active(self, mock_check_result):
        """Test stats update for active websites."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        processor.update_stats([mock_check_result])

        assert processor.stats.active_websites == 1
        assert processor.stats.inactive_websites == 0
        assert processor.stats.error_websites == 0

    def test_update_stats_error(self, mock_error_result):
        """Test stats update for error results."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        processor.update_stats([mock_error_result])

        assert processor.stats.active_websites == 0
        assert processor.stats.error_websites == 1

    def test_update_stats_processing_rate(self, mock_check_result):
        """Test processing rate calculation."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        # Update stats with some results
        processor.update_stats([mock_check_result] * 10)

        assert processor.stats.processing_rate > 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchProcessing:
    """Test batch processing workflow."""

    async def test_process_dataframe(self, temp_dir):
        """Test processing a DataFrame directly."""
        config = BatchConfig(batch_size=5)
        processor = BatchProcessor(config)

        # Create test DataFrame
        df = pd.DataFrame({
            "url": [f"https://example{i}.com" for i in range(10)]
        })

        output_file = temp_dir / "results.csv"

        # Mock the checker
        with patch.object(processor.checker, 'check_websites_batch') as mock_check:
            mock_check.return_value = [Mock(status_result=StatusResult.ACTIVE)] * 5

            stats = await processor.process_dataframe(df, output_file)

            assert stats.batches_processed == 2  # 10 URLs / 5 batch size
            assert mock_check.call_count == 2

    async def test_process_file_integration(self, sample_csv_file, temp_dir):
        """Test processing a file end-to-end."""
        config = BatchConfig(batch_size=10)
        processor = BatchProcessor(config)

        output_file = temp_dir / "results.csv"

        # Mock the checker to avoid actual HTTP requests
        with patch.object(processor.checker, 'check_websites_batch') as mock_check:
            mock_result = Mock(status_result=StatusResult.ACTIVE)
            mock_check.return_value = [mock_result] * 5

            stats = await processor.process_file(sample_csv_file, output_file)

            assert stats.batches_processed > 0
            assert mock_check.called


@pytest.mark.unit
class TestReportGeneration:
    """Test report generation functionality."""

    def test_generate_report(self, temp_dir):
        """Test generating processing report."""
        config = BatchConfig()
        processor = BatchProcessor(config)

        # Set some stats
        processor.stats.total_input_urls = 100
        processor.stats.active_websites = 75
        processor.stats.inactive_websites = 20
        processor.stats.error_websites = 5

        report_file = temp_dir / "report.json"
        report = processor.generate_report(report_file)

        assert report_file.exists()
        assert "processing_summary" in report
        assert report["processing_summary"]["total_input_urls"] == 100
        assert report["processing_summary"]["active_websites"] == 75
