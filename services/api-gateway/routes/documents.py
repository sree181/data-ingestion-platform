"""
Documents API endpoint for listing and retrieving documents from Elasticsearch
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, Dict, Any, List
import structlog
from elasticsearch import AsyncElasticsearch
import os

from auth.jwt_auth import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/docs-list", tags=["Documents"])

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")


@router.get("/search")
async def search_documents(
    q: Optional[str] = Query(default="*", description="Search query (* for all)"),
    page: int = Query(default=0, ge=0, description="Page number (0-based)"),
    size: int = Query(default=25, ge=1, le=100, description="Results per page"),
    classification: Optional[str] = Query(default=None, description="Filter by classification"),
    source: Optional[str] = Query(default=None, description="Filter by source")
    # Temporarily removed authentication for testing: current_user: dict = Depends(get_current_user)
):
    """
    Search and list documents from Elasticsearch with pagination and filters
    
    Args:
        q: Search query (use * for all documents)
        page: Page number (0-based)
        size: Results per page
        classification: Filter by PV classification (ICSR, Non-ICSR, etc.)
        source: Filter by document source (pubmed, pdf, etc.)
    
    Returns:
        Paginated list of documents with metadata
    """
    es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
    try:
        logger.info(f"Searching documents with query: {q}, page: {page}, size: {size}")
        
        # Build query
        query = {"match_all": {}}
        filters = []
        
        # Add search query if not wildcard
        if q and q != "*":
            query = {
                "multi_match": {
                    "query": q,
                    "fields": ["title^3", "abstract^2", "content", "authors.name"],
                    "type": "best_fields"
                }
            }
        
        # Add filters
        if classification:
            filters.append({"term": {"classification.keyword": classification}})
        if source:
            filters.append({"term": {"source.keyword": source}})
        
        # Construct final query
        if filters:
            es_query = {
                "bool": {
                    "must": [query] if q and q != "*" else [],
                    "filter": filters
                }
            }
            if q == "*" or not q:
                es_query["bool"]["must"].append({"match_all": {}})
        else:
            es_query = query
        
        # Execute search
        search_body = {
            "query": es_query,
            "from": page * size,
            "size": size,
            "sort": [{"created_at": {"order": "desc"}}]
        }
        logger.info(f"Executing Elasticsearch search with body: {search_body}")
        
        response = await es_client.search(
            index="documents",
            body=search_body
        )
        
        logger.info(f"Elasticsearch response: {response.body}")
        
        # Extract results and transform for frontend
        hits = response.body["hits"]
        total = hits["total"]["value"] if isinstance(hits["total"], dict) else hits["total"]
        results = []
        
        for hit in hits["hits"]:
            source = hit["_source"]
            
            # Transform ICSR classification data for frontend compatibility
            if source.get("icsr_classification"):
                icsr_data = source["icsr_classification"]
                source["classification"] = icsr_data.get("classification")
                source["classification_confidence"] = icsr_data.get("confidence")
                source["classification_entities"] = icsr_data.get("key_entities", [])
                source["classification_reasoning"] = icsr_data.get("reasoning")
                source["classification_cost"] = icsr_data.get("cost", 0)
            
            results.append({
                "_id": hit["_id"],
                "_source": source
            })
        
        logger.info(
            "Documents search completed",
            query=q,
            page=page,
            size=size,
            total=total,
            returned=len(results),
            classification_filter=classification
        )
        
        return {
            "total": total,
            "results": results,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
        
    except Exception as e:
        logger.error("Documents search failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        await es_client.close()


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single document by ID from Elasticsearch
    """
    es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
    try:
        response = await es_client.get(index="documents", id=document_id)
        
        return {
            "_id": response.body["_id"],
            "_source": response.body["_source"]
        }
    except Exception as e:
        logger.error("Get document failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    finally:
        await es_client.close()

