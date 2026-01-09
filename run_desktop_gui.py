#!/usr/bin/env python3
"""
Website Status Checker - Desktop GUI Launcher

Launch the tkinter-based desktop application.

Usage:
    python run_desktop_gui.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from desktop_gui.app import main
except ImportError as e:
    print(f"Error importing desktop GUI: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
