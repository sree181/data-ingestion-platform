# Force Ensemble UI Testing Guide

**Date**: October 30, 2025  
**Feature**: Force Full Ensemble Mode (Rule + BERT + LLM)  
**Status**: ✅ Backend Integrated, Ready for UI Testing

---

## 🎯 What Was Implemented

We've successfully wired the `force_ensemble` parameter through the entire classification pipeline:

1. **UI Toggle**: Added checkbox in Project Spaces ingestion form
2. **API Gateway**: Updated to accept and pass `force_ensemble` parameter
3. **PV Integration Service**: Modified to propagate the flag to classification service
4. **PV Classification Service**: Already supports `force_ensemble` in ensemble endpoint
5. **Elasticsearch Storage**: Updated to store full `individual_results` breakdown
6. **Document Viewer UI**: Enhanced to display per-model results table

---

## 📍 Where to Find the Toggle

### UI Location:
```
Project Spaces
  └─> Select a Project (or create new)
      └─> Documents & Ingestion Tab
          └─> Multi-Source Ingestion Card
              └─> AI Processing Options (Collapsible Section)
                  └─> Checkboxes:
                      • ✅ AI Analysis
                      • ✅ Entity Extraction
                      • ✅ Relationships
                      • ✅ ICSR Classification ← **Check this first**
                          └─> **Purple info box appears:**
                              💡 ICSR Classification automatically identifies...
                              └─> ☑️ **Force Full Ensemble (Run Rule+BERT+LLM for all documents)** ← **This is the new toggle!**
```

---

## 🧪 Step-by-Step Testing Instructions

### Phase 1: Clear Existing Data (Fresh Start)

1. **Navigate to Elasticsearch Admin** (if needed):
   ```bash
   # From terminal:
   curl -X DELETE "http://localhost:9200/documents"
   curl -X PUT "http://localhost:9200/documents"
   ```

   OR use the UI:
   - Go to Document Library
   - Select all documents (if any)
   - Delete them

### Phase 2: Start Force Ensemble Ingestion

1. **Navigate to Project Spaces**:
   - Click "Project Spaces" in the sidebar
   - Select an existing project OR create a new one:
     - Name: "Force Ensemble Test"
     - Description: "Testing full ensemble classification"

2. **Open Documents & Ingestion Tab**:
   - Click on the "Documents & Ingestion" tab

3. **Configure Multi-Source Ingestion**:
   - **Search Query**: `"Stevens-Johnson syndrome case report"`
   - **Sources**: Check ☑️ PubMed
   - **Max Results**: `5` (for quick testing)

4. **Enable AI Processing Options** (expand the section):
   - ☑️ AI Analysis: **Checked**
   - ☑️ Entity Extraction: **Checked**
   - ☑️ Relationships: **Checked**
   - ☑️ **ICSR Classification**: **Checked** ← This is critical!

5. **Enable Force Ensemble** (purple box appears after checking ICSR):
   - ☑️ **Force Full Ensemble (Run Rule+BERT+LLM for all documents)**: **Checked** ← The new feature!

6. **Select LLM Model**:
   - Choose: **GPT (OpenAI)** OR **Llama** OR **Phi3** (any should work)

7. **Start Ingestion**:
   - Click **"Start Ingestion"** button
   - A toast notification should appear: "Ingestion started successfully!"

### Phase 3: Monitor Ingestion Progress

**Option A: Using Terminal**
```bash
cd /Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion
./monitor_pubmed_ingestion.sh
```

**Option B: Using UI**
- Wait 30-60 seconds for documents to be processed
- Navigate to **Document Library**
- You should see 5 new documents appearing

### Phase 4: Verify Force Ensemble Results

1. **Navigate to Document Library**:
   - Sidebar → Document Library

2. **Check Document Badges** (should appear for all documents):
   - **ICSR** badge (red) OR **Safety_Information** badge (blue) OR **Non-ICSR** badge (light blue)
   - Documents should NOT be unbadged

3. **Open a Document**:
   - Click on any document title

4. **Verify Ensemble Classification Details** (in Document Viewer):
   - Scroll to the **"Classification Information"** section
   - You should see an **"Ensemble Classification Details"** alert (purple/secondary color)

5. **Verify Per-Model Results Table** (KEY VERIFICATION!):
   - Within the "Ensemble Classification Details" alert
   - Look for a section titled: **"📊 Per-Model Results (Force Ensemble Mode)"**
   - You should see a **table** with the following structure:

   | Model       | Classification     | Confidence | Reasoning                                      |
   |-------------|--------------------|------------|------------------------------------------------|
   | RULE-BASED  | ICSR              | 95%        | Case report detected with high confidence...   |
   | BERT        | ICSR              | 87%        | Zero-shot classification indicates ICSR...     |
   | LLM         | ICSR              | 92%        | Expert LLM analysis confirms this is an...     |
   | **FINAL VERDICT** | **ICSR**    | **92%**    | Ensemble vote from 3 model(s)                  |

   **Key Points to Check**:
   - ✅ All 3 models (RULE-BASED, BERT, LLM) have entries
   - ✅ Each model has its own classification, confidence, and reasoning
   - ✅ The "FINAL VERDICT" row shows the ensemble decision
   - ✅ The "Ensemble vote from X model(s)" indicates 3 models were used

