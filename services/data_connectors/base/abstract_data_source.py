"""
Abstract Data Source Base Class
===============================

This module defines the base class and interfaces for all external data source connectors.
Every data source (PubMed, ClinicalTrials.gov, FDA, etc.) must implement this interface
to ensure consistent behavior across the platform.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

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
    SOCIAL = "social"
    CUSTOM = "custom"

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
    EMAIL = "email"
    PRESENTATION = "presentation"
    REPORT = "report"
    OTHER = "other"

@dataclass
class Author:
    """Author information"""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    email: Optional[str] = None
    position: Optional[int] = None  # Order in author list

@dataclass
class Entity:
    """Extracted entity from document"""
    value: str
    normalized_value: str
    entity_type: str  # DRUG, DISEASE, GENE, etc.
    confidence: float
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    context: Optional[str] = None
    source: Optional[str] = None  # Which AI model extracted this

@dataclass
class Relationship:
    """Relationship between entities"""
    subject: str
    predicate: str
    object: str
    confidence: float
    context: Optional[str] = None
    source: Optional[str] = None

@dataclass
class StandardDocument:
    """
    Unified document format for ALL sources
    
    This is the core data structure that every external source
    must transform their data into. This ensures consistent
    processing, storage, and retrieval across the platform.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""  # "pubmed", "clinicaltrials", "fda", etc.
    source_id: str = ""  # Original ID from source (PMID, NCT ID, etc)
    project_space_id: Optional[str] = None
    
    # Basic content
    title: str = ""
    abstract: Optional[str] = None
    content: Optional[str] = None  # Full text if available
    summary: Optional[str] = None  # AI-generated summary
    
    # Classification
    document_type: DocumentType = DocumentType.OTHER
    language: str = "en"
    
    # Temporal
    publication_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # People
    authors: List[Author] = field(default_factory=list)
    
    # Links and references
    url: str = ""
    alternate_urls: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    citations: List[str] = field(default_factory=list)  # DOIs or source IDs
    
    # AI-extracted intelligence
    entities: Dict[str, List[Entity]] = field(default_factory=dict)  # {entity_type: [entities]}
    relationships: List[Relationship] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Quality and processing
    quality_score: float = 0.0  # 0-100
    processing_status: str = "pending"  # pending, processing, completed, failed
    processing_errors: List[str] = field(default_factory=list)
    
    # Source-specific metadata (flexible JSON)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # System fields
    version: int = 1
    is_deleted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "project_space_id": self.project_space_id,
            "title": self.title,
            "abstract": self.abstract,
            "content": self.content,
            "summary": self.summary,
            "document_type": self.document_type.value,
            "language": self.language,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "authors": [
                {
                    "name": author.name,
                    "affiliation": author.affiliation,
                    "orcid": author.orcid,
                    "email": author.email,
                    "position": author.position
                } for author in self.authors
            ],
            "url": self.url,
            "alternate_urls": self.alternate_urls,
            "doi": self.doi,
            "pmid": self.pmid,
            "pmcid": self.pmcid,
            "citations": self.citations,
            "entities": {
                entity_type: [
                    {
                        "value": entity.value,
                        "normalized_value": entity.normalized_value,
                        "entity_type": entity.entity_type,
                        "confidence": entity.confidence,
                        "start_pos": entity.start_pos,
                        "end_pos": entity.end_pos,
                        "context": entity.context,
                        "source": entity.source
                    } for entity in entities
                ] for entity_type, entities in self.entities.items()
            },
            "relationships": [
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "confidence": rel.confidence,
                    "context": rel.context,
                    "source": rel.source
                } for rel in self.relationships
            ],
            "key_concepts": self.key_concepts,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "processing_status": self.processing_status,
            "processing_errors": self.processing_errors,
            "metadata": self.metadata,
            "version": self.version,
            "is_deleted": self.is_deleted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardDocument':
        """Create from dictionary"""
        # Handle authors
        authors = []
        for author_data in data.get("authors", []):
            authors.append(Author(
                name=author_data["name"],
                affiliation=author_data.get("affiliation"),
                orcid=author_data.get("orcid"),
                email=author_data.get("email"),
                position=author_data.get("position")
            ))
        
        # Handle entities
        entities = {}
        for entity_type, entity_list in data.get("entities", {}).items():
            entities[entity_type] = [
                Entity(
                    value=entity_data["value"],
                    normalized_value=entity_data["normalized_value"],
                    entity_type=entity_data["entity_type"],
                    confidence=entity_data["confidence"],
                    start_pos=entity_data.get("start_pos"),
                    end_pos=entity_data.get("end_pos"),
                    context=entity_data.get("context"),
                    source=entity_data.get("source")
                ) for entity_data in entity_list
            ]
        
        # Handle relationships
        relationships = []
        for rel_data in data.get("relationships", []):
            relationships.append(Relationship(
                subject=rel_data["subject"],
                predicate=rel_data["predicate"],
                object=rel_data["object"],
                confidence=rel_data["confidence"],
                context=rel_data.get("context"),
                source=rel_data.get("source")
            ))
        
        # Handle dates
        publication_date = None
        if data.get("publication_date"):
            publication_date = datetime.fromisoformat(data["publication_date"].replace('Z', '+00:00'))
        
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            source=data["source"],
            source_id=data["source_id"],
            project_space_id=data.get("project_space_id"),
            title=data["title"],
            abstract=data.get("abstract"),
            content=data.get("content"),
            summary=data.get("summary"),
            document_type=DocumentType(data.get("document_type", "other")),
            language=data.get("language", "en"),
            publication_date=publication_date,
            created_at=created_at,
            updated_at=updated_at,
            authors=authors,
            url=data.get("url", ""),
            alternate_urls=data.get("alternate_urls", []),
            doi=data.get("doi"),
            pmid=data.get("pmid"),
            pmcid=data.get("pmcid"),
            citations=data.get("citations", []),
            entities=entities,
            relationships=relationships,
            key_concepts=data.get("key_concepts", []),
            tags=data.get("tags", []),
            quality_score=data.get("quality_score", 0.0),
            processing_status=data.get("processing_status", "pending"),
            processing_errors=data.get("processing_errors", []),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            is_deleted=data.get("is_deleted", False)
        )

