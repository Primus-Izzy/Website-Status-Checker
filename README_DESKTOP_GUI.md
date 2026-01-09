# Website Status Checker - Desktop GUI

A standalone desktop application for checking the status of multiple websites simultaneously. Built with Python and tkinter, this application provides a native desktop experience with real-time progress tracking.

## Features

- **Native Desktop Application**: Runs natively on Windows, macOS, and Linux
- **File Support**: Load URLs from CSV, Excel (.xlsx, .xls), or text files
- **Real-time Progress**: Live progress bar and statistics during processing
- **High Performance**: Process thousands of URLs with concurrent requests
- **Flexible Configuration**: Customize batch size, concurrency, timeout, and retries
- **Results Display**: Interactive table with sorting and filtering
- **Multiple Export Formats**: Export results to CSV, Excel, or JSON
- **Context Menu**: Right-click to copy URLs or open in browser
- **Configuration Persistence**: Saves your last used settings

## Requirements

- Python 3.8 or higher
- All dependencies from `requirements.txt` (tkinter is included with Python)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd C:\Users\EliteBook 1030G3\Videos\Website-Status-Checker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python run_desktop_gui.py
   ```

## Quick Start

### Launching the Application

Run the desktop GUI using:

```bash
python run_desktop_gui.py
```

### Basic Workflow

1. **Load a File**
   - Click "Browse..." button or press `Ctrl+O`
   - Select a CSV, Excel, or text file containing URLs
   - Wait for file validation (shows total URLs found)

2. **Configure Settings** (optional)
   - Adjust batch size (100-10000, default: 1000)
   - Set concurrent requests (1-500, default: 100)
   - Set timeout (5-120 seconds, default: 10)
   - Set retry count (0-10, default: 2)
   - Check/uncheck options (Include inactive, Include errors, Verify SSL)

3. **Start Processing**
   - Click "Start Processing" button or press `F5`
   - Watch real-time progress on the Progress tab
   - View statistics updating in real-time

4. **View Results**
   - Switch to "Results" tab to see all checked URLs
   - Sort by clicking column headers
   - Filter by status (All, Active, Inactive, Error)
   - Search for specific URLs in the filter box

5. **Export Results**
   - Click "Export Results..." button or press `Ctrl+S`
   - Choose format (CSV, Excel, or JSON)
   - Select save location

## User Interface

### Main Window Layout

```
┌────────────────────────────────────────────────────────────────┐
│ File  Help                                                     │
├───────────────┬────────────────────────────────────────────────┤
│               │                                                │
│ Control Panel │         Progress / Results / Statistics       │
│               │              (Tabbed Interface)                │
│ - File Select │                                                │
│ - Config      │                                                │
│ - Buttons     │                                                │
│               │                                                │
│               │                                                │
│               │                                                │
├───────────────┴────────────────────────────────────────────────┤
│ Status: Ready                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Control Panel (Left Sidebar)

**File Selection:**
- Input file path (read-only, click Browse to select)
- Browse button
- URL column name input (default: "url")

**Processing Configuration:**
- Batch Size: Number of URLs to process in each batch
- Concurrent Requests: Number of simultaneous HTTP requests
- Timeout: Maximum time to wait for each request (seconds)
- Retry Count: Number of retries for failed requests
- Include Inactive: Include inactive websites in results
- Include Errors: Include error websites in results
- Verify SSL: Verify SSL certificates

**Processing Controls:**
- Start Processing: Begin checking URLs
- Pause: (Not yet implemented)
- Stop: Stop processing (saves partial results)
- Export Results: Export results to file

### Progress Tab

Shows real-time progress during processing:

- **Status message**: Current operation status
- **Progress bar**: Visual progress indicator (0-100%)
- **Statistics**:
  - Total URLs
  - Processed
  - Active (green)
  - Inactive (orange)
  - Errors (red)
  - Processing rate (URLs/sec)
  - Elapsed time (HH:MM:SS)
  - Estimated time (HH:MM:SS)

### Results Tab

Interactive table showing all results:

- **Columns**:
  - URL: Original URL
  - Status: Active/Inactive/Error
  - Status Code: HTTP status code (200, 404, etc.)
  - Response Time: Time to receive response (ms or seconds)
  - Error Message: Error description if any
  - Final URL: URL after redirects

- **Features**:
  - Sorting: Click column headers to sort
  - Filtering: Filter by text or status
  - Context menu: Right-click for options
  - Color coding: Green (active), Orange (inactive), Red (error)

### Statistics Tab

Detailed statistics display:

- Processing summary
- Success rate breakdown
- Performance metrics
- Error breakdown by type
- Configuration used

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Export results |
| `Ctrl+Q` | Quit application |
| `F5` | Start/Resume processing |
| `Escape` | Stop processing |
| `F1` | Show About dialog |

## Configuration

The application saves your settings automatically in:
```
~/.website_status_checker/desktop_config.json
```

Saved settings include:
- Window size and position
- Last used directory
- Last used processing configuration
- UI preferences

To reset to defaults, delete this file.

## Input File Format

### CSV/Text Files

Your input file should have a column containing URLs. By default, the application looks for a column named "url", but you can specify a different column name.

