# Testing Guide: Literature & ICSR Automation Modules

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [UI Testing](#ui-testing)
3. [API Testing](#api-testing)
4. [Integration Testing](#integration-testing)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### ✅ Verify All Services Are Running

```bash
docker ps | grep -E "(literature|icsr|api-gateway)"
```

Expected output:
- `literature-automation` - Port 8009 (healthy)
- `icsr-automation` - Port 8010 (healthy)
- `api-gateway` - Port 8000

### ✅ Check Service Health

```bash
# Literature Service
curl http://localhost:8009/health

# ICSR Service
curl http://localhost:8010/health

# API Gateway
curl http://localhost:8000/health
```

---

## 🖥️ UI Testing

### **Test 1: Access the Modules**

1. **Open Browser**: http://localhost:3000
2. **Login**: 
   - Email: `admin@example.com`
   - Password: `admin123`
3. **Verify Sidebar**: Look for these menu items:
   - 📚 **Literature Automation**
   - ✉️ **ICSR Automation**

### **Test 2: Literature Automation UI**

#### **2.1 Search Functionality**
1. Click **"Literature Automation"** in sidebar
2. Enter search parameters:
   - **Query**: `COVID-19 vaccine adverse events`
   - **Source**: Select `PubMed`
   - **Max Results**: `10`
   - **Date From**: `2020-01-01`
3. Click **"Search Literature"**
4. **Expected**: Loading indicator → Results list

#### **2.2 View Article Details**
1. Click on any article in the results
2. **Expected**: Expanded view showing:
   - Full abstract
   - Authors
   - Journal information
   - Publication date

#### **2.3 Classify Article**
1. Select an article
2. Click **"Classify"** button
3. **Expected**: Classification result with:
   - Type (ICSR, Non-ICSR, Safety Info, Rejected)
   - Confidence score
   - Rationale

#### **2.4 Extract ICSR Data**
1. For ICSR-classified articles, click **"Extract Data"**
2. **Expected**: Extracted structured data:
   - Patient information
   - Product details
   - Adverse events
   - Reporter information

### **Test 3: ICSR Automation UI**

#### **3.1 View Statistics Dashboard**
1. Click **"ICSR Automation"** in sidebar
2. **Expected**: Dashboard showing:
   - Total emails processed
   - Valid ICSRs count
   - Invalid cases
   - XML files generated

#### **3.2 Process Email**
1. Click **"Process New Email"** button
2. Fill in email details:
   ```
   Subject: Adverse Event Report - Patient 12345
   Body: Patient experienced severe headache after taking Drug X...
   Sender: doctor@hospital.com
   ```
3. Click **"Process"**
4. **Expected**: Classification result

#### **3.3 View ICSR Cases**
1. Navigate to **"ICSR Cases"** tab
2. **Expected**: Table showing:
   - Case ID
   - Classification
   - Date processed
   - Status
   - Actions (View, Edit, Generate XML)

#### **3.4 Generate XML**
1. Select a validated ICSR case
2. Click **"Generate ICH E2B XML"**
3. **Expected**: XML file download

---

## 🔌 API Testing

### **Literature Automation API**

#### **Test Available Sources**
```bash
curl -s http://localhost:8009/api/v1/literature/sources | jq '.'
```

**Expected Output**:
```json
{
  "sources": [
    {"id": "pubmed", "name": "PubMed", ...},
    {"id": "embase", "name": "Embase", ...},
    {"id": "cochrane", "name": "Cochrane Library", ...}
  ]
}
```

#### **Test Literature Search**
```bash
curl -X POST http://localhost:8009/api/v1/literature/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "COVID-19 vaccine adverse events",
    "sources": ["pubmed"],
    "max_results": 5,
    "date_from": "2020-01-01"
  }' | jq '.articles | length'
```

#### **Test Article Classification**
```bash
curl -X POST http://localhost:8009/api/v1/literature/classify \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "title": "Severe allergic reaction to vaccine",
      "abstract": "Patient developed anaphylaxis...",
      "authors": ["Smith J"],
      "journal": "J Adverse Events",
      "publication_date": "2021-06-15"
    }
  }' | jq '.'
```

**Expected Output**:
```json
{
  "classification": "ICSR",
  "confidence": 0.95,
  "rationale": "Article describes individual case with adverse event..."
}
```

### **ICSR Automation API**

#### **Test Statistics**
```bash
curl -s http://localhost:8010/api/v1/icsr/statistics | jq '.'
```

**Expected Output**:
```json
{
  "total_processed": 42,
  "valid_icsrs": 35,
  "invalid_icsrs": 7,
  "xml_generated": 30,
  "average_processing_time": 2.5
}
```

#### **Test Email Processing**
```bash
curl -X POST http://localhost:8010/api/v1/icsr/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test-001",
    "subject": "Adverse Event Report",
    "body": "Patient: John Doe, Age: 45, Drug: ABC 50mg, Event: Headache...",
    "sender": "dr.smith@hospital.com",
    "received_date": "2024-01-15T10:00:00Z"
  }' | jq '.'
```

**Expected Output**:
```json
{
  "classification": "valid_icsr",
  "confidence": 0.89,
  "extracted_data": {
    "patient": {...},
    "product": {...},
    "events": [...]
  }
}
```

---

## 🔗 Integration Testing

### **Test 1: End-to-End Literature Workflow**

1. **Search** → Get articles from PubMed
2. **Classify** → Identify ICSR articles
3. **Extract** → Get structured ICSR data
4. **Validate** → Review extracted data
5. **Generate** → Create ICH E2B XML

### **Test 2: End-to-End ICSR Email Workflow**

1. **Receive** → Process incoming email
2. **Classify** → Valid/Invalid ICSR
3. **Extract** → Get case details
4. **Validate** → Review and confirm
5. **Generate** → Create XML for submission

### **Test 3: Multi-Source Integration**

Test data flow between:
- Literature Service → ICSR Service
- ICSR Service → Neo4j (for knowledge graph)
- ICSR Service → Elasticsearch (for search)

---

## 🐛 Troubleshooting

### **Issue: Endpoints Return 404 Not Found**

**Solution**: Check if endpoints are implemented
```bash
docker exec literature-automation python3 -c "from main import app; print([route.path for route in app.routes])"
```

### **Issue: Service Unhealthy**

**Solution**: Check service logs
```bash
docker logs literature-automation --tail 50
docker logs icsr-automation --tail 50
```

### **Issue: UI Not Showing New Modules**

**Solution 1**: Hard refresh browser
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

**Solution 2**: Rebuild frontend
```bash
docker-compose down frontend
docker-compose up --build frontend -d
```

### **Issue: API Gateway Can't Reach Services**

**Solution**: Check network connectivity
```bash
docker exec api-gateway curl http://literature-automation:8009/health
docker exec api-gateway curl http://icsr-automation:8010/health
```

---

## 📊 Test Data Examples

### **Sample ICSR Case (Literature)**
```
Title: "Anaphylaxis Following COVID-19 Vaccination"
Abstract: "A 45-year-old female with no known allergies developed anaphylaxis 
30 minutes after receiving the first dose of mRNA COVID-19 vaccine. Patient 
presented with urticaria, hypotension (BP 80/40), and respiratory distress. 
Treatment: Epinephrine 0.5mg IM, IV fluids, antihistamines. Outcome: Complete 
recovery after 2 hours of observation."
```

### **Sample ICSR Case (Email)**
```
From: dr.johnson@hospital.com
Subject: Urgent - Adverse Drug Reaction Report

Patient ID: 12345
Name: [Redacted per HIPAA]
Age: 67
Gender: Male
Date of Event: 2024-01-10

Product: DrugName XR 100mg (Batch: ABC123)
Indication: Hypertension
Dose: 100mg once daily

Adverse Event: Severe Stevens-Johnson Syndrome
Onset: 5 days after starting medication
Outcome: Hospitalized, drug discontinued, recovering

Reporter: Dr. Sarah Johnson, MD
Hospital: General Hospital, Cardiology Dept
Contact: dr.johnson@hospital.com
```

---

## ✅ Success Criteria

A successful test should demonstrate:

1. ✅ **UI Accessibility**: All pages load without errors
2. ✅ **Search Functionality**: Returns relevant results
3. ✅ **Classification**: Correctly identifies ICSRs
4. ✅ **Data Extraction**: Extracts structured information
5. ✅ **XML Generation**: Produces valid ICH E2B files
6. ✅ **API Responses**: All endpoints return expected data
7. ✅ **Error Handling**: Graceful error messages
8. ✅ **Performance**: Response times < 5 seconds

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________

| Test Case | Status | Notes |
|-----------|--------|-------|
| UI Access | ⬜ Pass / ⬜ Fail | |
| Literature Search | ⬜ Pass / ⬜ Fail | |
| Classification | ⬜ Pass / ⬜ Fail | |
| ICSR Extraction | ⬜ Pass / ⬜ Fail | |
| Email Processing | ⬜ Pass / ⬜ Fail | |
| XML Generation | ⬜ Pass / ⬜ Fail | |
| API Endpoints | ⬜ Pass / ⬜ Fail | |
```

---

## 🚀 Next Steps After Testing

1. **Report Issues**: Document any bugs or missing features
2. **Request Enhancements**: Suggest improvements
3. **Integration**: Connect to real data sources (PubMed API, email server)
4. **Validation**: Have domain experts review extracted data
5. **Production Deployment**: Move to production environment

---

**Need Help?**
- Check service logs: `docker logs <service-name>`
- Review API documentation: `http://localhost:8009/docs`
- Contact: Your development team

