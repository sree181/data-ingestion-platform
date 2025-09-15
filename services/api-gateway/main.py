from fastapi import FastAPI, Query, HTTPException, Depends, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, List
import httpx
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
import uvicorn

# Project spaces will be defined inline

# Pydantic Models for Investigation Features
class InvestigationCreate(BaseModel):
    title: str = Field(..., description="Investigation title")
    description: str = Field(..., description="Investigation description") 
    created_by: str = Field(default="user1", description="User ID who created the investigation")
    tags: List[str] = Field(default=[], description="Investigation tags")
    priority: str = Field(default="medium", description="Priority level")

# Project Spaces Models
class ProjectSpaceCreate(BaseModel):
    name: str = Field(..., description="Project space name")
    description: Optional[str] = Field(None, description="Project space description")
    color: str = Field("#1976d2", description="Hex color code")
    icon: str = Field("folder", description="Icon name")

class ProjectSpace(BaseModel):
    id: str = Field(..., description="Project space ID")
    name: str = Field(..., description="Project space name")
    description: Optional[str] = Field(None, description="Project space description")
    color: str = Field(..., description="Hex color code")
    icon: str = Field(..., description="Icon name")
    document_count: int = Field(0, description="Number of documents")
    member_count: int = Field(1, description="Number of members")
    user_role: str = Field("owner", description="User's role in this space")
    created_at: str = Field(..., description="Creation timestamp")

# Mock data for project spaces
mock_spaces = [
    {
        "id": "1",
        "name": "General",
        "description": "Default project space for general documents",
        "color": "#1976d2",
        "icon": "folder",
        "document_count": 12,
        "member_count": 1,
        "user_role": "owner",
        "created_at": "2024-01-10T09:00:00Z"
    },
    {
        "id": "2", 
        "name": "Contracts",
        "description": "Legal contracts and agreements",
        "color": "#4caf50",
        "icon": "gavel",
        "document_count": 5,
        "member_count": 3,
        "user_role": "owner",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "3",
        "name": "Research",
        "description": "Research documents and papers", 
        "color": "#ff9800",
        "icon": "science",
        "document_count": 8,
        "member_count": 2,
        "user_role": "admin",
        "created_at": "2024-01-20T14:30:00Z"
    }
]

app = FastAPI(
    title="Data Ingestion API Gateway", 
    description="Production-ready API Gateway",
    version="1.0.0"
)

# Custom middleware to handle large file uploads
from fastapi import Request
from fastapi.responses import Response as FastAPIResponse
import asyncio

@app.middleware("http")
async def large_file_upload_middleware(request: Request, call_next):
    """Middleware to handle large file uploads"""
    if request.url.path == "/api/v1/upload":
        # Set a larger timeout for uploads
        request.state.upload_timeout = 300  # 5 minutes
    response = await call_next(request)
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip middleware for compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Project spaces functionality will be added inline below

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "api-gateway-working"}

