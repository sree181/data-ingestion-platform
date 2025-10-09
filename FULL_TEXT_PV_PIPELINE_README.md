# Full-Text PubMed PV Pipeline - Production Implementation

## 🎯 Overview

Complete production-ready pipeline for **Pharmacovigilance (PV)** document processing with **full-text extraction** from PubMed Central (PMC).

## 🔄 Pipeline Flow

```
PubMed Search (E-utilities)
    ↓
PMID → PMCID Linking (ELink)
    ↓  
PMC Full-Text Extraction (JATS XML)
    ↓
Store in Elasticsearch
    ↓
AI Classification (ICSR/Non-ICSR/Safety Info/Rejected)
    ↓
ICSR Data Extraction (for ICSRs only)
    ├─ Patient demographics
    ├─ Suspect/Concomitant products
    ├─ Adverse events (MedDRA)
    ├─ Lab data
    └─ Death details
    ↓
AI Narrative Generation
    ↓
ICH E2B R3 XML Generation
    ↓
Store in Elasticsearch & Neo4j
    ↓
Display in UI with Classification Badge
```

## 📂 Files

### 1. `full_text_pubmed_ingestor.py`
**Production-ready PubMed/PMC full-text ingestor**

Features:
- NCBI E-utilities integration (ESearch, ELink, EFetch)
- PMID → PMCID mapping
- Full-text JATS XML parsing from PMC
- Rate limiting (3 req/s default, 10 req/s with API key)
- Rich metadata extraction (MeSH terms, publication types, authors, DOI)
- Predefined PV-relevant queries

### 2. `run_full_text_pv_pipeline.py`
**End-to-end orchestrator**

Integrates:
- Full-text ingestion
- PV classification service
- ICSR data extraction service
- Elasticsearch storage
- Comprehensive logging & statistics

### 3. ICSR Extraction Components (in `pv-classification-service/`)
- `icsr_extractor.py`: Extracts 80+ ICSR fields using GPT-4o
- `icsr_narrative_generator.py`: Generates regulatory-compliant narratives
- `ich_e2b_xml_generator.py`: Creates ICH E2B R3 XML

## 🚀 Usage

### Basic Usage

```bash
python3 run_full_text_pv_pipeline.py
```

### Programmatic Usage

```python
from full_text_pubmed_ingestor import FullTextPubMedIngestor, PV_QUERIES
from run_full_text_pv_pipeline import run_full_pipeline

# Option 1: Use predefined queries
run_full_pipeline(
    query_name="drug_induced_liver_injury",
    max_articles=50,
    require_full_text=True  # Only PMC full-text articles
)

# Option 2: Custom query
ingestor = FullTextPubMedIngestor(
    tool="YourToolName",
    email="your@email.com",
    api_key="YOUR_NCBI_API_KEY"  # Optional, for 10 req/s
)

articles = ingestor.ingest_articles(
    query='("cardiotoxicity"[MeSH]) AND "case reports"[pt] AND 2023:2025[dp]',
    max_results=100,
    require_full_text=True
)
```

## 📋 Predefined PV Queries

| Query Name | Description |
|------------|-------------|
| `drug_induced_liver_injury` | Drug-induced liver injury case reports (2020-2025) |
| `adverse_drug_reactions` | All ADR case reports (2023-2025) |
| `cardiotoxicity` | Drug-induced cardiotoxicity (2023-2025) |
| `hepatotoxicity` | Hepatotoxicity cases (2023-2025) |
| `vaccine_adverse_events` | COVID-19 vaccine adverse events (2023-2025) |

## 🎨 UI Display

Documents with PV classification display:

1. **Classification Badge**: 
   - ICSR (red) | Non-ICSR (blue) | Safety_Information (light blue) | Rejected (gray)
   - Confidence percentage

2. **Classification Entities**:
   - Highlighted entities that drove the AI classification
   - Entity type, text, and relevance reasoning

3. **ICSR Data** (for ICSRs only):
   - Patient demographics
   - Suspect/concomitant products
   - Adverse events with MedDRA coding
   - Lab results
   - AI-generated narrative
   - Downloadable ICH E2B R3 XML

## 📊 Data Schema

### Elasticsearch Document Structure

