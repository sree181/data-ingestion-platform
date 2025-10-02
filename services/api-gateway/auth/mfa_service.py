"""
Multi-Factor Authentication (MFA) Service
Implements TOTP-based MFA with QR code generation and verification
"""

import pyotp
import qrcode
import io
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from fastapi import HTTPException
import structlog

logger = structlog.get_logger(__name__)

class MFAService:
    """Multi-Factor Authentication Service using TOTP"""
    
    def __init__(self, issuer_name: str = "Data Ingestion Platform"):
        self.issuer_name = issuer_name
        self.totp_digits = 6
        self.totp_interval = 30
        self.backup_codes_count = 10
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_id: str, email: str, secret: str) -> str:
        """Generate QR code for MFA setup"""
        try:
            # Create TOTP object
            totp = pyotp.TOTP(secret)
            
            # Generate provisioning URI
            provisioning_uri = totp.provisioning_uri(
                name=email,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info("QR code generated for MFA setup", user_id=user_id, email=email)
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error("Failed to generate QR code", error=str(e), user_id=user_id)
            raise HTTPException(status_code=500, detail="Failed to generate QR code")
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=1)  # Allow 1 window tolerance
            
            if is_valid:
                logger.info("TOTP token verified successfully")
            else:
                logger.warning("Invalid TOTP token provided")
            
            return is_valid
            
        except Exception as e:
            logger.error("TOTP verification failed", error=str(e))
            return False
    
    def generate_backup_codes(self) -> list:
        """Generate backup codes for MFA recovery"""
        backup_codes = []
        for _ in range(self.backup_codes_count):
            code = secrets.token_urlsafe(8).upper()
            backup_codes.append(code)
        
        logger.info("Backup codes generated", count=len(backup_codes))
        return backup_codes
    
    def verify_backup_code(self, provided_code: str, stored_codes: list) -> bool:
        """Verify backup code"""
        if not stored_codes:
            return False
        
        # Check if code exists and remove it (one-time use)
        if provided_code in stored_codes:
            stored_codes.remove(provided_code)
            logger.info("Backup code verified and consumed")
            return True
        
        logger.warning("Invalid backup code provided")
        return False
    
    def setup_mfa(self, user_id: str, email: str) -> Dict:
        """Setup MFA for a user"""
        try:
            # Generate secret and QR code
            secret = self.generate_secret()
            qr_code = self.generate_qr_code(user_id, email, secret)
            backup_codes = self.generate_backup_codes()
            
            setup_data = {
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "manual_entry_key": secret,
                "setup_instructions": {
                    "step1": "Scan the QR code with your authenticator app",
                    "step2": "Enter the 6-digit code from your app to verify",
                    "step3": "Save the backup codes in a secure location",
                    "step4": "Test the setup by entering a verification code"
                }
            }
            
            logger.info("MFA setup initiated", user_id=user_id, email=email)
            return setup_data
            
        except Exception as e:
            logger.error("MFA setup failed", error=str(e), user_id=user_id)
            raise HTTPException(status_code=500, detail="MFA setup failed")
    
    def verify_mfa_setup(self, secret: str, verification_code: str) -> bool:
        """Verify MFA setup with a test code"""
        return self.verify_totp(secret, verification_code)
    
    def authenticate_with_mfa(self, secret: str, token: str, backup_codes: list = None) -> Dict:
        """Authenticate user with MFA"""
        try:
            # Try TOTP first
            if self.verify_totp(secret, token):
                return {
                    "success": True,
                    "method": "totp",
                    "message": "MFA authentication successful"
                }
            
            # Try backup codes if provided
            if backup_codes and self.verify_backup_code(token, backup_codes):
                return {
                    "success": True,
                    "method": "backup_code",
                    "message": "MFA authentication successful with backup code"
                }
            
            return {
                "success": False,
                "message": "Invalid MFA token"
            }
            
        except Exception as e:
            logger.error("MFA authentication failed", error=str(e))
            return {
                "success": False,
                "message": "MFA authentication error"
            }

# Global MFA service instance
mfa_service = MFAService()
