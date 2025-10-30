# Classification Fix Results

**Date**: October 30, 2025, 00:23  
**Implementation Status**: PARTIALLY COMPLETE  
**Test Results**: 30% pass rate (6/20) - **NO IMPROVEMENT YET**

---

## ✅ What Was Implemented

### 1. LLM Classifier Improvements ✅
- **Removed "be conservative" instruction** - Now has balanced guidance
- **Added explicit examples** for all 4 classes (ICSR, Safety_Information, Non-ICSR, Rejected)
- **Increased temperature** from 0.3 → 0.5 for more variation
- **Lowered fallback confidence** from 0.5 → 0.3
- **Added confidence guidelines** (0.85-0.95 high, 0.65-0.84 moderate, 0.50-0.64 low)

### 2. Safety_Information Logic ✅
- **Added Safety_Information MeSH terms** (15 terms including Pharmacovigilance, Drug Safety, Clinical Trials)
- **Added Safety_Information publication types** (12 types including Clinical Trial, Meta-Analysis, RCT)
- **Added Safety_Information keywords** (13 keywords like "safety profile", "tolerability", "surveillance")
- **Added 4 Safety_Information detection rules** with priorities

### 3. Rejected Detection Logic ✅
- **Added Retracted publication detection** (checks MeSH terms for "RETRACT")
- **Added Duplicate publication detection** (checks MeSH terms for "DUPLICATE")
- **Added In vitro/animal study detection** (2+ rejected signals)

### 4. Publication Type Precedence Fix ✅
- **Prioritized Case Reports** - Now checks ICSR_PUBLICATION_TYPES first
- **Proper rule ordering** - Rejected → ICSR → Safety_Information → Non-ICSR

---

## ❌ Issues Remaining

### **CRITICAL ISSUE: LLM Still Broken** 🔴

**Problem**: LLM classifier is STILL consistently voting Non-ICSR with 0.3 confidence

**Evidence from Test #20 (Fatal Anaphylaxis - Perfect ICSR)**:
```
rule_based: Non-ICSR (0.500)  ← Should be ICSR!
bert: ICSR (0.714)            ← Correct!
llm: Non-ICSR (0.300)         ← Still broken!
Result: Non-ICSR (2/3 vote)   ← WRONG!
```

**Root Cause**: The LLM prompt changes haven't taken effect yet, OR the LLM (GPT-4o-mini) needs more explicit instructions.

---

### **Issue #2: Rule-Based Not Detecting ICSR Correctly** 🔴

**Problem**: Rule-based classifier returning 0.5 confidence (low) for clear ICSR cases

**Example - Test #20 (Fatal Anaphylaxis)**:
```
Evidence:
  - patient_mentions: 8 ✅
  - drug_mentions: 1 ✅
  - adverse_event_mentions: 0 ❌ (Should detect "anaphylaxis")
  - temporal_mentions: 2 ✅
  - icsr_mesh_count: 2 ✅ (Anaphylaxis, Drug Hypersensitivity)
  - Publication Type: Case Reports ✅

Result: Non-ICSR (0.500) ← WRONG! Should be ICSR (0.95)
```

**Root Cause**: 
1. "anaphylaxis" not being detected as adverse_event (not in keyword list)
2. Rule I1 not triggering even though it has Case Reports + 2 ICSR MeSH terms

---

### **Issue #3: Safety_Information Still Not Detected** 🔴

**Problem**: 0/4 Safety_Information tests passed

**Example - Test #6 (Clinical Trial Safety)**:
```
Publication Types: ['Clinical Trial', 'Randomized Controlled Trial']
Expected: Safety_Information
Predicted: Non-ICSR (0.950)
```

**Root Cause**: Rule N1 (Non-ICSR for RCT) is triggering BEFORE Rule S1 (Safety_Information for Clinical Trial)

The problem is that `Randomized Controlled Trial` is in BOTH:
- `SAFETY_INFO_PUBLICATION_TYPES`
- Was previously in `NON_ICSR_PUBLICATION_TYPES` (I removed it, but the logic still prioritizes Non-ICSR)

---

## 📊 Test Results Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Overall Pass Rate** | 30% | 30% | **0%** ❌ |
| **ICSR Detection** | 45% (5/11) | 45% (5/11) | **0%** ❌ |
| **Safety_Info Detection** | 0% (0/4) | 0% (0/4) | **0%** ❌ |
| **Rejected Detection** | 0% (0/3) | 0% (0/3) | **0%** ❌ |
| **Avg Confidence** | 0.650 | 0.650 | **0%** ❌ |

**Conclusion**: **NO IMPROVEMENT** - The fixes did not work as expected.

---

## 🔍 Root Cause Analysis

### Why Didn't the Fixes Work?

