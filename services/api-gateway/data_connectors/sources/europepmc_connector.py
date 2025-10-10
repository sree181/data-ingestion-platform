"""
Europe PMC Data Connector
=========================

Connector for the Europe PMC API (https://europepmc.org/).
Provides access to European research papers and biomedical literature.

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

class EuropePMCConnector(AbstractDataSource):
    """
    Europe PMC data connector
    
    Provides access to:
    - European research papers
    - Biomedical literature
    - Full text articles (when available)
    - Author information
    - Citation data
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.api_key = api_key  # Optional for Europe PMC
    
    @property
    def source_name(self) -> str:
        return "europepmc"
    
    @property
    def display_name(self) -> str:
        return "Europe PMC"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.RESEARCH_PAPER
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.RESEARCH_ARTICLE, DocumentType.PREPRINT]
    
    @property
    def description(self) -> str:
        return "European PubMed Central - European research papers and biomedical literature"
    
    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "requests_per_second": 3,  # Europe PMC rate limit
            "requests_per_minute": 180,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        }
    
    def supports_full_text(self) -> bool:
        return True  # Europe PMC provides full text when available
    
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
        Search Europe PMC for research papers
        
        Args:
            query: Search query (paper title, abstract, authors, etc.)
            max_results: Maximum number of results
            filters: Additional filters like journal, author, etc.
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            List of research papers as StandardDocument
        """
        try:
            url = f"{self.base_url}/search"
            params = {
                "query": query,
                "resultType": "core",
                "pageSize": min(max_results, 1000),  # API limit
                "format": "json",
                "sortBy": "RELEVANCE"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Add filters
            if filters:
                if filters.get("journal"):
                    params["query"] += f" AND JOURNAL:\"{filters['journal']}\""
                if filters.get("author"):
                    params["query"] += f" AND AUTHOR:\"{filters['author']}\""
                if filters.get("has_full_text"):
                    params["query"] += " AND FULLTEXT:Y"
            
            # Add date filters
            if date_from:
                params["query"] += f" AND FIRST_PDATE:[{date_from.strftime('%Y-%m-%d')} TO *]"
            if date_to:
                params["query"] += f" AND FIRST_PDATE:[* TO {date_to.strftime('%Y-%m-%d')}]"
            
            self.logger.info(f"Searching Europe PMC: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"Europe PMC API error: {response.status}")
                    
                    data = await response.json()
            
            papers = data.get("resultList", {}).get("result", [])
            self.logger.info(f"Found {len(papers)} papers")
            
            documents = []
            for paper in papers:
                try:
                    doc = await self._transform_paper(paper)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform paper: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing Europe PMC: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching Europe PMC: {e}")
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific paper by Europe PMC ID
        
        Args:
            source_id: Europe PMC ID (PMC ID, PMID, or DOI)
            
        Returns:
            Paper as StandardDocument
        """
        try:
            url = f"{self.base_url}/search"
            params = {
                "query": f"EXT_ID:{source_id}",
                "resultType": "core",
                "pageSize": 1,
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"Europe PMC API error: {response.status}")
                    
                    data = await response.json()
            
            papers = data.get("resultList", {}).get("result", [])
            if not papers:
                raise DataSourceError(f"Paper not found: {source_id}")
            
            return await self._transform_paper(papers[0])
            
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
    
    async def _get_full_text_xml(self, source_id: str) -> Optional[str]:
        """
        Get full text XML using Europe PMC's dedicated full-text endpoint
        
        Uses the official endpoint: /{id}/fullTextXML
        This provides complete article content for Open Access articles
        """
        try:
            # Try to get full text XML from Europe PMC's dedicated endpoint
            url = f"{self.base_url}/{source_id}/fullTextXML"
            
            self.logger.info(f"Fetching full-text XML for {source_id}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        
                        # Parse XML to extract text content
                        try:
                            import xml.etree.ElementTree as ET
                            root = ET.fromstring(xml_content)
                            
                            # Extract text from various XML elements
                            text_parts = []
                            
                            # Get title
                            for title in root.iter('title'):
                                if title.text:
                                    text_parts.append(title.text.strip())
                            
                            # Get abstract
                            for abstract in root.iter('abstract'):
                                abstract_text = ''.join(abstract.itertext()).strip()
                                if abstract_text:
                                    text_parts.append(f"Abstract: {abstract_text}")
                            
                            # Get body sections
                            for sec in root.iter('sec'):
                                # Get section title
                                sec_title = sec.find('title')
                                if sec_title is not None and sec_title.text:
                                    text_parts.append(f"\n{sec_title.text.strip()}\n")
                                
                                # Get section paragraphs
                                for p in sec.iter('p'):
                                    para_text = ''.join(p.itertext()).strip()
                                    if para_text:
                                        text_parts.append(para_text)
                            
                            # Get results/conclusions
                            for conclusion in root.iter('conclusion'):
                                conclusion_text = ''.join(conclusion.itertext()).strip()
                                if conclusion_text:
                                    text_parts.append(f"Conclusion: {conclusion_text}")
                            
                            full_text = "\n\n".join(text_parts)
                            
                            if len(full_text) > 500:  # Ensure substantial content
                                self.logger.info(f"Successfully extracted {len(full_text)} characters from XML")
                                return full_text
                            else:
                                self.logger.warning(f"Extracted text too short: {len(full_text)} chars")
                                
                        except ET.ParseError as e:
                            self.logger.error(f"Failed to parse XML for {source_id}: {e}")
                            # Return raw XML if parsing fails
                            if len(xml_content) > 500:
                                return xml_content
                    
                    elif response.status == 404:
                        self.logger.info(f"No full-text available for {source_id} (404)")
                    else:
                        self.logger.warning(f"Full-text request failed with status {response.status}")
                        
        except Exception as e:
            self.logger.warning(f"Failed to get full-text XML for {source_id}: {e}")
        
        return None
    
    async def _get_full_text_content(self, source_id: str) -> Optional[str]:
        """
        Get full text content from Europe PMC with fallback strategy
        
        Strategy:
        1. Try dedicated full-text XML endpoint (best quality)
        2. Fall back to search API with fullText parameter
        3. Fall back to abstract + metadata
        """
        try:
            # STRATEGY 1: Try dedicated full-text XML endpoint (Europe PMC official)
            full_text_xml = await self._get_full_text_xml(source_id)
            if full_text_xml and len(full_text_xml) > 500:
                self.logger.info(f"Retrieved full-text XML for {source_id}: {len(full_text_xml)} chars")
                return full_text_xml
            
            # STRATEGY 2: Try search API with fullText parameter
            url = f"{self.base_url}/search"
            params = {
                "query": f"EXT_ID:{source_id}",
                "resultType": "core",
                "pageSize": 1,
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
            
            papers = data.get("resultList", {}).get("result", [])
            if not papers:
                return None
            
            paper = papers[0]
            
            # Check if full text is available
            has_full_text = paper.get("hasFullText", False)
            is_open_access = paper.get("isOpenAccess", "N") == "Y"
            
            self.logger.info(f"Paper {source_id}: hasFullText={has_full_text}, isOpenAccess={is_open_access}")
            
            # STRATEGY 3: Fall back to abstract + metadata
            text_fields = [
                paper.get("title", ""),
                paper.get("abstractText", ""),
                paper.get("authorString", ""),
                paper.get("journalTitle", ""),
                f"Keywords: {', '.join(paper.get('keywordList', {}).get('keyword', []))}"
            ]
            
            combined_text = "\n\n".join([field for field in text_fields if field])
            
            if len(combined_text) > 100:
                self.logger.info(f"Using abstract + metadata for {source_id}: {len(combined_text)} chars")
                return combined_text
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get full text content for {source_id}: {e}")
            return None
    
    async def _transform_paper(self, raw_data: Dict) -> StandardDocument:
        """Transform Europe PMC paper to StandardDocument"""
        try:
            # Extract basic info
            pmcid = raw_data.get("pmcid", "")
            pmid = raw_data.get("pmid", "")
            doi = raw_data.get("doi", "")
            title = raw_data.get("title", "")
            abstract = raw_data.get("abstractText", "")
            
            # Extract authors
            authors = []
            author_list = raw_data.get("authorList", {}).get("author", [])
            if isinstance(author_list, list):
                for i, author in enumerate(author_list):
                    author_name = author.get("fullName", "")
                    if author_name:
                        authors.append(Author(
                            name=author_name,
                            affiliation=author.get("affiliation", ""),
                            orcid=None,  # Not provided in basic search
                            position=i
                        ))
            
            # Extract journal info
            journal = raw_data.get("journalTitle", "")
            volume = raw_data.get("volume", "")
            issue = raw_data.get("issue", "")
            pages = raw_data.get("pageInfo", "")
            
            # Extract publication date
            pub_year = raw_data.get("pubYear", "")
            pub_month = raw_data.get("pubMonth", "")
            pub_day = raw_data.get("pubDay", "")
            
            # Extract additional info
            language = raw_data.get("lang", "en")
            has_full_text = raw_data.get("hasFullText", False)
            is_open_access = raw_data.get("isOpenAccess", "N") == "Y"
            cited_by_count = raw_data.get("citedByCount", 0)
            
            # Extract keywords
            keywords = raw_data.get("keywordList", {}).get("keyword", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            
            # Extract mesh terms
            mesh_terms = raw_data.get("meshHeadingList", {}).get("meshHeading", [])
            mesh_descriptors = []
            if isinstance(mesh_terms, list):
                for mesh in mesh_terms:
                    descriptor = mesh.get("descriptorName", {})
                    if isinstance(descriptor, dict):
                        mesh_descriptors.append(descriptor.get("$", ""))
                    elif isinstance(descriptor, str):
                        mesh_descriptors.append(descriptor)
            
            # Build content - try to get full text, fallback to abstract
            content = abstract
            
            # Try to get full text if available
            if has_full_text and (pmcid or pmid):
                try:
                    full_text = await self._get_full_text_content(pmcid or pmid)
                    if full_text and len(full_text) > len(abstract):
                        content = full_text
                        self.logger.info(f"Retrieved full text for {pmcid or pmid}: {len(full_text)} characters")
                except Exception as e:
                    self.logger.warning(f"Failed to get full text for {pmcid or pmid}: {e}")
                    # Continue with abstract as content
            
            # Extract entities
            entities = {
                "KEYWORD": [],
                "MESH_TERM": [],
                "JOURNAL": []
            }
            
            # Keyword entities
            for keyword in keywords:
                if keyword:
                    entities["KEYWORD"].append(Entity(
                        value=keyword,
                        normalized_value=keyword.lower(),
                        entity_type="KEYWORD",
                        confidence=0.7,
                        source="europepmc"
                    ))
            
            # MeSH term entities
            for mesh_term in mesh_descriptors:
                if mesh_term:
                    entities["MESH_TERM"].append(Entity(
                        value=mesh_term,
                        normalized_value=mesh_term.lower(),
                        entity_type="MESH_TERM",
                        confidence=0.9,
                        source="europepmc"
                    ))
            
            # Journal entity
            if journal:
                entities["JOURNAL"].append(Entity(
                    value=journal,
                    normalized_value=journal.lower(),
                    entity_type="JOURNAL",
                    confidence=0.8,
                    source="europepmc"
                ))
            
            # Parse publication date
            pub_date = None
            if pub_year:
                try:
                    year = int(pub_year)
                    month = int(pub_month) if pub_month else 1
                    day = int(pub_day) if pub_day else 1
                    pub_date = datetime(year, month, day)
                except:
                    try:
                        pub_date = datetime(int(pub_year), 1, 1)
                    except:
                        pass
            
            # Calculate quality score
            quality_score = 0.0
            if pmcid or pmid: quality_score += 10
            if title: quality_score += 15
            if abstract: quality_score += 25
            if authors: quality_score += 10
            if pub_date: quality_score += 10
            if doi: quality_score += 5
            if journal: quality_score += 5
            if has_full_text: quality_score += 10
            if is_open_access: quality_score += 5
            if cited_by_count > 0: quality_score += min(cited_by_count / 10, 15)  # Cap at 15
            if mesh_descriptors: quality_score += 5
            if keywords: quality_score += 3
            
            # Build URL
            if pmcid:
                url = f"https://europepmc.org/article/MED/{pmcid}"
            elif pmid:
                url = f"https://europepmc.org/article/MED/{pmid}"
            elif doi:
                url = f"https://doi.org/{doi}"
            else:
                url = ""
            
            # Build citations list
            citations = []
            if doi:
                citations.append(f"DOI: {doi}")
            if pmid:
                citations.append(f"PMID: {pmid}")
            if pmcid:
                citations.append(f"PMCID: {pmcid}")
            
            # Build journal reference
            journal_ref = journal
            if volume:
                journal_ref += f", {volume}"
            if issue:
                journal_ref += f"({issue})"
            if pages:
                journal_ref += f": {pages}"
            if pub_year:
                journal_ref += f" ({pub_year})"
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="europepmc",
                source_id=pmcid or pmid or doi,
                title=title,
                abstract=abstract,
                content=content,
                document_type=DocumentType.RESEARCH_ARTICLE,
                publication_date=pub_date,
                authors=authors,
                url=url,
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                citations=citations,
                entities=entities,
                relationships=[],
                key_concepts=keywords + mesh_descriptors,
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "pmcid": pmcid,
                    "pmid": pmid,
                    "doi": doi,
                    "journal": journal,
                    "journal_reference": journal_ref,
                    "volume": volume,
                    "issue": issue,
                    "pages": pages,
                    "pub_year": pub_year,
                    "pub_month": pub_month,
                    "pub_day": pub_day,
                    "language": language,
                    "has_full_text": has_full_text,
                    "is_open_access": is_open_access,
                    "cited_by_count": cited_by_count,
                    "keywords": keywords,
                    "mesh_terms": mesh_descriptors,
                    "raw_data": raw_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming Europe PMC paper: {e}")
            raise DataSourceError(f"Failed to transform paper: {e}")
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert Europe PMC data to StandardDocument"""
        return self._transform_paper(raw_data)
    
    def validate_config(self) -> bool:
        """Europe PMC doesn't require API key for basic usage"""
        return True
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for Europe PMC paper"""
        if doc.authors:
            first_author = doc.authors[0].name
            if len(doc.authors) > 1:
                author_str = f"{first_author} et al."
            else:
                author_str = first_author
        else:
            author_str = "Unknown"
        
        year = doc.publication_date.year if doc.publication_date else doc.metadata.get("pub_year", "Unknown")
        journal_ref = doc.metadata.get("journal_reference", doc.metadata.get("journal", ""))
        
        if journal_ref:
            return f"{author_str} ({year}). {doc.title}. {journal_ref}."
        else:
            return f"{author_str} ({year}). {doc.title}."
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to Europe PMC papers"""
        base_indicators = super().get_quality_indicators(doc)
        
        europepmc_indicators = {
            "has_pmcid": bool(doc.metadata.get("pmcid")),
            "has_pmid": bool(doc.metadata.get("pmid")),
            "has_doi": bool(doc.metadata.get("doi")),
            "has_journal": bool(doc.metadata.get("journal")),
            "has_full_text": doc.metadata.get("has_full_text", False),
            "is_open_access": doc.metadata.get("is_open_access", False),
            "has_citations": doc.metadata.get("cited_by_count", 0) > 0,
            "has_keywords": bool(doc.metadata.get("keywords")),
            "has_mesh_terms": bool(doc.metadata.get("mesh_terms")),
            "citation_count": doc.metadata.get("cited_by_count", 0),
            "language": doc.metadata.get("language", "en")
        }
        
        base_indicators.update(europepmc_indicators)
        return base_indicators
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Europe PMC is accessible"""
        try:
            start_time = datetime.now()
            
            # Try a simple search
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/search", 
                                     params={"query": "cancer", "pageSize": 1, "format": "json"}) as response:
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
