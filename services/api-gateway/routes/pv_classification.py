"""
PV Classification Routes
Integration with PV Classification Service - NEW MODULE
Does not modify any existing functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import structlog
import httpx
from datetime import datetime
import asyncio

from auth.jwt_auth import get_current_user

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/pv-classification",
    tags=["PV Classification"]
)


# Models
class PVClassificationEntity(BaseModel):
    """Classification entity"""
    entity: str
    type: str
    confidence: float
    relevance: str


class PVClassificationResult(BaseModel):
    """Classification result"""
    classification: str
    confidence: float
    reasoning: str
    key_entities: List[PVClassificationEntity]
    regulatory_elements: Dict[str, bool]


class ICSRProjectIngestRequest(BaseModel):
    """Request to ingest documents into ICSR project"""
    domain: str = Field(default="hepatotoxicity", description="Domain: hepatotoxicity | cardiotoxicity | neurotoxicity")
    max_articles: int = Field(default=50, ge=1, le=200, description="Maximum articles to ingest")
    force_ensemble: bool = Field(default=False, description="Force all 3 models (Rule+BERT+LLM) to run for every document")


class ICSRProjectIngestResponse(BaseModel):
    """Response after ingestion"""
    success: bool
    project_id: str
    articles_ingested: int
    articles_classified: int
    processing_time_seconds: float
    classifications: Dict[str, int]


# Service URLs
PV_CLASSIFICATION_SERVICE = "http://pv-classification-service:8002"


@router.get("/health")
async def health_check():
    """Health check for PV classification integration"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PV_CLASSIFICATION_SERVICE}/health", timeout=5.0)
            classification_status = response.json() if response.status_code == 200 else {"status": "unhealthy"}
        
        return {
            "status": "healthy",
            "integration": "pv-classification",
            "classification_service": classification_status
        }
    except Exception as e:
        return {
            "status": "degraded",
            "integration": "pv-classification",
            "error": str(e)
        }


@router.post("/ingest-and-classify", response_model=ICSRProjectIngestResponse)
async def ingest_and_classify_for_icsr_project(
    request: ICSRProjectIngestRequest,
    user: dict = Depends(get_current_user)
):
    """
    Ingest PubMed articles for ICSR project and classify them
    
    This endpoint:
    1. Fetches targeted articles from PubMed (MeSH term filtered)
    2. Saves to Elasticsearch with project_id="icsr"
    3. Classifies each article using PV classification service
    4. Extracts and stores entities in Neo4j
    5. Returns classification summary
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(
            "Starting ICSR project ingestion",
            domain=request.domain,
            max_articles=request.max_articles,
            user_id=user["user_id"]
        )
        
        # Step 1: Fetch articles from PubMed using targeted ingestion
        from services.pv_classification_integration_service import PVClassificationIntegrationService
        
        integration_service = PVClassificationIntegrationService()
        
        result = await integration_service.ingest_and_classify(
            domain=request.domain,
            max_articles=request.max_articles,
            project_id="icsr",
            user_id=user["user_id"],
            force_ensemble=request.force_ensemble
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "ICSR project ingestion completed",
            articles_ingested=result["articles_ingested"],
            articles_classified=result["articles_classified"],
            processing_time=processing_time
        )
        
        return ICSRProjectIngestResponse(
            success=True,
            project_id="icsr",
            articles_ingested=result["articles_ingested"],
            articles_classified=result["articles_classified"],
            processing_time_seconds=processing_time,
            classifications=result["classifications"]
        )
        
    except Exception as e:
        logger.error("ICSR project ingestion failed", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/stats")
async def get_icsr_project_stats(user: dict = Depends(get_current_user)):
    """
    Get statistics for ICSR project classifications
    """
    try:
        from elasticsearch import AsyncElasticsearch
        
        es_client = AsyncElasticsearch(["http://elasticsearch:9200"])
        
        # Query Elasticsearch for ICSR project documents
        query = {
            "query": {
                "term": {"project_id.keyword": "icsr"}
            },
            "aggs": {
                "classifications": {
                    "terms": {
                        "field": "classification.keyword",
                        "size": 10
                    }
                },
                "confidence_stats": {
                    "stats": {
                        "field": "classification_confidence"
                    }
                }
            },
            "size": 0
        }
        
        result = await es_client.search(index="documents", body=query)
        await es_client.close()
        
        classifications = {}
        if "aggregations" in result and "classifications" in result["aggregations"]:
            for bucket in result["aggregations"]["classifications"]["buckets"]:
                classifications[bucket["key"]] = bucket["doc_count"]
        
        confidence_stats = result.get("aggregations", {}).get("confidence_stats", {})
        
        return {
            "success": True,
            "project_id": "icsr",
            "total_documents": result["hits"]["total"]["value"],
            "classifications": classifications,
            "average_confidence": confidence_stats.get("avg", 0),
            "min_confidence": confidence_stats.get("min", 0),
            "max_confidence": confidence_stats.get("max", 0)
        }
        
    except Exception as e:
        logger.error("Failed to get ICSR stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/domains")
async def get_available_domains():
    """
    Get list of available domains for targeted ingestion
    """
    return {
        "domains": [
            {
                "id": "hepatotoxicity",
                "name": "Drug-Induced Liver Injury (Hepatotoxicity)",
                "description": "Articles related to drug-induced liver damage and hepatotoxicity",
                "mesh_terms": [
                    "Chemical and Drug Induced Liver Injury",
                    "Hepatotoxicity",
                    "Acute Liver Failure drug-induced"
                ]
            },
            {
                "id": "cardiotoxicity",
                "name": "Cardiotoxicity",
                "description": "Articles related to drug-induced cardiac adverse events",
                "mesh_terms": [
                    "Cardiotoxicity",
                    "Drug-Induced Arrhythmia",
                    "QT Prolongation drug-induced"
                ]
            },
            {
                "id": "neurotoxicity",
                "name": "Neurotoxicity",
                "description": "Articles related to drug-induced neurological adverse events",
                "mesh_terms": [
                    "Neurotoxicity Syndromes",
                    "Drug-Induced Encephalopathy",
                    "Seizures drug-induced"
                ]
            }
        ]
    }

