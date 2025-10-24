"""
Access Control API Routes

This module provides API endpoints for IP whitelist, domain restrictions,
and geographic access control management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime

from models.access_control import (
    AccessControlRequest, AccessControlUpdateRequest, AccessControlTestRequest,
    AccessControlPolicy, IPRange, DomainRestriction, GeographicRestriction,
    TimeRestriction, AccessControlRule, AccessLogEntry
)
from services.access_control_service import AccessControlService
from models.project_spaces import SpacePermission
from auth.space_mfa_enforcement import require_space_mfa_verification
from auth.space_permissions import require_space_permission
from database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/access-control", tags=["Access Control"])


@router.post("/configure")
async def configure_access_control(
    request: AccessControlRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.ADMIN))
):
    """
    Configure access control policy for a project space.
    Requires ADMIN permission and MFA verification for sensitive configurations.
    """
    logger.info("Configuring access control", space_id=request.space_id, user_id=current_user.get("user_id"))
    
    try:
        # Check MFA requirement for sensitive access control configurations
        sensitive_configs = [
            len(request.ip_whitelist or []) > 10,  # Large IP whitelist
            len(request.geographic_restrictions or []) > 0,  # Geographic restrictions
            request.default_action == "deny"  # Restrictive default action
        ]
        
        if any(sensitive_configs):
            await require_space_mfa_verification(request.space_id, None, current_user)
        
        access_control_service = AccessControlService(db_session)
        
        policy = await access_control_service.create_access_control_policy(
            space_id=request.space_id,
            policy_name=request.policy_name,
            description=request.description,
            ip_whitelist=request.ip_whitelist,
            ip_blacklist=request.ip_blacklist,
            allowed_domains=request.allowed_domains,
            blocked_domains=request.blocked_domains,
            geographic_restrictions=request.geographic_restrictions,
            time_restrictions=request.time_restrictions,
            default_action=request.default_action,
            enable_logging=request.enable_logging,
            enable_notifications=request.enable_notifications,
            created_by=current_user.get("user_id", "system")
        )
        
        logger.info("Access control configured successfully", space_id=request.space_id)
        
        return {
            "success": True,
            "message": "Access control policy configured successfully",
            "policy": policy.dict()
        }
        
    except PermissionError as e:
        logger.warning("Permission denied for access control configuration", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning("Invalid access control configuration", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to configure access control", 
                    space_id=request.space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure access control: {str(e)}"
        )


@router.get("/policy/{space_id}")
async def get_access_control_policy(
    space_id: str,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Get access control policy for a project space.
    Requires READ permission.
    """
    logger.info("Getting access control policy", space_id=space_id, user_id=current_user.get("user_id"))
    
    try:
        access_control_service = AccessControlService(db_session)
        policy = await access_control_service.get_access_control_policy(space_id)
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access control policy not found for this space"
            )
        
        logger.info("Access control policy retrieved", space_id=space_id)
        
        return {
            "success": True,
            "policy": policy.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get access control policy", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access control policy: {str(e)}"
        )


