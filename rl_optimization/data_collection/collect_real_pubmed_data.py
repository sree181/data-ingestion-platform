#!/usr/bin/env python3
"""
Collect Real PubMed Data for RL Training
Fetches real PubMed documents, classifies them, and collects data for RL training
"""

import requests
import json
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.data_collector import RLDataCollectionOrchestrator
from data_collection.feature_extractor import DocumentFeatureExtractor, ClassificationOutcomeTracker
from data_collection.data_validator import DataValidator

# Configuration
ELASTICSEARCH_URL = "http://localhost:9200"
CLASSIFICATION_URL = "http://localhost:8012/api/v1/classify/ensemble"
OUTPUT_DIR = "rl_optimization/real_pubmed_data"

class  tea:
    """
    Collects real PubMed data for RL training
    """
    
    def __init__(self):
        self.rl_orchestrator = RLDataCollectionOrchestrator(output_dir=OUTPUT_DIR)
        self.feature_extractor = DocumentFeatureExtractor()
        self.outcome_tracker = ClassificationOutcomeTracker()
        self.validator = DataValidator()
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("🚀 Real PubMed Data Collector initialized")
    
    def search_pubmed_for_documents(self, query: str, max_results: int = 50):
        """Search PubMed for documents using NCBI E-utilities"""
        print(f"🔍 Searching PubMed for: {query}")
        
        # Use NCBI E-utilities to search PubMed
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            pmids = data.get("esearchresult", {}).get("idlist", [])
            print(f"✅ Found {len(pmids)} PMIDs")
            return pmids
            
        except Exception as e:
            print(f"❌ Error searching PubMed: {e}")
            return []
    
    def fetch_pubmed_metadata(self, pmids: list):
        """Fetch REAL metadata for PMIDs using NCBI E-utilities"""
        print(f"📄 Fetching REAL metadata for {len(pmids)} documents...")
        
        # Use NCBI E-utilities to fetch metadata
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
        documents = []
        
        # Process in batches of 20 (NCBI limit)
        for i in range(0, len(pmids), 20):
            batch_pmids = pmids[i:i+20]
            
            params = {
                "db": "pubmed",
                "id": ",".join(batch_pmids),
                "retmode": "xml",
                "rettype": "abstract"
            }
            
            try:
                response = requests.get(fetch_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # Extract info for each PMID
                for article in root.findall('.//PubmedArticle'):
                    try:
                        # Extract PMID
                        pmid_elem = article.find('.//PMID')
                        pmid = pmid_elem.text if pmid_elem is not None else "unknown"
                        
                        # Extract title
                        title_elem = article.find('.//ArticleTitle')
                        title = title_elem.text if title_elem is not None else f"PubMed Article {pmid}"
                        
                        # Extract abstract
                        abstract_elem = article.find('.//AbstractText')
                        abstract = abstract_elem.text if abstract_elem is not None else f"Abstract for PMID {pmid}"
                        
                        # Extract authors
                        authors = []
                        for author in article.findall('.//Author'):
                            last_name = author.find('.//LastName')
                            first_name = author.find('.//ForeName')
                            if last_name is not None:
                                author_name = last_name.text
                                if first_name is not None:
                                    author_name = f"{first_name.text} {author_name}"
                                authors.append(author_name)
                        
                        # Extract journal
                        journal_elem = article.find('.//Journal/Title')
                        journal = journal_elem.text if journal_elem is not None else "Unknown Journal"
                        
                        # Extract publication date
                        pub_date_elem = article.find('.//PubDate/Year')
                        pub_year = pub_date_elem.text if pub_date_elem is not None else "2024"
                        
                        # Extract MeSH terms
                        mesh_terms = []
                        for mesh in article.findall('.//MeshHeading/DescriptorName'):
                            if mesh.text:
                                mesh_terms.append(mesh.text)
                        
                        # Extract publication types
                        pub_types = []
                        for pub_type in article.findall('.//PublicationType'):
                            if pub_type.text:
                                pub_types.append(pub_type.text)
                        
                        # Create document structure
                        doc = {
                            "document_id": f"pubmed_{pmid}",
                            "pmid": pmid,
                            "title": title,
                            "abstract": abstract,
                            "content": abstract,  # Use abstract as content for now
                            "authors": [{"name": author, "affiliation": None} for author in authors[:5]],  # Limit to 5 authors
                            "journal": journal,
                            "publication_date": f"{pub_year}-01-01",
                            "doi": f"10.1234/{pmid}",
                            "mesh_terms": mesh_terms[:10],  # Limit to 10 MeSH terms
                            "publication_types": pub_types,
                            "source": "pubmed",
                            "file_type": "pubmed_article",
                            "has_full_text": False,
                            "created_at": datetime.utcnow().isoformat(),
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "ai_processed": False
                        }
                        documents.append(doc)
                        
                    except Exception as e:
                        print(f"⚠️  Error parsing article: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Error fetching batch {i//20 + 1}: {e}")
                continue
        
        print(f"✅ Fetched REAL metadata for {len(documents)} documents")
        return documents
    
    def classify_document(self, doc: dict):
        """Classify document using ensemble classifier"""
        try:
            payload = {
                "document": {
                    "id": doc["document_id"],
                    "title": doc["title"],
                    "abstract": doc["abstract"],
                    "mesh_terms": doc["mesh_terms"],
                    "publication_types": doc["publication_types"]
                }
            }
            
            response = requests.post(
                CLASSIFICATION_URL,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract classification data from the response structure
                classification_data = result.get('classification', {})
                ensemble_metadata = result.get('ensemble_metadata', {})
                
                classification = classification_data.get('classification', 'Unknown')
                confidence = classification_data.get('confidence', 0.0)
                reasoning = classification_data.get('reasoning', '')
                models_used = ensemble_metadata.get('models_used', [])
                decision_path = ensemble_metadata.get('decision_path', 'unknown')
                processing_time_ms = ensemble_metadata.get('processing_time_ms', 0)
                cost_estimate = ensemble_metadata.get('cost_estimate', 0.0)
                
                print(f"   ✅ {classification} ({confidence:.2f}) | Models: {', '.join(models_used)} | Time: {processing_time_ms}ms | Cost: ${cost_estimate:.4f}")
                
                return {
                    'classification': classification,
                    'classification_confidence': confidence,
                    'reasoning': reasoning,
                    'models_used': models_used,
                    'decision_path': decision_path,
                    'processing_time_ms': processing_time_ms,
                    'cost_estimate': cost_estimate
                }
            else:
                print(f"   ❌ Classification failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Classification error: {e}")
            return None
    
    async def collect_data_from_documents(self, documents: list):
        """Collect RL training data from classified documents"""
        print(f"\n📊 Collecting RL training data from {len(documents)} documents...")
        print("=" * 80)
        
        collected_data = []
        stats = {
            'total': len(documents),
            'successful': 0,
            'failed': 0,
            'classifications': {},
            'domains': {},
            'valid_entries': 0,
            'invalid_entries': 0
        }
        
        for i, doc in enumerate(documents, 1):
            # Handle None title gracefully
            title = doc.get('title', 'No Title Available')
            if title is None:
                title = 'No Title Available'
            
            print(f"\n📄 Document {i}/{len(documents)}: {title[:80]}...")
            print(f"   PMID: {doc.get('pmid', 'N/A')}")
            print(f"   Journal: {doc.get('journal', 'N/A')}")
            print(f"   MeSH terms: {len(doc.get('mesh_terms', []))}")
            
            try:
                # Skip documents with missing essential data
                if not doc.get('pmid') or not doc.get('title'):
                    print(f"   ⚠️  Skipping document with missing data")
                    stats['failed'] += 1
                    continue
                
                # Classify the document
                classification_result = self.classify_document(doc)
                
                if classification_result:
                    # Create document data for RL collection
                    document_data = {
                        'title': doc['title'],
                        'abstract': doc['abstract'],
                        'mesh_terms': doc['mesh_terms'],
                        'publication_types': doc['publication_types']
                    }
                    
                    # Collect training data
                    training_data = self.rl_orchestrator.data_collector.collect_training_data(
                        document_data, 
                        classification_result, 
                        None  # No ground truth available
                    )
                    
                    # Validate training data
                    validation_result = self.validator.validate_training_data(training_data)
                    
                    # Store data
                    collected_data.append(training_data)
                    
                    # Update statistics
                    stats['successful'] += 1
                    classification = classification_result['classification']
                    stats['classifications'][classification] = stats['classifications'].get(classification, 0) + 1
                    
                    domain = training_data['features'].domain
                    stats['domains'][domain] = stats['domains'].get(domain, 0) + 1
                    
                    if validation_result.is_valid:
                        stats['valid_entries'] += 1
                    else:
                        stats['invalid_entries'] += 1
                    
                    print(f"   ✅ Data collected and validated (Quality: {validation_result.quality_score:.2f})")
                else:
                    stats['failed'] += 1
                    print(f"   ❌ Classification failed")
                
            except Exception as e:
                stats['failed'] += 1
                print(f"   ❌ Error processing document: {e}")
            
            # Small delay to avoid overwhelming services
            await asyncio.sleep(0.5)
        
        return collected_data, stats
    
    async def run_collection(self, query: str, max_results: int = 50):
        """Run the complete data collection process"""
        print("🚀 Starting Real PubMed Data Collection for RL Training")
        print("=" * 80)
        
        # Step 1: Search PubMed
        pmids = self.search_pubmed_for_documents(query, max_results)
        if not pmids:
            print("❌ No documents found")
            return
        
        # Step 2: Fetch metadata
        documents = self.fetch_pubmed_metadata(pmids)
        if not documents:
            print("❌ No documents fetched")
            return
        
        # Step 3: Collect RL training data
        collected_data, stats = await self.collect_data_from_documents(documents)
        
        # Step 4: Save collected data
        await self.save_collected_data(collected_data, stats)
        
        # Step 5: Generate report
        self.generate_collection_report(stats)
        
        return collected_data, stats
    
    async def save_collected_data(self, collected_data: list, stats: dict):
        """Save collected data to files"""
        print(f"\n💾 Saving collected data...")
        
        # Save training data
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        training_data_file = f"{OUTPUT_DIR}/real_pubmed_training_data_{timestamp}.json"
        
        # Convert dataclasses to dictionaries for JSON serialization
        serializable_data = []
        for entry in collected_data:
            serializable_entry = {
                'features': {
                    'title': entry['features'].title,
                    'abstract': entry['features'].abstract,
                    'mesh_terms': entry['features'].mesh_terms,
                    'publication_types': entry['features'].publication_types,
                    'word_count': entry['features'].word_count,
                    'sentence_count': entry['features'].sentence_count,
                    'technical_term_count': entry['features'].technical_term_count,
                    'medical_term_count': entry['features'].medical_term_count,
                    'patient_mentions': entry['features'].patient_mentions,
                    'drug_mentions': entry['features'].drug_mentions,
                    'adverse_event_mentions': entry['features'].adverse_event_mentions,
                    'temporal_mentions': entry['features'].temporal_mentions,
                    'icsr_mesh_count': entry['features'].icsr_mesh_count,
                    'non_icsr_mesh_count': entry['features'].non_icsr_mesh_count,
                    'rejected_signals': entry['features'].rejected_signals,
                    'domain': entry['features'].domain,
                    'complexity_score': entry['features'].complexity_score,
                    'confidence_indicators': entry['features'].confidence_indicators,
                    'extracted_at': entry['features'].extracted_at.isoformat()
                },
                'outcome': {
                    'true_classification': entry['outcome'].true_classification,
                    'predicted_classification': entry['outcome'].predicted_classification,
                    'confidence': entry['outcome'].confidence,
                    'reasoning': entry['outcome'].reasoning,
                    'models_used': entry['outcome'].models_used,
                    'decision_path': entry['outcome'].decision_path,
                    'processing_time_ms': entry['outcome'].processing_time_ms,
                    'cost_estimate': entry['outcome'].cost_estimate,
                    'is_correct': entry['outcome'].is_correct,
                    'confidence_penalty': entry['outcome'].confidence_penalty,
                    'cost_efficiency': entry['outcome'].cost_efficiency,
                    'classified_at': entry['outcome'].classified_at.isoformat()
                },
                'collected_at': entry['collected_at'].isoformat(),
                'data_id': entry['data_id']
            }
            serializable_data.append(serializable_entry)
        
        with open(training_data_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        # Save statistics
        stats_file = f"{OUTPUT_DIR}/real_pubmed_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ Data saved to: {training_data_file}")
        print(f"✅ Statistics saved to: {stats_file}")
    
    def generate_collection_report(self, stats: dict):
        """Generate and display collection report"""
        print("\n" + "=" * 80)
        print("📊 REAL PUBMED DATA COLLECTION REPORT")
        print("=" * 80)
        print(f"Total documents processed: {stats['total']}")
        print(f"Successful collections: {stats['successful']}")
        print(f"Failed collections: {stats['failed']}")
        print(f"Valid entries: {stats['valid_entries']}")
        print(f"Invalid entries: {stats['invalid_entries']}")
        
        if stats['valid_entries'] > 0:
            valid_rate = stats['valid_entries'] / stats['successful']
            print(f"Valid rate: {valid_rate:.2%}")
        
        print(f"\nClassification Distribution:")
        for classification, count in stats['classifications'].items():
            percentage = (count / stats['successful']) * 100 if stats['successful'] > 0 else 0
            print(f"  {classification}: {count} ({percentage:.1f}%)")
        
        print(f"\nDomain Distribution:")
        for domain, count in stats['domains'].items():
            percentage = (count / stats['successful']) * 100 if stats['successful'] > 0 else 0
            print(f"  {domain}: {count} ({percentage:.1f}%)")
        
        print(f"\n📁 Output directory: {OUTPUT_DIR}")
        print("=" * 80)


async def main():
    """Main function to run the data collection"""
    # Initialize collector
    collector = RealPubMedDataCollector()
    
    # Define search queries for different medical domains
    queries = [
        # Hepatotoxicity
        '("drug-induced liver injury" OR "chemical and drug induced liver injury") AND "case reports" AND 2020:2025[dp]',
        
        # Cardiotoxicity
        '("cardiotoxicity" OR "drug-induced arrhythmia") AND "case reports" AND 2020:2025[dp]',
        
        # Neurotoxicity
        '("neurotoxicity" OR "drug-induced encephalopathy") AND "case reports" AND 2020:2025[dp]',
        
        # General adverse events
        '("adverse drug reaction" OR "drug toxicity") AND "case reports" AND 2020:2025[dp]'
    ]
    
    all_collected_data = []
    all_stats = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}/{len(queries)}: {query}")
        print("-" * 80)
        
        # Collect data for this query
        collected_data, stats = await collector.run_collection(query, max_results=125)  # 125 per query = 500 total
        
        if collected_data:
            all_collected_data.extend(collected_data)
            all_stats.append(stats)
    
    # Generate final summary
    if all_collected_data:
        print("\n" + "=" * 80)
        print("🎉 FINAL SUMMARY - ALL QUERIES")
        print("=" * 80)
        
        total_documents = sum(s['total'] for s in all_stats)
        total_successful = sum(s['successful'] for s in all_stats)
        total_valid = sum(s['valid_entries'] for s in all_stats)
        
        print(f"Total documents processed: {total_documents}")
        print(f"Total successful collections: {total_successful}")
        print(f"Total valid entries: {total_valid}")
        print(f"Target: 500 documents (125 per domain)")
        
        if total_successful > 0:
            valid_rate = total_valid / total_successful
            print(f"Overall valid rate: {valid_rate:.2%}")
        
        # Combined classification distribution
        combined_classifications = {}
        for stats in all_stats:
            for classification, count in stats['classifications'].items():
                combined_classifications[classification] = combined_classifications.get(classification, 0) + count
        
        print(f"\nCombined Classification Distribution:")
        for classification, count in combined_classifications.items():
            percentage = (count / total_successful) * 100 if total_successful > 0 else 0
            print(f"  {classification}: {count} ({percentage:.1f}%)")
        
        print(f"\n📁 All data saved to: {OUTPUT_DIR}")
        print("🚀 Ready for RL training!")
    else:
        print("❌ No data was collected successfully")


if __name__ == "__main__":
    asyncio.run(main())
