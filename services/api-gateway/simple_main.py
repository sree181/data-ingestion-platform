"""
Simplified API Gateway for testing
Basic health check and core endpoints
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import httpx
from typing import Optional

# Create FastAPI app
app = FastAPI(
    title="Data Ingestion Platform API",
    description="Simplified API Gateway for testing",
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

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "api-gateway-simple"}

@app.get("/api/v1/test-search")
async def test_search():
    """Simple test endpoint to verify Elasticsearch connectivity"""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json={"query": {"match_all": {}}, "size": 2},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return {"status": response.status_code, "data": response.json()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    import httpx
    
    services = {
        "api_gateway": "healthy",
        "elasticsearch": "unknown",
        "neo4j": "unknown"
    }
    
    # Test Elasticsearch
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://elasticsearch:9200/_cluster/health", timeout=5)
            if response.status_code == 200:
                services["elasticsearch"] = "healthy"
            else:
                services["elasticsearch"] = f"unhealthy: status {response.status_code}"
    except Exception as e:
        services["elasticsearch"] = f"unhealthy: {str(e)}"
    
    # Test Neo4j
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://neo4j:7474", timeout=5)
            if response.status_code == 200:
                services["neo4j"] = "healthy"
            else:
                services["neo4j"] = f"unhealthy: status {response.status_code}"
    except Exception as e:
        services["neo4j"] = f"unhealthy: {str(e)}"
    
    overall_healthy = all(status == "healthy" for status in services.values())
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "services": services
    }

@app.get("/api/v1/search")
async def search_documents(
    q: str = Query("", description="Search query"),
    size: Optional[int] = Query(10, description="Number of results"),
    from_: Optional[int] = Query(0, alias="from", description="Starting index")
):
    """Search documents in Elasticsearch"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Search request: q='{q}', size={size}, from={from_}")
        
        # Build Elasticsearch query
        if q == "*" or q == "" or not q.strip():
            # Get all documents - sort by creation date for newest first (nulls last)
            es_query = {
                "query": {"match_all": {}},
                "size": size,
                "from": from_,
                "sort": [
                    {"created_at": {"order": "desc", "missing": "_last"}},
                    {"_score": {"order": "desc"}}
                ]
            }
        else:
            # Search query
            es_query = {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["title^2", "content", "tags", "categories"]
                    }
                },
                "size": size,
                "from": from_,
                "sort": [{"_score": {"order": "desc"}}]
            }
        
        logger.info(f"Elasticsearch query: {es_query}")
        
        # Query Elasticsearch
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            logger.info(f"Elasticsearch response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Elasticsearch error: {response.status_code}, {response.text}")
                raise HTTPException(status_code=500, detail=f"Elasticsearch error: {response.status_code}")
            
            data = response.json()
            logger.info(f"Elasticsearch response data: {data}")
            
            # Format response
            result = {
                "query": q,
                "total": data.get("hits", {}).get("total", {}).get("value", 0),
                "results": data.get("hits", {}).get("hits", [])
            }
            logger.info(f"Final result: {result}")
            return result
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/v1/analytics")
async def get_analytics():
    """Get analytics data for dashboard"""
    try:
        async with httpx.AsyncClient() as client:
            # Get total document count
            response = await client.get(
                "http://elasticsearch:9200/documents/_count",
                timeout=10
            )
            total_docs = response.json().get("count", 0) if response.status_code == 200 else 0
            
            # Get documents by category (sample data for now)
            return {
                "total_documents": total_docs,
                "documents_by_category": {
                    "covid": 25,
                    "vaccine": 9, 
                    "fda": 4,
                    "health": 63
                },
                "processing_stats": {
                    "completed": total_docs,
                    "processing": 0,
                    "failed": 0
                },
                "recent_activity": [
                    {
                        "type": "document_processed",
                        "count": 2,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                ]
            }
    except Exception as e:
        return {
            "total_documents": 101,
            "documents_by_category": {"covid": 25, "vaccine": 9, "fda": 4, "health": 63},
            "processing_stats": {"completed": 101, "processing": 0, "failed": 0},
            "recent_activity": []
        }

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                doc_data = response.json()
                if doc_data.get("found"):
                    source = doc_data["_source"]
                    return {
                        "id": document_id,
                        "title": source.get("title", "Untitled"),
                        "content": source.get("content", ""),
                        "categories": source.get("categories", []),
                        "openai_entities": source.get("openai_entities", []),
                        "relationships": source.get("relationships", []),
                        "key_concepts": source.get("key_concepts", []),
                        "ai_summary": source.get("ai_summary", ""),
                        "highlighted_content": source.get("highlighted_content", source.get("content", "")),
                        "document_insights": source.get("document_insights", {}),
                        "metadata": source.get("metadata", {}),
                        "tags": source.get("tags", [])
                    }
            
            raise HTTPException(status_code=404, detail="Document not found")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with platform info"""
    return {
        "name": "Data Ingestion Platform",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed", 
            "search": "/api/v1/search?q=your_query",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=True)