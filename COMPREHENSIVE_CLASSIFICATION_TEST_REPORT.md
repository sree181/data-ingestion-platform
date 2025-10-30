# Comprehensive PV Classification Test Report

**Date**: October 30, 2025, 00:09  
**Test Suite**: Comprehensive Classification Validation  
**Total Tests**: 20  
**Pass Rate**: 30% (6/20 passed)

---

## 🎯 Executive Summary

### Test Results:
| Metric | Value | Status |
|--------|-------|--------|
| **Total Tests** | 20 | - |
| **Passed** | 6 | 30% |
| **Failed** | 14 | 70% |
| **Avg Confidence** | 0.650 | Moderate |
| **Avg Processing Time** | 1.518s | Good |

### Classification Distribution:
| Class | Count | Expected | Accuracy |
|-------|-------|----------|----------|
| **ICSR** | 5 | 11 | 45% |
| **Non-ICSR** | 15 | 4 | 375% (over-classified) |
| **Safety_Information** | 0 | 4 | 0% |
| **Rejected** | 0 | 3 | 0% |

---

## ⚠️ Critical Issues Identified

### **Issue #1: Safety_Information Class Not Being Used** 🔴

**Problem**: 0 out of 4 Safety_Information documents were correctly classified.

**Failed Tests**:
1. ✗ Clinical Trial Safety Analysis → Classified as Non-ICSR (expected: Safety_Information)
2. ✗ Post-Marketing Surveillance → Classified as Non-ICSR (expected: Safety_Information)
3. ✗ Meta-Analysis → Classified as Non-ICSR (expected: Safety_Information)
4. ✗ Pregnancy Safety Study → Classified as Non-ICSR (expected: Safety_Information)

**Root Cause**: The classifier is not distinguishing between Safety_Information and Non-ICSR. All safety studies are being lumped into Non-ICSR.

**Impact**: **HIGH** - Safety information is a distinct category that should be tracked separately.

---

### **Issue #2: Rejected Class Not Being Used** 🔴

**Problem**: 0 out of 3 Rejected documents were correctly classified.

**Failed Tests**:
1. ✗ Retracted Article → Classified as Non-ICSR (expected: Rejected)
2. ✗ Duplicate Publication → Classified as Non-ICSR (expected: Rejected)
3. ✗ Insufficient Information → Classified as Non-ICSR (expected: Rejected)

**Root Cause**: The classifier does not have logic to detect:
- Retracted publications
- Duplicate publications
- Insufficient/low-quality content

**Impact**: **MEDIUM** - Rejected documents should be filtered out to maintain data quality.

---

### **Issue #3: ICSR Detection Rate Lower Than Expected** 🟡

**Problem**: Only 5 out of 11 ICSR documents were correctly classified (45% accuracy).

**Failed ICSR Tests**:
1. ✗ Drug-Induced Hepatotoxicity → Classified as Non-ICSR
2. ✗ Case Series (15 patients) → Classified as Non-ICSR
3. ✗ Conflicting Signals (Review + Case Report) → Classified as Non-ICSR
4. ✗ Fatal Anaphylaxis (Perfect ICSR) → Classified as Non-ICSR

**Passed ICSR Tests**:
1. ✓ Severe Allergic Rash with Anaphylaxis
2. ✓ Stevens-Johnson Syndrome
3. ✓ Complex Multi-Drug Reaction
4. ✓ Pediatric Allergic Reaction
5. ✓ No Metadata (Text Only) - **Impressive!**

**Root Cause Analysis**:
- **Rule-based classifier** works well when MeSH terms + publication types are present
- **Ensemble voting** sometimes overrides correct ICSR classification
- **LLM classifier** consistently votes Non-ICSR (0.3 confidence) - **This is the problem!**

**Impact**: **HIGH** - Missing 55% of ICSR cases is unacceptable for production.

---

## 📊 Detailed Analysis by Category

### Category 1: ICSR (Individual Case Safety Reports)

