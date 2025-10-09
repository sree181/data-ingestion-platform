# Production-Ready ICSR Classification - Step-by-Step Implementation

## 🎯 **Objective**
Replace keyword-based classification with production-grade AI/ML model that classifies literature into:
- **ICSR**: Individual Case Safety Reports
- **Non-ICSR**: General medical literature
- **Safety Information**: Clinical trials, post-marketing studies
- **Rejected**: Reviews, editorials, non-relevant

---

## 📋 **Implementation Roadmap**

### **Week 1-2: Data Preparation & Model Setup**
### **Week 3-4: Model Training & Validation**
### **Week 5: Integration & Deployment**
### **Week 6: Testing & Monitoring**

---

## 🗂️ **STEP 1: Prepare Training Data (3-5 days)**

### **Option A: Start with Weak Supervision (Faster)**

Use your existing keyword rules to create initial training set:

```python
# scripts/prepare_training_data.py
import pandas as pd
from pymed import PubMed
import json

class WeakSupervisionLabeler:
    def __init__(self):
        self.icsr_patterns = [
            r'case report',
            r'adverse (event|reaction|effect)',
            r'side effect',
            r'patient.*experienced',
            r'anaphylaxis',
            r'death.*following',
            r'hospitalization.*due to'
        ]
        
        self.safety_patterns = [
            r'clinical trial',
            r'phase (i|ii|iii|iv)',
            r'safety.*study',
            r'pharmacovigilance',
            r'post-marketing',
            r'observational study'
        ]
        
        self.rejected_patterns = [
            r'systematic review',
            r'meta-analysis',
            r'editorial',
            r'in vitro',
            r'animal study',
            r'review article'
        ]
    
    def auto_label(self, title: str, abstract: str) -> dict:
        """Auto-label based on patterns"""
        text = f"{title} {abstract}".lower()
        
        icsr_score = sum(1 for p in self.icsr_patterns if re.search(p, text))
        safety_score = sum(1 for p in self.safety_patterns if re.search(p, text))
        rejected_score = sum(1 for p in self.rejected_patterns if re.search(p, text))
        
        if icsr_score >= 2:
            return {"label": "ICSR", "confidence": "high" if icsr_score >= 3 else "medium"}
        elif safety_score >= 2:
            return {"label": "Safety_Information", "confidence": "medium"}
        elif rejected_score >= 2:
            return {"label": "Rejected", "confidence": "medium"}
        else:
            return {"label": "Non-ICSR", "confidence": "low"}

# Collect diverse articles from PubMed
queries = [
    "adverse drug reaction case report",
    "adverse event following immunization",
    "drug induced liver injury case",
    "clinical trial safety",
    "pharmacovigilance study",
    "systematic review drug safety",
    "cancer treatment",
    "diabetes mellitus"
]

# Download and auto-label
labeler = WeakSupervisionLabeler()
dataset = []

for query in queries:
    # Search PubMed (use existing code)
    articles = search_pubmed(query, max_results=200)
    
    for article in articles:
        label_info = labeler.auto_label(article.title, article.abstract)
        dataset.append({
            "article_id": article.pmid,
            "title": article.title,
            "abstract": article.abstract,
            "label": label_info["label"],
            "confidence": label_info["confidence"],
            "source": "pubmed"
        })

# Save for manual review
df = pd.DataFrame(dataset)
df.to_csv("data/auto_labeled_articles.csv", index=False)
print(f"Created dataset with {len(df)} articles")
print(df['label'].value_counts())
```

**Action Items:**
- [ ] Run script to collect 2,000-5,000 articles
- [ ] Review high-confidence labels (spot check 10%)
- [ ] Manually review medium-confidence labels (50%)
- [ ] Create train/val/test splits (70/15/15)

---

### **Option B: Manual Labeling (Higher Quality)**

Set up labeling interface:

```bash
# Install Label Studio
pip install label-studio

# Start server
label-studio start
```

