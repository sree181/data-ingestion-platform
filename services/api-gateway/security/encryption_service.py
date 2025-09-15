"""
Enterprise Encryption Service with Key Management
Implements AES-256 encryption, key rotation, and secure key storage
"""

import os
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class EncryptionKey(Base):
    __tablename__ = "encryption_keys"
    
    id = Column(Integer, primary_key=True)
    key_id = Column(String(64), unique=True, nullable=False)
    project_id = Column(Integer, nullable=True)  # None for master keys
    key_type = Column(String(20), nullable=False)  # master, project, document
    
    # Encrypted key material
    encrypted_key = Column(LargeBinary, nullable=False)
    key_derivation_salt = Column(LargeBinary, nullable=False)
    
    # Key metadata
    algorithm = Column(String(20), default="AES-256")
    key_version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Rotation and lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    rotation_frequency_days = Column(Integer, default=90)
    
    # Audit
    created_by = Column(Integer, nullable=False)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

class EncryptionAuditLog(Base):
    __tablename__ = "encryption_audit_logs"
    
    id = Column(Integer, primary_key=True)
    key_id = Column(String(64), nullable=False)
    operation = Column(String(20), nullable=False)  # encrypt, decrypt, rotate, create
    
    # Context
    user_id = Column(Integer, nullable=True)
    project_id = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    
    # Audit details
    ip_address = Column(String(45), nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class EnterpriseEncryptionService:
    def __init__(self, db_session: Session, master_password: str):
        self.db = db_session
        self.master_password = master_password
        self.backend = default_backend()
        
        # Initialize master key if not exists
        self._ensure_master_key()
    
    def _ensure_master_key(self):
        """Ensure master encryption key exists"""
        master_key = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_type == "master",
            EncryptionKey.is_active == True
        ).first()
        
        if not master_key:
            self._create_master_key()
    
    def _create_master_key(self) -> str:
        """Create new master encryption key"""
        # Generate key ID
        key_id = f"master_{secrets.token_hex(16)}"
        
        # Generate salt for key derivation
        salt = os.urandom(32)
        
        # Derive key from master password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        
        # Encrypt the actual encryption key
        f = Fernet(key)
        actual_key = Fernet.generate_key()
        encrypted_key = f.encrypt(actual_key)
        
        # Store in database
        master_key_record = EncryptionKey(
            key_id=key_id,
            key_type="master",
            encrypted_key=encrypted_key,
            key_derivation_salt=salt,
            created_by=1,  # System user
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        
        self.db.add(master_key_record)
        self.db.commit()
        
        self._log_encryption_operation(key_id, "create", success=True)
        return key_id
    
    def create_project_key(self, project_id: int, created_by: int) -> str:
        """Create encryption key for specific project"""
        # Generate key ID
        key_id = f"proj_{project_id}_{secrets.token_hex(12)}"
        
        # Generate project-specific key
        project_key = Fernet.generate_key()
        
        # Encrypt with master key
        master_key = self._get_master_key()
        encrypted_key = master_key.encrypt(project_key)
        
        # Generate salt for additional security
        salt = os.urandom(32)
        
        # Store in database
        project_key_record = EncryptionKey(
            key_id=key_id,
            project_id=project_id,
            key_type="project",
            encrypted_key=encrypted_key,
            key_derivation_salt=salt,
            created_by=created_by,
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        
        self.db.add(project_key_record)
        self.db.commit()
        
        self._log_encryption_operation(
            key_id, "create", 
            user_id=created_by, 
            project_id=project_id
        )
        
        return key_id
    
    def encrypt_data(self, data: bytes, key_id: str, user_id: int = None, 
                    resource_type: str = None, resource_id: str = None) -> Dict:
        """Encrypt data with specified key"""
        try:
            # Get encryption key
            key_record = self.db.query(EncryptionKey).filter(
                EncryptionKey.key_id == key_id,
                EncryptionKey.is_active == True
            ).first()
            
            if not key_record:
                raise ValueError(f"Encryption key {key_id} not found or inactive")
            
            # Check if key needs rotation
            if self._key_needs_rotation(key_record):
                self._rotate_key(key_record)
            
            # Get decrypted key
            encryption_key = self._decrypt_key(key_record)
            
            # Encrypt data
            f = Fernet(encryption_key)
            encrypted_data = f.encrypt(data)
            
            # Update usage statistics
            key_record.usage_count += 1
            key_record.last_used = datetime.utcnow()
            self.db.commit()
            
            # Log operation
            self._log_encryption_operation(
                key_id, "encrypt",
                user_id=user_id,
                project_id=key_record.project_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            return {
                "encrypted_data": base64.b64encode(encrypted_data).decode(),
                "key_id": key_id,
                "algorithm": key_record.algorithm,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._log_encryption_operation(
                key_id, "encrypt",
                user_id=user_id,
                success=False,
                error_message=str(e)
            )
            raise
    
    def decrypt_data(self, encrypted_data_b64: str, key_id: str, 
                    user_id: int = None, resource_type: str = None, 
                    resource_id: str = None) -> bytes:
        """Decrypt data with specified key"""
        try:
            # Get encryption key
            key_record = self.db.query(EncryptionKey).filter(
                EncryptionKey.key_id == key_id,
                EncryptionKey.is_active == True
            ).first()
            
            if not key_record:
                raise ValueError(f"Encryption key {key_id} not found or inactive")
            
            # Get decrypted key
            encryption_key = self._decrypt_key(key_record)
            
            # Decrypt data
            f = Fernet(encryption_key)
            encrypted_data = base64.b64decode(encrypted_data_b64.encode())
            decrypted_data = f.decrypt(encrypted_data)
            
            # Update usage statistics
            key_record.usage_count += 1
            key_record.last_used = datetime.utcnow()
            self.db.commit()
            
            # Log operation
            self._log_encryption_operation(
                key_id, "decrypt",
                user_id=user_id,
                project_id=key_record.project_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            return decrypted_data
            
        except Exception as e:
            self._log_encryption_operation(
                key_id, "decrypt",
                user_id=user_id,
                success=False,
                error_message=str(e)
            )
            raise
    
    def rotate_key(self, key_id: str, user_id: int) -> str:
        """Manually rotate encryption key"""
        key_record = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id,
            EncryptionKey.is_active == True
        ).first()
        
        if not key_record:
            raise ValueError(f"Encryption key {key_id} not found or inactive")
        
        return self._rotate_key(key_record, user_id)
    
    def _rotate_key(self, key_record: EncryptionKey, user_id: int = None) -> str:
        """Rotate encryption key"""
        try:
            # Mark old key as inactive
            key_record.is_active = False
            key_record.rotated_at = datetime.utcnow()
            
            # Create new key
            if key_record.key_type == "master":
                new_key_id = self._create_master_key()
            elif key_record.key_type == "project":
                new_key_id = self.create_project_key(
                    key_record.project_id, 
                    user_id or key_record.created_by
                )
            else:
                raise ValueError(f"Unsupported key type: {key_record.key_type}")
            
            self.db.commit()
            
            self._log_encryption_operation(
                key_record.key_id, "rotate",
                user_id=user_id,
                project_id=key_record.project_id
            )
            
            return new_key_id
            
        except Exception as e:
            self._log_encryption_operation(
                key_record.key_id, "rotate",
                user_id=user_id,
                success=False,
                error_message=str(e)
            )
            raise
    
    def _key_needs_rotation(self, key_record: EncryptionKey) -> bool:
        """Check if key needs rotation"""
        if key_record.expires_at and key_record.expires_at <= datetime.utcnow():
            return True
        
        rotation_due = key_record.created_at + timedelta(days=key_record.rotation_frequency_days)
        if rotation_due <= datetime.utcnow():
            return True
        
        return False
    
    def _get_master_key(self) -> Fernet:
        """Get active master key"""
        master_key_record = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_type == "master",
            EncryptionKey.is_active == True
        ).first()
        
        if not master_key_record:
            raise ValueError("No active master key found")
        
        return self._decrypt_key(master_key_record)
    
    def _decrypt_key(self, key_record: EncryptionKey) -> Fernet:
        """Decrypt stored encryption key"""
        if key_record.key_type == "master":
            # Derive key from master password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=key_record.key_derivation_salt,
                iterations=100000,
                backend=self.backend
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
            f = Fernet(derived_key)
            actual_key = f.decrypt(key_record.encrypted_key)
            return Fernet(actual_key)
        else:
            # Decrypt with master key
            master_key = self._get_master_key()
            actual_key = master_key.decrypt(key_record.encrypted_key)
            return Fernet(actual_key)
    
    def get_key_info(self, key_id: str) -> Dict:
        """Get key information (without exposing key material)"""
        key_record = self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == key_id
        ).first()
        
        if not key_record:
            raise ValueError(f"Key {key_id} not found")
        
        return {
            "key_id": key_record.key_id,
            "key_type": key_record.key_type,
            "project_id": key_record.project_id,
            "algorithm": key_record.algorithm,
            "key_version": key_record.key_version,
            "is_active": key_record.is_active,
            "created_at": key_record.created_at.isoformat(),
            "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
            "usage_count": key_record.usage_count,
            "last_used": key_record.last_used.isoformat() if key_record.last_used else None,
            "needs_rotation": self._key_needs_rotation(key_record)
        }
    
    def get_project_keys(self, project_id: int) -> List[Dict]:
        """Get all keys for a project"""
        keys = self.db.query(EncryptionKey).filter(
            EncryptionKey.project_id == project_id
        ).all()
        
        return [self.get_key_info(key.key_id) for key in keys]
    
    def get_encryption_metrics(self, project_id: int = None) -> Dict:
        """Get encryption usage metrics"""
        query = self.db.query(EncryptionKey)
        if project_id:
            query = query.filter(EncryptionKey.project_id == project_id)
        
        keys = query.all()
        
        total_keys = len(keys)
        active_keys = len([k for k in keys if k.is_active])
        keys_needing_rotation = len([k for k in keys if self._key_needs_rotation(k)])
        total_usage = sum(k.usage_count for k in keys)
        
        # Get audit log stats
        audit_query = self.db.query(EncryptionAuditLog)
        if project_id:
            audit_query = audit_query.filter(EncryptionAuditLog.project_id == project_id)
        
        recent_operations = audit_query.filter(
            EncryptionAuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        failed_operations = audit_query.filter(
            EncryptionAuditLog.success == False,
            EncryptionAuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "keys_needing_rotation": keys_needing_rotation,
            "total_usage_count": total_usage,
            "recent_operations_30d": recent_operations,
            "failed_operations_30d": failed_operations,
            "encryption_health_score": self._calculate_encryption_health_score(keys)
        }
    
    def _calculate_encryption_health_score(self, keys: List[EncryptionKey]) -> float:
        """Calculate encryption health score (0-100)"""
        if not keys:
            return 100.0
        
        score = 100.0
        
        # Deduct for keys needing rotation
        keys_needing_rotation = len([k for k in keys if self._key_needs_rotation(k)])
        rotation_penalty = (keys_needing_rotation / len(keys)) * 30
        score -= rotation_penalty
        
        # Deduct for inactive keys (indicates potential issues)
        inactive_keys = len([k for k in keys if not k.is_active])
        inactive_penalty = (inactive_keys / len(keys)) * 20
        score -= inactive_penalty
        
        # Deduct for old keys (security risk)
        old_keys = len([k for k in keys if k.created_at < datetime.utcnow() - timedelta(days=180)])
        age_penalty = (old_keys / len(keys)) * 15
        score -= age_penalty
        
        return max(0.0, score)
    
    def _log_encryption_operation(self, key_id: str, operation: str, 
                                user_id: int = None, project_id: int = None,
                                resource_type: str = None, resource_id: str = None,
                                ip_address: str = None, success: bool = True,
                                error_message: str = None):
        """Log encryption operation for audit"""
        log_entry = EncryptionAuditLog(
            key_id=key_id,
            operation=operation,
            user_id=user_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
        
        self.db.add(log_entry)
        self.db.commit()

class DocumentEncryptionManager:
    """High-level document encryption manager"""
    
    def __init__(self, encryption_service: EnterpriseEncryptionService):
        self.encryption_service = encryption_service
    
    def encrypt_document(self, document_content: bytes, project_id: int, 
                        document_id: str, user_id: int) -> Dict:
        """Encrypt document content"""
        # Get or create project key
        project_keys = self.encryption_service.get_project_keys(project_id)
        active_key = next((k for k in project_keys if k["is_active"]), None)
        
        if not active_key:
            # Create new project key
            key_id = self.encryption_service.create_project_key(project_id, user_id)
        else:
            key_id = active_key["key_id"]
        
        # Encrypt document
        result = self.encryption_service.encrypt_data(
            document_content,
            key_id,
            user_id=user_id,
            resource_type="document",
            resource_id=document_id
        )
        
        # Calculate checksum for integrity
        checksum = hashlib.sha256(document_content).hexdigest()
        result["checksum"] = checksum
        
        return result
    
    def decrypt_document(self, encrypted_data: str, key_id: str, 
                        document_id: str, user_id: int) -> bytes:
        """Decrypt document content"""
        return self.encryption_service.decrypt_data(
            encrypted_data,
            key_id,
            user_id=user_id,
            resource_type="document",
            resource_id=document_id
        )
    
    def verify_document_integrity(self, decrypted_content: bytes, 
                                expected_checksum: str) -> bool:
        """Verify document integrity using checksum"""
        actual_checksum = hashlib.sha256(decrypted_content).hexdigest()
        return actual_checksum == expected_checksum
