"""File controller for handling file operations."""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Callable, List
import pandas as pd


class FileController:
    """Controller for file selection and validation."""

    def __init__(self):
        self.current_file: Optional[Path] = None
        self.column_names: List[str] = []
        self.total_rows: int = 0

    def browse_file(
        self,
        on_success: Optional[Callable[[Path, List[str], int], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> Optional[Path]:
        """
        Open file dialog and select a file.

        Args:
            on_success: Callback for successful file selection (file_path, columns, row_count)
            on_error: Callback for errors

        Returns:
            Selected file path or None
        """
        filetypes = [
            ("All Supported", "*.csv;*.xlsx;*.xls;*.txt"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx;*.xls"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=filetypes
        )

        if not filepath:
            return None

        file_path = Path(filepath)

        # Validate in background thread
        def validate_and_load():
            try:
                is_valid, error_msg = self.validate_file(file_path)
                if not is_valid:
                    if on_error:
                        on_error(error_msg)
                    return

                # Extract metadata
                columns, row_count = self.extract_file_metadata(file_path)

                # Store current file info
                self.current_file = file_path
                self.column_names = columns
                self.total_rows = row_count

                # Call success callback
                if on_success:
                    on_success(file_path, columns, row_count)

            except Exception as e:
                if on_error:
                    on_error(f"Error loading file: {str(e)}")

        # Run validation in background thread
        thread = threading.Thread(target=validate_and_load, daemon=True)
        thread.start()

        return file_path

    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if not file_path.is_file():
            return False, f"Path is not a file: {file_path}"

        if file_path.suffix.lower() not in ['.csv', '.xlsx', '.xls', '.txt']:
            return False, f"Unsupported file format: {file_path.suffix}"

        # Try to read the file to ensure it's valid
        try:
            if file_path.suffix.lower() == '.csv' or file_path.suffix.lower() == '.txt':
                # Try reading first few rows
                df = pd.read_csv(file_path, nrows=5)
            else:
                # Excel file
                df = pd.read_excel(file_path, nrows=5)

            if df.empty:
                return False, "File is empty"

        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

        return True, None

    def extract_file_metadata(self, file_path: Path) -> tuple[List[str], int]:
        """
        Extract column names and row count from file.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (column_names, row_count)
        """
        try:
            if file_path.suffix.lower() == '.csv' or file_path.suffix.lower() == '.txt':
                # Read CSV
                df = pd.read_csv(file_path)
            else:
                # Read Excel
                df = pd.read_excel(file_path)

            columns = df.columns.tolist()
            row_count = len(df)

            return columns, row_count

        except Exception as e:
            raise Exception(f"Error extracting file metadata: {str(e)}")

    def get_current_file(self) -> Optional[Path]:
        """Get currently selected file."""
        return self.current_file

    def get_column_names(self) -> List[str]:
        """Get column names from current file."""
        return self.column_names

    def get_total_rows(self) -> int:
        """Get total number of rows in current file."""
        return self.total_rows

    def has_column(self, column_name: str) -> bool:
        """Check if current file has a specific column."""
        return column_name in self.column_names
