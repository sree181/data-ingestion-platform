# 🧪 Workflow Persistence & Templates - Testing Guide

## ✅ **Implementation Complete!**

All features have been implemented:
- ✅ Backend persistence (Neo4j)
- ✅ Pre-built templates (3 templates)
- ✅ Frontend UI (Save/Load/Templates dialogs)
- ✅ Full CRUD operations

---

## 🎯 **Testing Checklist**

### **1. Templates Gallery** (Easiest to test first)

**Steps:**
1. Open browser: `http://localhost:3000/workflow-builder`
2. Click **"Templates"** button in header
3. **Expected**: Dialog opens with 3 template cards:
   - Basic Document Ingestion (4 nodes)
   - Quick Document Analysis (3 nodes)
   - Knowledge Graph Builder (3 nodes)
4. Click **"Use Template"** on any card
5. **Expected**: Canvas loads with pre-configured nodes and connections

**What to verify:**
- ✅ All 3 templates appear
- ✅ Tags display correctly (colored chips)
- ✅ Node/connection counts are accurate
- ✅ Template loads to canvas when clicked
- ✅ Dialog closes after loading

---

### **2. Save Workflow**

**Steps:**
1. Create a custom workflow (drag nodes, connect them)
2. Click **"Save"** button
3. **Expected**: Save dialog opens
4. Enter:
   - Title: "My Test Workflow"
   - Description: "Testing save functionality"
   - (Optional) Check "Save as template"
5. Click **"Save Workflow"**
6. **Expected**: 
   - Success notification appears
   - Dialog closes

**What to verify:**
- ✅ Save button disabled when canvas is empty
- ✅ Dialog opens with form fields
- ✅ Title is required (shows warning if empty)
- ✅ Success message after saving
- ✅ Workflow gets a unique ID

**Backend verification:**
```bash
# Check Neo4j for saved workflow
curl -s http://localhost:8008/api/v1/workflows/list | jq '.workflows[] | {id, title, node_count}'
```

---

### **3. Load Workflow**

**Steps:**
1. Click **"Load"** button
2. **Expected**: Load dialog opens with list of saved workflows
3. **Expected**: Each workflow shows:
   - Title
   - Description
   - Node count, edge count
   - Updated date
   - Delete button (red trash icon)
4. Click on a workflow to load it
5. **Expected**:
   - Canvas clears
   - Workflow nodes/edges appear
   - Success notification
   - Dialog closes

**What to verify:**
- ✅ Empty state message if no workflows saved
- ✅ All saved workflows appear in list
- ✅ Metadata displays correctly
- ✅ Workflow loads to canvas
- ✅ Previous workflow is replaced

---

### **4. Delete Workflow**

**Steps:**
1. Open Load dialog
2. Click **red trash icon** on any workflow
3. **Expected**:
   - Workflow removed from list
   - Success notification

**What to verify:**
- ✅ Workflow disappears from list
- ✅ Workflow removed from Neo4j
- ✅ No errors in console

---

### **5. Clear Workflow**

**Steps:**
1. Load or create a workflow
2. Click **"Clear"** button
3. **Expected**:
   - Canvas resets to demo workflow (4 nodes)
   - Info notification

**What to verify:**
- ✅ Clear button disabled when canvas is empty
- ✅ Clear button disabled while workflow is running
- ✅ Canvas resets correctly

---

### **6. Run Workflow** (Integration test)

**Steps:**
1. Load any workflow (or use demo)
2. Click **"Run Workflow"**
3. **Expected**:
   - Nodes change status: pending → running → completed
   - Visual updates (colors, animations)
   - Success notification when done

**What to verify:**
- ✅ Run button disabled when canvas is empty
- ✅ Run button disabled while already running
- ✅ Node statuses update in real-time
- ✅ All nodes complete successfully

---

### **7. End-to-End Flow**

**Complete workflow:**
1. Open Templates → Use "Basic Document Ingestion"
2. Modify it (add/remove nodes)
3. Save as "Custom Pipeline v1"
4. Clear canvas
5. Load "Custom Pipeline v1"
6. Run the workflow
7. Verify it executes correctly
8. Save again (updates existing workflow)
9. Delete the workflow
10. Verify it's gone from Load dialog

---

## 🐛 **Common Issues & Solutions**

### **Issue: Templates not loading**
```bash
# Check backend logs
docker-compose logs workflow-builder | tail -20

# Test templates endpoint
curl http://localhost:8008/api/v1/workflows/templates/list | jq .
```

### **Issue: Save fails**
```bash
# Check Neo4j connection
docker ps | grep neo4j

# Test save endpoint manually
curl -X POST http://localhost:8008/api/v1/workflows/save \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "description": "Test workflow",
    "nodes": [],
    "edges": [],
    "tags": [],
    "is_template": false
  }' | jq .
```

