# 📊 **RL Framework Script Relationship Chart**

## 🎯 **Main Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RL FRAMEWORK ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   ENTRY POINT   │
                    │ train_rl_agent.py │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ TRAINING ENGINE │
                    │ training_engine.py │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   RL AGENT       │
                    │   rl_agent.py   │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ IP-ENHANCED RL   │
                    │ ip_enhanced_rl_agent.py │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ NOVEL ALGORITHMS │
                    │ AMORS + HRE + CAMO │
                    └─────────────────┘
```

## 🔗 **Detailed Script Relationships**

### **1. CORE RL TRAINING FLOW**

```
train_rl_agent.py (ENTRY POINT)
    │
    ├── training_engine.py (TRAINING ORCHESTRATOR)
    │   │
    │   ├── rl_agent.py (CORE RL AGENT)
    │   │   │
    │   │   ├── rule_optimizer.py (RULE CONFIGURATION)
    │   │   │
    │   │   └── ip_enhanced_rl_agent.py (IP INTEGRATION)
    │   │       │
    │   │       ├── adaptive_reward_shaping.py (AMORS)
    │   │       │
    │   │       ├── hierarchical_rule_evolution.py (HRE)
    │   │       │
    │   │       └── confidence_aware_multi_objective.py (CAMO)
    │   │
    │   └── data_collection/ (DATA SOURCES)
    │       │
    │       ├── data_collector.py
    │       │
    │       ├── feature_extractor.py
    │       │
    │       └── data_validator.py
    │
    └── test_rl_training.py (TESTING)
```

### **2. IP VALIDATION FLOW**

```
test_ip_framework.py (IP TESTING ENTRY)
    │
    ├── ip_validation_framework.py (IP VALIDATION)
    │   │
    │   ├── ip_enhanced_rl_agent.py (IP AGENT)
    │   │   │
    │   │   ├── adaptive_reward_shaping.py (AMORS)
    │   │   │
    │   │   ├── hierarchical_rule_evolution.py (HRE)
    │   │   │
    │   │   └── confidence_aware_multi_objective.py (CAMO)
    │   │
    │   └── rl_agent.py (CORE RL)
    │
    └── test_rl_training.py (COMPONENT TESTS)
```

### **3. DATA COLLECTION FLOW**

```
collect_real_pubmed_data.py (DATA COLLECTION)
    │
    ├── data_collector.py (ORCHESTRATOR)
    │   │
    │   ├── feature_extractor.py (FEATURE EXTRACTION)
    │   │   │
    │   │   └── DocumentFeatures + ClassificationOutcome
    │   │
    │   ├── data_validator.py (DATA VALIDATION)
    │   │
    │   └── services/pv-classification-service/ (ENSEMBLE)
    │       │
    │       ├── ensemble_classifier.py
    │       │
    │       ├── rule_based_classifier.py
    │       │
    │       ├── bert_classifier.py
    │       │
    │       └── main.py (LLM CLASSIFIER)
    │
    └── show_training_example.py (DISPLAY)
```

## 🎯 **Script Categories & Relationships**

### **A. CORE RL COMPONENTS**

| **Script** | **Role** | **Depends On** | **Used By** |
|------------|----------|----------------|-------------|
| `rl_agent.py` | Core RL Agent | None | `training_engine.py`, `ip_enhanced_rl_agent.py` |
| `training_engine.py` | Training Orchestrator | `rl_agent.py`, `rule_optimizer.py` | `train_rl_agent.py` |
| `train_rl_agent.py` | Entry Point | `training_engine.py` | User execution |
| `rule_optimizer.py` | Rule Configuration | None | `training_engine.py` |

### **B. IP-ENHANCED COMPONENTS**

| **Script** | **Role** | **Depends On** | **Used By** |
|------------|----------|----------------|-------------|
| `ip_enhanced_rl_agent.py` | IP Integration | `rl_agent.py`, AMORS, HRE, CAMO | `ip_validation_framework.py` |
| `adaptive_reward_shaping.py` | AMORS Algorithm | None | `ip_enhanced_rl_agent.py` |
| `hierarchical_rule_evolution.py` | HRE Algorithm | None | `ip_enhanced_rl_agent.py` |
| `confidence_aware_multi_objective.py` | CAMO Algorithm | None | `ip_enhanced_rl_agent.py` |

### **C. VALIDATION & TESTING**

| **Script** | **Role** | **Depends On** | **Used By** |
|------------|----------|----------------|-------------|
| `ip_validation_framework.py` | IP Validation | `ip_enhanced_rl_agent.py` | `test_ip_framework.py` |
| `test_ip_framework.py` | IP Testing | `ip_validation_framework.py` | User execution |
| `test_rl_training.py` | RL Testing | `rl_agent.py`, `training_engine.py` | User execution |

### **D. DATA COLLECTION**

| **Script** | **Role** | **Depends On** | **Used By** |
|------------|----------|----------------|-------------|
| `data_collector.py` | Data Orchestrator | `feature_extractor.py`, `data_validator.py` | `collect_real_pubmed_data.py` |
| `feature_extractor.py` | Feature Extraction | None | `data_collector.py` |
| `data_validator.py` | Data Validation | `feature_extractor.py` | `data_collector.py` |
| `collect_real_pubmed_data.py` | Data Collection | `data_collector.py` | User execution |

## 🔄 **Execution Flow Diagrams**

### **1. RL Training Flow**

```
User runs: python train_rl_agent.py
    │
    ▼
