"""Configuration management for the desktop GUI."""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DesktopConfig:
    """Desktop GUI specific configuration."""

    # Window settings
    window_width: int = 1280
    window_height: int = 800
    window_x: int = 100
    window_y: int = 100

    # Last used settings
    last_directory: str = ""
    last_url_column: str = "url"
    last_batch_size: int = 1000
    last_concurrent: int = 100
    last_timeout: int = 10
    last_retry_count: int = 2
    include_inactive: bool = True
    include_errors: bool = False
    verify_ssl: bool = True

    # UI preferences
    theme: str = "default"
    auto_export: bool = False
    show_notifications: bool = True

    @classmethod
    def get_config_file(cls) -> Path:
        """Get the configuration file path."""
        config_dir = Path.home() / ".website_status_checker"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "desktop_config.json"

    @classmethod
    def load(cls) -> "DesktopConfig":
        """
        Load configuration from file.

        Returns:
            DesktopConfig instance with loaded or default values
        """
        config_file = cls.get_config_file()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
                return cls()
        return cls()

    def save(self):
        """Save configuration to file."""
        config_file = self.get_config_file()
        try:
            with open(config_file, 'w') as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def update_window_geometry(self, width: int, height: int, x: int, y: int):
        """
        Update window geometry settings.

        Args:
            width: Window width
            height: Window height
            x: Window X position
            y: Window Y position
        """
        self.window_width = width
        self.window_height = height
        self.window_x = x
        self.window_y = y

    def update_processing_settings(
        self,
        batch_size: Optional[int] = None,
        concurrent: Optional[int] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None,
        include_inactive: Optional[bool] = None,
        include_errors: Optional[bool] = None,
        verify_ssl: Optional[bool] = None
    ):
        """
        Update processing settings.

        Args:
            batch_size: Batch size for processing
            concurrent: Number of concurrent requests
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            include_inactive: Include inactive websites in results
            include_errors: Include error websites in results
            verify_ssl: Verify SSL certificates
        """
        if batch_size is not None:
            self.last_batch_size = batch_size
        if concurrent is not None:
            self.last_concurrent = concurrent
        if timeout is not None:
            self.last_timeout = timeout
        if retry_count is not None:
            self.last_retry_count = retry_count
        if include_inactive is not None:
            self.include_inactive = include_inactive
        if include_errors is not None:
            self.include_errors = include_errors
        if verify_ssl is not None:
            self.verify_ssl = verify_ssl
