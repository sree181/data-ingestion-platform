"""
PubMed Targeted Ingestion Service
Fetches articles based on MeSH terms and publication types for ICSR classification
Enhanced with PMC full-text retrieval
"""

from pymed import PubMed
from typing import List, Dict, Optional
import structlog
from datetime import datetime
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

logger = structlog.get_logger()


class PubMedTargetedIngestor:
    """
    Targeted PubMed ingestion with MeSH term filters
    """
    
    def __init__(self):
        self.pubmed = PubMed(tool="PV_Classification", email="admin@example.com")
        
        # MeSH terms for pharmacovigilance
        self.mesh_terms = [
            "Drug-Related Side Effects and Adverse Reactions",
            "Toxicity",
            "Poisoning",
            "Chemical and Drug Induced Liver Injury",
            "Cardiotoxicity",
            "Neurotoxicity",
            "Drug Eruptions",
        ]
        
        # Publication types
        self.publication_types = [
            "Case Reports",
        ]
        
        # Seed domains for targeted ingestion
        self.seed_domains = {
            "hepatotoxicity": [
                "Drug-Induced Liver Injury",
                "Chemical and Drug Induced Liver Injury",
                "Hepatotoxicity",
                "Acute Liver Failure drug-induced"
            ],
            "cardiotoxicity": [
                "Cardiotoxicity",
                "Drug-Induced Arrhythmia",
                "QT Prolongation drug-induced"
            ],
            "neurotoxicity": [
                "Neurotoxicity Syndromes",
                "Drug-Induced Encephalopathy",
                "Seizures drug-induced"
            ]
        }
    
    def build_query(self, domain: str = "hepatotoxicity", max_results: int = 100) -> str:
        """
        Build PubMed query with MeSH terms and publication type filters
        """
        # Get domain-specific terms
        domain_terms = self.seed_domains.get(domain, self.seed_domains["hepatotoxicity"])
        
        # Combine with general MeSH terms
        all_mesh_terms = list(set(self.mesh_terms + domain_terms))
        
        # Build query
        # Format: ("term1"[MeSH Terms] OR "term2"[MeSH Terms]) AND "Case Reports"[Publication Type]
        mesh_query = " OR ".join([f'"{term}"[MeSH Terms]' for term in all_mesh_terms])
        pub_type_query = " OR ".join([f'"{pt}"[Publication Type]' for pt in self.publication_types])
        
        query = f"({mesh_query}) AND ({pub_type_query})"
        
        logger.info("Built PubMed query", domain=domain, query_length=len(query))
        return query
    
    async def fetch_articles(
        self, 
        domain: str = "hepatotoxicity", 
        max_results: int = 100
    ) -> List[Dict]:
        """
        Fetch articles from PubMed based on domain and filters
        """
        logger.info("Starting PubMed fetch", domain=domain, max_results=max_results)
        
        try:
            # Build query
            query = self.build_query(domain, max_results)
            
            # Search PubMed
            results = self.pubmed.query(query, max_results=max_results)
            
            articles = []
            for article in results:
                try:
                    # Extract MeSH terms if available
                    mesh_terms = []
                    if hasattr(article, 'mesh_terms') and article.mesh_terms:
                        mesh_terms = article.mesh_terms
                    
                    # Extract publication types
                    pub_types = []
                    if hasattr(article, 'publication_types') and article.publication_types:
                        pub_types = article.publication_types
                    
                    # Clean PubMed ID (sometimes contains multiple IDs with newlines)
                    clean_pmid = str(article.pubmed_id).split('\n')[0].split()[0].strip()
                    
                    # Try to get PMC ID if available
                    pmcid = None
                    if hasattr(article, 'pmc') and article.pmc:
                        pmcid = article.pmc
                    
                    # Build basic article data
                    article_data = {
                        'id': f"pubmed_{clean_pmid}",
                        'pmid': clean_pmid,
                        'pmcid': pmcid,
                        'title': article.title or '',
                        'abstract': article.abstract or '',
                        'content': article.abstract or '',  # Default to abstract
                        'authors': [
                            f"{author.get('firstname', '')} {author.get('lastname', '')}".strip()
                            for author in (article.authors or [])
                        ],
                        'journal': article.journal,
                        'publication_date': self._parse_date(article.publication_date) if hasattr(article, 'publication_date') else None,
                        'doi': article.doi,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{clean_pmid}/",
                        'mesh_terms': mesh_terms,
                        'publication_types': pub_types,
                        'keywords': article.keywords if hasattr(article, 'keywords') else [],
                        'source': 'pubmed',
                        'domain': domain,
                        'ingested_at': datetime.utcnow().isoformat(),
                        'has_full_text': False
                    }
                    
                    # Try to fetch full-text from PMC (async)
                    try:
                        full_text = await self._get_pmc_full_text(clean_pmid, pmcid)
                        if full_text and len(full_text) > len(article.abstract or ''):
                            article_data['content'] = full_text
                            article_data['has_full_text'] = True
                            logger.info(f"Retrieved full-text for PMID {clean_pmid}: {len(full_text)} chars")
                    except Exception as e:
                        logger.warning(f"Failed to get full-text for PMID {clean_pmid}: {e}")
                        # Continue with abstract
                    
                    articles.append(article_data)
                    
                except Exception as e:
                    logger.warning("Failed to process article", pubmed_id=article.pubmed_id, error=str(e))
                    continue
            
            logger.info("PubMed fetch completed", domain=domain, articles_fetched=len(articles))
            return articles
            
        except Exception as e:
            logger.error("PubMed fetch failed", domain=domain, error=str(e))
            return []
    
    async def _get_pmc_full_text(self, pmid: str, pmcid: Optional[str] = None) -> Optional[str]:
        """
        Fetch full-text from PubMed Central (PMC) using E-utilities
        
        Uses the efetch endpoint to retrieve JATS XML format full-text
        for Open Access articles
        """
        try:
            # If we have PMCID, use it directly
            if pmcid and pmcid.startswith('PMC'):
                fetch_id = pmcid
                db = 'pmc'
            else:
                # Try to convert PMID to PMCID using elink
                pmcid = await self._pmid_to_pmcid(pmid)
                if pmcid:
                    fetch_id = pmcid
                    db = 'pmc'
                else:
                    logger.info(f"No PMC ID found for PMID {pmid}")
                    return None
            
            # Fetch full-text XML from PMC
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': db,
                'id': fetch_id.replace('PMC', ''),  # Remove PMC prefix
                'rettype': 'full',
                'retmode': 'xml'
            }
            
            logger.info(f"Fetching PMC full-text for {fetch_id}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        
                        # Parse XML and extract text
                        full_text = self._parse_pmc_xml(xml_content)
                        
                        if full_text and len(full_text) > 500:
                            logger.info(f"Retrieved PMC full-text for {fetch_id}: {len(full_text)} chars")
                            return full_text
                    else:
                        logger.warning(f"PMC fetch failed with status {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to get PMC full-text for {pmid}: {e}")
        
        return None
    
    async def _pmid_to_pmcid(self, pmid: str) -> Optional[str]:
        """Convert PMID to PMCID using elink"""
        try:
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
            params = {
                'dbfrom': 'pubmed',
                'db': 'pmc',
                'id': pmid,
                'retmode': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract PMCID from response
                        linksets = data.get('linksets', [])
                        if linksets and len(linksets) > 0:
                            linksetdbs = linksets[0].get('linksetdbs', [])
                            for linksetdb in linksetdbs:
                                if linksetdb.get('dbto') == 'pmc':
                                    links = linksetdb.get('links', [])
                                    if links and len(links) > 0:
                                        pmcid = f"PMC{links[0]}"
                                        logger.info(f"Converted PMID {pmid} to {pmcid}")
                                        return pmcid
        except Exception as e:
            logger.warning(f"Failed to convert PMID {pmid} to PMCID: {e}")
        
        return None
    
    def _parse_pmc_xml(self, xml_content: str) -> Optional[str]:
        """Parse PMC JATS XML and extract full text"""
        try:
            root = ET.fromstring(xml_content)
            text_parts = []
            
            # Extract article title
            for title in root.iter('article-title'):
                if title.text:
                    text_parts.append(f"Title: {title.text.strip()}")
            
            # Extract abstract
            for abstract in root.iter('abstract'):
                abstract_text = ''.join(abstract.itertext()).strip()
                if abstract_text:
                    text_parts.append(f"\nAbstract:\n{abstract_text}")
            
            # Extract body sections
            for body in root.iter('body'):
                # Get all sections
                for sec in body.iter('sec'):
                    # Get section title
                    sec_title = sec.find('title')
                    if sec_title is not None and sec_title.text:
                        text_parts.append(f"\n\n{sec_title.text.strip()}\n")
                    
                    # Get all paragraphs in section
                    for p in sec.findall('p'):
                        para_text = ''.join(p.itertext()).strip()
                        if para_text:
                            text_parts.append(para_text)
            
            # Extract conclusions
            for conclusion in root.iter('conclusion'):
                conclusion_text = ''.join(conclusion.itertext()).strip()
                if conclusion_text:
                    text_parts.append(f"\n\nConclusion:\n{conclusion_text}")
            
            # Extract supplementary material references
            for supplementary in root.iter('supplementary-material'):
                label = supplementary.find('label')
                caption = supplementary.find('caption')
                if label is not None and caption is not None:
                    label_text = label.text.strip() if label.text else ""
                    caption_text = ''.join(caption.itertext()).strip()
                    if label_text or caption_text:
                        text_parts.append(f"\n{label_text}: {caption_text}")
            
            full_text = "\n".join(text_parts)
            
            if len(full_text) > 500:
                return full_text
            else:
                logger.warning(f"Parsed text too short: {len(full_text)} chars")
                return None
                
        except ET.ParseError as e:
            logger.error(f"Failed to parse PMC XML: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing PMC XML: {e}")
            return None
    
    def _parse_date(self, date_obj) -> Optional[str]:
        """Parse PubMed date to ISO format"""
        try:
            if isinstance(date_obj, datetime):
                return date_obj.isoformat()
            elif isinstance(date_obj, str):
                return date_obj
            else:
                return None
        except:
            return None
    
    async def fetch_multi_domain(
        self, 
        domains: List[str] = None, 
        articles_per_domain: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Fetch articles from multiple domains in parallel
        """
        if domains is None:
            domains = list(self.seed_domains.keys())
        
        logger.info("Starting multi-domain fetch", domains=domains, articles_per_domain=articles_per_domain)
        
        # Fetch from each domain in parallel
        tasks = [
            self.fetch_articles(domain, articles_per_domain)
            for domain in domains
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Organize by domain
        domain_articles = {
            domain: articles
            for domain, articles in zip(domains, results)
        }
        
        total_articles = sum(len(articles) for articles in domain_articles.values())
        logger.info("Multi-domain fetch completed", total_articles=total_articles)
        
        return domain_articles


# Test function
async def test_ingestion():
    """Test the PubMed targeted ingestion"""
    ingestor = PubMedTargetedIngestor()
    
    print("\n" + "="*80)
    print("TESTING PUBMED TARGETED INGESTION")
    print("="*80)
    
    # Test hepatotoxicity domain
    print("\nFetching hepatotoxicity articles...")
    articles = await ingestor.fetch_articles(domain="hepatotoxicity", max_results=10)
    
    print(f"\nFetched {len(articles)} articles")
    
    if articles:
        print("\nSample article:")
        sample = articles[0]
        print(f"  PMID: {sample['pmid']}")
        print(f"  Title: {sample['title'][:100]}...")
        print(f"  MeSH Terms: {', '.join(sample['mesh_terms'][:5])}")
        print(f"  Publication Types: {', '.join(sample['publication_types'])}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_ingestion())

