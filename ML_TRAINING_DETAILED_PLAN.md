# Detailed Plan: PubMed Classification Model Training

## 📋 **Complete Implementation Plan**

---

## **PHASE 1: Data Collection & Auto-Labeling (Day 1 - 4 hours)**

### **Objective:**
Collect 2,000 diverse medical articles from PubMed and automatically label them into 4 categories.

### **What We'll Build:**
**Script 1: `01_collect_pubmed_data.py`**

### **How It Works:**

#### **Step 1.1: Define Search Queries (Smart Targeting)**

We'll use **40 carefully crafted queries** to get diverse examples:

**ICSR Queries (10 queries):**
- "adverse drug reaction case report"
- "adverse event following immunization case"
- "drug induced liver injury case report"
- "anaphylaxis drug case report"
- "Stevens-Johnson syndrome drug case"
- "drug hypersensitivity case report"
- "medication error adverse event"
- "vaccine adverse event case report"
- "drug overdose case report"
- "fatal adverse drug reaction case"

**Safety Information Queries (8 queries):**
- "clinical trial drug safety"
- "phase III adverse events"
- "post-marketing safety study"
- "pharmacovigilance study"
- "drug safety surveillance"
- "observational study drug safety"
- "cohort study adverse events"
- "registry study drug safety"

**Non-ICSR Queries (8 queries):**
- "diabetes mellitus treatment"
- "hypertension management"
- "cancer pathophysiology"
- "cardiovascular disease prevention"
- "infectious disease epidemiology"
- "antibiotic resistance mechanisms"
- "psychiatric disorder diagnosis"
- "chronic kidney disease treatment"

**Rejected Queries (8 queries):**
- "systematic review drug therapy"
- "meta-analysis adverse events"
- "literature review pharmacology"
- "animal study drug toxicity"
- "in vitro drug effects"
- "editorial drug safety"
- "drug development protocol"
- "preclinical drug study"

**Why This Works:**
- Each query targets specific article types
- Ensures balanced dataset across all 4 classes
- Gets real-world examples of each category

---

#### **Step 1.2: Auto-Labeling Algorithm (Intelligent Pattern Matching)**

The auto-labeler uses **regex pattern matching** with weighted scoring:

**ICSR Detection Patterns:**
```python
Strong Indicators (weight: 3):
- "case report"
- "45-year-old patient developed..."
- "death following drug"
- "hospitalization due to"
- "patient experienced anaphylaxis"

Moderate Indicators (weight: 1):
- "adverse reaction"
- "side effect"
- "toxicity"
- "hypersensitivity"
```

**Safety Information Patterns:**
```python
Strong Indicators (weight: 3):
- "clinical trial"
- "phase III study"
- "post-marketing surveillance"
- "pharmacovigilance study"

Moderate Indicators (weight: 1):
- "safety profile"
- "tolerability"
- "real-world evidence"
```

**Rejected Patterns:**
```python
Strong Indicators (weight: 3):
- "systematic review"
- "meta-analysis"
- "editorial"
- "in vitro"
- "animal study"
```

**Scoring Logic:**
1. Count matches for each category
2. Strong match = 3 points, Moderate = 1 point
3. Highest score wins
4. Assign confidence level:
   - High: 2+ strong indicators
   - Medium: 1 strong or 3+ moderate
   - Low: unclear patterns

**Expected Accuracy:** 75-85% (good enough for initial training)

---

#### **Step 1.3: Collection Process**

```
For each query:
    1. Search PubMed (50 articles per query)
    2. Get: title, abstract, authors, journal, date, DOI, MeSH terms
    3. Auto-label using pattern matching
    4. Assign confidence score
    5. Save to dataset
    
Total: 40 queries × 50 articles = 2,000 articles
```

**Output Files:**
- `pubmed_raw_dataset.csv` - All collected articles with metadata
- `pubmed_labeled_dataset.csv` - High/medium confidence articles only
- `collection_statistics.json` - Collection metrics

**Time Estimate:** 2-4 hours (depends on network speed)

---

## **PHASE 2: Data Preparation & Splitting (Day 1 - 30 minutes)**

### **Objective:**
Clean data, balance classes, split into train/validation/test sets.

