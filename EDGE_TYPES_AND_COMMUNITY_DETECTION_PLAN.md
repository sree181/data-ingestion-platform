# 🔗 Knowledge Graph - Edge Types & Enhanced Community Detection
**Implementation Date:** November 1, 2025  
**Status:** 🚧 In Progress

---

## 🎯 Objectives

1. **Edge Type Granularity** - Add semantic meaning to relationships
2. **Enhanced Community Detection** - Improve clustering based on edge types
3. **Visual Relationship Indicators** - Show relationship types visually

---

## 📊 Edge Type Taxonomy

### **Medical/Pharmacovigilance Relationships:**

```
Drug → Disease:
  - TREATS
  - CAUSES
  - PREVENTS
  - ASSOCIATED_WITH

Drug → Drug:
  - INTERACTS_WITH
  - COMBINED_WITH
  - CONTRAINDICATES

Disease → Disease:
  - COMORBID_WITH
  - PROGRESSES_TO
  - RELATED_TO

Entity → Person:
  - STUDIED_BY
  - REPORTED_BY
  - AUTHORED_BY

Entity → Organization:
  - MANUFACTURED_BY
  - APPROVED_BY
  - INVESTIGATED_BY

Entity → Procedure:
  - DIAGNOSED_BY
  - TREATED_WITH
  - MONITORED_BY

Generic:
  - MENTIONED_IN
  - CO_OCCURS_WITH
  - RELATED_TO
```

---

## 🎨 Visual Design for Edge Types

### **1. Line Styles:**

```
TREATS, PREVENTS         → Solid, thick line (3px)
CAUSES, INTERACTS_WITH   → Dashed line [5, 5]
STUDIED_BY, AUTHORED_BY  → Dotted line [2, 4]
RELATED_TO, ASSOCIATED   → Thin dashed [3, 2]
```

### **2. Colors by Relationship Strength:**

```
Strong relationships:     Bright, saturated colors
Medium relationships:     Medium opacity (60%)
Weak relationships:       Low opacity (30%)
```

### **3. Arrows & Particles:**

```
Causal (CAUSES):          Red particles flowing
Treatment (TREATS):       Green particles flowing
Research (STUDIED_BY):    Blue particles flowing
Generic:                  Gray particles
```

---

## 🔍 Enhanced Community Detection Algorithm

### **Phase 1: Relationship-Weighted Clustering**

```javascript
// Weight edges by type
const edgeWeights = {
  TREATS: 1.0,
  CAUSES: 0.9,
  INTERACTS_WITH: 0.8,
  STUDIED_BY: 0.7,
  RELATED_TO: 0.5,
  CO_OCCURS_WITH: 0.3
};

// Calculate weighted modularity
function calculateModularity(communities, edges) {
  let modularity = 0;
  edges.forEach(edge => {
    const weight = edgeWeights[edge.type] || 0.5;
    if (communities[edge.source] === communities[edge.target]) {
      modularity += weight;
    }
  });
  return modularity;
}
```

### **Phase 2: Hierarchical Clustering**

```
Level 1: Entity Type (Drug, Disease, Person, etc.)
Level 2: Relationship Type (Treatment cluster, Research cluster, etc.)
Level 3: Connectivity (Strongly connected sub-clusters)
```

### **Phase 3: Semantic Clustering**

```javascript
// Group by semantic similarity
const clusters = {
  treatment_cluster: {
    entities: [/* drugs, procedures */],
    relationships: ['TREATS', 'PREVENTS']
  },
  research_cluster: {
    entities: [/* papers, people */],
    relationships: ['STUDIED_BY', 'AUTHORED_BY']
  },
  adverse_events_cluster: {
    entities: [/* drugs, diseases */],
    relationships: ['CAUSES', 'ASSOCIATED_WITH']
  }
};
```

---

## 🛠️ Implementation Plan

### **Step 1: Backend Enhancement (Neo4j Query)**

Update the Neo4j query to return relationship types:

```cypher
MATCH (n)-[r]-(m)
WHERE NOT n:User AND NOT m:User
RETURN 
  n,
  m,
  type(r) as relationship_type,
  r.confidence as relationship_confidence,
  properties(r) as relationship_props
```

### **Step 2: Frontend Data Structure**

Update link objects to include relationship metadata:

