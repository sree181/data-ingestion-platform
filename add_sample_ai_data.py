#!/usr/bin/env python3
"""
Add sample AI data to demonstrate entity highlighting and knowledge graph
"""
import json
import requests

def add_sample_ai_data():
    print("🤖 Adding sample AI data to demonstrate features...")
    
    # Sample AI data for demonstration
    sample_entities = [
        {
            "text": "FDA",
            "type": "ORGANIZATION", 
            "description": "Food and Drug Administration",
            "confidence": 0.95,
            "start_char": 0,
            "end_char": 3
        },
        {
            "text": "Pfizer",
            "type": "ORGANIZATION",
            "description": "Pharmaceutical company",
            "confidence": 0.98,
            "start_char": 20,
            "end_char": 26
        },
        {
            "text": "COVID-19",
            "type": "DISEASE",
            "description": "Coronavirus disease",
            "confidence": 0.99,
            "start_char": 40,
            "end_char": 48
        },
        {
            "text": "Dr. Anthony Fauci",
            "type": "PERSON",
            "description": "NIAID Director",
            "confidence": 0.97,
            "start_char": 70,
            "end_char": 87
        }
    ]
    
    sample_relationships = [
        {
            "source_entity": "FDA",
            "target_entity": "Pfizer",
            "relationship_type": "REGULATES",
            "description": "FDA regulates Pfizer products",
            "confidence": 0.90
        },
        {
            "source_entity": "Pfizer",
            "target_entity": "COVID-19",
            "relationship_type": "TREATS",
            "description": "Pfizer developed COVID-19 vaccine",
            "confidence": 0.95
        }
    ]
    
    sample_insights = {
        "document_type": "regulatory_document",
        "main_themes": ["COVID-19", "vaccine approval", "FDA regulation"],
        "sentiment": "positive",
        "key_findings": ["Vaccine approved for emergency use", "High efficacy reported"],
        "risk_factors": ["Side effects monitoring required"]
    }
    
    # Get a few sample documents
    try:
        response = requests.get("http://localhost:9200/documents/_search?size=3")
        data = response.json()
        
        documents = data['hits']['hits']
        print(f"📄 Found {len(documents)} documents to enhance")
        
        for i, doc in enumerate(documents):
            doc_id = doc['_id']
            title = doc['_source'].get('title', 'Untitled')
            content = doc['_source'].get('content', '')
            
            print(f"✨ Enhancing document: {title[:50]}...")
            
            # Create highlighted content
            highlighted_content = f'''<span class="entity entity-organization" title="ORGANIZATION: FDA">FDA</span> has approved the <span class="entity entity-organization" title="ORGANIZATION: Pfizer">Pfizer</span> <span class="entity entity-disease" title="DISEASE: COVID-19">COVID-19</span> vaccine for emergency use. <span class="entity entity-person" title="PERSON: Dr. Anthony Fauci">Dr. Anthony Fauci</span> stated that the vaccine shows high efficacy.
            
            {content}'''
            
            # Update document with AI data
            update_data = {
                "doc": {
                    "openai_entities": sample_entities,
                    "relationships": sample_relationships,
                    "key_concepts": [
                        {"concept": "vaccine approval", "importance": 0.95},
                        {"concept": "FDA regulation", "importance": 0.88},
                        {"concept": "COVID-19 response", "importance": 0.92}
                    ],
                    "ai_summary": f"Document discussing FDA approval and regulation of COVID-19 vaccines, featuring key stakeholders and regulatory processes.",
                    "highlighted_content": highlighted_content,
                    "document_insights": sample_insights,
                    "ai_processed": True
                }
            }
            
            # Update in Elasticsearch
            update_url = f"http://localhost:9200/documents/_update/{doc_id}"
            update_response = requests.post(
                update_url,
                headers={"Content-Type": "application/json"},
                json=update_data
            )
            
            if update_response.status_code == 200:
                print(f"✅ Enhanced document {doc_id}")
            else:
                print(f"❌ Failed to update document {doc_id}: {update_response.status_code}")
        
        print(f"\n🎉 Sample AI data added successfully!")
        print(f"🔗 Now check your UI:")
        print(f"   • Knowledge Graph should show entity relationships")
        print(f"   • Document viewer should show entity highlighting")
        print(f"   • Search should return enhanced results")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    add_sample_ai_data()