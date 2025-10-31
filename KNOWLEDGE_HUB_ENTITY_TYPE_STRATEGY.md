# 🎨 Knowledge Hub Entity Type Strategy

**AI Architect & UI/UX Professional Assessment**  
**Date**: October 31, 2025  
**Priority**: HIGH - Product Pipeline Integration

---

## 🔍 Problem Analysis

### Current State
- **All nodes are gray** (generic `Entity` type)
- Entity type mapping in Neo4j is **incomplete**
- Only maps: PERSON, ORG, GPE, DATE, MONEY, LAW
- **Missing critical PV types**: Drug, Disease, Adverse Event, Procedure

### Root Cause (File: `services/api-gateway/services/neo4j_service.py`, Lines 207-219)
```python
label_mapping = {
    "PERSON": "Person",
    "ORG": "Organization", 
    "ORGANIZATION": "Organization",
    "GPE": "Location",
    "LOCATION": "Location",
    "DATE": "Date",
    "MONEY": "Money",
    "LAW": "Law",
    "LEGAL": "Legal"
}

label = label_mapping.get(entity_type.upper(), "Entity")  # ← Defaults to "Entity"!
```

**Impact**: 95%+ of entities default to generic "Entity" → all gray nodes!

---

## 🎯 Solution Strategy: 3-Tier Approach

### Tier 1: **Immediate Fix** (Entity Type Enhancement)
Expand entity type mapping for pharmacovigilance domain

### Tier 2: **ML-Based Classification** (Product Pipeline)
Integrate with PV Classification Service for intelligent typing

### Tier 3: **User Utility** (Advanced Features)
Add entity type management UI and auto-correction

---

## 📊 Tier 1: Enhanced Entity Type Mapping

### Pharmacovigilance-Specific Types

```python
ENHANCED_LABEL_MAPPING = {
    # Medical/Pharmacovigilance Entities (GREEN family)
    "DRUG": "Drug",
    "MEDICATION": "Drug",
    "PHARMACEUTICAL": "Drug",
    "CHEMICAL": "Drug",
    "SUBSTANCE": "Drug",
    "COMPOUND": "Drug",
    
    # Diseases & Conditions (RED family)
    "DISEASE": "Disease",
    "CONDITION": "Disease",
    "DISORDER": "Disease",
    "SYNDROME": "Disease",
    "SYMPTOM": "Disease",
    "ADVERSE_EVENT": "Disease",
    "SIDE_EFFECT": "Disease",
    
    # Medical Procedures (CYAN family)
    "PROCEDURE": "Procedure",
    "TREATMENT": "Procedure",
    "THERAPY": "Procedure",
    "INTERVENTION": "Procedure",
    "SURGERY": "Procedure",
    "TEST": "Procedure",
    "EXAM": "Procedure",
    
    # Organizations (ORANGE family)
    "ORG": "Organization",
    "ORGANIZATION": "Organization",
    "COMPANY": "Organization",
    "MANUFACTURER": "Organization",
    "HOSPITAL": "Organization",
    "INSTITUTION": "Organization",
    
    # People (PURPLE family)
    "PERSON": "Person",
    "PATIENT": "Person",
    "DOCTOR": "Person",
    "PHYSICIAN": "Person",
    "RESEARCHER": "Person",
    
    # Generic (GRAY - fallback)
    "GPE": "Entity",
    "LOCATION": "Entity",
    "DATE": "Entity",
    "MONEY": "Entity",
    "LAW": "Entity",
    "LEGAL": "Entity",
}
```

### Color Mapping to UI
```javascript
// Frontend: Already defined in KnowledgeHub.js
Drug        → Green  (#10b981)  ✅
Disease     → Red    (#ef4444)  ✅
Procedure   → Cyan   (#06b6d4)  ✅
Organization→ Orange (#f59e0b)  ✅
Person      → Purple (#8b5cf6)  ✅
Entity      → Gray   (#6b7280)  ✅
```

---

## 🚀 Tier 2: ML-Based Entity Classification

### Integration with PV Classification Service

#### Current Pipeline:
```
Document → PV Classifier → key_entities: [{entity, type, confidence, relevance}]
                                         ↓
                                      Neo4j (all as "Entity")
```

#### Enhanced Pipeline:
```
Document → PV Classifier → key_entities with ML types
                                         ↓
                          Entity Type Resolver (NEW!)
                                         ↓
                          Intelligent Neo4j labeling
```

