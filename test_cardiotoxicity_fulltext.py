#!/usr/bin/env python3
"""
Test Full-Text Retrieval with Cardiotoxicity Articles
======================================================

This script tests the enhanced full-text API integration by:
1. Fetching cardiotoxicity case reports from PubMed
2. Attempting to retrieve full-text from PMC
3. Displaying content statistics
4. Optionally ingesting into Elasticsearch for classification

Usage:
    python test_cardiotoxicity_fulltext.py [--ingest]
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api-gateway'))

from services.pubmed_ingestor import PubMedTargetedIngestor
import structlog

logger = structlog.get_logger()

# Test configuration
TEST_CONFIG = {
    "domain": "cardiotoxicity",
    "max_articles": 10,  # Start with 10 for testing
    "min_full_text_length": 5000,  # Minimum length to consider "full-text"
}


async def test_full_text_retrieval():
    """Test full-text retrieval for cardiotoxicity articles"""
    
    print("=" * 80)
    print("🧪 TESTING FULL-TEXT RETRIEVAL - CARDIOTOXICITY ARTICLES")
    print("=" * 80)
    print()
    
    # Initialize ingestor
    ingestor = PubMedTargetedIngestor()
    
    print(f"📋 Configuration:")
    print(f"   Domain: {TEST_CONFIG['domain']}")
    print(f"   Max Articles: {TEST_CONFIG['max_articles']}")
    print(f"   Full-Text Threshold: {TEST_CONFIG['min_full_text_length']} chars")
    print()
    
    # Build query
    query = ingestor.build_query(domain=TEST_CONFIG['domain'])
    print(f"🔍 PubMed Query Built:")
    print(f"   {query[:200]}...")
    print()
    
    # Fetch articles
    print(f"⏳ Fetching {TEST_CONFIG['max_articles']} cardiotoxicity articles from PubMed...")
    articles = await ingestor.fetch_articles(
        domain=TEST_CONFIG['domain'],
        max_results=TEST_CONFIG['max_articles']
    )
    
    print(f"✅ Retrieved {len(articles)} articles")
    print()
    
    # Analyze results
    stats = {
        'total': len(articles),
        'with_full_text': 0,
        'abstract_only': 0,
        'full_text_lengths': [],
        'abstract_lengths': [],
        'pmcids_found': 0
    }
    
    print("=" * 80)
    print("📊 ARTICLE ANALYSIS")
    print("=" * 80)
    print()
    
    for i, article in enumerate(articles, 1):
        content_length = len(article.get('content', ''))
        abstract_length = len(article.get('abstract', ''))
        has_full_text = article.get('has_full_text', False)
        pmid = article.get('pmid', 'N/A')
        pmcid = article.get('pmcid', 'N/A')
        title = article.get('title', 'Untitled')[:60]
        
        # Update stats
        if has_full_text:
            stats['with_full_text'] += 1
            stats['full_text_lengths'].append(content_length)
        else:
            stats['abstract_only'] += 1
            stats['abstract_lengths'].append(abstract_length)
        
        if pmcid and pmcid != 'N/A':
            stats['pmcids_found'] += 1
        
        # Display article info
        print(f"📄 Article {i}/{len(articles)}")
        print(f"   PMID: {pmid}")
        print(f"   PMCID: {pmcid}")
        print(f"   Title: {title}...")
        print(f"   Content Length: {content_length:,} chars")
        print(f"   Has Full-Text: {'✅ YES' if has_full_text else '❌ NO (abstract only)'}")
        
        if has_full_text:
            print(f"   🎉 FULL-TEXT RETRIEVED!")
            print(f"   Preview: {article['content'][:200]}...")
        else:
            print(f"   ℹ️  Using abstract only ({abstract_length} chars)")
        
        print()
    
    # Display statistics
    print("=" * 80)
    print("📈 SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    print(f"Total Articles: {stats['total']}")
    print(f"With Full-Text: {stats['with_full_text']} ({stats['with_full_text']/stats['total']*100:.1f}%)")
    print(f"Abstract Only: {stats['abstract_only']} ({stats['abstract_only']/stats['total']*100:.1f}%)")
    print(f"PMCIDs Found: {stats['pmcids_found']}")
    print()
    
    if stats['full_text_lengths']:
        avg_full_text = sum(stats['full_text_lengths']) / len(stats['full_text_lengths'])
        max_full_text = max(stats['full_text_lengths'])
        min_full_text = min(stats['full_text_lengths'])
        print(f"Full-Text Statistics:")
        print(f"   Average Length: {avg_full_text:,.0f} chars")
        print(f"   Maximum Length: {max_full_text:,} chars")
        print(f"   Minimum Length: {min_full_text:,} chars")
        print()
    
    if stats['abstract_lengths']:
        avg_abstract = sum(stats['abstract_lengths']) / len(stats['abstract_lengths'])
        print(f"Abstract Statistics:")
        print(f"   Average Length: {avg_abstract:,.0f} chars")
        print()
    
    # Quality assessment
    print("=" * 80)
    print("✅ QUALITY ASSESSMENT")
    print("=" * 80)
    print()
    
    if stats['with_full_text'] >= stats['total'] * 0.3:
        print("✅ EXCELLENT: >30% full-text retrieval rate")
    elif stats['with_full_text'] >= stats['total'] * 0.2:
        print("✅ GOOD: 20-30% full-text retrieval rate")
    else:
        print("⚠️  FAIR: <20% full-text retrieval rate")
    
    print()
    
    if stats['full_text_lengths'] and avg_full_text >= 10000:
        print("✅ EXCELLENT: Average full-text >10,000 chars")
    elif stats['full_text_lengths'] and avg_full_text >= 5000:
        print("✅ GOOD: Average full-text 5,000-10,000 chars")
    else:
        print("⚠️  Could be improved: Average full-text <5,000 chars")
    
    print()
    
    return articles, stats


async def ingest_to_elasticsearch(articles, project_space_id="cardiotoxicity_test"):
    """Ingest articles to Elasticsearch for classification testing"""
    
    print()
    print("=" * 80)
    print("💾 INGESTING TO ELASTICSEARCH")
    print("=" * 80)
    print()
    
    from elasticsearch import Elasticsearch
    import uuid
    
    es = Elasticsearch(['http://localhost:9200'])
    
    # Check if index exists
    if not es.indices.exists(index='documents'):
        print("❌ Documents index doesn't exist")
        return
    
    print(f"📤 Ingesting {len(articles)} articles to Elasticsearch...")
    print(f"   Project Space: {project_space_id}")
    print()
    
    ingested_count = 0
    
    for i, article in enumerate(articles, 1):
        try:
            doc_id = f"test_cardio_{article['pmid']}"
            
            # Prepare document for Elasticsearch
            # Convert authors list to a simple string to avoid mapping issues
            authors_str = ', '.join(article['authors']) if article['authors'] else 'Unknown'
            
            es_doc = {
                'id': doc_id,
                'title': article['title'],
                'content': article['content'],
                'abstract': article['abstract'],
                'source': 'pubmed',
                'source_id': article['pmid'],
                'pmid': article['pmid'],
                'pmcid': article.get('pmcid'),
                'doi': article.get('doi'),
                'url': article['url'],
                'author': authors_str,  # Use 'author' (singular) as string
                'journal': article.get('journal'),
                'publication_date': article.get('publication_date'),
                'space_id': project_space_id,
                'project_space_id': project_space_id,
                'has_full_text': article.get('has_full_text', False),
                'ingested_at': datetime.utcnow().isoformat(),
                'test_batch': 'cardiotoxicity_fulltext_test',
                'metadata': {
                    'domain': 'cardiotoxicity',
                    'content_length': len(article['content']),
                    'abstract_length': len(article['abstract']),
                    'mesh_terms': article.get('mesh_terms', []),
                    'keywords': article.get('keywords', []),
                    'authors_list': article['authors']
                }
            }
            
            # Index document
            es.index(index='documents', id=doc_id, document=es_doc)
            ingested_count += 1
            
            print(f"   ✅ [{i}/{len(articles)}] {article['pmid']} - {len(article['content']):,} chars")
            
        except Exception as e:
            print(f"   ❌ [{i}/{len(articles)}] {article['pmid']} - Error: {str(e)}")
    
    print()
    print(f"✅ Successfully ingested {ingested_count}/{len(articles)} articles")
    print()
    
    # Display next steps
    print("=" * 80)
    print("🎯 NEXT STEPS")
    print("=" * 80)
    print()
    print("1. View documents in UI:")
    print("   → Open http://localhost:3000")
    print("   → Go to 'cardiotoxicity_test' project space")
    print("   → Open Document Library")
    print()
    print("2. Test ICSR Classification:")
    print("   → Navigate to a document")
    print("   → Check 'PV Classification Evidence' section")
    print("   → Verify full-text is displayed")
    print()
    print("3. Check full-text in Professional Viewer:")
    print("   → Click 'Switch to Professional View'")
    print("   → Scroll down to see full document content")
    print("   → Verify content length matches ingestion stats")
    print()
    
    return ingested_count


async def main():
    """Main test execution"""
    
    # Test full-text retrieval
    articles, stats = await test_full_text_retrieval()
    
    # Check if --ingest flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--ingest':
        await ingest_to_elasticsearch(articles)
    else:
        print()
        print("=" * 80)
        print("💡 TIP: Run with --ingest flag to ingest articles to Elasticsearch")
        print("   python test_cardiotoxicity_fulltext.py --ingest")
        print("=" * 80)
        print()
    
    print()
    print("✅ Test completed!")
    print()


if __name__ == "__main__":
    asyncio.run(main())

