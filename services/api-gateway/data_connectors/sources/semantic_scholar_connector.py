"""
Semantic Scholar Data Connector
===============================

Connector for the Semantic Scholar API (https://api.semanticscholar.org/).
Provides access to 200M+ research papers with AI-powered features.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import aiohttp
import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import json

from ..base.abstract_data_source import (
    AbstractDataSource, StandardDocument, SourceType, DocumentType, 
    Author, Entity, Relationship, DataSourceError, NetworkError
)

logger = logging.getLogger(__name__)

class SemanticScholarConnector(AbstractDataSource):
    """
    Semantic Scholar data connector
    
    Provides access to:
    - 200M+ research papers
    - AI-powered recommendations
    - Citation graphs
    - Author profiles
    - Paper abstracts and full text (when available)
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.api_key = api_key  # Optional for Semantic Scholar
    
    @property
    def source_name(self) -> str:
        return "semanticscholar"
    
    @property
    def display_name(self) -> str:
        return "Semantic Scholar"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.RESEARCH_PAPER
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.RESEARCH_ARTICLE, DocumentType.PREPRINT]
    
    @property
    def description(self) -> str:
        return "AI-powered research tool for scientific literature with 200M+ papers and intelligent recommendations"
    
    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "requests_per_second": 5,  # Semantic Scholar rate limit
            "requests_per_minute": 300,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        }
    
    def supports_full_text(self) -> bool:
        return True  # Semantic Scholar provides full text when available
    
    def supports_real_time_updates(self) -> bool:
        return True  # Can poll for new papers
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """
        Search Semantic Scholar for research papers
        
        Args:
            query: Search query (paper title, abstract, authors, etc.)
            max_results: Maximum number of results
            filters: Additional filters like fields_of_study, venue, etc.
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            List of research papers as StandardDocument
        """
        try:
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": min(max_results, 100),  # API limit
                "fields": "paperId,title,abstract,authors,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,fieldsOfStudy,publicationDate,externalIds"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Add filters
            if filters:
                if filters.get("fields_of_study"):
                    params["fieldsOfStudy"] = filters["fields_of_study"]
                if filters.get("venue"):
                    params["venue"] = filters["venue"]
                if filters.get("min_citation_count"):
                    params["minCitationCount"] = filters["min_citation_count"]
            
            # Add date filters
            if date_from:
                params["year"] = f"{date_from.year}-{date_to.year if date_to else '*'}"
            elif date_to:
                params["year"] = f"*-{date_to.year}"
            
            self.logger.info(f"Searching Semantic Scholar: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        raise NetworkError(f"Semantic Scholar rate limit exceeded: {response.status}")
                    elif response.status != 200:
                        raise NetworkError(f"Semantic Scholar API error: {response.status}")
                    
                    data = await response.json()
            
            papers = data.get("data", [])
            self.logger.info(f"Found {len(papers)} papers")
            
            documents = []
            for paper in papers:
                try:
                    doc = self._transform_paper(paper)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform paper: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing Semantic Scholar: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching Semantic Scholar: {e}")
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific paper by Semantic Scholar ID
        
        Args:
            source_id: Semantic Scholar paper ID
            
        Returns:
            Paper as StandardDocument
        """
        try:
            url = f"{self.base_url}/paper/{source_id}"
            params = {
                "fields": "paperId,title,abstract,authors,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,fieldsOfStudy,publicationDate,externalIds,url"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 404:
                        raise DataSourceError(f"Paper not found: {source_id}")
                    elif response.status != 200:
                        raise NetworkError(f"Semantic Scholar API error: {response.status}")
                    
                    data = await response.json()
            
            return self._transform_paper(data)
            
        except DataSourceError:
            raise
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error fetching paper {source_id}: {e}")
        except Exception as e:
            raise DataSourceError(f"Error fetching paper {source_id}: {e}")
    
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """Get full text of paper if available"""
        try:
            doc = await self.fetch_by_id(source_id)
            return doc.content
        except Exception as e:
            self.logger.error(f"Failed to get full text for {source_id}: {e}")
            return None
    
    def _transform_paper(self, raw_data: Dict) -> StandardDocument:
        """Transform Semantic Scholar paper to StandardDocument"""
        try:
            # Extract basic info
            paper_id = raw_data.get("paperId", "")
            title = raw_data.get("title", "")
            abstract = raw_data.get("abstract", "")
            venue = raw_data.get("venue", "")
            year = raw_data.get("year", 0)
            publication_date = raw_data.get("publicationDate", "")
            
            # Extract authors
            authors = []
            raw_authors = raw_data.get("authors", [])
            for i, author in enumerate(raw_authors):
                authors.append(Author(
                    name=author.get("name", ""),
                    affiliation=None,  # Not provided in basic search
                    orcid=None,  # Not provided in basic search
                    position=i
                ))
            
            # Extract external IDs
            external_ids = raw_data.get("externalIds", {})
            doi = external_ids.get("DOI", "")
            arxiv_id = external_ids.get("ArXiv", "")
            pmid = external_ids.get("PubMed", "")
            pmcid = external_ids.get("PubMedCentral", "")
            
            # Extract metrics
            citation_count = raw_data.get("citationCount", 0)
            reference_count = raw_data.get("referenceCount", 0)
            influential_citation_count = raw_data.get("influentialCitationCount", 0)
            
            # Extract fields of study
            fields_of_study = raw_data.get("fieldsOfStudy", [])
            
            # Extract open access info
            is_open_access = raw_data.get("isOpenAccess", False)
            open_access_pdf = raw_data.get("openAccessPdf", {})
            pdf_url = open_access_pdf.get("url", "") if open_access_pdf else ""
            
            # Build content (abstract is the main content)
            content = abstract
            
            # Extract entities (would be enhanced by AI processing)
            entities = {
                "FIELD_OF_STUDY": [],
                "VENUE": []
            }
            
            # Field of study entities
            for field in fields_of_study:
                entities["FIELD_OF_STUDY"].append(Entity(
                    value=field,
                    normalized_value=field.lower(),
                    entity_type="FIELD_OF_STUDY",
                    confidence=0.9,
                    source="semanticscholar"
                ))
            
            # Venue entity
            if venue:
                entities["VENUE"].append(Entity(
                    value=venue,
                    normalized_value=venue.lower(),
                    entity_type="VENUE",
                    confidence=0.8,
                    source="semanticscholar"
                ))
            
            # Parse publication date
            pub_date = None
            if publication_date:
                try:
                    pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
                except:
                    pass
            elif year:
                try:
                    pub_date = datetime(year, 1, 1)
                except:
                    pass
            
            # Calculate quality score
            quality_score = 0.0
            if paper_id: quality_score += 10
            if title: quality_score += 15
            if abstract: quality_score += 25
            if authors: quality_score += 10
            if pub_date: quality_score += 10
            if citation_count > 0: quality_score += min(citation_count / 10, 20)  # Cap at 20
            if influential_citation_count > 0: quality_score += min(influential_citation_count / 5, 10)  # Cap at 10
            if is_open_access: quality_score += 5
            if doi: quality_score += 5
            if fields_of_study: quality_score += 5
            
            # Build URL
            url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else ""
            
            # Build citations list
            citations = []
            if doi:
                citations.append(f"DOI: {doi}")
            if arxiv_id:
                citations.append(f"arXiv: {arxiv_id}")
            if pmid:
                citations.append(f"PMID: {pmid}")
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="semanticscholar",
                source_id=paper_id,
                title=title,
                abstract=abstract,
                content=content,
                document_type=DocumentType.RESEARCH_ARTICLE,
                publication_date=pub_date,
                authors=authors,
                url=url,
                alternate_urls=[pdf_url] if pdf_url else [],
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                citations=citations,
                entities=entities,
                relationships=[],
                key_concepts=fields_of_study,
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "paper_id": paper_id,
                    "venue": venue,
                    "year": year,
                    "citation_count": citation_count,
                    "reference_count": reference_count,
                    "influential_citation_count": influential_citation_count,
                    "fields_of_study": fields_of_study,
                    "is_open_access": is_open_access,
                    "pdf_url": pdf_url,
                    "external_ids": external_ids,
                    "raw_data": raw_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming Semantic Scholar paper: {e}")
            raise DataSourceError(f"Failed to transform paper: {e}")
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert Semantic Scholar data to StandardDocument"""
        return self._transform_paper(raw_data)
    
    def validate_config(self) -> bool:
        """Semantic Scholar doesn't require API key for basic usage"""
        return True
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for Semantic Scholar paper"""
        if doc.authors:
            first_author = doc.authors[0].name
            if len(doc.authors) > 1:
                author_str = f"{first_author} et al."
            else:
                author_str = first_author
        else:
            author_str = "Unknown"
        
        year = doc.publication_date.year if doc.publication_date else doc.metadata.get("year", "Unknown")
        venue = doc.metadata.get("venue", "")
        
        if venue:
            return f"{author_str} ({year}). {doc.title}. {venue}."
        else:
            return f"{author_str} ({year}). {doc.title}."
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to Semantic Scholar papers"""
        base_indicators = super().get_quality_indicators(doc)
        
        semantic_indicators = {
            "has_paper_id": bool(doc.metadata.get("paper_id")),
            "has_venue": bool(doc.metadata.get("venue")),
            "has_citations": doc.metadata.get("citation_count", 0) > 0,
            "has_influential_citations": doc.metadata.get("influential_citation_count", 0) > 0,
            "is_open_access": doc.metadata.get("is_open_access", False),
            "has_pdf": bool(doc.metadata.get("pdf_url")),
            "has_fields_of_study": bool(doc.metadata.get("fields_of_study")),
            "has_external_ids": bool(doc.metadata.get("external_ids")),
            "citation_count": doc.metadata.get("citation_count", 0),
            "influential_citation_count": doc.metadata.get("influential_citation_count", 0)
        }
        
        base_indicators.update(semantic_indicators)
        return base_indicators
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Semantic Scholar is accessible"""
        try:
            start_time = datetime.now()
            
            # Try a simple search
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/paper/search", 
                                     params={"query": "machine learning", "limit": 1}) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        return {
                            "status": "healthy",
                            "response_time_ms": int(response_time),
                            "last_check": datetime.now().isoformat(),
                            "api_status": "accessible"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"API returned status {response.status}",
                            "last_check": datetime.now().isoformat()
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