| Test | Expected | Predicted | Confidence | Status |
|------|----------|-----------|------------|--------|
| Severe Allergic Rash | ICSR | ICSR | 0.950 | ✅ PASS |
| Stevens-Johnson Syndrome | ICSR | ICSR | 0.950 | ✅ PASS |
| Drug-Induced Hepatotoxicity | ICSR | Non-ICSR | 0.420 | ❌ FAIL |
| Complex Multi-Drug | ICSR | ICSR | 0.950 | ✅ PASS |
| Pediatric Allergic Reaction | ICSR | ICSR | 0.950 | ✅ PASS |

**Pattern**: 
- ✅ Works well with strong MeSH terms + "Case Reports" publication type
- ❌ Fails when ensemble voting includes LLM (LLM always votes Non-ICSR with 0.3 confidence)

---

### Category 2: Safety_Information

| Test | Expected | Predicted | Confidence | Status |
|------|----------|-----------|------------|--------|
| Clinical Trial Safety | Safety_Info | Non-ICSR | 0.950 | ❌ FAIL |
| Post-Marketing Surveillance | Safety_Info | Non-ICSR | 0.420 | ❌ FAIL |
| Meta-Analysis | Safety_Info | Non-ICSR | 0.950 | ❌ FAIL |
| Pregnancy Safety Study | Safety_Info | Non-ICSR | 0.416 | ❌ FAIL |

**Pattern**: 
- ❌ Safety_Information class is **never** predicted
- All safety studies classified as Non-ICSR
- Rule-based classifier doesn't have logic for Safety_Information
- BERT sometimes detects it (e.g., 0.364 confidence) but gets outvoted

---

### Category 3: Non-ICSR

| Test | Expected | Predicted | Confidence | Status |
|------|----------|-----------|------------|--------|
| Review Article | Non-ICSR | Non-ICSR | 0.950 | ✅ PASS |
| Mechanistic Study | Non-ICSR | Non-ICSR | 0.420 | ⚠️ PASS (low conf) |
| Epidemiological Study | Non-ICSR | Non-ICSR | 0.471 | ⚠️ PASS (low conf) |
| Clinical Guidelines | Non-ICSR | Non-ICSR | 0.420 | ⚠️ PASS (low conf) |

**Pattern**: 
- ✅ Non-ICSR detection works well
- ⚠️ But confidence is often low (0.42-0.47)
- This is the "default" classification when uncertain

---

### Category 4: Rejected

| Test | Expected | Predicted | Confidence | Status |
|------|----------|-----------|------------|--------|
| Retracted Article | Rejected | Non-ICSR | 0.420 | ❌ FAIL |
| Duplicate Publication | Rejected | Non-ICSR | 0.420 | ❌ FAIL |
| Insufficient Information | Rejected | Non-ICSR | 0.420 | ❌ FAIL |

**Pattern**: 
- ❌ Rejected class is **never** predicted
- No logic to detect retracted/duplicate publications
- No quality threshold for insufficient information

---

### Edge Cases

| Test | Expected | Predicted | Confidence | Status |
|------|----------|-----------|------------|--------|
| Case Series (Borderline) | ICSR | Non-ICSR | 0.420 | ❌ FAIL |
| No Metadata (Text Only) | ICSR | ICSR | 0.742 | ✅ PASS |
| Conflicting Signals | ICSR | Non-ICSR | 0.950 | ❌ FAIL |
| Perfect ICSR (All Signals) | ICSR | Non-ICSR | 0.420 | ❌ FAIL |

**Pattern**: 
- ✅ **Impressive**: Text-only classification works! (No metadata, still detected ICSR)
- ❌ Conflicting signals: "Review" publication type overrides "Case Reports"
- ❌ Even "perfect" ICSR with all signals can fail due to LLM voting

---

## 🔍 Model Performance Analysis

### Rule-Based Classifier:
- **Usage**: 20/20 tests (100%)
- **Accuracy**: Good for ICSR when metadata present
- **Issues**:
  - No logic for Safety_Information
  - No logic for Rejected
  - Publication type precedence issues (Review overrides Case Reports)

### BERT Classifier:
- **Usage**: 12/20 tests (60%)
- **Accuracy**: Mixed
- **Strengths**: Sometimes detects Safety_Information (0.364 confidence)
- **Issues**: Gets outvoted by rule-based + LLM

