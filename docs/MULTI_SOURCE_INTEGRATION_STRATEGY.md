# Multi-Source Integration Strategy for Ingestion Pipeline

## Overview

This document outlines how to integrate multi-source external data (ClinicalTrials.gov, FDA OpenFDA, Semantic Scholar, etc.) into the existing document ingestion pipeline while maintaining consistency and performance.

## Current Pipeline Architecture

```
Document Upload → MinIO → LlamaParse → AI Analysis → Elasticsearch + Neo4j
```

## Enhanced Pipeline with Multi-Source Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENHANCED INGESTION PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   LOCAL FILES   │    │  EXTERNAL APIs  │    │  STREAMING DATA │        │
│  │                 │    │                 │    │                 │        │
│  │ • PDFs          │    │ • PubMed        │    │ • Kafka Topics  │        │
│  │ • Word Docs     │    │ • ClinicalTrials│    │ • Real-time     │        │
│  │ • Images        │    │ • FDA OpenFDA   │    │ • Webhooks      │        │
│  │ • Excel         │    │ • Semantic      │    │ • IoT Sensors   │        │
│  │                 │    │   Scholar       │    │                 │        │
│  │                 │    │ • ChEMBL        │    │                 │        │
│  │                 │    │ • Europe PMC    │    │                 │        │
│  └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘        │
│            │                      │                      │                │
│            └──────────────────────┼──────────────────────┘                │
│                                   │                                       │
│            ┌──────────────────────▼──────────────────────┐                │
│            │           UNIFIED INGESTION LAYER           │                │
│            │                                             │                │
│            │  ┌─────────────────────────────────────────┐│                │
│            │  │        StandardDocument Model          ││                │
│            │  │                                         ││                │
│            │  │ • Unified format for ALL sources       ││                │
│            │  │ • Consistent metadata structure        ││                │
│            │  │ • AI-extracted entities & relationships││                │
│            │  │ • Quality scoring & validation         ││                │
│            │  └─────────────────────────────────────────┘│                │
│            └──────────────────────┬──────────────────────┘                │
│                                   │                                       │
│            ┌──────────────────────▼──────────────────────┐                │
│            │         PROCESSING ORCHESTRATOR            │                │
│            │                                             │                │
│            │  ┌─────────────┐  ┌─────────────┐  ┌───────┐│                │
│            │  │   PARSING   │  │     AI      │  │ DEDUP ││                │
│            │  │             │  │ PROCESSING  │  │       ││                │
│            │  │ • LlamaParse│  │             │  │       ││                │
│            │  │ • PDF Tools │  │ • Entity    │  │       ││                │
│            │  │ • OCR       │  │   Extract   │  │       ││                │
│            │  │ • Text      │  │ • Relations │  │       ││                │
│            │  │   Extract   │  │ • Concepts  │  │       ││                │
│            │  │             │  │ • Summary   │  │       ││                │
│            │  └─────────────┘  └─────────────┘  └───────┘│                │
│            └──────────────────────┬──────────────────────┘                │
│                                   │                                       │
│            ┌──────────────────────▼──────────────────────┐                │
│            │            STORAGE LAYER                    │                │
│            │                                             │                │
│            │  ┌─────────────┐  ┌─────────────┐  ┌───────┐│                │
│            │  │ELASTICSEARCH│  │    NEO4J    │  │ MINIO ││                │
│            │  │             │  │             │  │       ││                │
│            │  │ • Full-text │  │ • Knowledge │  │       ││                │
│            │  │   Search    │  │   Graph     │  │       ││                │
│            │  │ • Faceted   │  │ • Relations │  │       ││                │
│            │  │   Search    │  │ • Entities  │  │       ││                │
│            │  │ • Vector    │  │ • Concepts  │  │       ││                │
│            │  │   Search    │  │             │  │       ││                │
│            │  └─────────────┘  └─────────────┘  └───────┘│                │
│            └──────────────────────┬──────────────────────┘                │
│                                   │                                       │
│            ┌──────────────────────▼──────────────────────┐                │
│            │            API & ANALYTICS                  │                │
│            │                                             │                │
│            │  ┌─────────────┐  ┌─────────────┐  ┌───────┐│                │
│            │  │  SEARCH API │  │  GRAPH API  │  │ANALYTICS││                │
│            │  │             │  │             │  │       ││                │
│            │  │ • Unified   │  │ • Relations │  │       ││                │
│            │  │   Search    │  │ • Entities  │  │       ││                │
│            │  │ • Multi-    │  │ • Concepts  │  │       ││                │
│            │  │   Source    │  │ • Insights  │  │       ││                │
│            │  │ • Faceted   │  │             │  │       ││                │
│            │  └─────────────┘  └─────────────┘  └───────┘│                │
│            └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. **Unified Document Model (StandardDocument)**