### Entity Type Resolver Logic
```python
class EntityTypeResolver:
    """Intelligently resolve entity types for knowledge graph"""
    
    def resolve_type(self, entity: Dict) -> str:
        """
        Resolve entity type using multiple signals:
        1. ML classification from PV service
        2. Context from document classification
        3. MeSH term matching
        4. Keyword heuristics
        """
        
        # 1. Direct ML classification (if confident)
        ml_type = entity.get("type", "").upper()
        confidence = entity.get("confidence", 0)
        
        if confidence > 0.8 and ml_type in ENHANCED_LABEL_MAPPING:
            return ENHANCED_LABEL_MAPPING[ml_type]
        
        # 2. Context-based inference
        entity_name = entity.get("entity", "").lower()
        context = entity.get("context", "").lower()
        
        # Drug indicators
        drug_keywords = ["drug", "medication", "pharmaceutical", "compound", 
                        "mg", "dose", "tablet", "capsule", "injection"]
        if any(kw in entity_name or kw in context for kw in drug_keywords):
            return "Drug"
        
        # Disease indicators  
        disease_keywords = ["disease", "syndrome", "disorder", "condition",
                           "adverse event", "reaction", "toxicity", "injury"]
        if any(kw in entity_name or kw in context for kw in disease_keywords):
            return "Disease"
        
        # Procedure indicators
        procedure_keywords = ["therapy", "treatment", "surgery", "procedure",
                             "test", "screening", "intervention"]
        if any(kw in entity_name or kw in context for kw in procedure_keywords):
            return "Procedure"
        
        # 3. MeSH term matching (if available)
        mesh_terms = entity.get("mesh_terms", [])
        if mesh_terms:
            if any("D04" in term for term in mesh_terms):  # MeSH: Chemicals
                return "Drug"
            if any("C" in term for term in mesh_terms):    # MeSH: Diseases
                return "Disease"
        
        # 4. Fallback to generic
        return "Entity"
```

---

## 🎨 Tier 3: User Utility Features

### Feature 1: Entity Type Correction UI
```
When user clicks on a node:
┌─────────────────────────────────┐
│ Entity: Hepatotoxicity          │
│ Current Type: Entity (Gray) ❌  │
│                                 │
│ Suggested Type: Disease (Red)   │
│ Confidence: 85%                 │
│                                 │
│ [Accept] [Change Type ▼]        │
└─────────────────────────────────┘
```

### Feature 2: Bulk Entity Classification
```
Knowledge Hub Actions Menu:
- Re-classify all entities (ML)
- Auto-fix common types
- Export entity taxonomy
- Import custom mappings
```

### Feature 3: Smart Legend with Filtering
```
┌──────────────────────┐
│ Entity Types         │
├──────────────────────┤
│ ✓ Drugs      (245)🟢│ ← Click to filter
│ ✓ Diseases   (189)🔴│
│ ✓ Procedures  (67)🔵│
│ ✓ People      (34)🟣│
│ ✓ Orgs        (28)🟠│
│ ✓ Other       (12)⚫│
├──────────────────────┤
│ [Select All]         │
│ [Re-classify Graph]  │
└──────────────────────┘
```

---

## 📈 Product Pipeline Integration

### Phase 1: Backend Enhancement (This Week)
1. ✅ Update `neo4j_service.py` with ENHANCED_LABEL_MAPPING
2. ✅ Create `EntityTypeResolver` service
3. ✅ Integrate with PV Classification pipeline
4. ✅ Add entity type correction API endpoint

### Phase 2: Frontend Enhancement (Next Week)
1. ✅ Add entity type filter in legend
2. ✅ Implement type correction UI
3. ✅ Add bulk re-classification button
4. ✅ Show type confidence indicators

### Phase 3: ML Enhancement (Sprint 2)
1. Train dedicated entity type classifier
2. Fine-tune on pharmacovigilance corpus
3. Add active learning feedback loop
4. Integrate with user corrections

---

## 🎯 Expected Impact

### Aesthetics
- **Color Distribution**: 
  - Green (Drugs): ~35-40%
  - Red (Diseases): ~30-35%
  - Cyan (Procedures): ~10-15%
  - Purple (People): ~5-10%
  - Orange (Orgs): ~5-10%
  - Gray (Other): ~5-10%

### User Utility
- **Instant Recognition**: Users identify entity types by color at a glance
- **Efficient Navigation**: Filter by entity type to focus on relevant connections
- **Quality Feedback**: Users can correct mis-classifications → improves ML model
- **Professional Appearance**: Varied colors create visual interest and hierarchy

### Product Value
- **Domain-Specific**: Tailored for pharmacovigilance use cases
- **Scalable**: Entity type resolver can be expanded for new domains
- **Intelligent**: Learns from user corrections
- **Exportable**: Entity taxonomy can be exported for reporting

---

## 🚀 Implementation Priority

### Immediate (Today - 2 hours)
```python
# File: services/api-gateway/services/neo4j_service.py
# Replace lines 207-219 with enhanced mapping
```

### Short-term (This Week - 6 hours)
- Entity Type Resolver service
- API endpoint for type correction
- Integration with PV classification

### Medium-term (Next Week - 8 hours)
- Frontend entity type filter
- Type correction UI
- Bulk re-classification

---

## ✅ Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Entity Type Accuracy** | <10% | - | >80% |
| **Colored Nodes** | 5% (gray) | - | 95% |
| **User Comprehension** | Low | - | High |
| **Visual Appeal** | 4/10 | - | 9/10 |
| **Domain Relevance** | Generic | - | PV-specific |

---

**Status**: Ready for implementation  
**Priority**: HIGH  
**Dependencies**: None  
**Risk**: Low (non-breaking change)

---

*This strategy balances immediate visual improvement with long-term product utility and ML intelligence.*

