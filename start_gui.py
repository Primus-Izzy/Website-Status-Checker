#!/usr/bin/env python3
"""
Quick Start Script for Website Status Checker Web GUI

This script checks dependencies and starts the web server.
"""

import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if GUI dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import jinja2
        import pydantic
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("\n📦 Installing GUI dependencies...")
        return False


def install_dependencies():
    """Install GUI dependencies"""
    requirements_file = Path(__file__).parent / "requirements-gui.txt"

    if not requirements_file.exists():
        print("❌ requirements-gui.txt not found!")
        return False

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def start_server():
    """Start the GUI server"""
    print("\n🚀 Starting Website Status Checker Web GUI...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/api/docs")
    print("\n⌨️  Press Ctrl+C to stop the server\n")

    try:
        subprocess.check_call([
            sys.executable, "-m", "uvicorn", "gui.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 60)
    print("Website Status Checker - Web GUI Quick Start")
    print("=" * 60)

    # Check dependencies
    if not check_dependencies():
        print("\nWould you like to install the required dependencies? (y/n): ", end="")
        choice = input().strip().lower()

        if choice == 'y':
            if not install_dependencies():
                print("\n❌ Failed to install dependencies. Please install manually:")
                print("   pip install -r requirements-gui.txt")
                sys.exit(1)
        else:
            print("\n❌ Cannot start GUI without dependencies.")
            print("   Install with: pip install -r requirements-gui.txt")
            sys.exit(1)
    else:
        print("✅ All dependencies are installed")

    # Start server
    start_server()


if __name__ == "__main__":
    main()