Example CSV:
```csv
url,name
https://example.com,Example Site
https://google.com,Google
https://github.com,GitHub
```

### Excel Files

Excel files (.xlsx, .xls) are supported with the same column requirements.

## Output Format

Results are saved with the following columns:

| Column | Description |
|--------|-------------|
| url | Original URL from input file |
| status | Active, Inactive, Error, or Timeout |
| status_code | HTTP status code (200, 404, 500, etc.) |
| response_time | Response time in milliseconds |
| error | Error message if any |
| final_url | Final URL after following redirects |

## Performance Tips

1. **Batch Size**: Larger batches use more memory but may be faster
   - Small files (< 1000 URLs): 100-500
   - Medium files (1000-10000 URLs): 500-1000
   - Large files (> 10000 URLs): 1000-2000

2. **Concurrent Requests**: More concurrent requests = faster but higher resource usage
   - Conservative: 50-100
   - Moderate: 100-200
   - Aggressive: 200-500 (may overwhelm your network)

3. **Timeout**: Balance between speed and accuracy
   - Fast sites: 5-10 seconds
   - Slow sites: 15-30 seconds
   - Very slow sites: 30-60 seconds

4. **Memory**: For very large files (100K+ URLs), results are saved incrementally

## Troubleshooting

### Application won't start

**Problem**: Error importing tkinter
**Solution**: tkinter should be included with Python. If missing:
- Windows: Reinstall Python with "tcl/tk" option checked
- macOS: `brew install python-tk`
- Linux: `sudo apt-get install python3-tk`

### File won't load

**Problem**: "Cannot read file" error
**Solution**:
- Ensure file is valid CSV or Excel format
- Check that URL column exists
- Try opening file in Excel/spreadsheet software first
- Check file permissions

### Processing is slow

**Problem**: Processing takes too long
**Solution**:
- Increase concurrent requests (up to 200-500)
- Decrease timeout for fast sites
- Increase batch size
- Check your internet connection

### GUI freezes

**Problem**: Application becomes unresponsive
**Solution**: This shouldn't happen as processing runs in background thread. If it does:
- Stop processing and restart application
- Reduce concurrent requests
- Reduce batch size
- Report as bug

### Results not showing

**Problem**: Processing completes but no results displayed
**Solution**:
- Check if output file was created
- Switch to Results tab manually
- Try exporting results directly
- Check logs in ~/.website_status_checker/desktop_gui.log

## Known Limitations

1. **Pause functionality**: Not yet implemented (coming in future version)
2. **Resume from interruption**: Must restart processing from beginning
3. **Maximum URLs**: Tested up to 250,000 URLs (limited by available RAM)
4. **Network**: Respects system network limits

## Comparison with Web GUI

| Feature | Desktop GUI | Web GUI |
|---------|-------------|---------|
| Installation | Python only | Requires web server |
| Performance | Direct core integration | API overhead |
| UI Framework | tkinter (native) | HTML/CSS/JS |
| Deployment | Standalone executable | Requires hosting |
| Best For | Personal use, developers | Team use, remote access |

## Development

### Project Structure

```
desktop_gui/
├── app.py                      # Entry point
├── main_window.py              # Main window
├── widgets/                    # UI components
│   ├── control_panel.py        # Control panel
│   ├── progress_tab.py         # Progress display
│   ├── results_table.py        # Results table
│   └── stats_tab.py            # Statistics
├── controllers/                # Business logic
│   ├── file_controller.py      # File operations
│   ├── export_controller.py    # Export functionality
│   └── process_controller.py   # Processing orchestration
├── models/                     # Data models
│   ├── app_state.py            # State management
│   └── config.py               # Configuration
├── utils/                      # Utilities
│   ├── async_bridge.py         # Async/sync bridge
│   ├── formatters.py           # Display formatting
│   └── validators.py           # Input validation
└── resources/                  # Resources
    └── styles.py               # UI styles

```

## FAQ

**Q: Can I run this without the web GUI?**
A: Yes! The desktop GUI directly uses the core engine and doesn't require the web GUI or any server.

**Q: How many URLs can I process?**
A: Tested with up to 250,000 URLs. Actual limit depends on your available RAM.

**Q: Can I stop and resume processing?**
A: You can stop processing, and partial results are saved. Resume functionality will be added in a future version.

**Q: Does it work on macOS and Linux?**
A: Yes! tkinter is cross-platform and works on Windows, macOS, and Linux.

**Q: Can I process multiple files at once?**
A: Not currently. Process one file at a time.

**Q: Is there a dark mode?**
A: Not yet. Dark mode will be added in a future version.

## Support

For issues, questions, or feature requests:
1. Check the main project README.md
2. Check logs at ~/.website_status_checker/desktop_gui.log
3. Report issues at the project repository

## License

Same license as the main Website Status Checker project.

## Version History

### v1.0.0 (2026-01-09)
- Initial release
- File selection (CSV, Excel, TXT)
- Real-time progress tracking
- Results table with sorting and filtering
- Export to CSV, Excel, JSON
- Configuration persistence
- Cross-platform support (Windows, macOS, Linux)
