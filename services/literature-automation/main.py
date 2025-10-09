"""
Literature Automation Service
Handles literature search, classification, and ICSR data extraction
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog
from typing import List, Dict, Any
import uvicorn

from models.literature_models import (
    LiteratureSearchRequest,
    LiteratureSearchResponse,
    ArticleClassificationRequest,
    ArticleClassificationResponse
)
from services.literature_search_service import LiteratureSearchService
from services.classification_service import ClassificationService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Literature Automation Service",
    description="AI-powered literature search, classification, and ICSR data extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
literature_search_service = LiteratureSearchService()
classification_service = ClassificationService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "literature-automation"}

@app.post("/api/v1/literature/search", response_model=LiteratureSearchResponse)
async def search_literature(request: LiteratureSearchRequest):
    """Search literature from multiple sources (PubMed, Embase, etc.)"""
    try:
        logger.info("Literature search request", query=request.query, sources=request.sources)
        
        results = await literature_search_service.search_literature(
            query=request.query,
            sources=request.sources,
            max_results=request.max_results,
            date_range=request.date_range
        )
        
        logger.info("Literature search completed", results_count=len(results))
        return LiteratureSearchResponse(
            success=True,
            results=results,
            total_count=len(results)
        )
        
    except Exception as e:
        logger.error("Literature search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Literature search failed: {str(e)}")

@app.post("/api/v1/literature/classify", response_model=ArticleClassificationResponse)
async def classify_article(request: ArticleClassificationRequest):
    """Classify article using AI (ICSR, Non-ICSR, Safety Information, Rejected)"""
    try:
        logger.info("Article classification request", article_id=request.article_id)
        
        classification = await classification_service.classify_article(
            title=request.title,
            abstract=request.abstract,
            content=request.content
        )
        
        logger.info("Article classification completed", 
                   article_id=request.article_id, 
                   classification=classification.category)
        
        return ArticleClassificationResponse(
            success=True,
            classification=classification.category,
            confidence=classification.confidence,
            reasoning=classification.reasoning
        )
        
    except Exception as e:
        logger.error("Article classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Article classification failed: {str(e)}")


@app.get("/api/v1/literature/sources")
async def get_available_sources():
    """Get list of available literature sources"""
    return {
        "sources": [
            {"id": "pubmed", "name": "PubMed", "description": "NCBI PubMed database"},
            {"id": "embase", "name": "Embase", "description": "Elsevier Embase database"},
            {"id": "cochrane", "name": "Cochrane Library", "description": "Cochrane systematic reviews"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
