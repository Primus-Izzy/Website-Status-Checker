# Quick Start Guide

Get up and running with Website Status Checker in 5 minutes! 🚀

## 1. Installation

### Prerequisites
- Python 3.8 or higher
- 2GB+ RAM available
- Stable internet connection

### Install the Tool

```bash
# Clone the repository
git clone https://github.com/Primus-Izzy/website-status-checker.git
cd website-status-checker

# Create virtual environment (recommended)
python -m venv website-checker-env
source website-checker-env/bin/activate  # Linux/macOS
# or
website-checker-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. Prepare Your Data

### Create Input File

The tool supports CSV, Excel, and text files. Here's a simple CSV example:

```bash
# Create a sample input file
echo "url" > websites.csv
echo "https://isrealoyarinde.com" >> websites.csv
echo "https://contentika.com" >> websites.csv  
echo "https://spinah.com" >> websites.csv
echo "https://python.org" >> websites.csv
echo "https://this-site-does-not-exist-12345.com" >> websites.csv
```

### Input File Formats

**CSV Format:**
```csv
url
https://isrealoyarinde.com
https://contentika.com
https://spinah.com
```

**Excel Format:** Any column with URLs (specify column name with `--url-column`)

**Text Format:** One URL per line

## 3. Run Your First Check

### Basic Check
```bash
# Check websites and save active ones
python src/cli.py websites.csv --output results.csv
```

### View Results
```bash
# View the first few results
head -5 results.csv
```

Expected output:
```csv
url,normalized_url,status_result,status_code,error_category,error_message,response_time,timestamp,retry_count,final_url
https://google.com,https://google.com,active,200,,OK,0.234,1640995200.0,0,https://www.google.com/
https://github.com,https://github.com,active,200,,OK,0.567,1640995200.5,0,https://github.com/
https://stackoverflow.com,https://stackoverflow.com,active,200,,OK,0.445,1640995201.0,0,https://stackoverflow.com/
https://example.com,https://example.com,active,200,,OK,0.334,1640995201.5,0,https://example.com/
```

## 4. Common Use Cases

### High-Performance Processing

For large datasets (10K+ URLs):

```bash
python src/cli.py large_dataset.csv \
  --output results.csv \
  --concurrent 200 \
  --batch-size 2000 \
  --timeout 10
```

### Include All Results

To see inactive and error websites too:

```bash
python src/cli.py websites.csv \
  --output complete_results.csv \
  --include-inactive \
  --include-errors
```

### Debug Mode

For troubleshooting issues:

```bash  
python src/cli.py websites.csv \
  --output debug_results.csv \
  --verbose \
  --debug \
  --log-file debug.log
```

### Excel Input/Output

Process Excel files and output results as Excel:

```bash
python src/cli.py companies.xlsx \
  --url-column "Website URL" \
  --output active_companies.xlsx \
  --format xlsx
```

## 5. Understanding Results

### Status Types

| Status | Meaning | What It Tells You |
|--------|---------|------------------|
| `active` | ✅ Website is working (HTTP 200) | Website is accessible and responding |
| `inactive` | ⚠️ Website has issues (non-200 HTTP) | Website exists but has problems |
| `error` | ❌ Website is unreachable | DNS, connection, or SSL errors |
| `timeout` | 🕐 Website is too slow | Server is slow or unresponsive |
| `invalid_url` | 🔧 URL format is wrong | Fix the URL format |

### Key Columns in Results

- **url**: Original URL from your input
- **normalized_url**: Cleaned/standardized URL used for checking
- **status_result**: Website status (active, inactive, error, etc.)
- **status_code**: HTTP response code (200, 404, 500, etc.)
- **response_time**: How long the check took (seconds)
- **final_url**: URL after following redirects
- **error_message**: Details if there was an error

## 6. Performance Guide

### Start Small, Scale Up

```bash
# Test with 100 URLs first
head -100 large_dataset.csv > test_sample.csv
python src/cli.py test_sample.csv --output test_results.csv --verbose

