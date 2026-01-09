"""Main application window for the desktop GUI."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

from desktop_gui.models.app_state import AppState, StateManager
from desktop_gui.models.config import DesktopConfig
from desktop_gui.widgets.control_panel import ControlPanel
from desktop_gui.widgets.progress_tab import ProgressTab
from desktop_gui.widgets.results_table import ResultsTable
from desktop_gui.widgets.stats_tab import StatsTab
from desktop_gui.controllers.file_controller import FileController
from desktop_gui.controllers.export_controller import ExportController
from desktop_gui.controllers.process_controller import ProcessController
from desktop_gui.resources.styles import WINDOW


class MainWindow:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = DesktopConfig.load()
        self.state_manager = StateManager()

        # Controllers
        self.file_controller = FileController()
        self.export_controller = ExportController()
        self.process_controller = ProcessController()

        # Current file info
        self.current_file: Optional[Path] = None
        self.output_file: Optional[Path] = None

        # Setup window
        self._setup_window()
        self._build_ui()
        self._setup_callbacks()
        self._setup_keyboard_shortcuts()
        self._setup_state_callbacks()

        # Load last configuration
        self._load_configuration()

        # Start progress polling
        self._poll_progress()

    def _setup_window(self):
        """Setup main window properties."""
        self.root.title("Website Status Checker - Desktop Edition v1.0")

        # Set window size and position
        width = self.config.window_width
        height = self.config.window_height
        x = self.config.window_x
        y = self.config.window_y

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(WINDOW["min_width"], WINDOW["min_height"])

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        """Build the user interface."""
        # Menu bar
        self._create_menu_bar()

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Configure grid
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=0)  # Control panel fixed
        main_container.grid_columnconfigure(1, weight=1)  # Main area expands

        # Control panel (left)
        self.control_panel = ControlPanel(main_container)
        self.control_panel.grid(row=0, column=0, sticky='ns', padx=(10, 5), pady=10)

        # Main display area (right) with tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)

        # Create tabs
        self.progress_tab = ProgressTab(self.notebook)
        self.results_tab = ResultsTable(self.notebook)
        self.stats_tab = StatsTab(self.notebook)

        self.notebook.add(self.progress_tab, text="Progress")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.stats_tab, text="Statistics")

        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File... (Ctrl+O)", command=self._on_browse_file)
        file_menu.add_command(label="Export Results... (Ctrl+S)", command=self._on_export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit (Ctrl+Q)", command=self._on_closing)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About (F1)", command=self._show_about)

    def _setup_callbacks(self):
        """Setup callbacks for widgets."""
        # Control panel callbacks
        self.control_panel.on_browse_callback = self._on_browse_file
        self.control_panel.on_start_callback = self._on_start_processing
        self.control_panel.on_pause_callback = self._on_pause_processing
        self.control_panel.on_stop_callback = self._on_stop_processing
        self.control_panel.on_export_callback = self._on_export_results

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind('<Control-o>', lambda e: self._on_browse_file())
        self.root.bind('<Control-s>', lambda e: self._on_export_results())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<F5>', lambda e: self._on_start_processing())
        self.root.bind('<Escape>', lambda e: self._on_stop_processing())
        self.root.bind('<F1>', lambda e: self._show_about())

    def _setup_state_callbacks(self):
        """Setup state change callbacks."""
        self.state_manager.register_callback(self._on_state_changed)

    def _load_configuration(self):
        """Load configuration from saved settings."""
        config_dict = {
            "url_column": self.config.last_url_column,
            "batch_size": self.config.last_batch_size,
            "concurrent": self.config.last_concurrent,
            "timeout": self.config.last_timeout,
            "retry_count": self.config.last_retry_count,
            "include_inactive": self.config.include_inactive,
            "include_errors": self.config.include_errors,
            "verify_ssl": self.config.verify_ssl
        }
        self.control_panel.set_config(config_dict)

    def _on_browse_file(self):
        """Handle file browse."""
        self.update_status("Loading file...")
        self.state_manager.set_state(AppState.LOADING)

        def on_success(file_path, columns, row_count):
            self.root.after(0, lambda: self._on_file_loaded(file_path, columns, row_count))

        def on_error(error_msg):
            self.root.after(0, lambda: self._on_file_error(error_msg))

        self.file_controller.browse_file(on_success=on_success, on_error=on_error)

    def _on_file_loaded(self, file_path: Path, columns: list, row_count: int):
        """Handle successful file load."""
        self.current_file = file_path
        self.control_panel.set_file_path(str(file_path))

        # Suggest output file name
        self.output_file = file_path.parent / f"{file_path.stem}_results{file_path.suffix}"

        self.update_status(f"Loaded {row_count:,} URLs from {file_path.name}")

        # Update progress tab
        self.progress_tab.reset()
        self.progress_tab.update_statistics(total_urls=row_count)

        # Clear previous results
        self.results_tab.clear_results()
        self.stats_tab.clear()

        # Set state to ready
        self.state_manager.set_state(AppState.READY)

    def _on_file_error(self, error_msg: str):
        """Handle file load error."""
        messagebox.showerror("File Error", error_msg)
        self.update_status("Error loading file")
        self.state_manager.set_state(AppState.IDLE)

    def _on_start_processing(self):
        """Handle start processing."""
        if not self.state_manager.can_start_processing():
            return

        if not self.current_file or not self.output_file:
            messagebox.showerror("Error", "Please select an input file first.")
            return

        # Get configuration
        config = self.control_panel.get_config()

        # Save configuration
        self.config.update_processing_settings(
            batch_size=config['batch_size'],
            concurrent=config['concurrent'],
            timeout=config['timeout'],
            retry_count=config['retry_count'],
            include_inactive=config['include_inactive'],
            include_errors=config['include_errors'],
            verify_ssl=config['verify_ssl']
        )
        self.config.last_url_column = config['url_column']
        self.config.save()

        try:
            # Start processing
            self.process_controller.start_processing(
                self.current_file,
                self.output_file,
                config
            )

            self.state_manager.set_state(AppState.PROCESSING)
            self.update_status("Processing...")
            self.progress_tab.update_status("Processing URLs...")

            # Switch to progress tab
            self.notebook.select(self.progress_tab)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start processing:\n{str(e)}")
            self.state_manager.set_state(AppState.ERROR)

    def _on_pause_processing(self):
        """Handle pause processing."""
        # Not implemented in current version
        messagebox.showinfo("Not Implemented", "Pause functionality will be added in a future version.")

    def _on_stop_processing(self):
        """Handle stop processing."""
        if not self.state_manager.can_stop_processing():
            return

        result = messagebox.askyesno(
            "Stop Processing",
            "Are you sure you want to stop processing?\nPartial results will be saved."
        )

        if result:
            self.process_controller.stop_processing()
            self.update_status("Stopping...")

    def _on_export_results(self):
        """Handle export results."""
        results = self.results_tab.get_all_results()

        if not results:
            messagebox.showwarning("No Results", "No results to export.")
            return

        initial_filename = "results"
        if self.current_file:
            initial_filename = f"{self.current_file.stem}_results"

        self.export_controller.export_results(results, initial_filename)

    def _poll_progress(self):
        """Poll progress queue for updates."""
        update = self.process_controller.get_progress_update()

        if update:
            self._handle_progress_update(update)

        # Schedule next poll
        self.root.after(100, self._poll_progress)

    def _handle_progress_update(self, update: dict):
        """Handle progress update from processor."""
        msg_type = update.get("type")
        data = update.get("data", {})

        if msg_type == "started":
            total_urls = data.get("total_urls", 0)
            self.progress_tab.update_statistics(total_urls=total_urls)

        elif msg_type == "batch_complete":
            # Update progress bar
            progress = data.get("progress", 0)
            self.progress_tab.update_progress(progress)

            # Update statistics
            self.progress_tab.update_statistics(
                processed=data.get("processed", 0),
                active=data.get("active", 0),
                inactive=data.get("inactive", 0),
                errors=data.get("errors", 0),
                rate=data.get("processing_rate", 0),
                elapsed=data.get("elapsed_time", 0),
                eta=data.get("eta", -1)
            )

            self.update_status(f"Processing: {data.get('processed', 0):,} / {data.get('total', 0):,} URLs")

        elif msg_type == "complete":
            stats = data.get("stats", {})
            self._on_processing_complete(stats)

        elif msg_type == "error":
            error_msg = data.get("message", "Unknown error")
            self._on_processing_error(error_msg)

        elif msg_type == "stopped":
            self._on_processing_stopped()

    def _on_processing_complete(self, stats: dict):
        """Handle processing completion."""
        self.state_manager.set_state(AppState.COMPLETED)

        total = stats.get("total_urls", 0)
        active = stats.get("active", 0)
        elapsed = stats.get("elapsed_time", 0)

        self.update_status(f"Complete! Processed {total:,} URLs in {elapsed:.1f}s")
        self.progress_tab.update_status(f"Processing complete! Found {active:,} active websites.")

        # Load results from output file
        self._load_results_from_file()

        # Update statistics tab
        self._update_statistics_tab(stats)

        messagebox.showinfo(
            "Processing Complete",
            f"Successfully processed {total:,} URLs.\n\n"
            f"Active: {active:,}\n"
            f"Results saved to: {self.output_file}"
        )

    def _on_processing_error(self, error_msg: str):
        """Handle processing error."""
        self.state_manager.set_state(AppState.ERROR)
        self.update_status(f"Error: {error_msg}")
        messagebox.showerror("Processing Error", f"An error occurred during processing:\n{error_msg}")

    def _on_processing_stopped(self):
        """Handle processing stopped."""
        self.state_manager.set_state(AppState.IDLE)
        self.update_status("Processing stopped by user")
        messagebox.showinfo("Stopped", "Processing stopped. Partial results have been saved.")

    def _load_results_from_file(self):
        """Load results from output file into results table."""
        if not self.output_file or not self.output_file.exists():
            return

        try:
            import pandas as pd

            if self.output_file.suffix.lower() == '.csv':
                df = pd.read_csv(self.output_file)
            else:
                df = pd.read_excel(self.output_file)

            results = df.to_dict('records')
            self.results_tab.set_results(results)

            # Switch to results tab
            self.notebook.select(self.results_tab)

        except Exception as e:
            print(f"Error loading results: {e}")

    def _update_statistics_tab(self, stats: dict):
        """Update statistics tab with final stats."""
        config = self.control_panel.get_config()
        stats['config'] = config
        self.stats_tab.update_statistics(stats)

    def _on_state_changed(self, old_state: AppState, new_state: AppState, message: str):
        """Handle state changes."""
        # Update UI based on state
        if new_state == AppState.IDLE:
            self.control_panel.enable_start_button(False)
            self.control_panel.enable_pause_button(False)
            self.control_panel.enable_stop_button(False)

        elif new_state == AppState.READY:
            self.control_panel.enable_start_button(True)
            self.control_panel.enable_pause_button(False)
            self.control_panel.enable_stop_button(False)

        elif new_state == AppState.PROCESSING:
            self.control_panel.enable_start_button(False)
            self.control_panel.enable_pause_button(False)  # Pause not implemented yet
            self.control_panel.enable_stop_button(True)

        elif new_state == AppState.COMPLETED:
            self.control_panel.enable_start_button(False)
            self.control_panel.enable_pause_button(False)
            self.control_panel.enable_stop_button(False)
            self.control_panel.enable_export_button(True)

    def update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.config(text=message)

    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "Website Status Checker\n"
            "Desktop Edition v1.0\n\n"
            "A high-performance desktop application for checking\n"
            "the status of multiple websites simultaneously.\n\n"
            "Built with Python and tkinter"
        )
        messagebox.showinfo("About", about_text)

    def _on_closing(self):
        """Handle window closing."""
        # Save window geometry
        geometry = self.root.geometry()
        parts = geometry.split('+')
        size_parts = parts[0].split('x')

        self.config.update_window_geometry(
            int(size_parts[0]),
            int(size_parts[1]),
            int(parts[1]) if len(parts) > 1 else 100,
            int(parts[2]) if len(parts) > 2 else 100
        )
        self.config.save()

        # Stop processing if running
        if self.process_controller.is_running():
            result = messagebox.askyesno(
                "Processing in Progress",
                "Processing is still running. Are you sure you want to exit?"
            )
            if not result:
                return

            self.process_controller.stop_processing()

        self.root.destroy()
