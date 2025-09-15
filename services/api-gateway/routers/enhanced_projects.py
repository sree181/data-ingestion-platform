"""
Enhanced Project Management API with Security Features
Implements project isolation, stakeholder management, and security controls
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from models.security_models import (
    Project, ProjectMember, User, Organization, AuditLog,
    UserRole, PermissionType, AuditAction, SecurityClassification,
    ProjectSecurityConfig, UserPermissions
)
from auth.enhanced_auth import (
    EnhancedAuthService, get_current_user, require_permission
)
from database import get_db

router = APIRouter(prefix="/api/v1/projects", tags=["Enhanced Projects"])

class ProjectSecurityManager:
    def __init__(self, db: Session):
        self.db = db

    async def create_secure_project(self, project_data: Dict, creator_id: int, 
                                  organization_id: int) -> Project:
        """Create project with security configuration"""
        
        # Generate unique project code
        project_code = self._generate_project_code(project_data["name"])
        
        # Create project
        project = Project(
            name=project_data["name"],
            description=project_data.get("description"),
            project_code=project_code,
            security_classification=SecurityClassification(
                project_data.get("security_classification", "internal")
            ),
            encryption_enabled=project_data.get("encryption_enabled", True),
            requires_mfa=project_data.get("requires_mfa", False),
            ip_whitelist=project_data.get("ip_whitelist", []),
            allowed_domains=project_data.get("allowed_domains", []),
            compliance_frameworks=project_data.get("compliance_frameworks", []),
            data_retention_days=project_data.get("data_retention_days", 2555),
            organization_id=organization_id,
            created_by=creator_id
        )
        
        self.db.add(project)
        self.db.flush()  # Get project ID
        
        # Add creator as project owner
        owner_membership = ProjectMember(
            project_id=project.id,
            user_id=creator_id,
            role=UserRole.PROJECT_OWNER,
            invited_by=creator_id,
            joined_at=datetime.utcnow()
        )
        
        self.db.add(owner_membership)
        self.db.commit()
        
        return project

    async def invite_project_member(self, project_id: int, inviter_id: int,
                                  email: str, role: UserRole, 
                                  permissions: List[str] = None) -> Dict:
        """Invite user to project with specific role and permissions"""
        
        # Check if user exists
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already a member
        existing = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(status_code=409, detail="User already a project member")
        
        # Create membership
        membership = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            role=role,
            permissions=permissions or [],
            invited_by=inviter_id,
            invited_at=datetime.utcnow()
        )
        
        self.db.add(membership)
        self.db.commit()
        
        # Log audit event
        await self._log_project_event(
            inviter_id, project_id, AuditAction.PERMISSION_GRANT,
            {"invited_user": email, "role": role.value}
        )
        
        return {
            "user_id": user.id,
            "email": user.email,
            "role": role.value,
            "invited_at": membership.invited_at
        }

    async def update_member_role(self, project_id: int, user_id: int, 
                               new_role: UserRole, updated_by: int) -> Dict:
        """Update project member role"""
        
        membership = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="Project membership not found")
        
        old_role = membership.role
        membership.role = new_role
        self.db.commit()
        
        # Log audit event
        await self._log_project_event(
            updated_by, project_id, AuditAction.ROLE_CHANGE,
            {"user_id": user_id, "old_role": old_role.value, "new_role": new_role.value}
        )
        
        return {
            "user_id": user_id,
            "old_role": old_role.value,
            "new_role": new_role.value,
            "updated_at": datetime.utcnow()
        }

    async def get_project_members(self, project_id: int) -> List[Dict]:
        """Get all project members with their roles and permissions"""
        
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).all()
        
        result = []
        for member in members:
            user = member.user
            result.append({
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": member.role.value,
                "permissions": member.permissions,
                "joined_at": member.joined_at,
                "last_access": member.last_access,
                "security_clearance": user.security_clearance.value,
                "mfa_enabled": user.mfa_enabled
            })
        
        return result

    async def get_project_security_metrics(self, project_id: int) -> Dict:
        """Get security metrics for project"""
        
        # Get project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get members count
        total_members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).count()
        
        # Get MFA adoption rate
        mfa_enabled_members = self.db.query(ProjectMember).join(User).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True,
            User.mfa_enabled == True
        ).count()
        
        mfa_adoption_rate = (mfa_enabled_members / total_members) * 100 if total_members > 0 else 0
        
        # Get recent audit events
        recent_events = self.db.query(AuditLog).filter(
            AuditLog.project_id == project_id,
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Get high-risk events
        high_risk_events = self.db.query(AuditLog).filter(
            AuditLog.project_id == project_id,
            AuditLog.risk_score >= 70,
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return {
            "project_id": project_id,
            "security_classification": project.security_classification.value,
            "encryption_enabled": project.encryption_enabled,
            "requires_mfa": project.requires_mfa,
            "total_members": total_members,
            "mfa_adoption_rate": round(mfa_adoption_rate, 2),
            "recent_audit_events": recent_events,
            "high_risk_events": high_risk_events,
            "compliance_frameworks": project.compliance_frameworks,
            "ip_whitelist_configured": len(project.ip_whitelist) > 0,
            "data_retention_days": project.data_retention_days
        }

    def _generate_project_code(self, project_name: str) -> str:
        """Generate unique project code"""
        import re
        import secrets
        
        # Clean name and take first 4 characters
        clean_name = re.sub(r'[^A-Za-z0-9]', '', project_name).upper()[:4]
        
        # Add random suffix
        suffix = secrets.token_hex(2).upper()
        
        return f"{clean_name}-{suffix}"

    async def _log_project_event(self, user_id: int, project_id: int, 
                               action: AuditAction, details: Dict):
        """Log project-related audit event"""
        log_entry = AuditLog(
            user_id=user_id,
            project_id=project_id,
            action=action,
            resource_type="project",
            resource_id=str(project_id),
            details=details,
            timestamp=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()

# API Endpoints
@router.post("/", response_model=Dict)
async def create_project(
    project_data: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new project with security configuration"""
    
    # Validate required fields
    if not project_data.get("name"):
        raise HTTPException(status_code=400, detail="Project name is required")
    
    # Get user's organization
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    security_manager = ProjectSecurityManager(db)
    project = await security_manager.create_secure_project(
        project_data, current_user["user_id"], user.organization_id
    )
    
    return {
        "id": project.id,
        "name": project.name,
        "project_code": project.project_code,
        "security_classification": project.security_classification.value,
        "created_at": project.created_at
    }

