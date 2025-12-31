"""
Integration Tests for Batch Processing

Tests the end-to-end batch processing workflow including file I/O,
URL checking, result generation, and export in multiple formats.
"""

import pytest
import asyncio
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.batch import BatchProcessor, BatchConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_csv(temp_dir: Path) -> Path:
    """Create a sample CSV file with test URLs."""
    csv_file = temp_dir / "test_urls.csv"
    df = pd.DataFrame({
        "url": [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.python.org",
        ]
    })
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_txt(temp_dir: Path) -> Path:
    """Create a sample text file with test URLs."""
    txt_file = temp_dir / "test_urls.txt"
    urls = [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.python.org",
    ]
    txt_file.write_text("\n".join(urls))
    return txt_file


@pytest.fixture
def sample_excel(temp_dir: Path) -> Path:
    """Create a sample Excel file with test URLs."""
    excel_file = temp_dir / "test_urls.xlsx"
    df = pd.DataFrame({
        "url": [
            "https://www.google.com",
            "https://www.github.com",
        ]
    })
    df.to_excel(excel_file, index=False, engine='openpyxl')
    return excel_file


@pytest.fixture
def batch_config() -> BatchConfig:
    """Create a batch configuration for testing."""
    return BatchConfig(
        batch_size=2,
        max_concurrent=3,
        timeout=10,
        retry_count=1,
        verify_ssl=True,
        save_interval=1,
        memory_efficient=False,  # Disable for testing to get total counts
        include_inactive=True,
        include_errors=True
    )