**Labeling Guidelines:**
```markdown
## ICSR Criteria:
✅ Individual patient case described
✅ Drug/vaccine mentioned
✅ Adverse event/reaction reported
✅ Temporal relationship indicated
✅ Outcome mentioned (recovered, ongoing, fatal, etc.)

Examples:
- "A 45-year-old male developed anaphylaxis after receiving..."
- "Case report: severe liver injury following drug X..."

## Safety Information Criteria:
✅ Clinical trial or study
✅ Safety data from multiple patients
✅ Aggregate safety information
✅ Post-marketing surveillance

Examples:
- "Phase III trial safety results showed..."
- "Observational study of 1,000 patients..."

## Non-ICSR Criteria:
✅ General medical information
✅ Disease pathology
✅ Treatment guidelines
✅ No specific adverse event focus

## Rejected Criteria:
✅ Review articles
✅ Meta-analyses
✅ Editorials
✅ Preclinical studies
```

**Estimated Time:** 
- 500 articles: 20-30 hours
- 2,000 articles: 80-120 hours (with 2-3 reviewers)

---

## 🤖 **STEP 2: Set Up Model Training Infrastructure (1-2 days)**

### **2.1 Install Dependencies**

```bash
# Create virtual environment
python -m venv ml_env
source ml_env/bin/activate

# Install requirements
pip install torch==2.1.0
pip install transformers==4.35.0
pip install datasets==2.14.0
pip install scikit-learn==1.3.0
pip install wandb==0.15.0
pip install accelerate==0.24.0
pip install evaluate==0.4.1
```

### **2.2 Verify GPU Access**

```python
import torch
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

If no GPU:
- **Option A**: Use Google Colab Pro ($10/month)
- **Option B**: AWS SageMaker (pay-as-you-go)
- **Option C**: Continue with CPU (slower, but works)

---

## 🏋️ **STEP 3: Train Classification Model (2-3 days)**

### **3.1 Training Script**

```python
# scripts/train_classifier.py
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import load_dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np
import wandb

# Initialize Weights & Biases for tracking
wandb.init(project="literature-classification", name="pubmedbert-v1")

# Load data
dataset = load_dataset('csv', data_files={
    'train': 'data/train.csv',
    'validation': 'data/val.csv',
    'test': 'data/test.csv'
})

# Define label mapping
label2id = {"ICSR": 0, "Non-ICSR": 1, "Safety_Information": 2, "Rejected": 3}
id2label = {v: k for k, v in label2id.items()}

# Load PubMedBERT
model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=4,
    id2label=id2label,
    label2id=label2id
)

# Tokenization function
def tokenize_function(examples):
    # Combine title and abstract
    texts = [
        f"{title} [SEP] {abstract}" 
        for title, abstract in zip(examples['title'], examples['abstract'])
    ]
    return tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=512
    )

# Tokenize datasets
tokenized_datasets = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset["train"].column_names
)

# Add labels
def add_labels(examples):
    examples['labels'] = [label2id[label] for label in examples['label']]
    return examples

tokenized_datasets = tokenized_datasets.map(add_labels, batched=True)

# Evaluation metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted'
    )
    
    # Per-class metrics
    per_class_metrics = {}
    for label_id, label_name in id2label.items():
        mask = labels == label_id
        if mask.sum() > 0:
            pred_mask = predictions == label_id
            per_class_metrics[f"{label_name}_precision"] = precision_score(
                labels[mask], predictions[mask], average='binary'
            )
            per_class_metrics[f"{label_name}_recall"] = recall_score(
                labels[mask], predictions[mask], average='binary'
            )
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        **per_class_metrics
    }

