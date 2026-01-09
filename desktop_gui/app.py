"""Main application entry point for the desktop GUI."""

import sys
import tkinter as tk
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from desktop_gui.main_window import MainWindow


def main():
    """Main entry point for the desktop application."""
    try:
        # Create root window
        root = tk.Tk()

        # Create main window
        app = MainWindow(root)

        # Start event loop
        root.mainloop()

        return 0

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
