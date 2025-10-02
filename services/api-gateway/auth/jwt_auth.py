"""
JWT Authentication Service
Implements secure JWT token generation, validation, and refresh
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
import structlog

logger = structlog.get_logger(__name__)

class JWTAuthService:
    """JWT Authentication Service with enhanced security"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = 7
        self.security = HTTPBearer(auto_error=False)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_token_pair(self, user_id: str, email: str, roles: list = None, 
                          permissions: list = None, mfa_verified: bool = False) -> Dict[str, str]:
        """Generate access and refresh token pair"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "user_id": user_id,
            "email": email,
            "roles": roles or [],
            "permissions": permissions or [],
            "mfa_verified": mfa_verified,
            "token_type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "jti": secrets.token_urlsafe(32)  # JWT ID for token tracking
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": user_id,
            "email": email,
            "token_type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
            "jti": secrets.token_urlsafe(32)
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info("Token pair generated", user_id=user_id, email=email, mfa_verified=mfa_verified)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("token_type") != token_type:
                raise HTTPException(status_code=401, detail=f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise HTTPException(status_code=401, detail="Token expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Generate new access token from refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            
            # Generate new access token
            now = datetime.utcnow()
            access_payload = {
                "user_id": payload["user_id"],
                "email": payload["email"],
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "mfa_verified": False,  # MFA must be re-verified
                "token_type": "access",
                "iat": now,
                "exp": now + timedelta(minutes=self.access_token_expire_minutes),
                "jti": secrets.token_urlsafe(32)
            }
            
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info("Access token refreshed", user_id=payload["user_id"])
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise HTTPException(status_code=401, detail="Token refresh failed")
    
    def get_user_from_token(self, token: str) -> Dict:
        """Extract user information from token"""
        payload = self.verify_token(token)
        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "mfa_verified": payload.get("mfa_verified", False)
        }
    
    def require_mfa(self, token: str) -> bool:
        """Check if MFA is required for the current operation"""
        payload = self.verify_token(token)
        return not payload.get("mfa_verified", False)

# Global JWT service instance
jwt_service = JWTAuthService(
    secret_key="your-secret-key-change-in-production",  # TODO: Move to environment variable
    algorithm="HS256",
    access_token_expire_minutes=30
)

# FastAPI dependency for JWT authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(jwt_service.security)):
    """FastAPI dependency to get current authenticated user from JWT"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user = jwt_service.get_user_from_token(credentials.credentials)
        logger.info("User authenticated", user_id=user["user_id"], email=user["email"])
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(status_code=401, detail="Authentication failed")

# FastAPI dependency for MFA verification
async def require_mfa_verification(credentials: HTTPAuthorizationCredentials = Depends(jwt_service.security)):
    """FastAPI dependency to require MFA verification"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if jwt_service.require_mfa(credentials.credentials):
        raise HTTPException(status_code=403, detail="Multi-factor authentication required")
    
    return jwt_service.get_user_from_token(credentials.credentials)

# Initialize JWT service instance
jwt_service = JWTAuthService(
    secret_key="your-secret-key-change-in-production",
    algorithm="HS256",
    access_token_expire_minutes=30
)