The `StandardDocument` model serves as the bridge between external sources and the existing pipeline:

```python
@dataclass
class StandardDocument:
    # Core identification
    id: str
    source: str  # "pubmed", "clinicaltrials", "fda", etc.
    source_id: str  # Original ID from source
    project_space_id: Optional[str] = None
    
    # Content (unified across all sources)
    title: str
    abstract: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    
    # Classification
    document_type: DocumentType
    language: str = "en"
    
    # AI-extracted intelligence
    entities: Dict[str, List[Entity]]
    relationships: List[Relationship]
    key_concepts: List[str]
    
    # Quality and processing
    quality_score: float
    processing_status: str
    processing_errors: List[str]
    
    # Source-specific metadata
    metadata: Dict[str, Any]
```

### 2. **Multi-Source Ingestion Service**

Create a new service that handles external data ingestion:

```python
class MultiSourceIngestionService:
    """Handles ingestion from external data sources"""
    
    async def ingest_from_sources(
        self,
        project_space_id: str,
        query: str,
        sources: List[str],
        max_results_per_source: int = 100
    ) -> str:
        """Start ingestion job from multiple sources"""
        
    async def process_external_document(
        self,
        doc: StandardDocument,
        project_space_id: str
    ) -> bool:
        """Process external document through existing pipeline"""
```

### 3. **Integration with Existing Pipeline**

#### A. **Document Processor Integration**

Modify the existing `DocumentProcessor` to handle `StandardDocument`:

```python
class DocumentProcessor:
    async def process_standard_document(
        self,
        doc: StandardDocument,
        project_space_id: str
    ):
        """Process StandardDocument through existing pipeline"""
        
        # 1. Set project space
        doc.project_space_id = project_space_id
        
        # 2. AI enrichment (if not already done)
        if not doc.entities:
            await self.enrich_with_ai(doc)
        
        # 3. Index in Elasticsearch
        await self.index_document(doc.id, doc.to_dict())
        
        # 4. Create knowledge graph
        if doc.entities:
            await self.create_knowledge_graph(doc.id, doc)
        
        # 5. Update processing status
        await self.update_document_status(
            doc.id, "completed", "External document processed"
        )
```

#### B. **Storage Integration**

Both external and local documents use the same storage systems:

- **Elasticsearch**: Full-text search, faceted search, vector search
- **Neo4j**: Knowledge graph with entities and relationships
- **MinIO**: File storage (for external documents, store metadata)

#### C. **Search Integration**

The existing search APIs work with both local and external documents:

```python
# Unified search across all document types
async def search_documents(
    query: str,
    sources: Optional[List[str]] = None,
    document_types: Optional[List[str]] = None,
    project_space_id: Optional[str] = None
):
    """Search across local and external documents"""
```

## Implementation Phases

### **Phase 1: Core Integration (Week 1-2)**

1. **Create Multi-Source Ingestion Service**
   - Implement `MultiSourceIngestionService`
   - Add ingestion job management
   - Integrate with existing `DocumentProcessor`

2. **Modify Document Processor**
   - Add `StandardDocument` processing capability
   - Maintain backward compatibility with local files
   - Add source-specific processing logic

3. **Update Storage Layer**
   - Ensure Elasticsearch can handle external documents
   - Update Neo4j schema for multi-source entities
   - Add source tracking in metadata

### **Phase 2: API Integration (Week 3-4)**

1. **Unified Search API**
   - Extend existing search endpoints
   - Add source filtering
   - Implement faceted search by source

