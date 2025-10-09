"""
Project Space MFA Enforcement API Endpoints
Provides endpoints for checking and enforcing MFA requirements
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict
import structlog
from auth.jwt_auth import get_current_user
from auth.space_mfa_enforcement import (
    require_space_mfa_verification,
    check_space_mfa_requirement,
    get_space_mfa_status
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/security/spaces", tags=["Space MFA Enforcement"])

@router.get("/{space_id}/mfa-status")
async def get_space_mfa_status_endpoint(
    space_id: str,
    user: Dict = Depends(get_current_user)
):
    """
    Get detailed MFA status for a project space
    
    This endpoint provides comprehensive MFA information for UI components
    to display appropriate messages and controls.
    
    Returns:
        Dict: Detailed MFA status information including:
        - space_id: Project space identifier
        - space_name: Human-readable space name
        - requires_mfa: Whether the space requires MFA
        - user_mfa_enabled: Whether the user has MFA enabled
        - user_mfa_verified: Whether the user has verified MFA in this session
        - access_allowed: Whether the user can access the space
        - mfa_setup_required: Whether the user needs to set up MFA
        - mfa_verification_required: Whether the user needs to verify MFA
        - security_classification: Space security level
        - compliance_frameworks: Applicable compliance frameworks
        - encryption_enabled: Whether encryption is enabled
    """
    try:
        return await get_space_mfa_status(space_id, user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get space MFA status", error=str(e), space_id=space_id, user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to get space MFA status")

@router.get("/{space_id}/mfa-requirement")
async def check_space_mfa_requirement_endpoint(
    space_id: str,
    user: Dict = Depends(get_current_user)
):
    """
    Check if a project space requires MFA without enforcing it
    
    This is useful for UI components that need to know if MFA is required
    but don't need to enforce it immediately.
    
    Returns:
        Dict: MFA requirement information including:
        - requires_mfa: Whether the space requires MFA
        - user_mfa_enabled: Whether the user has MFA enabled
        - user_mfa_verified: Whether the user has verified MFA in this session
        - access_allowed: Whether the user can access the space
        - space_id: Project space identifier
        - space_name: Human-readable space name
    """
    try:
        return await check_space_mfa_requirement(space_id, user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check space MFA requirement", error=str(e), space_id=space_id, user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to check space MFA requirement")

@router.post("/{space_id}/verify-mfa")
async def verify_space_mfa_access(
    space_id: str,
    user: Dict = Depends(get_current_user)
):
    """
    Verify MFA access for a project space
    
    This endpoint enforces MFA requirements for the specified space.
    It will return an error if MFA is required but not satisfied.
    
    Returns:
        Dict: Success response if MFA requirements are met
        
    Raises:
        HTTPException: If MFA is required but not satisfied
    """
    try:
        # This will raise an exception if MFA is required but not satisfied
        verified_user = await require_space_mfa_verification(space_id, None, user)
        
        return {
            "success": True,
            "message": "MFA verification successful",
            "space_id": space_id,
            "user_id": verified_user["user_id"],
            "mfa_verified": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to verify space MFA access", error=str(e), space_id=space_id, user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to verify space MFA access")

@router.get("/mfa-required-spaces")
async def get_mfa_required_spaces(
    user: Dict = Depends(get_current_user)
):
    """
    Get all spaces that require MFA for the current user
    
    This endpoint returns a list of spaces that require MFA,
    along with the user's MFA status for each space.
    
    Returns:
        Dict: List of MFA-required spaces with status information
    """
    try:
        # This would need to be implemented in the spaces service
        # For now, return a placeholder response
        return {
            "mfa_required_spaces": [],
            "user_mfa_enabled": user.get("mfa_enabled", False),
            "user_mfa_verified": user.get("mfa_verified", False),
            "total_spaces": 0
        }
    except Exception as e:
        logger.error("Failed to get MFA required spaces", error=str(e), user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="Failed to get MFA required spaces")
