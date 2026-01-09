"""Progress tab widget for displaying processing progress."""

import tkinter as tk
from tkinter import ttk
from desktop_gui.resources.styles import COLORS, FONTS, SPACING
from desktop_gui.utils.formatters import format_time, format_rate, format_number


class ProgressTab(ttk.Frame):
    """Tab displaying progress bar and statistics."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Variables
        self.status_var = tk.StringVar(value="Ready to process...")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.percentage_var = tk.StringVar(value="0%")

        self.total_urls_var = tk.StringVar(value="0")
        self.processed_var = tk.StringVar(value="0")
        self.active_var = tk.StringVar(value="0")
        self.inactive_var = tk.StringVar(value="0")
        self.errors_var = tk.StringVar(value="0")
        self.rate_var = tk.StringVar(value="0.0 URLs/sec")
        self.elapsed_var = tk.StringVar(value="00:00:00")
        self.eta_var = tk.StringVar(value="--:--:--")

        self._build_ui()

    def _build_ui(self):
        """Build the progress tab UI."""
        # Main container with padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Status label
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=FONTS["header"]
        )
        status_label.pack(pady=(0, 20))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=600
        )
        self.progress_bar.pack(pady=(0, 10))

        # Percentage label
        percentage_label = ttk.Label(
            main_frame,
            textvariable=self.percentage_var,
            font=FONTS["label"]
        )
        percentage_label.pack(pady=(0, 30))

        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding=20)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        # Create grid of statistics
        row = 0

        # Total URLs
        ttk.Label(stats_frame, text="Total URLs:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_frame, textvariable=self.total_urls_var, font=FONTS["value"]).grid(
            row=row, column=1, sticky=tk.E, padx=10, pady=5
        )
        row += 1

        # Processed
        ttk.Label(stats_frame, text="Processed:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_frame, textvariable=self.processed_var, font=FONTS["value"]).grid(
            row=row, column=1, sticky=tk.E, padx=10, pady=5
        )
        row += 1

        # Active
        ttk.Label(stats_frame, text="Active:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.active_label = ttk.Label(
            stats_frame,
            textvariable=self.active_var,
            font=FONTS["value"],
            foreground=COLORS["success"]
        )
        self.active_label.grid(row=row, column=1, sticky=tk.E, padx=10, pady=5)
        row += 1

        # Inactive
        ttk.Label(stats_frame, text="Inactive:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.inactive_label = ttk.Label(
            stats_frame,
            textvariable=self.inactive_var,
            font=FONTS["value"],
            foreground=COLORS["warning"]
        )
        self.inactive_label.grid(row=row, column=1, sticky=tk.E, padx=10, pady=5)
        row += 1

        # Errors
        ttk.Label(stats_frame, text="Errors:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.errors_label = ttk.Label(
            stats_frame,
            textvariable=self.errors_var,
            font=FONTS["value"],
            foreground=COLORS["error"]
        )
        self.errors_label.grid(row=row, column=1, sticky=tk.E, padx=10, pady=5)
        row += 1

        # Separator
        ttk.Separator(stats_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=15
        )
        row += 1

        # Processing rate
        ttk.Label(stats_frame, text="Processing Rate:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_frame, textvariable=self.rate_var, font=FONTS["value"]).grid(
            row=row, column=1, sticky=tk.E, padx=10, pady=5
        )
        row += 1

        # Elapsed time
        ttk.Label(stats_frame, text="Elapsed Time:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_frame, textvariable=self.elapsed_var, font=FONTS["value"]).grid(
            row=row, column=1, sticky=tk.E, padx=10, pady=5
        )
        row += 1

        # ETA
        ttk.Label(stats_frame, text="Estimated Time:", font=FONTS["label"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_frame, textvariable=self.eta_var, font=FONTS["value"]).grid(
            row=row, column=1, sticky=tk.E, padx=10, pady=5
        )

        # Configure column weights for proper alignment
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)

    def update_status(self, status: str):
        """Update status message."""
        self.status_var.set(status)

    def update_progress(self, percentage: float):
        """Update progress bar."""
        self.progress_var.set(percentage)
        self.percentage_var.set(f"{percentage:.1f}%")

    def update_statistics(
        self,
        total_urls: int = None,
        processed: int = None,
        active: int = None,
        inactive: int = None,
        errors: int = None,
        rate: float = None,
        elapsed: float = None,
        eta: float = None
    ):
        """Update statistics display."""
        if total_urls is not None:
            self.total_urls_var.set(format_number(total_urls))

        if processed is not None:
            self.processed_var.set(format_number(processed))

        if active is not None:
            self.active_var.set(format_number(active))

        if inactive is not None:
            self.inactive_var.set(format_number(inactive))

        if errors is not None:
            self.errors_var.set(format_number(errors))

        if rate is not None:
            self.rate_var.set(format_rate(rate))

        if elapsed is not None:
            self.elapsed_var.set(format_time(elapsed))

        if eta is not None:
            self.eta_var.set(format_time(eta))

    def reset(self):
        """Reset all progress and statistics."""
        self.status_var.set("Ready to process...")
        self.progress_var.set(0.0)
        self.percentage_var.set("0%")
        self.total_urls_var.set("0")
        self.processed_var.set("0")
        self.active_var.set("0")
        self.inactive_var.set("0")
        self.errors_var.set("0")
        self.rate_var.set("0.0 URLs/sec")
        self.elapsed_var.set("00:00:00")
        self.eta_var.set("--:--:--")
