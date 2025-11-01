# 🧪 Knowledge Hub - Client Value-Add Feature Test Plan

**Date**: October 31, 2025  
**Purpose**: Comprehensive testing for client demonstration  
**Priority**: HIGH - Value-Add Feature

---

## 🎯 Test Objectives

1. **Verify all UX fixes work correctly**
2. **Ensure search finds entities accurately**
3. **Validate source filtering functions properly**
4. **Confirm legend shows accurate real-time counts**
5. **Test keyboard shortcuts work smoothly**
6. **Validate node selection/deselection**

---

## 🧪 Test Suite

### Test 1: Graph Loading & Display ✅

**Steps**:
1. Navigate to `http://localhost:3000/knowledge-hub`
2. Wait for graph to load (should take 2-3 seconds)
3. Open Browser Console (F12 or Cmd+Option+I)

**Expected Results**:
- ✅ Graph displays with colorful nodes (Green, Red, Purple, Orange, Cyan, Gray)
- ✅ Legend shows 6 stat cards with counts
- ✅ Console shows: `📊 Graph Loaded:` with node count
- ✅ No error messages

**Acceptance Criteria**:
- [ ] 400-500 nodes visible
- [ ] Multiple colors visible (not all gray)
- [ ] Legend shows accurate counts
- [ ] Console log shows `hasAspirin: true`

---

### Test 2: Entity Search (CRITICAL) 🔍

**Test 2a: Search for "aspirin"**

**Steps**:
1. Type "aspirin" in search box
2. Click "Search" button (or press Enter)
3. Check console for debug logs

**Expected Results**:
- ✅ Console shows: `🔍 Search Debug:` with query="aspirin"
- ✅ Console shows: `🔍 Search Results:` with matchingCount > 0
- ✅ Aspirin node(s) highlight in the graph
- ✅ Graph zooms to aspirin node
- ✅ No error message

**Acceptance Criteria**:
- [ ] At least 1 match found
- [ ] Node highlights visually (brighter/glowing)
- [ ] Graph centers on the match
- [ ] Error message does NOT appear

**If Test Fails**:
- Check console log for `filteredGraphNodes` count
- Check if `sourceFilter` is set to something other than "all"
- Check if `hasAspirin: false` in Graph Loaded log

---

**Test 2b: Search for "hepato"**

**Steps**:
1. Clear previous search
2. Type "hepato" in search box
3. Click "Search"

**Expected Results**:
- ✅ Multiple nodes highlight (hepatotoxicity, hepatitis, etc.)
- ✅ Graph zooms to first match
- ✅ Console shows multiple matches

**Acceptance Criteria**:
- [ ] 3+ matches found
- [ ] All matching nodes highlight
- [ ] Graph centers appropriately

---

**Test 2c: Search for non-existent entity**

**Steps**:
1. Type "zzzznonexistent" in search box
2. Click "Search"

**Expected Results**:
- ✅ Error message: "No entities found matching 'zzzznonexistent' in current graph"
- ✅ No nodes highlighted
- ✅ Console shows: `matchingCount: 0`

**Acceptance Criteria**:
- [ ] Appropriate error message shown
- [ ] No false positives

---

### Test 3: Source Filtering (HIGH PRIORITY) 🔽

**Test 3a: Filter by "PDF Only"**

**Steps**:
1. Note current legend counts (e.g., 500 Total Entities)
2. Select "📄 PDF Only" from "Filter by Source" dropdown
3. Wait 1 second for graph to update
4. Check console for debug logs

**Expected Results**:
- ✅ Graph filters to show fewer nodes
- ✅ Legend counts UPDATE (e.g., 300 Total Entities)
- ✅ Only nodes with `has_pdf: true` remain
- ✅ Console shows: `filteredGraphNodes` < `totalGraphNodes`

**Acceptance Criteria**:
- [ ] Node count decreases
- [ ] Legend updates to match filtered count
- [ ] Graph re-renders smoothly
- [ ] No errors in console

---

**Test 3b: Filter by "External Only"**

**Steps**:
1. Select "🌐 External Only" from dropdown
2. Check legend counts

**Expected Results**:
- ✅ Different set of nodes visible
- ✅ Legend shows different counts than PDF filter
- ✅ Only nodes with `has_external: true` remain

**Acceptance Criteria**:
- [ ] Node count changes from PDF filter
- [ ] Legend updates correctly

---

**Test 3c: Filter by "Cross-Source"**

**Steps**:
1. Select "🔗 Cross-Source" from dropdown
2. Check legend counts

**Expected Results**:
- ✅ Smallest node count (most restrictive filter)
- ✅ Only nodes with BOTH `has_pdf: true` AND `has_external: true`
- ✅ Legend shows lowest counts

