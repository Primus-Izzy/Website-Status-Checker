"""Statistics API Endpoint"""

from fastapi import APIRouter, HTTPException
from gui.services.file_handler import FileHandler
from gui.models.schemas import StatisticsResponse
import pandas as pd
from collections import Counter

router = APIRouter()
file_handler = FileHandler()


@router.get("/{job_id}", response_model=StatisticsResponse)
async def get_statistics(job_id: str):
    """
    Get comprehensive statistics for a job.

    Args:
        job_id: Job identifier

    Returns:
        StatisticsResponse with detailed statistics
    """
    try:
        # Get results file
        results_file = file_handler.get_export_path(job_id, "csv")

        if not results_file.exists():
            raise HTTPException(status_code=404, detail="Results not found")

        # Read results
        df = pd.read_csv(results_file)

        # Count by status
        status_counts = df['status_result'].value_counts().to_dict()

        # Error breakdown
        error_df = df[df['error_category'].notna()]
        error_breakdown = error_df['error_category'].value_counts().to_dict()

        # Response time statistics
        valid_times = df[df['response_time'] > 0]['response_time']
        response_time_avg = float(valid_times.mean()) if len(valid_times) > 0 else 0.0
        response_time_min = float(valid_times.min()) if len(valid_times) > 0 else 0.0
        response_time_max = float(valid_times.max()) if len(valid_times) > 0 else 0.0

        # Calculate processing rate (if available)
        processing_rate = 0.0
        if 'timestamp' in df.columns and len(df) > 1:
            time_range = df['timestamp'].max() - df['timestamp'].min()
            if time_range > 0:
                processing_rate = len(df) / time_range

        return StatisticsResponse(
            job_id=job_id,
            active_count=status_counts.get('active', 0),
            inactive_count=status_counts.get('inactive', 0),
            error_count=status_counts.get('error', 0),
            timeout_count=status_counts.get('timeout', 0),
            invalid_url_count=status_counts.get('invalid_url', 0),
            error_breakdown=error_breakdown,
            response_time_avg=response_time_avg,
            response_time_min=response_time_min,
            response_time_max=response_time_max,
            processing_rate=processing_rate
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")
