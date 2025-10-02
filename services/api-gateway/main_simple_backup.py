from fastapi import FastAPI, Query, HTTPException, Depends, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, List
import httpx
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
import uvicorn
import asyncio
import os

# Import database manager
from database import DatabaseManager

# Pydantic Models for Project Spaces
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

app = FastAPI(
    title="Data Ingestion API Gateway", 
    description="Production-ready API Gateway",
    version="1.0.0"
)

# Initialize database manager
db_manager = None

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

# Include project spaces routes
from routes.project_spaces import router as spaces_router
app.include_router(spaces_router)

# Document ingestion endpoint (temporary inline implementation)
@app.get("/api/v1/spaces/{space_id}/documents/local-files")
async def list_local_files_simple(space_id: str):
    """Simple endpoint to list local files"""
    try:
        from pathlib import Path
        import os
        from datetime import datetime
        
        # Mock response for now - in a real implementation, this would scan the Searchable folder
        mock_files = [
            {
                "filename": "sample_document_1.pdf",
                "path": "/app/Searchable/sample_document_1.pdf",
                "size": 1024000,
                "modified_date": datetime.utcnow().isoformat(),
                "file_type": "pdf"
            },
            {
                "filename": "sample_document_2.pdf", 
                "path": "/app/Searchable/sample_document_2.pdf",
                "size": 2048000,
                "modified_date": datetime.utcnow().isoformat(),
                "file_type": "pdf"
            }
        ]
        
        return {
            "files": mock_files,
            "total_files": len(mock_files),
            "total_size": sum(f["size"] for f in mock_files),
            "searchable_path": "/app/Searchable"
        }
        
    except Exception as e:
        return {"files": [], "total_files": 0, "total_size": 0, "error": str(e)}

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "api-gateway-simple"}

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
            
            return {
                "total_documents": total_docs,
                "documents_by_category": {"General": total_docs},
                "documents_by_file_type": {"pdf": total_docs},
                "extraction_methods": {"basic": total_docs},
                "timeline_data": [],
                "processing_stats": {
                    "completed": total_docs,
                    "ai_processed": 0,
                    "ai_processed_percentage": 0,
                    "basic_processed": total_docs,
                    "processing": 0,
                    "failed": 0
                },
                "insights": {
                    "avg_file_size_mb": 1.5,
                    "total_entities_extracted": 0,
                    "avg_entities_per_doc": 0,
                    "most_common_category": "General",
                    "documents_uploaded_today": 0
                },
                "recent_activity": []
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

# Database startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global db_manager
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/dataplatform")
        db_manager = DatabaseManager(database_url)
        await db_manager.connect()
        
        # Create default admin user if it doesn't exist
        await create_default_admin_user()
        
        print("✅ Database connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        # Don't raise exception to allow app to start with mock data

async def create_default_admin_user():
    """Create default admin user for project spaces"""
    try:
        async with db_manager.pool.acquire() as conn:
            # Check if admin user exists
            admin_id = await conn.fetchval("SELECT id FROM users WHERE username = 'admin'")
            
            if not admin_id:
                # Create admin user
                admin_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO users (id, username, email, created_at, updated_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    admin_id, "admin", "admin@company.com"
                )
                print("✅ Created default admin user")
            else:
                print("✅ Admin user already exists")
    except Exception as e:
        print(f"⚠️  Could not create admin user: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    global db_manager
    if db_manager:
        await db_manager.close()
        print("✅ Database connections closed")

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
