"""
Literature Automation Data Models
Pydantic models for literature search, classification, and ICSR extraction
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class LiteratureSource(str, Enum):
    PUBMED = "pubmed"
    EMBASE = "embase"
    COCHRANE = "cochrane"
    CUSTOM = "custom"

class ArticleClassification(str, Enum):
    ICSR = "ICSR"
    NON_ICSR = "Non-ICSR"
    SAFETY_INFORMATION = "Safety Information"
    REJECTED = "Rejected"

class LiteratureSearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    sources: List[LiteratureSource] = Field(default=[LiteratureSource.PUBMED], description="Literature sources to search")
    max_results: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter (from_date, to_date)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional search filters")

class LiteratureArticle(BaseModel):
    id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    abstract: Optional[str] = Field(None, description="Article abstract")
    authors: List[str] = Field(default=[], description="List of authors")
    journal: Optional[str] = Field(None, description="Journal name")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    url: Optional[str] = Field(None, description="Article URL")
    source: LiteratureSource = Field(..., description="Literature source")
    keywords: List[str] = Field(default=[], description="Article keywords")
    mesh_terms: List[str] = Field(default=[], description="MeSH terms")
    content: Optional[str] = Field(None, description="Full article content")

class LiteratureSearchResponse(BaseModel):
    success: bool = Field(..., description="Search success status")
    results: List[LiteratureArticle] = Field(default=[], description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="Search metadata")
    errors: List[str] = Field(default=[], description="Search errors")

class ArticleClassificationRequest(BaseModel):
    article_id: str = Field(..., description="Article identifier")
    title: str = Field(..., description="Article title")
    abstract: Optional[str] = Field(None, description="Article abstract")
    content: Optional[str] = Field(None, description="Full article content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional article metadata")

class ClassificationResult(BaseModel):
    category: ArticleClassification = Field(..., description="Classification category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: str = Field(..., description="Classification reasoning")
    supporting_evidence: List[str] = Field(default=[], description="Supporting evidence for classification")

class ArticleClassificationResponse(BaseModel):
    success: bool = Field(..., description="Classification success status")
    classification: ArticleClassification = Field(..., description="Article classification")
    confidence: float = Field(..., description="Classification confidence")
    reasoning: str = Field(..., description="Classification reasoning")
    supporting_evidence: List[str] = Field(default=[], description="Supporting evidence")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class ICSRExtractionRequest(BaseModel):
    article_id: str = Field(..., description="Article identifier")
    title: str = Field(..., description="Article title")
    abstract: Optional[str] = Field(None, description="Article abstract")
    content: str = Field(..., description="Full article content")
    article_metadata: Optional[Dict[str, Any]] = Field(None, description="Article metadata")

class ICSRExtractionResponse(BaseModel):
    success: bool = Field(..., description="Extraction success status")
    extracted_data: Dict[str, Any] = Field(..., description="Extracted ICSR data")
    confidence: float = Field(..., description="Extraction confidence score")
    validation_errors: List[str] = Field(default=[], description="Data validation errors")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
