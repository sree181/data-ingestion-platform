"""
Source Configuration API Routes
================================

Modern API endpoints for managing data source configuration.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import structlog

from services.source_configuration_service import SourceConfigurationService
from auth.jwt_auth import get_current_user

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/source-config", tags=["source-configuration"])

# Initialize service
source_config_service = SourceConfigurationService()


# ============ Request/Response Models ============

class SourceConfigUpdate(BaseModel):
    """Model for updating source configuration"""
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    rate_limit_per_second: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    sync_frequency_hours: Optional[int] = None
    auto_sync_enabled: Optional[bool] = None
    custom_config: Optional[Dict[str, Any]] = None


class SourceToggle(BaseModel):
    """Model for toggling source on/off"""
    enabled: bool


# ============ API Endpoints ============

@router.get("/sources")
async def get_all_sources(
    include_disabled: bool = True
):
    """
    Get all data sources with configuration and status (PUBLIC - no auth required)
    
    Query Parameters:
        include_disabled: Include disabled sources (default: true)
    
    Returns:
        List of all configured data sources
    """
    try:
        sources = await source_config_service.get_all_sources(include_disabled)
        
        return {
            "success": True,
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{source_id}")
async def get_source(
    source_id: str
):
    """
    Get a specific source by ID (PUBLIC - no auth required)
    
    Path Parameters:
        source_id: Source identifier
    
    Returns:
        Source configuration and status
    """
    try:
        source = await source_config_service.get_source_by_id(source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        return {
            "success": True,
            "source": source
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sources/{source_id}")
async def update_source_config(
    source_id: str,
    config: SourceConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update source configuration
    
    Path Parameters:
        source_id: Source identifier
    
    Body:
        Configuration updates
    
    Returns:
        Updated source configuration
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        config_dict = config.dict(exclude_none=True)
        
        updated_source = await source_config_service.update_source_config(
            source_id, 
            config_dict
        )
        
        logger.info(
            f"Source {source_id} configuration updated",
            user_id=current_user.get("user_id"),
            fields_updated=list(config_dict.keys())
        )
        
        return {
            "success": True,
            "message": f"Source {source_id} configuration updated",
            "source": updated_source
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/toggle")
async def toggle_source(
    source_id: str,
    toggle: SourceToggle,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable or disable a source
    
    Path Parameters:
        source_id: Source identifier
    
    Body:
        enabled: true/false
    
    Returns:
        Updated source configuration
    """
    try:
        updated_source = await source_config_service.toggle_source(
            source_id, 
            toggle.enabled
        )
        
        action = "enabled" if toggle.enabled else "disabled"
        logger.info(
            f"Source {source_id} {action}",
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "message": f"Source {source_id} {action}",
            "source": updated_source
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/health-check")
async def check_source_health(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check health of a specific source
    
    Path Parameters:
        source_id: Source identifier
    
    Returns:
        Health status
    """
    try:
        health = await source_config_service.check_source_health(source_id)
        
        return {
            "success": True,
            "source_id": source_id,
            "health": health
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking health for {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_all_health():
    """
    Check health of all sources (PUBLIC - no auth required)
    
    Returns:
        Health status for all sources
    """
    try:
        health_summary = await source_config_service.check_all_health()
        
        return {
            "success": True,
            **health_summary
        }
        
    except Exception as e:
        logger.error(f"Error checking all health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/refresh")
async def refresh_source(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh/sync a source
    
    Path Parameters:
        source_id: Source identifier
    
    Returns:
        Refresh result
    """
    try:
        result = await source_config_service.refresh_source(source_id)
        
        logger.info(
            f"Source {source_id} refresh triggered",
            user_id=current_user.get("user_id"),
            success=result["success"]
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get overall statistics for all sources
    
    Returns:
        Statistics summary
    """
    try:
        stats = await source_config_service.get_source_statistics()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of source categories
    
    Returns:
        List of unique categories
    """
    try:
        sources = await source_config_service.get_all_sources()
        categories = list(set(s.get("category", "Other") for s in sources))
        categories.sort()
        
        return {
            "success": True,
            "categories": categories,
            "count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
