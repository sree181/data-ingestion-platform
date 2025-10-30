"""
Simplified RL Controller for Testing
A lightweight version without complex dependencies
"""

import asyncio
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from dataclasses import dataclass

logger = structlog.get_logger(__name__)

@dataclass
class SimpleRLResult:
    """Simplified RL classification result"""
    classification: str
    confidence: float
    reasoning: str
    models_used: List[str]
    rl_decision_path: str
    processing_time: float
    rl_optimization_applied: bool

class SimpleRLController:
    """
    Simplified RL Controller for testing
    """
    
    def __init__(self):
        self.performance_metrics = {
            'accuracy': 0.9,
            'cost_efficiency': 0.6,
            'processing_speed': 1.0,
            'domain_specialization': 0.7
        }
        logger.info("Simple RL Controller initialized")
    
    async def classify_document(self, 
                              title: str,
                              abstract: Optional[str] = None,
                              mesh_terms: Optional[List[str]] = None,
                              publication_types: Optional[List[str]] = None,
                              document_id: Optional[str] = None) -> SimpleRLResult:
        """
        Simplified RL classification
        """
        start_time = datetime.utcnow()
        
        try:
            # Simulate RL analysis
            complexity_score = self._calculate_complexity(title, abstract)
            
            # Simple RL decision logic
            if complexity_score < 0.3:
                # Simple document - use rule-based only
                classification = "Non-ICSR"
                confidence = 0.85
                reasoning = "Simple document, rule-based classification sufficient"
                models_used = ["rule_based"]
                rl_decision_path = "rule_based_only"
            elif complexity_score < 0.7:
                # Medium complexity - use rule + BERT
                classification = "Safety_Information"
                confidence = 0.78
                reasoning = "Medium complexity, rule-based + BERT classification"
                models_used = ["rule_based", "bert"]
                rl_decision_path = "rule_based_and_bert"
            else:
                # Complex document - use full ensemble
                classification = "ICSR"
                confidence = 0.92
                reasoning = "Complex document, full ensemble classification"
                models_used = ["rule_based", "bert", "llm"]
                rl_decision_path = "full_ensemble"
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return SimpleRLResult(
                classification=classification,
                confidence=confidence,
                reasoning=reasoning,
                models_used=models_used,
                rl_decision_path=rl_decision_path,
                processing_time=processing_time,
                rl_optimization_applied=True
            )
            
        except Exception as e:
            logger.error("RL classification failed", error=str(e))
            # Fallback result
            return SimpleRLResult(
                classification="Non-ICSR",
                confidence=0.5,
                reasoning="Fallback classification due to error",
                models_used=["fallback"],
                rl_decision_path="fallback",
                processing_time=0.1,
                rl_optimization_applied=False
            )
    
    def _calculate_complexity(self, title: str, abstract: str) -> float:
        """Calculate document complexity score"""
        score = 0.0
        
        # Title complexity
        if title:
            score += min(len(title.split()) / 20.0, 1.0) * 0.3
        
        # Abstract complexity  
        if abstract:
            score += min(len(abstract.split()) / 200.0, 1.0) * 0.4
        
        # Medical keywords
        text = f"{title} {abstract}".lower()
        medical_keywords = ['adverse', 'reaction', 'toxicity', 'patient', 'drug', 'case']
        keyword_matches = sum(1 for keyword in medical_keywords if keyword in text)
        score += (keyword_matches / len(medical_keywords)) * 0.3
        
        return min(score, 1.0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'accuracy': f"{self.performance_metrics['accuracy']:.4f}",
            'cost_efficiency': f"{self.performance_metrics['cost_efficiency']:.4f}",
            'processing_speed': f"{self.performance_metrics['processing_speed']:.4f}",
            'domain_specialization': f"{self.performance_metrics['domain_specialization']:.4f}",
            'timestamp': datetime.utcnow().isoformat()
        }