class TestBatchProcessingCSV:
    """Test batch processing with CSV files."""

    @pytest.mark.asyncio
    async def test_process_csv_file(self, sample_csv: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test processing a CSV file with mixed results."""
        output_file = temp_dir / "results.csv"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Verify output file exists
        assert output_file.exists()

        # Verify stats were returned
        assert stats.total_input_urls == 3

        # Load and verify results
        results_df = pd.read_csv(output_file)

        # Check all URLs were processed
        assert len(results_df) >= 1  # At least some results

        # Check required columns from CheckResult
        expected_columns = ["url", "status_code"]
        for col in expected_columns:
            assert col in results_df.columns

        # Verify we have some successful checks
        successful = results_df[results_df["status_code"].isin([200, 301, 302, 303, 307, 308])]
        assert len(successful) >= 1  # At least one should work

    @pytest.mark.asyncio
    async def test_process_csv_statistics(self, sample_csv: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test that processing statistics are collected correctly."""
        output_file = temp_dir / "results.csv"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Verify statistics
        assert stats.total_input_urls == 3
        assert stats.batches_processed > 0
        assert stats.total_batches > 0
        assert stats.elapsed_time > 0

        # Verify at least some websites were processed
        total_processed = stats.active_websites + stats.inactive_websites + stats.error_websites
        assert total_processed == 3


class TestBatchProcessingJSON:
    """Test batch processing with JSON output."""

    @pytest.mark.asyncio
    async def test_process_csv_to_json(self, sample_csv: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test exporting results to JSON format."""
        output_file = temp_dir / "results.json"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Verify output file exists
        assert output_file.exists()

        # Verify stats
        assert stats.total_input_urls == 3

        # Load and verify JSON
        import json
        with open(output_file, 'r') as f:
            results = json.load(f)

        assert isinstance(results, list)
        assert len(results) >= 1

        # Verify JSON structure
        if results:
            assert "url" in results[0]
            assert "status_code" in results[0]


class TestBatchProcessingExcel:
    """Test batch processing with Excel files."""

    @pytest.mark.asyncio
    async def test_process_excel_input(self, sample_excel: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test processing Excel input file."""
        output_file = temp_dir / "results.csv"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_excel),
            output_file=Path(output_file)
        )

        # Verify output
        assert output_file.exists()
        assert stats.total_input_urls == 2

        results_df = pd.read_csv(output_file)
        assert len(results_df) >= 1

    @pytest.mark.asyncio
    async def test_process_to_excel_output(self, sample_csv: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test exporting results to Excel format."""
        output_file = temp_dir / "results.xlsx"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Verify output file exists
        assert output_file.exists()
        assert stats.total_input_urls == 3

        # Load and verify Excel
        results_df = pd.read_excel(output_file, engine='openpyxl')
        assert len(results_df) >= 1


class TestBatchProcessingText:
    """Test batch processing with text files."""

    @pytest.mark.asyncio
    async def test_process_text_file(self, sample_txt: Path, temp_dir: Path, batch_config: BatchConfig):
        """Test processing plain text file with URLs."""
        output_file = temp_dir / "results.csv"

        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(sample_txt),
            output_file=Path(output_file)
        )

        # Verify output
        assert output_file.exists()

        results_df = pd.read_csv(output_file)
        assert len(results_df) >= 1


class TestBatchProcessingErrorHandling:
    """Test error handling in batch processing."""

    @pytest.mark.asyncio
    async def test_invalid_input_file(self, temp_dir: Path, batch_config: BatchConfig):
        """Test handling of non-existent input file."""
        output_file = temp_dir / "results.csv"
        processor = BatchProcessor(batch_config)

        with pytest.raises((FileNotFoundError, OSError)):
            await processor.process_file(
                input_file=Path(temp_dir / "nonexistent.csv"),
                output_file=Path(output_file)
            )

    @pytest.mark.asyncio
    async def test_empty_input_file(self, temp_dir: Path, batch_config: BatchConfig):
        """Test handling of empty input file."""
        empty_csv = temp_dir / "empty.csv"
        empty_csv.write_text("url\n")  # Just header

        output_file = temp_dir / "results.csv"
        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(empty_csv),
            output_file=Path(output_file)
        )

        # Should complete without errors
        assert stats.total_input_urls == 0

    @pytest.mark.asyncio
    async def test_malformed_urls(self, temp_dir: Path, batch_config: BatchConfig):
        """Test handling of malformed URLs."""
        malformed_csv = temp_dir / "malformed.csv"
        df = pd.DataFrame({
            "url": [
                "not-a-url",
                "https://google.com",
            ]
        })
        df.to_csv(malformed_csv, index=False)

        output_file = temp_dir / "results.csv"
        processor = BatchProcessor(batch_config)

        stats = await processor.process_file(
            input_file=Path(malformed_csv),
            output_file=Path(output_file)
        )

        # Should process all URLs, even if some fail
        assert output_file.exists()
        assert stats.total_input_urls == 2

        results_df = pd.read_csv(output_file)
        # Results may vary based on how malformed URLs are handled
        assert len(results_df) >= 1


class TestBatchProcessingConfig:
    """Test different batch configuration options."""

    @pytest.mark.asyncio
    async def test_include_inactive_false(self, sample_csv: Path, temp_dir: Path):
        """Test filtering out inactive websites."""
        config = BatchConfig(
            batch_size=10,
            max_concurrent=3,
            timeout=10,
            include_inactive=False,  # Filter out inactive sites
            include_errors=False
        )

        output_file = temp_dir / "results.csv"
        processor = BatchProcessor(config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Results should only include active sites (200-level responses)
        if output_file.exists():
            results_df = pd.read_csv(output_file)
            # All results should be successful (if any)
            if len(results_df) > 0:
                assert all(results_df["status_code"].between(200, 399))

    @pytest.mark.asyncio
    async def test_ssl_verification_disabled(self, sample_csv: Path, temp_dir: Path):
        """Test with SSL verification disabled."""
        config = BatchConfig(
            batch_size=10,
            max_concurrent=3,
            timeout=10,
            verify_ssl=False,  # Disable SSL verification
            memory_efficient=False  # Disable to get total count
        )

        output_file = temp_dir / "results.csv"
        processor = BatchProcessor(config)

        stats = await processor.process_file(
            input_file=Path(sample_csv),
            output_file=Path(output_file)
        )

        # Should complete successfully
        assert output_file.exists()
        assert stats.total_input_urls == 3
