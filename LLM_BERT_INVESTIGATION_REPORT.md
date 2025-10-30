# 🔍 LLM and BERT Investigation Report

**Date**: October 30, 2025  
**Investigation**: Why LLM is broken and BERT isn't triggering

---

## 🎯 Executive Summary

**Root Causes Identified**:
1. ✅ **LLM Issue**: Prompt changes were made to **OpenAI** prompt, but system uses **Ollama** by default
2. ✅ **BERT Issue**: BERT **IS** triggering, but only when rule-based confidence < 0.85
3. ✅ **Real Problem**: Rule-based classifier is returning **0.95 confidence** for wrong classifications

---

## 📊 Test Results Analysis

### Current Performance: 30% Pass Rate (6/20 tests)

**Decision Path Breakdown**:
- `rule_based_only`: 15 tests (75%) - **Rule-based confidence ≥ 0.85, BERT never called**
- `full_ensemble`: 5 tests (25%) - All 3 models used

**Key Finding**: BERT and LLM are only triggered in 25% of cases!

---

## 🔍 Detailed Investigation

### Issue #1: LLM Prompt Changes Not Applied ❌

**What I Changed**:
```python
# File: services/pv-classification-service/main.py
# Lines 124-225: Updated PHARMACOVIGILANCE_EXPERT_PROMPT
```

**Actual LLM Being Used**:
```python
# File: services/pv-classification-service/main.py
# Line 234-240:
def __init__(self, use_ollama: bool = True):
    self.use_ollama = use_ollama
    self.ollama_classifier = None
    
    if use_ollama:
        # Use Ollama LLM classifier
        self.ollama_classifier = ollama_llm_classifier
```

**Problem**: System uses **Ollama** by default, NOT OpenAI!

**Ollama Prompt Location**:
```python
# File: services/pv-classification-service/ollama_llm_classifier.py
# Lines 31-47: self.classification_prompt
```

**Ollama Prompt Issues**:
1. ❌ Very basic prompt (only 16 lines)
2. ❌ No examples for any class
3. ❌ No confidence guidelines
4. ❌ Temperature = 0.1 (too conservative)
5. ❌ No regulatory elements guidance

---

### Issue #2: BERT Not Triggering (Mostly) ⚠️

**Ensemble Logic** (`ensemble_classifier.py` lines 36-39):
```python
CONFIDENCE_THRESHOLDS = {
    'rule_based': 0.85,  # If rule-based confidence < 0.85, use BERT
    'bert': 0.75,        # If BERT confidence < 0.75, use LLM
}
```

**Test Results Show**:
- **15/20 tests**: Rule-based returns 0.95 confidence → BERT never called
- **5/20 tests**: Rule-based returns low confidence → Full ensemble triggered

**Example - Safety_Info Test #6** (FAILED):
```json
{
  "test_name": "Safety_Info - Clinical Trial Safety Analysis",
  "expected": "Safety_Information",
  "predicted": "Non-ICSR",
  "confidence": 0.95,  ← Rule-based is WRONG but CONFIDENT!
  "models_used": ["rule_based"],
  "decision_path": "rule_based_only"
}
```

---

### Issue #3: Rule-Based Classifier Overconfidence 🚨

**The Real Problem**: Rule-based classifier returns **0.95 confidence** even when wrong!

**Examples of Overconfident Failures**:

1. **Test #6 - Safety_Info (Clinical Trial)**:
   - Expected: `Safety_Information`
   - Predicted: `Non-ICSR` with **0.95 confidence**
   - Why: Safety_Information rules not triggering

2. **Test #7 - Safety_Info (Post-Marketing Surveillance)**:
   - Expected: `Safety_Information`
   - Predicted: `Non-ICSR` with **0.95 confidence**
   - Why: Same issue

3. **Test #8 - Safety_Info (Meta-Analysis)**:
   - Expected: `Safety_Information`
   - Predicted: `Non-ICSR` with **0.95 confidence**
   - Why: Same issue

**Pattern**: All Safety_Information tests fail with high confidence from rule-based!

---

## 🔧 Why BERT Isn't Helping

**BERT Triggers Only When**:
- Rule-based confidence < 0.85

**But Rule-Based Returns**:
- 0.95 confidence for ICSR (correct)
- 0.95 confidence for Non-ICSR (often wrong)
- 0.95 confidence for Rejected (correct)
- **Never returns anything for Safety_Information!**

**Result**: BERT never gets a chance to correct Safety_Information misclassifications.

---

## 🔧 Why LLM Isn't Helping

**LLM Triggers Only When**:
- Rule-based confidence < 0.85 **AND** BERT confidence < 0.75

**But in the 5 tests where LLM was called**:
- Ollama LLM is using a weak prompt
- Ollama returns `Non-ICSR` with 0.3 confidence (default fallback)
- This drags down the ensemble vote

