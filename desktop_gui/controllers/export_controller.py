"""Export controller for exporting results to various formats."""

import json
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Dict, Optional
import pandas as pd


class ExportController:
    """Controller for exporting results."""

    def export_results(
        self,
        results: List[Dict],
        initial_filename: str = "results"
    ) -> bool:
        """
        Export results to a file (user selects format and location).

        Args:
            results: List of result dictionaries
            initial_filename: Initial filename suggestion

        Returns:
            True if export successful, False otherwise
        """
        if not results:
            messagebox.showwarning(
                "No Results",
                "No results to export. Please process some URLs first."
            )
            return False

        # Ask user for file location and format
        filetypes = [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]

        filepath = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            initialfile=initial_filename,
            filetypes=filetypes
        )

        if not filepath:
            return False

        file_path = Path(filepath)

        try:
            # Determine format from extension
            if file_path.suffix.lower() == '.csv':
                success = self.export_to_csv(results, file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                success = self.export_to_excel(results, file_path)
            elif file_path.suffix.lower() == '.json':
                success = self.export_to_json(results, file_path)
            else:
                # Default to CSV
                success = self.export_to_csv(results, file_path)

            if success:
                messagebox.showinfo(
                    "Export Successful",
                    f"Results exported successfully to:\n{file_path}"
                )
                return True
            else:
                return False

        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Failed to export results:\n{str(e)}"
            )
            return False

    def export_to_csv(self, results: List[Dict], file_path: Path) -> bool:
        """
        Export results to CSV file.

        Args:
            results: List of result dictionaries
            file_path: Path to save CSV file

        Returns:
            True if successful
        """
        try:
            df = pd.DataFrame(results)

            # Reorder columns if they exist
            desired_columns = ['url', 'status', 'status_code', 'response_time', 'error', 'final_url']
            columns = [col for col in desired_columns if col in df.columns]

            # Add any remaining columns
            remaining_columns = [col for col in df.columns if col not in columns]
            columns.extend(remaining_columns)

            df = df[columns]

            # Save to CSV
            df.to_csv(file_path, index=False, encoding='utf-8')

            return True

        except Exception as e:
            raise Exception(f"Error exporting to CSV: {str(e)}")

    def export_to_excel(self, results: List[Dict], file_path: Path) -> bool:
        """
        Export results to Excel file.

        Args:
            results: List of result dictionaries
            file_path: Path to save Excel file

        Returns:
            True if successful
        """
        try:
            df = pd.DataFrame(results)

            # Reorder columns if they exist
            desired_columns = ['url', 'status', 'status_code', 'response_time', 'error', 'final_url']
            columns = [col for col in desired_columns if col in df.columns]

            # Add any remaining columns
            remaining_columns = [col for col in df.columns if col not in columns]
            columns.extend(remaining_columns)

            df = df[columns]

            # Save to Excel
            df.to_excel(file_path, index=False, engine='openpyxl')

            return True

        except Exception as e:
            raise Exception(f"Error exporting to Excel: {str(e)}")

    def export_to_json(self, results: List[Dict], file_path: Path) -> bool:
        """
        Export results to JSON file.

        Args:
            results: List of result dictionaries
            file_path: Path to save JSON file

        Returns:
            True if successful
        """
        try:
            # Convert any non-serializable objects
            serializable_results = []
            for result in results:
                serializable_result = {}
                for key, value in result.items():
                    # Convert to string if not JSON serializable
                    try:
                        json.dumps(value)
                        serializable_result[key] = value
                    except (TypeError, ValueError):
                        serializable_result[key] = str(value)
                serializable_results.append(serializable_result)

            # Save to JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            raise Exception(f"Error exporting to JSON: {str(e)}")
