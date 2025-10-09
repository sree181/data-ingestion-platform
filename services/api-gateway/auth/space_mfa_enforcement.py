"""
Project Space MFA Enforcement
Implements MFA requirements based on project space security configuration
"""

from fastapi import Depends, HTTPException, Request
from typing import Dict, Optional
import structlog
from auth.jwt_auth import get_current_user, jwt_service
from services.project_spaces_service import ProjectSpacesService

logger = structlog.get_logger(__name__)

async def get_spaces_service() -> Optional[ProjectSpacesService]:
    """Get project spaces service instance"""
    try:
        # Import db_manager at runtime to get the current value
        from main import db_manager
        
        if db_manager is None or db_manager.pool is None:
            logger.warning("Database not available for MFA enforcement")
            return None
        
        return ProjectSpacesService(db_manager.pool)
    except Exception as e:
        logger.error("Failed to create spaces service for MFA enforcement", error=str(e))
        return None

async def require_space_mfa_verification(
    space_id: str,
    request: Request,
    user: Dict = Depends(get_current_user),
    spaces_service: Optional[ProjectSpacesService] = Depends(get_spaces_service)
) -> Dict:
    """
    FastAPI dependency to enforce MFA for project spaces that require it
    
    This dependency:
    1. Checks if the project space has requires_mfa=true
    2. If it does, verifies that the user has MFA enabled and verified
    3. If not, allows access without MFA
    
    Args:
        space_id: The project space ID to check
        request: FastAPI request object
        user: Current authenticated user
        spaces_service: Project spaces service instance
    
    Returns:
        Dict: User information if access is allowed
        
    Raises:
        HTTPException: If MFA is required but not verified
    """
    try:
        # If no spaces service available, skip MFA enforcement
        if spaces_service is None:
            logger.warning("Spaces service not available, skipping MFA enforcement")
            return user
        
        # Get project space details
        space = await spaces_service.get_space_by_id(space_id, user["user_id"])
        if not space:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        # Check if space requires MFA
        if not space.requires_mfa:
            logger.debug(f"Space {space_id} does not require MFA, allowing access")
            return user
        
        logger.info(f"Space {space_id} requires MFA, checking user MFA status")
        
        # Check if user has MFA enabled
        if not user.get("mfa_enabled", False):
            logger.warning(f"User {user['user_id']} attempted to access MFA-required space without MFA enabled")
            raise HTTPException(
                status_code=403, 
                detail={
                    "error": "MFA_REQUIRED",
                    "message": "This project space requires multi-factor authentication. Please enable MFA in your account settings.",
                    "space_id": space_id,
                    "space_name": space.name,
                    "action_required": "setup_mfa"
                }
            )
        
        # Check if MFA is verified in the current session
        if not user.get("mfa_verified", False):
            logger.warning(f"User {user['user_id']} attempted to access MFA-required space without MFA verification")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "MFA_VERIFICATION_REQUIRED", 
                    "message": "Multi-factor authentication verification required for this project space.",
                    "space_id": space_id,
                    "space_name": space.name,
                    "action_required": "verify_mfa"
                }
            )
        
        logger.info(f"User {user['user_id']} successfully accessed MFA-required space {space_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA enforcement check failed for space {space_id}", error=str(e), user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="MFA enforcement check failed")

async def check_space_mfa_requirement(
    space_id: str,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Check if a project space requires MFA without enforcing it
    
    This is useful for UI components that need to know if MFA is required
    but don't need to enforce it immediately.
    
    Args:
        space_id: The project space ID to check
        user: Current authenticated user
        spaces_service: Project spaces service instance
    
    Returns:
        Dict: MFA requirement information
    """
    try:
        # Get spaces service directly
        spaces_service = await get_spaces_service()
        
        # If no spaces service available, return default
        if spaces_service is None:
            return {
                "requires_mfa": False,
                "user_mfa_enabled": user.get("mfa_enabled", False),
                "user_mfa_verified": user.get("mfa_verified", False),
                "access_allowed": True
            }
        
        # Get project space details
        space = await spaces_service.get_space_by_id(space_id, user["user_id"])
        if not space:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        requires_mfa = space.requires_mfa
        user_mfa_enabled = user.get("mfa_enabled", False)
        user_mfa_verified = user.get("mfa_verified", False)
        
        # Determine if access is allowed
        access_allowed = not requires_mfa or (user_mfa_enabled and user_mfa_verified)
        
        return {
            "requires_mfa": requires_mfa,
            "user_mfa_enabled": user_mfa_enabled,
            "user_mfa_verified": user_mfa_verified,
            "access_allowed": access_allowed,
            "space_id": space_id,
            "space_name": space.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA requirement check failed for space {space_id}", error=str(e), user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="MFA requirement check failed")

async def get_space_mfa_status(
    space_id: str,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get detailed MFA status for a project space
    
    This endpoint provides comprehensive MFA information for UI components
    to display appropriate messages and controls.
    
    Args:
        space_id: The project space ID to check
        user: Current authenticated user
        spaces_service: Project spaces service instance
    
    Returns:
        Dict: Detailed MFA status information
    """
    try:
        # Get spaces service directly
        spaces_service = await get_spaces_service()
        
        # If no spaces service available, return default
        if spaces_service is None:
            return {
                "space_id": space_id,
                "space_name": "Unknown",
                "requires_mfa": False,
                "user_mfa_enabled": user.get("mfa_enabled", False),
                "user_mfa_verified": user.get("mfa_verified", False),
                "access_allowed": True,
                "mfa_setup_required": False,
                "mfa_verification_required": False,
                "security_classification": "internal"
            }
        
        # Get project space details
        space = await spaces_service.get_space_by_id(space_id, user["user_id"])
        if not space:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        requires_mfa = space.requires_mfa
        user_mfa_enabled = user.get("mfa_enabled", False)
        user_mfa_verified = user.get("mfa_verified", False)
        
        # Determine access status
        access_allowed = not requires_mfa or (user_mfa_enabled and user_mfa_verified)
        mfa_setup_required = requires_mfa and not user_mfa_enabled
        mfa_verification_required = requires_mfa and user_mfa_enabled and not user_mfa_verified
        
        return {
            "space_id": space_id,
            "space_name": space.name,
            "requires_mfa": requires_mfa,
            "user_mfa_enabled": user_mfa_enabled,
            "user_mfa_verified": user_mfa_verified,
            "access_allowed": access_allowed,
            "mfa_setup_required": mfa_setup_required,
            "mfa_verification_required": mfa_verification_required,
            "security_classification": space.security_classification,
            "compliance_frameworks": space.compliance_frameworks,
            "encryption_enabled": space.encryption_enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA status check failed for space {space_id}", error=str(e), user_id=user.get("user_id"))
        raise HTTPException(status_code=500, detail="MFA status check failed")
