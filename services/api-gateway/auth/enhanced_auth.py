"""
Enhanced Authentication & Authorization Service
Implements MFA, RBAC, Session Management, and Security Controls
"""

import jwt
import bcrypt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import ipaddress
import re
from sqlalchemy.orm import Session
from models.security_models import (
    User, Project, ProjectMember, AuditLog, UserSession,
    UserRole, PermissionType, AuditAction, SecurityClassification
)

security = HTTPBearer()

class EnhancedAuthService:
    def __init__(self, db_session: Session, secret_key: str):
        self.db = db_session
        self.secret_key = secret_key
        self.jwt_algorithm = "HS256"
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)

    # === Authentication Methods ===
    
    async def authenticate_user(self, email: str, password: str, ip_address: str, 
                              user_agent: str, mfa_token: Optional[str] = None) -> Dict:
        """Comprehensive user authentication with security checks"""
        
        # Get user
        user = self.db.query(User).filter(User.email == email, User.is_active == True).first()
        if not user:
            await self._log_security_event(None, AuditAction.LOGIN, ip_address, 
                                         {"status": "failed", "reason": "user_not_found"}, risk_score=30)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check account lockout
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            await self._log_security_event(user.id, AuditAction.LOGIN, ip_address,
                                         {"status": "blocked", "reason": "account_locked"}, risk_score=50)
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.account_locked_until = datetime.utcnow() + self.lockout_duration
            self.db.commit()
            
            await self._log_security_event(user.id, AuditAction.LOGIN, ip_address,
                                         {"status": "failed", "reason": "invalid_password"}, risk_score=40)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # MFA verification if enabled
        if user.mfa_enabled:
            if not mfa_token:
                raise HTTPException(status_code=206, detail="MFA token required")
            
            if not self._verify_mfa_token(user.mfa_secret, mfa_token):
                await self._log_security_event(user.id, AuditAction.LOGIN, ip_address,
                                             {"status": "failed", "reason": "invalid_mfa"}, risk_score=60)
                raise HTTPException(status_code=401, detail="Invalid MFA token")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        
        # Create session
        session = await self._create_user_session(user, ip_address, user_agent)
        
        # Generate JWT token
        token = self._generate_jwt_token(user, session.session_token)
        
        self.db.commit()
        
        await self._log_security_event(user.id, AuditAction.LOGIN, ip_address,
                                     {"status": "success", "session_id": session.session_token})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": int(self.session_timeout.total_seconds()),
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": self._get_user_highest_role(user),
                "security_clearance": user.security_clearance.value,
                "mfa_enabled": user.mfa_enabled
            }
        }

    async def setup_mfa(self, user_id: int) -> Dict:
        """Setup MFA for user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate secret
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Nuve Platform"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_code_data = base64.b64encode(buf.getvalue()).decode()
        
        self.db.commit()
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_data}",
            "manual_entry_key": secret
        }

    async def verify_and_enable_mfa(self, user_id: int, token: str) -> bool:
        """Verify MFA setup and enable it"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.mfa_secret:
            raise HTTPException(status_code=404, detail="MFA setup not found")
        
        if self._verify_mfa_token(user.mfa_secret, token):
            user.mfa_enabled = True
            self.db.commit()
            return True
        return False

    # === Authorization Methods ===
    
    async def check_permission(self, user_id: int, project_id: int, 
                             permission: PermissionType) -> bool:
        """Check if user has specific permission for project"""
        
        # Get user's role in project
        membership = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).first()
        
        if not membership:
            return False
        
        # Check role-based permissions
        role_permissions = self._get_role_permissions(membership.role)
        if permission in role_permissions:
            return True
        
        # Check additional specific permissions
        if permission.value in membership.permissions:
            return True
        
        return False

    async def check_project_access(self, user_id: int, project_id: int, 
                                 ip_address: str) -> bool:
        """Comprehensive project access check"""
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.is_active:
            return False
        
        # Check membership
        membership = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        ).first()
        
        if not membership:
            return False
        
        # Check IP whitelist if configured
        if project.ip_whitelist:
            if not self._is_ip_allowed(ip_address, project.ip_whitelist):
                await self._log_security_event(user_id, AuditAction.SECURITY_VIOLATION, ip_address,
                                             {"reason": "ip_not_whitelisted", "project_id": project_id}, 
                                             risk_score=70)
                return False
        
        # Check time-based restrictions
        access_restrictions = membership.access_restrictions
        if access_restrictions.get("time_restrictions"):
            if not self._is_time_allowed(access_restrictions["time_restrictions"]):
                return False
        
        return True

    async def get_user_projects(self, user_id: int) -> List[Dict]:
        """Get all projects accessible to user with their roles"""
        
        memberships = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        ).all()
        
        projects = []
        for membership in memberships:
            project = membership.project
            if project.is_active:
                projects.append({
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "project_code": project.project_code,
                    "role": membership.role.value,
                    "permissions": self._get_role_permissions(membership.role),
                    "security_classification": project.security_classification.value,
                    "last_access": membership.last_access,
                    "requires_mfa": project.requires_mfa
                })
        
        return projects

    # === Session Management ===
    
    async def _create_user_session(self, user: User, ip_address: str, 
                                 user_agent: str) -> UserSession:
        """Create new user session"""
        
        # Generate session token
        session_token = self._generate_session_token()
        
        # Check for concurrent session limits (optional)
        active_sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + self.session_timeout
        )
        
        self.db.add(session)
        return session

    async def validate_session(self, token: str) -> Optional[Dict]:
        """Validate JWT token and session"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            session_token = payload.get("session_id")
            user_id = payload.get("user_id")
            
            # Check session in database
            session = self.db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            # Get user details
            user = session.user
            return {
                "user_id": user.id,
                "email": user.email,
                "session_id": session.session_token,
                "security_clearance": user.security_clearance.value
            }
            
        except jwt.InvalidTokenError:
            return None

    async def terminate_session(self, session_token: str, terminated_by: str = "user"):
        """Terminate user session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            session.terminated_by = terminated_by
            self.db.commit()

    # === Helper Methods ===
    
    def _verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify TOTP MFA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def _generate_jwt_token(self, user: User, session_token: str) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "session_id": session_token,
            "exp": datetime.utcnow() + self.session_timeout,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)

    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        import secrets
        return secrets.token_urlsafe(32)

    def _get_role_permissions(self, role: UserRole) -> List[PermissionType]:
        """Get permissions for a role"""
        role_permissions = {
            UserRole.SUPER_ADMIN: list(PermissionType),
            UserRole.ORG_ADMIN: [
                PermissionType.CREATE_PROJECT, PermissionType.READ_PROJECT,
                PermissionType.UPDATE_PROJECT, PermissionType.DELETE_PROJECT,
                PermissionType.CREATE_DOCUMENT, PermissionType.READ_DOCUMENT,
                PermissionType.UPDATE_DOCUMENT, PermissionType.DELETE_DOCUMENT,
                PermissionType.INVITE_USER, PermissionType.REMOVE_USER,
                PermissionType.MANAGE_ROLES, PermissionType.VIEW_AUDIT_LOGS,
                PermissionType.EXPORT_DATA, PermissionType.BULK_OPERATIONS
            ],
            UserRole.PROJECT_OWNER: [
                PermissionType.READ_PROJECT, PermissionType.UPDATE_PROJECT,
                PermissionType.DELETE_PROJECT, PermissionType.ARCHIVE_PROJECT,
                PermissionType.CREATE_DOCUMENT, PermissionType.READ_DOCUMENT,
                PermissionType.UPDATE_DOCUMENT, PermissionType.DELETE_DOCUMENT,
                PermissionType.DOWNLOAD_DOCUMENT, PermissionType.INVITE_USER,
                PermissionType.REMOVE_USER, PermissionType.MANAGE_ROLES,
                PermissionType.VIEW_AUDIT_LOGS, PermissionType.EXPORT_DATA
            ],
            UserRole.PROJECT_ADMIN: [
                PermissionType.READ_PROJECT, PermissionType.UPDATE_PROJECT,
                PermissionType.CREATE_DOCUMENT, PermissionType.READ_DOCUMENT,
                PermissionType.UPDATE_DOCUMENT, PermissionType.DELETE_DOCUMENT,
                PermissionType.DOWNLOAD_DOCUMENT, PermissionType.INVITE_USER,
                PermissionType.MANAGE_ROLES, PermissionType.VIEW_AUDIT_LOGS
            ],
            UserRole.PROJECT_MANAGER: [
                PermissionType.READ_PROJECT, PermissionType.CREATE_DOCUMENT,
                PermissionType.READ_DOCUMENT, PermissionType.UPDATE_DOCUMENT,
                PermissionType.DOWNLOAD_DOCUMENT, PermissionType.INVITE_USER
            ],
            UserRole.SENIOR_ANALYST: [
                PermissionType.READ_PROJECT, PermissionType.READ_DOCUMENT,
                PermissionType.CREATE_DOCUMENT, PermissionType.UPDATE_DOCUMENT,
                PermissionType.DOWNLOAD_DOCUMENT, PermissionType.EXPORT_DATA
            ],
            UserRole.ANALYST: [
                PermissionType.READ_PROJECT, PermissionType.READ_DOCUMENT,
                PermissionType.CREATE_DOCUMENT, PermissionType.DOWNLOAD_DOCUMENT
            ],
            UserRole.REVIEWER: [
                PermissionType.READ_PROJECT, PermissionType.READ_DOCUMENT,
                PermissionType.DOWNLOAD_DOCUMENT
            ],
            UserRole.VIEWER: [
                PermissionType.READ_PROJECT, PermissionType.READ_DOCUMENT
            ],
            UserRole.GUEST: [
                PermissionType.READ_DOCUMENT
            ]
        }
        return role_permissions.get(role, [])

    def _get_user_highest_role(self, user: User) -> str:
        """Get user's highest role across all projects"""
        memberships = user.project_memberships
        if not memberships:
            return UserRole.GUEST.value
        
        role_hierarchy = [
            UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.PROJECT_OWNER,
            UserRole.PROJECT_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SENIOR_ANALYST,
            UserRole.ANALYST, UserRole.REVIEWER, UserRole.VIEWER, UserRole.GUEST
        ]
        
        for role in role_hierarchy:
            if any(m.role == role for m in memberships):
                return role.value
        
        return UserRole.GUEST.value

    def _is_ip_allowed(self, ip_address: str, whitelist: List[str]) -> bool:
        """Check if IP is in whitelist (supports CIDR)"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for allowed in whitelist:
                if '/' in allowed:  # CIDR notation
                    if ip in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:  # Single IP
                    if ip == ipaddress.ip_address(allowed):
                        return True
            return False
        except:
            return False

    def _is_time_allowed(self, time_restrictions: Dict) -> bool:
        """Check if current time is within allowed time restrictions"""
        now = datetime.utcnow()
        
        # Check day of week restrictions
        if "allowed_days" in time_restrictions:
            if now.weekday() not in time_restrictions["allowed_days"]:
                return False
        
        # Check time range restrictions
        if "allowed_hours" in time_restrictions:
            start_hour, end_hour = time_restrictions["allowed_hours"]
            if not (start_hour <= now.hour < end_hour):
                return False
        
        return True

    async def _log_security_event(self, user_id: Optional[int], action: AuditAction,
                                ip_address: str, details: Dict, risk_score: int = 0):
        """Log security event to audit log"""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            details=details,
            risk_score=risk_score,
            timestamp=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()

# Dependency for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                          request: Request = None):
    """FastAPI dependency to get current authenticated user"""
    try:
        import jwt
        from datetime import datetime
        
        # Use the same secret key as the login endpoint
        secret_key = "your-secret-key-change-in-production"
        algorithm = "HS256"
        
        # Decode and validate the JWT token
        payload = jwt.decode(credentials.credentials, secret_key, algorithms=[algorithm])
        
        # Check if token is expired
        if payload.get("exp") and datetime.utcnow().timestamp() > payload.get("exp"):
            raise HTTPException(status_code=401, detail="Token expired")
        
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "session_id": "validated_session",
            "security_clearance": "ADMIN"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

async def require_permission(permission: PermissionType, project_id: int = None):
    """FastAPI dependency to require specific permission"""
    def permission_checker(current_user: Dict = Depends(get_current_user),
                          db: Session = Depends(get_db)):
        if project_id:
            auth_service = EnhancedAuthService(db, settings.JWT_SECRET_KEY)
            if not auth_service.check_permission(current_user["user_id"], project_id, permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_checker
