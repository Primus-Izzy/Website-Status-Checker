"""UI styles and color themes for the desktop GUI."""

# Color palette
COLORS = {
    # Status colors
    "success": "#2ecc71",      # Green for active websites
    "warning": "#e67e22",      # Orange for inactive websites
    "error": "#e74c3c",        # Red for errors
    "info": "#3498db",         # Blue for information
    "disabled": "#95a5a6",     # Gray for disabled elements

    # Button colors
    "button_start": "#27ae60",
    "button_start_hover": "#229954",
    "button_start_active": "#1e8449",

    "button_stop": "#e74c3c",
    "button_stop_hover": "#cb4335",
    "button_stop_active": "#b03a2e",

    "button_pause": "#f39c12",
    "button_pause_hover": "#e67e22",
    "button_pause_active": "#d68910",

    "button_default": "#3498db",
    "button_default_hover": "#2e86c1",
    "button_default_active": "#2874a6",

    # Background colors
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8f9fa",
    "bg_tertiary": "#e9ecef",

    # Text colors
    "text_primary": "#2c3e50",
    "text_secondary": "#7f8c8d",
    "text_light": "#95a5a6",

    # Border colors
    "border_light": "#dee2e6",
    "border_medium": "#ced4da",
    "border_dark": "#adb5bd",
}

# Font configurations
FONTS = {
    "header": ("Arial", 12, "bold"),
    "label": ("Arial", 10),
    "value": ("Courier New", 10),
    "button": ("Arial", 10),
    "status": ("Arial", 9, "italic"),
    "monospace": ("Courier New", 9),
}

# Widget spacing
SPACING = {
    "padding_small": 5,
    "padding_medium": 10,
    "padding_large": 15,
    "widget_spacing": 5,
    "section_spacing": 15,
}

# Window dimensions
WINDOW = {
    "min_width": 1024,
    "min_height": 768,
    "default_width": 1280,
    "default_height": 800,
}

# Control panel dimensions
CONTROL_PANEL = {
    "width": 300,
}


def get_color(name: str) -> str:
    """
    Get color by name.

    Args:
        name: Color name

    Returns:
        Hex color code
    """
    return COLORS.get(name, "#000000")


def get_font(name: str) -> tuple:
    """
    Get font configuration by name.

    Args:
        name: Font name

    Returns:
        Font tuple (family, size, weight)
    """
    return FONTS.get(name, ("Arial", 10))


def get_spacing(name: str) -> int:
    """
    Get spacing value by name.

    Args:
        name: Spacing name

    Returns:
        Spacing value in pixels
    """
    return SPACING.get(name, 10)