training_engine.py (initializes)
    │
    ├── Loads training data from data_collection/
    │
    ├── Creates rl_agent.py (MultiObjectiveRLAgent)
    │
    ├── Creates rule_optimizer.py (RuleConfigurationGenerator)
    │
    ├── Creates ip_enhanced_rl_agent.py (IPEnhancedRLAgent)
    │   │
    │   ├── adaptive_reward_shaping.py (AMORS)
    │   │
    │   ├── hierarchical_rule_evolution.py (HRE)
    │   │
    │   └── confidence_aware_multi_objective.py (CAMO)
    │
    └── Runs training loop with all components
```

### **2. IP Validation Flow**

```
User runs: python test_ip_framework.py
    │
    ▼
ip_validation_framework.py (initializes)
    │
    ├── Creates ip_enhanced_rl_agent.py (IPEnhancedRLAgent)
    │   │
    │   ├── adaptive_reward_shaping.py (AMORS)
    │   │
    │   ├── hierarchical_rule_evolution.py (HRE)
    │   │
    │   └── confidence_aware_multi_objective.py (CAMO)
    │
    ├── Tests performance metrics
    │
    ├── Tests novelty assessment
    │
    ├── Tests patent criteria
    │
    └── Generates IP readiness report
```

### **3. Data Collection Flow**

```
User runs: python collect_real_pubmed_data.py
    │
    ▼
data_collector.py (orchestrates)
    │
    ├── feature_extractor.py (extracts features)
    │
    ├── Calls services/pv-classification-service/ (classifies)
    │   │
    │   ├── ensemble_classifier.py
    │   │
    │   ├── rule_based_classifier.py
    │   │
    │   ├── bert_classifier.py
    │   │
    │   └── main.py (LLM)
    │
    ├── data_validator.py (validates data)
    │
    └── Stores training data for RL
```

## 🎯 **Key Relationships**

### **1. Core Dependencies**
- **`train_rl_agent.py`** → **`training_engine.py`** → **`rl_agent.py`**
- **`ip_enhanced_rl_agent.py`** → **`rl_agent.py`** + **3 Novel Algorithms**
- **`ip_validation_framework.py`** → **`ip_enhanced_rl_agent.py`**

### **2. Data Flow**
- **`collect_real_pubmed_data.py`** → **`data_collector.py`** → **`feature_extractor.py`**
- **`data_collector.py`** → **`services/pv-classification-service/`** (ensemble)
- **`training_engine.py`** → **`data_collection/`** (loads training data)

### **3. Testing Flow**
- **`test_ip_framework.py`** → **`ip_validation_framework.py`** → **`ip_enhanced_rl_agent.py`**
- **`test_rl_training.py`** → **`rl_agent.py`** + **`training_engine.py`**

## 🚀 **Quick Reference**

### **Main Entry Points:**
1. **`train_rl_agent.py`** - Start RL training
2. **`test_ip_framework.py`** - Test IP framework
3. **`collect_real_pubmed_data.py`** - Collect training data

### **Core Components:**
1. **`rl_agent.py`** - Core RL implementation
2. **`ip_enhanced_rl_agent.py`** - IP integration
3. **`training_engine.py`** - Training orchestrator

### **Novel Algorithms:**
1. **`adaptive_reward_shaping.py`** - AMORS
2. **`hierarchical_rule_evolution.py`** - HRE
3. **`confidence_aware_multi_objective.py`** - CAMO

**This chart shows the complete relationship between all 21 Python files in the RL framework!** 🎯
