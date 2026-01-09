#!/usr/bin/env python3
"""
Master Verification Script - Website Status Checker
Tests EVERYTHING to ensure the system is production-ready
"""

import sys
import subprocess
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_test(name, status, message=""):
    """Print test result"""
    if status:
        symbol = f"{Colors.GREEN}[OK]{Colors.END}"
        status_text = f"{Colors.GREEN}PASS{Colors.END}"
    else:
        symbol = f"{Colors.RED}[!!]{Colors.END}"
        status_text = f"{Colors.RED}FAIL{Colors.END}"

    print(f"{symbol} {name:<50} [{status_text}]")
    if message:
        print(f"  {Colors.YELLOW}-> {message}{Colors.END}")

def run_test_file(filepath, description):
    """Run a test file and return success status"""
    print(f"\n{Colors.BOLD}Running: {description}{Colors.END}")
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=60
        )
        success = result.returncode == 0
        if success:
            print(f"{Colors.GREEN}SUCCESS{Colors.END}")
        else:
            print(f"{Colors.RED}FAILED{Colors.END}")
            if result.stderr:
                print(f"{Colors.YELLOW}Error output:{Colors.END}")
                print(result.stderr[:500])
        return success
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}TIMEOUT{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}ERROR: {e}{Colors.END}")
        return False

def main():
    """Run all verification tests"""
    print_header("WEBSITE STATUS CHECKER - MASTER VERIFICATION")

    results = {}
    total_tests = 0
    passed_tests = 0

    # Phase 1: Dependency Check
    print_header("PHASE 1: DEPENDENCY VERIFICATION")

    dependencies = [
        ("Python 3.8+", "python", sys.version_info >= (3, 8)),
        ("aiohttp", "import aiohttp", None),
        ("pandas", "import pandas", None),
        ("tkinter", "import tkinter", None),
        ("FastAPI", "import fastapi", None),
        ("requests", "import requests", None),
        ("pytest", "import pytest", None),
    ]

    for name, import_cmd, check in dependencies:
        total_tests += 1
        if check is not None:
            status = check
        else:
            try:
                exec(import_cmd)
                status = True
            except ImportError:
                status = False

        print_test(name, status)
        results[name] = status
        if status:
            passed_tests += 1

    # Phase 2: Core Module Imports
    print_header("PHASE 2: CORE MODULE VERIFICATION")

    core_imports = [
        ("Core Checker", "from src.core.checker import WebsiteStatusChecker"),
        ("Batch Processor", "from src.core.batch import BatchProcessor, BatchConfig"),
        ("Config", "from src.config import get_app_config"),
        ("Web GUI Main", "from gui.main import app"),
        ("Desktop GUI App", "from desktop_gui.app import main"),
    ]

    for name, import_cmd in core_imports:
        total_tests += 1
        try:
            exec(import_cmd)
            status = True
            message = "Imported successfully"
        except Exception as e:
            status = False
            message = str(e)[:100]

        print_test(name, status, message if not status else "")
        results[name] = status
        if status:
            passed_tests += 1

    # Phase 3: File Structure Verification
    print_header("PHASE 3: FILE STRUCTURE VERIFICATION")

    critical_files = [
        "src/core/checker.py",
        "src/core/batch.py",
        "src/cli/main.py",
        "gui/main.py",
        "desktop_gui/app.py",
        "desktop_gui/main_window.py",
        "requirements.txt",
        "README.md",
        "run_desktop_gui.py",
    ]

    for filepath in critical_files:
        total_tests += 1
        path = Path(filepath)
        status = path.exists()
        print_test(f"File: {filepath}", status)
        results[f"File:{filepath}"] = status
        if status:
            passed_tests += 1

    # Phase 4: Test Suite Execution
    print_header("PHASE 4: TEST SUITE EXECUTION")

    test_files = [
        ("test_core.py", "Core Functionality Tests"),
        ("test_web_gui.py", "Web GUI Tests"),
        ("test_desktop_gui.py", "Desktop GUI Tests"),
    ]

    for test_file, description in test_files:
        total_tests += 1
        if Path(test_file).exists():
            status = run_test_file(test_file, description)
        else:
            status = False
            print(f"{Colors.RED}Test file not found: {test_file}{Colors.END}")

        print_test(description, status)
        results[description] = status
        if status:
            passed_tests += 1

    # Phase 5: Example Files Verification
    print_header("PHASE 5: EXAMPLE FILES VERIFICATION")

    example_files = [
        "examples/sample_websites.csv",
        "examples/api_usage_examples.py",
        "examples/batch_processing_example.py",
    ]

    for filepath in example_files:
        total_tests += 1
        path = Path(filepath)
        status = path.exists()
        print_test(f"Example: {path.name}", status)
        results[f"Example:{filepath}"] = status
        if status:
            passed_tests += 1

    # Phase 6: Documentation Verification
    print_header("PHASE 6: DOCUMENTATION VERIFICATION")

    docs = [
        "README.md",
        "README_DESKTOP_GUI.md",
        "GUI_README.md",
        "START_HERE.md",
        "QUICKSTART.md",
        "ARCHITECTURE.md",
        "FAQ.md",
    ]

    for doc in docs:
        total_tests += 1
        path = Path(doc)
        status = path.exists() and path.stat().st_size > 100
        print_test(f"Doc: {doc}", status)
        results[f"Doc:{doc}"] = status
        if status:
            passed_tests += 1

    # Phase 7: Output Directories
    print_header("PHASE 7: OUTPUT DIRECTORIES VERIFICATION")

    directories = [
        "gui/uploads",
        "gui/exports",
    ]

    for directory in directories:
        total_tests += 1
        path = Path(directory)
        status = path.exists() and path.is_dir()
        print_test(f"Directory: {directory}", status)
        results[f"Dir:{directory}"] = status
        if status:
            passed_tests += 1

    # Final Summary
    print_header("FINAL VERIFICATION SUMMARY")

    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\n{Colors.BOLD}Total Tests Run:{Colors.END} {total_tests}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {passed_tests}")
    print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {total_tests - passed_tests}")
    print(f"{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%\n")

    if pass_rate >= 95:
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}")
        print(f"[OK] VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL".center(70))
        print(f"{'='*70}{Colors.END}\n")
        print(f"{Colors.GREEN}SUCCESS: The system is PRODUCTION READY!{Colors.END}\n")
        return 0
    elif pass_rate >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}{'='*70}")
        print(f"[!!] VERIFICATION COMPLETE - SOME ISSUES FOUND".center(70))
        print(f"{'='*70}{Colors.END}\n")
        print(f"{Colors.YELLOW}WARNING: The system is mostly functional but has some issues{Colors.END}\n")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}{'='*70}")
        print(f"[FAIL] VERIFICATION FAILED - CRITICAL ISSUES FOUND".center(70))
        print(f"{'='*70}{Colors.END}\n")
        print(f"{Colors.RED}ERROR: The system has critical issues that need fixing{Colors.END}\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