@app.get("/api/v1/documents/{document_id}/images")
async def get_document_images(document_id: str):
    """Get all images for a specific document"""
    try:
        async with httpx.AsyncClient() as client:
            # Get document with images
            response = await client.get(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to retrieve document")
            
            doc = response.json()["_source"]
            stored_images = doc.get("stored_images", [])
            image_metadata = doc.get("image_metadata", [])
            
            # Combine image data with metadata
            enhanced_images = []
            for img in stored_images:
                # Find matching metadata
                matching_metadata = next(
                    (meta for meta in image_metadata if meta.get("image_id") == img.get("image_id")),
                    {}
                )
                
                enhanced_images.append({
                    **img,
                    **matching_metadata,
                    "document_id": document_id,
                    "access_url": f"/api/v1/documents/{document_id}/images/{img.get('image_id')}/data"
                })
            
            return {
                "document_id": document_id,
                "image_count": len(enhanced_images),
                "images": enhanced_images
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document images: {str(e)}")

@app.get("/api/v1/images/search")
async def search_images(
    q: str = Query("", description="Search query for images"),
    image_type: Optional[str] = Query(None, description="Filter by image type"),
    entity_type: Optional[str] = Query(None, description="Filter by entities in images"),
    confidence_threshold: Optional[float] = Query(0.5, description="Minimum confidence threshold"),
    size: Optional[int] = Query(20, description="Number of results"),
    from_: Optional[int] = Query(0, alias="from", description="Starting index")
):
    """Search for images across all documents"""
    try:
        async with httpx.AsyncClient() as client:
            # Build query for documents with images
            must_clauses = [
                {"exists": {"field": "stored_images"}}
            ]
            
            # Add text search if provided
            if q and q.strip():
                must_clauses.append({
                    "multi_match": {
                        "query": q,
                        "fields": ["title^2", "content", "image_metadata.analysis", "image_metadata.text_content"]
                    }
                })
            
            # Add image type filter
            if image_type:
                must_clauses.append({
                    "term": {"image_metadata.image_type.keyword": image_type}
                })
            
            # Add entity type filter for image entities
            if entity_type:
                must_clauses.append({
                    "term": {"image_entities.type.keyword": entity_type}
                })
            
            es_query = {
                "query": {"bool": {"must": must_clauses}},
                "size": size,
                "from": from_,
                "_source": ["title", "stored_images", "image_metadata", "image_entities"]
            }
            
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Elasticsearch search failed")
            
            data = response.json()
            results = []
            
            for hit in data.get("hits", {}).get("hits", []):
                doc = hit["_source"]
                doc_id = hit["_id"]
                
                # Extract images from document
                for img in doc.get("stored_images", []):
                    # Find matching metadata
                    matching_metadata = next(
                        (meta for meta in doc.get("image_metadata", []) 
                         if meta.get("image_id") == img.get("image_id")),
                        {}
                    )
                    
                    # Find matching entities
                    matching_entities = [
                        entity for entity in doc.get("image_entities", [])
                        if entity.get("image_id") == img.get("image_id") or 
                           entity.get("page_number") == img.get("page_number")
                    ]
                    
                    # Filter by confidence if specified
                    if confidence_threshold:
                        matching_entities = [
                            e for e in matching_entities 
                            if e.get("confidence", 0) >= confidence_threshold
                        ]
                    
                    results.append({
                        **img,
                        **matching_metadata,
                        "document_id": doc_id,
                        "document_title": doc.get("title", "Untitled"),
                        "entities": matching_entities,
                        "access_url": f"/api/v1/documents/{doc_id}/images/{img.get('image_id')}/data"
                    })
            
            return {
                "total": len(results),
                "query": q,
                "filters": {
                    "image_type": image_type,
                    "entity_type": entity_type,
                    "confidence_threshold": confidence_threshold
                },
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@app.get("/api/v1/search")
async def search_documents(
    q: str = Query("", description="Search query"),
    size: Optional[int] = Query(10, description="Number of results"),
    from_: Optional[int] = Query(0, alias="from", description="Starting index")
):
    """Search documents in Elasticsearch"""
    try:
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
                        "fields": ["title", "content"]
                    }
                },
                "size": size,
                "from": from_
            }
        
        # Query Elasticsearch
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code != 200:
                return {"error": f"Elasticsearch error: {response.status_code}"}
            
            data = response.json()
            
            # Format response
            return {
                "query": q,
                "total": data.get("hits", {}).get("total", {}).get("value", 0),
                "results": data.get("hits", {}).get("hits", [])
            }
            
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}

