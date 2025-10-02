"""
Simple JWT Authentication
Minimal working JWT authentication for testing
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Optional
import jwt
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Simple JWT configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Simple login endpoint"""
    try:
        # Simple authentication
        if login_data.email == "admin@example.com" and login_data.password == "admin123":
            # Create token
            token_data = {
                "user_id": "db9e2b54-9d8c-4c49-8a3a-7c318de748e3",
                "email": login_data.email,
                "roles": ["owner", "admin"],
                "permissions": ["read", "write", "delete", "admin"]
            }
            
            access_token = create_access_token(token_data)
            
            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "user_id": token_data["user_id"],
                    "email": token_data["email"],
                    "roles": token_data["roles"],
                    "permissions": token_data["permissions"]
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me")
async def get_current_user(user: Dict = Depends(verify_token)):
    """Get current user information"""
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "roles": user["roles"],
        "permissions": user["permissions"]
    }

class MFASetupRequest(BaseModel):
    user_id: str

class MFAVerifyRequest(BaseModel):
    user_id: str
    token: str

@router.post("/setup-mfa")
async def setup_mfa(request: MFASetupRequest):
    """Setup MFA for user"""
    try:
        # Generate MFA secret
        secret = "JBSWY3DPEHPK3PXP"  # Mock secret for testing
        qr_code_url = f"otpauth://totp/DataIngestion:admin@example.com?secret={secret}&issuer=DataIngestion"
        
        return {
            "secret": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": ["123456", "789012", "345678", "901234", "567890"]
        }
    except Exception as e:
        logger.error("MFA setup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"MFA setup failed: {str(e)}")

@router.post("/verify-mfa")
async def verify_mfa(request: MFAVerifyRequest):
    """Verify MFA token"""
    try:
        # Mock MFA verification - accept any 6-digit token
        if len(request.token) == 6 and request.token.isdigit():
            return {"success": True, "message": "MFA verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid MFA token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("MFA verification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"MFA verification failed: {str(e)}")

@router.get("/test")
async def test_auth():
    """Test authentication endpoint"""
    return {"message": "Authentication service is working"}
