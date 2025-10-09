"""
ICSR Automation Routes
API endpoints for email processing, ICSR validation, and XML generation
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog
import httpx

from auth.jwt_auth import get_current_user
from models.simple_icsr_models import (
    EmailProcessingRequest, EmailProcessingResponse,
    ICSRValidationRequest, ICSRValidationResponse,
    XMLGenerationRequest, XMLGenerationResponse,
    ICSRExtractionRequest, ICSRExtractionResponse
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/icsr", tags=["ICSR Automation"])

# ICSR Automation Service URL
ICSR_SERVICE_URL = "http://icsr-automation:8010"

@router.post("/process-email", response_model=EmailProcessingResponse)
async def process_email(
    request: EmailProcessingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process safety email for ICSR classification and data extraction"""
    try:
        logger.info("Email processing request", 
                   user_id=current_user["user_id"], 
                   email_id=request.email_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/process-email",
                json=request.dict(),
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Email processing service error", error=str(e))
        raise HTTPException(status_code=502, detail="Email processing service unavailable")
    except Exception as e:
        logger.error("Email processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Email processing failed: {str(e)}")

@router.post("/validate", response_model=ICSRValidationResponse)
async def validate_icsr(
    request: ICSRValidationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate ICSR data against business rules and regulatory requirements"""
    try:
        logger.info("ICSR validation request", 
                   user_id=current_user["user_id"], 
                   icsr_id=request.icsr_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/validate",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("ICSR validation service error", error=str(e))
        raise HTTPException(status_code=502, detail="ICSR validation service unavailable")
    except Exception as e:
        logger.error("ICSR validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ICSR validation failed: {str(e)}")

@router.post("/generate-xml", response_model=XMLGenerationResponse)
async def generate_xml(
    request: XMLGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate ICH E2B R3 XML file from ICSR data"""
    try:
        logger.info("XML generation request", 
                   user_id=current_user["user_id"], 
                   icsr_id=request.icsr_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/generate-xml",
                json=request.dict(),
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("XML generation service error", error=str(e))
        raise HTTPException(status_code=502, detail="XML generation service unavailable")
    except Exception as e:
        logger.error("XML generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"XML generation failed: {str(e)}")

@router.get("/validation-rules")
async def get_validation_rules(current_user: dict = Depends(get_current_user)):
    """Get available ICSR validation rules"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/validation-rules",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Validation rules service error", error=str(e))
        raise HTTPException(status_code=502, detail="Validation rules service unavailable")
    except Exception as e:
        logger.error("Get validation rules failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Get validation rules failed: {str(e)}")

@router.get("/templates")
async def get_icsr_templates(current_user: dict = Depends(get_current_user)):
    """Get available ICSR templates and formats"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/templates",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("ICSR templates service error", error=str(e))
        raise HTTPException(status_code=502, detail="ICSR templates service unavailable")
    except Exception as e:
        logger.error("Get ICSR templates failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Get ICSR templates failed: {str(e)}")

@router.post("/extract", response_model=ICSRExtractionResponse)
async def extract_icsr_data(
    request: ICSRExtractionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extract structured ICSR data from literature article"""
    try:
        logger.info("ICSR extraction request", 
                   user_id=current_user["user_id"], 
                   article_id=request.article_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/extract",
                json=request.dict(),
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("ICSR extraction service error", error=str(e))
        raise HTTPException(status_code=502, detail="ICSR extraction service unavailable")
    except Exception as e:
        logger.error("ICSR extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ICSR extraction failed: {str(e)}")

@router.get("/statistics")
async def get_icsr_statistics(current_user: dict = Depends(get_current_user)):
    """Get ICSR processing statistics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ICSR_SERVICE_URL}/api/v1/icsr/statistics",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("ICSR statistics service error", error=str(e))
        raise HTTPException(status_code=502, detail="ICSR statistics service unavailable")
    except Exception as e:
        logger.error("Get ICSR statistics failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Get ICSR statistics failed: {str(e)}")

@router.get("/health")
async def icsr_service_health():
    """Check ICSR automation service health"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ICSR_SERVICE_URL}/health",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("ICSR service health check failed", error=str(e))
        return {"status": "unhealthy", "service": "icsr-automation", "error": str(e)}
    except Exception as e:
        logger.error("ICSR service health check error", error=str(e))
        return {"status": "unhealthy", "service": "icsr-automation", "error": str(e)}