class AbstractDataSource(ABC):
    """
    Base class for all data source connectors
    
    Every external data source must implement this interface to ensure
    consistent behavior across the platform. This includes:
    - Standardized search interface
    - Unified document format (StandardDocument)
    - Error handling and rate limiting
    - Caching strategies
    - Configuration validation
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        self.api_key = api_key
        self.config = config or {}
        self.rate_limiter = None
        self.cache = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup source-specific logging"""
        self.logger = logging.getLogger(f"data_connector.{self.source_name}")
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Unique identifier for this source
        
        Examples:
        - "pubmed"
        - "clinicaltrials"
        - "fda_openfda"
        - "chembl"
        """
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display"""
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
    
    @property
    def description(self) -> str:
        """Description of this data source"""
        return f"{self.display_name} data connector"
    
    @property
    def is_active(self) -> bool:
        """Is this source currently active and available?"""
        return True
    
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
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            filters: Source-specific filters (e.g., {"condition": "cancer"})
            date_from: Start date for filtering
            date_to: End date for filtering
            
        Returns:
            List of documents in StandardDocument format
            
        Raises:
            DataSourceError: If search fails
            RateLimitError: If rate limit exceeded
            AuthenticationError: If API key invalid
        """
        pass
    
    @abstractmethod
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific document by its source ID
        
        Args:
            source_id: Original ID from the source (PMID, NCT ID, etc)
            
        Returns:
            Document in StandardDocument format
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DataSourceError: If fetch fails
        """
        pass
    
    @abstractmethod
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """
        Attempt to retrieve full text (if available)
        
        Args:
            source_id: Original ID from the source
            
        Returns:
            Full text content or None if not available
        """
        pass
    
    @abstractmethod
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """
        Convert source-specific format to StandardDocument
        
        This is the core transformation logic that converts
        each source's unique data format into our unified
        StandardDocument format.
        
        Args:
            raw_data: Raw data from the source API
            
        Returns:
            StandardDocument instance
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Check if API keys, credentials are valid
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    # Optional methods that sources can override
    
    def supports_full_text(self) -> bool:
        """Does this source provide full text?"""
        return False
    
    def supports_real_time_updates(self) -> bool:
        """Can we poll for new documents?"""
        return True
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Return rate limit info for this source"""
        return {
            "requests_per_second": 3,
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for this document"""
        if doc.authors:
            first_author = doc.authors[0].name
            if len(doc.authors) > 1:
                author_str = f"{first_author} et al."
            else:
                author_str = first_author
        else:
            author_str = "Unknown"
        
        year = doc.publication_date.year if doc.publication_date else "Unknown"
        return f"{author_str} ({year}). {doc.title}. {self.display_name}"
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to this source"""
        return {
            "has_abstract": bool(doc.abstract),
            "has_full_text": bool(doc.content),
            "has_doi": bool(doc.doi),
            "has_authors": len(doc.authors) > 0,
            "has_citations": len(doc.citations) > 0,
            "source_quality": "high" if self.source_name in ["pubmed", "clinicaltrials"] else "medium"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the source is healthy and accessible
        
        Returns:
            Health status information
        """
        try:
            # Try a simple search to verify connectivity
            test_results = await self.search("test", max_results=1)
            return {
                "status": "healthy",
                "response_time_ms": 0,  # Would measure actual time
                "last_check": datetime.now().isoformat(),
                "test_query_results": len(test_results)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this source"""
        return {
            "name": self.source_name,
            "display_name": self.display_name,
            "type": self.source_type.value,
            "description": self.description,
            "document_types": [dt.value for dt in self.supported_document_types],
            "supports_full_text": self.supports_full_text(),
            "supports_real_time": self.supports_real_time_updates(),
            "rate_limits": self.get_rate_limits(),
            "is_active": self.is_active,
            "config_valid": self.validate_config()
        }

# Custom exceptions for data source errors

class DataSourceError(Exception):
    """Base exception for data source errors"""
    pass

class AuthenticationError(DataSourceError):
    """API authentication failed"""
    pass

class RateLimitError(DataSourceError):
    """Rate limit exceeded"""
    pass

class DocumentNotFoundError(DataSourceError):
    """Document not found in source"""
    pass

class ConfigurationError(DataSourceError):
    """Invalid configuration"""
    pass

class NetworkError(DataSourceError):
    """Network connectivity error"""
    pass
