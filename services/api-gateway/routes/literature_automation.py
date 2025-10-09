"""
Literature Automation Routes
API endpoints for literature search, classification, and ICSR extraction
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog
import httpx

from auth.jwt_auth import get_current_user
from models.literature_models import (
    LiteratureSearchRequest, LiteratureSearchResponse,
    ArticleClassificationRequest, ArticleClassificationResponse,
    ICSRExtractionRequest, ICSRExtractionResponse
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/literature", tags=["Literature Automation"])

# Literature Automation Service URL
LITERATURE_SERVICE_URL = "http://literature-automation:8009"

@router.post("/search", response_model=LiteratureSearchResponse)
async def search_literature(
    request: LiteratureSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search literature from multiple sources (PubMed, Embase, Cochrane)"""
    try:
        logger.info("Literature search request", 
                   user_id=current_user["user_id"], 
                   query=request.query)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LITERATURE_SERVICE_URL}/api/v1/literature/search",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Literature search service error", error=str(e))
        raise HTTPException(status_code=502, detail="Literature search service unavailable")
    except Exception as e:
        logger.error("Literature search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Literature search failed: {str(e)}")

@router.post("/classify", response_model=ArticleClassificationResponse)
async def classify_article(
    request: ArticleClassificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Classify article for ICSR identification"""
    try:
        logger.info("Article classification request", 
                   user_id=current_user["user_id"], 
                   article_id=request.article_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LITERATURE_SERVICE_URL}/api/v1/literature/classify",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Article classification service error", error=str(e))
        raise HTTPException(status_code=502, detail="Article classification service unavailable")
    except Exception as e:
        logger.error("Article classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Article classification failed: {str(e)}")


@router.get("/sources")
async def get_literature_sources(current_user: dict = Depends(get_current_user)):
    """Get available literature sources"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LITERATURE_SERVICE_URL}/api/v1/literature/sources",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Literature sources service error", error=str(e))
        raise HTTPException(status_code=502, detail="Literature sources service unavailable")
    except Exception as e:
        logger.error("Get literature sources failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Get literature sources failed: {str(e)}")

@router.get("/health")
async def literature_service_health():
    """Check literature automation service health"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LITERATURE_SERVICE_URL}/health",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error("Literature service health check failed", error=str(e))
        return {"status": "unhealthy", "service": "literature-automation", "error": str(e)}
    except Exception as e:
        logger.error("Literature service health check error", error=str(e))
        return {"status": "unhealthy", "service": "literature-automation", "error": str(e)}
