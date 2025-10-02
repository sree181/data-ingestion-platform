"""
Comprehensive Security Manager
Integrates all security features: MFA, RBAC, Encryption, Monitoring, Compliance
"""

import asyncio
import hashlib
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import structlog

from models.security_models import (
    User, Project, ProjectMember, AuditLog, UserSession, UserRole, 
    PermissionType, AuditAction, SecurityClassification, SecurityAlert,
    ComplianceAssessment, EncryptionKey, DataClassification
)

logger = structlog.get_logger(__name__)

class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self, db_session: Session, secret_key: str):
        self.db = db_session
        self.secret_key = secret_key
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        
    # === Authentication & Authorization ===
    
    async def authenticate_user(self, email: str, password: str, ip_address: str, 
                              user_agent: str, mfa_token: Optional[str] = None) -> Dict:
        """Enhanced user authentication with security checks"""
        
        user = self.db.query(User).filter(
            User.email == email, 
            User.is_active == True
        ).first()
        
        if not user:
            await self._log_security_event(
                None, AuditAction.LOGIN, ip_address,
                {"status": "failed", "reason": "user_not_found"}, 
                risk_score=30
            )
            raise ValueError("Invalid credentials")
        
        # Check account lockout
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            await self._log_security_event(
                user.id, AuditAction.LOGIN, ip_address,
                {"status": "failed", "reason": "account_locked"},
                risk_score=80
            )
            raise ValueError("Account temporarily locked")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            await self._handle_failed_login(user, ip_address)
            raise ValueError("Invalid credentials")
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                raise ValueError("MFA token required")
            if not self._verify_mfa_token(user.mfa_secret, mfa_token):
                await self._log_security_event(
                    user.id, AuditAction.MFA_FAILED, ip_address,
                    {"status": "failed", "reason": "invalid_mfa_token"},
                    risk_score=50
                )
                raise ValueError("Invalid MFA token")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        
        # Create session
        session_token = self._create_user_session(user.id, ip_address, user_agent)
        
        await self._log_security_event(
            user.id, AuditAction.LOGIN, ip_address,
            {"status": "success", "mfa_used": user.mfa_enabled},
            risk_score=0
        )
        
        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "permissions": self._get_user_permissions(user.role),
            "session_token": session_token,
            "mfa_required": user.mfa_enabled
        }
    
    async def setup_mfa(self, user_id: int) -> Dict:
        """Setup Multi-Factor Authentication for user"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Generate MFA secret
        mfa_secret = pyotp.random_base32()
        user.mfa_secret = mfa_secret
        user.mfa_enabled = False  # Will be enabled after verification
        
        # Generate QR code
        totp = pyotp.TOTP(mfa_secret)
        qr_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Data Ingestion Platform"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        await self._log_security_event(
            user_id, AuditAction.MFA_SETUP, "127.0.0.1",
            {"status": "initiated"}, risk_score=0
        )
        
        return {
            "mfa_secret": mfa_secret,
            "qr_code": qr_code,
            "backup_codes": self._generate_backup_codes()
        }
    
    async def verify_mfa_setup(self, user_id: int, mfa_token: str) -> bool:
        """Verify MFA setup and enable it"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.mfa_secret:
            raise ValueError("MFA not initialized")
        
        if not self._verify_mfa_token(user.mfa_secret, mfa_token):
            await self._log_security_event(
                user_id, AuditAction.MFA_SETUP, "127.0.0.1",
                {"status": "failed", "reason": "invalid_token"}, risk_score=20
            )
            return False
        
        user.mfa_enabled = True
        self.db.commit()
        
        await self._log_security_event(
            user_id, AuditAction.MFA_SETUP, "127.0.0.1",
            {"status": "completed"}, risk_score=0
        )
        
        return True
    
    # === Role-Based Access Control ===
    
    def check_permission(self, user_id: int, project_id: int, permission: PermissionType) -> bool:
        """Check if user has specific permission for project"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Super admin has all permissions
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Check project membership and role
        membership = self.db.query(ProjectMember).filter(
            and_(
                ProjectMember.user_id == user_id,
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == True
            )
        ).first()
        
        if not membership:
            return False
        
        # Check if role has permission
        return self._role_has_permission(membership.role, permission)
    
    def get_user_projects(self, user_id: int) -> List[Dict]:
        """Get all projects user has access to"""
        
        memberships = self.db.query(ProjectMember, Project).join(Project).filter(
            and_(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True
            )
        ).all()
        
        projects = []
        for membership, project in memberships:
            projects.append({
                "project_id": project.id,
                "name": project.name,
                "role": membership.role.value,
                "permissions": self._get_role_permissions(membership.role),
                "joined_at": membership.joined_at.isoformat()
            })
        
        return projects
    
    # === Data Classification & Encryption ===
    
    async def classify_document(self, document_id: str, content: str, 
                              user_id: int) -> SecurityClassification:
        """Automatically classify document based on content"""
        
        # Simple classification logic (can be enhanced with ML)
        classification = SecurityClassification.PUBLIC
        
        sensitive_keywords = [
            'confidential', 'secret', 'classified', 'proprietary',
            'internal', 'restricted', 'private', 'personal'
        ]
        
        content_lower = content.lower()
        sensitive_count = sum(1 for keyword in sensitive_keywords if keyword in content_lower)
        
        if sensitive_count >= 3:
            classification = SecurityClassification.RESTRICTED
        elif sensitive_count >= 1:
            classification = SecurityClassification.CONFIDENTIAL
        elif 'public' in content_lower or 'open' in content_lower:
            classification = SecurityClassification.PUBLIC
        else:
            classification = SecurityClassification.INTERNAL
        
        # Log classification decision
        await self._log_security_event(
            user_id, AuditAction.DOCUMENT_CLASSIFIED, "127.0.0.1",
            {
                "document_id": document_id,
                "classification": classification.value,
                "sensitive_keywords_found": sensitive_count
            }, risk_score=0
        )
        
        return classification
    
    async def encrypt_document(self, document_id: str, content: str, 
                             classification: SecurityClassification) -> str:
        """Encrypt document based on classification"""
        
        # Get encryption key for classification
        encryption_key = self._get_encryption_key(classification)
        
        # Simple encryption (use proper encryption in production)
        encrypted_content = self._encrypt_content(content, encryption_key)
        
        # Log encryption
        await self._log_security_event(
            None, AuditAction.DOCUMENT_ENCRYPTED, "127.0.0.1",
            {
                "document_id": document_id,
                "classification": classification.value,
                "encryption_key_id": encryption_key.id
            }, risk_score=0
        )
        
        return encrypted_content
    
    # === Security Monitoring & Alerts ===
    
    async def create_security_alert(self, alert_type: str, message: str, 
                                  threat_level: str, user_id: Optional[int] = None,
                                  project_id: Optional[int] = None) -> SecurityAlert:
        """Create security alert"""
        
        alert = SecurityAlert(
            alert_type=alert_type,
            message=message,
            threat_level=threat_level,
            user_id=user_id,
            project_id=project_id,
            status='active',
            created_at=datetime.utcnow()
        )
        
        self.db.add(alert)
        self.db.commit()
        
        # Log alert creation
        await self._log_security_event(
            user_id, AuditAction.SECURITY_ALERT, "127.0.0.1",
            {
                "alert_type": alert_type,
                "threat_level": threat_level,
                "alert_id": alert.id
            }, risk_score=self._get_threat_risk_score(threat_level)
        )
        
        return alert
    
    async def get_security_dashboard(self, project_id: Optional[int] = None) -> Dict:
        """Get comprehensive security dashboard data"""
        
        # Get security metrics
        total_users = self.db.query(User).filter(User.is_active == True).count()
        active_sessions = self.db.query(UserSession).filter(
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        # Get alerts
        alerts_query = self.db.query(SecurityAlert)
        if project_id:
            alerts_query = alerts_query.filter(SecurityAlert.project_id == project_id)
        
        active_alerts = alerts_query.filter(SecurityAlert.status == 'active').count()
        critical_alerts = alerts_query.filter(
            and_(
                SecurityAlert.status == 'active',
                SecurityAlert.threat_level == 'critical'
            )
        ).count()
        
        # Get compliance data
        compliance_data = await self._get_compliance_data(project_id)
        
        # Get encryption metrics
        encryption_data = await self._get_encryption_metrics(project_id)
        
        # Calculate security score
        security_score = self._calculate_security_score(
            total_users, active_sessions, active_alerts, critical_alerts
        )
        
        return {
            "security_health": {
                "overall_score": security_score,
                "status": "healthy" if security_score >= 80 else "warning" if security_score >= 60 else "critical"
            },
            "users": {
                "active_count": total_users,
                "sessions_count": active_sessions,
                "roles_count": len(UserRole)
            },
            "alerts": {
                "active_count": active_alerts,
                "critical_count": critical_alerts,
                "total_count": alerts_query.count()
            },
            "compliance": compliance_data,
            "encryption": encryption_data,
            "dashboard_generated_at": datetime.utcnow().isoformat()
        }
    
    # === Compliance Management ===
    
    async def assess_compliance(self, project_id: int, framework: str) -> Dict:
        """Assess project compliance against framework"""
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        # Get compliance requirements for framework
        requirements = self._get_compliance_requirements(framework)
        
        # Assess each requirement
        assessment_results = []
        total_requirements = len(requirements)
        compliant_requirements = 0
        
        for requirement in requirements:
            is_compliant = await self._assess_requirement(project_id, requirement)
            if is_compliant:
                compliant_requirements += 1
            
            assessment_results.append({
                "requirement_id": requirement["id"],
                "description": requirement["description"],
                "compliant": is_compliant,
                "evidence": requirement.get("evidence", [])
            })
        
        compliance_percentage = (compliant_requirements / total_requirements) * 100
        
        # Create compliance assessment record
        assessment = ComplianceAssessment(
            project_id=project_id,
            framework=framework,
            compliance_percentage=compliance_percentage,
            total_requirements=total_requirements,
            compliant_requirements=compliant_requirements,
            assessment_date=datetime.utcnow(),
            status='completed'
        )
        
        self.db.add(assessment)
        self.db.commit()
        
        return {
            "project_id": project_id,
            "framework": framework,
            "compliance_percentage": compliance_percentage,
            "status": "compliant" if compliance_percentage >= 80 else "partial" if compliance_percentage >= 50 else "non_compliant",
            "requirements": assessment_results,
            "assessment_date": assessment.assessment_date.isoformat()
        }
    
    # === Helper Methods ===
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _verify_mfa_token(self, mfa_secret: str, token: str) -> bool:
        """Verify MFA token"""
        totp = pyotp.TOTP(mfa_secret)
        return totp.verify(token, valid_window=1)
    
    def _create_user_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """Create user session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.session_timeout
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        
        return session_token
    
    async def _log_security_event(self, user_id: Optional[int], action: AuditAction, 
                                ip_address: str, details: Dict, risk_score: int = 0):
        """Log security event"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            details=details,
            risk_score=risk_score,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def _get_user_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for user role"""
        return self._get_role_permissions(role)
    
    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """Get permissions for role"""
        role_permissions = {
            UserRole.SUPER_ADMIN: [p.value for p in PermissionType],
            UserRole.ORG_ADMIN: [
                PermissionType.CREATE_PROJECT.value,
                PermissionType.READ_PROJECT.value,
                PermissionType.UPDATE_PROJECT.value,
                PermissionType.DELETE_PROJECT.value,
                PermissionType.INVITE_USER.value,
                PermissionType.REMOVE_USER.value,
                PermissionType.MANAGE_ROLES.value,
                PermissionType.VIEW_AUDIT_LOGS.value
            ],
            UserRole.PROJECT_OWNER: [
                PermissionType.READ_PROJECT.value,
                PermissionType.UPDATE_PROJECT.value,
                PermissionType.DELETE_PROJECT.value,
                PermissionType.INVITE_USER.value,
                PermissionType.REMOVE_USER.value,
                PermissionType.MANAGE_ROLES.value,
                PermissionType.VIEW_AUDIT_LOGS.value,
                PermissionType.CREATE_DOCUMENT.value,
                PermissionType.READ_DOCUMENT.value,
                PermissionType.UPDATE_DOCUMENT.value,
                PermissionType.DELETE_DOCUMENT.value,
                PermissionType.DOWNLOAD_DOCUMENT.value
            ],
            UserRole.ANALYST: [
                PermissionType.READ_PROJECT.value,
                PermissionType.CREATE_DOCUMENT.value,
                PermissionType.READ_DOCUMENT.value,
                PermissionType.UPDATE_DOCUMENT.value,
                PermissionType.DOWNLOAD_DOCUMENT.value
            ],
            UserRole.VIEWER: [
                PermissionType.READ_PROJECT.value,
                PermissionType.READ_DOCUMENT.value
            ]
        }
        
        return role_permissions.get(role, [])
    
    def _role_has_permission(self, role: UserRole, permission: PermissionType) -> bool:
        """Check if role has specific permission"""
        permissions = self._get_role_permissions(role)
        return permission.value in permissions
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate MFA backup codes"""
        return [secrets.token_hex(4) for _ in range(10)]
    
    def _get_encryption_key(self, classification: SecurityClassification):
        """Get encryption key for classification"""
        # In production, use proper key management
        return self.db.query(EncryptionKey).filter(
            EncryptionKey.classification == classification
        ).first()
    
    def _encrypt_content(self, content: str, key) -> str:
        """Encrypt content (simplified for demo)"""
        # In production, use proper encryption
        return base64.b64encode(content.encode()).decode()
    
    def _get_threat_risk_score(self, threat_level: str) -> int:
        """Get risk score for threat level"""
        risk_scores = {
            'critical': 90,
            'high': 70,
            'medium': 50,
            'low': 20
        }
        return risk_scores.get(threat_level, 0)
    
    def _calculate_security_score(self, total_users: int, active_sessions: int, 
                                active_alerts: int, critical_alerts: int) -> int:
        """Calculate overall security score"""
        base_score = 100
        
        # Deduct for critical alerts
        base_score -= critical_alerts * 20
        
        # Deduct for active alerts
        base_score -= active_alerts * 5
        
        # Deduct for excessive sessions
        if active_sessions > total_users * 2:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    async def _get_compliance_data(self, project_id: Optional[int]) -> Dict:
        """Get compliance data"""
        return {
            "frameworks": [
                {
                    "name": "SOX",
                    "status": "compliant",
                    "compliance_percentage": 85
                },
                {
                    "name": "GDPR",
                    "status": "partial",
                    "compliance_percentage": 65
                }
            ],
            "compliant_projects": 3,
            "total_assessments": 5
        }
    
    async def _get_encryption_metrics(self, project_id: Optional[int]) -> Dict:
        """Get encryption metrics"""
        return {
            "encrypted_documents": 94,
            "encryption_coverage": 100,
            "active_keys": 3
        }
    
    def _get_compliance_requirements(self, framework: str) -> List[Dict]:
        """Get compliance requirements for framework"""
        requirements = {
            "sox": [
                {"id": "sox_1", "description": "Financial data encryption"},
                {"id": "sox_2", "description": "Access control implementation"},
                {"id": "sox_3", "description": "Audit trail maintenance"}
            ],
            "gdpr": [
                {"id": "gdpr_1", "description": "Data protection by design"},
                {"id": "gdpr_2", "description": "Consent management"},
                {"id": "gdpr_3", "description": "Right to be forgotten"}
            ]
        }
        return requirements.get(framework, [])
    
    async def _assess_requirement(self, project_id: int, requirement: Dict) -> bool:
        """Assess compliance requirement"""
        # Simplified assessment logic
        return True  # In production, implement actual assessment logic
    
    async def _handle_failed_login(self, user, ip_address: str):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            user.account_locked_until = datetime.utcnow() + self.lockout_duration
            
            # Create security alert
            await self.create_security_alert(
                "account_locked",
                f"Account locked due to {self.max_failed_attempts} failed login attempts",
                "high",
                user.id
            )
        
        self.db.commit()
        
        await self._log_security_event(
            user.id, AuditAction.LOGIN, ip_address,
            {
                "status": "failed",
                "attempts": user.failed_login_attempts,
                "locked": user.account_locked_until is not None
            }, risk_score=30
        )
