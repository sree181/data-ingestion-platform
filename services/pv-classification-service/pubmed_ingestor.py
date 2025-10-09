"""
PubMed Targeted Ingestion Service
Fetches articles based on MeSH terms and publication types for ICSR classification
"""

from pymed import PubMed
from typing import List, Dict, Optional
import structlog
from datetime import datetime
import asyncio

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
                    
                    article_data = {
                        'id': f"pubmed_{article.pubmed_id}",
                        'pmid': str(article.pubmed_id),
                        'title': article.title or '',
                        'abstract': article.abstract or '',
                        'authors': [
                            f"{author.get('firstname', '')} {author.get('lastname', '')}".strip()
                            for author in (article.authors or [])
                        ],
                        'journal': article.journal,
                        'publication_date': self._parse_date(article.publication_date) if hasattr(article, 'publication_date') else None,
                        'doi': article.doi,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/",
                        'mesh_terms': mesh_terms,
                        'publication_types': pub_types,
                        'keywords': article.keywords if hasattr(article, 'keywords') else [],
                        'source': 'pubmed',
                        'domain': domain,
                        'ingested_at': datetime.utcnow().isoformat()
                    }
                    articles.append(article_data)
                    
                except Exception as e:
                    logger.warning("Failed to process article", pubmed_id=article.pubmed_id, error=str(e))
                    continue
            
            logger.info("PubMed fetch completed", domain=domain, articles_fetched=len(articles))
            return articles
            
        except Exception as e:
            logger.error("PubMed fetch failed", domain=domain, error=str(e))
            return []
    
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


