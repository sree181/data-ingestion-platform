# 🎯 Phase 3: Investigation Board - Integration & Architecture Plan

## **✅ Backend Complete!**

### **What We Built:**
1. ✅ **Database Models** (`db/models/investigation.py`)
2. ✅ **Pydantic Schemas** (`schemas/investigation.py`)
3. ✅ **Service Layer** (`services/investigation_service.py`)
4. ✅ **API Routes** (`routes/investigation.py`)
5. ✅ **Registered in FastAPI** (`main.py`)

---

## **🔄 Integration with Existing System**

### **1. Knowledge Hub → Investigation Board Flow**

```
Knowledge Hub (Frontend)
     ↓
Click Entity → Open Drawer
     ↓
"📌 Pin to Board" Button
     ↓
Select/Create Investigation Board
     ↓
POST /api/v1/investigations/pin
     ↓
Entity saved to PostgreSQL
     ↓
Board canvas updates with new entity
```

**UI Changes Needed:**
- Add **"Pin to Board"** button in Knowledge Hub entity drawer (next to "Chat" section)
- Modal dialog to select existing board or create new one
- Show pin confirmation with link to board

---

### **2. Investigation Board Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
├─────────────────────────────────────────────────────────┤
│  Investigation Boards Page                               │
│    - Board List View                                     │
│    - Board Canvas (react-beautiful-dnd for drag-drop)   │
│    - Entity Cards with Notes                            │
│    - Connection Lines                                    │
│    - Export Button                                       │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│                  API Gateway (FastAPI)                   │
├─────────────────────────────────────────────────────────┤
│  /api/v1/investigations/boards                          │
│  /api/v1/investigations/pin                             │
│  /api/v1/investigations/findings                        │
│  /api/v1/investigations/connections                     │
│  /api/v1/investigations/boards/{id}/export              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL (Persistent Storage)             │
├─────────────────────────────────────────────────────────┤
│  investigation_boards                                    │
│  pinned_entities (with x,y positions)                   │
│  investigation_findings (notes/evidence)                │
│  entity_connections (user-drawn links)                  │
└─────────────────────────────────────────────────────────┘
```

---

## **3. Data Flow Between Components**

### **Neo4j (Knowledge Hub) ↔ PostgreSQL (Investigation Boards)**

**Knowledge Hub Data (Read-Only):**
- Neo4j stores **entity metadata** (name, type, properties)
- Neo4j stores **AI-extracted relationships**

**Investigation Boards (User-Generated):**
- PostgreSQL stores **user's investigation boards**
- PostgreSQL stores **which entities user pinned**
- PostgreSQL stores **user's notes on entities**
- PostgreSQL stores **user-drawn connections**

**Key Insight:** 
- We **reference** entities by name (not store copies)
- User investigates entities discovered in Knowledge Hub
- User adds their own insights, hypotheses, and connections

---

## **4. Frontend Component Structure**

```
src/pages/InvestigationBoards.js
├── BoardListView
│   ├── BoardCard (title, entity count, last updated)
│   └── CreateBoardDialog
│
└── BoardDetailView
    ├── BoardHeader (title, description, status, export button)
    ├── BoardCanvas
    │   ├── EntityCard (draggable)
    │   │   ├── EntityName
    │   │   ├── EntityType badge
    │   │   ├── Notes icon with count
    │   │   └── Actions (unpin, add note)
    │   ├── ConnectionLines (SVG/Canvas)
    │   └── ConnectionDialog (create/edit connections)
    │
    ├── NotesPanel (drawer)
    │   ├── NotesList
    │   ├── AddNoteForm
    │   └── NoteFilters (by type: note, evidence, hypothesis)
    │
    └── FloatingActions
        ├── Export button
        ├── Share button
        └── Settings button
```

---

## **5. Bigger Picture: Complete User Journey**

### **Discovery → Investigation → Action**

```
PHASE 1: Discovery
    User uploads PDFs
         ↓
    AI extracts entities & relationships
         ↓
    Data goes to Elasticsearch + Neo4j
         ↓
    Knowledge Hub visualizes the graph

PHASE 2: Exploration
    User explores Knowledge Hub
         ↓
    Clicks entity → Sees source documents
         ↓
    Asks questions → AI answers with citations
         ↓
    User identifies interesting entities

PHASE 3: Investigation (NEW!)
    User pins entities to Investigation Board
         ↓
    User adds notes, hypotheses, evidence
         ↓
    User draws connections between entities
         ↓
    User organizes findings by case/project
         ↓
    User exports for reports/collaboration

FUTURE PHASES:
    - Collaboration (share boards with team)
    - Alerts (notify when new related entities appear)
    - Automated insights (AI suggests connections)
    - Integration with case management systems
