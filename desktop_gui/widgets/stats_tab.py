"""Statistics tab widget for displaying detailed statistics."""

import tkinter as tk
from tkinter import ttk, scrolledtext
from desktop_gui.resources.styles import FONTS
from desktop_gui.utils.formatters import format_time, format_rate, format_number, format_percentage


class StatsTab(ttk.Frame):
    """Tab displaying detailed statistics and summary."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._build_ui()

    def _build_ui(self):
        """Build the stats tab UI."""
        # Scrolled text widget for displaying statistics
        self.stats_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=FONTS["monospace"],
            state=tk.DISABLED,
            padx=20,
            pady=20
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure tags for formatting
        self.stats_text.tag_configure("header", font=("Arial", 12, "bold"), spacing1=10)
        self.stats_text.tag_configure("subheader", font=("Arial", 10, "bold"), spacing1=5)
        self.stats_text.tag_configure("normal", font=("Courier New", 10))

        # Set initial content
        self._set_initial_content()

    def _set_initial_content(self):
        """Set initial statistics content."""
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "No statistics available yet.\n\n")
        self.stats_text.insert(tk.END, "Start processing URLs to see detailed statistics here.")
        self.stats_text.configure(state=tk.DISABLED)

    def update_statistics(self, stats: dict):
        """
        Update statistics display.

        Args:
            stats: Dictionary containing statistics
        """
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)

        # Processing Summary
        self.stats_text.insert(tk.END, "PROCESSING SUMMARY\n", "header")
        self.stats_text.insert(tk.END, "=" * 80 + "\n\n", "normal")

        total = stats.get("total", 0)
        processed = stats.get("processed", 0)
        active = stats.get("active", 0)
        inactive = stats.get("inactive", 0)
        errors = stats.get("errors", 0)

        self.stats_text.insert(tk.END, f"Total URLs:              {format_number(total)}\n", "normal")
        self.stats_text.insert(tk.END, f"Processed:               {format_number(processed)}\n", "normal")
        self.stats_text.insert(tk.END, f"Active:                  {format_number(active)}\n", "normal")
        self.stats_text.insert(tk.END, f"Inactive:                {format_number(inactive)}\n", "normal")
        self.stats_text.insert(tk.END, f"Errors:                  {format_number(errors)}\n", "normal")

        # Success Rate
        self.stats_text.insert(tk.END, "\nSUCCESS RATE\n", "header")
        self.stats_text.insert(tk.END, "=" * 80 + "\n\n", "normal")

        if processed > 0:
            success_rate = (active / processed) * 100
            error_rate = (errors / processed) * 100
            inactive_rate = (inactive / processed) * 100

            self.stats_text.insert(tk.END, f"Active Rate:             {success_rate:.1f}%\n", "normal")
            self.stats_text.insert(tk.END, f"Inactive Rate:           {inactive_rate:.1f}%\n", "normal")
            self.stats_text.insert(tk.END, f"Error Rate:              {error_rate:.1f}%\n", "normal")
        else:
            self.stats_text.insert(tk.END, "No data available yet.\n", "normal")

        # Performance Metrics
        self.stats_text.insert(tk.END, "\nPERFORMANCE METRICS\n", "header")
        self.stats_text.insert(tk.END, "=" * 80 + "\n\n", "normal")

        elapsed = stats.get("elapsed_time", 0)
        rate = stats.get("processing_rate", 0)

        self.stats_text.insert(tk.END, f"Elapsed Time:            {format_time(elapsed)}\n", "normal")
        self.stats_text.insert(tk.END, f"Processing Rate:         {format_rate(rate)}\n", "normal")

        if processed > 0 and elapsed > 0:
            avg_time = (elapsed / processed) * 1000  # ms per URL
            self.stats_text.insert(tk.END, f"Average Time per URL:    {avg_time:.2f} ms\n", "normal")

        # Error Breakdown
        error_breakdown = stats.get("error_breakdown", {})
        if error_breakdown:
            self.stats_text.insert(tk.END, "\nERROR BREAKDOWN\n", "header")
            self.stats_text.insert(tk.END, "=" * 80 + "\n\n", "normal")

            for error_type, count in error_breakdown.items():
                self.stats_text.insert(tk.END, f"{error_type:30s} {format_number(count)}\n", "normal")

        # Configuration Used
        config = stats.get("config", {})
        if config:
            self.stats_text.insert(tk.END, "\nCONFIGURATION\n", "header")
            self.stats_text.insert(tk.END, "=" * 80 + "\n\n", "normal")

            self.stats_text.insert(tk.END, f"Batch Size:              {config.get('batch_size', 'N/A')}\n", "normal")
            self.stats_text.insert(tk.END, f"Concurrent Requests:     {config.get('concurrent', 'N/A')}\n", "normal")
            self.stats_text.insert(tk.END, f"Timeout:                 {config.get('timeout', 'N/A')} seconds\n", "normal")
            self.stats_text.insert(tk.END, f"Retry Count:             {config.get('retry_count', 'N/A')}\n", "normal")
            self.stats_text.insert(tk.END, f"SSL Verification:        {'Enabled' if config.get('verify_ssl', True) else 'Disabled'}\n", "normal")

        self.stats_text.configure(state=tk.DISABLED)

    def clear(self):
        """Clear statistics display."""
        self._set_initial_content()
