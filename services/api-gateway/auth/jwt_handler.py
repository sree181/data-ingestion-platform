"""
JWT token handling for authentication
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt
import structlog

logger = structlog.get_logger(__name__)


class JWTHandler:
    """Handle JWT token creation and verification"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(
        self, 
        user_data: Dict[str, Any], 
        expires_minutes: int = 30
    ) -> str:
        """Create a JWT token"""
        try:
            # Calculate expiration
            expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
            
            # Create payload
            payload = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "role": user_data.get("role", "user"),
                "permissions": user_data.get("permissions", []),
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access_token"
            }
            
            # Create token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.debug("JWT token created", user_id=user_data.get("user_id"))
            return token
            
        except Exception as e:
            logger.error("Failed to create JWT token", error=str(e))
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Check if token is not expired
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise jwt.ExpiredSignatureError("Token has expired")
            
            logger.debug("JWT token verified", user_id=payload.get("user_id"))
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise Exception("Token has expired")
        except jwt.JWTError as e:
            logger.warning("Invalid JWT token", error=str(e))
            raise Exception("Invalid token")
        except Exception as e:
            logger.error("JWT verification failed", error=str(e))
            raise
    
    def refresh_token(self, token: str, expires_minutes: int = 30) -> str:
        """Refresh an existing token"""
        try:
            # Decode current token (this will raise exception if invalid)
            payload = self.verify_token(token)
            
            # Create new token with same user data
            user_data = {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload["role"],
                "permissions": payload["permissions"]
            }
            
            return self.create_token(user_data, expires_minutes)
            
        except Exception as e:
            logger.error("Failed to refresh token", error=str(e))
            raise