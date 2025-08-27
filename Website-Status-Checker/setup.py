from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() 
        for line in fh 
        if line.strip() and not line.startswith("#") and not line.startswith("-")
    ]

# Clean requirements (remove version constraints and extras for basic install)
cleaned_requirements = []
for req in requirements:
    if ";" not in req:  # Skip conditional dependencies
        if ">=" in req:
            cleaned_requirements.append(req.split(">=")[0])
        elif "==" in req:
            cleaned_requirements.append(req.split("==")[0])
        elif "<" in req:
            cleaned_requirements.append(req.split("<")[0])
        else:
            cleaned_requirements.append(req)

setup(
    name="website-status-checker",
    version="1.0.0",
    author="Isreal Oyarinde",
    author_email="contact@isrealoyarinde.com",
    description="High-performance website status validation at scale",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Primus-Izzy/website-status-checker",
    project_urls={
        "Bug Tracker": "https://github.com/Primus-Izzy/website-status-checker/issues",
        "Documentation": "https://github.com/Primus-Izzy/website-status-checker/docs",
        "Source Code": "https://github.com/Primus-Izzy/website-status-checker",
        "Changelog": "https://github.com/Primus-Izzy/website-status-checker/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=cleaned_requirements,
    extras_require={
        "performance": [
            "aiodns>=3.0.0",
            "cchardet>=2.1.7",
            "orjson>=3.8.0",
        ],
        "profiling": [
            "memory-profiler>=0.60.0",
            "psutil>=5.9.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "isort>=5.10.0",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "all": [
            "aiodns>=3.0.0",
            "cchardet>=2.1.7",
            "orjson>=3.8.0",
            "memory-profiler>=0.60.0",
            "psutil>=5.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "website-status-checker=cli:cli_entry_point",
            "wsc=cli:cli_entry_point",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "website", "status", "checker", "http", "monitoring", "validation",
        "async", "concurrent", "batch", "scale", "performance", "uptime"
    ],
    platforms=["any"],
)