### **What We'll Build:**
**Script 2: `02_prepare_training_data.py`**

### **How It Works:**

#### **Step 2.1: Data Cleaning**
```python
1. Remove duplicates (by PMID)
2. Remove articles with missing abstracts
3. Remove very short abstracts (<100 characters)
4. Remove non-English articles (if detected)
5. Remove articles with low confidence (<0.6)
```

#### **Step 2.2: Class Balancing**
```python
# Check class distribution
ICSR: 600 articles
Non-ICSR: 550 articles
Safety_Information: 500 articles
Rejected: 450 articles

# Balance by undersampling majority class
Target: 450 articles per class (balanced)
Total after balancing: 1,800 articles
```

**Why Balance?**
- Prevents model bias toward majority class
- Ensures equal learning for all categories
- Improves minority class performance

#### **Step 2.3: Train/Val/Test Split**
```python
1,800 articles split as:
- Train: 1,260 articles (70%) - 315 per class
- Validation: 270 articles (15%) - 67-68 per class
- Test: 270 articles (15%) - 67-68 per class

Stratified split ensures each split has same class distribution
```

**Output Files:**
- `train.csv` - Training data (1,260 articles)
- `val.csv` - Validation data (270 articles)
- `test.csv` - Test data (270 articles)
- `data_stats.json` - Statistics report

**Time Estimate:** 30 minutes

---

## **PHASE 3: Model Training Setup (Day 1 - 1 hour)**

### **Objective:**
Set up training environment and dependencies.

### **What We'll Build:**
**Script 3: `03_setup_training_env.py`**

### **How It Works:**

#### **Step 3.1: Check GPU Availability**
```python
import torch
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

**Options:**
- **Have GPU**: Use it (fast training - 2-4 hours)
- **No GPU**: Use Google Colab Pro (recommended)
- **CPU only**: Works but slow (12-24 hours)

#### **Step 3.2: Install Dependencies**
```bash
pip install torch==2.1.0
pip install transformers==4.35.0
pip install datasets==2.14.0
pip install scikit-learn==1.3.0
pip install wandb==0.15.0  # Optional: experiment tracking
```

#### **Step 3.3: Download PubMedBERT Model**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=4  # 4 classes
)
```

**Model Details:**
- **Name**: PubMedBERT
- **Size**: 440 MB
- **Pre-trained on**: 14M PubMed abstracts + 3M full-text articles
- **Base architecture**: BERT-base (110M parameters)
- **Why this model**: Best for medical text classification

**Time Estimate:** 30-60 minutes (includes downloads)

---

## **PHASE 4: Model Training (Day 2 - 2-4 hours GPU / 12-24 hours CPU)**

### **Objective:**
Fine-tune PubMedBERT on our labeled dataset.

### **What We'll Build:**
**Script 4: `04_train_classifier.py`**

### **How It Works:**

#### **Step 4.1: Data Tokenization**
```python
# Combine title and abstract
text = f"{title} [SEP] {abstract}"

# Tokenize using PubMedBERT tokenizer
tokens = tokenizer(
    text,
    max_length=512,  # BERT limit
    truncation=True,  # Cut if longer
    padding=True      # Pad if shorter
)
```

**Why 512 tokens?**
- BERT's maximum sequence length
- Covers title + abstract for most articles
- ~400-500 words typically

#### **Step 4.2: Training Configuration**
```python
Training Parameters:
- Learning rate: 2e-5 (standard for BERT fine-tuning)
- Batch size: 16 (fits in 8GB GPU)
- Epochs: 5 (usually sufficient)
- Warmup steps: 500 (gradual learning rate increase)
- Weight decay: 0.01 (regularization)
- Optimizer: AdamW (BERT standard)
- Early stopping: 3 epochs patience
```

**Why These Values?**
- Learning rate: Prevents catastrophic forgetting of pre-trained weights
- Batch size: Balances speed and memory usage
- Epochs: More than this risks overfitting
- Early stopping: Prevents overfitting

