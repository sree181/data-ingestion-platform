# 🚀 Phase 3: Investigation Board - Implementation Plan

## **Overview** 📋

The Investigation Board allows users to:
- **Pin entities** from the Knowledge Hub for further investigation
- **Add notes & findings** to pinned entities
- **Organize investigations** with boards (cases/projects)
- **Export findings** for reports and collaboration
- **Track investigation progress**

---

## **Backend Architecture** 🏗️

### **Database Schema (PostgreSQL)**

```sql
-- Investigation Boards (Cases/Projects)
CREATE TABLE investigation_boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    space_id UUID REFERENCES spaces(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, archived, completed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Pinned Entities
CREATE TABLE pinned_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES investigation_boards(id) ON DELETE CASCADE,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    pin_reason TEXT,
    position_x FLOAT DEFAULT 0, -- For board layout
    position_y FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Investigation Findings/Notes
CREATE TABLE investigation_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pinned_entity_id UUID NOT NULL REFERENCES pinned_entities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    finding_type VARCHAR(50), -- note, evidence, hypothesis, conclusion
    content TEXT NOT NULL,
    tags TEXT[], -- Array of tags for categorization
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Entity Connections (User-drawn connections between pinned entities)
CREATE TABLE entity_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES investigation_boards(id) ON DELETE CASCADE,
    source_entity_id UUID NOT NULL REFERENCES pinned_entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES pinned_entities(id) ON DELETE CASCADE,
    connection_type VARCHAR(100), -- hypothesis, evidence, causal, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **API Endpoints**

```
GET    /api/v1/investigations/boards                  - List user's boards
POST   /api/v1/investigations/boards                  - Create new board
GET    /api/v1/investigations/boards/{board_id}       - Get board details
PUT    /api/v1/investigations/boards/{board_id}       - Update board
DELETE /api/v1/investigations/boards/{board_id}       - Delete board

POST   /api/v1/investigations/boards/{board_id}/pin   - Pin an entity
DELETE /api/v1/investigations/boards/{board_id}/pin/{pin_id} - Unpin
PUT    /api/v1/investigations/boards/{board_id}/pin/{pin_id} - Update pin position

POST   /api/v1/investigations/findings                - Add finding/note
PUT    /api/v1/investigations/findings/{finding_id}   - Update finding
DELETE /api/v1/investigations/findings/{finding_id}   - Delete finding

POST   /api/v1/investigations/connections             - Create connection
DELETE /api/v1/investigations/connections/{conn_id}   - Delete connection

GET    /api/v1/investigations/boards/{board_id}/export - Export board
```

---

## **Frontend UI** 🎨

### **Layout**

```
┌─────────────────────────────────────────────────────────┐
│ Investigation Boards                           [+ New]   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐│
│  │ Case Alpha    │  │ Clinical Trial │  │ FDA Review  ││
│  │ 5 entities    │  │ 12 entities    │  │ 3 entities  ││
│  │ Active        │  │ In Progress    │  │ Completed   ││
│  └───────────────┘  └───────────────┘  └─────────────┘│
│                                                           │
├─────────────────────────────────────────────────────────┤
│ Board: Case Alpha                      [Export] [Share]  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────┐         ┌────────────┐                  │
│  │ Drug A     │────────→│ Disease X  │                  │
│  │ Confidence │         │ Side Effect│                  │
│  │ 0.9        │         │            │                  │
│  │ [3 Notes]  │         │ [1 Note]   │                  │
│  └────────────┘         └────────────┘                  │
│                              ↓                            │
│                         ┌────────────┐                  │
│                         │ Clinical   │                  │
│                         │ Trial #123 │                  │
│                         │ [2 Notes]  │                  │
│                         └────────────┘                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### **Features**

1. **Board Management**
   - Create/edit/delete investigation boards
   - Set board status (active, archived, completed)
   - Filter boards by status

2. **Entity Pinning**
   - Pin from Knowledge Hub (button in entity drawer)
   - Select target board
   - Add pin reason
   - Drag & drop to rearrange

3. **Notes & Findings**
   - Add notes to pinned entities
   - Categorize by type (note, evidence, hypothesis)
   - Tag for organization
   - Edit/delete notes

4. **Visual Connections**
   - Draw connections between entities
   - Label connection types
   - Add connection notes

5. **Export**
   - Export as PDF report
   - Export as JSON (for sharing)
   - Include all notes & findings

---

## **Implementation Steps** 📝

### **Phase 3.1: Backend Database & API** (Current)
1. Create PostgreSQL migrations
2. Define Pydantic models
3. Implement service layer
4. Create API endpoints
5. Test with sample data

### **Phase 3.2: Frontend UI**
1. Create Investigation Boards page
2. Implement board list & creation
3. Add pin button to Knowledge Hub
4. Build board canvas with drag-drop
5. Add notes panel

### **Phase 3.3: Export & Polish**
1. Implement PDF export
2. Add JSON export
3. Polish UI/UX
4. End-to-end testing

---

## **Technical Stack** 🛠️

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, Material-UI, react-beautiful-dnd (drag & drop)
- **Export**: jsPDF (PDF export), JSON serialization
- **State**: React Context + useState for board state

---

## **User Flow** 👤

1. User explores Knowledge Hub graph
2. Clicks interesting entity → Opens drawer
3. Clicks "📌 Pin to Board" button
4. Selects/creates investigation board
5. Entity appears on board canvas
6. User adds notes, draws connections
7. Exports findings as report

---

## **Success Metrics** ✅

- Users can create and manage multiple boards
- Entities can be pinned from Knowledge Hub
- Notes and findings are saved
- Boards can be exported
- UI is intuitive and responsive

---

**Status**: Phase 3 - Starting Implementation!

