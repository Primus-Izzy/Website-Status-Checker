"""Results table widget for displaying URL check results."""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional
import webbrowser
from desktop_gui.resources.styles import COLORS
from desktop_gui.utils.formatters import format_response_time


class ResultsTable(ttk.Frame):
    """Tab displaying results in a sortable, filterable table."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Data storage
        self.all_results: List[Dict] = []
        self.filtered_results: List[Dict] = []
        self.sort_column: Optional[str] = None
        self.sort_reverse = False

        # Variables
        self.filter_text_var = tk.StringVar()
        self.filter_text_var.trace('w', lambda *args: self._apply_filters())
        self.status_filter_var = tk.StringVar(value="All")
        self.result_count_var = tk.StringVar(value="Showing 0 results")

        self._build_ui()

    def _build_ui(self):
        """Build the results table UI."""
        # Filter controls at the top
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))

        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_text_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter_var,
            values=["All", "Active", "Inactive", "Error"],
            state='readonly',
            width=10
        )
        status_combo.pack(side=tk.LEFT)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # Result count label
        count_label = ttk.Label(filter_frame, textvariable=self.result_count_var)
        count_label.pack(side=tk.RIGHT)

        # Treeview with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Define columns
        columns = ("url", "status", "status_code", "response_time", "error", "final_url")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')

        # Configure columns
        self.tree.heading("url", text="URL", command=lambda: self._sort_by_column("url"))
        self.tree.heading("status", text="Status", command=lambda: self._sort_by_column("status"))
        self.tree.heading("status_code", text="Status Code", command=lambda: self._sort_by_column("status_code"))
        self.tree.heading("response_time", text="Response Time", command=lambda: self._sort_by_column("response_time"))
        self.tree.heading("error", text="Error Message", command=lambda: self._sort_by_column("error"))
        self.tree.heading("final_url", text="Final URL", command=lambda: self._sort_by_column("final_url"))

        self.tree.column("url", width=300, anchor=tk.W)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("status_code", width=100, anchor=tk.CENTER)
        self.tree.column("response_time", width=120, anchor=tk.E)
        self.tree.column("error", width=250, anchor=tk.W)
        self.tree.column("final_url", width=200, anchor=tk.W)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Configure tags for color coding
        self.tree.tag_configure('active', foreground=COLORS["success"])
        self.tree.tag_configure('inactive', foreground=COLORS["warning"])
        self.tree.tag_configure('error', foreground=COLORS["error"])

        # Context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Copy URL", command=self._copy_url)
        self.context_menu.add_command(label="Copy Row", command=self._copy_row)
        self.context_menu.add_command(label="Open in Browser", command=self._open_in_browser)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _copy_url(self):
        """Copy selected URL to clipboard."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            url = self.tree.item(item)['values'][0]
            self.clipboard_clear()
            self.clipboard_append(url)

    def _copy_row(self):
        """Copy selected row to clipboard."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item)['values']
            row_text = '\t'.join(str(v) for v in values)
            self.clipboard_clear()
            self.clipboard_append(row_text)

    def _open_in_browser(self):
        """Open selected URL in browser."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            url = self.tree.item(item)['values'][0]
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"Error opening URL: {e}")

    def _sort_by_column(self, column: str):
        """Sort table by column."""
        # Toggle sort direction if same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Sort the filtered results
        col_index = ["url", "status", "status_code", "response_time", "error", "final_url"].index(column)

        self.filtered_results.sort(
            key=lambda x: self._get_sort_key(x, col_index),
            reverse=self.sort_reverse
        )

        # Refresh display
        self._populate_tree()

    def _get_sort_key(self, result: Dict, col_index: int):
        """Get sort key for a result."""
        values = self._result_to_values(result)
        value = values[col_index]

        # Handle numeric columns
        if col_index == 2:  # status_code
            try:
                return int(value) if value else 0
            except:
                return 0
        elif col_index == 3:  # response_time
            # Extract numeric value from formatted string
            try:
                if "ms" in str(value):
                    return float(str(value).replace(" ms", ""))
                elif "s" in str(value):
                    return float(str(value).replace(" s", "")) * 1000
                else:
                    return 0
            except:
                return 0

        return str(value).lower()

    def _apply_filters(self):
        """Apply text and status filters."""
        filter_text = self.filter_text_var.get().lower()
        status_filter = self.status_filter_var.get()

        # Filter results
        self.filtered_results = []
        for result in self.all_results:
            # Status filter
            if status_filter != "All":
                if result.get("status", "").lower() != status_filter.lower():
                    continue

            # Text filter (search in URL and error)
            if filter_text:
                url = result.get("url", "").lower()
                error = result.get("error", "").lower()
                if filter_text not in url and filter_text not in error:
                    continue

            self.filtered_results.append(result)

        # Update display
        self._populate_tree()
        self._update_count()

    def _populate_tree(self):
        """Populate tree with filtered results."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add filtered results
        for result in self.filtered_results:
            values = self._result_to_values(result)
            tag = self._get_tag_for_status(result.get("status", ""))
            self.tree.insert('', tk.END, values=values, tags=(tag,))

    def _result_to_values(self, result: Dict) -> tuple:
        """Convert result dict to tuple of values for display."""
        return (
            result.get("url", ""),
            result.get("status", ""),
            result.get("status_code", ""),
            format_response_time(result.get("response_time", 0)),
            result.get("error", ""),
            result.get("final_url", result.get("url", ""))
        )

    def _get_tag_for_status(self, status: str) -> str:
        """Get tag name for status."""
        status_lower = status.lower()
        if "active" in status_lower:
            return "active"
        elif "inactive" in status_lower:
            return "inactive"
        else:
            return "error"

    def _update_count(self):
        """Update result count label."""
        total = len(self.all_results)
        filtered = len(self.filtered_results)

        if total == filtered:
            self.result_count_var.set(f"Showing {filtered:,} results")
        else:
            self.result_count_var.set(f"Showing {filtered:,} of {total:,} results")

    def add_results(self, results: List[Dict]):
        """Add results to the table."""
        self.all_results.extend(results)
        self._apply_filters()

    def set_results(self, results: List[Dict]):
        """Set results (replacing existing)."""
        self.all_results = results
        self._apply_filters()

    def clear_results(self):
        """Clear all results."""
        self.all_results = []
        self.filtered_results = []
        self._populate_tree()
        self._update_count()

    def get_filtered_results(self) -> List[Dict]:
        """Get currently filtered results."""
        return self.filtered_results

    def get_all_results(self) -> List[Dict]:
        """Get all results."""
        return self.all_results
