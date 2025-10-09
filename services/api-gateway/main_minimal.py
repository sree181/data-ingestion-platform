"""
Minimal API Gateway for Testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog
import httpx
import uvicorn

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
    title="Data Ingestion API Gateway",
    description="API Gateway for Data Ingestion Platform",
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

# Service URLs
LITERATURE_SERVICE_URL = "http://literature-automation:8009"
ICSR_SERVICE_URL = "http://icsr-automation:8010"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/api/v1/literature/sources")
async def get_literature_sources():
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

@app.post("/api/v1/literature/search")
async def search_literature(request: dict):
    """Search literature from multiple sources"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LITERATURE_SERVICE_URL}/api/v1/literature/search",
                json=request,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("Literature search service error", error=str(e))
        raise HTTPException(status_code=502, detail="Literature search service unavailable")
    except Exception as e:
        logger.error("Literature search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Literature search failed: {str(e)}")

@app.post("/api/v1/literature/classify")
async def classify_article(request: dict):
    """Classify article using AI"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LITERATURE_SERVICE_URL}/api/v1/literature/classify",
                json=request,
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

@app.get("/api/v1/icsr/statistics")
async def get_icsr_statistics():
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