**Acceptance Criteria**:
- [ ] Fewer nodes than PDF or External alone
- [ ] Legend updates correctly

---

**Test 3d: Reset to "All Sources"**

**Steps**:
1. Select "All Sources" from dropdown
2. Check legend counts

**Expected Results**:
- ✅ All 500 nodes visible again
- ✅ Legend shows original counts
- ✅ Graph returns to full view

**Acceptance Criteria**:
- [ ] Full node count restored
- [ ] Legend matches initial load

---

### Test 4: Search + Filter Combination 🔍+🔽

**Steps**:
1. Select "PDF Only" filter
2. Type "aspirin" in search
3. Click "Search"

**Expected Results**:
- ✅ Search only looks in PDF-filtered nodes
- ✅ If aspirin is in PDF nodes → highlights it
- ✅ If aspirin is NOT in PDF nodes → shows error
- ✅ Console shows: `filteredGraphNodes` < total

**Acceptance Criteria**:
- [ ] Search respects active filter
- [ ] Results are accurate for filtered set

---

### Test 5: Node Selection/Deselection ✅

**Test 5a: Click to select**

**Steps**:
1. Click any colored node (Drug, Disease, etc.)

**Expected Results**:
- ✅ Node and its connections highlight
- ✅ Entity details drawer opens on right
- ✅ Node appears brighter/selected

**Acceptance Criteria**:
- [ ] Visual feedback immediate
- [ ] Drawer shows entity details

---

**Test 5b: Click same node to deselect**

**Steps**:
1. Click the same selected node again

**Expected Results**:
- ✅ Node deselects
- ✅ Highlights clear
- ✅ Drawer closes
- ✅ NO page refresh needed

**Acceptance Criteria**:
- [ ] Deselection works smoothly
- [ ] No page reload

---

**Test 5c: Click background to deselect**

**Steps**:
1. Select a node
2. Click on empty graph background

**Expected Results**:
- ✅ Node deselects
- ✅ Highlights clear
- ✅ Drawer closes

**Acceptance Criteria**:
- [ ] Background click deselects
- [ ] Smooth interaction

---

**Test 5d: Press ESC to deselect**

**Steps**:
1. Select a node
2. Press ESC key

**Expected Results**:
- ✅ Node deselects
- ✅ Highlights clear
- ✅ Drawer closes
- ✅ Search clears (if any)

**Acceptance Criteria**:
- [ ] ESC key works
- [ ] All state clears

---

### Test 6: Keyboard Shortcuts ⌨️

**Test 6a: Ctrl+K to focus search**

**Steps**:
1. Click anywhere on the page
2. Press `Ctrl+K` (Windows) or `Cmd+K` (Mac)

**Expected Results**:
- ✅ Search box receives focus
- ✅ Cursor appears in search box
- ✅ Ready to type

**Acceptance Criteria**:
- [ ] Keyboard shortcut works
- [ ] Search box focuses

---

**Test 6b: ESC to clear everything**

**Steps**:
1. Search for something
2. Select a node
3. Press ESC

**Expected Results**:
- ✅ Search clears
- ✅ Node deselects
- ✅ Error messages clear
- ✅ Highlights clear

**Acceptance Criteria**:
- [ ] ESC clears all state
- [ ] Clean slate

---

### Test 7: Dynamic Legend Accuracy 📊

**Test 7a: Legend matches graph**

**Steps**:
1. Count visible nodes by color manually (rough estimate)
2. Compare to legend counts

**Expected Results**:
- ✅ Legend "Total Entities" matches visible node count
- ✅ Legend "Drugs" count matches green nodes (roughly)
- ✅ Legend "Diseases" count matches red nodes (roughly)

**Acceptance Criteria**:
- [ ] Legend is reasonably accurate
- [ ] No wildly wrong counts

---

**Test 7b: Legend updates with filter**

**Steps**:
1. Note legend counts with "All Sources"
2. Select "PDF Only"
3. Note new legend counts
4. Select "All Sources" again

**Expected Results**:
- ✅ Legend counts DECREASE with PDF filter
- ✅ Legend counts RESTORE with All Sources
- ✅ Updates happen immediately

**Acceptance Criteria**:
- [ ] Legend is dynamic, not static
- [ ] Updates in real-time

---

## 🐛 Known Issues & Debugging

### Issue 1: Search Returns "No entities found" (But entity exists)

**Possible Causes**:
1. **Source filter is active** - Entity might be filtered out
   - Solution: Set filter to "All Sources"
   
2. **Graph hasn't loaded yet** - Searching before data loads
   - Solution: Wait for graph to fully render
   
