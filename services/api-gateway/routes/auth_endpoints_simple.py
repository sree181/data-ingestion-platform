"""
Simplified Authentication Endpoints
Handles login, MFA setup, token refresh, and user management
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from typing import Dict, Optional
import structlog
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from auth.jwt_auth import jwt_service, get_current_user
from auth.mfa_service import mfa_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    mfa_required: bool = False
    user_info: Dict

class MfaSetupRequest(BaseModel):
    user_id: str

class MfaSetupResponse(BaseModel):
    qr_code: str
    backup_codes: list
    manual_entry_key: str
    setup_instructions: Dict

class MfaVerifyRequest(BaseModel):
    user_id: str
    token: str
    secret: str

class MfaVerifyResponse(BaseModel):
    success: bool
    message: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user with email and password"""
    try:
        # Simple authentication for now
        if login_data.email == "admin@example.com" and login_data.password == "admin123":
            user_id = "db9e2b54-9d8c-4c49-8a3a-7c318de748e3"
            user_roles = ["owner", "admin"]
            user_permissions = ["read", "write", "delete", "admin"]
            mfa_enabled = False  # Disable MFA for now
            mfa_verified = True
            
            # Generate tokens
            token_pair = jwt_service.generate_token_pair(
                user_id=user_id,
                email=login_data.email,
                roles=user_roles,
                permissions=user_permissions,
                mfa_verified=mfa_verified
            )
            
            return LoginResponse(
                access_token=token_pair["access_token"],
                refresh_token=token_pair["refresh_token"],
                token_type="bearer",
                expires_in=jwt_service.access_token_expire_minutes * 60,
                mfa_required=False,
                user_info={
                    "user_id": user_id,
                    "email": login_data.email,
                    "roles": user_roles,
                    "permissions": user_permissions
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(mfa_data: MfaSetupRequest, request: Request):
    """Setup MFA for a user"""
    try:
        # Generate MFA secret
        secret = mfa_service.generate_mfa_secret()
        
        # Generate QR code
        qr_code = mfa_service.generate_qr_code(mfa_data.user_id, secret)
        
        # Generate backup codes
        backup_codes = mfa_service.generate_backup_codes()
        
        return MfaSetupResponse(
            qr_code=qr_code,
            backup_codes=backup_codes,
            manual_entry_key=secret,
            setup_instructions={
                "step1": "Scan the QR code with your authenticator app",
                "step2": "Enter the 6-digit code to verify setup",
                "step3": "Save the backup codes in a secure location"
            }
        )
        
    except Exception as e:
        logger.error("MFA setup failed", error=str(e))
        raise HTTPException(status_code=500, detail="MFA setup failed")

@router.post("/mfa/verify", response_model=MfaVerifyResponse)
async def verify_mfa_setup(mfa_data: MfaVerifyRequest, request: Request):
    """Verify MFA setup and enable it"""
    try:
        # Verify MFA token
        is_valid = mfa_service.verify_mfa_token(mfa_data.secret, mfa_data.token)
        
        if is_valid:
            # TODO: Save MFA secret to database
            return MfaVerifyResponse(
                success=True,
                message="MFA setup completed successfully"
            )
        else:
            return MfaVerifyResponse(
                success=False,
                message="Invalid MFA token"
            )
            
    except Exception as e:
        logger.error("MFA verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="MFA verification failed")

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(refresh_data: TokenRefreshRequest, request: Request):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = jwt_service.decode_token(refresh_data.refresh_token)
        
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Generate new access token
        new_access_token = jwt_service.create_access_token(
            user_id=payload["user_id"],
            email=payload["email"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            mfa_verified=payload.get("mfa_verified", False)
        )
        
        return TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=jwt_service.access_token_expire_minutes * 60
        )
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "roles": user["roles"],
        "permissions": user["permissions"],
        "mfa_verified": user.get("mfa_verified", False)
    }
