# Classification Fix Implementation Plan

**Date**: October 30, 2025  
**Priority**: CRITICAL  
**Estimated Time**: 2-3 hours

---

## 🎯 Objectives

1. **Fix LLM Classifier** - Currently voting Non-ICSR with 0.3 confidence consistently
2. **Add Safety_Information Logic** - Currently 0% detection rate
3. **Improve Overall Classification Accuracy** - From 30% to 85%+

---

## 📋 Part 1: Fix LLM Classifier

### Current Issues:
1. **Prompt is too conservative** - "Be conservative when labeling ICSR" leads to over-classification as Non-ICSR
2. **Temperature too low** (0.3) - May be causing repetitive behavior
3. **Fallback always returns Non-ICSR** with 0.5 confidence
4. **No explicit examples** in the prompt for each class

### Changes to Implement:

#### 1.1 Update PHARMACOVIGILANCE_EXPERT_PROMPT in `main.py`

**Current Prompt Issues**:
- Line 164: "Be conservative when labeling ICSR" - **TOO CONSERVATIVE**
- Missing clear examples for each class
- Safety_Information description is vague
- No confidence calibration guidance

**New Prompt Will**:
- Remove "be conservative" instruction
- Add explicit examples for all 4 classes
- Clarify Safety_Information vs Non-ICSR distinction
- Add confidence scoring guidance
- Emphasize balanced classification

#### 1.2 Adjust Temperature
**Change**: `temperature=0.3` → `temperature=0.5`
**Reason**: Allow more variation in responses, reduce repetitive Non-ICSR voting

#### 1.3 Fix Fallback Classification
**Current** (line 324):
```python
classification_data = {
    "classification": "Non-ICSR",
    "confidence": 0.5,
    ...
}
```

**New**:
```python
classification_data = {
    "classification": "Non-ICSR",
    "confidence": 0.3,  # Lower confidence for fallback
    ...
}
```

#### 1.4 Add Confidence Calibration
- ICSR: 0.7-0.95 (high confidence for clear cases)
- Safety_Information: 0.6-0.85
- Non-ICSR: 0.5-0.9
- Rejected: 0.8-0.95 (high confidence needed)

---

## 📋 Part 2: Add Safety_Information Logic

### Current Issues:
1. **No Safety_Information detection in rule-based classifier**
2. **Safety_Information never predicted** (0% detection rate)
3. **All safety studies misclassified as Non-ICSR**

### Changes to Implement:

#### 2.1 Add Safety_Information MeSH Terms to `rule_based_classifier.py`

**Add New Constant**:
```python
SAFETY_INFO_MESH_TERMS = {
    'Pharmacovigilance',
    'Drug Safety',
    'Product Surveillance, Postmarketing',
    'Adverse Drug Reaction Reporting Systems',
    'Clinical Trials, Phase I',
    'Clinical Trials, Phase II',
    'Clinical Trials, Phase III',
    'Clinical Trials, Phase IV',
    'Meta-Analysis',
    'Systematic Review',
    'Risk Assessment',
    'Drug Monitoring',
    'Safety Management'
}
```

#### 2.2 Add Safety_Information Publication Types

**Add to Existing Constants**:
```python
SAFETY_INFO_PUBLICATION_TYPES = {
    'Clinical Trial',
    'Clinical Trial, Phase I',
    'Clinical Trial, Phase II',
    'Clinical Trial, Phase III',
    'Clinical Trial, Phase IV',
    'Meta-Analysis',
    'Systematic Review',
    'Observational Study',
    'Cohort Study',
    'Multicenter Study'
}
```

#### 2.3 Add Safety_Information Keywords

**Add New Constant**:
```python
SAFETY_INFO_KEYWORDS = [
    'safety profile',
    'safety analysis',
    'safety data',
    'tolerability',
    'adverse events',
    'safety and efficacy',
    'post-marketing',
    'surveillance',
    'pharmacovigilance',
    'risk assessment',
    'safety monitoring',
    'clinical trial safety'
]
```

#### 2.4 Update `_calculate_evidence()` Method

**Add**:
```python
evidence['safety_info_mesh_count'] = len(mesh_set & self.SAFETY_INFO_MESH_TERMS)
evidence['safety_info_keywords'] = sum(1 for kw in self.SAFETY_INFO_KEYWORDS if kw in text)
```

#### 2.5 Update `_make_decision()` Method

**Add Safety_Information Rules** (insert after line 195):

```python
# SAFETY_INFORMATION RULES
# Rule: Clinical trial or meta-analysis with safety focus
if (pub_types & self.SAFETY_INFO_PUBLICATION_TYPES) and (
    evidence['safety_info_keywords'] >= 2 or 
    evidence['safety_info_mesh_count'] >= 1
):
    return (
        "Safety_Information",
        0.85,
        "High confidence: Clinical trial/meta-analysis with safety focus"
    )

# Rule: Pharmacovigilance/surveillance study
if evidence['safety_info_mesh_count'] >= 2:
    return (
        "Safety_Information",
        0.80,
        "High confidence: Multiple pharmacovigilance/safety MeSH terms"
    )

# Rule: Safety keywords without individual case
if (evidence['safety_info_keywords'] >= 3 and 
    evidence['patient_mentions'] < 2):
    return (
        "Safety_Information",
        0.75,
        "Moderate confidence: Safety-focused content without individual case reports"
    )
```

**Important**: Place these rules BEFORE the general Non-ICSR rules to ensure Safety_Information is detected first.

---

## 📋 Part 3: Additional Improvements

### 3.1 Add Rejected Detection Logic

