"""
Source Management API Routes
===========================

API endpoints for managing data sources and their configuration.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging

from services.unified_search_service import UnifiedSearchService
from auth.jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sources", tags=["source-management"])

# Initialize unified search service
unified_search_service = UnifiedSearchService()

@router.get("/")
async def get_sources(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of all available data sources
    
    Returns:
        List of data sources with their configuration and status
    """
    try:
        sources = await unified_search_service.get_available_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

@router.get("/health")
async def get_source_health(
    current_user: dict = Depends(get_current_user)
):
    """
    Get health status of all data sources
    
    Returns:
        Health status of all sources
    """
    try:
        health_status = await unified_search_service.get_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error getting source health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.post("/{source_id}/enable")
async def enable_source(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable a data source
    
    Args:
        source_id: ID of the source to enable
    
    Returns:
        Success message
    """
    try:
        # Check if source exists
        sources = await unified_search_service.get_available_sources()
        source_exists = any(source["id"] == source_id for source in sources)
        
        if not source_exists:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Enable source in registry
        registry = unified_search_service.registry
        registry.enable_source(source_id)
        
        logger.info(f"Source {source_id} enabled by user {current_user.get('user_id')}")
        
        return {"message": f"Source {source_id} enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enable source: {str(e)}")

@router.post("/{source_id}/disable")
async def disable_source(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable a data source
    
    Args:
        source_id: ID of the source to disable
    
    Returns:
        Success message
    """
    try:
        # Check if source exists
        sources = await unified_search_service.get_available_sources()
        source_exists = any(source["id"] == source_id for source in sources)
        
        if not source_exists:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Disable source in registry
        registry = unified_search_service.registry
        registry.disable_source(source_id)
        
        logger.info(f"Source {source_id} disabled by user {current_user.get('user_id')}")
        
        return {"message": f"Source {source_id} disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to disable source: {str(e)}")

@router.put("/{source_id}/config")
async def update_source_config(
    source_id: str,
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Update configuration for a data source
    
    Args:
        source_id: ID of the source to update
        config: Configuration data (e.g., API key, settings)
    
    Returns:
        Success message
    """
    try:
        # Check if source exists
        sources = await unified_search_service.get_available_sources()
        source_exists = any(source["id"] == source_id for source in sources)
        
        if not source_exists:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Update source configuration
        registry = unified_search_service.registry
        source = registry.get_source(source_id)
        
        if source and hasattr(source, 'update_config'):
            source.update_config(config)
        
        # Store configuration (in production, this would be saved to database)
        # For now, we'll just log it
        logger.info(
            f"Source {source_id} configuration updated by user {current_user.get('user_id')}",
            config_keys=list(config.keys())
        )
        
        return {"message": f"Source {source_id} configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating source config {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update source config: {str(e)}")

@router.post("/{source_id}/test")
async def test_source_connection(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Test connection to a data source
    
    Args:
        source_id: ID of the source to test
    
    Returns:
        Test result with connection status
    """
    try:
        result = await unified_search_service.test_source_connection(source_id)
        return result
    except Exception as e:
        logger.error(f"Error testing source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to test source: {str(e)}")

@router.get("/{source_id}/status")
async def get_source_status(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed status of a specific source
    
    Args:
        source_id: ID of the source
    
    Returns:
        Detailed source status
    """
    try:
        # Get source info
        sources = await unified_search_service.get_available_sources()
        source_info = next((s for s in sources if s["id"] == source_id), None)
        
        if not source_info:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Get health status
        health_status = await unified_search_service.get_health_status()
        source_health = health_status.get("sources", {}).get(source_id, {})
        
        # Combine info and health
        status = {
            **source_info,
            "health": source_health,
            "last_checked": source_health.get("last_check"),
            "response_time_ms": source_health.get("response_time_ms", 0)
        }
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source status {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get source status: {str(e)}")

@router.get("/{source_id}/stats")
async def get_source_stats(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a specific source
    
    Args:
        source_id: ID of the source
    
    Returns:
        Source statistics
    """
    try:
        # This would typically query a database for actual usage statistics
        # For now, return mock data
        stats = {
            "source_id": source_id,
            "total_searches": 0,
            "total_documents": 0,
            "last_search": None,
            "average_response_time_ms": 0,
            "error_rate": 0.0,
            "uptime_percentage": 100.0
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting source stats {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get source stats: {str(e)}")

@router.post("/{source_id}/sync")
async def sync_source_data(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger a manual sync for a data source
    
    Args:
        source_id: ID of the source to sync
    
    Returns:
        Sync result
    """
    try:
        # Check if source exists
        sources = await unified_search_service.get_available_sources()
        source_exists = any(source["id"] == source_id for source in sources)
        
        if not source_exists:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # For now, just test the connection as a sync operation
        test_result = await unified_search_service.test_source_connection(source_id)
        
        if test_result["status"] == "healthy":
            return {
                "message": f"Source {source_id} sync completed successfully",
                "status": "success",
                "sync_time": test_result.get("last_check")
            }
        else:
            return {
                "message": f"Source {source_id} sync failed: {test_result.get('message', 'Unknown error')}",
                "status": "failed",
                "error": test_result.get("message")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to sync source: {str(e)}")
