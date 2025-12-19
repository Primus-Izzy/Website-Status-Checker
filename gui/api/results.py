"""Results API Endpoints"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from gui.services.file_handler import FileHandler
from gui.models.schemas import ResultsResponse
import pandas as pd
from typing import Optional
import math

router = APIRouter()
file_handler = FileHandler()


@router.get("/{job_id}", response_model=ResultsResponse)
async def get_results(
    job_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    filter_status: Optional[str] = None,
    sort_by: str = "url"
):
    """
    Get paginated results for a job.

    Args:
        job_id: Job identifier
        page: Page number (1-indexed)
        limit: Results per page
        filter_status: Filter by status (active, inactive, error)
        sort_by: Column to sort by

    Returns:
        ResultsResponse with paginated results
    """
    try:
        # Get results file
        results_file = file_handler.get_export_path(job_id, "csv")

        if not results_file.exists():
            raise HTTPException(status_code=404, detail="Results not found")

        # Read results
        df = pd.read_csv(results_file)

        # Apply filter
        if filter_status:
            df = df[df['status_result'] == filter_status]

        # Sort
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by)

        # Calculate pagination
        total_count = len(df)
        total_pages = math.ceil(total_count / limit)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # Get page data
        page_data = df.iloc[start_idx:end_idx]

        # Convert to dict
        results_list = page_data.to_dict('records')

        return ResultsResponse(
            job_id=job_id,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            results=results_list
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading results: {str(e)}")


@router.get("/{job_id}/export")
async def export_results(job_id: str, format: str = Query("csv", regex="^(csv|json|xlsx)$")):
    """
    Export results in specified format.

    Args:
        job_id: Job identifier
        format: Export format (csv, json, xlsx)

    Returns:
        FileResponse with results file
    """
    try:
        # Get source results
        results_file = file_handler.get_export_path(job_id, "csv")

        if not results_file.exists():
            raise HTTPException(status_code=404, detail="Results not found")

        # If requesting CSV, return directly
        if format == "csv":
            return FileResponse(
                results_file,
                media_type="text/csv",
                filename=f"results_{job_id}.csv"
            )

        # Convert to requested format
        df = pd.read_csv(results_file)

        export_path = file_handler.get_export_path(job_id, format)

        if format == "json":
            df.to_json(export_path, orient="records", indent=2)
            media_type = "application/json"
        elif format == "xlsx":
            df.to_excel(export_path, index=False)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return FileResponse(
            export_path,
            media_type=media_type,
            filename=f"results_{job_id}.{format}"
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting results: {str(e)}")
