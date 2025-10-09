# Integrated Classification System Plan

## 🎯 **Goal: Add AI Classification to Existing Document Library**

---

## **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING INFRASTRUCTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Elasticsearch                Neo4j                Frontend      │
│  ├─ Documents ingested       ├─ Entities            ├─ Document │
│  ├─ PubMed articles          ├─ Relationships       │   Library │
│  └─ Full-text indexed        └─ Knowledge graph     └─ Viewer   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    NEW CLASSIFICATION LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Classification Service (Llama 3.1-based)            │      │
│  │  ────────────────────────────────────────            │      │
│  │                                                       │      │
│  │  Input: Document (title + abstract)                  │      │
│  │  Process:                                             │      │
│  │    1. Analyze content with Llama                      │      │
│  │    2. Classify: ICSR | Safety | Non-ICSR | Rejected  │      │
│  │    3. Extract key entities used for classification    │      │
│  │    4. Calculate confidence scores                     │      │
│  │  Output:                                              │      │
│  │    - Classification label                             │      │
│  │    - Confidence score                                 │      │
│  │    - Key entities (highlighted)                       │      │
│  │    - Reasoning                                        │      │
│  │                                                       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ENHANCED DOCUMENT LIBRARY                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Document View                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  📄 Title: "Anaphylaxis after vaccine..."          │         │
│  │                                                     │         │
│  │  🏷️  Tags:                                          │         │
│  │     [ICSR] [High Confidence: 92%]                  │         │
│  │     [PubMed] [Classified: 2025-10-06]              │         │
│  │                                                     │         │
│  │  🎯 Classification Entities (5):                    │         │
│  │     • anaphylaxis (Adverse Event) - 90%            │         │
│  │     • vaccine (Medical Treatment) - 85%            │         │
│  │     • 45-year-old patient (Patient Info) - 80%     │         │
│  │     • hospitalization (Outcome) - 75%              │         │
│  │     • immediate reaction (Temporal) - 70%          │         │
│  │                                                     │         │
│  │  💡 Classification Reasoning:                       │         │
│  │     "Individual case report with patient age,       │         │
│  │      specific adverse event, and temporal           │         │
│  │      relationship. Clear ICSR indicators."          │         │
│  │                                                     │         │
│  │  📊 Document Content (with highlights)              │         │
│  │     Purpose: To report a case of [anaphylaxis]     │         │
│  │     following [COVID-19 vaccine] in a               │         │
│  │     [45-year-old female patient]...                 │         │
│  │                                                     │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
│  Filter & Search:                                                │
│  ┌────────────────────────────────────────────────────┐         │
│  │  🔍 Search: [___________]                           │         │
│  │                                                     │         │
│  │  Filter by Classification:                          │         │
│  │    ☑ ICSR (245 docs)                               │         │
│  │    ☑ Safety Information (180 docs)                 │         │
│  │    ☐ Non-ICSR (320 docs)                           │         │
│  │    ☐ Rejected (155 docs)                           │         │
│  │                                                     │         │
│  │  Filter by Confidence:                              │         │
│  │    ☑ High (≥90%): 650 docs                         │         │
│  │    ☑ Medium (70-90%): 180 docs                     │         │
│  │    ☐ Low (<70%): 70 docs                           │         │
│  │                                                     │         │
│  │  Filter by Source:                                  │         │
│  │    ☑ PubMed                                        │         │
│  │    ☑ Embase                                        │         │
│  │                                                     │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## **Implementation Plan**

### **PHASE 1: Build Classification Service (Day 1 - 4 hours)**

#### **Step 1.1: Create Llama-Based Classification Service**

**File: `services/classification-service/main.py`**

