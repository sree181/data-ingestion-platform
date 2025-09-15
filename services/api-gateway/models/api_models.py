"""
Pydantic models for API requests and responses
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class SearchSortOrder(str, Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EntityType(str, Enum):
    """Entity types in knowledge graph"""
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    DOCUMENT = "Document"
    CONCEPT = "Concept"
    DATE = "Date"


# Search Models
class SearchFilter(BaseModel):
    """Search filter specification"""
    field: str = Field(..., description="Field name to filter on")
    value: Union[str, List[str]] = Field(..., description="Filter value(s)")
    operator: str = Field("equals", description="Filter operator (equals, contains, range)")


class SearchSort(BaseModel):
    """Search sort specification"""
    field: str = Field(..., description="Field name to sort on")
    order: SearchSortOrder = Field(SearchSortOrder.DESC, description="Sort order")


class SearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(..., description="Search query text")
    filters: Optional[List[SearchFilter]] = Field(None, description="Additional filters")
    size: int = Field(20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort: Optional[List[SearchSort]] = Field(None, description="Sort specifications")
    highlight: bool = Field(True, description="Enable text highlighting")
    include_facets: bool = Field(True, description="Include facet aggregations")


class SearchHit(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Relevance score")
    source: Dict[str, Any] = Field(..., description="Document source data")
    highlight: Optional[Dict[str, List[str]]] = Field(None, description="Highlighted text snippets")


class SearchFacet(BaseModel):
    """Search facet result"""
    field: str = Field(..., description="Facet field name")
    buckets: List[Dict[str, Any]] = Field(..., description="Facet bucket counts")


class SearchResponse(BaseModel):
    """Document search response"""
    total: int = Field(..., description="Total number of matching documents")
    hits: List[SearchHit] = Field(..., description="Search results")
    facets: Optional[List[SearchFacet]] = Field(None, description="Facet aggregations")
    took: int = Field(..., description="Query execution time in milliseconds")
    query: str = Field(..., description="Original search query")


# Graph Query Models
class GraphQueryRequest(BaseModel):
    """Neo4j graph query request"""
    cypher_query: str = Field(..., description="Cypher query to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")


class GraphNode(BaseModel):
    """Graph node representation"""
    id: str = Field(..., description="Node ID")
    labels: List[str] = Field(..., description="Node labels")
    properties: Dict[str, Any] = Field(..., description="Node properties")


class GraphRelationship(BaseModel):
    """Graph relationship representation"""
    id: str = Field(..., description="Relationship ID")
    type: str = Field(..., description="Relationship type")
    start_node: str = Field(..., description="Start node ID")
    end_node: str = Field(..., description="End node ID")
    properties: Dict[str, Any] = Field(..., description="Relationship properties")


class GraphQueryResponse(BaseModel):
    """Neo4j graph query response"""
    nodes: List[GraphNode] = Field(..., description="Result nodes")
    relationships: List[GraphRelationship] = Field(..., description="Result relationships")
    total: int = Field(..., description="Total number of results")
    took: int = Field(..., description="Query execution time in milliseconds")


# Document Upload Models
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")
    upload_url: Optional[str] = Field(None, description="Direct access URL")


class IngestionStatus(BaseModel):
    """Document ingestion status"""
    document_id: str = Field(..., description="Document identifier")
    status: DocumentStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0, le=100, description="Processing progress percentage")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Entity Models
class Entity(BaseModel):
    """Knowledge graph entity"""
    id: str = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: EntityType = Field(..., description="Entity type")
    properties: Dict[str, Any] = Field(..., description="Entity properties")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")


class EntitySearchResponse(BaseModel):
    """Entity search response"""
    entities: List[Entity] = Field(..., description="Found entities")
    total: int = Field(..., description="Total number of matching entities")


# Analytics Models
class DocumentStats(BaseModel):
    """Document statistics"""
    total_documents: int = Field(..., description="Total number of documents")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    documents_by_type: Dict[str, int] = Field(..., description="Document count by type")
    recent_uploads: int = Field(..., description="Recent uploads count")


class GraphStats(BaseModel):
    """Knowledge graph statistics"""
    total_nodes: int = Field(..., description="Total number of nodes")
    total_relationships: int = Field(..., description="Total number of relationships")
    nodes_by_type: Dict[str, int] = Field(..., description="Node count by type")
    relationships_by_type: Dict[str, int] = Field(..., description="Relationship count by type")


class ProcessingStats(BaseModel):
    """Processing pipeline statistics"""
    pending_jobs: int = Field(..., description="Number of pending jobs")
    processing_jobs: int = Field(..., description="Number of currently processing jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    average_processing_time: float = Field(..., description="Average processing time in seconds")


class DashboardData(BaseModel):
    """Dashboard analytics data"""
    document_stats: DocumentStats = Field(..., description="Document statistics")
    graph_stats: GraphStats = Field(..., description="Knowledge graph statistics")
    processing_stats: ProcessingStats = Field(..., description="Processing statistics")
    timestamp: datetime = Field(..., description="Data collection timestamp")


# Authentication Models
class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserToken(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserInfo(BaseModel):
    """User information"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role")
    permissions: List[str] = Field(..., description="User permissions")


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Streaming Models
class StreamingConfig(BaseModel):
    """Streaming data configuration"""
    source_type: str = Field(..., description="Data source type")
    source_config: Dict[str, Any] = Field(..., description="Source-specific configuration")
    processing_config: Dict[str, Any] = Field(..., description="Processing configuration")
    output_config: Dict[str, Any] = Field(..., description="Output configuration")


class StreamingStatus(BaseModel):
    """Streaming pipeline status"""
    pipeline_id: str = Field(..., description="Pipeline ID")
    status: str = Field(..., description="Pipeline status")
    records_processed: int = Field(..., description="Number of records processed")
    last_processed: Optional[datetime] = Field(None, description="Last processing timestamp")
    error_count: int = Field(..., description="Number of errors")
    throughput: float = Field(..., description="Records per second")


# Validation helpers
@validator('query', pre=True)
def validate_search_query(cls, v):
    """Validate search query"""
    if not v or not v.strip():
        raise ValueError("Search query cannot be empty")
    return v.strip()


@validator('cypher_query', pre=True)
def validate_cypher_query(cls, v):
    """Validate Cypher query"""
    if not v or not v.strip():
        raise ValueError("Cypher query cannot be empty")
    # Basic validation - ensure it's a read-only query
    dangerous_keywords = ['DELETE', 'DROP', 'CREATE', 'SET', 'REMOVE', 'MERGE']
    query_upper = v.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"Query contains dangerous keyword: {keyword}")
    return v.strip()