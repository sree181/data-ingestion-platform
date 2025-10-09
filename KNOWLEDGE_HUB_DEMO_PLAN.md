# Knowledge Hub Demo Plan - Rich Data Ingestion

## 📊 Current State Analysis

### Elasticsearch Status
- **Total Documents:** 530
- **AI-Processed:** 236 (with entities extracted)
- **Not Processed:** 294
- **Data Sources:**
  - Europe PMC: 132 papers
  - ClinicalTrials: 117 trials
  - FDA: 78 drug labels

### Neo4j Status
- **Total Entities:** 7 (only mock test data)
- **Problem:** AI-extracted entities from 236 documents are NOT synced to Neo4j
- **Solution:** We need to sync existing entities to Neo4j + process remaining 294 docs

---

## 🎯 Demo Strategy: Create a Compelling Cancer Research Knowledge Graph

### Target Use Case: **Oncology Drug Discovery**
**Persona:** Clinical researcher investigating treatment options for Triple Negative Breast Cancer

**Demo Narrative:**
1. User searches for "Pembrolizumab" (immunotherapy drug)
2. Discovers connections to:
   - Multiple cancer types (breast, lung, melanoma)
   - Clinical trials (phase 2, phase 3)
   - Biomarkers (PD-L1, BRCA)
   - Research institutions (Mayo Clinic, MD Anderson)
   - Adverse events (cardiotoxicity, immune reactions)
3. Explores treatment alternatives
4. Saves promising connections to Investigation Workspace
5. Exports findings for grant proposal

---

## 🚀 Implementation Plan (3-Phase Approach)

### **PHASE 1: Sync Existing AI-Processed Documents to Neo4j** ⏱️ 1-2 hours

**Goal:** Get 236 already-processed documents into Neo4j

**Steps:**

1. **Create Batch Sync Script**
```python
# services/api-gateway/scripts/sync_elasticsearch_to_neo4j.py

"""
Sync AI-processed documents from Elasticsearch to Neo4j
Reads documents with ai_processed=true and syncs entities/relationships
"""

import asyncio
import sys
sys.path.append('/app')

from elasticsearch import Elasticsearch
from services.knowledge_hub_service import KnowledgeHubService
from graph_db.integration_service import Neo4jIntegrationService

async def sync_documents():
    es = Elasticsearch(['http://elasticsearch:9200'])
    neo4j_service = Neo4jIntegrationService()
    
    # Query all AI-processed documents
    query = {
        "query": {
            "term": {"ai_processed": True}
        },
        "size": 1000,
        "_source": ["openai_entities", "openai_relationships", "metadata"]
    }
    
    results = es.search(index="documents", body=query)
    total = results['hits']['total']['value']
    
    print(f"Found {total} AI-processed documents to sync")
    
    synced_count = 0
    for hit in results['hits']['hits']:
        doc_id = hit['_id']
        source = hit['_source']
        
        # Extract AI results
        ai_results = {
            "entities": source.get("openai_entities", []),
            "relationships": source.get("openai_relationships", [])
        }
        
        doc_metadata = source.get("metadata", {})
        
        try:
            # Sync to Neo4j
            await neo4j_service.process_document_to_neo4j(
                doc_id, 
                ai_results, 
                doc_metadata
            )
            synced_count += 1
            
            if synced_count % 10 == 0:
                print(f"Synced {synced_count}/{total} documents...")
                
        except Exception as e:
            print(f"Error syncing document {doc_id}: {e}")
    
    print(f"✅ Sync complete! {synced_count}/{total} documents synced to Neo4j")

if __name__ == "__main__":
    asyncio.run(sync_documents())
```

2. **Run Sync Command**
```bash
docker exec -it api-gateway python /app/scripts/sync_elasticsearch_to_neo4j.py
```

**Expected Outcome:**
- 200+ entities in Neo4j (drugs, diseases, proteins, organizations)
- 100+ relationships
- Ready for Knowledge Hub exploration

---

### **PHASE 2: Process Remaining 294 Documents** ⏱️ 2-3 hours

**Goal:** Run AI processing on unprocessed documents

**Steps:**