@app.get("/api/v1/analytics")
async def get_analytics():
    """Get comprehensive analytics data for dashboard"""
    try:
        async with httpx.AsyncClient() as client:
            # Get total document count
            count_response = await client.get(
                "http://elasticsearch:9200/documents/_count",
                timeout=10
            )
            
            if count_response.status_code == 200:
                count_data = count_response.json()
                total_docs = count_data.get("count", 0)
            else:
                total_docs = 0
            
            # Get documents with categories aggregation
            agg_query = {
                "size": 0,
                "aggs": {
                    "by_categories": {
                        "terms": {
                            "field": "categories.keyword",
                            "size": 20,
                            "missing": "Uncategorized"
                        }
                    },
                    "by_file_type": {
                        "terms": {
                            "field": "file_type.keyword", 
                            "size": 10,
                            "missing": "Unknown"
                        }
                    },
                    "by_extraction_method": {
                        "terms": {
                            "field": "extraction_method.keyword",
                            "size": 10,
                            "missing": "Basic"
                        }
                    },
                    "recent_documents": {
                        "date_histogram": {
                            "field": "created_at",
                            "calendar_interval": "day",
                            "order": {"_key": "desc"},
                            "min_doc_count": 0
                        }
                    },
                    "avg_file_size": {
                        "avg": {
                            "field": "metadata.file_size"
                        }
                    },
                    "entities_count": {
                        "sum": {
                            "script": {
                                "source": "if (params._source.openai_entities != null) { return params._source.openai_entities.size(); } return 0;"
                            }
                        }
                    }
                }
            }
            
            agg_response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=agg_query,
                timeout=10
            )
            
            agg_data = {}
            if agg_response.status_code == 200:
                agg_data = agg_response.json().get("aggregations", {})
            
            # Process category data
            category_buckets = agg_data.get("by_categories", {}).get("buckets", [])
            categories_data = {}
            for bucket in category_buckets:
                category = bucket["key"] if bucket["key"] != "Uncategorized" else "Other"
                categories_data[category] = bucket["doc_count"]
            
            # Process file type data  
            file_type_buckets = agg_data.get("by_file_type", {}).get("buckets", [])
            file_types_data = {}
            for bucket in file_type_buckets:
                file_types_data[bucket["key"]] = bucket["doc_count"]
            
            # Process extraction method data
            extraction_buckets = agg_data.get("by_extraction_method", {}).get("buckets", [])
            extraction_data = {}
            for bucket in extraction_buckets:
                extraction_data[bucket["key"]] = bucket["doc_count"]
                
            # Process timeline data
            timeline_buckets = agg_data.get("recent_documents", {}).get("buckets", [])
            timeline_data = []
            for bucket in timeline_buckets[:7]:  # Last 7 days
                timeline_data.append({
                    "date": bucket["key_as_string"][:10],  # YYYY-MM-DD
                    "count": bucket["doc_count"]
                })
            
            # Calculate AI processing statistics
            ai_processed = extraction_data.get("llamaparse_multimodal", 0) + \
                          extraction_data.get("llava_multimodal", 0) + \
                          extraction_data.get("official_llava_multimodal", 0)
            
            ai_processed_percentage = round((ai_processed / total_docs * 100) if total_docs > 0 else 0, 1)
            
            # Calculate insights
            avg_file_size = agg_data.get("avg_file_size", {}).get("value", 0) or 0
            total_entities = agg_data.get("entities_count", {}).get("value", 0) or 0
            
            return {
                "total_documents": total_docs,
                "documents_by_category": categories_data,
                "documents_by_file_type": file_types_data,
                "extraction_methods": extraction_data,
                "timeline_data": timeline_data,
                "processing_stats": {
                    "completed": total_docs,
                    "ai_processed": ai_processed,
                    "ai_processed_percentage": ai_processed_percentage,
                    "basic_processed": total_docs - ai_processed,
                    "processing": 0,
                    "failed": 0
                },
                "insights": {
                    "avg_file_size_mb": round(avg_file_size / (1024 * 1024), 2) if avg_file_size else 0,
                    "total_entities_extracted": int(total_entities),
                    "avg_entities_per_doc": round(total_entities / total_docs, 1) if total_docs > 0 else 0,
                    "most_common_category": max(categories_data.items(), key=lambda x: x[1])[0] if categories_data else "None",
                    "documents_uploaded_today": timeline_data[0]["count"] if timeline_data else 0
                },
                "recent_activity": [
                    {
                        "type": "documents_processed", 
                        "count": ai_processed,
                        "timestamp": "2025-08-06T12:00:00Z",
                        "description": f"{ai_processed} documents processed with AI"
                    },
                    {
                        "type": "total_indexed",
                        "count": total_docs, 
                        "timestamp": "2025-08-06T12:00:00Z",
                        "description": f"{total_docs} total documents indexed"
                    }
                ]
            }
            
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        return {
            "total_documents": 0,
            "documents_by_category": {},
            "documents_by_file_type": {},
            "extraction_methods": {},
            "timeline_data": [],
            "processing_stats": {"completed": 0, "ai_processed": 0, "ai_processed_percentage": 0, "basic_processed": 0, "processing": 0, "failed": 0},
            "insights": {"avg_file_size_mb": 0, "total_entities_extracted": 0, "avg_entities_per_doc": 0, "most_common_category": "None", "documents_uploaded_today": 0},
            "recent_activity": [],
            "error": f"Analytics error: {str(e)}"
        }

