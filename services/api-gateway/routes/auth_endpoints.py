"""
Authentication Endpoints
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
from security.rate_limiter import check_rate_limit
from security.security_monitor import security_monitor, SecurityEventType, ThreatLevel

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
        # Rate limiting for login attempts
        is_limited, rate_info = check_rate_limit(request, "auth", "login", login_data.email)
        if is_limited:
            await security_monitor.log_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                None,
                request.client.host,
                request.headers.get("user-agent", "unknown"),
                "auth:login",
                "login_attempt",
                {"email": login_data.email, "rate_info": rate_info},
                ThreatLevel.MEDIUM
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rate_info.get('reason', 'Too many login attempts')}",
                headers=rate_info.get("headers", {})
            )
        
        # TODO: Replace with actual user authentication
        # For now, we'll simulate authentication
        if login_data.email == "admin@example.com" and login_data.password == "admin123":
            user_id = "db9e2b54-9d8c-4c49-8a3a-7c318de748e3"
            user_roles = ["owner", "admin"]
            user_permissions = ["read", "write", "delete", "admin"]
            mfa_enabled = True
            mfa_verified = False
            
            # Check MFA if enabled
            if mfa_enabled and not login_data.mfa_token:
                # MFA required but not provided
                await security_monitor.log_event(
                    SecurityEventType.MFA_BYPASS_ATTEMPT,
                    user_id,
                    request.client.host,
                    request.headers.get("user-agent", "unknown"),
                    "auth:login",
                    "mfa_required",
                    {"email": login_data.email},
                    ThreatLevel.MEDIUM
                )
                
                return LoginResponse(
                    access_token="",
                    refresh_token="",
                    token_type="bearer",
                    expires_in=0,
                    mfa_required=True,
                    user_info={
                        "user_id": user_id,
                        "email": login_data.email,
                        "roles": user_roles,
                        "permissions": user_permissions
                    }
                )
            
            # Verify MFA token if provided
            if mfa_enabled and login_data.mfa_token:
                # TODO: Get user's MFA secret from database
                mfa_secret = "JBSWY3DPEHPK3PXP"  # This would come from database
                mfa_result = mfa_service.authenticate_with_mfa(mfa_secret, login_data.mfa_token)
                
                if not mfa_result["success"]:
                    await security_monitor.log_event(
                        SecurityEventType.AUTH_FAILURE,
                        user_id,
                        request.client.host,
                        request.headers.get("user-agent", "unknown"),
                        "auth:login",
                        "invalid_mfa_token",
                        {"email": login_data.email},
                        ThreatLevel.MEDIUM
                    )
                    raise HTTPException(status_code=401, detail="Invalid MFA token")
                
                mfa_verified = True
            
            # Generate tokens
            token_pair = jwt_service.generate_token_pair(
                user_id=user_id,
                email=login_data.email,
                roles=user_roles,
                permissions=user_permissions,
                mfa_verified=mfa_verified
            )
            
            # Log successful login
            await security_monitor.log_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,  # Using this as a general event type
                user_id,
                request.client.host,
                request.headers.get("user-agent", "unknown"),
                "auth:login",
                "successful_login",
                {"email": login_data.email, "mfa_verified": mfa_verified},
                ThreatLevel.LOW
            )
            
            return LoginResponse(
                access_token=token_pair["access_token"],
                refresh_token=token_pair["refresh_token"],
                token_type=token_pair["token_type"],
                expires_in=token_pair["expires_in"],
                mfa_required=False,
                user_info={
                    "user_id": user_id,
                    "email": login_data.email,
                    "roles": user_roles,
                    "permissions": user_permissions,
                    "mfa_enabled": mfa_enabled,
                    "mfa_verified": mfa_verified
                }
            )
        
        else:
            # Invalid credentials
            await security_monitor.log_event(
                SecurityEventType.AUTH_FAILURE,
                None,
                request.client.host,
                request.headers.get("user-agent", "unknown"),
                "auth:login",
                "invalid_credentials",
                {"email": login_data.email},
                ThreatLevel.MEDIUM
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e), email=login_data.email)
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(mfa_data: MfaSetupRequest, request: Request):
    """Setup MFA for a user"""
    try:
        # Rate limiting for MFA setup
        is_limited, rate_info = check_rate_limit(request, "auth", "mfa", mfa_data.user_id)
        if is_limited:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rate_info.get('reason', 'Too many MFA setup attempts')}",
                headers=rate_info.get("headers", {})
            )
        
        # Setup MFA
        setup_data = mfa_service.setup_mfa(mfa_data.user_id, "user@example.com")  # TODO: Get email from user_id
        
        # Log MFA setup
        await security_monitor.log_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            mfa_data.user_id,
            request.client.host,
            request.headers.get("user-agent", "unknown"),
            "auth:mfa_setup",
            "mfa_setup_initiated",
            {"user_id": mfa_data.user_id},
            ThreatLevel.LOW
        )
        
        return MfaSetupResponse(
            qr_code=setup_data["qr_code"],
            backup_codes=setup_data["backup_codes"],
            manual_entry_key=setup_data["manual_entry_key"],
            setup_instructions=setup_data["setup_instructions"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("MFA setup failed", error=str(e), user_id=mfa_data.user_id)
        raise HTTPException(status_code=500, detail="MFA setup failed")

@router.post("/mfa/verify", response_model=MfaVerifyResponse)
async def verify_mfa(mfa_data: MfaVerifyRequest, request: Request):
    """Verify MFA setup with a test token"""
    try:
        # Rate limiting for MFA verification
        is_limited, rate_info = check_rate_limit(request, "auth", "mfa", mfa_data.user_id)
        if is_limited:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rate_info.get('reason', 'Too many MFA verification attempts')}",
                headers=rate_info.get("headers", {})
            )
        
        # Verify MFA setup
        is_valid = mfa_service.verify_mfa_setup(mfa_data.secret, mfa_data.token)
        
        if is_valid:
            # Log successful MFA verification
            await security_monitor.log_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                mfa_data.user_id,
                request.client.host,
                request.headers.get("user-agent", "unknown"),
                "auth:mfa_verify",
                "mfa_setup_verified",
                {"user_id": mfa_data.user_id},
                ThreatLevel.LOW
            )
            
            return MfaVerifyResponse(
                success=True,
                message="MFA setup verified successfully"
            )
        else:
            # Log failed MFA verification
            await security_monitor.log_event(
                SecurityEventType.AUTH_FAILURE,
                mfa_data.user_id,
                request.client.host,
                request.headers.get("user-agent", "unknown"),
                "auth:mfa_verify",
                "invalid_mfa_token",
                {"user_id": mfa_data.user_id},
                ThreatLevel.MEDIUM
            )
            
            return MfaVerifyResponse(
                success=False,
                message="Invalid MFA token"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("MFA verification failed", error=str(e), user_id=mfa_data.user_id)
        raise HTTPException(status_code=500, detail="MFA verification failed")

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(refresh_data: TokenRefreshRequest, request: Request):
    """Refresh access token using refresh token"""
    try:
        # Rate limiting for token refresh
        is_limited, rate_info = check_rate_limit(request, "auth", "refresh", "anonymous")
        if is_limited:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rate_info.get('reason', 'Too many token refresh attempts')}",
                headers=rate_info.get("headers", {})
            )
        
        # Refresh token
        new_tokens = jwt_service.refresh_access_token(refresh_data.refresh_token)
        
        # Log token refresh
        await security_monitor.log_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            None,
            request.client.host,
            request.headers.get("user-agent", "unknown"),
            "auth:refresh",
            "token_refreshed",
            {},
            ThreatLevel.LOW
        )
        
        return TokenRefreshResponse(
            access_token=new_tokens["access_token"],
            token_type=new_tokens["token_type"],
            expires_in=new_tokens["expires_in"]
        )
    
    except HTTPException:
        raise
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
        "mfa_verified": user["mfa_verified"]
    }