### Phase 5: Verify Elasticsearch Storage

**Terminal Verification**:
```bash
# Check a single document's individual_results field
curl -s -X GET "http://localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'{
  "size": 1,
  "sort": [{"created_at": {"order": "desc"}}],
  "_source": ["title", "classification", "classification_confidence", "ensemble_models_used", "individual_results", "decision_path"]
}' | jq -r '.hits.hits[0]._source'
```

**Expected Output**:
```json
{
  "title": "Stevens-Johnson syndrome following...",
  "classification": "ICSR",
  "classification_confidence": 0.92,
  "ensemble_models_used": ["rule_based", "bert", "llm"],
  "decision_path": "Rule→BERT→LLM(Ensemble)",
  "individual_results": {
    "rule_based": {
      "classification": "ICSR",
      "confidence": 0.95,
      "reasoning": "Case report detected..."
    },
    "bert": {
      "classification": "ICSR",
      "confidence": 0.87,
      "reasoning": "Zero-shot classification..."
    },
    "llm": {
      "classification": "ICSR",
      "confidence": 0.92,
      "reasoning": "Expert LLM analysis..."
    }
  }
}
```

---

## ✅ Success Criteria

### Phase 1 Success:
- ☑️ Ingestion starts without errors
- ☑️ Toast notification confirms ingestion started

### Phase 2 Success:
- ☑️ Documents appear in Document Library (should be 5 documents)
- ☑️ All documents have classification badges (ICSR, Safety_Information, or Non-ICSR)

### Phase 3 Success (CRITICAL):
- ☑️ **Per-Model Results Table** is visible in Document Viewer
- ☑️ Table shows **3 rows** (RULE-BASED, BERT, LLM)
- ☑️ Each row has **classification, confidence, and reasoning**
- ☑️ **FINAL VERDICT** row is present at the bottom
- ☑️ Ensemble says "Ensemble vote from **3** model(s)" (not 1 or 2)

### Phase 4 Success (Technical):
- ☑️ Elasticsearch `individual_results` field is populated for all documents
- ☑️ `ensemble_models_used` array contains all 3 models: `["rule_based", "bert", "llm"]`
- ☑️ `decision_path` shows full ensemble flow (e.g., "Rule→BERT→LLM(Ensemble)")

---

## 🐛 Troubleshooting

### Issue 1: Toggle Not Visible
**Symptom**: "Force Full Ensemble" checkbox doesn't appear  
**Cause**: ICSR Classification checkbox is not enabled  
**Fix**: Make sure you **check** the "ICSR Classification" checkbox first. The Force Ensemble toggle only appears after ICSR is enabled.

---

### Issue 2: No Per-Model Table in Document Viewer
**Symptom**: Document Viewer shows classification but no per-model table  
**Possible Causes**:
1. **Force Ensemble was not enabled during ingestion**
   - **Fix**: Delete documents, re-ingest with the toggle **checked**

2. **Old frontend bundle is cached**
   - **Fix**: Hard refresh browser (Cmd+Shift+R on Mac, Ctrl+Shift+F5 on Windows)
   - **Verify**: Check browser console for `DocumentViewer.js` logs
   - **Nuclear Option**: Clear browser cache completely

3. **`individual_results` not stored in Elasticsearch**
   - **Fix**: Check Elasticsearch using terminal command above
   - **If missing**: Restart API Gateway: `docker-compose restart api-gateway`

---

### Issue 3: Only 1 or 2 Models in Table
**Symptom**: Table shows only RULE-BASED, or RULE-BASED + BERT, but not LLM  
**Cause**: Backend is using intelligent cascade instead of force ensemble  
**Possible Reasons**:
1. **Force Ensemble parameter not passed**:
   - Check browser network tab for the ingestion API call
   - Look for `"force_ensemble": true` in the request payload
   - **If missing**: Frontend rebuild required: `docker-compose restart frontend`

2. **API Gateway not passing the parameter**:
   - Check API Gateway logs: `docker logs api-gateway | tail -100`
   - **If parameter not logged**: Ensure API Gateway was rebuilt (see "Backend Rebuild" section below)

3. **PV Classification Service not receiving it**:
   - Check PV service logs: `docker logs pv-classification-service | tail -100`
   - **If parameter not logged**: Restart PV service: `docker-compose restart pv-classification-service`

---

### Issue 4: Classification Errors in Logs
**Symptom**: Documents appear but have no classification, or error badges  
**Check Logs**:
```bash
# Check API Gateway
docker logs api-gateway --tail 50 | grep -i "error\|classification"

# Check PV Classification Service
docker logs pv-classification-service --tail 50 | grep -i "error\|llm"

# Check Literature Automation
docker logs literature-automation --tail 50 | grep -i "error"
```

