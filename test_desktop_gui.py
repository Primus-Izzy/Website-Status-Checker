#!/usr/bin/env python3
"""Test desktop GUI initialization and components"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all desktop GUI imports"""
    print("=" * 60)
    print("TEST: Desktop GUI Imports and Initialization")
    print("=" * 60)

    errors = []

    print("\n1. Testing tkinter availability...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()
        print("   [PASS] tkinter is available")
    except Exception as e:
        print(f"   [FAIL] tkinter error: {e}")
        errors.append(f"tkinter: {e}")

    print("\n2. Testing desktop_gui package...")
    try:
        from desktop_gui import app
        print("   [PASS] desktop_gui.app imports successfully")
    except Exception as e:
        print(f"   [FAIL] desktop_gui.app error: {e}")
        errors.append(f"desktop_gui.app: {e}")
        return False

    print("\n3. Testing main window...")
    try:
        from desktop_gui import main_window
        print("   [PASS] main_window imports successfully")
    except Exception as e:
        print(f"   [FAIL] main_window error: {e}")
        errors.append(f"main_window: {e}")

    print("\n4. Testing widgets...")
    try:
        from desktop_gui.widgets import control_panel
        from desktop_gui.widgets import progress_tab
        from desktop_gui.widgets import results_table
        from desktop_gui.widgets import stats_tab
        print("   [PASS] All widgets import successfully")
    except Exception as e:
        print(f"   [FAIL] widgets error: {e}")
        errors.append(f"widgets: {e}")

    print("\n5. Testing controllers...")
    try:
        from desktop_gui.controllers import file_controller
        from desktop_gui.controllers import export_controller
        from desktop_gui.controllers import process_controller
        print("   [PASS] All controllers import successfully")
    except Exception as e:
        print(f"   [FAIL] controllers error: {e}")
        errors.append(f"controllers: {e}")

    print("\n6. Testing models...")
    try:
        from desktop_gui.models import app_state
        from desktop_gui.models import config
        print("   [PASS] All models import successfully")
    except Exception as e:
        print(f"   [FAIL] models error: {e}")
        errors.append(f"models: {e}")

    print("\n7. Testing utilities...")
    try:
        from desktop_gui.utils import async_bridge
        from desktop_gui.utils import formatters
        from desktop_gui.utils import validators
        print("   [PASS] All utilities import successfully")
    except Exception as e:
        print(f"   [FAIL] utilities error: {e}")
        errors.append(f"utilities: {e}")

    print("\n8. Testing resources...")
    try:
        from desktop_gui.resources import styles
        print("   [PASS] Resources import successfully")
    except Exception as e:
        print(f"   [FAIL] resources error: {e}")
        errors.append(f"resources: {e}")

    print("\n9. Testing app initialization...")
    try:
        from desktop_gui.app import main
        # Don't actually run it, just verify it can be imported
        print("   [PASS] App main function available")
    except Exception as e:
        print(f"   [FAIL] app main error: {e}")
        errors.append(f"app main: {e}")

    print("\n10. Testing model instantiation...")
    try:
        from desktop_gui.models.app_state import AppState, StateManager
        from desktop_gui.models.config import DesktopConfig

        # Create instances
        config = DesktopConfig()
        state_manager = StateManager()

        print(f"   Initial state: {state_manager.current}")
        print(f"   Config loaded successfully")
        print("   [PASS] Models can be instantiated")
    except Exception as e:
        print(f"   [FAIL] model instantiation error: {e}")
        errors.append(f"model instantiation: {e}")

    if errors:
        print("\n" + "=" * 60)
        print(f"[FAIL] {len(errors)} errors found:")
        for error in errors:
            print(f"  - {error}")
        print("=" * 60)
        return False
    else:
        print("\n" + "=" * 60)
        print("[SUCCESS] All desktop GUI tests passed!")
        print("=" * 60)
        print("\nDesktop GUI is ready to run:")
        print("  python run_desktop_gui.py")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