@app.post("/api/v1/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    space_id: Optional[str] = Form(None)
):
    """Upload documents for processing"""
    try:
        results = []
        for uploaded_file in files:
            # Read the file content
            file_content = await uploaded_file.read()
            
            # Send each file to document processor with space_id
            async with httpx.AsyncClient() as client:
                files_data = {"file": (uploaded_file.filename, file_content, uploaded_file.content_type)}
                data = {}
                if space_id:
                    data["space_id"] = space_id
                
                response = await client.post(
                    "http://document-processor:8001/process-file",
                    files=files_data,
                    data=data,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "filename": uploaded_file.filename,
                        "status": "success",
                        "message": "Document uploaded and processing started",
                        "document_id": result.get("document_id"),
                        "space_id": space_id,
                        "processing_result": result
                    })
                else:
                    results.append({
                        "filename": uploaded_file.filename, 
                        "status": "error",
                        "message": f"Processing failed: {response.text}"
                    })
        
        return {"results": results, "total_uploaded": len(results), "space_id": space_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Elasticsearch error: {response.status_code}")
            
            data = response.json()
            return data.get("_source", {})
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document: {str(e)}")

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the system"""
    try:
        async with httpx.AsyncClient() as client:
            # Delete from Elasticsearch
            response = await client.delete(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code not in [200, 404]:
                raise HTTPException(status_code=500, detail=f"Elasticsearch error: {response.status_code}")
            
            return {"message": "Document deleted successfully", "document_id": document_id}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.put("/api/v1/documents/{document_id}")
async def update_document(document_id: str, update_data: dict):
    """Update document metadata"""
    try:
        async with httpx.AsyncClient() as client:
            # First check if document exists
            response = await client.get(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Elasticsearch error: {response.status_code}")
            
            # Update document
            update_response = await client.post(
                f"http://elasticsearch:9200/documents/_update/{document_id}",
                json={"doc": update_data},
                timeout=10
            )
            
            if update_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to update document")
            
            return {"message": "Document updated successfully", "document_id": document_id}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@app.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: str):
    """Download original document file"""
    try:
        async with httpx.AsyncClient() as client:
            # Get document metadata
            response = await client.get(
                f"http://elasticsearch:9200/documents/_doc/{document_id}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to retrieve document")
            
            doc = response.json()["_source"]
            filename = doc.get("title", f"document_{document_id}")
            content = doc.get("content", "")
            
            # For now, return the extracted content as a text file
            # In a production system, you'd retrieve the original file from MinIO
            return Response(
                content=content,
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}.txt"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

@app.get("/api/v1/knowledge-graph")
async def get_knowledge_graph():
    """Get knowledge graph data from Neo4j Aura and Elasticsearch"""
    try:
        # First, try to get data from Neo4j Aura
        try:
            neo4j_data = await get_neo4j_graph_data()
            if neo4j_data and neo4j_data.get("nodes"):
                return neo4j_data
        except Exception as e:
            print(f"Neo4j Aura connection failed, falling back to Elasticsearch: {e}")
        
        # Fallback: Query Elasticsearch for AI-processed documents with entities
        query = {
            "query": {"exists": {"field": "openai_entities"}},
            "size": 50,
            "_source": ["title", "openai_entities"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code != 200:
                return {"nodes": [], "links": [], "error": f"Elasticsearch error: {response.status_code}"}
            
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            
            # Build knowledge graph data
            nodes = {}
            links = []
            
            for hit in hits:
                doc = hit["_source"]
                doc_id = hit["_id"]
                doc_title = doc.get("title", "Untitled")[:50]
                
                # Add document as a node with original data preserved
                nodes[doc_id] = {
                    "id": doc_id,
                    "label": doc_title,
                    "type": "DOCUMENT",
                    "size": 10,
                    "color": "#4CAF50",
                    "originalDoc": doc,
                    "openai_entities": doc.get("openai_entities", [])
                }
                
                # Add entities as nodes
                for entity in doc.get("openai_entities", []):
                    entity_id = f"entity_{entity['text'].replace(' ', '_')}"
                    if entity_id not in nodes:
                        nodes[entity_id] = {
                            "id": entity_id,
                            "label": entity["text"],
                            "type": entity["type"],
                            "size": 6,
                            "color": get_entity_color(entity["type"]),
                            "confidence": entity.get("confidence", 0)
                        }
                    
                    # Link document to entity
                    links.append({
                        "source": doc_id,
                        "target": entity_id,
                        "relationship": "CONTAINS",
                        "weight": entity.get("confidence", 0.5)
                    })
                
                # Create entity-to-entity links for entities in the same document
                doc_entities = [f"entity_{entity['text'].replace(' ', '_')}" for entity in doc.get("openai_entities", [])]
                for i, entity1 in enumerate(doc_entities):
                    for entity2 in doc_entities[i+1:]:
                        links.append({
                            "source": entity1,
                            "target": entity2,
                            "relationship": "CO_OCCURS",
                            "weight": 0.7
                        })
            
            return {
                "nodes": list(nodes.values()),
                "links": links,
                "stats": {
                    "total_documents": len([n for n in nodes.values() if n["type"] == "DOCUMENT"]),
                    "total_entities": len([n for n in nodes.values() if n["type"] != "DOCUMENT"]),
                    "total_relationships": len(links)
                }
            }
            
    except Exception as e:
        return {"nodes": [], "links": [], "error": f"Knowledge graph error: {str(e)}"}
    
async def get_neo4j_graph_data():
    """Get knowledge graph data from Neo4j Aura"""
    import json
    
    # Neo4j Aura connection details
    neo4j_uri = "neo4j+s://a857a30a.databases.neo4j.io"
    neo4j_user = "neo4j"
    neo4j_password = "tWgpQzsTzGupIo5DGmos_AecmkgJYhSnL4gW_Z2012E"
    
    # Try to connect to Neo4j Aura and get graph data
    try:
        # For now, return empty data as we need to install neo4j driver
        # This will be populated once relationships are stored in Neo4j
        return {
            "nodes": [],
            "links": [],
            "stats": {
                "total_documents": 0,
                "total_entities": 0,
                "total_relationships": 0
            },
            "source": "neo4j_aura_placeholder"
        }
    except Exception as e:
        print(f"Neo4j Aura connection error: {e}")
        return None

def get_entity_color(entity_type):
        """Get color for entity type"""
        colors = {
            "ORGANIZATION": "#2196F3",
            "PERSON": "#9C27B0",
            "EVENT": "#F44336",
            "DATE": "#795548",
            "CONCEPT": "#607D8B",
            "REGULATION": "#FF5722",
            "DRUG": "#8BC34A",
            "LOCATION": "#FFC107"
        }
        return colors.get(entity_type, "#9E9E9E")

# Palantir-style Investigation Functions (Inline)
async def create_simple_investigation(title: str, description: str, created_by: str = "user1"):
    """Create a simple investigation case"""
    case_id = str(uuid.uuid4())
    
    investigation_data = {
        "case_id": case_id,
        "title": title,
        "description": description,
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "tags": ["investigation"],
        "priority": "medium",
        "statistics": {
            "total_entities": 0,
            "total_relationships": 0,
            "total_documents": 0
        }
    }
    
    # Store in Elasticsearch
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"http://elasticsearch:9200/investigations/_doc/{case_id}",
                json=investigation_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return {"case_id": case_id, "status": "created", "data": investigation_data}
            else:
                return {"error": f"Failed to create investigation: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to create investigation: {str(e)}"}

async def list_simple_investigations():
    """List investigations"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://elasticsearch:9200/investigations/_search",
                json={"query": {"match_all": {}}, "sort": [{"created_at": {"order": "desc"}}], "size": 100},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                investigations = [
                    {**hit["_source"], "id": hit["_id"]} 
                    for hit in data.get("hits", {}).get("hits", [])
                ]
                return {"investigations": investigations, "total": len(investigations)}
            else:
                return {"investigations": [], "total": 0, "error": f"Search failed: {response.status_code}"}
        except Exception as e:
            return {"investigations": [], "total": 0, "error": f"Search failed: {str(e)}"}

async def explore_entity_simple(entity_id: str, depth: int = 2, confidence_threshold: float = 0.5):
    """Simple entity exploration - Palantir Gotham style"""
    try:
        # Find documents containing the entity
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"openai_entities.text.keyword": entity_id}},
                        {"range": {"openai_entities.confidence": {"gte": confidence_threshold}}}
                    ]
                }
            },
            "size": 50
        }
        
        connected_entities = []
        center_entity = None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data.get("hits", {}).get("hits", []):
                    doc = hit["_source"]
                    
                    # Find the center entity details
                    for entity in doc.get("openai_entities", []):
                        if entity["text"] == entity_id and not center_entity:
                            center_entity = {
                                "id": entity_id,
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "size": 10,
                                "color": "#ff6b35"
                            }
                    
                    # Get connected entities from same documents
                    for entity in doc.get("openai_entities", []):
                        if (entity["text"] != entity_id and 
                            entity["confidence"] >= confidence_threshold):
                            
                            connected_entities.append({
                                "id": entity["text"],
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "size": 6,
                                "color": get_entity_color(entity["type"]),
                                "source_document": doc.get("title", "Unknown")
                            })
        
        # Remove duplicates
        unique_entities = {}
        for entity in connected_entities:
            if entity["id"] not in unique_entities:
                unique_entities[entity["id"]] = entity
            else:
                if entity["confidence"] > unique_entities[entity["id"]]["confidence"]:
                    unique_entities[entity["id"]] = entity
        
        connected_list = list(unique_entities.values())[:20]  # Limit to 20
        
        # Create network data
        nodes = []
        links = []
        
        if center_entity:
            nodes.append(center_entity)
            
            for entity in connected_list:
                nodes.append(entity)
                links.append({
                    "source": center_entity["id"],
                    "target": entity["id"],
                    "relationship": "CO_OCCURS",
                    "weight": entity["confidence"]
                })
        
        return {
            "center_entity": center_entity,
            "connected_entities": connected_list,
            "network_data": {"nodes": nodes, "links": links},
            "statistics": {
                "total_connections": len(connected_list),
                "unique_entity_types": len(set(e["type"] for e in connected_list)),
                "average_confidence": sum(e["confidence"] for e in connected_list) / len(connected_list) if connected_list else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Entity exploration failed: {str(e)}", "center_entity": None, "connected_entities": []}

async def get_investigation_timeline(case_id: str, start_date: str, end_date: str):
    """Get timeline for investigation - Palantir timeline analysis"""
    try:
        # Simple timeline based on document timestamps
        query = {
            "query": {
                "range": {
                    "metadata.upload_date": {
                        "gte": start_date,
                        "lte": end_date
                    }
                }
            },
            "sort": [{"metadata.upload_date": {"order": "asc"}}],
            "size": 100
        }
        
        timeline_events = []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data.get("hits", {}).get("hits", []):
                    doc = hit["_source"]
                    timeline_events.append({
                        "id": hit["_id"],
                        "timestamp": doc["metadata"]["upload_date"],
                        "title": f"Document Processed: {doc['title'][:50]}...",
                        "description": doc.get("ai_summary", "")[:200] + "...",
                        "type": "document_processed",
                        "entities": doc.get("openai_entities", [])[:3],  # Top 3 entities
                        "confidence": 0.9
                    })
        
        return {
            "timeline_events": timeline_events,
            "statistics": {
                "total_events": len(timeline_events),
                "date_range": {"start": start_date, "end": end_date}
            }
        }
        
    except Exception as e:
        return {"error": f"Timeline generation failed: {str(e)}", "timeline_events": []}

async def advanced_search_simple(query: str = "", entity_types: Optional[str] = None, confidence_threshold: float = 0.5, size: int = 20, from_: int = 0):
    """Advanced search with filters - Palantir search capabilities"""
    try:
        must_clauses = []
        
        if query and query.strip():
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content", "ai_summary"],
                    "fuzziness": "AUTO"
                }
            })
        
        if entity_types:
            types = [t.strip() for t in entity_types.split(",")]
            must_clauses.append({
                "bool": {
                    "must": [
                        {"terms": {"openai_entities.type.keyword": types}},
                        {"range": {"openai_entities.confidence": {"gte": confidence_threshold}}}
                    ]
                }
            })
        
        es_query = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}]
                }
            },
            "highlight": {
                "fields": {
                    "content": {},
                    "title": {},
                    "ai_summary": {}
                }
            },
            "size": size,
            "from": from_,
            "sort": [{"_score": {"order": "desc"}}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "query": query,
                    "filters": {
                        "entity_types": entity_types,
                        "confidence_threshold": confidence_threshold
                    },
                    "total": data.get("hits", {}).get("total", {}).get("value", 0),
                    "results": data.get("hits", {}).get("hits", []),
                    "took": data.get("took", 0)
                }
            else:
                return {"error": f"Search failed: {response.status_code}"}
                
    except Exception as e:
        return {"error": f"Advanced search failed: {str(e)}"}

