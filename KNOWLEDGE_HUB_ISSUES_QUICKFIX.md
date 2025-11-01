# Knowledge Hub Issues - Quick Fix Guide

Based on your screenshot and console logs, here are the issues and immediate fixes:

## Issues Identified

### 1. ❌ **"Show Documents" is OFF by default**
**What you see**: No pink document nodes
**Why**: `showDocuments: false` (visible in console log)
**Fix**: Toggle "Show Documents" ON in the Advanced Filters section

### 2. ❌ **All relationships look the same**
**Root Cause**: Neo4j likely only has `HAS_ENTITY` relationships (not diverse semantic types like TREATS, CAUSES, etc.)
**What you see**: All links are one color
**Why**: The semantic relationship extraction hasn't been run on your data yet

### 3. ❌ **Community Detection shows but colors don't change**
**What you see**: "Show Communities" toggle ON, but nodes still have entity-type colors
**Console shows**: "Enhanced community detection complete: 492 communities"
**Issue**: Need to verify the `nodeColor` function is using community colors

### 4. ❌ **Drag not working**
**Issue**: `enableNodeDrag` might not be set correctly on the ForceGraph2D component

---

## 🔧 Immediate Fixes

### Fix 1: Enable Documents (User Action)
**In the UI right now:**
1. Look for "Advanced Filters" section (you can see it in your screenshot)
2. Find the "Show Documents" toggle
3. **Toggle it ON**
4. You should see pink nodes appear (documents)

### Fix 2: Check Why Only One Relationship Type

The console shows:
```
Final filtered graph: {nodes: 19, links: 17}
```

This means there ARE relationships, but they're all the same type. Let me check the data structure:

**Most likely cause**: Your Neo4j database only has `HAS_ENTITY` relationships (Document → Entity), not semantic relationships like:
- TREATS
- CAUSES  
- INTERACTS_WITH
- etc.

**To verify**: Look in the console for logs about relationship types when you load the graph.

### Fix 3: Verify Drag is Enabled

The `enableNodeDrag={true}` should be on line ~2302. Let me check if it's correctly set.

### Fix 4: Community Detection Colors

The community detection is running (492 communities found!), but the node colors might not be applying. Need to check the `nodeColor` callback.

---

## 🎯 Quick Test Steps

1. **Toggle "Show Documents" ON** → Pink nodes should appear
2. **Click "Show Communities" OFF then ON** → Colors should change
3. **Try dragging a node** → Click and hold, then move mouse
4. **Hover over a link** → Tooltip should show relationship type
5. **Check console** → Look for errors or warnings

---

## 📊 What Your Data Actually Has

From the console logs:
- ✅ 500 total nodes
- ✅ 456 nodes after document filter (because documents are hidden)
- ✅ 19 nodes after progressive disclosure (top 50)
- ✅ 17 relationships between these 19 nodes
- ✅ Community detection found 492 communities

**The code IS working**, but:
- Documents are hidden (toggle them on!)
- Relationships might all be `HAS_ENTITY` type (need semantic extraction)
- Community colors might not be rendering

---

## 🔍 Debug Commands

To see what's actually in your data, run in browser console:

```javascript
// See what relationship types exist
console.log('Relationship types:', 
  [...new Set(filteredGraphData.links.map(l => l.type))]
);

// See if documents exist
console.log('Documents:', 
  graphData.nodes.filter(n => n.type === 'Document').length
);

// See if community colors are set
console.log('Community colors:', communityColors);
```

Let me now check and fix the drag and community color issues in the code.