**Add to `rule_based_classifier.py`**:

```python
# REJECTED RULES (check first)
# Rule: Retracted publications
if 'RETRACTED' in title.upper() or 'retraction' in text:
    return (
        "Rejected",
        0.95,
        "High confidence: Retracted publication"
    )

# Rule: Duplicate publications
if 'DUPLICATE' in title.upper() or 'duplicate publication' in text:
    return (
        "Rejected",
        0.95,
        "High confidence: Duplicate publication"
    )

# Rule: Insufficient information
if len(title) < 10 or (abstract and len(abstract) < 50):
    return (
        "Rejected",
        0.80,
        "Moderate confidence: Insufficient information"
    )
```

### 3.2 Fix Publication Type Precedence

**Current Issue**: "Review" overrides "Case Reports" when both present

**Fix in `_make_decision()`** (line 169):

```python
# Rule 1: Case Report publication type + ICSR MeSH terms
# PRIORITIZE Case Reports even if Review is also present
if (pub_types & self.ICSR_PUBLICATION_TYPES):
    # Check if this is truly a case report (not just a review mentioning cases)
    if evidence['icsr_mesh_count'] >= 1 or (
        evidence['patient_mentions'] >= 2 and 
        evidence['adverse_event_mentions'] >= 1
    ):
        return (
            "ICSR",
            0.95,
            "High confidence: Case Report publication type with ICSR evidence"
        )
```

### 3.3 Improve Entity Detection

**Add more drug keywords**:
```python
'drug': [
    'administered', 'prescribed', 'treatment with', 'therapy with', 'received', 
    'medication', 'dose', 'dosage', 'mg', 'tablet', 'injection',
    # ADD THESE:
    'drug', 'medicine', 'pharmaceutical', 'compound', 'agent',
    'antibiotic', 'analgesic', 'antidepressant', 'chemotherapy'
]
```

**Add more adverse event keywords**:
```python
'adverse_event': [
    'adverse', 'reaction', 'side effect', 'toxicity', 'complication',
    'injury', 'death', 'hospitalization', 'discontinued', 'withdrawn',
    # ADD THESE:
    'rash', 'anaphylaxis', 'hypersensitivity', 'allergy', 'allergic',
    'hepatotoxicity', 'nephrotoxicity', 'cardiotoxicity', 'neurotoxicity',
    'syndrome', 'failure', 'damage', 'impairment'
]
```

---

## 📊 Implementation Order

### Phase 1: Critical Fixes (30 minutes)
1. ✅ Update LLM prompt (remove "be conservative", add examples)
2. ✅ Adjust LLM temperature (0.3 → 0.5)
3. ✅ Add Safety_Information MeSH terms and keywords
4. ✅ Add Safety_Information detection rules

### Phase 2: Enhancements (20 minutes)
5. ✅ Add Rejected detection logic
6. ✅ Fix publication type precedence
7. ✅ Improve entity detection keywords

### Phase 3: Testing (10 minutes)
8. ✅ Re-run comprehensive test suite
9. ✅ Verify improvements
10. ✅ Document results

---

## 📈 Expected Results

### Before Fixes:
| Metric | Current |
|--------|---------|
| Overall Pass Rate | 30% |
| ICSR Detection | 45% |
| Safety_Info Detection | 0% |
| Rejected Detection | 0% |
| Avg Confidence | 0.650 |

### After Fixes:
| Metric | Target |
|--------|--------|
| Overall Pass Rate | 85%+ |
| ICSR Detection | 90%+ |
| Safety_Info Detection | 80%+ |
| Rejected Detection | 90%+ |
| Avg Confidence | 0.850 |

---

## 🔧 Files to Modify

1. **`services/pv-classification-service/main.py`**
   - Update `PHARMACOVIGILANCE_EXPERT_PROMPT` (lines 124-200)
   - Adjust temperature (line 311)
   - Fix fallback confidence (line 325)

2. **`services/pv-classification-service/rule_based_classifier.py`**
   - Add `SAFETY_INFO_MESH_TERMS` (after line 44)
   - Add `SAFETY_INFO_PUBLICATION_TYPES` (after line 74)
   - Add `SAFETY_INFO_KEYWORDS` (after line 80)
   - Update `_calculate_evidence()` (add safety_info counts)
   - Update `_make_decision()` (add Safety_Information rules)
   - Add Rejected detection rules
   - Fix publication type precedence
   - Improve entity detection keywords

---

## ✅ Validation Plan

After implementing fixes:

1. **Run comprehensive test suite**:
   ```bash
   python test_classification_comprehensive.py
   ```

2. **Expected improvements**:
   - ICSR tests: 5/11 → 10/11 passed
   - Safety_Info tests: 0/4 → 3/4 passed
   - Rejected tests: 0/3 → 2/3 passed
   - Overall: 6/20 → 17/20 passed (85%)

3. **Test with real documents**:
   - Re-run ingestion of "Allergic rashes" documents
   - Verify improved classification distribution

---

## 🚀 Ready to Implement

All changes are documented and ready for implementation. The fixes are:
- **Well-defined** - Exact line numbers and code changes specified
- **Low-risk** - No breaking changes to API or data structures
- **High-impact** - Expected to improve accuracy from 30% to 85%+
- **Testable** - Comprehensive test suite ready to validate

**Estimated Implementation Time**: 1 hour  
**Estimated Testing Time**: 30 minutes  
**Total Time**: 1.5 hours

---

**Document Created**: October 30, 2025, 00:20  
**Status**: Ready for Implementation  
**Priority**: CRITICAL