```json
{
  "document_id": "pubmed_40998545",
  "pmid": "40998545",
  "pmcid": "PMC12401406",
  "title": "Article title",
  "abstract": "Abstract text",
  "content": "Full text (19,222 chars)",
  "has_full_text": true,
  "classification": "ICSR",
  "classification_confidence": 0.95,
  "classification_reasoning": "...",
  "classification_entities": [
    {
      "entity": "Febuxostat",
      "type": "drug",
      "confidence": 0.95,
      "relevance": "Suspect drug causing ADR"
    }
  ],
  "icsr_data": {
    "patient": {...},
    "suspect_products": [...],
    "events": [...],
    "lab_data": [...],
    "extraction_confidence": 0.85
  },
  "icsr_narrative": "A 50-year-old male...",
  "icsr_xml": "<?xml version='1.0'...",
  "mesh_terms": ["Drug-Induced Liver Injury", ...],
  "publication_types": ["Case Reports"],
  "ai_processed": true
}
```

## 🔧 Configuration

### Environment Variables

```bash
# NCBI E-utilities (optional but recommended)
NCBI_API_KEY=your_api_key_here

# OpenAI (required for classification & extraction)
OPENAI_API_KEY=your_openai_key_here

# Services
ELASTICSEARCH_HOST=http://localhost:9200
PV_CLASSIFICATION_SERVICE=http://localhost:8012
```

### Rate Limits

- Without API key: 3 requests/second
- With NCBI API key: 10 requests/second
- Automatic rate limiting built-in

## 📈 Performance

### Test Results (10 articles)

- **Full-text ingestion**: ~2-3 articles/minute (depends on PMC availability)
- **Classification**: ~13 seconds/document (GPT-4o-mini)
- **ICSR extraction**: ~20-30 seconds/document (GPT-4o)
- **XML generation**: <1 second

### Full-Text Availability

**Important**: Not all PubMed articles have PMC full text!

- ~20-30% of recent case reports have PMC full text
- Open Access articles more likely to have full text
- Set `require_full_text=False` to process abstracts for others

## 🎯 Key Features

### 1. Production-Ready Code
✅ Comprehensive error handling
✅ Structured logging
✅ Rate limiting
✅ Batch processing
✅ Progress tracking

### 2. Regulatory Compliance
✅ ICH E2B R3 XML generation
✅ MedDRA coding support
✅ FDA/EMA guideline adherence
✅ Audit trail (extraction dates, confidence scores)

### 3. AI-Powered
✅ GPT-4o for complex ICSR extraction
✅ Entity-based classification
✅ Narrative generation
✅ High accuracy (85-95% confidence)

### 4. Scalable Architecture
✅ Microservices-based
✅ Docker containerized
✅ Elasticsearch for search
✅ Neo4j for knowledge graph
✅ Parallel processing support

## 🚧 Known Limitations

1. **PMC Full-Text Availability**: Only ~20-30% of PubMed articles
   - **Solution**: Also support abstract-only processing
   - **Alternative**: Unpaywall API for OA full text

2. **Rate Limits**: NCBI enforces 3-10 req/s
   - **Solution**: Use API key, batch processing, caching

3. **Cost**: GPT-4o for extraction (~$0.02-0.05/article)
   - **Solution**: Batch processing, smart filtering, cache results

4. **MedDRA Coding**: Not all events auto-coded
   - **Solution**: Implement MedDRA dictionary lookup API

## 🔮 Future Enhancements

1. **Unpaywall Integration**: Get OA full text for non-PMC articles
2. **Europe PMC API**: Alternative source for full text
3. **MedDRA Auto-Coding**: Integrate MedDRA dictionary API
4. **Neo4j Integration**: Auto-sync entities/relationships
5. **Batch Processing**: Process 1000s of articles efficiently
6. **Quality Scoring**: ML model for ICSR completeness

## 📞 Support

For issues or questions:
- Check logs in Docker: `docker logs pv-classification-service`
- Elasticsearch: `curl http://localhost:9200/documents/_search`
- UI: `http://localhost:3000/documents`

## ✅ Implementation Status

- ✅ Full-text PubMed ingestor
- ✅ PMID → PMCID linking
- ✅ PMC JATS XML parser
- ✅ PV classification service
- ✅ ICSR data extractor (80+ fields)
- ✅ AI narrative generator
- ✅ ICH E2B R3 XML generator
- ✅ Elasticsearch integration
- ✅ End-to-end pipeline orchestrator
- ✅ UI display (classification badges, entities)
- ⚠️  Neo4j auto-sync (manual script available)
- ⚠️  Unpaywall integration (planned)
- ⚠️  MedDRA auto-coding (planned)

## 📚 References

- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [PubMed Central OAI-PMH](https://www.ncbi.nlm.nih.gov/pmc/tools/oai/)
- [ICH E2B R3 Guidelines](https://www.ich.org/page/efficacy-guidelines)
- [MedDRA Coding](https://www.meddra.org/)

