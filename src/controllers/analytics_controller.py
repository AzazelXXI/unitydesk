from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import os
import json
import shutil
from uuid import uuid4
from fastapi import HTTPException, status, UploadFile

from src.database import get_db
from src.models.marketing_project import (
    MarketingProject, AnalyticsReport, ReportType
)
from src.schemas.marketing_project import (
    AnalyticsReportCreate, AnalyticsReportUpdate, AnalyticsReportRead
)

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsController:
    """Controller for handling analytics report operations"""
    
    @staticmethod
    async def create_report(
        project_id: int,
        report_data: AnalyticsReportCreate,
        db: AsyncSession
    ) -> AnalyticsReport:
        """
        Create a new analytics report for a project
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Create the report
            new_report = AnalyticsReport(
                project_id=project_id,
                report_type=report_data.report_type,
                title=report_data.title,
                description=report_data.description,
                content=report_data.content,
                insights=report_data.insights,
                recommendations=report_data.recommendations,
                period_start=report_data.period_start,
                period_end=report_data.period_end,
                is_draft=report_data.is_draft,
                creator_id=report_data.creator_id,
                approved_by_id=report_data.approved_by_id,
                file_path=report_data.file_path,
                file_url=report_data.file_url,
                metrics=report_data.metrics
            )
            
            db.add(new_report)
            await db.commit()
            await db.refresh(new_report)
            
            logger.info(f"Created new analytics report: {new_report.title} for project {project_id}")
            
            # Return the created report with related info
            report_query = select(AnalyticsReport).filter(
                AnalyticsReport.id == new_report.id
            ).options(
                joinedload(AnalyticsReport.creator),
                joinedload(AnalyticsReport.approved_by),
                joinedload(AnalyticsReport.project)
            )
            
            result = await db.execute(report_query)
            report = result.scalars().first()
            
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating analytics report for project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create analytics report: {str(e)}"
            )
    
    @staticmethod
    async def upload_report_file(
        project_id: int,
        file: UploadFile,
        title: str,
        report_type: ReportType,
        description: Optional[str],
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        insights: Optional[str],
        recommendations: Optional[str],
        creator_id: int,
        is_draft: bool,
        metrics_json: Optional[str],
        db: AsyncSession
    ) -> AnalyticsReport:
        """
        Upload a file as an analytics report for a project
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Create directory for project reports if it doesn't exist
            upload_dir = f"uploads/projects/{project_id}/reports"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid4()}{file_extension}"
            file_path = f"{upload_dir}/{unique_filename}"
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Validate metrics JSON if provided
            if metrics_json:
                try:
                    json.loads(metrics_json)
                except json.JSONDecodeError:
                    logger.error(f"Invalid metrics JSON provided")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid metrics JSON format"
                    )
            
            # Create report in database
            new_report = AnalyticsReport(
                project_id=project_id,
                report_type=report_type,
                title=title,
                description=description,
                period_start=period_start,
                period_end=period_end,
                insights=insights,
                recommendations=recommendations,
                is_draft=is_draft,
                creator_id=creator_id,
                file_path=file_path,
                file_url=f"/api/reports/{unique_filename}",
                metrics=metrics_json
            )
            
            db.add(new_report)
            await db.commit()
            await db.refresh(new_report)
            
            logger.info(f"Uploaded new analytics report: {new_report.title} for project {project_id}")
            
            # Return the created report with related info
            report_query = select(AnalyticsReport).filter(
                AnalyticsReport.id == new_report.id
            ).options(
                joinedload(AnalyticsReport.creator),
                joinedload(AnalyticsReport.project)
            )
            
            result = await db.execute(report_query)
            report = result.scalars().first()
            
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading analytics report for project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload analytics report: {str(e)}"
            )
    
    @staticmethod
    async def get_project_reports(
        project_id: int,
        report_type: Optional[ReportType],
        is_draft: Optional[bool],
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        creator_id: Optional[int],
        search: Optional[str],
        db: AsyncSession
    ) -> List[AnalyticsReport]:
        """
        Get all analytics reports for a project with optional filtering
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Build query with filters
            query = select(AnalyticsReport).filter(AnalyticsReport.project_id == project_id)
            
            if report_type:
                query = query.filter(AnalyticsReport.report_type == report_type)
            if is_draft is not None:
                query = query.filter(AnalyticsReport.is_draft == is_draft)
            if period_start:
                query = query.filter(AnalyticsReport.period_start >= period_start)
            if period_end:
                query = query.filter(AnalyticsReport.period_end <= period_end)
            if creator_id:
                query = query.filter(AnalyticsReport.creator_id == creator_id)
            if search:
                query = query.filter(AnalyticsReport.title.ilike(f"%{search}%"))
            
            # Sort by created_at descending (newest first)
            query = query.order_by(desc(AnalyticsReport.created_at))
            
            # Add eager loading
            query = query.options(
                joinedload(AnalyticsReport.creator),
                joinedload(AnalyticsReport.approved_by),
                joinedload(AnalyticsReport.project)
            )
            
            # Execute query
            result = await db.execute(query)
            reports = result.scalars().all()
            
            return reports
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching reports for project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch reports: {str(e)}"
            )
    
    @staticmethod
    async def get_report(
        project_id: int,
        report_id: int,
        db: AsyncSession
    ) -> AnalyticsReport:
        """
        Get a specific analytics report
        """
        try:
            # Query with eager loading
            query = select(AnalyticsReport).filter(
                AnalyticsReport.project_id == project_id,
                AnalyticsReport.id == report_id
            ).options(
                joinedload(AnalyticsReport.creator),
                joinedload(AnalyticsReport.approved_by),
                joinedload(AnalyticsReport.project)
            )
            
            result = await db.execute(query)
            report = result.scalars().first()
            
            if not report:
                logger.warning(f"Report with ID {report_id} not found for project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with ID {report_id} not found for project {project_id}"
                )
            
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching analytics report {report_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch analytics report: {str(e)}"
            )
    
    @staticmethod
    async def update_report(
        project_id: int,
        report_id: int,
        report_data: AnalyticsReportUpdate,
        db: AsyncSession
    ) -> AnalyticsReport:
        """
        Update an analytics report
        """
        try:
            # Get the report
            query = select(AnalyticsReport).filter(
                AnalyticsReport.project_id == project_id,
                AnalyticsReport.id == report_id
            )
            
            result = await db.execute(query)
            report = result.scalars().first()
            
            if not report:
                logger.warning(f"Report with ID {report_id} not found for project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with ID {report_id} not found for project {project_id}"
                )
            
            # Update report attributes
            update_data = report_data.dict(exclude_unset=True)
            
            # If metrics is provided as JSON string, validate it
            if "metrics" in update_data and update_data["metrics"]:
                try:
                    json.loads(update_data["metrics"])
                except json.JSONDecodeError:
                    logger.error(f"Invalid metrics JSON provided")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid metrics JSON format"
                    )
            
            for key, value in update_data.items():
                if value is not None:
                    setattr(report, key, value)
            
            await db.commit()
            await db.refresh(report)
            
            logger.info(f"Updated analytics report {report_id} for project {project_id}")
            
            # Return the updated report with full details
            return await AnalyticsController.get_report(project_id, report_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating analytics report {report_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update analytics report: {str(e)}"
            )
    
    @staticmethod
    async def delete_report(
        project_id: int,
        report_id: int,
        delete_file: bool,
        db: AsyncSession
    ) -> None:
        """
        Delete an analytics report
        """
        try:
            # Get the report
            query = select(AnalyticsReport).filter(
                AnalyticsReport.project_id == project_id,
                AnalyticsReport.id == report_id
            )
            
            result = await db.execute(query)
            report = result.scalars().first()
            
            if not report:
                logger.warning(f"Report with ID {report_id} not found for project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with ID {report_id} not found for project {project_id}"
                )
            
            # Delete physical file if requested and exists
            if delete_file and report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                    logger.info(f"Deleted physical file: {report.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete physical file: {report.file_path}, error: {str(e)}")
            
            # Delete the report from database
            await db.delete(report)
            await db.commit()
            
            logger.info(f"Deleted analytics report {report_id} from project {project_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting analytics report {report_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete analytics report: {str(e)}"
            )
    
    @staticmethod
    async def publish_report(
        project_id: int,
        report_id: int,
        approved_by_id: int,
        db: AsyncSession
    ) -> AnalyticsReport:
        """
        Publish a draft report (mark as final)
        """
        try:
            # Get the report
            query = select(AnalyticsReport).filter(
                AnalyticsReport.project_id == project_id,
                AnalyticsReport.id == report_id
            )
            
            result = await db.execute(query)
            report = result.scalars().first()
            
            if not report:
                logger.warning(f"Report with ID {report_id} not found for project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with ID {report_id} not found for project {project_id}"
                )
            
            # Update report status
            report.is_draft = False
            report.approved_by_id = approved_by_id
            
            await db.commit()
            await db.refresh(report)
            
            logger.info(f"Published analytics report {report_id}")
            
            # Return the updated report
            return await AnalyticsController.get_report(project_id, report_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error publishing analytics report {report_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to publish report: {str(e)}"
            )
    
    @staticmethod
    async def get_project_dashboard(
        project_id: int,
        period_days: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get dashboard data for a project (summary of key metrics)
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get latest reports
            reports_query = select(AnalyticsReport).filter(
                AnalyticsReport.project_id == project_id,
                AnalyticsReport.is_draft == False
            ).order_by(
                desc(AnalyticsReport.created_at)
            ).limit(5)
            
            reports_result = await db.execute(reports_query)
            latest_reports = reports_result.scalars().all()
            
            # Extract metrics from reports
            metrics_collection = []
            for report in latest_reports:
                if report.metrics:
                    try:
                        metrics_data = json.loads(report.metrics)
                        metrics_collection.append({
                            "report_id": report.id,
                            "report_title": report.title,
                            "report_type": report.report_type,
                            "created_at": report.created_at,
                            "metrics": metrics_data
                        })
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in report {report.id} metrics")
            
            # Compile dashboard data
            dashboard_data = {
                "project_info": {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "current_stage": project.current_stage,
                    "start_date": project.start_date,
                    "target_end_date": project.target_end_date
                },
                "latest_reports": [
                    {
                        "id": report.id,
                        "title": report.title,
                        "report_type": report.report_type,
                        "created_at": report.created_at
                    }
                    for report in latest_reports
                ],
                "metrics_collection": metrics_collection,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": period_days
                }
            }
            
            return dashboard_data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating dashboard for project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate dashboard: {str(e)}"
            )