# Then process the full dataset
python src/cli.py large_dataset.csv --output full_results.csv --concurrent 150
```

### Optimize for Your System

**For Fast Processing:**
```bash
--concurrent 300 --batch-size 5000 --timeout 5
```

**For Reliable Processing:**
```bash
--concurrent 100 --batch-size 1000 --timeout 15 --retry-count 3
```

**For Limited Memory:**
```bash
--memory-efficient --batch-size 500 --concurrent 50
```

### Monitor Progress

The tool shows real-time progress:
```
2025-01-15 10:30:15 - INFO - Progress: 5/50 batches (10.0%) | Processed: 5,000/50,000 URLs | Active: 3,750 (75.0%) | Rate: 125.5 URLs/sec | ETA: 00:06:23
```

## 7. Real Examples

### Example 1: Marketing Database Cleanup

**Scenario**: Clean a marketing database of 50,000 companies

```bash
# Process the database
python src/cli.py marketing_companies.csv \
  --url-column "Company Website" \
  --output active_companies.csv \
  --concurrent 200 \
  --batch-size 2000 \
  --report cleanup_report.json

# Results: Found 37,500 active websites (75% success rate)
```

### Example 2: SEO Link Audit

**Scenario**: Validate 10,000 backlinks for SEO audit

```bash
# Include all results for analysis
python src/cli.py backlinks.csv \
  --output link_audit.csv \
  --include-inactive \
  --include-errors \
  --format xlsx \
  --verbose

# Analyze results in Excel for SEO insights
```

### Example 3: Competitor Monitoring

**Scenario**: Monitor 500 competitor websites daily

```bash
# Quick daily check
python src/cli.py competitors.csv \
  --output daily_check_$(date +%Y%m%d).csv \
  --concurrent 50 \
  --timeout 20 \
  --log-file competitor_monitoring.log
```

## 8. Common Patterns

### Resume Interrupted Processing

If processing gets interrupted:

```bash
# Automatically resumes from where it left off
python src/cli.py large_dataset.csv --output results.csv --resume
```

### Generate Processing Report

```bash
# Get detailed statistics
python src/cli.py websites.csv \
  --output results.csv \
  --report processing_report.json

# View the report
cat processing_report.json
```

### Process Multiple Files

```bash
# Process multiple country files
for file in companies_*.csv; do
    echo "Processing $file..."
    python src/cli.py "$file" --output "active_$file" --concurrent 100
done
```

## 9. Troubleshooting Quick Fixes

### Problem: Too many connection errors
```bash
# Solution: Reduce concurrent requests
python src/cli.py input.csv --concurrent 50 --timeout 20
```

### Problem: Running out of memory
```bash
# Solution: Enable memory-efficient mode
python src/cli.py input.csv --memory-efficient --batch-size 500
```

### Problem: Processing too slow
```bash
# Solution: Increase concurrency (if your system can handle it)
python src/cli.py input.csv --concurrent 200 --timeout 5
```

### Problem: Many timeout errors
```bash
# Solution: Increase timeout duration
python src/cli.py input.csv --timeout 30 --retry-count 1
```

## 10. Next Steps

### For Production Use
- Read [CONFIGURATION.md](docs/CONFIGURATION.md) for advanced settings
- Check [PERFORMANCE.md](docs/PERFORMANCE.md) for optimization tips
- See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions

### For Developers
- Explore [API.md](docs/API.md) for programmatic usage
- Check the `examples/` directory for code samples
- Review [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

### Sample Output Analysis

After running the tool, you might see results like:

```
╔══════════════════════════════════════════════════════════════╗
║                    Website Status Checker                    ║
║              High-Performance URL Status Validation         ║
║                        Version 1.0.0                        ║
╚══════════════════════════════════════════════════════════════╝

2025-01-15 10:25:30 - INFO - Processing Configuration:
2025-01-15 10:25:30 - INFO -   Input file: websites.csv
2025-01-15 10:25:30 - INFO -   Output file: results.csv
2025-01-15 10:25:30 - INFO -   Batch size: 1000
2025-01-15 10:25:30 - INFO -   Concurrent requests: 100

2025-01-15 10:25:35 - INFO - Progress: 1/5 batches (20.0%) | Processed: 1,000/5,000 URLs | Active: 750 (75.0%) | Rate: 200.0 URLs/sec | ETA: 00:00:20

================================================================================
PROCESSING COMPLETE!
================================================================================
Total URLs processed: 5,000
Active websites found: 3,750 (75.00%)
Inactive websites: 875
Error websites: 375
Processing time: 0.42 minutes
Average rate: 198.4 URLs/second
Results saved to: results.csv
```

## 🎉 You're Ready!

You now have a powerful tool for checking website status at scale. Start with small datasets and gradually scale up as you become more comfortable with the options.

**Pro tip**: Always test with a small sample first to validate your configuration before processing large datasets!

---

**Need Help?** Check the `docs/` directory for detailed guides or create an issue on GitHub.