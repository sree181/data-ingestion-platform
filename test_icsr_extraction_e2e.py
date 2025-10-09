#!/usr/bin/env python3
"""
End-to-End Test for ICSR Data Extraction
Tests: Classification → ICSR Extraction → Narrative → XML
"""
import requests
import json
import time

# Configuration
ES_HOST = "http://localhost:9200"
PV_CLASSIFICATION_SERVICE = "http://localhost:8012"
API_GATEWAY = "http://localhost:8000"

def test_e2e_icsr_extraction():
    """Test end-to-end ICSR extraction pipeline"""
    
    print("=" * 80)
    print("🧪 ICSR DATA EXTRACTION - END-TO-END TEST")
    print("=" * 80)
    
    # Step 1: Get a classified ICSR document from Elasticsearch
    print("\n📊 Step 1: Fetching ICSR documents from Elasticsearch...")
    
    # Use requests instead of Elasticsearch client to avoid version issues
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"classification": "ICSR"}},
                    {"exists": {"field": "title"}},
                    {"exists": {"field": "content"}}
                ]
            }
        },
        "size": 3
    }
    
    response = requests.post(
        f"{ES_HOST}/documents/_search",
        json=query,
        headers={"Content-Type": "application/json"}
    ).json()
    
    if response['hits']['total']['value'] == 0:
        print("❌ No ICSR documents found in Elasticsearch")
        print("💡 Run classify_pubmed_docs.py first to classify documents")
        return False
    
    print(f"✅ Found {response['hits']['total']['value']} ICSR documents")
    
    # Test with first 3 documents
    results = []
    
    for idx, hit in enumerate(response['hits']['hits'], 1):
        doc = hit['_source']
        doc_id = hit['_id']
        
        print(f"\n{'=' * 80}")
        print(f"🔬 Test {idx}/3: Processing Document {doc_id}")
        print(f"{'=' * 80}")
        print(f"📄 Title: {doc.get('title', 'N/A')[:100]}...")
        print(f"🏷️  Classification: {doc.get('classification', 'N/A')}")
        print(f"📈 Confidence: {doc.get('classification_confidence', 0):.2f}")
        
        # Step 2: Call ICSR extraction service
        print(f"\n🔍 Step 2: Extracting ICSR data...")
        
        extraction_request = {
            "document_id": doc_id,
            "title": doc.get('title', ''),
            "abstract": doc.get('content', '')[:2000],  # Use content as abstract
            "full_text": doc.get('content', ''),
            "pmid": doc.get('pmid', doc.get('document_id', '')),
            "doi": doc.get('doi', '')
        }
        
        try:
            extraction_response = requests.post(
                f"{PV_CLASSIFICATION_SERVICE}/api/v1/extract/icsr",
                json=extraction_request,
                timeout=120  # 2 minutes timeout for GPT-4o
            )
            
            if extraction_response.status_code == 200:
                result = extraction_response.json()
                
                print("✅ ICSR extraction completed!")
                
                # Display extracted data
                icsr_data = result.get('icsr_data', {})
                
                print(f"\n📋 EXTRACTED ICSR DATA:")
                print(f"{'─' * 80}")
                
                # Patient
                patient = icsr_data.get('patient', {})
                if patient:
                    print(f"\n👤 Patient:")
                    print(f"   Age: {patient.get('age')} {patient.get('age_unit', '')}")
                    print(f"   Gender: {patient.get('gender', 'Unknown')}")
                    print(f"   Medical History: {patient.get('medical_history', 'None')[:100]}")
                
                # Suspect Products
                suspect_products = icsr_data.get('suspect_products', [])
                print(f"\n💊 Suspect Products: {len(suspect_products)}")
                for i, prod in enumerate(suspect_products[:3], 1):
                    print(f"   {i}. {prod.get('generic_name') or prod.get('brand_name', 'Unknown')}")
                    print(f"      Dose: {prod.get('dose', 'Not specified')}")
                    print(f"      Route: {prod.get('route', 'Not specified')}")
                    print(f"      Action: {prod.get('action_taken', 'Unknown')}")
                
                # Events
                events = icsr_data.get('events', [])
                print(f"\n⚠️  Adverse Events: {len(events)}")
                for i, event in enumerate(events[:3], 1):
                    print(f"   {i}. {event.get('description', 'Unknown')[:80]}")
                    print(f"      MedDRA PT: {event.get('meddra_pt', 'Not coded')}")
                    print(f"      Outcome: {event.get('outcome', 'Unknown')}")
                    seriousness = event.get('seriousness_criteria', [])
                    if seriousness:
                        print(f"      Seriousness: {', '.join(seriousness)}")
                
                # Lab Data
                lab_data = icsr_data.get('lab_data', [])
                if lab_data:
                    print(f"\n🔬 Lab Data: {len(lab_data)} tests")
                    for lab in lab_data[:3]:
                        print(f"   - {lab.get('test_name')}: {lab.get('result_value')} {lab.get('unit', '')} ({lab.get('result_status', 'Unknown')})")
                
                # Narrative
                narrative = result.get('narrative', '')
                print(f"\n📝 AI-Generated Narrative ({len(narrative)} chars):")
                print(f"{'─' * 80}")
                print(narrative[:500])
                if len(narrative) > 500:
                    print(f"... [truncated, {len(narrative) - 500} more characters]")
                
                # XML
                xml_content = result.get('xml', '')
                print(f"\n📄 ICH E2B R3 XML: {len(xml_content)} bytes")
                print(f"   Status: {'✅ Generated' if xml_content else '❌ Failed'}")
                
                # Save results
                results.append({
                    'document_id': doc_id,
                    'title': doc.get('title', ''),
                    'extraction_success': True,
                    'num_events': len(events),
                    'num_products': len(suspect_products),
                    'num_lab_tests': len(lab_data),
                    'narrative_length': len(narrative),
                    'xml_size': len(xml_content),
                    'extraction_confidence': icsr_data.get('extraction_confidence', 0)
                })
                
            else:
                print(f"❌ Extraction failed: {extraction_response.status_code}")
                print(f"   Error: {extraction_response.text[:200]}")
                results.append({
                    'document_id': doc_id,
                    'extraction_success': False,
                    'error': extraction_response.text[:200]
                })
        
        except Exception as e:
            print(f"❌ Exception during extraction: {str(e)}")
            results.append({
                'document_id': doc_id,
                'extraction_success': False,
                'error': str(e)
            })
        
        print(f"\n{'=' * 80}")
        
        # Small delay between requests
        time.sleep(2)
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 TEST SUMMARY")
    print(f"{'=' * 80}")
    
    successful = sum(1 for r in results if r.get('extraction_success'))
    print(f"✅ Successful extractions: {successful}/{len(results)}")
    
    if successful > 0:
        avg_events = sum(r.get('num_events', 0) for r in results if r.get('extraction_success')) / successful
        avg_products = sum(r.get('num_products', 0) for r in results if r.get('extraction_success')) / successful
        avg_narrative = sum(r.get('narrative_length', 0) for r in results if r.get('extraction_success')) / successful
        
        print(f"\n📈 Average Metrics:")
        print(f"   Events per ICSR: {avg_events:.1f}")
        print(f"   Products per ICSR: {avg_products:.1f}")
        print(f"   Narrative length: {avg_narrative:.0f} characters")
    
    print(f"\n{'=' * 80}")
    
    return successful > 0


if __name__ == "__main__":
    try:
        success = test_e2e_icsr_extraction()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