```python
from fastapi import FastAPI
from ollama import Client
import structlog

app = FastAPI(title="Document Classification Service")
logger = structlog.get_logger()

# Initialize Ollama client
ollama = Client(host='http://ollama:11434')

CLASSIFICATION_PROMPT = """
You are a pharmacovigilance expert. Classify this medical article into ONE category:

Categories:
1. ICSR - Individual case reports with patient details
2. Safety_Information - Clinical trials, surveillance studies
3. Non-ICSR - General medical literature
4. Rejected - Reviews, meta-analyses, preclinical

Article:
Title: {title}
Abstract: {abstract}

Output JSON:
{{
  "classification": "ICSR|Safety_Information|Non-ICSR|Rejected",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "key_entities": [
    {{"entity": "text", "type": "entity_type", "confidence": 0.9, "relevance": "why important"}},
    ...
  ]
}}

Focus on entities that drove the classification decision.
"""

@app.post("/api/v1/classify")
async def classify_document(document: dict):
    """
    Classify a document using Llama
    """
    try:
        # Format prompt
        prompt = CLASSIFICATION_PROMPT.format(
            title=document['title'],
            abstract=document.get('abstract', '')
        )
        
        # Call Llama via Ollama
        response = ollama.chat(
            model='llama3.1:latest',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        # Parse response
        result = json.loads(response['message']['content'])
        
        # Save to Elasticsearch
        await save_classification(document['id'], result)
        
        # Save entities to Neo4j
        await save_classification_entities(document['id'], result['key_entities'])
        
        return {
            "success": True,
            "document_id": document['id'],
            "classification": result
        }
        
    except Exception as e:
        logger.error("Classification failed", error=str(e))
        raise
```

---

#### **Step 1.2: Batch Classification Endpoint**

```python
@app.post("/api/v1/classify/batch")
async def classify_batch(document_ids: List[str]):
    """
    Classify multiple documents in parallel
    """
    # Fetch documents from Elasticsearch
    documents = await fetch_documents(document_ids)
    
    # Process in parallel (10 at a time)
    tasks = [classify_document(doc) for doc in documents]
    results = []
    
    for i in range(0, len(tasks), 10):
        batch = tasks[i:i+10]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
    
    return {
        "total": len(results),
        "success": sum(1 for r in results if r['success']),
        "failed": sum(1 for r in results if not r['success'])
    }
```

---

#### **Step 1.3: Auto-Classification on Ingestion**

```python
# Add to document ingestion pipeline
# services/api-gateway/routes/multi_source_ingestion.py

@router.post("/api/v1/ingest/pubmed")
async def ingest_pubmed(request: PubMedIngestRequest):
    """
    Ingest PubMed articles and auto-classify
    """
    # Existing ingestion logic
    documents = await fetch_from_pubmed(request.query)
    
    # Save to Elasticsearch
    for doc in documents:
        await es_service.index_document(doc)
    
    # NEW: Trigger classification
    classification_service = httpx.AsyncClient(base_url="http://classification-service:8011")
    await classification_service.post("/api/v1/classify/batch", json={
        "document_ids": [doc.id for doc in documents]
    })
    
    return {"ingested": len(documents), "classification": "in_progress"}
```

---

### **PHASE 2: Update Database Schema (Day 1 - 1 hour)**

#### **Step 2.1: Elasticsearch Schema Update**

```python
# Add classification fields to document index

ES_CLASSIFICATION_MAPPING = {
    "classification": {
        "type": "keyword"  # ICSR, Safety_Information, Non-ICSR, Rejected
    },
    "classification_confidence": {
        "type": "float"
    },
    "classification_reasoning": {
        "type": "text"
    },
    "classification_entities": {
        "type": "nested",
        "properties": {
            "entity": {"type": "text"},
            "type": {"type": "keyword"},
            "confidence": {"type": "float"},
            "relevance": {"type": "text"}
        }
    },
    "classified_at": {
        "type": "date"
    },
    "classification_model": {
        "type": "keyword"  # "llama3.1" or "pubmedbert"
    }
}
```

---

#### **Step 2.2: Neo4j Schema Update**

```cypher
// Add Classification relationship

// Document node (existing)
(:Document {
  id: "PMC12345",
  title: "...",
  source: "pubmed"
})

// NEW: Classification node
(:Classification {
  id: "class_001",
  label: "ICSR",
  confidence: 0.92,
  reasoning: "Individual case report...",
  classified_at: "2025-10-06T10:30:00Z",
  model: "llama3.1"
})

// NEW: ClassificationEntity relationship
(:Document)-[:CLASSIFIED_AS]->(:Classification)
(:Classification)-[:USED_ENTITY {
  confidence: 0.85,
  relevance: "Primary indicator"
}]->(:Entity {name: "anaphylaxis", type: "adverse_event"})
```

