"""
Multi-Source Ingestion API Routes
=================================

API endpoints for ingesting documents from external data sources.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.unified_ingestion_service import unified_ingestion_service
from auth.jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["multi-source-ingestion"])

# Use the global unified service instance

@router.post("/start")
async def start_ingestion_job(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new multi-source ingestion job
    
    Args:
        request: Ingestion request containing:
            - project_space_id: Target project space ID
            - query: Search query
            - sources: List of source IDs to search (optional)
            - max_results_per_source: Max results per source (default: 100)
            - filters: Additional filters (optional)
            - options: Processing options (optional)
    
    Returns:
        Job information including job_id for tracking
    """
    try:
        # Validate required fields
        if not request.get("project_space_id"):
            raise HTTPException(status_code=400, detail="project_space_id is required")
        
        if not request.get("query"):
            raise HTTPException(status_code=400, detail="query is required")
        
        # Extract parameters
        project_space_id = request["project_space_id"]
        query = request["query"]
        sources = request.get("sources")
        max_results_per_source = request.get("max_results_per_source", 100)
        filters = request.get("filters", {})
        # Support both 'options' and 'processing_options' for backward compatibility
        options = request.get("processing_options", request.get("options", {}))
        
        # Validate max_results_per_source
        if max_results_per_source < 1 or max_results_per_source > 1000:
            raise HTTPException(
                status_code=400, 
                detail="max_results_per_source must be between 1 and 1000"
            )
        
        # Start ingestion job
        job_id = await unified_ingestion_service.start_ingestion(
            query=query,
            sources=sources,
            max_results_per_source=max_results_per_source,
            space_id=project_space_id,
            processing_options=options
        )
        
        logger.info(
            f"Started ingestion job {job_id}",
            user_id=current_user.get("user_id"),
            project_space_id=project_space_id,
            query=query,
            sources=sources
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Ingestion job started successfully",
            "project_space_id": project_space_id,
            "query": query,
            "sources": sources or "all enabled sources",
            "max_results_per_source": max_results_per_source
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start ingestion job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start ingestion job")

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of an ingestion job
    
    Args:
        job_id: Job ID to check status for
    
    Returns:
        Job status information
    """
    try:
        job_status = await unified_ingestion_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job status")

@router.get("/jobs")
async def list_jobs(
    project_space_id: Optional[str] = Query(None, description="Filter by project space ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    List all ingestion jobs
    
    Args:
        project_space_id: Optional project space ID to filter by
    
    Returns:
        List of ingestion jobs
    """
    try:
        jobs = await unified_ingestion_service.list_jobs(project_space_id)
        
        return {
            "jobs": jobs,
            "total": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a running ingestion job
    
    Args:
        job_id: Job ID to cancel
    
    Returns:
        Cancellation status
    """
    try:
        success = await ingestion_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        logger.info(f"Cancelled ingestion job {job_id}", user_id=current_user.get("user_id"))
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.get("/sources")
async def get_available_sources(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of available data sources for ingestion
    
    Returns:
        List of available sources with their status
    """
    try:
        # Get enabled sources
        enabled_sources = ingestion_service._get_enabled_sources()
        
        # Get all source information
        all_sources = ingestion_service.registry.get_all_source_info()
        
        sources = []
        for source_info in all_sources:
            sources.append({
                "id": source_info.name,
                "display_name": source_info.display_name,
                "enabled": source_info.is_enabled,
                "source_type": source_info.source_type.value,
                "requires_api_key": getattr(source_info.connector_class(), 'requires_api_key', False)
            })
        
        return {
            "sources": sources,
            "enabled_count": len(enabled_sources),
            "total_count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get available sources")

@router.post("/sources/{source_id}/enable")
async def enable_source(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable a data source for ingestion
    
    Args:
        source_id: Source ID to enable
    
    Returns:
        Enable status
    """
    try:
        # Check if source exists
        source_info = ingestion_service.registry.get_source_info(source_id)
        if not source_info:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Enable source
        ingestion_service.registry.enable_source(source_id)
        
        logger.info(f"Enabled source {source_id}", user_id=current_user.get("user_id"))
        
        return {
            "source_id": source_id,
            "status": "enabled",
            "message": f"Source {source_id} enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enable source")

@router.post("/sources/{source_id}/disable")
async def disable_source(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable a data source for ingestion
    
    Args:
        source_id: Source ID to disable
    
    Returns:
        Disable status
    """
    try:
        # Check if source exists
        source_info = ingestion_service.registry.get_source_info(source_id)
        if not source_info:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Disable source
        ingestion_service.registry.disable_source(source_id)
        
        logger.info(f"Disabled source {source_id}", user_id=current_user.get("user_id"))
        
        return {
            "source_id": source_id,
            "status": "disabled",
            "message": f"Source {source_id} disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable source: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disable source")

@router.get("/health")
async def get_ingestion_health(
    current_user: dict = Depends(get_current_user)
):
    """
    Get health status of the ingestion service
    
    Returns:
        Health status information
    """
    try:
        # Get active jobs count
        active_jobs = await ingestion_service.list_jobs()
        running_jobs = [job for job in active_jobs if job["status"] == "running"]
        
        # Get source health
        enabled_sources = ingestion_service._get_enabled_sources()
        
        return {
            "status": "healthy",
            "active_jobs": len(active_jobs),
            "running_jobs": len(running_jobs),
            "enabled_sources": len(enabled_sources),
            "enabled_source_ids": enabled_sources,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ingestion health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get ingestion health")
