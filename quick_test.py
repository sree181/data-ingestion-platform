#!/usr/bin/env python3
"""
Quick test of the core services that are working
"""

import json
import requests
from datetime import datetime

def test_elasticsearch():
    """Test Elasticsearch connectivity and basic operations"""
    print("🔍 Testing Elasticsearch...")
    
    try:
        # Test cluster health
        response = requests.get("http://localhost:9200/_cluster/health")
        if response.status_code == 200:
            health = response.json()
            print(f"  ✅ Elasticsearch cluster status: {health['status']}")
            print(f"  📊 Nodes: {health['number_of_nodes']}, Shards: {health['active_shards']}")
        
        # Test creating an index
        test_doc = {
            "title": "Test Document",
            "content": "This is a test document for the data ingestion platform",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "test"
        }
        
        response = requests.put(
            "http://localhost:9200/test_index/_doc/1",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_doc)
        )
        
        if response.status_code in [200, 201]:
            print("  ✅ Successfully indexed test document")
        
        # Test searching
        search_query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }
        
        response = requests.post(
            "http://localhost:9200/test_index/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_query)
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"  ✅ Search test successful - found {results['hits']['total']['value']} documents")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Elasticsearch test failed: {e}")
        return False

def test_kibana():
    """Test Kibana accessibility"""
    print("\n📊 Testing Kibana...")
    
    try:
        response = requests.get("http://localhost:5601", timeout=5)
        if response.status_code in [200, 302]:
            print("  ✅ Kibana is accessible")
            print("  🌐 Access at: http://localhost:5601")
            return True
        else:
            print(f"  ⚠️ Kibana returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Kibana test failed: {e}")
        return False

def test_minio():
    """Test MinIO accessibility"""
    print("\n🗂️ Testing MinIO...")
    
    try:
        response = requests.get("http://localhost:9001", timeout=5)
        if response.status_code == 200:
            print("  ✅ MinIO Console is accessible")
            print("  🌐 Access at: http://localhost:9001 (admin/minio123)")
            return True
        else:
            print(f"  ⚠️ MinIO returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ MinIO test failed: {e}")
        return False

def test_neo4j():
    """Test Neo4j accessibility"""
    print("\n🕸️ Testing Neo4j...")
    
    try:
        # Test the browser interface
        response = requests.get("http://localhost:7474", timeout=5)
        if response.status_code == 200:
            print("  ✅ Neo4j Browser is accessible")
            print("  🌐 Access at: http://localhost:7474 (neo4j/password123)")
            return True
        else:
            print(f"  ⚠️ Neo4j returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Neo4j browser test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Data Ingestion Platform Components")
    print("=" * 50)
    
    results = []
    results.append(test_elasticsearch())
    results.append(test_kibana())
    results.append(test_minio())
    results.append(test_neo4j())
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    
    working_services = sum(results)
    total_services = len(results)
    
    print(f"✅ Working services: {working_services}/{total_services}")
    
    if working_services >= 3:
        print("\n🎉 Core platform is functional!")
        print("\n📚 Next steps:")
        print("  1. Visit http://localhost:5601 to explore Kibana")
        print("  2. Visit http://localhost:9001 to access MinIO (admin/minio123)")
        print("  3. Visit http://localhost:7474 for Neo4j (neo4j/password123)")
        print("  4. Use Elasticsearch directly at http://localhost:9200")
        print("\n💡 You can now:")
        print("  • Index documents directly into Elasticsearch")
        print("  • Create knowledge graphs in Neo4j")
        print("  • Store files in MinIO")
        print("  • Visualize data in Kibana")
    else:
        print("\n⚠️ Some services need attention. Check Docker logs for details.")
        print("Run: docker-compose -f docker-compose-optimized.yml logs [service-name]")

if __name__ == "__main__":
    main()