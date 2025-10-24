"""
Security Manager
Comprehensive security and compliance system for RL training framework
"""

import os
import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import structlog
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import threading
from pathlib import Path

logger = structlog.get_logger(__name__)

@dataclass
class SecurityConfig:
    """Configuration for security system"""
    enable_encryption: bool = True
    enable_authentication: bool = True
    enable_authorization: bool = True
    enable_audit_logging: bool = True
    enable_data_protection: bool = True
    enable_compliance: bool = True
    jwt_secret_key: str = None
    encryption_key: str = None
    audit_log_file: str = "security_audit.log"
    compliance_standards: List[str] = None
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes

class EncryptionManager:
    """Data encryption and decryption utilities"""
    
    def __init__(self, key: str = None):
        self.key = key or self._generate_key()
        self.cipher = Fernet(self.key)
        self.encryption_history = []
    
    def _generate_key(self) -> str:
        """Generate encryption key"""
        return Fernet.generate_key().decode()
    
    def encrypt_data(self, data: Union[str, bytes, dict]) -> str:
        """Encrypt data"""
        try:
            # Convert to bytes if needed
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode()
            elif isinstance(data, str):
                data_bytes = data.encode()
            else:
                data_bytes = data
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(data_bytes)
            encrypted_b64 = base64.b64encode(encrypted_data).decode()
            
            # Record encryption
            self.encryption_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'data_size': len(data_bytes),
                'encrypted_size': len(encrypted_b64)
            })
            
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Union[str, dict]:
        """Decrypt data"""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            
            # Try to parse as JSON first, fallback to string
            try:
                return json.loads(decrypted_bytes.decode())
            except json.JSONDecodeError:
                return decrypted_bytes.decode()
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_data(self, data: str, salt: str = None) -> Tuple[str, str]:
        """Hash data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Create hash
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            data.encode(),
            salt.encode(),
            100000  # iterations
        )
        
        hash_hex = hash_obj.hex()
        return hash_hex, salt
    
    def verify_hash(self, data: str, hash_value: str, salt: str) -> bool:
        """Verify hashed data"""
        computed_hash, _ = self.hash_data(data, salt)
        return hmac.compare_digest(computed_hash, hash_value)

class AuthenticationManager:
    """User authentication and session management"""
    
    def __init__(self, jwt_secret: str = None, session_timeout: int = 3600):
        self.jwt_secret = jwt_secret or secrets.token_hex(32)
        self.session_timeout = session_timeout
        self.active_sessions = {}
        self.user_credentials = {}
        self.login_attempts = {}
        self.lockout_timeout = 900  # 15 minutes
        self.max_attempts = 5
        
        # Initialize default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_password = "admin123"  # Should be changed in production
        password_hash, salt = self._hash_password(admin_password)
        
        self.user_credentials["admin"] = {
            "password_hash": password_hash,
            "salt": salt,
            "role": "admin",
            "permissions": ["read", "write", "execute", "admin"],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return hash_obj.hex(), salt
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        )
        return hmac.compare_digest(hash_obj.hex(), stored_hash)
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        try:
            # Check if user is locked out
            if self._is_user_locked_out(username):
                logger.warning(f"User {username} is locked out")
                return None
            
            # Check if user exists
            if username not in self.user_credentials:
                self._record_failed_attempt(username)
                return None
            
            user_data = self.user_credentials[username]
            
            # Verify password
            if not self._verify_password(password, user_data["password_hash"], user_data["salt"]):
                self._record_failed_attempt(username)
                return None
            
            # Reset failed attempts on successful login
            if username in self.login_attempts:
                del self.login_attempts[username]
            
            # Generate JWT token
            token = self._generate_jwt_token(username, user_data)
            
            # Store session
            self.active_sessions[token] = {
                "username": username,
                "role": user_data["role"],
                "permissions": user_data["permissions"],
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=self.session_timeout)
            }
            
            logger.info(f"User {username} authenticated successfully")
            return token
            
        except Exception as e:
            logger.error(f"Authentication failed for user {username}: {e}")
            return None
    
    def _is_user_locked_out(self, username: str) -> bool:
        """Check if user is locked out"""
        if username not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[username]
        if attempts["count"] >= self.max_attempts:
            lockout_end = attempts["last_attempt"] + timedelta(seconds=self.lockout_timeout)
            if datetime.utcnow() < lockout_end:
                return True
            else:
                # Lockout expired, reset attempts
                del self.login_attempts[username]
        
        return False
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.login_attempts:
            self.login_attempts[username] = {
                "count": 0,
                "last_attempt": None
            }
        
        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = datetime.utcnow()
        
        logger.warning(f"Failed login attempt for user {username}")
    
    def _generate_jwt_token(self, username: str, user_data: dict) -> str:
        """Generate JWT token"""
        payload = {
            "username": username,
            "role": user_data["role"],
            "permissions": user_data["permissions"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self.session_timeout)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return user data"""
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check if session exists and is not expired
            if token in self.active_sessions:
                session = self.active_sessions[token]
                if datetime.utcnow() < session["expires_at"]:
                    return session
                else:
                    # Session expired
                    del self.active_sessions[token]
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def logout_user(self, token: str) -> bool:
        """Logout user and invalidate session"""
        if token in self.active_sessions:
            del self.active_sessions[token]
            logger.info("User logged out successfully")
            return True
        return False
    
    def get_user_permissions(self, token: str) -> List[str]:
        """Get user permissions from token"""
        session = self.verify_token(token)
        if session:
            return session.get("permissions", [])
        return []
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = self.get_user_permissions(token)
        return permission in permissions

