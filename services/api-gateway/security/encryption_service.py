"""
Document Encryption Service
Handles encryption and decryption of documents based on their classification level.
"""

import os
import base64
import hashlib
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets
import json
import logging

from models.security_models import DataClassification, EncryptionKey

logger = logging.getLogger(__name__)

class DocumentEncryptionService:
    """Service for encrypting and decrypting documents based on classification."""
    
    def __init__(self):
        self.encryption_keys: Dict[str, bytes] = {}
        self.master_key: Optional[bytes] = None
        self._initialize_master_key()
    
    def _initialize_master_key(self):
        """Initialize or retrieve the master encryption key."""
        try:
            # In production, this should be stored securely (e.g., AWS KMS, Azure Key Vault)
            master_key_env = os.getenv('MASTER_ENCRYPTION_KEY')
            if master_key_env:
                self.master_key = base64.b64decode(master_key_env)
            else:
                # Generate a new master key (for development)
                self.master_key = Fernet.generate_key()
                logger.warning("Using generated master key. In production, set MASTER_ENCRYPTION_KEY environment variable.")
        except Exception as e:
            logger.error(f"Failed to initialize master key: {e}")
            raise
    
    def _derive_key(self, classification: str, salt: bytes) -> bytes:
        """Derive a classification-specific key from the master key."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(f"{classification}_{self.master_key}".encode())
            return key
        except Exception as e:
            logger.error(f"Failed to derive key for classification {classification}: {e}")
            raise
    
    def _get_classification_salt(self, classification: str) -> bytes:
        """Get or generate a salt for the classification."""
        # In production, salts should be stored securely
        salt_key = f"salt_{classification}"
        if salt_key in self.encryption_keys:
            return self.encryption_keys[salt_key]
        
        # Generate new salt
        salt = secrets.token_bytes(32)
        self.encryption_keys[salt_key] = salt
        return salt
    
    def _get_encryption_key(self, classification: str) -> bytes:
        """Get the encryption key for a specific classification."""
        salt = self._get_classification_salt(classification)
        return self._derive_key(classification, salt)
    
    def encrypt_document(self, content: bytes, classification: str, document_id: str) -> Dict[str, Any]:
        """
        Encrypt document content based on classification level.
        
        Args:
            content: Raw document content
            classification: Document classification level
            document_id: Unique document identifier
            
        Returns:
            Dictionary containing encrypted content and metadata
        """
        try:
            logger.info(f"Encrypting document {document_id} with classification {classification}")
            
            # Get classification-specific key
            key = self._get_encryption_key(classification)
            
            # Generate random IV for this encryption
            iv = secrets.token_bytes(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad content to multiple of 16 bytes (AES block size)
            padding_length = 16 - (len(content) % 16)
            padded_content = content + bytes([padding_length] * padding_length)
            
            # Encrypt content
            encrypted_content = encryptor.update(padded_content) + encryptor.finalize()
            
            # Encode encrypted content and IV
            encrypted_b64 = base64.b64encode(encrypted_content).decode('utf-8')
            iv_b64 = base64.b64encode(iv).decode('utf-8')
            
            # Create metadata
            metadata = {
                'document_id': document_id,
                'classification': classification,
                'encryption_algorithm': 'AES-256-CBC',
                'iv': iv_b64,
                'salt': base64.b64encode(self._get_classification_salt(classification)).decode('utf-8'),
                'encrypted_content': encrypted_b64,
                'original_size': len(content),
                'encrypted_size': len(encrypted_content)
            }
            
            logger.info(f"Document {document_id} encrypted successfully. Size: {len(content)} -> {len(encrypted_content)} bytes")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to encrypt document {document_id}: {e}")
            raise
    
    def decrypt_document(self, metadata: Dict[str, Any]) -> bytes:
        """
        Decrypt document content using stored metadata.
        
        Args:
            metadata: Dictionary containing encryption metadata
            
        Returns:
            Decrypted document content
        """
        try:
            document_id = metadata.get('document_id')
            classification = metadata.get('classification')
            encrypted_content = base64.b64decode(metadata['encrypted_content'])
            iv = base64.b64decode(metadata['iv'])
            salt = base64.b64decode(metadata['salt'])
            
            logger.info(f"Decrypting document {document_id} with classification {classification}")
            
            # Derive the same key used for encryption
            key = self._derive_key(classification, salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt content
            decrypted_padded = decryptor.update(encrypted_content) + decryptor.finalize()
            
            # Remove padding
            padding_length = decrypted_padded[-1]
            decrypted_content = decrypted_padded[:-padding_length]
            
            logger.info(f"Document {document_id} decrypted successfully. Size: {len(encrypted_content)} -> {len(decrypted_content)} bytes")
            
            return decrypted_content
            
        except Exception as e:
            logger.error(f"Failed to decrypt document {document_id}: {e}")
            raise
    
    def get_encryption_status(self, document_id: str) -> Dict[str, Any]:
        """Get encryption status for a document."""
        try:
            # This would typically query the database for encryption metadata
            # For now, return a mock status
            return {
                'document_id': document_id,
                'is_encrypted': True,
                'encryption_algorithm': 'AES-256-CBC',
                'classification': 'Confidential',
                'encrypted_at': '2025-09-30T20:58:39Z'
            }
        except Exception as e:
            logger.error(f"Failed to get encryption status for document {document_id}: {e}")
            return {
                'document_id': document_id,
                'is_encrypted': False,
                'error': str(e)
            }
    
    def rekey_document(self, document_id: str, old_classification: str, new_classification: str) -> Dict[str, Any]:
        """
        Re-encrypt a document with a new classification level.
        
        Args:
            document_id: Document identifier
            old_classification: Current classification
            new_classification: New classification level
            
        Returns:
            Updated encryption metadata
        """
        try:
            logger.info(f"Rekeying document {document_id} from {old_classification} to {new_classification}")
            
            # In a real implementation, this would:
            # 1. Retrieve the document from storage
            # 2. Decrypt with old classification
            # 3. Re-encrypt with new classification
            # 4. Update metadata in database
            
            # For now, return a mock response
            return {
                'document_id': document_id,
                'old_classification': old_classification,
                'new_classification': new_classification,
                'rekeyed_at': '2025-09-30T20:58:39Z',
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to rekey document {document_id}: {e}")
            raise
    
    def get_classification_encryption_info(self, classification: str) -> Dict[str, Any]:
        """Get encryption information for a specific classification level."""
        try:
            salt = self._get_classification_salt(classification)
            key = self._get_encryption_key(classification)
            
            return {
                'classification': classification,
                'encryption_algorithm': 'AES-256-CBC',
                'key_derivation': 'PBKDF2-SHA256',
                'iterations': 100000,
                'salt_length': len(salt),
                'key_length': len(key),
                'is_configured': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get encryption info for classification {classification}: {e}")
            return {
                'classification': classification,
                'is_configured': False,
                'error': str(e)
            }

# Global encryption service instance
encryption_service = DocumentEncryptionService()