1. **Create Batch Processing Script**
```python
# services/api-gateway/scripts/batch_process_documents.py

"""
Process unprocessed documents through AI pipeline
Extracts entities, relationships, and syncs to Neo4j
"""

import asyncio
import httpx
from elasticsearch import Elasticsearch

async def process_documents():
    es = Elasticsearch(['http://elasticsearch:9200'])
    
    # Query unprocessed documents
    query = {
        "query": {
            "bool": {
                "must_not": {"exists": {"field": "ai_processed"}}
            }
        },
        "size": 294
    }
    
    results = es.search(index="documents", body=query)
    total = results['hits']['total']['value']
    
    print(f"Found {total} unprocessed documents")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        for i, hit in enumerate(results['hits']['hits']):
            doc_id = hit['_id']
            source = hit['_source']
            
            try:
                # Send to document processor
                response = await client.post(
                    "http://document-processor:8001/process-external-document",
                    json={
                        "document_id": doc_id,
                        "content": source.get("content", ""),
                        "title": source.get("title", ""),
                        "metadata": source.get("metadata", {})
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Processed {i+1}/{total}: {source.get('title', doc_id)[:50]}")
                else:
                    print(f"❌ Failed {doc_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error processing {doc_id}: {e}")

if __name__ == "__main__":
    asyncio.run(process_documents())
```

2. **Run Processing (Background)**
```bash
docker exec -d api-gateway python /app/scripts/batch_process_documents.py
```

**Expected Outcome:**
- All 530 documents AI-processed
- 500+ entities total
- 200+ relationships
- Rich knowledge graph

---

### **PHASE 3: Ingest Fresh External Data (RECOMMENDED FOR DEMO)** ⏱️ 30-60 min

**Goal:** Add NEW documents from external sources to show real-time ingestion

**Demo Sources to Query:**

#### **1. ClinicalTrials.gov - Cancer Immunotherapy**
```
Query: "triple negative breast cancer pembrolizumab"
Filter: Phase 2, Phase 3 trials
Target: 20 trials
```

#### **2. Europe PMC - Recent Research Papers**
```
Query: "PD-L1 breast cancer immunotherapy"
Filter: Published in last 2 years
Target: 20 papers
```

#### **3. FDA Drug Labels**
```
Query: "pembrolizumab, atezolizumab, nivolumab"
Target: 10 drug labels
```

**Steps:**

1. **Use Project Spaces UI**
   - Create new space: "Cancer Immunotherapy Research"
   - Navigate to Multi-Source Ingestion
   - Configure sources with above queries
   - Start ingestion

2. **Monitor Progress**
```bash
# Watch ingestion logs
docker logs -f api-gateway | grep "ingestion"

# Check document count
curl http://localhost:9200/documents/_count
```

3. **Verify Neo4j Sync**
```bash
curl -u neo4j:password123 -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n)"}]}'
```

**Expected Outcome:**
- 50 new documents ingested
- Real-time entity extraction
- Automatic Neo4j sync
- Live demo of full pipeline

---

## 🎬 Demo Presentation Flow

### **Act 1: The Problem (2 min)**
"A clinical researcher is investigating treatment options for Triple Negative Breast Cancer. 
Traditional literature review would take weeks. Let's see how Knowledge Hub accelerates this."

### **Act 2: Discovery (5 min)**

1. **Search for Pembrolizumab**
   - Show 50+ connected entities
   - Color-coded by type (drugs, diseases, trials, etc.)
   
2. **Click on Triple Negative Breast Cancer**
   - Show all related drugs
   - Highlight clinical trials
   - Display success rates

3. **Explore PD-L1 biomarker**
   - Show mechanism of action
   - Connect to multiple drugs
   - Identify patient selection criteria

4. **Find Alternative Drugs**
   - Compare Pembrolizumab vs Atezolizumab
   - Show side effect profiles
   - Identify combination therapies

### **Act 3: Action (3 min)**

1. **Save Findings**
   - Add promising drug-disease pairs to Investigation Workspace
   - Annotate with notes

2. **Enrich Entities**
   - Pull latest FDA approval status
   - Get recent clinical trial results
   - Check adverse event reports

3. **Export Results**
   - Generate PDF report
   - Include graph visualization
   - List all source documents

### **Act 4: The Wow Moment (1 min)**

"What would have taken 3 weeks of manual research took 10 minutes with Knowledge Hub.
The researcher can now make data-driven treatment recommendations."

---

## 📊 Expected Demo Data Profile

After completing all 3 phases:

### **Entities (600+)**
- **Drugs:** 80+ (pembrolizumab, nivolumab, atezolizumab, etc.)
- **Diseases:** 100+ (breast cancer, melanoma, NSCLC, etc.)
- **Proteins/Biomarkers:** 150+ (PD-L1, BRCA1, EGFR, etc.)
- **Organizations:** 120+ (Mayo Clinic, Merck, FDA, etc.)
- **Trials:** 100+ (NCT identifiers)
- **People:** 50+ (principal investigators, researchers)

### **Relationships (300+)**
- **TREATS:** Drug → Disease (120 relationships)
- **HAS_BIOMARKER:** Disease → Protein (80 relationships)
- **STUDIED_IN:** Drug → Clinical Trial (100 relationships)
- **RESEARCHED_BY:** Drug → Organization (50 relationships)
- **CAUSES:** Drug → Adverse Event (40 relationships)