2. **Ingestion Management API**
   - Add endpoints for starting ingestion jobs
   - Job status monitoring
   - Error handling and retry logic

3. **Source Management API**
   - Enable/disable sources
   - Configure API keys
   - Monitor source health

### **Phase 3: Advanced Features (Week 5-6)**

1. **Real-time Ingestion**
   - Webhook support for real-time updates
   - Streaming data integration
   - Change detection and updates

2. **Data Quality & Deduplication**
   - Cross-source duplicate detection
   - Quality scoring and validation
   - Data freshness monitoring

3. **Analytics & Monitoring**
   - Ingestion metrics dashboard
   - Source performance monitoring
   - Data lineage tracking

## Data Flow Examples

### **Example 1: Clinical Trial Ingestion**

```python
# 1. User searches for "covid vaccine" in ClinicalTrials.gov
search_result = await unified_search_service.search(
    query="covid vaccine",
    sources=["clinicaltrials"],
    max_results=50
)

# 2. Convert to StandardDocument
documents = []
for trial in search_result.results:
    doc = StandardDocument(
        id=str(uuid.uuid4()),
        source="clinicaltrials",
        source_id=trial["nct_id"],
        title=trial["title"],
        abstract=trial["description"],
        document_type=DocumentType.CLINICAL_TRIAL,
        publication_date=trial["start_date"],
        url=trial["url"],
        metadata=trial  # Store original trial data
    )
    documents.append(doc)

# 3. Process through existing pipeline
for doc in documents:
    await document_processor.process_standard_document(
        doc, project_space_id
    )

# 4. Now searchable via existing APIs
search_results = await search_service.search(
    query="covid vaccine",
    project_space_id=project_space_id
)
```

### **Example 2: FDA Adverse Events Ingestion**

```python
# 1. Search FDA for adverse events
fda_results = await fda_connector.search(
    query="covid vaccine",
    max_results=100
)

# 2. Process each adverse event
for event in fda_results:
    doc = StandardDocument(
        source="fda",
        source_id=event["safetyreportid"],
        title=f"Adverse Event: {event['patient']['drug'][0]['medicinalproduct']}",
        document_type=DocumentType.ADVERSE_EVENT,
        metadata=event
    )
    
    # 3. AI enrichment
    await ai_processor.enrich_document(doc)
    
    # 4. Store and index
    await document_processor.process_standard_document(doc, project_space_id)
```

## Benefits of This Integration

### **1. Unified Data Model**
- All documents (local and external) use the same `StandardDocument` format
- Consistent processing, storage, and retrieval
- Seamless search across all sources

### **2. Leverage Existing Infrastructure**
- Reuse existing AI processing pipeline
- Utilize current Elasticsearch and Neo4j setup
- Maintain existing search and analytics capabilities

### **3. Scalable Architecture**
- Easy to add new external sources
- Parallel processing of multiple sources
- Independent scaling of components

### **4. Data Quality & Consistency**
- Standardized entity extraction across all sources
- Unified relationship mapping
- Consistent quality scoring

### **5. Real-time Capabilities**
- Live data from external APIs
- Real-time search across all sources
- Up-to-date knowledge graphs

## Migration Strategy

### **Phase 1: Parallel Operation**
- Run existing pipeline unchanged
- Add multi-source ingestion alongside
- Gradual migration of users

### **Phase 2: Unified Interface**
- Merge search APIs
- Unified document management
- Single dashboard for all sources

### **Phase 3: Full Integration**
- Deprecate old APIs
- Complete migration to unified system
- Advanced multi-source features

## Monitoring & Observability

### **Metrics to Track**
- Ingestion job success/failure rates
- Source API response times
- Document processing times
- Search performance across sources
- Data quality scores

### **Alerts**
- Source API failures
- Ingestion job failures
- High error rates
- Performance degradation

### **Dashboards**
- Real-time ingestion status
- Source health monitoring
- Search analytics
- Data quality metrics

This integration strategy ensures that multi-source external data seamlessly integrates with the existing ingestion pipeline while maintaining performance, consistency, and scalability.
