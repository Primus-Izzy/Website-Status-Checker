# Website Status Checker - Web GUI

Modern web interface for the Website Status Checker with real-time progress tracking, interactive charts, and comprehensive results management.

## Features

- **Drag-and-Drop File Upload**: Easy CSV/Excel file upload
- **Real-Time Progress**: Live updates via Server-Sent Events (SSE)
- **Interactive Charts**: Visual status distribution and processing rate charts
- **Results Management**: Filter, sort, and export results
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### 1. Install Core Dependencies

First, install the base dependencies:

```bash
pip install -r requirements.txt
```

### 2. Install GUI Dependencies

Then install the GUI-specific dependencies:

```bash
pip install -r requirements-gui.txt
```

## Running the GUI

### Development Mode

Start the development server with hot reload:

```bash
# From the project root directory
python -m gui.main

# Or using uvicorn directly
uvicorn gui.main:app --reload --port 8000
```

### Production Mode

For production deployment:

```bash
# Using Gunicorn with Uvicorn workers
gunicorn gui.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Accessing the GUI

Once the server is running, open your browser and navigate to:

```
http://localhost:8000
```

## API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Usage Guide

### Step 1: Upload File

1. Click the upload area or drag and drop a CSV/Excel file
2. Supported formats: `.csv`, `.xlsx`, `.xls`
3. The file should contain a column with URLs (default column name: "url")

### Step 2: Configure Processing

1. Click "Configure & Start" after upload
2. Adjust settings:
   - **Batch Size**: Number of URLs to process in each batch (default: 1000)
   - **Concurrent Requests**: Maximum simultaneous requests (default: 100)
   - **Timeout**: Request timeout in seconds (default: 10)
   - **URL Column**: Name of the column containing URLs (default: "url")
   - **Include Inactive**: Include non-200 responses in results
   - **Include Errors**: Include failed requests in results

### Step 3: Monitor Progress

- View real-time progress bar
- See live statistics (Active, Inactive, Errors, Processing Rate, ETA)
- Watch interactive charts update in real-time

### Step 4: View & Export Results

- Filter results by status (All, Active, Inactive, Errors)
- View results in an interactive table
- Export results as CSV

## File Structure

```
gui/
├── main.py                  # FastAPI application entry point
├── api/                     # API endpoints
│   ├── upload.py
│   ├── process.py
│   ├── results.py
│   ├── stats.py
│   └── sse.py
├── services/                # Business logic
│   ├── job_manager.py
│   ├── file_handler.py
│   └── processor.py
├── models/                  # Data models
│   └── schemas.py
├── static/                  # Frontend files
│   ├── js/
│   │   ├── app.js
│   │   └── charts.js
│   └── css/
│       └── styles.css
├── templates/               # HTML templates
│   ├── base.html
│   └── index.html
├── uploads/                 # Temporary upload storage
└── exports/                 # Generated export files
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
uvicorn gui.main:app --port 8080
```

### CORS Issues

If accessing from a different domain, update CORS settings in `gui/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://yourdomain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Import Errors

Make sure you're running from the project root directory:

```bash
cd /path/to/Website-Status-Checker
python -m gui.main
```

## Performance Tips

### For Large Datasets (100K+ URLs)

- Increase batch size: 2000-5000
- Adjust concurrent requests based on your system: 200-500
- Use memory-efficient mode (handled automatically)

### System Resources

- **Memory**: Minimum 2GB RAM, 4GB+ recommended for large datasets
- **Network**: Stable internet connection
- **CPU**: Multi-core processor recommended for concurrent processing

## Security Notes

### Production Deployment

1. **Configure CORS properly**: Restrict to your domain
2. **Use HTTPS**: Deploy behind a reverse proxy (nginx, Apache)
3. **Set file size limits**: Configure maximum upload size
4. **Implement authentication**: Add auth middleware for production use
5. **Clean up old files**: Schedule periodic cleanup of uploads/exports

### Example nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # SSE specific
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## License

MIT License - See LICENSE file for details
