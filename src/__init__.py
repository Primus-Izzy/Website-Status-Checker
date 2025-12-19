"""
Website Status Checker

A high-performance tool for checking website status at scale with concurrent
processing, intelligent error handling, and comprehensive reporting.

Features:
- Concurrent HTTP status checking (up to 1000+ simultaneous requests)
- Smart URL normalization and validation
- Automatic retry logic with exponential backoff
- Batch processing for large datasets (100K+ URLs)
- Memory-efficient streaming processing
- Progress tracking and resume capability
- Multiple output formats (CSV, JSON, Excel)
- Comprehensive error categorization
- Real-time statistics and performance monitoring

Usage:
    # Command line usage
    python -m website_status_checker websites.csv --output results.csv
    
    # Programmatic usage
    from website_status_checker import WebsiteStatusChecker
    
    checker = WebsiteStatusChecker()
    result = await checker.check_website("https://isrealoyarinde.com")
    print(f"Status: {result.status_result}")

Author: Isreal Oyarinde
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Isreal Oyarinde"
__license__ = "MIT"
__maintainer__ = "Isreal Oyarinde"
__email__ = "contact@isrealoyarinde.com"
__status__ = "Production"

# Core imports for easy access
try:
    from .core.checker import (
        WebsiteStatusChecker,
        StatusResult,
        ErrorCategory,
        CheckResult,
        CheckerStats,
    )

    from .core.batch import (
        BatchProcessor,
        BatchConfig,
        ProcessingStats,
    )
    
    __all__ = [
        # Core classes
        "WebsiteStatusChecker",
        "BatchProcessor",
        
        # Configuration classes
        "BatchConfig",
        
        # Result classes
        "CheckResult",
        "CheckerStats", 
        "ProcessingStats",
        
        # Enums
        "StatusResult",
        "ErrorCategory",
        
        # Metadata
        "__version__",
        "__author__",
        "__license__",
    ]
    
except ImportError as e:
    # Handle import errors gracefully during development/installation
    import warnings
    warnings.warn(f"Some Website Status Checker modules could not be imported: {e}")
    __all__ = ["__version__", "__author__", "__license__"]

# Package metadata
__title__ = "website-status-checker"
__description__ = "High-performance website status validation at scale"
__url__ = "https://github.com/Primus-Izzy/website-status-checker"
__download_url__ = "https://github.com/Primus-Izzy/website-status-checker/archive/main.zip"
__docs__ = "https://github.com/Primus-Izzy/website-status-checker/blob/main/README.md"
__tracker__ = "https://github.com/Primus-Izzy/website-status-checker/issues"
__keywords__ = [
    "website", "status", "checker", "http", "monitoring", "validation",
    "async", "concurrent", "batch", "scale", "performance", "uptime"
]