1. **LLM Changes Not Applied**
   - The prompt was updated in `main.py`
   - Service was restarted
   - BUT: LLM is still behaving the same way (0.3 confidence, Non-ICSR)
   - **Possible Reason**: Using Ollama instead of OpenAI? Need to check which LLM is actually being used.

2. **Rule-Based Logic Issues**
   - Added Safety_Information rules
   - BUT: They're not triggering because of rule ordering
   - **Problem**: Non-ICSR rules (N1) are catching documents before Safety_Information rules (S1)

3. **Adverse Event Keywords Missing**
   - "anaphylaxis", "hepatotoxicity", "rash" not in adverse_event keyword list
   - Need to add more specific adverse event terms

---

## 🔧 What Needs to be Fixed

### Priority 1: Fix Rule Ordering 🔴 CRITICAL

**Problem**: Non-ICSR rules catching Safety_Information documents

**Solution**: Move Safety_Information checks BEFORE checking for Non-ICSR publication types

**Current Order**:
```python
1. Check ICSR
2. Check Safety_Information
3. Check Non-ICSR ← This catches RCTs before Safety_Information!
```

**Should Be**:
```python
1. Check ICSR
2. Check Safety_Information (with RCT + safety keywords)
3. Check Non-ICSR (only if NOT safety-focused)
```

---

### Priority 2: Add Missing Adverse Event Keywords 🔴 CRITICAL

**Add to `ICSR_KEYWORDS['adverse_event']`**:
```python
'anaphylaxis', 'hepatotoxicity', 'nephrotoxicity', 'cardiotoxicity',
'rash', 'urticaria', 'angioedema', 'hypersensitivity',
'stevens-johnson', 'liver injury', 'liver failure',
'syndrome', 'failure', 'damage', 'impairment'
```

---

### Priority 3: Fix Rule I1 Logic 🔴 CRITICAL

**Current Rule I1**:
```python
if pub_types & self.ICSR_PUBLICATION_TYPES:
    if evidence['icsr_mesh_count'] >= 1 or (
        evidence['patient_mentions'] >= 2 and 
        evidence['adverse_event_mentions'] >= 1
    ):
        return ("ICSR", 0.95, ...)
```

**Problem**: Requires `adverse_event_mentions >= 1`, but "anaphylaxis" not detected

**Solution**: Lower threshold or add more keywords
```python
if pub_types & self.ICSR_PUBLICATION_TYPES:
    if evidence['icsr_mesh_count'] >= 1:  # Remove adverse_event requirement
        return ("ICSR", 0.95, ...)
```

---

### Priority 4: Investigate LLM Behavior 🟡 HIGH

**Questions to Answer**:
1. Is the service using OpenAI or Ollama?
2. Is the new prompt actually being used?
3. Why is LLM still voting Non-ICSR with 0.3 confidence?

**Check**:
```python
# In main.py, line 255
if self.use_ollama and self.ollama_classifier:
    # Using Ollama
else:
    # Using OpenAI
```

---

## 📋 Next Steps

### Immediate Actions (30 minutes)

1. ✅ **Add missing adverse event keywords** to rule_based_classifier.py
2. ✅ **Fix Rule I1 logic** - Remove adverse_event requirement when ICSR MeSH terms present
3. ✅ **Fix Safety_Information rule ordering** - Check before Non-ICSR
4. ✅ **Restart service and re-test**

### Investigation (15 minutes)

5. ⏳ **Check which LLM is being used** (Ollama vs OpenAI)
6. ⏳ **Verify prompt is being applied** (add logging)
7. ⏳ **Test LLM directly** with a single document

---

## 📈 Expected Results After Next Round of Fixes

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Overall Pass Rate | 30% | 60%+ | +100% |
| ICSR Detection | 45% | 75%+ | +67% |
| Safety_Info Detection | 0% | 50%+ | +∞ |
| Rejected Detection | 0% | 33%+ | +∞ |

---

## ✅ Summary

### What Worked:
- ✅ Code changes were implemented correctly
- ✅ Service restarted successfully
- ✅ New rules and keywords added

### What Didn't Work:
- ❌ LLM still broken (0.3 confidence, Non-ICSR)
- ❌ Rule-based not detecting ICSR correctly
- ❌ Safety_Information rules not triggering
- ❌ Adverse event keywords insufficient

### Why:
- Rule ordering issues (Non-ICSR before Safety_Information)
- Missing adverse event keywords ("anaphylaxis", etc.)
- Rule I1 logic too strict
- LLM changes may not be applied (need to verify)

### Next:
- Fix rule ordering
- Add missing keywords
- Simplify Rule I1
- Investigate LLM behavior
- Re-test

---

**Status**: PARTIALLY IMPLEMENTED - Need Round 2 of fixes  
**Time Invested**: 1 hour  
**Time Needed**: 30 minutes more  
**Expected Final Pass Rate**: 60-70%