3. **Case sensitivity issue** - Search is case-sensitive
   - Solution: Try lowercase (already implemented)
   
4. **Entity name mismatch** - Searching for "Aspirin" but stored as "aspirin"
   - Solution: Check console log for actual node names

**Debug Steps**:
1. Open console (F12)
2. Look for `📊 Graph Loaded:` log
3. Check `hasAspirin: true/false`
4. Check `nodeCount` (should be 400-500)
5. Look for `🔍 Search Debug:` log
6. Check `filteredGraphNodes` count
7. Check `sourceFilter` value

---

### Issue 2: Source Filter Doesn't Change Graph

**Possible Causes**:
1. **All nodes have same source** - Filter has no effect
   - Check: `has_pdf` and `has_external` properties
   
2. **Filter state not updating** - React state issue
   - Check console for `sourceFilter` value
   
3. **Memoization issue** - `filteredGraphData` not recalculating
   - Check if `useMemo` dependencies are correct

**Debug Steps**:
1. Open console
2. Select different filters
3. Check if `🔍 Search Debug:` shows different `filteredGraphNodes` counts
4. Check if legend counts change

---

### Issue 3: Legend Shows Wrong Counts

**Possible Causes**:
1. **Using API statistics instead of graph data** - Old bug
   - Should be fixed (using `filteredGraphData.nodes`)
   
2. **Graph data not loaded** - Calculating from empty array
   - Check `graphData.nodes.length` in console

**Debug Steps**:
1. Check console for `📊 Graph Loaded:` log
2. Verify `nodeCount` matches legend "Total Entities"
3. Check `nodeTypes` breakdown matches legend

---

## ✅ Success Criteria Summary

### Must Pass (Critical):
- [ ] **Search finds "aspirin"** (entity known to exist)
- [ ] **Source filter changes node count**
- [ ] **Legend shows accurate counts**
- [ ] **Node deselection works (no refresh needed)**
- [ ] **No console errors**

### Should Pass (High Priority):
- [ ] **Search highlights multiple matches**
- [ ] **Search + Filter combination works**
- [ ] **Keyboard shortcuts work (ESC, Ctrl+K)**
- [ ] **Graph renders smoothly**

### Nice to Have (Medium Priority):
- [ ] **Graph zooms to search results**
- [ ] **Visual feedback is immediate**
- [ ] **All 6 legend cards show data**

---

## 📊 Test Results Template

```
KNOWLEDGE HUB TEST RESULTS
==========================
Date: ___________
Tester: ___________

Test 1: Graph Loading          [ PASS / FAIL ]
Test 2a: Search "aspirin"      [ PASS / FAIL ]
Test 2b: Search "hepato"       [ PASS / FAIL ]
Test 2c: Search non-existent   [ PASS / FAIL ]
Test 3a: Filter PDF Only       [ PASS / FAIL ]
Test 3b: Filter External       [ PASS / FAIL ]
Test 3c: Filter Cross-Source   [ PASS / FAIL ]
Test 3d: Reset All Sources     [ PASS / FAIL ]
Test 4: Search + Filter        [ PASS / FAIL ]
Test 5a: Select node           [ PASS / FAIL ]
Test 5b: Deselect same node    [ PASS / FAIL ]
Test 5c: Deselect background   [ PASS / FAIL ]
Test 5d: Deselect with ESC     [ PASS / FAIL ]
Test 6a: Ctrl+K shortcut       [ PASS / FAIL ]
Test 6b: ESC clears all        [ PASS / FAIL ]
Test 7a: Legend accuracy       [ PASS / FAIL ]
Test 7b: Legend updates        [ PASS / FAIL ]

OVERALL: [ PASS / FAIL ]

Issues Found:
1. ___________
2. ___________
3. ___________

Console Logs:
___________
```

---

## 🎯 Client Value Proposition

**Why This Feature Matters**:

1. **Interactive Exploration** - Clients can explore their knowledge graph visually
2. **Fast Search** - Find entities instantly without SQL queries
3. **Source Filtering** - See which entities come from PDFs vs external sources
4. **Real-time Updates** - Legend and counts update dynamically
5. **Professional UX** - Smooth interactions, no page refreshes
6. **Power User Features** - Keyboard shortcuts for efficiency

**Demo Script**:
> "Let me show you our Knowledge Hub. Here you can see all 500 entities from your documents, color-coded by type. Watch as I search for 'aspirin'... see how it highlights and zooms? Now let me filter to show only entities from your PDF documents... notice the counts update in real-time? This is a powerful tool for exploring connections in your pharmacovigilance data."

---

**Status**: Ready for Client Testing  
**Next Step**: Execute test plan and report results

---

*This is a value-add feature that demonstrates our platform's intelligence and usability.*

