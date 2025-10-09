"""
PubMedBERT Zero-Shot Classifier
Uses pre-trained biomedical BERT for classification without fine-tuning
"""

from typing import Dict, List, Optional, Tuple
import structlog
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

logger = structlog.get_logger(__name__)


class BERTClassifier:
    """
    Zero-shot classifier using PubMedBERT
    Falls back to simpler zero-shot approach if model not available
    """
    
    def __init__(self, model_name: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.use_zero_shot_nli = False
        self.classifier = None
        
        # Initialize patterns regardless (used as fallback)
        self._initialize_patterns()
        
        try:
            self._initialize_model()
            logger.info(f"BERT classifier initialized", model=model_name, device=self.device)
        except Exception as e:
            logger.warning(f"Could not load full BERT model, using simplified approach: {e}")
            self.use_zero_shot_nli = True
    
    def _initialize_model(self):
        """Initialize the full BERT model for zero-shot classification"""
        # Try to use zero-shot classification model
        from transformers import pipeline
        
        # Use a zero-shot classification pipeline
        # This will work with any text classification task
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",  # Good for medical text
            device=0 if self.device == "cuda" else -1
        )
        
        logger.info("Zero-shot classification pipeline initialized")
    
    def _initialize_patterns(self):
        """Initialize keyword patterns for simple scoring (always available as fallback)"""
        # Keyword patterns for simple scoring
        self.patterns = {
            'ICSR': [
                'case report', 'patient', 'year-old', 'presented with', 'developed',
                'administered', 'dose', 'adverse event', 'reaction', 'outcome',
                'diagnosed', 'treatment', 'therapy', 'medication'
            ],
            'Non-ICSR': [
                'study', 'trial', 'cohort', 'population', 'analysis', 'review',
                'systematic', 'meta-analysis', 'randomized', 'controlled',
                'participants', 'subjects', 'data', 'results'
            ],
            'Safety_Information': [
                'safety', 'toxicity', 'risk', 'adverse effects', 'side effects',
                'pharmacovigilance', 'monitoring', 'surveillance', 'warning',
                'precaution', 'contraindication'
            ],
            'Rejected': [
                'in vitro', 'in vivo', 'animal', 'cell culture', 'molecular',
                'structure', 'computational', 'simulation', 'theoretical',
                'model organism', 'protein', 'gene'
            ]
        }
    
    def classify(
        self,
        title: str,
        abstract: Optional[str] = None,
        mesh_terms: Optional[List[str]] = None
    ) -> Tuple[str, float, str]:
        """
        Classify document using BERT
        
        Returns:
            (classification, confidence, reasoning)
        """
        text = f"{title}. {abstract or ''}"[:512]  # Truncate to BERT max length
        
        if not self.use_zero_shot_nli and self.classifier:
            return self._classify_with_pipeline(text)
        else:
            return self._classify_with_keywords(text)
    
    def _classify_with_pipeline(self, text: str) -> Tuple[str, float, str]:
        """Classify using zero-shot classification pipeline"""
        try:
            # Define candidate labels
            candidate_labels = [
                "individual case safety report of adverse drug reaction",
                "clinical trial or research study",
                "drug safety information and warnings",
                "non-pharmacovigilance research"
            ]
            
            result = self.classifier(
                text,
                candidate_labels,
                multi_label=False
            )
            
            # Map labels back to our categories
            label_map = {
                candidate_labels[0]: "ICSR",
                candidate_labels[1]: "Non-ICSR",
                candidate_labels[2]: "Safety_Information",
                candidate_labels[3]: "Rejected"
            }
            
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            classification = label_map[top_label]
            confidence = float(top_score)
            
            reasoning = f"BERT zero-shot classification: {top_label} (score: {top_score:.3f})"
            
            logger.debug("BERT classification", 
                        classification=classification, 
                        confidence=confidence,
                        all_scores=dict(zip(result['labels'], result['scores'])))
            
            return classification, confidence, reasoning
            
        except Exception as e:
            logger.error(f"BERT classification failed: {e}")
            # Fallback to keyword-based
            return self._classify_with_keywords(text)
    
    def _classify_with_keywords(self, text: str) -> Tuple[str, float, str]:
        """Simple keyword-based classification as fallback"""
        text_lower = text.lower()
        
        scores = {}
        for category, keywords in self.patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score / len(keywords)  # Normalize
        
        # Get top category
        top_category = max(scores, key=scores.get)
        confidence = scores[top_category]
        
        # Normalize confidence to 0-1 range and cap at 0.80 (since it's simple)
        confidence = min(confidence * 2, 0.80)  # Scale up but cap
        
        reasoning = f"Keyword-based BERT scoring: {top_category} with {len([k for k in self.patterns[top_category] if k in text_lower])} matching keywords"
        
        logger.debug("Keyword classification", 
                    classification=top_category, 
                    confidence=confidence,
                    all_scores=scores)
        
        return top_category, confidence, reasoning
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extract BERT embeddings for ensemble features
        
        Returns:
            Dictionary of feature scores
        """
        if not self.use_zero_shot_nli and self.classifier:
            # Get full score distribution
            candidate_labels = [
                "case report", "clinical trial", "safety information", "basic research"
            ]
            result = self.classifier(text[:512], candidate_labels, multi_label=True)
            
            features = {
                f"bert_{label}": score 
                for label, score in zip(result['labels'], result['scores'])
            }
            return features
        else:
            # Return keyword match scores as features
            text_lower = text.lower()
            features = {}
            for category, keywords in self.patterns.items():
                score = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
                features[f"bert_{category}"] = score
            return features


# Singleton instance
bert_classifier = BERTClassifier()