# Training arguments
training_args = TrainingArguments(
    output_dir="./models/pubmedbert-classifier",
    evaluation_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=100,
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    weight_decay=0.01,
    warmup_steps=500,
    logging_dir='./logs',
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    report_to="wandb",
    save_total_limit=3,
    fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

# Train
print("Starting training...")
trainer.train()

# Evaluate on test set
print("\nEvaluating on test set...")
test_results = trainer.evaluate(tokenized_datasets["test"])
print(test_results)

# Save final model
trainer.save_model("./models/pubmedbert-classifier-final")
tokenizer.save_pretrained("./models/pubmedbert-classifier-final")

print("\n✅ Training complete!")
```

**Run Training:**
```bash
python scripts/train_classifier.py
```

**Expected Training Time:**
- GPU (T4): 2-4 hours
- GPU (V100): 1-2 hours
- CPU: 12-24 hours

---

## 🧪 **STEP 4: Validate Model (1 day)**

### **4.1 Evaluation Script**

```python
# scripts/evaluate_model.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load model
model_path = "./models/pubmedbert-classifier-final"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

# Load test data
test_df = pd.read_csv("data/test.csv")

# Predictions
predictions = []
true_labels = []

for idx, row in test_df.iterrows():
    text = f"{row['title']} [SEP] {row['abstract']}"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred = torch.argmax(logits, dim=-1).item()
    
    predictions.append(id2label[pred])
    true_labels.append(row['label'])

# Metrics
print("\n" + "="*50)
print("CLASSIFICATION REPORT")
print("="*50)
print(classification_report(true_labels, predictions))

# Confusion matrix
cm = confusion_matrix(true_labels, predictions)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=label2id.keys(),
            yticklabels=label2id.keys())
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig('confusion_matrix.png')
print("\n✅ Confusion matrix saved to confusion_matrix.png")

# Error analysis
errors = []
for idx, (true, pred) in enumerate(zip(true_labels, predictions)):
    if true != pred:
        errors.append({
            'article_id': test_df.iloc[idx]['article_id'],
            'title': test_df.iloc[idx]['title'],
            'true_label': true,
            'predicted_label': pred
        })

errors_df = pd.DataFrame(errors)
errors_df.to_csv('classification_errors.csv', index=False)
print(f"\n✅ {len(errors)} errors saved to classification_errors.csv for review")
```

**Action Items:**
- [ ] Review classification report
- [ ] Analyze confusion matrix
- [ ] Review misclassified examples
- [ ] Have domain expert validate edge cases

**Acceptance Criteria:**
- Overall accuracy ≥ 85%
- ICSR precision ≥ 88%
- ICSR recall ≥ 85%
- No systematic bias in errors

---

## 🚀 **STEP 5: Deploy Production Service (2-3 days)**

### **5.1 Update Classification Service**

```python
# services/literature-automation/services/production_classification_service.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List, Optional
import structlog
from pathlib import Path

logger = structlog.get_logger()

class ProductionClassificationService:
    def __init__(self, model_path: str = "./models/pubmedbert-classifier-final"):
        """Initialize production classifier with fine-tuned PubMedBERT"""
        logger.info("Loading production classification model", model_path=model_path)
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model.eval()
            
            # Move to GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            self.labels = ["ICSR", "Non-ICSR", "Safety_Information", "Rejected"]
            
            logger.info("Production model loaded successfully", 
                       device=str(self.device),
                       model_type="PubMedBERT")
                       
        except Exception as e:
            logger.error("Failed to load production model", error=str(e))
            raise
    
    async def classify_article(
        self,
        title: str,
        abstract: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict:
        """Classify article using production model"""
        
        # Prepare text
        text_parts = [title]
        if abstract:
            text_parts.append(abstract)
        elif content:
            # Use first 1000 chars of content if no abstract
            text_parts.append(content[:1000])
        
        text = " [SEP] ".join(text_parts)
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
        
        # Get predictions
        predicted_class_id = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][predicted_class_id].item()
        
        # All class probabilities
        all_probs = {
            label: float(prob)
            for label, prob in zip(self.labels, probs[0].cpu().numpy())
        }
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            self.labels[predicted_class_id],
            confidence,
            all_probs
        )
        
        return {
            "category": self.labels[predicted_class_id],
            "confidence": float(confidence),
            "probabilities": all_probs,
            "reasoning": reasoning,
            "model_version": "pubmedbert-v1.0"
        }
    
    def _generate_reasoning(self, category: str, confidence: float, probs: Dict) -> str:
        """Generate human-readable reasoning"""
        if confidence > 0.9:
            certainty = "High confidence"
        elif confidence > 0.7:
            certainty = "Medium confidence"
        else:
            certainty = "Low confidence"
        
        # Find second highest probability
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        second_class, second_prob = sorted_probs[1]
        
        reasoning = f"{certainty} classification as {category} "
        reasoning += f"(confidence: {confidence:.2%}). "
        
        if second_prob > 0.2:
            reasoning += f"Also shows similarity to {second_class} "
            reasoning += f"({second_prob:.2%}), suggesting mixed characteristics."
        
        return reasoning