@router.get("/", response_model=List[Dict])
async def get_user_projects(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects accessible to current user"""
    
    auth_service = EnhancedAuthService(db, "your-secret-key")  # TODO: Get from settings
    projects = await auth_service.get_user_projects(current_user["user_id"])
    
    return projects

@router.get("/{project_id}", response_model=Dict)
async def get_project_details(
    project_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed project information"""
    
    # Check project access
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_access = await auth_service.check_project_access(
        current_user["user_id"], project_id, "127.0.0.1"  # TODO: Get real IP
    )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    security_manager = ProjectSecurityManager(db)
    members = await security_manager.get_project_members(project_id)
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "project_code": project.project_code,
        "security_classification": project.security_classification.value,
        "encryption_enabled": project.encryption_enabled,
        "requires_mfa": project.requires_mfa,
        "compliance_frameworks": project.compliance_frameworks,
        "members": members,
        "created_at": project.created_at
    }

@router.post("/{project_id}/members", response_model=Dict)
async def invite_project_member(
    project_id: int,
    invitation_data: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite user to project"""
    
    # Check permission
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_permission = await auth_service.check_permission(
        current_user["user_id"], project_id, PermissionType.INVITE_USER
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    security_manager = ProjectSecurityManager(db)
    result = await security_manager.invite_project_member(
        project_id,
        current_user["user_id"],
        invitation_data["email"],
        UserRole(invitation_data["role"]),
        invitation_data.get("permissions", [])
    )
    
    return result

@router.put("/{project_id}/members/{user_id}/role", response_model=Dict)
async def update_member_role(
    project_id: int,
    user_id: int,
    role_data: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project member role"""
    
    # Check permission
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_permission = await auth_service.check_permission(
        current_user["user_id"], project_id, PermissionType.MANAGE_ROLES
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    security_manager = ProjectSecurityManager(db)
    result = await security_manager.update_member_role(
        project_id, user_id, UserRole(role_data["role"]), current_user["user_id"]
    )
    
    return result

@router.get("/{project_id}/security-metrics", response_model=Dict)
async def get_project_security_metrics(
    project_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project security metrics"""
    
    # Check permission
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_permission = await auth_service.check_permission(
        current_user["user_id"], project_id, PermissionType.VIEW_AUDIT_LOGS
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    security_manager = ProjectSecurityManager(db)
    metrics = await security_manager.get_project_security_metrics(project_id)
    
    return metrics

@router.get("/{project_id}/audit-logs", response_model=List[Dict])
async def get_project_audit_logs(
    project_id: int,
    days: int = Query(30, description="Number of days to retrieve"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project audit logs"""
    
    # Check permission
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_permission = await auth_service.check_permission(
        current_user["user_id"], project_id, PermissionType.VIEW_AUDIT_LOGS
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Build query
    query = db.query(AuditLog).filter(
        AuditLog.project_id == project_id,
        AuditLog.timestamp >= datetime.utcnow() - timedelta(days=days)
    )
    
    if action:
        query = query.filter(AuditLog.action == AuditAction(action))
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(1000).all()
    
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action.value,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "details": log.details,
            "risk_score": log.risk_score,
            "timestamp": log.timestamp
        })
    
    return result

@router.put("/{project_id}/security-config", response_model=Dict)
async def update_project_security_config(
    project_id: int,
    security_config: ProjectSecurityConfig,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project security configuration"""
    
    # Check permission
    auth_service = EnhancedAuthService(db, "your-secret-key")
    has_permission = await auth_service.check_permission(
        current_user["user_id"], project_id, PermissionType.UPDATE_PROJECT
    )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update security settings
    project.security_classification = security_config.classification
    project.encryption_enabled = security_config.encryption_enabled
    project.requires_mfa = security_config.requires_mfa
    project.ip_whitelist = security_config.ip_whitelist
    project.allowed_domains = security_config.allowed_domains
    project.compliance_frameworks = security_config.compliance_frameworks
    project.data_retention_days = security_config.data_retention_days
    
    db.commit()
    
    # Log audit event
    security_manager = ProjectSecurityManager(db)
    await security_manager._log_project_event(
        current_user["user_id"], project_id, AuditAction.PERMISSION_GRANT,
        {"action": "security_config_updated", "config": security_config.dict()}
    )
    
    return {
        "project_id": project_id,
        "security_classification": project.security_classification.value,
        "updated_at": datetime.utcnow()
    }
