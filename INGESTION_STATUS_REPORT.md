# PubMed Ingestion Status Report

**Date**: October 30, 2025, 23:42  
**Query**: "Allergic rash"

---

## 📊 Current System Status

### ✅ What's Working:

1. **Document Ingestion**: ✅ Working
   - Documents are being successfully ingested into Elasticsearch
   - Total documents: **277** (increased from 265)
   - New documents ingested: **12** in the last few minutes

2. **PV Classification Service**: ✅ Working
   - Service is healthy and responding
   - Test classification successful (95% confidence for ICSR)
   - Ensemble model operational (Rule-based → BERT → LLM)

3. **"Allergic Rash" Documents**: ✅ Found
   - **34 documents** related to "Allergic rash" in the system
   - Sources: FDA, ClinicalTrials.gov, EuropePMC

---

## ⚠️ Issues Identified:

### **MAIN ISSUE: Incomplete Classification Coverage**

**Problem**: Only **35%** of documents are being classified

| Status | Count | Percentage |
|--------|-------|------------|
| **Classified** | 98 | 35% |
| **Unclassified** | 180 | 65% |
| **Total** | 277 | 100% |

### Classification Breakdown (for classified documents):

| Classification | Count | Percentage |
|----------------|-------|------------|
| ICSR | 40 | 41% |
| Non-ICSR | 33 | 34% |
| Safety_Information | 13 | 13% |
| Rejected | 10 | 10% |

---

## 🔍 Root Cause Analysis

### Why are documents not being classified?

Based on the investigation:

1. **Batch Ingestion Without Classification Flag**
   - Documents from FDA, EuropePMC, and ClinicalTrials.gov are being ingested
   - BUT they're not being sent through the PV classification pipeline
   - The ingestion process may not have `enable_icsr_classification=true` flag set

2. **Source-Specific Behavior**
   - Some sources (like manual uploads) trigger classification
   - Automated batch ingestion from external sources may skip classification

3. **Recent Unclassified Documents**:
   - FDA adverse event reports (not classified)
   - EuropePMC articles (not classified)
   - ClinicalTrials.gov studies (not classified)

---

## 📋 Recommendations

### Immediate Actions:

1. **Enable Classification for Batch Ingestion**
   ```bash
   # When ingesting from UI, ensure classification is enabled
   # Check if there's a toggle or checkbox for "Enable ICSR Classification"
   ```

2. **Retroactively Classify Existing Documents**
   - Run a batch classification job on the 180 unclassified documents
   - Use the PV classification service endpoint: `/api/v1/classify/ensemble`

3. **Verify Ingestion Settings**
   - Check Literature Automation page settings
   - Ensure "Enable ICSR Classification" is checked when searching PubMed

---

## 🎯 Next Steps for User

### To Ingest "Allergic Rash" Documents with Classification:

1. **Open Frontend**: http://localhost:3000

2. **Navigate to**: Literature Automation (in sidebar)

3. **Search Settings**:
   - Query: `Allergic rash`
   - Source: `PubMed`
   - Max Results: `20-50`
   - **✅ IMPORTANT**: Enable "ICSR Classification" toggle (if available)

4. **After Search**:
   - Review results
   - Select documents to ingest
   - Click "Ingest" or "Classify" button

5. **Monitor Progress**:
   ```bash
   # Run this command to monitor:
   ./check_ingestion_status.sh
   ```

---

## 📈 Monitoring Commands

### Check Current Status:
```bash
./check_ingestion_status.sh
```

### Monitor Real-Time Ingestion:
```bash
./monitor_pubmed_ingestion.sh
```

### Check Classification Coverage:
```bash
curl -s "http://localhost:9200/documents/_count" | python3 -c "import sys, json; print('Total:', json.load(sys.stdin)['count'])"

curl -s -X GET "http://localhost:9200/documents/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"exists": {"field": "classification"}}, "size": 0}' | \
  python3 -c "import sys, json; print('Classified:', json.load(sys.stdin)['hits']['total']['value'])"
```

---

## 🔧 Technical Details

### PV Classification Service Test:
```json
{
  "success": true,
  "classification": "ICSR",
  "confidence": 0.95,
  "models_used": ["rule_based"],
  "decision_path": "rule_based_only"
}
```

### Elasticsearch Index:
- **Index**: `documents`
- **Total Documents**: 277
- **Timestamp Field**: `created_at` (not `ingestion_timestamp`)

### Document Sources:
- FDA Adverse Event Reports
- ClinicalTrials.gov
- EuropePMC
- PubMed (via Literature Automation)

---

## ✅ Summary

**System Status**: ✅ **OPERATIONAL**

**Classification Service**: ✅ **WORKING**

**Main Issue**: ⚠️ **65% of documents are not being classified during ingestion**

**Action Required**: Enable ICSR classification when ingesting documents from the UI

**Monitoring**: Active - Use `check_ingestion_status.sh` for updates

---

**Last Updated**: October 30, 2025, 23:42  
**Next Check**: Run `./check_ingestion_status.sh` after starting UI ingestion