### LLM Classifier (GPT-4o-mini):
- **Usage**: 12/20 tests (60%)
- **Accuracy**: **VERY POOR**
- **Pattern**: Consistently votes Non-ICSR with 0.3 confidence
- **Issues**: 
  - Appears to be overly conservative
  - May have prompt engineering issues
  - Dragging down ensemble performance

---

## 🎯 Ensemble Voting Analysis

### Decision Paths:
- **rule_based_only**: 8 tests (40%)
  - High confidence (0.95)
  - Good accuracy when metadata present
  
- **full_ensemble**: 12 tests (60%)
  - Lower confidence (0.42-0.74)
  - LLM consistently votes Non-ICSR, dragging down results

### Voting Pattern Issues:

**Example: Fatal Anaphylaxis (Should be ICSR)**
```
rule_based: Non-ICSR (0.500) ← Wrong
bert: ICSR (0.714) ← Correct
llm: Non-ICSR (0.300) ← Wrong
Result: Non-ICSR (majority vote 2/3) ← WRONG
```

**Example: Drug-Induced Hepatotoxicity (Should be ICSR)**
```
rule_based: Non-ICSR (0.500) ← Wrong
bert: ICSR (0.714) ← Correct
llm: Non-ICSR (0.300) ← Wrong
Result: Non-ICSR (majority vote 2/3) ← WRONG
```

**Problem**: LLM + rule-based voting together (2/3) overrides correct BERT classification.

---

## 🔧 Root Causes

### 1. **LLM Classifier Issues** 🔴
- Consistently votes Non-ICSR with low confidence (0.3)
- Appears to be overly conservative or has prompt issues
- Dragging down ensemble performance

### 2. **Missing Classification Logic** 🔴
- No Safety_Information detection in rule-based classifier
- No Rejected detection logic
- No quality thresholding

### 3. **Publication Type Precedence** 🟡
- "Review" overrides "Case Reports" when both present
- Should prioritize "Case Reports" for ICSR detection

### 4. **Entity Extraction Issues** 🟡
- Drug mentions not being detected (e.g., "amoxicillin" → 0 drug mentions)
- Adverse event mentions not being detected consistently

---

## 📋 Recommendations

### **Priority 1: Fix LLM Classifier** 🔴 **CRITICAL**

**Problem**: LLM consistently votes Non-ICSR with 0.3 confidence

**Solutions**:
1. **Review and fix LLM prompt engineering**
   - Current prompt may be too conservative
   - Add explicit instructions for ICSR detection
   - Provide examples of each classification class

2. **Adjust LLM confidence calibration**
   - 0.3 confidence is too low and unreliable
   - May need to recalibrate or retrain

3. **Consider LLM fallback strategy**
   - Only use LLM for truly ambiguous cases
   - Don't let LLM override high-confidence rule-based/BERT results

**Expected Impact**: Increase ICSR detection from 45% → 85%+

---

### **Priority 2: Add Safety_Information Logic** 🔴 **CRITICAL**

**Problem**: Safety_Information class never predicted

**Solutions**:
1. **Add rule-based logic for Safety_Information**:
   ```python
   if publication_type in ['Clinical Trial', 'Meta-Analysis', 'Systematic Review']:
       if 'safety' in title.lower() or 'adverse events' in abstract.lower():
           return 'Safety_Information'
   
   if mesh_terms contains ['Pharmacovigilance', 'Drug Safety', 'Post-Marketing']:
       return 'Safety_Information'
   ```

2. **Train BERT on Safety_Information examples**
   - Current BERT sometimes detects it but gets outvoted
   - Need more training data for this class

**Expected Impact**: 0% → 80%+ Safety_Information detection

---

### **Priority 3: Add Rejected Logic** 🟡 **HIGH**

**Problem**: Rejected class never predicted

**Solutions**:
1. **Add retraction detection**:
   ```python
   if 'RETRACTED' in title or 'retraction' in abstract.lower():
       return 'Rejected'
   
   if publication_type == 'Retracted Publication':
       return 'Rejected'
   ```

2. **Add duplicate detection**:
   ```python
   if 'DUPLICATE' in title or 'duplicate publication' in abstract.lower():
       return 'Rejected'
   ```

