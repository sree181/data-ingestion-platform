# 🏗️ **MULTI-SOURCE DATA INTEGRATION ARCHITECTURE**
## *Unified Ingestion & Consumption Framework*

---

# 📋 **TABLE OF CONTENTS**

1. [Architecture Overview](#architecture)
2. [Data Source Abstraction Layer](#abstraction)
3. [Unified Ingestion Pipeline](#ingestion)
4. [Data Normalization & Enrichment](#normalization)
5. [Storage Strategy](#storage)
6. [Query & Consumption Layer](#consumption)
7. [UI/UX Design](#ui-ux)
8. [Implementation Roadmap](#roadmap)

---

<a name="architecture"></a>
# 1️⃣ **ARCHITECTURE OVERVIEW**

## **The Big Picture: Unified Data Intelligence Platform**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🎨 UNIFIED SEARCH & DISCOVERY                              │    │
│  │  • Single search bar → queries ALL sources                 │    │
│  │  • Filter by source, date, type, domain                    │    │
│  │  • Faceted navigation                                       │    │
│  │  • Source-specific advanced options                         │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE CONNECTOR LAYER                     │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐     │
│  │  PubMed      │ Clinical     │  FDA         │   ChEMBL     │     │
│  │  Connector   │ Trials       │  OpenFDA     │   Connector  │     │
│  │              │  Connector   │  Connector   │              │     │
│  └──────────────┴──────────────┴──────────────┴──────────────┘     │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐     │
│  │  PubChem     │ Europe PMC   │  Patents     │   SEC EDGAR  │     │
│  │  Connector   │ Connector    │  Connector   │   Connector  │     │
│  └──────────────┴──────────────┴──────────────┴──────────────┘     │
│                          ... 30+ more ...                            │
│                                                                      │
│  Each connector implements: AbstractDataSource interface            │
│    • fetch(query)                                                   │
│    • transform_to_standard_format()                                 │
│    • get_metadata()                                                 │
│    • handle_rate_limits()                                           │
│    • cache_strategy()                                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA NORMALIZATION LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Convert ALL sources to → Unified Document Schema          │    │
│  │                                                             │    │
│  │  StandardDocument:                                          │    │
│  │    • id (UUID)                                             │    │
│  │    • source (pubmed|clinicaltrials|fda|...)                │    │
│  │    • source_id (original ID)                               │    │
│  │    • title                                                  │    │
│  │    • abstract/summary                                       │    │
│  │    • content (full text if available)                      │    │
│  │    • authors[]                                              │    │
│  │    • publication_date                                       │    │
│  │    • document_type (research|trial|patent|filing|...)      │    │
│  │    • entities[] (extracted)                                 │    │
│  │    • metadata{} (source-specific fields)                   │    │
│  │    • urls[] (original links)                               │    │
│  │    • citations[]                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      AI ENRICHMENT LAYER                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  • Entity Extraction (unified across all sources)          │    │
│  │  • Relationship Extraction                                  │    │
│  │  • Summarization                                            │    │
│  │  • Classification                                           │    │
│  │  • Embedding Generation (semantic search)                  │    │
│  │  • Cross-source linking (same drug in different sources)   │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐     │
│  │ Elasticsearch│   Neo4j      │  PostgreSQL  │    MinIO     │     │
│  │ (Search)     │  (Graph)     │  (Metadata)  │  (Raw Files) │     │
│  │              │              │              │              │     │
│  │ • Full-text  │ • Cross-src  │ • Jobs       │ • Original   │     │
│  │ • Facets     │   links      │ • Sources    │   documents  │     │
│  │ • Aggreg.    │ • Entities   │ • Users      │ • Images     │     │
│  └──────────────┴──────────────┴──────────────┴──────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CONSUMPTION LAYER                               │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  • Unified Search API                                       │    │
│  │  • Cross-source analytics                                   │    │
│  │  • Export (PDF, CSV, JSON)                                 │    │
│  │  • Alerts & Notifications                                   │    │
│  │  • Dashboard & Visualizations                               │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

<a name="abstraction"></a>
# 2️⃣ **DATA SOURCE ABSTRACTION LAYER**

## **Design Pattern: Abstract Factory + Strategy**

### **Core Interface: `AbstractDataSource`**

```python
# services/data-connectors/base/abstract_data_source.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SourceType(Enum):
    """Category of data source"""
    RESEARCH_PAPER = "research_paper"
    CLINICAL_TRIAL = "clinical_trial"
    REGULATORY = "regulatory"
    PATENT = "patent"
    FINANCIAL = "financial"
    CHEMICAL = "chemical"
    GENOMIC = "genomic"
    NEWS = "news"
    GRANT = "grant"

class DocumentType(Enum):
    """Type of document"""
    RESEARCH_ARTICLE = "research_article"
    PREPRINT = "preprint"
    CLINICAL_TRIAL = "clinical_trial"
    PATENT = "patent"
    SEC_FILING = "sec_filing"
    DRUG_LABEL = "drug_label"
    ADVERSE_EVENT = "adverse_event"
    CHEMICAL_COMPOUND = "chemical_compound"
    PROTEIN_STRUCTURE = "protein_structure"
    NEWS_ARTICLE = "news_article"
    GRANT_AWARD = "grant_award"

@dataclass
class StandardDocument:
    """Unified document format for ALL sources"""
    # Core fields (required)
    id: str                          # UUID generated by our system
    source: str                      # "pubmed", "clinicaltrials", etc
    source_id: str                   # Original ID from source
    title: str
    abstract: Optional[str]
    publication_date: datetime
    document_type: DocumentType
    
    # Content
    content: Optional[str]           # Full text if available
    summary: Optional[str]           # AI-generated summary
    
    # People
    authors: List[Dict[str, str]]    # [{name, affiliation, orcid}]
    
    # Links & References
    url: str                         # Primary URL
    alternate_urls: List[str]
    doi: Optional[str]
    citations: List[str]             # DOIs or source IDs
    
    # AI-extracted entities (unified across all sources)
    entities: Dict[str, List[Dict]]  # {entity_type: [{value, confidence}]}
    relationships: List[Dict]        # [{subject, predicate, object}]
    key_concepts: List[str]
    
    # Source-specific metadata (flexible JSON)
    metadata: Dict[str, Any]
    
    # System fields
    created_at: datetime
    updated_at: datetime
    processing_status: str           # "pending", "processing", "completed", "failed"
    quality_score: float             # 0-100
    
class AbstractDataSource(ABC):
    """Base class for all data source connectors"""
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        self.api_key = api_key
        self.config = config or {}
        self.rate_limiter = None
        self.cache = None
        
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g., 'pubmed')"""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Category of this source"""
        pass
    
    @property
    @abstractmethod
    def supported_document_types(self) -> List[DocumentType]:
        """What document types this source provides"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """
        Search this data source
        Returns: List of documents in StandardDocument format
        """
        pass
    
    @abstractmethod
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """Fetch a specific document by its source ID"""
        pass
    
    @abstractmethod
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """Attempt to retrieve full text (if available)"""
        pass
    
    @abstractmethod
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert source-specific format to StandardDocument"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Check if API keys, credentials are valid"""
        pass
    
    # Optional: Override for source-specific features
    def supports_full_text(self) -> bool:
        """Does this source provide full text?"""
        return False
    
    def supports_real_time_updates(self) -> bool:
        """Can we poll for new documents?"""
        return True
    
    def get_rate_limits(self) -> Dict:
        """Return rate limit info for this source"""
        return {
            "requests_per_second": 3,
            "requests_per_day": 100000
        }
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for this document"""
        return f"{doc.authors[0]['name']} et al. ({doc.publication_date.year}). {doc.title}. {doc.source}"
```

### **Example Implementation: PubMed Connector**

```python
# services/data-connectors/sources/pubmed_connector.py

from base.abstract_data_source import AbstractDataSource, StandardDocument, SourceType, DocumentType
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp

class PubMedConnector(AbstractDataSource):
    
    @property
    def source_name(self) -> str:
        return "pubmed"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.RESEARCH_PAPER
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.RESEARCH_ARTICLE, DocumentType.PREPRINT]
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search PubMed and return standardized documents"""
        
        # Build PubMed-specific query
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }
        
        if date_from:
            params["mindate"] = date_from.strftime("%Y/%m/%d")
        if date_to:
            params["maxdate"] = date_to.strftime("%Y/%m/%d")
        
        # Fetch IDs
        async with aiohttp.ClientSession() as session:
            async with session.get(esearch_url, params=params) as response:
                data = await response.json()
                pmids = data.get("esearchresult", {}).get("idlist", [])
        
        # Fetch full records
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(efetch_url, params=params) as response:
                xml_data = await response.text()
        
        # Parse XML and transform to StandardDocument
        documents = []
        for article in self._parse_pubmed_xml(xml_data):
            documents.append(self.transform_to_standard(article))
        
        return documents
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """Fetch a specific PubMed article by PMID"""
        # Implementation...
        pass
    
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """Try to get full text from PubMed Central"""
        # Check if available in PMC
        # Implementation...
        return None
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert PubMed XML to StandardDocument"""
        return StandardDocument(
            id=self._generate_uuid(),
            source="pubmed",
            source_id=raw_data.get("pmid"),
            title=raw_data.get("title"),
            abstract=raw_data.get("abstract"),
            publication_date=self._parse_date(raw_data.get("pub_date")),
            document_type=DocumentType.RESEARCH_ARTICLE,
            content=None,  # Usually not available
            summary=None,  # Will be generated by AI
            authors=self._parse_authors(raw_data.get("authors", [])),
            url=f"https://pubmed.ncbi.nlm.nih.gov/{raw_data.get('pmid')}",
            alternate_urls=[],
            doi=raw_data.get("doi"),
            citations=[],
            entities={},  # Will be extracted by AI
            relationships=[],
            key_concepts=[],
            metadata={
                "journal": raw_data.get("journal"),
                "mesh_terms": raw_data.get("mesh_terms", []),
                "publication_types": raw_data.get("pub_types", []),
                "pmcid": raw_data.get("pmcid"),
                "language": raw_data.get("language", "en")
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            processing_status="pending",
            quality_score=0.0
        )
    
    def validate_config(self) -> bool:
        """PubMed doesn't require API key for basic usage"""
        return True
    
    def supports_full_text(self) -> bool:
        return True  # Via PMC for some articles
```

### **Example: ClinicalTrials.gov Connector**

```python
# services/data-connectors/sources/clinicaltrials_connector.py

class ClinicalTrialsConnector(AbstractDataSource):
    
    @property
    def source_name(self) -> str:
        return "clinicaltrials"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.CLINICAL_TRIAL
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.CLINICAL_TRIAL]
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search ClinicalTrials.gov"""
        
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": query,
            "pageSize": min(max_results, 1000),
            "format": "json"
        }
        
        if filters:
            if filters.get("condition"):
                params["query.cond"] = filters["condition"]
            if filters.get("intervention"):
                params["query.intr"] = filters["intervention"]
            if filters.get("status"):
                params["filter.overallStatus"] = filters["status"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                data = await response.json()
        
        documents = []
        for study in data.get("studies", []):
            documents.append(self.transform_to_standard(study))
        
        return documents
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert ClinicalTrials.gov JSON to StandardDocument"""
        protocol = raw_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        status = protocol.get("statusModule", {})
        
        return StandardDocument(
            id=self._generate_uuid(),
            source="clinicaltrials",
            source_id=identification.get("nctId"),
            title=identification.get("briefTitle"),
            abstract=description.get("briefSummary"),
            publication_date=self._parse_date(status.get("startDateStruct", {}).get("date")),
            document_type=DocumentType.CLINICAL_TRIAL,
            content=description.get("detailedDescription"),
            summary=None,
            authors=[],  # Trials have sponsors, not authors
            url=f"https://clinicaltrials.gov/study/{identification.get('nctId')}",
            alternate_urls=[],
            doi=None,
            citations=[],
            entities={},
            relationships=[],
            key_concepts=[],
            metadata={
                "nct_id": identification.get("nctId"),
                "official_title": identification.get("officialTitle"),
                "sponsor": protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
                "phase": protocol.get("designModule", {}).get("phases", []),
                "status": status.get("overallStatus"),
                "enrollment": status.get("enrollmentInfo", {}).get("count"),
                "conditions": protocol.get("conditionsModule", {}).get("conditions", []),
                "interventions": protocol.get("armsInterventionsModule", {}).get("interventions", []),
                "outcomes": protocol.get("outcomesModule", {}),
                "locations": protocol.get("contactsLocationsModule", {}).get("locations", [])
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            processing_status="pending",
            quality_score=0.0
        )
```

---

<a name="ingestion"></a>
# 3️⃣ **UNIFIED INGESTION PIPELINE**

## **Multi-Source Orchestrator**

```python
# services/ingestion-orchestrator/multi_source_orchestrator.py

from typing import List, Dict, Optional
from base.abstract_data_source import AbstractDataSource, StandardDocument
from sources.pubmed_connector import PubMedConnector
from sources.clinicaltrials_connector import ClinicalTrialsConnector
from sources.fda_connector import FDAConnector
# ... import all connectors

class DataSourceRegistry:
    """Registry of all available data sources"""
    
    def __init__(self):
        self.sources: Dict[str, AbstractDataSource] = {}
        self._register_all_sources()
    
    def _register_all_sources(self):
        """Register all available connectors"""
        self.register(PubMedConnector())
        self.register(ClinicalTrialsConnector())
        self.register(FDAConnector())
        # ... register all 38 sources
    
    def register(self, source: AbstractDataSource):
        """Add a data source to the registry"""
        self.sources[source.source_name] = source
    
    def get_source(self, name: str) -> Optional[AbstractDataSource]:
        """Get a specific source by name"""
        return self.sources.get(name)
    
    def get_all_sources(self) -> List[AbstractDataSource]:
        """Get all registered sources"""
        return list(self.sources.values())
    
    def get_sources_by_type(self, source_type: SourceType) -> List[AbstractDataSource]:
        """Get sources by category"""
        return [s for s in self.sources.values() if s.source_type == source_type]

class MultiSourceOrchestrator:
    """Orchestrates ingestion from multiple sources"""
    
    def __init__(self):
        self.registry = DataSourceRegistry()
        self.ai_processor = None  # AI enrichment service
        self.storage = None       # Storage service
    
    async def search_all_sources(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 100
    ) -> Dict[str, List[StandardDocument]]:
        """
        Search across multiple sources in parallel
        Returns: {source_name: [documents]}
        """
        if sources is None:
            sources = list(self.registry.sources.keys())
        
        tasks = []
        for source_name in sources:
            source = self.registry.get_source(source_name)
            if source:
                task = source.search(query, max_results=max_results_per_source)
                tasks.append((source_name, task))
        
        results = {}
        for source_name, task in tasks:
            try:
                docs = await task
                results[source_name] = docs
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                results[source_name] = []
        
        return results
    
    async def ingest_from_source(
        self,
        source_name: str,
        query: str,
        project_space_id: str,
        options: Dict = None
    ) -> Dict:
        """
        Complete ingestion workflow from a single source
        
        Steps:
        1. Fetch from source
        2. Normalize to StandardDocument
        3. AI enrichment (entity extraction, etc)
        4. Store in database
        5. Index for search
        6. Link to knowledge graph
        """
        source = self.registry.get_source(source_name)
        if not source:
            raise ValueError(f"Unknown source: {source_name}")
        
        # Step 1: Fetch
        documents = await source.search(query, max_results=options.get("max_results", 100))
        
        # Step 2: Already normalized (StandardDocument format)
        
        # Step 3: AI Enrichment
        for doc in documents:
            await self._enrich_document(doc, options)
        
        # Step 4-6: Store and index
        for doc in documents:
            await self._store_document(doc, project_space_id)
        
        return {
            "source": source_name,
            "query": query,
            "documents_fetched": len(documents),
            "status": "completed"
        }
    
    async def _enrich_document(self, doc: StandardDocument, options: Dict):
        """Apply AI processing to extract entities, relationships, etc"""
        
        # Extract entities
        text = f"{doc.title} {doc.abstract or ''} {doc.content or ''}"
        doc.entities = await self.ai_processor.extract_entities(text, options.get("model"))
        
        # Extract relationships
        doc.relationships = await self.ai_processor.extract_relationships(text, doc.entities)
        
        # Generate summary if not present
        if not doc.summary and len(text) > 500:
            doc.summary = await self.ai_processor.summarize(text)
        
        # Extract key concepts
        doc.key_concepts = await self.ai_processor.extract_key_concepts(text)
        
        # Calculate quality score
        doc.quality_score = self._calculate_quality_score(doc)
        
        doc.processing_status = "completed"
    
    async def _store_document(self, doc: StandardDocument, project_space_id: str):
        """Store in all relevant databases"""
        
        # 1. PostgreSQL: Metadata
        await self.storage.pg.store_document_metadata(doc, project_space_id)
        
        # 2. Elasticsearch: Full-text search
        await self.storage.es.index_document(doc)
        
        # 3. Neo4j: Knowledge graph
        await self.storage.neo4j.create_document_node(doc)
        await self.storage.neo4j.create_entity_links(doc)
        
        # 4. MinIO: Original if applicable
        if doc.content:
            await self.storage.minio.store_content(doc.id, doc.content)
```

---

<a name="normalization"></a>
# 4️⃣ **DATA NORMALIZATION & ENRICHMENT**

## **Entity Reconciliation Across Sources**

```python
# services/enrichment/cross_source_linker.py

class CrossSourceLinker:
    """Link related entities across different sources"""
    
    async def link_drug_mentions(self, documents: List[StandardDocument]):
        """
        Find the same drug mentioned in different sources
        
        Example:
        - PubMed paper mentions "Aspirin"
        - ChEMBL has compound data for "Aspirin" (CHEMBL25)
        - DrugBank has drug profile for "Aspirin" (DB00945)
        - ClinicalTrials has trials for "Aspirin"
        - FDA has adverse events for "Aspirin"
        
        Link all these together!
        """
        
        drug_entities = {}
        for doc in documents:
            for entity_type, entities in doc.entities.items():
                if entity_type in ["DRUG", "CHEMICAL", "COMPOUND"]:
                    for entity in entities:
                        drug_name = self._normalize_drug_name(entity["value"])
                        if drug_name not in drug_entities:
                            drug_entities[drug_name] = []
                        drug_entities[drug_name].append({
                            "document_id": doc.id,
                            "source": doc.source,
                            "context": entity.get("context")
                        })
        
        # Create cross-source links in Neo4j
        for drug_name, mentions in drug_entities.items():
            await self._create_drug_hub(drug_name, mentions)
    
    async def _create_drug_hub(self, drug_name: str, mentions: List[Dict]):
        """Create a central node for a drug with links to all mentions"""
        
        # Create DrugHub node
        cypher = """
        MERGE (d:DrugHub {name: $drug_name})
        SET d.normalized_name = $normalized_name
        RETURN d
        """
        await neo4j.execute(cypher, drug_name=drug_name, normalized_name=drug_name.lower())
        
        # Link to all documents mentioning this drug
        for mention in mentions:
            cypher = """
            MATCH (d:DrugHub {name: $drug_name})
            MATCH (doc:Document {id: $doc_id})
            MERGE (doc)-[r:MENTIONS]->(d)
            SET r.source = $source,
                r.context = $context
            """
            await neo4j.execute(
                cypher,
                drug_name=drug_name,
                doc_id=mention["document_id"],
                source=mention["source"],
                context=mention.get("context")
            )
```

---

<a name="storage"></a>
# 5️⃣ **STORAGE STRATEGY**

## **Database Schema for Multi-Source**

```sql
-- PostgreSQL: Core metadata and source management

CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'pubmed', 'clinicaltrials', etc
    display_name VARCHAR(200),
    source_type VARCHAR(50),             -- 'research_paper', 'clinical_trial', etc
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'disabled', 'maintenance'
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_second INTEGER,
    last_sync_at TIMESTAMP,
    config JSONB,                        -- Source-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE source_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id),
    project_space_id UUID,
    query TEXT,
    filters JSONB,
    status VARCHAR(20),                  -- 'pending', 'running', 'completed', 'failed'
    documents_fetched INTEGER,
    documents_processed INTEGER,
    documents_failed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_by UUID
);

CREATE TABLE documents (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES data_sources(id),
    source_document_id VARCHAR(200),     -- Original ID from source (PMID, NCT ID, etc)
    project_space_id UUID,
    title TEXT,
    abstract TEXT,
    document_type VARCHAR(50),
    publication_date TIMESTAMP,
    authors JSONB,
    url TEXT,
    doi VARCHAR(200),
    processing_status VARCHAR(20),
    quality_score FLOAT,
    metadata JSONB,                      -- Source-specific fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, source_document_id)  -- Prevent duplicates
);

CREATE TABLE document_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    entity_type VARCHAR(50),             -- 'DRUG', 'DISEASE', 'GENE', etc
    entity_value TEXT,
    normalized_value TEXT,               -- Standardized name
    confidence FLOAT,
    context TEXT,
    start_pos INTEGER,
    end_pos INTEGER
);

CREATE TABLE cross_source_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50),
    normalized_value TEXT,
    source_1 VARCHAR(100),
    source_id_1 VARCHAR(200),
    source_2 VARCHAR(100),
    source_id_2 VARCHAR(200),
    link_type VARCHAR(50),               -- 'same_entity', 'related', 'contradicts'
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_documents_source ON documents(source_id);
CREATE INDEX idx_documents_space ON documents(project_space_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_date ON documents(publication_date);
CREATE INDEX idx_entities_document ON document_entities(document_id);
CREATE INDEX idx_entities_type ON document_entities(entity_type);
CREATE INDEX idx_entities_value ON document_entities(normalized_value);
```

---

<a name="consumption"></a>
# 6️⃣ **QUERY & CONSUMPTION LAYER**

## **Unified Search API**

```python
# services/api-gateway/routes/unified_search.py

from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter()

@router.get("/unified-search")
async def unified_search(
    q: str = Query(..., description="Search query"),
    sources: Optional[List[str]] = Query(None, description="Specific sources to search"),
    document_types: Optional[List[str]] = Query(None, description="Filter by document type"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    entities: Optional[List[str]] = Query(None, description="Filter by entity (e.g., 'Aspirin')"),
    page: int = Query(0, ge=0),
    size: int = Query(25, ge=1, le=100)
):
    """
    Unified search across ALL data sources
    
    Example:
    GET /unified-search?q=cancer+immunotherapy&sources=pubmed,clinicaltrials&date_from=2024-01-01
    
    Returns:
    {
        "query": "cancer immunotherapy",
        "total": 15234,
        "sources": {
            "pubmed": 10000,
            "clinicaltrials": 4234,
            "fda": 1000
        },
        "results": [
            {
                "id": "uuid",
                "source": "pubmed",
                "source_id": "PMID12345",
                "title": "...",
                "abstract": "...",
                "score": 0.95,
                "highlight": "...cancer <em>immunotherapy</em>...",
                "url": "..."
            },
            ...
        ],
        "facets": {
            "source": {"pubmed": 100, "clinicaltrials": 50},
            "document_type": {"research_article": 120, "clinical_trial": 30},
            "year": {"2024": 80, "2023": 70},
            "entity_DRUG": {"Pembrolizumab": 45, "Nivolumab": 30}
        }
    }
    """
    
    # Build Elasticsearch query that searches across all sources
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["title^3", "abstract^2", "content"]
                        }
                    }
                ],
                "filter": []
            }
        },
        "from": page * size,
        "size": size,
        "aggs": {
            "by_source": {"terms": {"field": "source.keyword", "size": 50}},
            "by_type": {"terms": {"field": "document_type.keyword", "size": 20}},
            "by_year": {"date_histogram": {"field": "publication_date", "calendar_interval": "year"}},
            "top_drugs": {"terms": {"field": "entities.DRUG.normalized_value.keyword", "size": 20}}
        },
        "highlight": {
            "fields": {
                "title": {},
                "abstract": {},
                "content": {}
            }
        }
    }
    
    # Apply filters
    if sources:
        es_query["query"]["bool"]["filter"].append({"terms": {"source.keyword": sources}})
    
    if document_types:
        es_query["query"]["bool"]["filter"].append({"terms": {"document_type.keyword": document_types}})
    
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        es_query["query"]["bool"]["filter"].append({"range": {"publication_date": date_range}})
    
    if entities:
        # Search for specific entities
        es_query["query"]["bool"]["filter"].append({
            "nested": {
                "path": "entities",
                "query": {
                    "terms": {"entities.normalized_value.keyword": entities}
                }
            }
        })
    
    # Execute search
    results = await elasticsearch.search(index="documents", body=es_query)
    
    return {
        "query": q,
        "total": results["hits"]["total"]["value"],
        "sources": {agg["key"]: agg["doc_count"] for agg in results["aggregations"]["by_source"]["buckets"]},
        "results": [transform_hit(hit) for hit in results["hits"]["hits"]],
        "facets": {
            "source": {agg["key"]: agg["doc_count"] for agg in results["aggregations"]["by_source"]["buckets"]},
            "document_type": {agg["key"]: agg["doc_count"] for agg in results["aggregations"]["by_type"]["buckets"]},
            "year": {agg["key_as_string"]: agg["doc_count"] for agg in results["aggregations"]["by_year"]["buckets"]},
            "entity_DRUG": {agg["key"]: agg["doc_count"] for agg in results["aggregations"]["top_drugs"]["buckets"]}
        }
    }
```

---

<a name="ui-ux"></a>
# 7️⃣ **UI/UX DESIGN FOR MULTI-SOURCE**

## **Design Principles**

1. **Progressive Disclosure**: Start simple, reveal complexity as needed
2. **Source Agnostic**: User doesn't need to know about sources initially
3. **Smart Defaults**: Auto-select best sources based on query
4. **Visual Hierarchy**: Clear distinction between sources in results
5. **Configurability**: Power users can fine-tune everything

## **UI Component Structure**

```
┌─────────────────────────────────────────────────────────────────┐
│  📍 NAVIGATION: Data Sources                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Dashboard] [Search All] [Configure Sources] [Sync Jobs]       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  🔍 UNIFIED SEARCH PAGE                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  🔍  Search across all sources...                      │    │
│  │                                                         │    │
│  │  [Advanced Options ▼]                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  💡 SMART SOURCE SELECTOR (Auto-enabled)               │    │
│  │                                                         │    │
│  │  Based on your query "cancer immunotherapy", we'll     │    │
│  │  search:                                                │    │
│  │  ✓ PubMed (research papers)                            │    │
│  │  ✓ ClinicalTrials.gov (trials)                         │    │
│  │  ✓ FDA OpenFDA (safety data)                           │    │
│  │                                                         │    │
│  │  [Customize Sources]                                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FILTERS (Sidebar)                                       │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  📊 SOURCES (15,234 total)                              │   │
│  │  ☑ PubMed (10,000)                                      │   │
│  │  ☑ ClinicalTrials (4,234)                               │   │
│  │  ☑ FDA (1,000)                                          │   │
│  │  ☐ ChEMBL (234)                                         │   │
│  │  ☐ Patents (156)                                        │   │
│  │  [+ Show 33 more sources]                               │   │
│  │                                                          │   │
│  │  📄 DOCUMENT TYPE                                       │   │
│  │  ☑ Research Article (8,500)                             │   │
│  │  ☑ Clinical Trial (4,234)                               │   │
│  │  ☑ Drug Label (1,000)                                   │   │
│  │  ☐ Patent (500)                                         │   │
│  │                                                          │   │
│  │  📅 DATE RANGE                                          │   │
│  │  [2020-01-01] to [2025-12-31]                          │   │
│  │                                                          │   │
│  │  🏷️ TOP ENTITIES                                        │   │
│  │  💊 Pembrolizumab (450)                                 │   │
│  │  💊 Nivolumab (320)                                     │   │
│  │  🦠 Melanoma (280)                                      │   │
│  │  🦠 Lung Cancer (250)                                   │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RESULTS (Grouped by Source or Mixed)                   │   │
│  │                                                          │   │
│  │  [Group by Source ▼] [Sort: Relevance ▼]  [Grid|List]  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  ━━━ PUBMED (10,000 results) ━━━                        │   │
│  │                                                          │   │
│  │  📄 [Pubmed] Pembrolizumab in Advanced Melanoma         │   │
│  │     PMID: 12345678 | 2024-03-15 | Cited: 45            │   │
│  │     Smith J, et al. | New England Journal of Medicine   │   │
│  │                                                          │   │
│  │     "...combination of <mark>cancer immunotherapy</mark>│   │
│  │     showed significant improvement..."                   │   │
│  │                                                          │   │
│  │     💊 Entities: Pembrolizumab, Melanoma, PD-1         │   │
│  │                                                          │   │
│  │     [View Full] [Add to Project] [Cite] [Related]      │   │
│  │                                                          │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │                                                          │   │
│  │  ━━━ CLINICALTRIALS.GOV (4,234 results) ━━━             │   │
│  │                                                          │   │
│  │  🔬 [Trial] Phase III Study of Pembrolizumab            │   │
│  │     NCT04567890 | Status: Recruiting | Phase III        │   │
│  │     Sponsor: Merck | Enrollment: 500 patients           │   │
│  │                                                          │   │
│  │     Primary Outcome: Overall Survival                    │   │
│  │     Condition: Advanced Melanoma                         │   │
│  │     Intervention: Pembrolizumab 200mg IV Q3W            │   │
│  │                                                          │   │
│  │     📍 Locations: 45 sites (USA, EU)                    │   │
│  │                                                          │   │
│  │     [View Full] [Track Trial] [Find Sites] [Related]   │   │
│  │                                                          │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │                                                          │   │
│  │  ━━━ FDA OPENFDA (1,000 results) ━━━                    │   │
│  │                                                          │   │
│  │  ⚠️ [FDA] Adverse Event Report: Pembrolizumab           │   │
│  │     Report ID: 12345678 | Date: 2024-02-10             │   │
│  │     Serious: Yes | Outcome: Hospitalization             │   │
│  │                                                          │   │
│  │     Reaction: Immune-related colitis                     │   │
│  │     Patient: 65yo Male, Melanoma patient                │   │
│  │     Concomitant: Nivolumab                              │   │
│  │                                                          │   │
│  │     [View Full] [Similar Cases] [Safety Profile]       │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## **Configure Sources Page**

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ DATA SOURCES CONFIGURATION                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [All Sources] [Enabled (15)] [Disabled (23)] [Needs Setup (5)]│
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  🔍 Filter sources: [Search by name or type...]        │    │
│  │  📊 Category: [All ▼] [Research ▼] [Clinical ▼] ...   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ━━━ RESEARCH PAPERS ━━━                                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ✅ PubMed                                 [Configure]  │    │
│  │  📚 NCBI E-utilities API                                │    │
│  │                                                         │    │
│  │  Status: ✓ Active | Last Sync: 2 hours ago             │    │
│  │  Documents: 1,234 indexed                               │    │
│  │  Rate Limit: 3/sec (no API key)                        │    │
│  │                                                         │    │
│  │  [Sync Now] [View Logs] [Disable] [Settings ⚙️]       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ✅ Europe PMC                             [Configure]  │    │
│  │  📚 European PubMed Central                             │    │
│  │                                                         │    │
│  │  Status: ✓ Active | Last Sync: 1 day ago               │    │
│  │  Documents: 456 indexed                                 │    │
│  │                                                         │    │
│  │  [Sync Now] [View Logs] [Disable] [Settings ⚙️]       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ⚪ Semantic Scholar                       [Enable]     │    │
│  │  🤖 AI-powered research database                        │    │
│  │                                                         │    │
│  │  Status: Not enabled                                    │    │
│  │  Cost: FREE                                             │    │
│  │  Setup Time: ~5 minutes                                 │    │
│  │                                                         │    │
│  │  💡 Why add? AI-powered recommendations, 200M+ papers  │    │
│  │                                                         │    │
│  │  [Quick Setup] [Learn More]                            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ━━━ CLINICAL TRIALS ━━━                                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ✅ ClinicalTrials.gov                     [Configure]  │    │
│  │  🔬 US National Library of Medicine                     │    │
│  │                                                         │    │
│  │  Status: ✓ Active | Auto-sync: Daily at 2 AM           │    │
│  │  Documents: 789 trials indexed                          │    │
│  │                                                         │    │
│  │  📊 Breakdown:                                          │    │
│  │     • Recruiting: 234                                   │    │
│  │     • Completed: 456                                    │    │
│  │     • Terminated: 89                                    │    │
│  │                                                         │    │
│  │  [Sync Now] [View Logs] [Disable] [Settings ⚙️]       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ━━━ REGULATORY & SAFETY ━━━                                    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ✅ FDA OpenFDA                            [Configure]  │    │
│  │  ⚕️ Food and Drug Administration                        │    │
│  │                                                         │    │
│  │  Status: ✓ Active | Auto-sync: Hourly                  │    │
│  │  Documents: 3,456 events, 234 labels indexed            │    │
│  │                                                         │    │
│  │  Endpoints enabled:                                     │    │
│  │  ✓ Drug Adverse Events                                 │    │
│  │  ✓ Drug Labels                                          │    │
│  │  ☐ Device Recalls (Enable?)                            │    │
│  │  ☐ Food Recalls (Enable?)                              │    │
│  │                                                         │    │
│  │  [Sync Now] [View Logs] [Disable] [Settings ⚙️]       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ━━━ CHEMICALS & COMPOUNDS ━━━                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  🟡 ChEMBL                                 [Setup Req'd]│    │
│  │  🧪 EMBL-EBI Bioactivity Database                      │    │
│  │                                                         │    │
│  │  Status: ⚠️ Not configured                              │    │
│  │  Cost: FREE                                             │    │
│  │  API Key: Required (free registration)                  │    │
│  │                                                         │    │
│  │  📊 What you'll get:                                    │    │
│  │     • 2.3M+ compounds                                   │    │
│  │     • 19M+ bioactivity data points                      │    │
│  │     • Drug targets & mechanisms                         │    │
│  │                                                         │    │
│  │  [Start Setup Wizard] [Learn More]                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [+ Add Custom Data Source]  [Import Configuration]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## **Source Setup Wizard (Example: ChEMBL)**

```
┌─────────────────────────────────────────────────────────────────┐
│  🧙 CHEMBL SETUP WIZARD                              Step 1 of 3 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📝 Get Your API Key                                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ChEMBL is FREE but requires registration.              │    │
│  │                                                         │    │
│  │  1. Visit: https://www.ebi.ac.uk/chembl/              │    │
│  │  2. Click "Register" (top right)                        │    │
│  │  3. Fill out the form (2 minutes)                       │    │
│  │  4. Copy your API key from your profile                │    │
│  │                                                         │    │
│  │  [Open ChEMBL Registration →]                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Enter Your API Key:                                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  [___________________________________________]          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ☐ I don't have an API key (skip for now, limited access)      │
│                                                                  │
│  [Cancel]                             [Test Connection] [Next →]│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  🧙 CHEMBL SETUP WIZARD                              Step 2 of 3 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⚙️ Configure Sync Options                                      │
│                                                                  │
│  What do you want to sync from ChEMBL?                          │
│                                                                  │
│  ☑ Compound Data                                                │
│     └─ Names, structures, properties                            │
│                                                                  │
│  ☑ Bioactivity Data                                             │
│     └─ Assays, IC50, EC50 values                               │
│                                                                  │
│  ☑ Drug Targets                                                 │
│     └─ Proteins, genes, mechanisms                              │
│                                                                  │
│  ☐ Clinical Trials (from ChEMBL)                                │
│     └─ You already have ClinicalTrials.gov enabled              │
│                                                                  │
│  How often should we sync?                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  (•) Weekly (recommended for ChEMBL)                    │    │
│  │  ( ) Daily                                              │    │
│  │  ( ) Monthly                                            │    │
│  │  ( ) Manual only                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [← Back]                                             [Next →]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  🧙 CHEMBL SETUP WIZARD                              Step 3 of 3 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🚀 Ready to Connect!                                           │
│                                                                  │
│  Summary:                                                        │
│  ✓ API Key: Verified                                           │
│  ✓ Sync: Weekly (Sundays at 3 AM)                              │
│  ✓ Data: Compounds, Bioactivity, Targets                       │
│                                                                  │
│  Initial Sync:                                                   │
│  We'll perform an initial sync of:                              │
│  • ~2,000 compounds relevant to your existing data             │
│  • Estimated time: 10-15 minutes                                │
│  • You'll get a notification when complete                      │
│                                                                  │
│  ☑ Start initial sync now                                       │
│  ☐ Schedule for tonight (3 AM)                                  │
│                                                                  │
│  [← Back]                      [Finish Setup & Start Sync! 🎉]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

<a name="roadmap"></a>
# 8️⃣ **IMPLEMENTATION ROADMAP**

## **Phase 1: Foundation (Weeks 1-2)**

### **Week 1: Architecture Setup**
- [ ] Create `AbstractDataSource` base class
- [ ] Implement `StandardDocument` schema
- [ ] Set up `DataSourceRegistry`
- [ ] Create database schema for multi-source
- [ ] Build `MultiSourceOrchestrator`

### **Week 2: UI Foundation**
- [ ] Design unified search page mockups
- [ ] Create reusable components:
  - [ ] `SourceCard` - Display source info
  - [ ] `DocumentCard` - Display results (source-agnostic)
  - [ ] `SourceFilter` - Filter by source
  - [ ] `SourceSelector` - Multi-source picker
- [ ] Build "Configure Sources" page structure

## **Phase 2: First 5 Sources (Weeks 3-6)**

### **Week 3: ClinicalTrials.gov**
- [ ] Implement `ClinicalTrialsConnector`
- [ ] Transform to `StandardDocument`
- [ ] Add source-specific metadata handling
- [ ] Create UI for trial-specific fields
- [ ] Test end-to-end ingestion

### **Week 4: FDA OpenFDA**
- [ ] Implement `FDAConnector` (adverse events)
- [ ] Handle multiple FDA endpoints
- [ ] Create safety alert visualization
- [ ] Link drugs across sources
- [ ] Test adverse event tracking

### **Week 5: ChEMBL**
- [ ] Implement `ChEMBLConnector`
- [ ] Chemical structure handling
- [ ] Bioactivity data integration
- [ ] Create compound profile page
- [ ] Link to PubMed compounds

### **Week 6: Semantic Scholar + Europe PMC**
- [ ] Implement `SemanticScholarConnector`
- [ ] Implement `EuropePMCConnector`
- [ ] Full-text retrieval logic
- [ ] AI recommendation integration
- [ ] Citation graph visualization

## **Phase 3: Cross-Source Intelligence (Weeks 7-8)**

### **Week 7: Entity Linking**
- [ ] Implement `CrossSourceLinker`
- [ ] Drug name normalization
- [ ] Create knowledge graph hubs
- [ ] Build "360° Drug View" page
  - Shows same drug across all sources
  - PubMed papers + Trials + FDA events + ChEMBL data

### **Week 8: Unified Search**
- [ ] Complete unified search API
- [ ] Faceted navigation
- [ ] Source grouping/mixing options
- [ ] Export functionality
- [ ] Polish UI

## **Phase 4: Batch Integration (Weeks 9-12)**

Add 5 sources per week using the established pattern:

### **Week 9: Patents & Financial**
- [ ] USPTO Patents
- [ ] EPO Patents
- [ ] SEC EDGAR

### **Week 10: Genomics**
- [ ] NCBI Gene
- [ ] ClinVar
- [ ] UniProt

### **Week 11: More Research**
- [ ] BioRxiv
- [ ] CrossRef
- [ ] NIH RePORTER

### **Week 12: Advanced**
- [ ] PubChem
- [ ] Protein Data Bank
- [ ] Materials Project

## **Phase 5: Polish & Scale (Weeks 13-14)**

### **Week 13: Performance**
- [ ] Query optimization
- [ ] Caching strategy
- [ ] Rate limit handling
- [ ] Error recovery

### **Week 14: UX Polish**
- [ ] Onboarding tour
- [ ] Setup wizards for all sources
- [ ] Analytics dashboard
- [ ] Documentation

---

# 🎯 **SUCCESS METRICS**

## **Technical Metrics**
- ✅ 15+ sources integrated (Phase 1-2)
- ✅ <500ms unified search response time
- ✅ 99.9% uptime for all connectors
- ✅ <5% duplicate documents across sources
- ✅ 95%+ entity linking accuracy

## **User Metrics**
- ✅ <30 seconds to configure a new source
- ✅ Users search 3+ sources per query (on average)
- ✅ 50%+ of searches use cross-source filters
- ✅ 4.5+ user satisfaction score
- ✅ 80%+ feature adoption rate

## **Business Metrics**
- ✅ 10x data coverage vs competitors
- ✅ "Single source of truth" positioning
- ✅ 30%+ price premium justification
- ✅ 90%+ customer retention

---

# 📝 **NEXT STEPS**

1. **Review this architecture** - Does it align with your vision?
2. **Prioritize sources** - Confirm the first 5 to implement
3. **Design approval** - Review UI/UX mockups
4. **Start Phase 1** - Build the foundation (2 weeks)
5. **Iterate** - Add sources incrementally

---

**Ready to start building? Which phase should we tackle first?**

