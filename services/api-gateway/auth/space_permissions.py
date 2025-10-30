"""
Space Permission Management
Handles project space permission checking and enforcement
"""

from typing import Dict, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from models.project_spaces import SpacePermission
from auth.jwt_auth import get_current_user
from database import get_db
from services.project_spaces_service import ProjectSpacesService

logger = structlog.get_logger(__name__)

def require_space_permission(permission: SpacePermission, space_id: Optional[str] = None):
    """
    FastAPI dependency to require specific space permission
    
    Args:
        permission: The required permission level
        space_id: Optional space ID to check permissions for
    
    Returns:
        FastAPI dependency function
    """
    def permission_checker(
        current_user: Dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            # Get user ID from current user
            user_id = current_user.get("user_id") or current_user.get("id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User ID not found in token"
                )
            
            # If space_id is provided, check specific space permissions
            if space_id:
                space_service = ProjectSpacesService(db)
                
                # Check if user has the required permission for this space
                has_permission = space_service._check_space_permission(
                    space_id, user_id, permission
                )
                
                if not has_permission:
                    logger.warning(
                        "Insufficient space permissions",
                        user_id=user_id,
                        space_id=space_id,
                        required_permission=permission.value
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required: {permission.value}"
                    )
                
                logger.info(
                    "Space permission granted",
                    user_id=user_id,
                    space_id=space_id,
                    permission=permission.value
                )
            
            # Return current user with space context
            return {
                **current_user,
                "space_id": space_id,
                "permission": permission.value
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Space permission check failed",
                user_id=user_id,
                space_id=space_id,
                permission=permission.value,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )
    
    return permission_checker

def require_space_admin(space_id: Optional[str] = None):
    """
    FastAPI dependency to require admin permission for a space
    
    Args:
        space_id: Optional space ID to check admin permissions for
    
    Returns:
        FastAPI dependency function
    """
    return require_space_permission(SpacePermission.ADMIN, space_id)

def require_space_write(space_id: Optional[str] = None):
    """
    FastAPI dependency to require write permission for a space
    
    Args:
        space_id: Optional space ID to check write permissions for
    
    Returns:
        FastAPI dependency function
    """
    return require_space_permission(SpacePermission.WRITE, space_id)

def require_space_read(space_id: Optional[str] = None):
    """
    FastAPI dependency to require read permission for a space
    
    Args:
        space_id: Optional space ID to check read permissions for
    
    Returns:
        FastAPI dependency function
    """
    return require_space_permission(SpacePermission.READ, space_id)

def check_space_permission_for_user(
    user_id: str, 
    space_id: str, 
    permission: SpacePermission,
    db: Session
) -> bool:
    """
    Check if a user has a specific permission for a space
    
    Args:
        user_id: User ID to check
        space_id: Space ID to check permissions for
        permission: Required permission level
        db: Database session
    
    Returns:
        True if user has permission, False otherwise
    """
    try:
        space_service = ProjectSpacesService(db)
        return space_service._check_space_permission(space_id, user_id, permission)
    except Exception as e:
        logger.error(
            "Space permission check failed",
            user_id=user_id,
            space_id=space_id,
            permission=permission.value,
            error=str(e)
        )
        return False

def get_user_space_permissions(user_id: str, space_id: str, db: Session) -> Dict[str, bool]:
    """
    Get all permissions for a user in a specific space
    
    Args:
        user_id: User ID
        space_id: Space ID
        db: Database session
    
    Returns:
        Dictionary of permission levels and their status
    """
    try:
        space_service = ProjectSpacesService(db)
        
        permissions = {}
        for permission in SpacePermission:
            permissions[permission.value] = space_service._check_space_permission(
                space_id, user_id, permission
            )
        
        return permissions
    except Exception as e:
        logger.error(
            "Failed to get user space permissions",
            user_id=user_id,
            space_id=space_id,
            error=str(e)
        )
        return {permission.value: False for permission in SpacePermission}