@router.put("/policy/{space_id}")
async def update_access_control_policy(
    space_id: str,
    request: AccessControlUpdateRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.ADMIN))
):
    """
    Update access control policy for a project space.
    Requires ADMIN permission and MFA verification for sensitive changes.
    """
    logger.info("Updating access control policy", space_id=space_id, user_id=current_user.get("user_id"))
    
    try:
        # Check MFA requirement for sensitive changes
        sensitive_changes = [
            len(request.ip_whitelist or []) > 10,  # Large IP whitelist changes
            len(request.geographic_restrictions or []) > 0,  # Geographic restrictions
            request.default_action == "deny"  # Restrictive default action
        ]
        
        if any(sensitive_changes):
            await require_space_mfa_verification(space_id, None, current_user)
        
        access_control_service = AccessControlService(db_session)
        
        policy = await access_control_service.update_access_control_policy(
            space_id=space_id,
            policy_name=request.policy_name,
            description=request.description,
            ip_whitelist=request.ip_whitelist,
            ip_blacklist=request.ip_blacklist,
            allowed_domains=request.allowed_domains,
            blocked_domains=request.blocked_domains,
            geographic_restrictions=request.geographic_restrictions,
            time_restrictions=request.time_restrictions,
            default_action=request.default_action,
            enable_logging=request.enable_logging,
            enable_notifications=request.enable_notifications,
            modified_by=current_user.get("user_id", "system")
        )
        
        logger.info("Access control policy updated successfully", space_id=space_id)
        
        return {
            "success": True,
            "message": "Access control policy updated successfully",
            "policy": policy.dict()
        }
        
    except PermissionError as e:
        logger.warning("Permission denied for access control update", 
                      space_id=space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning("Invalid access control update", 
                      space_id=space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update access control policy", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update access control policy: {str(e)}"
        )


@router.post("/test")
async def test_access_control(
    request: AccessControlTestRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Test access control rules for a given IP address and domain.
    Requires READ permission.
    """
    logger.info("Testing access control", space_id=request.space_id, user_id=current_user.get("user_id"))
    
    try:
        access_control_service = AccessControlService(db_session)
        
        result = await access_control_service.test_access_control(
            space_id=request.space_id,
            ip_address=request.ip_address,
            email_domain=request.email_domain,
            user_agent=request.user_agent,
            timestamp=request.timestamp
        )
        
        logger.info("Access control test completed", 
                   space_id=request.space_id, action=result.action)
        
        return {
            "success": True,
            "result": result.dict()
        }
        
    except ValueError as e:
        logger.warning("Invalid access control test", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to test access control", 
                    space_id=request.space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test access control: {str(e)}"
        )


@router.get("/logs/{space_id}")
async def get_access_logs(
    space_id: str,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Get access logs for a project space.
    Requires READ permission.
    """
    logger.info("Getting access logs", space_id=space_id, limit=limit, user_id=current_user.get("user_id"))
    
    try:
        access_control_service = AccessControlService(db_session)
        
        # Parse date strings
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        logs = await access_control_service.get_access_logs(
            space_id=space_id,
            limit=limit,
            offset=offset,
            start_date=start_dt,
            end_date=end_dt,
            action=action
        )
        
        logger.info("Access logs retrieved", space_id=space_id, count=len(logs))
        
        return {
            "success": True,
            "logs": [log.dict() for log in logs],
            "total": len(logs)
        }
        
    except Exception as e:
        logger.error("Failed to get access logs", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access logs: {str(e)}"
        )


@router.post("/enforce/{space_id}")
async def enforce_access_control(
    space_id: str,
    request: Request,
    db_session=Depends(get_db)
):
    """
    Enforce access control for a request.
    This endpoint is called by the middleware to check access permissions.
    """
    logger.info("Enforcing access control", space_id=space_id)
    
    try:
        # Get client IP address
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "")
        
        # Get user ID from headers (set by auth middleware)
        user_id = request.headers.get("x-user-id")
        
        access_control_service = AccessControlService(db_session)
        
        # Test access control
        result = await access_control_service.test_access_control(
            space_id=space_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Log the access attempt
        await access_control_service.log_access_attempt(
            space_id=space_id,
            ip_address=client_ip,
            action=result.action,
            user_id=user_id,
            user_agent=user_agent,
            reason=result.reason,
            metadata=result.metadata
        )
        
        # Return access control decision
        if result.action == "deny":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {result.reason}"
            )
        elif result.action == "challenge":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Access requires additional verification: {result.reason}"
            )
        
        logger.info("Access control enforced", space_id=space_id, action=result.action)
        
        return {
            "success": True,
            "action": result.action,
            "reason": result.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to enforce access control", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enforce access control: {str(e)}"
        )