class AuthorizationManager:
    """Access control and authorization"""
    
    def __init__(self):
        self.resource_permissions = {}
        self.role_hierarchy = {
            "admin": ["read", "write", "execute", "admin"],
            "user": ["read", "write"],
            "viewer": ["read"]
        }
        self.resource_access_log = []
    
    def define_resource_permissions(self, resource: str, permissions: List[str]):
        """Define permissions for a resource"""
        self.resource_permissions[resource] = permissions
        logger.info(f"Resource permissions defined for {resource}: {permissions}")
    
    def check_access(self, token: str, resource: str, action: str) -> bool:
        """Check if user has access to perform action on resource"""
        try:
            # Get user permissions
            user_permissions = self.get_user_permissions(token)
            if not user_permissions:
                return False
            
            # Check if resource exists
            if resource not in self.resource_permissions:
                logger.warning(f"Resource {resource} not found")
                return False
            
            # Check if action is allowed for resource
            required_permissions = self.resource_permissions[resource]
            if action not in required_permissions:
                logger.warning(f"Action {action} not allowed for resource {resource}")
                return False
            
            # Check if user has required permission
            has_permission = any(perm in user_permissions for perm in required_permissions)
            
            # Log access attempt
            self.resource_access_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "resource": resource,
                "action": action,
                "granted": has_permission,
                "user_permissions": user_permissions
            })
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Access check failed: {e}")
            return False
    
    def get_user_permissions(self, token: str) -> List[str]:
        """Get user permissions from token (placeholder)"""
        # This would typically decode the token and extract permissions
        # For now, return empty list
        return []

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_entries = []
        self.lock = threading.Lock()
    
    def log_event(self, event_type: str, user: str, resource: str, action: str, 
                  success: bool, details: dict = None):
        """Log security event"""
        try:
            with self.lock:
                entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": event_type,
                    "user": user,
                    "resource": resource,
                    "action": action,
                    "success": success,
                    "details": details or {}
                }
                
                self.audit_entries.append(entry)
                
                # Write to file
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")
                
                logger.info(f"Audit event logged: {event_type}")
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def get_audit_entries(self, limit: int = 100) -> List[dict]:
        """Get recent audit entries"""
        with self.lock:
            return self.audit_entries[-limit:]

class ComplianceManager:
    """Compliance and regulatory requirements"""
    
    def __init__(self, standards: List[str] = None):
        self.standards = standards or ["HIPAA", "GDPR", "SOX"]
        self.compliance_checks = {}
        self.violation_log = []
        
        # Initialize compliance checks
        self._initialize_compliance_checks()
    
    def _initialize_compliance_checks(self):
        """Initialize compliance checks for different standards"""
        self.compliance_checks = {
            "HIPAA": {
                "data_encryption": True,
                "access_control": True,
                "audit_logging": True,
                "data_retention": 7 * 365 * 24 * 3600,  # 7 years
                "breach_notification": 60 * 24 * 3600  # 60 days
            },
            "GDPR": {
                "data_encryption": True,
                "access_control": True,
                "audit_logging": True,
                "data_retention": 365 * 24 * 3600,  # 1 year
                "breach_notification": 72 * 3600  # 72 hours
            },
            "SOX": {
                "data_encryption": True,
                "access_control": True,
                "audit_logging": True,
                "data_retention": 7 * 365 * 24 * 3600,  # 7 years
                "change_management": True
            }
        }
    
    def check_compliance(self, standard: str, data_type: str) -> dict:
        """Check compliance for specific standard and data type"""
        try:
            if standard not in self.compliance_checks:
                return {"compliant": False, "error": f"Standard {standard} not supported"}
            
            checks = self.compliance_checks[standard]
            results = {}
            
            # Check encryption requirement
            if checks.get("data_encryption", False):
                results["encryption_required"] = True
                results["encryption_status"] = "encrypted"  # Placeholder
            
            # Check access control
            if checks.get("access_control", False):
                results["access_control_required"] = True
                results["access_control_status"] = "enabled"  # Placeholder
            
            # Check audit logging
            if checks.get("audit_logging", False):
                results["audit_logging_required"] = True
                results["audit_logging_status"] = "enabled"  # Placeholder
            
            # Check data retention
            if "data_retention" in checks:
                results["data_retention_required"] = True
                results["retention_period_seconds"] = checks["data_retention"]
            
            # Overall compliance
            results["compliant"] = all(
                results.get(key, False) for key in results 
                if key.endswith("_status") and "enabled" in str(results[key])
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return {"compliant": False, "error": str(e)}
    
    def log_violation(self, standard: str, violation_type: str, details: dict):
        """Log compliance violation"""
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "standard": standard,
            "violation_type": violation_type,
            "details": details
        }
        
        self.violation_log.append(violation)
        logger.warning(f"Compliance violation logged: {standard} - {violation_type}")