---

### **PHASE 3: Enhanced Frontend UI (Day 2 - 4 hours)**

#### **Step 3.1: Document Library with Tags**

**File: `frontend/src/pages/DocumentLibrary.js`**

```jsx
import React, { useState, useEffect } from 'react';
import { 
  Box, Card, Chip, Typography, TextField, 
  Checkbox, FormGroup, FormControlLabel 
} from '@mui/material';
import { LocalOffer, Science, Warning, Article, Block } from '@mui/icons-material';

const classificationIcons = {
  'ICSR': <Warning color="error" />,
  'Safety_Information': <Science color="primary" />,
  'Non-ICSR': <Article color="info" />,
  'Rejected': <Block color="disabled" />
};

const classificationColors = {
  'ICSR': '#d32f2f',
  'Safety_Information': '#1976d2',
  'Non-ICSR': '#0288d1',
  'Rejected': '#757575'
};

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);
  const [filters, setFilters] = useState({
    classifications: ['ICSR', 'Safety_Information', 'Non-ICSR', 'Rejected'],
    confidenceLevels: ['high', 'medium', 'low']
  });

  useEffect(() => {
    fetchDocuments();
  }, [filters]);

  const fetchDocuments = async () => {
    const response = await fetch('/api/v1/documents/classified', {
      method: 'POST',
      body: JSON.stringify({ filters })
    });
    const data = await response.json();
    setDocuments(data.documents);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📚 Document Library
      </Typography>

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 3 }}>
        {/* Classification Filter */}
        <Card sx={{ p: 2, minWidth: 250 }}>
          <Typography variant="h6" gutterBottom>
            Classification
          </Typography>
          <FormGroup>
            {['ICSR', 'Safety_Information', 'Non-ICSR', 'Rejected'].map(cls => (
              <FormControlLabel
                key={cls}
                control={<Checkbox checked={filters.classifications.includes(cls)} />}
                label={`${cls} (${getCount(cls)})`}
              />
            ))}
          </FormGroup>
        </Card>

        {/* Confidence Filter */}
        <Card sx={{ p: 2, minWidth: 250 }}>
          <Typography variant="h6" gutterBottom>
            Confidence Level
          </Typography>
          <FormGroup>
            <FormControlLabel control={<Checkbox />} label="High (≥90%)" />
            <FormControlLabel control={<Checkbox />} label="Medium (70-90%)" />
            <FormControlLabel control={<Checkbox />} label="Low (<70%)" />
          </FormGroup>
        </Card>
      </Box>

      {/* Document List */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {documents.map(doc => (
          <DocumentCard key={doc.id} document={doc} />
        ))}
      </Box>
    </Box>
  );
}

function DocumentCard({ document }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card sx={{ p: 3, cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
      {/* Title */}
      <Typography variant="h6" gutterBottom>
        {document.title}
      </Typography>

      {/* Tags */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        {/* Classification Tag */}
        <Chip
          icon={classificationIcons[document.classification]}
          label={document.classification}
          sx={{ 
            backgroundColor: classificationColors[document.classification],
            color: 'white',
            fontWeight: 'bold'
          }}
        />

        {/* Confidence Tag */}
        <Chip
          label={`Confidence: ${(document.classification_confidence * 100).toFixed(0)}%`}
          color={document.classification_confidence >= 0.9 ? 'success' : 'warning'}
        />

        {/* Source Tag */}
        <Chip label={document.source} variant="outlined" />

        {/* Date Tag */}
        <Chip 
          label={`Classified: ${new Date(document.classified_at).toLocaleDateString()}`}
          variant="outlined"
          size="small"
        />
      </Box>

      {/* Classification Entities */}
      {expanded && (
        <>
          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              🎯 Classification Entities ({document.classification_entities.length}):
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, ml: 2 }}>
              {document.classification_entities.map((entity, idx) => (
                <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    icon={<LocalOffer />}
                    label={entity.entity}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Typography variant="body2" color="text.secondary">
                    {entity.type}
                  </Typography>
                  <Chip
                    label={`${(entity.confidence * 100).toFixed(0)}%`}
                    size="small"
                    color={entity.confidence >= 0.8 ? 'success' : 'default'}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    {entity.relevance}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Classification Reasoning */}
          <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
              💡 Classification Reasoning:
            </Typography>
            <Typography variant="body2">
              {document.classification_reasoning}
            </Typography>
          </Box>

          {/* Document Content with Highlights */}
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
              📄 Document Content:
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {highlightEntities(document.abstract, document.classification_entities)}
            </Typography>
          </Box>
        </>
      )}
    </Card>
  );
}

function highlightEntities(text, entities) {
  // Highlight entities in text
  let highlighted = text;
  entities.forEach(entity => {
    const regex = new RegExp(`(${entity.entity})`, 'gi');
    highlighted = highlighted.replace(regex, '<mark>$1</mark>');
  });
  return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
}
```