**Common Errors**:
- **"OpenAI API key not found"**: Ensure `.env` file has `OPENAI_API_KEY`
- **"Ollama connection failed"**: Ensure Ollama is running: `docker ps | grep ollama`
- **"BERT model not found"**: First-time use downloads the model, may take 2-3 minutes

---

### Issue 5: Documents Not Appearing in UI
**Symptom**: Ingestion starts but no documents in Document Library  
**Steps**:
1. **Check Elasticsearch**:
   ```bash
   curl -s http://localhost:9200/documents/_count | jq '.'
   ```
   - **If count is 0**: Ingestion failed, check logs
   - **If count > 0**: Frontend refresh issue

2. **Check Literature Automation Service**:
   ```bash
   docker logs literature-automation --tail 50
   ```
   - Look for "Ingestion job completed" messages

3. **Restart Frontend**:
   ```bash
   docker-compose restart frontend
   ```

---

## 🔧 Backend Rebuild (If Needed)

If changes to backend code were made after initial testing:

```bash
# Stop, rebuild, and restart API Gateway
docker-compose stop api-gateway
docker-compose build --no-cache api-gateway
docker-compose up -d api-gateway

# Restart PV Classification Service
docker-compose restart pv-classification-service

# Restart Frontend (if UI changes were made)
docker-compose stop frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## 📊 Expected Results Summary

### Before Force Ensemble:
- **Intelligent Cascade**: Only 1-2 models run per document
- **Decision Path**: "Rule" OR "Rule→BERT" OR "Rule→BERT→LLM"
- **UI**: No per-model table, only final classification

### After Force Ensemble:
- **Full Ensemble**: **All 3 models** run for every document
- **Decision Path**: "Rule→BERT→LLM(Ensemble)" (always)
- **UI**: **Per-model results table** with 3 rows + final verdict
- **Elasticsearch**: `individual_results` populated with all 3 models

---

## 🎓 What This Demonstrates

### Technical Value:
1. **Transparency**: Users can see how each model voted
2. **Validation**: Verify ensemble methodology is working correctly
3. **Debugging**: Identify which model is underperforming
4. **Comparison**: Compare rule-based, ML (BERT), and LLM approaches side-by-side

### Business Value:
1. **Trust**: Explainable AI with full model breakdown
2. **Compliance**: Audit trail for regulatory requirements
3. **Quality Assurance**: Validate classification accuracy with multiple models
4. **Model Improvement**: Identify training/rule refinement opportunities

---

## 📝 Test Results Log

Use this section to record your test results:

### Test Run 1:
- **Date**: __________
- **Search Query**: __________
- **Force Ensemble Enabled**: ☐ Yes ☐ No
- **Documents Ingested**: __________
- **Per-Model Table Visible**: ☐ Yes ☐ No
- **Number of Models in Table**: __________
- **Issues Encountered**: __________
- **Status**: ☐ Pass ☐ Fail

### Test Run 2:
- **Date**: __________
- **Search Query**: __________
- **Force Ensemble Enabled**: ☐ Yes ☐ No
- **Documents Ingested**: __________
- **Per-Model Table Visible**: ☐ Yes ☐ No
- **Number of Models in Table**: __________
- **Issues Encountered**: __________
- **Status**: ☐ Pass ☐ Fail

---

## 📞 Quick Reference Commands

```bash
# 1. Monitor ingestion in real-time
./monitor_pubmed_ingestion.sh

# 2. Check document count
curl -s http://localhost:9200/documents/_count | jq '.count'

# 3. Get latest document details (including individual_results)
curl -s -X GET "http://localhost:9200/documents/_search" -H 'Content-Type: application/json' -d'{
  "size": 1,
  "sort": [{"created_at": {"order": "desc"}}],
  "_source": ["title", "classification", "ensemble_models_used", "individual_results"]
}' | jq -r '.hits.hits[0]._source'

# 4. Check API Gateway logs
docker logs api-gateway --tail 100 | grep -i "force_ensemble\|classification"

# 5. Check PV Classification Service logs
docker logs pv-classification-service --tail 100 | grep -i "ensemble\|force"

# 6. Restart all relevant services
docker-compose restart api-gateway pv-classification-service frontend

# 7. Clear all documents (fresh start)
curl -X DELETE "http://localhost:9200/documents" && curl -X PUT "http://localhost:9200/documents"
```

---

## ✨ Next Steps After Successful Testing

Once this test is successful:

1. **Create Summary Document**: Document the feature implementation and test results
2. **Update User Documentation**: Add Force Ensemble to user manual
3. **Performance Benchmarking**: Compare processing time and accuracy with/without force ensemble
4. **Production Deployment**: Plan rollout strategy for production environment
5. **User Training**: Prepare training materials for end users

---

**Status**: Ready for UI Testing 🚀  
**Backend Integration**: ✅ Complete  
**Frontend Integration**: ✅ Complete  
**Elasticsearch Persistence**: ✅ Complete  
**UI Rendering**: ✅ Complete  

**Expected Test Duration**: 10-15 minutes  
**Prerequisites**: OpenAI API key configured, Ollama running (if using local LLM)  
**Impact**: Enables full transparency in ensemble classification with per-model result visualization