```

### **5.2 Update Main Service**

```python
# services/literature-automation/main.py
# Replace old classification_service with new one

from services.production_classification_service import ProductionClassificationService

# Initialize production service
try:
    classification_service = ProductionClassificationService(
        model_path="./models/pubmedbert-classifier-final"
    )
    logger.info("✅ Production classification model loaded")
except Exception as e:
    logger.warning("⚠️ Production model not found, using fallback", error=str(e))
    from services.classification_service import ClassificationService
    classification_service = ClassificationService()
```

---

## 📦 **STEP 6: Docker Integration (1 day)**

### **6.1 Update Dockerfile**

```dockerfile
# services/literature-automation/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download model (during build)
RUN pip install gdown
RUN mkdir -p /app/models

# Copy model from training (or download from cloud storage)
COPY models/pubmedbert-classifier-final /app/models/pubmedbert-classifier-final

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8009

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
```

### **6.2 Update requirements.txt**

```txt
# Add to services/literature-automation/requirements.txt
torch==2.1.0
transformers==4.35.0
accelerate==0.24.0
```

### **6.3 Rebuild and Deploy**

```bash
# Rebuild literature-automation service
docker-compose build --no-cache literature-automation

# Restart service
docker-compose restart literature-automation

# Test
curl -X POST http://localhost:8009/api/v1/literature/classify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Severe anaphylaxis following COVID-19 vaccination",
    "abstract": "A 45-year-old patient developed anaphylaxis 30 minutes after receiving the COVID-19 vaccine..."
  }'
```

---

## 📊 **STEP 7: Monitoring & Maintenance**

### **7.1 Add Model Monitoring**

```python
# services/literature-automation/monitoring/model_monitor.py
class ModelMonitor:
    def __init__(self):
        self.predictions_log = []
        self.confidence_threshold = 0.7
        
    def log_prediction(self, article_id: str, prediction: Dict, text_length: int):
        """Log each prediction for monitoring"""
        self.predictions_log.append({
            "timestamp": datetime.now(),
            "article_id": article_id,
            "prediction": prediction["category"],
            "confidence": prediction["confidence"],
            "text_length": text_length
        })
        
        # Check for low confidence
        if prediction["confidence"] < self.confidence_threshold:
            logger.warning(
                "Low confidence prediction",
                article_id=article_id,
                prediction=prediction["category"],
                confidence=prediction["confidence"]
            )
    
    def get_metrics(self) -> Dict:
        """Get monitoring metrics"""
        if not self.predictions_log:
            return {}
        
        df = pd.DataFrame(self.predictions_log)
        
        return {
            "total_predictions": len(df),
            "average_confidence": df["confidence"].mean(),
            "low_confidence_count": (df["confidence"] < self.confidence_threshold).sum(),
            "predictions_by_class": df["prediction"].value_counts().to_dict()
        }
```

### **7.2 Add Monitoring Endpoint**

```python
@app.get("/api/v1/model/metrics")
async def get_model_metrics():
    """Get model performance metrics"""
    return model_monitor.get_metrics()
```

---

## ✅ **Success Checklist**

- [ ] Training data collected and labeled (1000+ articles)
- [ ] Model trained and validated (accuracy ≥85%)
- [ ] Production service implemented
- [ ] Docker image built and deployed
- [ ] Integration tests passing
- [ ] Monitoring endpoints working
- [ ] Documentation updated
- [ ] Domain expert sign-off

---

## 🎯 **Next Steps After Classification**

Once classification is production-ready:
1. Add Embase/Europe PMC connectors
2. Integrate with Elasticsearch (store classified articles)
3. Integrate with Neo4j (build knowledge graph)
4. Build reviewer interface
5. Add ICSR data extraction (Phase 2)

---

**Ready to start? I can help you with any specific step!**

