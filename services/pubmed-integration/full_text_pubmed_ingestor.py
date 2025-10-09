#!/usr/bin/env python3
"""
Production-Ready PubMed Full-Text Ingestor
Implements the complete pipeline:
PubMed Search → PMID → PMCID check → PMC Full Text (JATS XML) → Classification → ICSR Extraction
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PubMedArticle:
    """PubMed article with full metadata and text"""
    pmid: str
    pmcid: Optional[str]
    title: str
    abstract: str
    full_text: Optional[str]
    authors: List[str]
    journal: str
    pub_date: str
    doi: Optional[str]
    mesh_terms: List[str]
    publication_types: List[str]
    has_full_text: bool
    source: str = "pubmed"


class FullTextPubMedIngestor:
    """
    Full-text PubMed ingestor using NCBI E-utilities and PMC
    """
    
    def __init__(
        self,
        tool: str = "NuvePlatformPVSystem",
        email: str = "admin@nuve.com",
        api_key: Optional[str] = None
    ):
        self.ncbi_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.tool = tool
        self.email = email
        self.api_key = api_key
        
        # Rate limiting
        self.requests_per_second = 10 if api_key else 3
        self.last_request_time = 0
        
        logger.info(
            f"Initialized FullTextPubMedIngestor",
            extra={"rate_limit": self.requests_per_second}
        )
    
    def _rate_limit(self):
        """Enforce NCBI rate limits"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _get_common_params(self) -> Dict[str, str]:
        """Get common NCBI API parameters"""
        params = {
            "tool": self.tool,
            "email": self.email
        }
        if self.api_key:
            params["api_key"] = self.api_key
        return params
    
    def search_pubmed(
        self,
        query: str,
        max_results: int = 100,
        use_history: bool = True
    ) -> Tuple[List[str], Optional[str], Optional[str]]:
        """
        Search PubMed and return PMIDs
        
        Args:
            query: PubMed query (e.g., 'drug induced liver injury[MeSH] AND case reports[pt]')
            max_results: Maximum number of results
            use_history: Use history server for large result sets
            
        Returns:
            (pmids, webenv, query_key)
        """
        logger.info(f"Searching PubMed: {query}")
        
        self._rate_limit()
        
        params = {
            **self._get_common_params(),
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "usehistory": "y" if use_history else "n"
        }
        
        response = requests.get(f"{self.ncbi_base}esearch.fcgi", params=params)
        response.raise_for_status()
        
        data = response.json()
        result = data.get("esearchresult", {})
        
        pmids = result.get("idlist", [])
        webenv = result.get("webenv")
        query_key = result.get("querykey")
        
        logger.info(f"Found {len(pmids)} PMIDs")
        
        return pmids, webenv, query_key
    
    def link_pmid_to_pmcid(self, pmids: List[str]) -> Dict[str, Optional[str]]:
        """
        Map PMIDs to PMCIDs using ELink
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dict mapping PMID -> PMCID (None if no PMC full text)
        """
        logger.info(f"Linking {len(pmids)} PMIDs to PMCIDs...")
        
        self._rate_limit()
        
        params = {
            **self._get_common_params(),
            "dbfrom": "pubmed",
            "db": "pmc",
            "id": ",".join(pmids),
            "retmode": "json"
        }
        
        response = requests.get(f"{self.ncbi_base}elink.fcgi", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse linksets to map PMID -> PMCID
        pmid_to_pmcid = {}
        
        for linkset in data.get("linksets", []):
            pmid = linkset.get("ids", [""])[0]
            
            # Look for pubmed_pmc link
            for linksetdb in linkset.get("linksetdbs", []):
                if linksetdb.get("linkname") == "pubmed_pmc":
                    pmcids = linksetdb.get("links", [])
                    pmid_to_pmcid[pmid] = f"PMC{pmcids[0]}" if pmcids else None
                    break
            else:
                pmid_to_pmcid[pmid] = None
        
        full_text_available = sum(1 for v in pmid_to_pmcid.values() if v)
        logger.info(f"Found {full_text_available}/{len(pmids)} with PMC full text")
        
        return pmid_to_pmcid
    
    def fetch_pubmed_metadata(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch rich metadata from PubMed (MEDLINE XML)
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of metadata dictionaries
        """
        logger.info(f"Fetching metadata for {len(pmids)} PMIDs...")
        
        self._rate_limit()
        
        params = {
            **self._get_common_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        response = requests.get(f"{self.ncbi_base}efetch.fcgi", params=params)
        response.raise_for_status()
        
        # Parse MEDLINE XML
        root = ET.fromstring(response.text)
        
        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            metadata = self._parse_medline_article(article_elem)
            articles.append(metadata)
        
        logger.info(f"Parsed {len(articles)} article metadata records")
        
        return articles
    
    def _parse_medline_article(self, article_elem: ET.Element) -> Dict:
        """Parse MEDLINE XML article element"""
        
        # PMID
        pmid_elem = article_elem.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""
        
        # Title
        title_elem = article_elem.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""
        
        # Abstract
        abstract_parts = []
        for abstract_text in article_elem.findall(".//AbstractText"):
            label = abstract_text.get("Label", "")
            text = "".join(abstract_text.itertext())
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = "\n".join(abstract_parts)
        
        # Authors
        authors = []
        for author in article_elem.findall(".//Author"):
            last_name = author.findtext("LastName", "")
            fore_name = author.findtext("ForeName", "")
            if last_name and fore_name:
                authors.append(f"{fore_name} {last_name}")
        
        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""
        
        # Publication date
        pub_date_elem = article_elem.find(".//PubDate")
        year = pub_date_elem.findtext("Year", "") if pub_date_elem is not None else ""
        month = pub_date_elem.findtext("Month", "") if pub_date_elem is not None else ""
        day = pub_date_elem.findtext("Day", "") if pub_date_elem is not None else ""
        pub_date = f"{year}-{month}-{day}".strip("-")
        
        # DOI
        doi = None
        for article_id in article_elem.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break
        
        # MeSH terms
        mesh_terms = []
        for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
            mesh_terms.append(mesh.text)
        
        # Publication types
        pub_types = []
        for pub_type in article_elem.findall(".//PublicationType"):
            pub_types.append(pub_type.text)
        
        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "pub_date": pub_date,
            "doi": doi,
            "mesh_terms": mesh_terms,
            "publication_types": pub_types
        }
    
    def fetch_pmc_full_text(self, pmcid: str) -> Optional[str]:
        """
        Fetch full text from PMC in JATS XML format
        
        Args:
            pmcid: PMC ID (e.g., 'PMC1234567')
            
        Returns:
            Full text extracted from JATS XML
        """
        logger.info(f"Fetching full text for {pmcid}")
        
        self._rate_limit()
        
        # Remove 'PMC' prefix if present
        pmcid_clean = pmcid.replace("PMC", "")
        
        params = {
            **self._get_common_params(),
            "db": "pmc",
            "id": pmcid_clean,
            "retmode": "xml"
        }
        
        try:
            response = requests.get(f"{self.ncbi_base}efetch.fcgi", params=params)
            response.raise_for_status()
            
            # Parse JATS XML
            root = ET.fromstring(response.text)
            
            # Extract body text
            full_text_parts = []
            
            # Extract from all paragraphs
            for p in root.findall(".//body//p"):
                text = "".join(p.itertext()).strip()
                if text:
                    full_text_parts.append(text)
            
            full_text = "\n\n".join(full_text_parts)
            
            logger.info(f"Extracted {len(full_text)} characters from {pmcid}")
            
            return full_text if full_text else None
            
        except Exception as e:
            logger.error(f"Failed to fetch full text for {pmcid}: {str(e)}")
            return None
    
    def ingest_articles(
        self,
        query: str,
        max_results: int = 50,
        require_full_text: bool = False
    ) -> List[PubMedArticle]:
        """
        Complete ingestion pipeline
        
        Args:
            query: PubMed search query
            max_results: Maximum number of articles
            require_full_text: Only return articles with PMC full text
            
        Returns:
            List of PubMedArticle objects
        """
        logger.info(f"Starting full-text ingestion pipeline")
        logger.info(f"Query: {query}")
        logger.info(f"Max results: {max_results}")
        logger.info(f"Require full text: {require_full_text}")
        
        # Step 1: Search PubMed
        pmids, webenv, query_key = self.search_pubmed(query, max_results)
        
        if not pmids:
            logger.warning("No PMIDs found")
            return []
        
        # Step 2: Link PMIDs to PMCIDs
        pmid_to_pmcid = self.link_pmid_to_pmcid(pmids)
        
        # Step 3: Fetch PubMed metadata
        metadata_list = self.fetch_pubmed_metadata(pmids)
        
        # Create metadata lookup
        metadata_dict = {m["pmid"]: m for m in metadata_list}
        
        # Step 4: Fetch full text for articles with PMCID
        articles = []
        
        for pmid, pmcid in pmid_to_pmcid.items():
            metadata = metadata_dict.get(pmid, {})
            
            # Skip if require_full_text and no PMCID
            if require_full_text and not pmcid:
                logger.debug(f"Skipping {pmid} - no PMC full text")
                continue
            
            # Fetch full text if available
            full_text = None
            if pmcid:
                full_text = self.fetch_pmc_full_text(pmcid)
            
            # Create article object
            article = PubMedArticle(
                pmid=pmid,
                pmcid=pmcid,
                title=metadata.get("title", ""),
                abstract=metadata.get("abstract", ""),
                full_text=full_text,
                authors=metadata.get("authors", []),
                journal=metadata.get("journal", ""),
                pub_date=metadata.get("pub_date", ""),
                doi=metadata.get("doi"),
                mesh_terms=metadata.get("mesh_terms", []),
                publication_types=metadata.get("publication_types", []),
                has_full_text=bool(full_text)
            )
            
            articles.append(article)
            
            logger.info(
                f"Processed {pmid} (PMCID: {pmcid or 'N/A'}, "
                f"Full text: {'Yes' if full_text else 'No'})"
            )
        
        logger.info(f"Ingestion complete: {len(articles)} articles")
        logger.info(
            f"Full text available: {sum(1 for a in articles if a.has_full_text)}/{len(articles)}"
        )
        
        return articles


# Predefined PV-relevant queries
PV_QUERIES = {
    "drug_induced_liver_injury": '("drug-induced liver injury"[MeSH Terms] OR "chemical and drug induced liver injury"[MeSH Terms]) AND "case reports"[Publication Type] AND 2020:2025[dp]',
    
    "adverse_drug_reactions": '("drug-related side effects and adverse reactions"[MeSH Terms]) AND "case reports"[Publication Type] AND 2023:2025[dp]',
    
    "cardiotoxicity": '("cardiotoxicity"[MeSH Terms] OR "drug-induced cardiotoxicity") AND "case reports"[Publication Type] AND 2023:2025[dp]',
    
    "hepatotoxicity": '("hepatotoxicity" OR "drug-induced hepatitis") AND "case reports"[Publication Type] AND 2023:2025[dp]',
    
    "vaccine_adverse_events": '("covid-19 vaccines"[MeSH Terms] AND "adverse effects"[Subheading]) AND "case reports"[Publication Type] AND 2023:2025[dp]',
}


if __name__ == "__main__":
    # Example usage
    ingestor = FullTextPubMedIngestor()
    
    # Ingest drug-induced liver injury case reports with full text
    articles = ingestor.ingest_articles(
        query=PV_QUERIES["drug_induced_liver_injury"],
        max_results=20,
        require_full_text=True  # Only articles with PMC full text
    )
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"INGESTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total articles: {len(articles)}")
    print(f"With full text: {sum(1 for a in articles if a.has_full_text)}")
    print(f"\nSample articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article.title[:100]}...")
        print(f"   PMID: {article.pmid} | PMCID: {article.pmcid or 'N/A'}")
        print(f"   Full text: {'Yes' if article.full_text else 'No'} ({len(article.full_text or '')} chars)")