3. **Add quality threshold**:
   ```python
   if len(abstract) < 50 or len(title) < 10:
       return 'Rejected'  # Insufficient information
   ```

**Expected Impact**: 0% → 90%+ Rejected detection

---

### **Priority 4: Fix Entity Extraction** 🟡 **HIGH**

**Problem**: Drug/adverse event mentions not detected

**Example**: "amoxicillin" in text → 0 drug mentions

**Solutions**:
1. Use medical NER (Named Entity Recognition)
2. Implement drug dictionary lookup
3. Use regex patterns for common drug names
4. Add adverse event keyword detection

**Expected Impact**: Improve rule-based evidence quality

---

### **Priority 5: Fix Publication Type Precedence** 🟢 **MEDIUM**

**Problem**: "Review" overrides "Case Reports"

**Solution**:
```python
# Prioritize Case Reports for ICSR detection
if 'Case Reports' in publication_types:
    # Don't let 'Review' override this
    return check_icsr_criteria()
```

**Expected Impact**: Reduce false negatives for ICSR

---

## 📈 Expected Improvements

### After Implementing All Recommendations:

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Overall Pass Rate** | 30% | 85%+ | +183% |
| **ICSR Detection** | 45% | 90%+ | +100% |
| **Safety_Info Detection** | 0% | 80%+ | +∞ |
| **Rejected Detection** | 0% | 90%+ | +∞ |
| **Non-ICSR Detection** | 100% | 95% | -5% (acceptable) |
| **Avg Confidence** | 0.650 | 0.850 | +31% |

---

## 🎯 Action Plan

### Phase 1: Critical Fixes (Week 1)
1. ✅ Fix LLM prompt engineering
2. ✅ Add Safety_Information logic
3. ✅ Add Rejected detection logic

### Phase 2: Enhancements (Week 2)
4. ✅ Improve entity extraction
5. ✅ Fix publication type precedence
6. ✅ Recalibrate ensemble voting weights

### Phase 3: Validation (Week 3)
7. ✅ Re-run comprehensive test suite
8. ✅ Test with real-world data
9. ✅ Deploy to production

---

## 📊 Test Data Summary

### Test Coverage:
- **ICSR**: 11 tests (55%)
  - Classic ICSR cases: 5
  - Edge cases: 4
  - Borderline cases: 2

- **Safety_Information**: 4 tests (20%)
  - Clinical trials: 1
  - Post-marketing: 1
  - Meta-analysis: 1
  - Special populations: 1

- **Non-ICSR**: 4 tests (20%)
  - Reviews: 1
  - Mechanistic studies: 1
  - Epidemiological: 1
  - Guidelines: 1

- **Rejected**: 3 tests (15%)
  - Retracted: 1
  - Duplicate: 1
  - Insufficient: 1

---

## 🔗 Related Files

- **Test Script**: `test_classification_comprehensive.py`
- **Test Results**: `classification_test_results_20251030_000927.json`
- **Classification Service**: `services/pv-classification-service/main.py`
- **Rule-Based Classifier**: `services/pv-classification-service/rule_based_classifier.py`
- **BERT Classifier**: `services/pv-classification-service/bert_classifier.py`
- **LLM Classifier**: `services/pv-classification-service/llm_classifier.py`

---

## ✅ Conclusion

The comprehensive test revealed **significant issues** with the classification system:

1. **LLM classifier is broken** - consistently voting Non-ICSR with 0.3 confidence
2. **Safety_Information class is not being used** - all safety studies misclassified as Non-ICSR
3. **Rejected class is not being used** - no logic to detect retracted/duplicate/low-quality documents
4. **ICSR detection rate is only 45%** - unacceptable for production

**However**, the test also revealed **strengths**:
- Rule-based classifier works well with proper metadata
- BERT classifier shows promise
- Text-only classification works (impressive!)
- Non-ICSR detection is accurate

**Next Steps**: Implement the recommended fixes in priority order, starting with the LLM classifier and Safety_Information logic.

---

**Report Generated**: October 30, 2025, 00:15  
**Test Suite Version**: 1.0  
**Classification Service**: v1.0.0