### **Issue: Load shows empty list**
```bash
# Check if workflows exist
curl http://localhost:8008/api/v1/workflows/list | jq '.workflows | length'

# Check Neo4j directly
docker exec -it neo4j cypher-shell -u neo4j -p password123 \
  "MATCH (w:Workflow) RETURN w LIMIT 5;"
```

### **Issue: Frontend errors**
```bash
# Check browser console (F12)
# Look for API errors or React warnings

# Check frontend logs
docker-compose logs frontend | tail -20

# Rebuild frontend if needed
docker-compose build frontend && docker-compose up -d frontend
```

---

## 📊 **Backend API Testing**

### **Test all endpoints:**

```bash
# 1. List templates
curl -s http://localhost:8008/api/v1/workflows/templates/list | jq '.templates | length'
# Expected: 3

# 2. Use a template
curl -s -X POST http://localhost:8008/api/v1/workflows/templates/template_basic_ingestion/use | jq '.success'
# Expected: true

# 3. Save a workflow
WORKFLOW_ID=$(curl -s -X POST http://localhost:8008/api/v1/workflows/save \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Workflow",
    "description": "Created via API",
    "nodes": [{"id": "1", "type": "upload", "position": {"x": 0, "y": 0}, "data": {"label": "Test"}}],
    "edges": [],
    "tags": ["test"],
    "is_template": false
  }' | jq -r '.workflow_id')

echo "Created workflow: $WORKFLOW_ID"

# 4. Get workflow by ID
curl -s "http://localhost:8008/api/v1/workflows/$WORKFLOW_ID" | jq '.workflow.title'
# Expected: "API Test Workflow"

# 5. List all workflows
curl -s http://localhost:8008/api/v1/workflows/list | jq '.workflows | length'
# Expected: >= 1

# 6. Delete workflow
curl -s -X DELETE "http://localhost:8008/api/v1/workflows/$WORKFLOW_ID" | jq '.success'
# Expected: true

# 7. Verify deletion
curl -s "http://localhost:8008/api/v1/workflows/$WORKFLOW_ID" | jq '.success'
# Expected: false
```

---

## 🎨 **UI/UX Verification**

### **Visual checks:**
- ✅ Buttons have proper icons
- ✅ Dialogs are centered and responsive
- ✅ Forms have proper validation
- ✅ Loading states show correctly
- ✅ Empty states are informative
- ✅ Success/error notifications appear
- ✅ Template cards look professional
- ✅ Workflow list is readable

### **Interaction checks:**
- ✅ All buttons are clickable
- ✅ Dialogs can be closed (X button, outside click)
- ✅ Forms can be submitted (Enter key)
- ✅ Lists are scrollable
- ✅ No console errors
- ✅ No broken layouts

---

## 📈 **Performance Testing**

### **Test with multiple workflows:**

```bash
# Create 10 test workflows
for i in {1..10}; do
  curl -s -X POST http://localhost:8008/api/v1/workflows/save \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Test Workflow $i\",
      \"description\": \"Performance test workflow\",
      \"nodes\": [{\"id\": \"1\", \"type\": \"upload\", \"position\": {\"x\": 0, \"y\": 0}, \"data\": {\"label\": \"Test\"}}],
      \"edges\": [],
      \"tags\": [\"test\"],
      \"is_template\": false
    }" > /dev/null
done

# Verify all created
curl -s http://localhost:8008/api/v1/workflows/list | jq '.workflows | length'
# Expected: 10
```

**Then test:**
- ✅ Load dialog opens quickly
- ✅ List scrolls smoothly
- ✅ Search/filter works (if implemented)
- ✅ No lag when loading workflows

---

## ✅ **Success Criteria**

**All features working if:**
1. ✅ All 3 templates load correctly
2. ✅ Workflows can be saved with title/description
3. ✅ Saved workflows appear in Load dialog
4. ✅ Workflows can be loaded to canvas
5. ✅ Workflows can be deleted
6. ✅ No errors in browser console
7. ✅ No errors in backend logs
8. ✅ Neo4j stores workflow data correctly
9. ✅ UI is responsive and intuitive
10. ✅ All buttons/dialogs work as expected

---

## 🚀 **Next Steps After Testing**

If all tests pass:
1. ✅ Mark todos as complete
2. 📝 Document any edge cases found
3. 🎨 Consider UI polish (animations, transitions)
4. 📊 Add analytics (track template usage)
5. 🔍 Add search/filter for workflows
6. 📤 Add export/import (JSON files)
7. 🔄 Add workflow versioning
8. 👥 Add workflow sharing/permissions

---

**Ready to test? Open http://localhost:3000/workflow-builder and start with the Templates button!** 🎉
