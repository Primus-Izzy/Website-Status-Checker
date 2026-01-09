"""Control panel widget for file selection and configuration."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from desktop_gui.resources.styles import COLORS, FONTS, SPACING, CONTROL_PANEL


class ControlPanel(ttk.Frame):
    """Left sidebar control panel with file selection and configuration."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Callbacks
        self.on_browse_callback: Optional[Callable] = None
        self.on_start_callback: Optional[Callable] = None
        self.on_pause_callback: Optional[Callable] = None
        self.on_stop_callback: Optional[Callable] = None
        self.on_export_callback: Optional[Callable] = None

        # Variables
        self.file_path_var = tk.StringVar()
        self.url_column_var = tk.StringVar(value="url")
        self.batch_size_var = tk.IntVar(value=1000)
        self.concurrent_var = tk.IntVar(value=100)
        self.timeout_var = tk.IntVar(value=10)
        self.retry_var = tk.IntVar(value=2)
        self.include_inactive_var = tk.BooleanVar(value=True)
        self.include_errors_var = tk.BooleanVar(value=False)
        self.verify_ssl_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        """Build the control panel UI."""
        self.configure(width=CONTROL_PANEL["width"])

        # File selection section
        file_frame = ttk.LabelFrame(self, text="File Selection", padding=SPACING["padding_medium"])
        file_frame.pack(fill=tk.X, padx=SPACING["padding_medium"], pady=SPACING["padding_medium"])

        ttk.Label(file_frame, text="Input File:").pack(anchor=tk.W)

        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.pack(fill=tk.X, pady=(5, 0))

        self.file_entry = ttk.Entry(file_entry_frame, textvariable=self.file_path_var, state='readonly')
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_button = ttk.Button(file_entry_frame, text="Browse...", command=self._on_browse, width=10)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(file_frame, text="URL Column:").pack(anchor=tk.W, pady=(10, 0))
        self.url_column_entry = ttk.Entry(file_frame, textvariable=self.url_column_var)
        self.url_column_entry.pack(fill=tk.X, pady=(5, 0))

        # Configuration section
        config_frame = ttk.LabelFrame(self, text="Processing Configuration", padding=SPACING["padding_medium"])
        config_frame.pack(fill=tk.X, padx=SPACING["padding_medium"], pady=SPACING["padding_medium"])

        # Batch size
        ttk.Label(config_frame, text="Batch Size (100-10000):").pack(anchor=tk.W)
        self.batch_size_spinbox = ttk.Spinbox(
            config_frame,
            from_=100,
            to=10000,
            textvariable=self.batch_size_var,
            increment=100
        )
        self.batch_size_spinbox.pack(fill=tk.X, pady=(5, 10))

        # Concurrent requests
        ttk.Label(config_frame, text="Concurrent Requests (1-500):").pack(anchor=tk.W)
        self.concurrent_spinbox = ttk.Spinbox(
            config_frame,
            from_=1,
            to=500,
            textvariable=self.concurrent_var,
            increment=10
        )
        self.concurrent_spinbox.pack(fill=tk.X, pady=(5, 10))

        # Timeout
        ttk.Label(config_frame, text="Timeout (seconds, 5-120):").pack(anchor=tk.W)
        self.timeout_spinbox = ttk.Spinbox(
            config_frame,
            from_=5,
            to=120,
            textvariable=self.timeout_var,
            increment=5
        )
        self.timeout_spinbox.pack(fill=tk.X, pady=(5, 10))

        # Retry count
        ttk.Label(config_frame, text="Retry Count (0-10):").pack(anchor=tk.W)
        self.retry_spinbox = ttk.Spinbox(
            config_frame,
            from_=0,
            to=10,
            textvariable=self.retry_var
        )
        self.retry_spinbox.pack(fill=tk.X, pady=(5, 10))

        # Checkboxes
        self.include_inactive_check = ttk.Checkbutton(
            config_frame,
            text="Include Inactive Websites",
            variable=self.include_inactive_var
        )
        self.include_inactive_check.pack(anchor=tk.W, pady=(5, 5))

        self.include_errors_check = ttk.Checkbutton(
            config_frame,
            text="Include Error Websites",
            variable=self.include_errors_var
        )
        self.include_errors_check.pack(anchor=tk.W, pady=(0, 5))

        self.verify_ssl_check = ttk.Checkbutton(
            config_frame,
            text="Verify SSL Certificates",
            variable=self.verify_ssl_var
        )
        self.verify_ssl_check.pack(anchor=tk.W)

        # Control buttons section
        control_frame = ttk.LabelFrame(self, text="Processing Controls", padding=SPACING["padding_medium"])
        control_frame.pack(fill=tk.X, padx=SPACING["padding_medium"], pady=SPACING["padding_medium"])

        self.start_button = ttk.Button(
            control_frame,
            text="Start Processing",
            command=self._on_start,
            state=tk.DISABLED
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5))

        self.pause_button = ttk.Button(
            control_frame,
            text="Pause",
            command=self._on_pause,
            state=tk.DISABLED
        )
        self.pause_button.pack(fill=tk.X, pady=(0, 5))

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop",
            command=self._on_stop,
            state=tk.DISABLED
        )
        self.stop_button.pack(fill=tk.X, pady=(0, 5))

        self.export_button = ttk.Button(
            control_frame,
            text="Export Results...",
            command=self._on_export,
            state=tk.DISABLED
        )
        self.export_button.pack(fill=tk.X)

    def _on_browse(self):
        """Handle browse button click."""
        if self.on_browse_callback:
            self.on_browse_callback()

    def _on_start(self):
        """Handle start button click."""
        if self.on_start_callback:
            self.on_start_callback()

    def _on_pause(self):
        """Handle pause button click."""
        if self.on_pause_callback:
            self.on_pause_callback()

    def _on_stop(self):
        """Handle stop button click."""
        if self.on_stop_callback:
            self.on_stop_callback()

    def _on_export(self):
        """Handle export button click."""
        if self.on_export_callback:
            self.on_export_callback()

    def set_file_path(self, path: str):
        """Set the file path."""
        self.file_path_var.set(path)

    def get_file_path(self) -> str:
        """Get the file path."""
        return self.file_path_var.get()

    def get_config(self) -> dict:
        """Get current configuration as dictionary."""
        return {
            "file_path": self.file_path_var.get(),
            "url_column": self.url_column_var.get(),
            "batch_size": self.batch_size_var.get(),
            "concurrent": self.concurrent_var.get(),
            "timeout": self.timeout_var.get(),
            "retry_count": self.retry_var.get(),
            "include_inactive": self.include_inactive_var.get(),
            "include_errors": self.include_errors_var.get(),
            "verify_ssl": self.verify_ssl_var.get(),
        }

    def set_config(self, config: dict):
        """Set configuration from dictionary."""
        if "url_column" in config:
            self.url_column_var.set(config["url_column"])
        if "batch_size" in config:
            self.batch_size_var.set(config["batch_size"])
        if "concurrent" in config:
            self.concurrent_var.set(config["concurrent"])
        if "timeout" in config:
            self.timeout_var.set(config["timeout"])
        if "retry_count" in config:
            self.retry_var.set(config["retry_count"])
        if "include_inactive" in config:
            self.include_inactive_var.set(config["include_inactive"])
        if "include_errors" in config:
            self.include_errors_var.set(config["include_errors"])
        if "verify_ssl" in config:
            self.verify_ssl_var.set(config["verify_ssl"])

    def enable_start_button(self, enabled: bool = True):
        """Enable or disable the start button."""
        self.start_button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def enable_pause_button(self, enabled: bool = True):
        """Enable or disable the pause button."""
        self.pause_button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def enable_stop_button(self, enabled: bool = True):
        """Enable or disable the stop button."""
        self.stop_button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def enable_export_button(self, enabled: bool = True):
        """Enable or disable the export button."""
        self.export_button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_pause_button_text(self, text: str):
        """Set the pause button text (for Resume)."""
        self.pause_button.configure(text=text)
