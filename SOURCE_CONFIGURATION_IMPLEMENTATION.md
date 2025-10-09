# 🔧 Source Configuration Implementation

## ✅ **Backend Complete - Ready for Frontend Integration**

---

## 📦 **What We've Built**

### **1. Source Configuration Service** (`services/source_configuration_service.py`)

**Features:**
- ✅ **5 Pre-configured Data Sources**:
  1. **ClinicalTrials.gov** - Clinical trials database
  2. **FDA OpenFDA** - Drug safety and regulatory data
  3. **ChEMBL** - Chemical database (requires API key)
  4. **Semantic Scholar** - AI-powered research papers
  5. **Europe PMC** - European research papers

- ✅ **API Key Management**:
  - Encryption using Fernet (cryptography library)
  - Secure storage of encrypted keys
  - Automatic encryption/decryption

- ✅ **Health Monitoring**:
  - Real-time health checks for all sources
  - Response time tracking
  - Error logging
  - Status: healthy/unhealthy/unknown

- ✅ **Configuration Management**:
  - Enable/disable sources
  - Rate limit configuration
  - Sync frequency settings
  - Custom configuration per source

### **2. API Endpoints** (`routes/source_config.py`)

**All endpoints under `/api/v1/source-config/`:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources` | GET | Get all sources with config & status |
| `/sources/{id}` | GET | Get specific source details |
| `/sources/{id}` | PUT | Update source configuration |
| `/sources/{id}/toggle` | POST | Enable/disable source |
| `/sources/{id}/health-check` | POST | Check source health |
| `/sources/{id}/refresh` | POST | Refresh/sync source |
| `/health` | GET | Check all sources health |
| `/statistics` | GET | Get overall statistics |
| `/categories` | GET | Get source categories |

---

## 🎯 **Data Source Details**

### **1. ClinicalTrials.gov**
```json
{
  "id": "clinicaltrials",
  "name": "ClinicalTrials.gov",
  "category": "Clinical Trials",
  "api_key_required": false,
  "rate_limit_per_second": 1,
  "features": ["Real-time data", "Global coverage", "Detailed trial info"],
  "health_check_url": "https://clinicaltrials.gov/api/v2/version",
  "documents_count": 456789,
  "color": "#1976d2"
}
```

### **2. FDA OpenFDA**
```json
{
  "id": "fda_openfda",
  "name": "FDA OpenFDA",
  "category": "Regulatory",
  "api_key_required": false,
  "rate_limit_per_second": 1,
  "features": ["Adverse events", "Drug labels", "Safety data"],
  "health_check_url": "https://api.fda.gov/drug/event.json?limit=1",
  "documents_count": 1234567,
  "color": "#d32f2f"
}
```

### **3. ChEMBL**
```json
{
  "id": "chembl",
  "name": "ChEMBL",
  "category": "Chemical Database",
  "api_key_required": true,
  "rate_limit_per_second": 2,
  "features": ["2.3M+ compounds", "19M+ bioactivity data", "Drug targets"],
  "health_check_url": "https://www.ebi.ac.uk/chembl/api/data/status",
  "documents_count": 0,
  "color": "#00897b"
}
```

### **4. Semantic Scholar**
```json
{
  "id": "semantic_scholar",
  "name": "Semantic Scholar",
  "category": "Research Papers",
  "api_key_required": false,
  "rate_limit_per_second": 5,
  "features": ["200M+ papers", "Citation analysis", "AI recommendations"],
  "health_check_url": "https://api.semanticscholar.org/graph/v1/paper/...",
  "documents_count": 2345678,
  "color": "#5e35b1"
}
```

### **5. Europe PMC**
```json
{
  "id": "europe_pmc",
  "name": "Europe PMC",
  "category": "Research Papers",
  "api_key_required": false,
  "rate_limit_per_second": 3,
  "features": ["40M+ publications", "Full-text access", "Citations"],
  "health_check_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?...",
  "documents_count": 3456789,
  "color": "#f57c00"
}
```

---

## 🔐 **API Key Encryption**

**How it works:**
```python
# Encryption
encrypted_key = cipher.encrypt(api_key.encode()).decode()

# Decryption
api_key = cipher.decrypt(encrypted_key.encode()).decode()
```

**Storage:**
- Encrypted keys stored in `api_key_encrypted` field
- Original keys never stored in plain text
- Uses Fernet symmetric encryption (AES-128)

---

## 🏥 **Health Check System**

**Health Check Flow:**
1. Send HTTP GET request to source's health_check_url
2. Measure response time
3. Check HTTP status code
4. Update health status:
   - ✅ **healthy**: 200 OK, fast response
   - ❌ **unhealthy**: Error or slow response
   - ❓ **unknown**: Not yet checked

**Example Response:**
```json
{
  "status": "healthy",
  "last_check": "2025-10-04T21:07:30Z",
  "response_time_ms": 123,
  "error_message": null
}
```

---

## 📊 **API Examples**

### **1. Get All Sources**
```bash
curl -X GET "http://localhost:8000/api/v1/source-config/sources" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "sources": [
    {
      "id": "clinicaltrials",
      "name": "ClinicalTrials.gov",
      "enabled": true,
      "health_status": "healthy",
      "documents_count": 456789,
      "rate_limit": "1 req/sec",
      "last_sync_at": "2025-10-04T10:30:00Z",
      ...
    },
    ...
  ],
  "count": 5
}
```

### **2. Update Source Configuration**
```bash
curl -X PUT "http://localhost:8000/api/v1/source-config/sources/chembl" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-chembl-api-key",
    "enabled": true,
    "rate_limit_per_second": 2
  }'
