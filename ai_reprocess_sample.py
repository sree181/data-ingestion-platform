#!/usr/bin/env python3
"""
AI Reprocessing Script - Process existing documents with OpenAI entity extraction
"""
import asyncio
import json
import httpx
from elasticsearch import Elasticsearch

async def main():
    print("🤖 Starting AI reprocessing of sample documents...")
    
    # Connect to Elasticsearch (compatible with ES 8.x)
    es = Elasticsearch(
        ['http://localhost:9200'],
        request_timeout=30,
        headers={'Content-Type': 'application/json'}
    )
    
    # Connect to our AI document processor
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Get a few sample documents from Elasticsearch
        response = es.search(
            index='documents',
            body={
                'query': {'match_all': {}},
                'size': 5,  # Process 5 documents for demo
                '_source': ['title', 'content']
            }
        )
        
        documents = response['hits']['hits']
        print(f"📄 Found {len(documents)} documents to process")
        
        for i, doc in enumerate(documents):
            doc_id = doc['_id']
            title = doc['_source'].get('title', 'Untitled')
            content = doc['_source'].get('content', '')
            
            print(f"\n🔄 Processing document {i+1}/5: {title[:50]}...")
            
            # Skip if content is too short
            if len(content.strip()) < 100:
                print(f"⏭️  Skipping - content too short")
                continue
            
            try:
                # Send to our AI processor
                ai_response = await client.post(
                    'http://localhost:8001/process-text',
                    json={
                        'text': content[:5000],  # Limit to 5000 chars for demo
                        'title': title
                    }
                )
                
                if ai_response.status_code == 200:
                    ai_data = ai_response.json()
                    
                    # Extract AI results
                    entities = ai_data.get('entities', [])
                    relationships = ai_data.get('relationships', [])
                    key_concepts = ai_data.get('key_concepts', [])
                    ai_summary = ai_data.get('document_summary', '')
                    highlighted_content = ai_data.get('highlighted_content', content)
                    document_insights = ai_data.get('document_insights', {})
                    
                    print(f"✅ AI extraction successful:")
                    print(f"   - Entities: {len(entities)}")
                    print(f"   - Relationships: {len(relationships)}")
                    print(f"   - Key concepts: {len(key_concepts)}")
                    
                    # Update the document in Elasticsearch
                    update_body = {
                        'doc': {
                            'openai_entities': entities,
                            'relationships': relationships,
                            'key_concepts': key_concepts,
                            'ai_summary': ai_summary,
                            'highlighted_content': highlighted_content,
                            'document_insights': document_insights,
                            'ai_processed': True,
                            'ai_processed_date': '2024-01-01T00:00:00Z'
                        }
                    }
                    
                    es.update(
                        index='documents',
                        id=doc_id,
                        body=update_body
                    )
                    
                    print(f"📝 Updated document {doc_id} in Elasticsearch")
                    
                    # Show some sample entities
                    if entities:
                        print(f"🏷️  Sample entities:")
                        for entity in entities[:3]:
                            print(f"   - {entity.get('type', 'UNKNOWN')}: {entity.get('text', 'N/A')}")
                
                else:
                    print(f"❌ AI processing failed: {ai_response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error processing document: {str(e)}")
                continue
        
        print(f"\n🎉 AI reprocessing complete!")
        print(f"📊 Check your UI now - the Knowledge Graph and entity highlighting should work!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        await client.aclose()

if __name__ == '__main__':
    asyncio.run(main())