# Investigation Management Endpoints - Palantir-style
@app.post("/api/v1/investigations")
async def create_investigation(investigation: InvestigationCreate):
    """Create a new investigation case"""
    try:
        result = await create_simple_investigation(
            investigation.title,
            investigation.description,
            investigation.created_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create investigation: {str(e)}")

@app.get("/api/v1/investigations")
async def list_investigations():
    """List investigations"""
    try:
        result = await list_simple_investigations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list investigations: {str(e)}")

# Entity Exploration Endpoints - Gotham-style
@app.get("/api/v1/entities/{entity_id}/explore")
async def explore_entity(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5, description="Relationship depth"),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence")
):
    """Deep exploration of entity connections - Palantir Gotham style"""
    try:
        result = await explore_entity_simple(entity_id, depth, confidence_threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity exploration failed: {str(e)}")

@app.get("/api/v1/entities/{entity_id}/network")
async def get_entity_network(
    entity_id: str,
    depth: int = Query(2, ge=1, le=5, description="Relationship depth"),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence")
):
    """Get entity network graph - Gotham network visualization"""
    try:
        result = await explore_entity_simple(entity_id, depth, confidence_threshold)
        
        if "network_data" in result:
            return result["network_data"]
        else:
            return {"nodes": [], "links": [], "error": result.get("error", "Unknown error")}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity network: {str(e)}")

# Temporal Analysis Endpoints - Foundry-style
@app.get("/api/v1/temporal/timeline")
async def get_timeline(
    case_id: str = Query("default", description="Investigation case ID"),
    start_date: str = Query("2024-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query("2025-12-31", description="End date (YYYY-MM-DD)"),
    granularity: str = Query("day", description="Time granularity")
):
    """Get timeline for investigation case - Palantir timeline analysis"""
    try:
        result = await get_investigation_timeline(case_id, start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")

# Advanced Search Endpoints - Palantir search capabilities
@app.get("/api/v1/search/advanced")
async def advanced_search(
    q: str = Query("", description="Search query"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types (PERSON,ORGANIZATION,EVENT,etc)"),
    confidence_threshold: float = Query(0.5, description="Minimum confidence threshold"),
    size: int = Query(20, description="Number of results"),
    from_: int = Query(0, alias="from", description="Starting index")
):
    """Advanced multi-dimensional search - Palantir search with entity filtering"""
    try:
        result = await advanced_search_simple(
            query=q,
            entity_types=entity_types,
            confidence_threshold=confidence_threshold,
            size=size,
            from_=from_
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@app.get("/api/v1/entities/types")
async def get_entity_types():
    """Get available entity types for debugging"""
    try:
        async with httpx.AsyncClient() as client:
            # Get a sample of documents with entities
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json={"query": {"exists": {"field": "openai_entities"}}, "size": 10, "_source": ["openai_entities.type"]},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                types = set()
                for hit in data.get("hits", {}).get("hits", []):
                    for entity in hit["_source"].get("openai_entities", []):
                        types.add(entity.get("type", "UNKNOWN"))
                
                return {"entity_types": sorted(list(types)), "total_docs": data.get("hits", {}).get("total", {}).get("value", 0)}
            else:
                return {"error": f"Elasticsearch error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to get entity types: {str(e)}"}

# Entity Enrichment Endpoints
@app.get("/api/v1/entities")
async def get_all_entities():
    """Get all entities available for enrichment"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://entity-enrichment:8003/api/v1/entities",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get entities")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")

@app.get("/api/v1/entities/{entity_id}")
async def get_entity_details(entity_id: str):
    """Get detailed information about a specific entity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://entity-enrichment:8003/api/v1/entities/{entity_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Entity not found")
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get entity details")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity details: {str(e)}")

@app.post("/api/v1/entities/enrich")
async def enrich_entities(request: dict):
    """Start entity enrichment process"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://entity-enrichment:8003/api/v1/entities/enrich",
                json=request,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to start enrichment")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enrichment: {str(e)}")

@app.get("/api/v1/entities/status/{entity_id}")
async def get_enrichment_status(entity_id: str):
    """Get enrichment status for a specific entity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://entity-enrichment:8003/api/v1/entities/status/{entity_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Entity status not found")
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get entity status")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity status: {str(e)}")

# Document Chat Endpoints
@app.post("/api/v1/chat")
async def chat_with_documents(request: dict):
    """Chat with documents using AI"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://document-chat:8004/api/v1/chat",
                json=request,
                timeout=60  # Longer timeout for AI processing
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to process chat request")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")

@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://document-chat:8004/api/v1/conversations/{conversation_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.get("/api/v1/conversations")
async def list_conversations(user_id: str = "user1", limit: int = 50, offset: int = 0):
    """List user conversations"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://document-chat:8004/api/v1/conversations?user_id={user_id}&limit={limit}&offset={offset}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to list conversations")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://document-chat:8004/api/v1/conversations/{conversation_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to delete conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

# Project Spaces API Endpoints
@app.get("/api/v1/spaces", response_model=List[ProjectSpace], tags=["Project Spaces"])
async def get_user_spaces():
    """Get all project spaces for the current user"""
    return [ProjectSpace(**space) for space in mock_spaces]

@app.post("/api/v1/spaces", response_model=ProjectSpace, tags=["Project Spaces"])
async def create_project_space(space_data: ProjectSpaceCreate):
    """Create a new project space"""
    new_space = {
        "id": str(uuid.uuid4()),
        "name": space_data.name,
        "description": space_data.description,
        "color": space_data.color,
        "icon": space_data.icon,
        "document_count": 0,
        "member_count": 1,
        "user_role": "owner",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    mock_spaces.append(new_space)
    return ProjectSpace(**new_space)

@app.get("/api/v1/spaces/{space_id}", response_model=ProjectSpace, tags=["Project Spaces"])
async def get_project_space(space_id: str):
    """Get a specific project space"""
    for space in mock_spaces:
        if space["id"] == space_id:
            return ProjectSpace(**space)
    
    raise HTTPException(status_code=404, detail="Project space not found")

@app.put("/api/v1/spaces/{space_id}", response_model=ProjectSpace, tags=["Project Spaces"])
async def update_project_space(space_id: str, space_data: ProjectSpaceCreate):
    """Update a project space"""
    for i, space in enumerate(mock_spaces):
        if space["id"] == space_id:
            mock_spaces[i].update({
                "name": space_data.name,
                "description": space_data.description,
                "color": space_data.color,
                "icon": space_data.icon
            })
            return ProjectSpace(**mock_spaces[i])
    
    raise HTTPException(status_code=404, detail="Project space not found")

@app.delete("/api/v1/spaces/{space_id}", tags=["Project Spaces"])
async def delete_project_space(space_id: str):
    """Delete a project space"""
    for i, space in enumerate(mock_spaces):
        if space["id"] == space_id:
            del mock_spaces[i]
            return {"message": "Project space deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Project space not found")

@app.get("/api/v1/spaces/{space_id}/analytics", tags=["Project Spaces"])
async def get_space_analytics(space_id: str):
    """Get analytics for a project space"""
    for space in mock_spaces:
        if space["id"] == space_id:
            return {
                "space_id": space_id,
                "space_name": space["name"],
                "total_documents": space["document_count"],
                "processed_documents": int(space["document_count"] * 0.8),
                "processing_documents": int(space["document_count"] * 0.1),
                "failed_documents": int(space["document_count"] * 0.1),
                "avg_progress": 85.5,
                "member_count": space["member_count"]
            }
    
    raise HTTPException(status_code=404, detail="Project space not found")

# Entity Enrichment Endpoints
class EntityEnrichmentRequest(BaseModel):
    entity_ids: List[str] = Field(..., description="List of entity IDs to enrich")
    entity_type: Optional[str] = Field(None, description="Type of entities to enrich")
    max_sources: int = Field(3, description="Maximum number of sources to scrape")

@app.post("/api/v1/enrichment/enrich", tags=["Entity Enrichment"])
async def enrich_entities(request: EntityEnrichmentRequest):
    """Start entity enrichment process"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://entity-enrichment:8003/api/v1/entities/enrich",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Enrichment service error: {str(e)}")

@app.get("/api/v1/enrichment/status/{entity_id}", tags=["Entity Enrichment"])
async def get_enrichment_status(entity_id: str):
    """Get enrichment status for a specific entity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://entity-enrichment:8003/api/v1/entities/status/{entity_id}",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Enrichment service error: {str(e)}")

@app.get("/api/v1/enrichment/entities", tags=["Entity Enrichment"])
async def get_all_entities():
    """Get all enriched entities"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://entity-enrichment:8003/api/v1/entities",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Enrichment service error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,
        limit_max_requests=1000,
        limit_concurrency=100
    )