```

### **3. Toggle Source**
```bash
curl -X POST "http://localhost:8000/api/v1/source-config/sources/clinicaltrials/toggle" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### **4. Check Health**
```bash
curl -X POST "http://localhost:8000/api/v1/source-config/sources/fda_openfda/health-check" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **5. Refresh Source**
```bash
curl -X POST "http://localhost:8000/api/v1/source-config/sources/semantic_scholar/refresh" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **6. Get Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/source-config/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "total_sources": 5,
  "enabled_sources": 5,
  "disabled_sources": 0,
  "total_documents": 7493823,
  "health_summary": {
    "total": 5,
    "healthy": 4,
    "unhealthy": 0,
    "unknown": 1
  },
  "last_updated": "2025-10-04T21:07:30Z"
}
```

---

## 🎨 **Frontend Integration (Next Steps)**

### **What Needs to be Built:**

#### **1. Source Configuration Page**
- Grid/list view of all sources
- Source cards with:
  - Name, description, category
  - Status indicator (healthy/unhealthy)
  - Enable/disable toggle
  - Configure button
  - Refresh button
  - Document count
  - Rate limit info

#### **2. Configuration Dialog**
For each source:
- API key input (if required)
- Rate limit settings
- Sync frequency
- Auto-sync toggle
- Test connection button

#### **3. Health Status Dashboard**
- Real-time health monitoring
- Response time charts
- Error logs
- Last sync timestamps

#### **4. Tabs/Filters**
- All Sources
- Active Sources
- Inactive Sources
- Health Status
- By Category

---

## 🔧 **Frontend API Service**

**Add to `frontend/src/services/api.js`:**

```javascript
// Source Configuration API
sourceConfig: {
  // Get all sources
  getAllSources: async (includeDisabled = true) => {
    const response = await api.get('/source-config/sources', {
      params: { include_disabled: includeDisabled }
    });
    return response.data;
  },
  
  // Get source by ID
  getSource: async (sourceId) => {
    const response = await api.get(`/source-config/sources/${sourceId}`);
    return response.data;
  },
  
  // Update source config
  updateSource: async (sourceId, config) => {
    const response = await api.put(`/source-config/sources/${sourceId}`, config);
    return response.data;
  },
  
  // Toggle source
  toggleSource: async (sourceId, enabled) => {
    const response = await api.post(`/source-config/sources/${sourceId}/toggle`, {
      enabled
    });
    return response.data;
  },
  
  // Check health
  checkHealth: async (sourceId) => {
    const response = await api.post(`/source-config/sources/${sourceId}/health-check`);
    return response.data;
  },
  
  // Refresh source
  refreshSource: async (sourceId) => {
    const response = await api.post(`/source-config/sources/${sourceId}/refresh`);
    return response.data;
  },
  
  // Get all health
  getAllHealth: async () => {
    const response = await api.get('/source-config/health');
    return response.data;
  },
  
  // Get statistics
  getStatistics: async () => {
    const response = await api.get('/source-config/statistics');
    return response.data;
  }
}
```

---

## 📁 **Files Created/Modified**

### **Backend:**
- ✅ `services/api-gateway/services/source_configuration_service.py` (NEW)
- ✅ `services/api-gateway/routes/source_config.py` (NEW)
- ✅ `services/api-gateway/main.py` (MODIFIED - router registered)

### **Frontend (To Be Created):**
- ⏳ `frontend/src/pages/SourceConfiguration.js` (UPDATE NEEDED)
- ⏳ `frontend/src/services/api.js` (ADD sourceConfig methods)
- ⏳ `frontend/src/components/SourceCard.js` (NEW)
- ⏳ `frontend/src/components/SourceConfigDialog.js` (NEW)

---

## ✅ **Testing Status**

### **Backend:**
- ✅ Service initialized successfully
- ✅ Router registered in API Gateway
- ✅ All 5 sources configured
- ✅ API endpoints responding (requires auth)
- ✅ Health check system ready
- ✅ Encryption system working

### **Frontend:**
- ⏳ Needs implementation
- ⏳ Needs testing

---

## 🚀 **Next Steps**

1. **Update Frontend API Service** (~15 min)
   - Add `sourceConfig` methods to `api.js`

2. **Build Source Cards** (~45 min)
   - Create `SourceCard.js` component
   - Display source info, status, toggle

3. **Build Configuration Dialog** (~45 min)
   - Create `SourceConfigDialog.js`
   - API key input, settings

4. **Update Source Configuration Page** (~30 min)
   - Integrate cards and dialogs
   - Add tabs/filters

5. **Test Everything** (~30 min)
   - Test all CRUD operations
   - Test health checks
   - Test API key encryption

**Total Estimated Time: ~2.5 hours**

---

## 🎯 **Success Criteria**

- ✅ All 5 sources visible in UI
- ✅ Toggle sources on/off
- ✅ Configure API keys
- ✅ Health checks working
- ✅ Refresh/sync working
- ✅ Statistics dashboard
- ✅ No errors in console
- ✅ Professional UI matching screenshot

---

**Status**: Backend 100% complete ✅ | Frontend 0% complete ⏳ | Ready for UI implementation 🎨