**Example - Test #3 (ICSR - Hepatotoxicity)**:
```json
{
  "test_name": "ICSR - Drug-Induced Hepatotoxicity",
  "expected": "ICSR",
  "predicted": "Non-ICSR",
  "models_used": ["rule_based", "bert", "llm"],
  "decision_path": "full_ensemble",
  "confidence": 0.42  ← All 3 models voted, still wrong!
}
```

---

## 📋 Root Cause Summary

### Primary Issue: Rule-Based Classifier Logic Gaps

1. **Safety_Information Detection**: Rules added but not triggering
   - Possible causes:
     - Rule ordering issue (Non-ICSR rules firing first)
     - Keyword matching too strict
     - MeSH term matching not working

2. **Overconfidence**: Returns 0.95 even when uncertain
   - Should return lower confidence when no strong signals

### Secondary Issue: Ollama LLM Weak Prompt

1. **Prompt Quality**: Basic 16-line prompt vs. 100+ line OpenAI prompt
2. **No Examples**: Doesn't show what each class looks like
3. **Low Temperature**: 0.1 is too conservative
4. **No Confidence Guidance**: Doesn't know when to be uncertain

### Tertiary Issue: BERT Not Given a Chance

1. **Threshold Too High**: 0.85 threshold means BERT rarely triggers
2. **Could Help**: BERT might correctly identify Safety_Information

---

## 🎯 Recommended Fixes (Priority Order)

### 🔥 CRITICAL - Fix Rule-Based Safety_Information Logic

**Problem**: Safety_Information rules not triggering at all.

**Investigation Needed**:
1. Check rule ordering in `rule_based_classifier.py`
2. Verify Safety_Information rules are actually being evaluated
3. Add debug logging to see which rules are firing

**Expected Impact**: Should fix 4-5 failed tests (Safety_Information category)

---

### 🔥 HIGH - Update Ollama LLM Prompt

**Problem**: Ollama using weak prompt, always returns Non-ICSR.

**Fix**: Copy the improved OpenAI prompt to Ollama classifier.

**File**: `services/pv-classification-service/ollama_llm_classifier.py`

**Changes**:
1. Replace lines 31-47 with full prompt (from `main.py` lines 124-225)
2. Increase temperature from 0.1 to 0.5
3. Add JSON response parsing (Ollama supports it)
4. Add confidence calculation based on response

**Expected Impact**: Should fix 2-3 failed tests where LLM was called

---

### 🟡 MEDIUM - Lower Rule-Based Confidence Threshold

**Problem**: Rule-based returns 0.95 even when wrong.

**Fix**: Add uncertainty scoring to rule-based classifier.

**Logic**:
```python
# If multiple weak signals but no strong signal
if max_confidence < 0.70:
    return classification, 0.60  # Lower confidence

# If conflicting signals
if has_conflicting_signals():
    return classification, 0.70  # Medium confidence
```

**Expected Impact**: BERT will trigger more often, improving accuracy

---

### 🟢 LOW - Adjust Ensemble Thresholds

**Problem**: BERT threshold (0.85) is too high.

**Fix**: Lower thresholds to trigger BERT more often.

```python
CONFIDENCE_THRESHOLDS = {
    'rule_based': 0.75,  # Was 0.85
    'bert': 0.70,        # Was 0.75
}
```

**Expected Impact**: More ensemble voting, better accuracy

---

## 🎬 Recommended Action Plan

### Phase 1: Debug Rule-Based Safety_Information (15 minutes)
1. Add debug logging to `rule_based_classifier.py`
2. Run one Safety_Information test
3. See which rules are firing (or not firing)
4. Fix the logic issue

### Phase 2: Update Ollama Prompt (20 minutes)
1. Copy improved prompt to `ollama_llm_classifier.py`
2. Update temperature and confidence logic
3. Restart PV classification service
4. Test

### Phase 3: Re-run Full Test Suite (5 minutes)
1. Run `test_classification_comprehensive.py`
2. Analyze results
3. Iterate if needed

**Total Time**: ~40 minutes

---

## 📊 Expected Outcomes

**Current**: 30% pass rate (6/20)

**After Phase 1** (Fix Safety_Information):
- Expected: 50-55% pass rate (10-11/20)
- Fixes: All 4 Safety_Information tests

**After Phase 2** (Fix Ollama LLM):
- Expected: 65-70% pass rate (13-14/20)
- Fixes: Tests where LLM is called

**After Phase 3** (Adjust thresholds):
- Expected: 75-85% pass rate (15-17/20)
- Fixes: Edge cases where BERT could help

---

## 🔍 Key Insights

1. **Ensemble is working correctly** - Logic is sound
2. **BERT is fine** - Just not being triggered
3. **Real issues**:
   - Rule-based Safety_Information logic broken
   - Ollama LLM using weak prompt
   - Rule-based too confident when wrong

4. **Quick wins available**:
   - Fix Safety_Information rules → +20% pass rate
   - Update Ollama prompt → +15% pass rate

---

## 🎯 Next Steps

**Immediate**: Debug why Safety_Information rules aren't triggering.

**Question for User**: Should I proceed with Phase 1 (debug Safety_Information logic)?