```

---

## **6. Value Proposition**

### **For Domain Experts:**

| Before | After |
|--------|-------|
| ❌ Copy-paste entities to Word docs | ✅ Pin entities to organized boards |
| ❌ Lose track of investigation threads | ✅ Visual canvas with connections |
| ❌ Notes scattered across tools | ✅ All notes attached to entities |
| ❌ Hard to share findings | ✅ Export as PDF/JSON |
| ❌ Can't see the full picture | ✅ Bird's-eye view of entire case |

### **Example Use Cases:**

1. **Legal Attorney:**
   - Investigates pharmaceutical adverse events
   - Pins: Drug entities, adverse reactions, clinical trials
   - Notes: Evidence from documents, legal precedents
   - Connections: Drug → Side Effect → Clinical Trial
   - Export: PDF report for case file

2. **Clinical Scientist:**
   - Researches drug interactions
   - Pins: Multiple drugs, diseases, biomarkers
   - Notes: Hypothesis, experimental results
   - Connections: Drug A + Drug B → Interaction
   - Export: JSON for analysis tools

3. **Physician:**
   - Investigates rare disease treatment options
   - Pins: Disease, symptoms, treatments, studies
   - Notes: Patient observations, treatment efficacy
   - Connections: Treatment → Symptom improvement
   - Export: PDF for medical record

---

## **7. Technical Implementation Details**

### **Database Migration:**
```sql
-- Run Alembic migration to create tables
alembic revision --autogenerate -m "Add investigation boards"
alembic upgrade head
```

### **Frontend Dependencies:**
```json
{
  "react-beautiful-dnd": "^13.1.1",  // Drag & drop
  "react-draggable": "^4.4.5",       // Alternative
  "canvas-confetti": "^1.6.0",       // Celebration on export
  "jspdf": "^2.5.1",                 // PDF export
  "file-saver": "^2.0.5"             // Download files
}
```

### **API Integration (frontend/src/services/api.js):**
```javascript
// Investigation Board API methods
investigationBoards: {
  list: () => api.get('/investigations/boards'),
  create: (data) => api.post('/investigations/boards', data),
  get: (boardId) => api.get(`/investigations/boards/${boardId}`),
  update: (boardId, data) => api.put(`/investigations/boards/${boardId}`, data),
  delete: (boardId) => api.delete(`/investigations/boards/${boardId}`),
  
  pin: (data) => api.post('/investigations/pin', data),
  unpin: (pinId) => api.delete(`/investigations/pin/${pinId}`),
  updatePin: (pinId, data) => api.put(`/investigations/pin/${pinId}`, data),
  
  addFinding: (data) => api.post('/investigations/findings', data),
  updateFinding: (findingId, data) => api.put(`/investigations/findings/${findingId}`, data),
  deleteFinding: (findingId) => api.delete(`/investigations/findings/${findingId}`),
  
  createConnection: (data) => api.post('/investigations/connections', data),
  deleteConnection: (connId) => api.delete(`/investigations/connections/${connId}`),
  
  export: (boardId) => api.get(`/investigations/boards/${boardId}/export`)
}
```

---

## **8. Next Implementation Steps**

### **Step 1: Database Migration** (5 min)
```bash
cd services/api-gateway
alembic revision --autogenerate -m "Add investigation boards"
alembic upgrade head
```

### **Step 2: Test Backend APIs** (10 min)
```bash
# Test create board
curl -X POST http://localhost:8000/api/v1/investigations/boards \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Test Case", "description": "Test"}'

# Test pin entity
curl -X POST http://localhost:8000/api/v1/investigations/pin \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"board_id": "<board_id>", "entity_name": "Drug A", "entity_type": "Drug"}'
```

### **Step 3: Add Pin Button to Knowledge Hub** (20 min)
- Modify `frontend/src/pages/KnowledgeHub.js`
- Add button in entity drawer
- Create pin dialog component

### **Step 4: Build Investigation Boards Page** (2-3 hours)
- Create `frontend/src/pages/InvestigationBoards.js`
- Implement board list view
- Implement board canvas with drag-drop
- Add notes panel

### **Step 5: Implement Export** (30 min)
- PDF export with jsPDF
- JSON download
- Include all entities, notes, connections

### **Step 6: Polish & Test** (1 hour)
- Loading states
- Error handling
- Responsive design
- End-to-end testing

---

## **9. Timeline Estimate**

| Phase | Time | Tasks |
|-------|------|-------|
| ✅ Backend | 2 hours | COMPLETE |
| 🔄 Database Migration | 5 min | Alembic migration |
| 🔄 API Testing | 10 min | curl/Postman tests |
| 🔄 Pin Button | 20 min | Knowledge Hub integration |
| 🔄 Frontend Core | 2-3 hours | Boards page + canvas |
| 🔄 Export | 30 min | PDF/JSON export |
| 🔄 Polish | 1 hour | UI/UX refinement |
| **Total** | **~4-5 hours** | **End-to-end MVP** |

---

## **10. How It Fits Into the Product**

```
DATA INGESTION PLATFORM
├── Document Upload & Processing ✅
├── AI Entity Extraction ✅
├── Elasticsearch Search ✅
├── Neo4j Knowledge Graph ✅
│
├── Knowledge Hub (Phase 1-2) ✅
│   ├── Interactive Graph Visualization
│   ├── Source Document Linking
│   └── Entity-Centric Chat
│
├── Investigation Board (Phase 3) 🔄 NEW
│   ├── Pin Entities for Investigation
│   ├── Add Notes & Findings
│   ├── Organize by Cases
│   └── Export Reports
│
└── Future Enhancements 📋
    ├── Team Collaboration
    ├── Automated Insights
    ├── Alert System
    └── External Integrations
```

---

## **Summary**

**Backend:** ✅ **COMPLETE** - All APIs ready
**Frontend:** 🔄 **READY TO BUILD** - Clear architecture
**Integration:** 🎯 **WELL-DEFINED** - Seamless with Knowledge Hub
**Value:** 💎 **HIGH** - Transforms discovery into actionable intelligence

**Next:** Run database migration and test backend, then build frontend UI!

---

**Status:** Backend Complete | Ready for Migration & Frontend Development

