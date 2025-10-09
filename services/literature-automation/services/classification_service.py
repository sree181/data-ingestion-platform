"""
Classification Service
AI-powered classification of literature articles for ICSR identification
"""

import asyncio
from typing import Dict, Any, Optional
import structlog
from transformers import pipeline
import torch

from models.literature_models import (
    ArticleClassification,
    ClassificationResult
)

logger = structlog.get_logger()

class ClassificationService:
    def __init__(self):
        self.classifier = None
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Initialize the classification model"""
        try:
            # Use a pre-trained model for text classification
            # In production, this would be a fine-tuned medical model
            self.classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",  # Placeholder - replace with medical model
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Classification model initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize classification model", error=str(e))
            self.classifier = None
    
    async def classify_article(
        self, 
        title: str, 
        abstract: Optional[str] = None, 
        content: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify article using AI
        Categories: ICSR, Non-ICSR, Safety Information, Rejected
        """
        logger.info("Starting article classification", title=title[:100])
        
        try:
            # Prepare text for classification
            text_for_classification = self._prepare_text_for_classification(title, abstract, content)
            
            # Use AI classification
            if self.classifier:
                classification_result = await self._ai_classify(text_for_classification)
            else:
                # Fallback to rule-based classification
                classification_result = await self._rule_based_classify(text_for_classification)
            
            logger.info("Article classification completed", 
                       classification=classification_result.category,
                       confidence=classification_result.confidence)
            
            return classification_result
            
        except Exception as e:
            logger.error("Article classification failed", error=str(e))
            # Return default classification on error
            return ClassificationResult(
                category=ArticleClassification.REJECTED,
                confidence=0.0,
                reasoning="Classification failed due to error",
                supporting_evidence=[]
            )
    
    def _prepare_text_for_classification(self, title: str, abstract: Optional[str], content: Optional[str]) -> str:
        """Prepare text for classification by combining available content"""
        text_parts = []
        
        if title:
            text_parts.append(f"Title: {title}")
        
        if abstract:
            text_parts.append(f"Abstract: {abstract}")
        
        if content and len(content) > 1000:  # Use first 1000 chars if content is too long
            text_parts.append(f"Content: {content[:1000]}...")
        elif content:
            text_parts.append(f"Content: {content}")
        
        return "\n\n".join(text_parts)
    
    async def _ai_classify(self, text: str) -> ClassificationResult:
        """Use AI model for classification"""
        try:
            # This is a placeholder implementation
            # In production, you would use a fine-tuned medical classification model
            
            # For now, use rule-based classification as fallback
            return await self._rule_based_classify(text)
            
        except Exception as e:
            logger.error("AI classification failed", error=str(e))
            return await self._rule_based_classify(text)
    
    async def _rule_based_classify(self, text: str) -> ClassificationResult:
        """Rule-based classification as fallback"""
        text_lower = text.lower()
        
        # Keywords for ICSR identification
        icsr_keywords = [
            'adverse event', 'adverse reaction', 'side effect', 'adverse drug reaction',
            'adr', 'ae', 'toxicity', 'overdose', 'allergic reaction', 'hypersensitivity',
            'death', 'fatal', 'serious adverse event', 'sae', 'hospitalization',
            'disability', 'life-threatening', 'congenital anomaly', 'birth defect'
        ]
        
        # Keywords for safety information
        safety_keywords = [
            'safety', 'tolerability', 'pharmacovigilance', 'post-marketing',
            'real-world evidence', 'observational study', 'cohort study',
            'case series', 'case report', 'clinical trial', 'phase i', 'phase ii',
            'phase iii', 'phase iv', 'post-authorization'
        ]
        
        # Keywords for rejection
        rejection_keywords = [
            'review', 'meta-analysis', 'systematic review', 'editorial',
            'commentary', 'opinion', 'guideline', 'protocol', 'methodology',
            'in vitro', 'animal study', 'preclinical', 'pharmacokinetic',
            'pharmacodynamic', 'drug interaction', 'formulation'
        ]
        
        # Count keyword matches
        icsr_score = sum(1 for keyword in icsr_keywords if keyword in text_lower)
        safety_score = sum(1 for keyword in safety_keywords if keyword in text_lower)
        rejection_score = sum(1 for keyword in rejection_keywords if keyword in text_lower)
        
        # Determine classification based on scores
        if icsr_score >= 3:
            category = ArticleClassification.ICSR
            confidence = min(0.9, 0.5 + (icsr_score * 0.1))
            reasoning = f"High ICSR keyword match ({icsr_score} matches): adverse events, reactions, or safety concerns identified"
            evidence = [kw for kw in icsr_keywords if kw in text_lower]
        elif safety_score >= 2:
            category = ArticleClassification.SAFETY_INFORMATION
            confidence = min(0.8, 0.4 + (safety_score * 0.1))
            reasoning = f"Safety information identified ({safety_score} matches): clinical studies or safety data"
            evidence = [kw for kw in safety_keywords if kw in text_lower]
        elif rejection_score >= 2:
            category = ArticleClassification.REJECTED
            confidence = min(0.7, 0.3 + (rejection_score * 0.1))
            reasoning = f"Non-ICSR content identified ({rejection_score} matches): reviews, methodologies, or non-clinical studies"
            evidence = [kw for kw in rejection_keywords if kw in text_lower]
        else:
            category = ArticleClassification.NON_ICSR
            confidence = 0.5
            reasoning = "No clear ICSR indicators found, classified as general medical literature"
            evidence = []
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=evidence
        )