@router.get("/ip-ranges")
async def get_ip_range_templates():
    """
    Get common IP range templates for easy configuration.
    No authentication required.
    """
    logger.info("Getting IP range templates")
    
    try:
        templates = {
            "common_ranges": [
                {
                    "name": "Office Network",
                    "description": "Typical office network range",
                    "ip_address": "192.168.1.0/24",
                    "range_type": "cidr_block"
                },
                {
                    "name": "VPN Network",
                    "description": "VPN client range",
                    "ip_address": "10.0.0.0/8",
                    "range_type": "cidr_block"
                },
                {
                    "name": "Cloud Provider",
                    "description": "AWS EC2 range",
                    "ip_address": "3.0.0.0/8",
                    "range_type": "cidr_block"
                }
            ],
            "range_types": [
                {"value": "single_ip", "name": "Single IP", "description": "Individual IP address"},
                {"value": "cidr_block", "name": "CIDR Block", "description": "Network range (e.g., 192.168.1.0/24)"},
                {"value": "ip_range", "name": "IP Range", "description": "Range of IPs (e.g., 192.168.1.1-192.168.1.100)"},
                {"value": "wildcard", "name": "Wildcard", "description": "Pattern matching (e.g., 192.168.*.*)"}
            ]
        }
        
        return {
            "success": True,
            "templates": templates
        }
        
    except Exception as e:
        logger.error("Failed to get IP range templates", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get IP range templates: {str(e)}"
        )


@router.get("/domain-templates")
async def get_domain_templates():
    """
    Get common domain templates for easy configuration.
    No authentication required.
    """
    logger.info("Getting domain templates")
    
    try:
        templates = {
            "common_domains": [
                {
                    "name": "Company Domain",
                    "description": "Internal company email domain",
                    "domain": "company.com",
                    "domain_type": "email_domain"
                },
                {
                    "name": "Partner Domain",
                    "description": "Partner organization domain",
                    "domain": "partner.com",
                    "domain_type": "email_domain"
                },
                {
                    "name": "Wildcard Subdomain",
                    "description": "All subdomains of a domain",
                    "domain": "*.company.com",
                    "domain_type": "wildcard_domain"
                }
            ],
            "domain_types": [
                {"value": "email_domain", "name": "Email Domain", "description": "Exact email domain match"},
                {"value": "allowed_domains", "name": "Allowed Domains", "description": "List of allowed domains"},
                {"value": "blocked_domains", "name": "Blocked Domains", "description": "List of blocked domains"},
                {"value": "wildcard_domain", "name": "Wildcard Domain", "description": "Pattern matching (e.g., *.company.com)"}
            ]
        }
        
        return {
            "success": True,
            "templates": templates
        }
        
    except Exception as e:
        logger.error("Failed to get domain templates", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get domain templates: {str(e)}"
        )


@router.get("/geographic-regions")
async def get_geographic_regions():
    """
    Get available geographic regions for access control.
    No authentication required.
    """
    logger.info("Getting geographic regions")
    
    try:
        regions = [
            {"value": "north_america", "name": "North America", "description": "United States, Canada, Mexico"},
            {"value": "south_america", "name": "South America", "description": "Brazil, Argentina, Chile, etc."},
            {"value": "europe", "name": "Europe", "description": "EU countries and UK"},
            {"value": "asia", "name": "Asia", "description": "China, Japan, India, etc."},
            {"value": "africa", "name": "Africa", "description": "African countries"},
            {"value": "oceania", "name": "Oceania", "description": "Australia, New Zealand, etc."},
            {"value": "middle_east", "name": "Middle East", "description": "Middle Eastern countries"},
            {"value": "custom", "name": "Custom", "description": "Custom country list"}
        ]
        
        return {
            "success": True,
            "regions": regions
        }
        
    except Exception as e:
        logger.error("Failed to get geographic regions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get geographic regions: {str(e)}"
        )