---

### **PHASE 4: Batch Classification Tool (Day 2 - 2 hours)**

#### **Step 4.1: Admin Tool for Batch Classification**

```jsx
// frontend/src/pages/ClassificationAdmin.js

export default function ClassificationAdmin() {
  const [stats, setStats] = useState(null);

  const handleClassifyAll = async () => {
    // Classify all unclassified documents
    const response = await fetch('/api/v1/classify/all-unclassified', {
      method: 'POST'
    });
    // Show progress
  };

  return (
    <Box>
      <Typography variant="h4">Classification Management</Typography>

      <Card sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6">Statistics</Typography>
        <Box sx={{ display: 'flex', gap: 3, mt: 2 }}>
          <Statistic label="Total Documents" value={stats?.total} />
          <Statistic label="Classified" value={stats?.classified} />
          <Statistic label="Unclassified" value={stats?.unclassified} />
        </Box>

        <Button 
          variant="contained" 
          onClick={handleClassifyAll}
          sx={{ mt: 3 }}
        >
          Classify All Unclassified Documents
        </Button>
      </Card>
    </Box>
  );
}
```

---

## **Summary: What This Solution Provides**

### **✅ Features:**
1. **Auto-Classification**: Every ingested PubMed article gets classified
2. **Entity Extraction**: Key entities that drove classification decision
3. **Visual Tags**: Clear, color-coded labels in Document Library
4. **Filtering**: Filter by classification, confidence, source
5. **Explainability**: Shows reasoning and entities
6. **Batch Processing**: Classify existing documents
7. **Real-time**: New documents classified on ingestion

### **✅ User Experience:**
- **Document Library** shows classification tags prominently
- Click to expand → see classification entities
- Entities highlighted in document text
- Filter and search by classification
- Confidence scores visible

### **✅ Technical:**
- Uses existing infrastructure (Elasticsearch, Neo4j)
- Llama 3.1 via Ollama (free, local)
- Parallel processing (fast)
- No external API costs
- Scalable to millions of documents

---

## **Timeline**

**Day 1: Backend (5 hours)**
- Classification service with Llama
- Database schema updates
- API endpoints

**Day 2: Frontend (4 hours)**
- Enhanced Document Library UI
- Tag display and filtering
- Entity visualization

**Day 3: Testing & Deployment (3 hours)**
- Batch classify existing documents
- Test UI/UX
- Deploy to production

**Total: 12 hours over 3 days**

---

## **Cost**
- **$0** (uses local Llama via Ollama)
- No GPT-4 API costs
- No training required initially
- Just classification on existing data

---

## ❓ **Does this match your vision?**

This approach:
- ✅ Uses existing ingested PubMed articles
- ✅ Llama-based classification
- ✅ Shows tags in Document Library
- ✅ Displays classification entities (like your image)
- ✅ Real-time classification on new ingestion
- ✅ Zero cost (local Llama)

**Should I start implementing?** 🚀