class SecurityManager:
    """
    Main security management system
    - Data encryption
    - User authentication
    - Access control
    - Audit logging
    - Compliance management
    """
    
    def __init__(self, config: SecurityConfig):
        """
        Initialize security manager
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.encryption_manager = None
        self.auth_manager = None
        self.authz_manager = None
        self.audit_logger = None
        self.compliance_manager = None
        
        # Initialize components
        self._initialize_components()
        
        logger.info("SecurityManager initialized", 
                   encryption=config.enable_encryption,
                   authentication=config.enable_authentication,
                   authorization=config.enable_authorization,
                   audit_logging=config.enable_audit_logging,
                   compliance=config.enable_compliance)
    
    def _initialize_components(self):
        """Initialize security components"""
        try:
            # Initialize encryption manager
            if self.config.enable_encryption:
                self.encryption_manager = EncryptionManager(self.config.encryption_key)
                logger.info("Encryption manager initialized")
            
            # Initialize authentication manager
            if self.config.enable_authentication:
                self.auth_manager = AuthenticationManager(
                    self.config.jwt_secret_key,
                    self.config.session_timeout
                )
                logger.info("Authentication manager initialized")
            
            # Initialize authorization manager
            if self.config.enable_authorization:
                self.authz_manager = AuthorizationManager()
                logger.info("Authorization manager initialized")
            
            # Initialize audit logger
            if self.config.enable_audit_logging:
                self.audit_logger = AuditLogger(self.config.audit_log_file)
                logger.info("Audit logger initialized")
            
            # Initialize compliance manager
            if self.config.enable_compliance:
                self.compliance_manager = ComplianceManager(self.config.compliance_standards)
                logger.info("Compliance manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize security components: {e}")
            raise
    
    def encrypt_sensitive_data(self, data: Union[str, dict]) -> str:
        """Encrypt sensitive data"""
        if not self.encryption_manager:
            logger.warning("Encryption not enabled")
            return str(data)
        
        return self.encryption_manager.encrypt_data(data)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Union[str, dict]:
        """Decrypt sensitive data"""
        if not self.encryption_manager:
            logger.warning("Encryption not enabled")
            return encrypted_data
        
        return self.encryption_manager.decrypt_data(encrypted_data)
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user"""
        if not self.auth_manager:
            logger.warning("Authentication not enabled")
            return None
        
        token = self.auth_manager.authenticate_user(username, password)
        
        # Log authentication attempt
        if self.audit_logger:
            self.audit_logger.log_event(
                "authentication",
                username,
                "system",
                "login",
                token is not None
            )
        
        return token
    
    def verify_access(self, token: str, resource: str, action: str) -> bool:
        """Verify user access to resource"""
        if not self.authz_manager:
            logger.warning("Authorization not enabled")
            return True
        
        has_access = self.authz_manager.check_access(token, resource, action)
        
        # Log access attempt
        if self.audit_logger:
            user = "unknown"
            if self.auth_manager:
                session = self.auth_manager.verify_token(token)
                if session:
                    user = session.get("username", "unknown")
            
            self.audit_logger.log_event(
                "authorization",
                user,
                resource,
                action,
                has_access
            )
        
        return has_access
    
    def check_compliance(self, standard: str, data_type: str) -> dict:
        """Check compliance for data type"""
        if not self.compliance_manager:
            logger.warning("Compliance checking not enabled")
            return {"compliant": True}
        
        return self.compliance_manager.check_compliance(standard, data_type)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "encryption_enabled": self.config.enable_encryption,
                "authentication_enabled": self.config.enable_authentication,
                "authorization_enabled": self.config.enable_authorization,
                "audit_logging_enabled": self.config.enable_audit_logging,
                "compliance_enabled": self.config.enable_compliance,
                "active_sessions": len(self.auth_manager.active_sessions) if self.auth_manager else 0,
                "audit_entries": len(self.audit_logger.audit_entries) if self.audit_logger else 0,
                "compliance_standards": self.config.compliance_standards or []
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get security summary: {e}")
            return {}

# Factory function for easy security manager setup
def create_security_manager(
    enable_encryption: bool = True,
    enable_authentication: bool = True,
    enable_authorization: bool = True,
    enable_audit_logging: bool = True,
    enable_compliance: bool = True,
    **kwargs
) -> SecurityManager:
    """
    Create security manager with default configuration
    
    Args:
        enable_encryption: Enable data encryption
        enable_authentication: Enable user authentication
        enable_authorization: Enable access control
        enable_audit_logging: Enable audit logging
        enable_compliance: Enable compliance checking
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured SecurityManager
    """
    config = SecurityConfig(
        enable_encryption=enable_encryption,
        enable_authentication=enable_authentication,
        enable_authorization=enable_authorization,
        enable_audit_logging=enable_audit_logging,
        enable_compliance=enable_compliance,
        **kwargs
    )
    
    return SecurityManager(config)
