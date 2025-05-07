from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from src.database import get_db
from src.controllers.analytics_controller import AnalyticsController
from src.models.marketing_project import ReportType
from src.schemas.marketing_project import (
    AnalyticsReportCreate, AnalyticsReportUpdate, AnalyticsReportRead
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["analytics reports"],
    responses={404: {"description": "Not found"}}
)


@router.post("/{project_id}/reports", response_model=AnalyticsReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    project_id: int,
    report_data: AnalyticsReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new analytics report for a project
    """
    return await AnalyticsController.create_report(project_id, report_data, db)


@router.post("/{project_id}/reports/upload", response_model=AnalyticsReportRead, status_code=status.HTTP_201_CREATED)
async def upload_report_file(
    project_id: int,
    file: UploadFile = File(...),
    title: str = Query(..., description="Report title"),
    report_type: ReportType = Query(..., description="Report type"),
    description: Optional[str] = Query(None, description="Report description"),
    period_start: Optional[datetime] = Query(None, description="Report period start date"),
    period_end: Optional[datetime] = Query(None, description="Report period end date"),
    insights: Optional[str] = Query(None, description="Report insights"),
    recommendations: Optional[str] = Query(None, description="Report recommendations"),
    creator_id: int = Query(..., description="Creator user ID"),
    is_draft: bool = Query(True, description="Whether this is a draft report"),
    metrics_json: Optional[str] = Query(None, description="Report metrics as JSON string"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file as an analytics report for a project
    """
    return await AnalyticsController.upload_report_file(
        project_id, file, title, report_type, description, 
        period_start, period_end, insights, recommendations,
        creator_id, is_draft, metrics_json, db
    )


@router.get("/{project_id}/reports", response_model=List[AnalyticsReportRead])
async def get_project_reports(
    project_id: int,
    report_type: Optional[ReportType] = None,
    is_draft: Optional[bool] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    creator_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all analytics reports for a project with optional filtering
    """
    return await AnalyticsController.get_project_reports(
        project_id, report_type, is_draft, period_start, 
        period_end, creator_id, search, db
    )


@router.get("/{project_id}/reports/{report_id}", response_model=AnalyticsReportRead)
async def get_report(
    project_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific analytics report
    """
    return await AnalyticsController.get_report(project_id, report_id, db)


@router.put("/{project_id}/reports/{report_id}", response_model=AnalyticsReportRead)
async def update_report(
    project_id: int,
    report_id: int,
    report_data: AnalyticsReportUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an analytics report
    """
    return await AnalyticsController.update_report(project_id, report_id, report_data, db)


@router.delete("/{project_id}/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    project_id: int,
    report_id: int,
    delete_file: bool = Query(False, description="Whether to delete the physical file"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an analytics report
    """
    await AnalyticsController.delete_report(project_id, report_id, delete_file, db)


@router.put("/{project_id}/reports/{report_id}/publish", response_model=AnalyticsReportRead)
async def publish_report(
    project_id: int,
    report_id: int,
    approved_by_id: int = Query(..., description="User ID of the approver"),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a draft report (mark as final)
    """
    return await AnalyticsController.publish_report(project_id, report_id, approved_by_id, db)


@router.get("/{project_id}/dashboard", response_model=Dict[str, Any])
async def get_project_dashboard(
    project_id: int,
    period_days: int = Query(30, description="Period in days for the dashboard data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard data for a project (summary of key metrics)
    """
    return await AnalyticsController.get_project_dashboard(project_id, period_days, db)