### **Document Types**
- Clinical trial protocols: 150
- Research papers: 180
- Drug labels: 90
- FDA reports: 80
- European medicines reports: 50

---

## 🎯 Recommended Execution Order

### **Option A: Quick Demo (2 hours total)**
**Best for:** Immediate demo needs

1. ✅ Run Phase 1 (Sync existing) - 30 min
2. ✅ Test Knowledge Hub - 15 min
3. ✅ Run Phase 3 (Fresh data) - 45 min
4. ✅ Practice demo narrative - 30 min

**Result:** 250+ entities, compelling demo

---

### **Option B: Comprehensive Demo (4 hours total)**
**Best for:** Production readiness

1. ✅ Run Phase 1 (Sync existing) - 30 min
2. ✅ Run Phase 2 (Process remaining) - 2 hours
3. ✅ Run Phase 3 (Fresh data) - 45 min
4. ✅ Test & practice - 45 min

**Result:** 600+ entities, production-ready graph

---

### **Option C: Hybrid Approach (3 hours total)** ⭐ **RECOMMENDED**
**Best for:** Balanced approach

1. ✅ Run Phase 1 (Sync existing 236) - 30 min
2. ✅ Run Phase 2 (Process 100 most relevant) - 1 hour
3. ✅ Run Phase 3 (Fresh cancer data) - 45 min
4. ✅ Test & practice - 45 min

**Result:** 400+ entities, focused domain, impressive demo

---

## 🛠️ Quick Start Commands

### **Step 1: Sync Existing Documents to Neo4j**
```bash
# Create sync script
cat > /Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion/services/api-gateway/scripts/sync_elasticsearch_to_neo4j.py << 'EOF'
[script content from Phase 1]
EOF

# Run sync
docker exec -it api-gateway python /app/scripts/sync_elasticsearch_to_neo4j.py
```

### **Step 2: Check Neo4j**
```bash
# Count entities
curl -u neo4j:password123 -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN labels(n)[0] as type, count(n) as count GROUP BY type"}]}' | jq '.results[0].data'
```

### **Step 3: Test Knowledge Hub**
1. Go to http://localhost:3000/knowledge-hub
2. Search for "cancer" or "pembrolizumab"
3. Explore the graph

### **Step 4: Ingest Fresh Data** (Optional but recommended)
1. Go to Project Spaces
2. Create "Cancer Research Demo"
3. Start multi-source ingestion
4. Use queries from Phase 3

---

## 📈 Success Metrics

**Before Demo:**
- [ ] 200+ entities in Neo4j
- [ ] 100+ relationships
- [ ] Graph renders smoothly
- [ ] Search returns relevant results
- [ ] Entity details show rich context

**During Demo:**
- [ ] Less than 2 seconds to load graph
- [ ] Smooth zoom/pan interactions
- [ ] Click entity → see details instantly
- [ ] Filter by type works correctly
- [ ] Legend is clear and helpful

**After Demo:**
- [ ] Audience says "wow"
- [ ] Questions about integration
- [ ] Requests for pilot program
- [ ] Recognition of time savings

---

## 🚨 Troubleshooting

### **Issue: Sync script fails**
```bash
# Check Elasticsearch connection
curl http://localhost:9200/_cluster/health

# Check Neo4j connection
curl -u neo4j:password123 http://localhost:7474/db/neo4j/

# Check API Gateway logs
docker logs api-gateway | tail -50
```

### **Issue: Graph is empty**
```bash
# Verify entities in Neo4j
curl -u neo4j:password123 -X POST http://localhost:7474/db/neo4j/tx/commit \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n)"}]}'

# Check Knowledge Hub API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/knowledge-hub/statistics
```

### **Issue: AI processing is slow**
```bash
# Check Ollama status
docker ps | grep ollama

# Restart if needed
docker restart ollama

# Use GPT-4 instead (faster but costs $$)
# Set OPENAI_API_KEY in docker-compose.yml
```

---

## 🎉 Next Steps After Demo

1. **Gather Feedback**
   - What worked well?
   - What was confusing?
   - What features are missing?

2. **Implement Priority Features**
   - Entity details drawer enhancement
   - Save to Investigation Workspace
   - Export to PDF/PowerPoint

3. **Scale Up**
   - Ingest 1000+ documents
   - Add more data sources (PubMed, Patents)
   - Implement entity consolidation

4. **Production Deploy**
   - Set up monitoring
   - Add authentication/authorization
   - Configure backup/disaster recovery

---

**Ready to build an amazing demo? Let's start with Phase 1!** 🚀


