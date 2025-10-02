"""
Test Authentication Endpoint
Simple test to debug JWT authentication issues
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/login")
async def test_login():
    """Simple test login endpoint"""
    try:
        return {
            "message": "Test login successful",
            "status": "working"
        }
    except Exception as e:
        logger.error("Test login failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test login failed: {str(e)}")

@router.get("/health")
async def test_health():
    """Test health endpoint"""
    return {"status": "healthy", "service": "test-auth"}