#### **Step 4.3: Training Process**
```
Epoch 1:
  Train: 1,260 articles in 79 batches
  Validate: 270 articles
  Accuracy: ~65%
  
Epoch 2:
  Accuracy: ~78%
  
Epoch 3:
  Accuracy: ~85%
  Best model saved!
  
Epoch 4:
  Accuracy: ~86%
  Best model updated!
  
Epoch 5:
  Accuracy: ~85% (no improvement)
  Early stopping triggered
  
Final Model: Epoch 4 checkpoint
```

#### **Step 4.4: Evaluation Metrics**
```python
Metrics tracked:
1. Accuracy: Overall correctness
2. Precision: Of predicted ICSRs, how many are real ICSRs?
3. Recall: Of real ICSRs, how many did we find?
4. F1-Score: Harmonic mean of precision and recall
5. Per-class metrics: For all 4 classes
6. Confusion matrix: Where does model get confused?
```

**Target Performance:**
- Overall accuracy: ≥85%
- ICSR precision: ≥88% (important: minimize false positives)
- ICSR recall: ≥85% (important: don't miss real ICSRs)
- F1-Score: ≥86%

**Output Files:**
- `models/pubmedbert-classifier/` - Model checkpoints during training
- `models/pubmedbert-classifier-final/` - Best model
- `training_logs/` - Training metrics
- `training_curves.png` - Loss/accuracy graphs

**Time Estimate:** 
- GPU (T4): 2-4 hours
- CPU: 12-24 hours

---

## **PHASE 5: Model Evaluation (Day 2 - 1 hour)**

### **Objective:**
Thoroughly evaluate model performance on test set.

### **What We'll Build:**
**Script 5: `05_evaluate_model.py`**

### **How It Works:**

#### **Step 5.1: Test Set Evaluation**
```python
Load test set (270 articles)
For each article:
    1. Tokenize
    2. Get model prediction
    3. Compare with true label
    4. Record results
```

#### **Step 5.2: Generate Reports**
```
Classification Report:
                    precision  recall  f1-score  support
ICSR                   0.89     0.87     0.88       68
Non-ICSR               0.84     0.85     0.84       67
Safety_Information     0.86     0.88     0.87       68
Rejected               0.92     0.90     0.91       67

accuracy                                  0.88      270
macro avg              0.88     0.88     0.88      270
weighted avg           0.88     0.88     0.88      270
```

#### **Step 5.3: Confusion Matrix**
```
                  Predicted
Actual      ICSR  Non-ICSR  Safety  Rejected
ICSR         59      5        3        1
Non-ICSR      4     57        5        1
Safety        3      4       60        1
Rejected      1      2        1       63
```

**What to Look For:**
- High diagonal values (correct predictions)
- Low off-diagonal (misclassifications)
- No systematic bias

#### **Step 5.4: Error Analysis**
```python
# Analyze misclassified examples
errors = []
for article in test_set:
    if prediction != true_label:
        errors.append({
            'pmid': article.pmid,
            'title': article.title,
            'true': true_label,
            'predicted': prediction,
            'confidence': confidence
        })

# Save for manual review
errors.to_csv('classification_errors.csv')
```

**Output Files:**
- `evaluation_report.txt` - Classification metrics
- `confusion_matrix.png` - Visualization
- `classification_errors.csv` - Misclassified articles for review
- `evaluation_stats.json` - Detailed metrics

**Time Estimate:** 30-60 minutes

---

## **PHASE 6: Model Deployment (Day 3 - 2-3 hours)**

### **Objective:**
Deploy trained model in production literature-automation service.

### **What We'll Build:**
**Script 6: `06_deploy_model.py`**

### **How It Works:**

#### **Step 6.1: Model Optimization (Optional)**
```python
# Convert to ONNX for faster inference
python -m transformers.onnx \
    --model=models/pubmedbert-classifier-final \
    --output=models/pubmedbert-classifier.onnx

# 30-40% faster inference on CPU
```

#### **Step 6.2: Update Production Service**
```python
# Replace classification_service.py with production version
# Uses trained model instead of keyword matching

Changes:
1. Load fine-tuned PubMedBERT model
2. Use model for predictions instead of rules
3. Add confidence thresholds
4. Add fallback to rules if model uncertain
```

#### **Step 6.3: Docker Integration**
```dockerfile
# Add model to Docker image
COPY models/pubmedbert-classifier-final /app/models/
RUN pip install torch transformers

# Model loaded on service startup
```

#### **Step 6.4: Update API Response**
```json
{
  "classification": "ICSR",
  "confidence": 0.92,
  "probabilities": {
    "ICSR": 0.92,
    "Non-ICSR": 0.04,
    "Safety_Information": 0.03,
    "Rejected": 0.01
  },
  "model_version": "pubmedbert-v1.0",
  "reasoning": "High confidence ICSR classification based on case report indicators"
}
```

**Output:**
- Production model deployed
- API updated
- Docker image rebuilt
- Service restarted

**Time Estimate:** 2-3 hours

---

## **PHASE 7: Monitoring & Validation (Day 3 - Ongoing)**

### **Objective:**
Monitor model performance in production.

### **What We'll Build:**
**Script 7: `07_monitor_model.py`**

### **How It Works:**

#### **Step 7.1: Log Predictions**
```python
# Log every classification
{
  "timestamp": "2025-10-06T10:30:00Z",
  "article_id": "PMC12345",
  "prediction": "ICSR",
  "confidence": 0.89,
  "processing_time_ms": 234
}
```

#### **Step 7.2: Track Metrics**
```python
Daily Metrics:
- Total predictions: 150
- Average confidence: 0.84
- Low confidence count: 12 (8%)
- Processing time: avg 250ms

Weekly Metrics:
- Predictions by class
- Confidence distribution
- Performance trends
```

#### **Step 7.3: Alert on Issues**
```python
Alerts:
- Confidence < 0.7 for >20% of predictions
- Processing time > 1 second
- Unusual class distribution
- Model errors/crashes
```

**Output:**
- Real-time monitoring dashboard
- Daily/weekly reports
- Alerts for issues

---

## 📊 **Summary: Complete Timeline**

### **Day 1: Data Collection & Setup (6-7 hours)**
- ✅ Collect 2,000 articles from PubMed (2-4 hours)
- ✅ Auto-label using intelligent patterns (included above)
- ✅ Prepare and split data (30 min)
- ✅ Set up training environment (1 hour)
- ✅ Start model training (2-4 hours, can run overnight)

### **Day 2: Training & Evaluation (3-5 hours)**
- ✅ Complete training (continues from Day 1)
- ✅ Evaluate on test set (1 hour)
- ✅ Analyze errors (1 hour)
- ✅ Validate with domain expert (1-2 hours)

### **Day 3: Deployment (2-3 hours)**
- ✅ Deploy model to production (2 hours)
- ✅ Test API endpoints (30 min)
- ✅ Set up monitoring (30 min)

### **Total: 11-15 hours of work over 3 days**

---

## 💰 **Resource Requirements**

### **Compute:**
- **Option A (Free)**: Google Colab free tier
  - GPU: Tesla K80
  - Training time: 4-6 hours
  - Cost: $0

- **Option B (Recommended)**: Google Colab Pro
  - GPU: Tesla T4 or P100
  - Training time: 2-4 hours
  - Cost: $10/month

- **Option C**: Your local machine
  - Needs: GPU with 8GB+ VRAM
  - Training time: 2-4 hours
  - Cost: $0 (existing hardware)

- **Option D**: AWS SageMaker
  - Instance: ml.p3.2xlarge (V100)
  - Training time: 1-2 hours
  - Cost: ~$3-6 one-time

### **Storage:**
- Training data: ~500 MB
- Model files: ~500 MB
- Logs and outputs: ~100 MB
- **Total: ~1 GB**

### **Personnel:**
- ML Engineer: 11-15 hours over 3 days
- Domain Expert: 2-3 hours for validation (optional)

---

## 🎯 **Expected Results**

### **Model Performance:**
- **Overall Accuracy**: 85-90%
- **ICSR Precision**: 88-92%
- **ICSR Recall**: 85-90%
- **F1-Score**: 86-91%

### **Production Performance:**
- **Inference Speed**: 200-500ms per article
- **Throughput**: 500-1000 articles/hour
- **Memory Usage**: ~2GB RAM (model loaded)

### **Business Impact:**
- **Manual Review Reduction**: 70-80%
- **Time Savings**: 85% faster than manual classification
- **Cost Savings**: ~90% reduction in classification cost

---

## 📋 **Files We'll Create**

```
ml_training/
├── 01_collect_pubmed_data.py          # Data collection script
├── 02_prepare_training_data.py         # Data preparation
├── 03_setup_training_env.py            # Environment setup
├── 04_train_classifier.py              # Training script
├── 05_evaluate_model.py                # Evaluation script
├── 06_deploy_model.py                  # Deployment script
├── 07_monitor_model.py                 # Monitoring script
├── requirements.txt                     # Python dependencies
├── README.md                           # Documentation
│
├── data/
│   ├── pubmed_raw_dataset.csv          # Raw collected data
│   ├── pubmed_labeled_dataset.csv      # Auto-labeled data
│   ├── train.csv                       # Training set
│   ├── val.csv                         # Validation set
│   ├── test.csv                        # Test set
│   └── collection_statistics.json      # Stats
│
├── models/
│   ├── pubmedbert-classifier/          # Training checkpoints
│   └── pubmedbert-classifier-final/    # Best model
│
├── logs/
│   ├── training_logs/                  # Training metrics
│   └── evaluation_logs/                # Evaluation results
│
└── outputs/
    ├── confusion_matrix.png
    ├── training_curves.png
    ├── evaluation_report.txt
    └── classification_errors.csv
```

---

## ✅ **Success Criteria**

### **Phase 1 Success:**
- [ ] Collected 2,000+ articles from PubMed
- [ ] Auto-labeled with ≥75% accuracy
- [ ] Balanced classes (400-500 per class)

### **Phase 2 Success:**
- [ ] Clean dataset with no duplicates
- [ ] Proper train/val/test split
- [ ] No data leakage between splits

### **Phase 3 Success:**
- [ ] Environment set up correctly
- [ ] Dependencies installed
- [ ] Model downloaded and working

### **Phase 4 Success:**
- [ ] Training completes without errors
- [ ] Validation accuracy ≥85%
- [ ] No overfitting (train/val gap <5%)

### **Phase 5 Success:**
- [ ] Test accuracy ≥85%
- [ ] ICSR precision ≥88%
- [ ] No systematic bias in errors

### **Phase 6 Success:**
- [ ] Model deployed to production
- [ ] API returns correct predictions
- [ ] Response time <500ms

### **Phase 7 Success:**
- [ ] Monitoring dashboard active
- [ ] Predictions logged correctly
- [ ] Alerts working

---

## ⚠️ **Risk Mitigation**

### **Risk 1: Poor Auto-Labeling Quality**
- **Mitigation**: Review sample of 100 articles manually
- **Threshold**: If <70% accuracy, refine patterns
- **Fallback**: Manual labeling of unclear cases

### **Risk 2: Insufficient Training Data**
- **Mitigation**: Start with 1,500 articles minimum
- **Threshold**: Need ≥300 per class
- **Fallback**: Collect more from additional queries

### **Risk 3: Model Doesn't Converge**
- **Mitigation**: Adjust learning rate, try different optimizer
- **Threshold**: If accuracy <75% after 5 epochs
- **Fallback**: Use ensemble with rules + ML

### **Risk 4: Overfitting**
- **Mitigation**: Early stopping, dropout, regularization
- **Threshold**: If train/val gap >10%
- **Fallback**: Reduce model complexity

### **Risk 5: Production Performance Issues**
- **Mitigation**: Model quantization, ONNX conversion
- **Threshold**: If inference >1 second
- **Fallback**: Batch processing, GPU inference

---

## 🚀 **Next Steps After This Plan**

Once you approve this plan, I will:

1. ✅ Create all 7 Python scripts
2. ✅ Create requirements.txt
3. ✅ Create README with instructions
4. ✅ Run data collection (or guide you through it)
5. ✅ Help with training setup
6. ✅ Monitor training progress
7. ✅ Help with deployment

---

## ❓ **Questions to Confirm**

Before we proceed:

1. **GPU Access**: Do you have GPU, or should we use Google Colab Pro?
2. **Time Commitment**: Can you dedicate 3 days for this? (can run scripts, review results)
3. **Domain Expert**: Do you have someone to validate a sample of auto-labels?
4. **Approval**: Does this plan meet your expectations?

**Once you confirm, I'll start creating all the scripts!** 🚀