```javascript
const formattedEdges = edges.map(edge => ({
  source: edge.source,
  target: edge.target,
  type: edge.relationship_type,      // NEW: TREATS, CAUSES, etc.
  label: edge.predicate || edge.type,
  confidence: edge.confidence,
  strength: calculateStrength(edge), // NEW: Based on type & confidence
  category: categorizeRelationship(edge.type) // NEW: treatment, research, adverse
}));
```

### **Step 3: Enhanced Link Rendering**

```javascript
linkCanvasObject={(link, ctx, globalScale) => {
  // 1. Determine line style based on relationship type
  const lineStyle = getLineStyle(link.type);
  
  // 2. Set color based on relationship category
  const color = getRelationshipColor(link.category);
  
  // 3. Set width based on strength
  const width = 1 + (link.strength * 3);
  
  // 4. Render with appropriate style
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash(lineStyle);
  
  // 5. Draw the line
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
  
  // 6. Add label if zoomed in
  if (globalScale > 1.5) {
    drawLinkLabel(ctx, link, start, end);
  }
}};
```

### **Step 4: Relationship Type Filter**

Add UI control to filter by relationship type:

```javascript
<FormControl>
  <InputLabel>Relationship Type</InputLabel>
  <Select
    multiple
    value={selectedRelationships}
    onChange={(e) => setSelectedRelationships(e.target.value)}
  >
    <MenuItem value="TREATS">Treats</MenuItem>
    <MenuItem value="CAUSES">Causes</MenuItem>
    <MenuItem value="STUDIED_BY">Studied By</MenuItem>
    <MenuItem value="INTERACTS_WITH">Interacts With</MenuItem>
    <MenuItem value="RELATED_TO">Related To</MenuItem>
  </Select>
</FormControl>
```

### **Step 5: Enhanced Community Detection**

```javascript
const detectSemanticCommunities = useCallback(() => {
  // 1. Build weighted adjacency matrix
  const adjacency = buildWeightedAdjacency(graphData.nodes, graphData.links);
  
  // 2. Run Louvain with edge weights
  const communities = louvainWithWeights(adjacency);
  
  // 3. Refine by relationship types
  const refinedCommunities = refineByRelationships(communities, graphData.links);
  
  // 4. Assign colors
  const colors = generateCommunityColors(refinedCommunities);
  
  return { communities: refinedCommunities, colors };
}, [graphData]);
```

### **Step 6: Relationship Legend**

Add a legend showing relationship types:

```javascript
<Card sx={{ position: 'absolute', top: 16, right: 16, p: 2 }}>
  <Typography variant="subtitle2" gutterBottom>
    Relationship Types
  </Typography>
  {relationshipTypes.map(type => (
    <Box key={type.name} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
      <div style={{
        width: 30,
        height: 2,
        background: type.color,
        borderStyle: type.style
      }} />
      <Typography variant="caption">{type.label}</Typography>
    </Box>
  ))}
</Card>
```

---

## 📈 Expected Improvements

### **Before:**
```
- All links look the same
- Can't distinguish relationship types
- Basic community detection by entity type only
- No semantic clustering
```

### **After:**
```
✅ Visual distinction by relationship type
✅ Color-coded by relationship category
✅ Line style indicates semantic meaning
✅ Enhanced community detection with edge weights
✅ Semantic clusters (treatment, research, adverse events)
✅ Relationship type filtering
✅ Interactive legend
```

---

## 🎯 Success Metrics

1. **Visual Clarity**: Users can identify relationship types at a glance
2. **Clustering Quality**: Communities are more semantically coherent
3. **Discoverability**: Easy to find specific relationship patterns
4. **Performance**: No impact on rendering speed
5. **Usability**: Intuitive controls for filtering relationships

---

## 🚀 Implementation Status

- [ ] Backend: Update Neo4j query to return relationship types
- [ ] Frontend: Add relationship metadata to link objects
- [ ] Visual: Implement line styles for different relationship types
- [ ] Visual: Add color coding by relationship category
- [ ] Algorithm: Implement weighted Louvain community detection
- [ ] Algorithm: Add semantic clustering refinement
- [ ] UI: Add relationship type filter
- [ ] UI: Add relationship legend
- [ ] Testing: Verify all relationship types render correctly
- [ ] Documentation: Update user guide

---

**Next Steps:** Begin implementation with backend Neo4j query enhancement.

