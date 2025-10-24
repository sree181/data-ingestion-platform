"""
Ensemble Strategy
Combine predictions from multiple models with weighted voting and confidence-based selection
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class Prediction:
    """Individual model prediction"""
    model_name: str
    classification: str
    confidence: float
    reasoning: str
    processing_time_ms: int
    cost_estimate: float
    timestamp: datetime

@dataclass
class EnsembleResult:
    """Ensemble prediction result"""
    classification: str
    confidence: float
    reasoning: str
    models_used: List[str]
    decision_path: str
    individual_predictions: List[Prediction]
    ensemble_metadata: Dict[str, Any]

class EnsembleStrategy:
    """
    Combine predictions from multiple models
    - Weighted voting
    - Confidence-based selection
    - Cascade strategy (rule -> BERT -> LLM)
    - Dynamic threshold adjustment
    """
    
    def __init__(
        self,
        default_weights: Optional[Dict[str, float]] = None,
        confidence_thresholds: Optional[Dict[str, float]] = None,
        cascade_enabled: bool = True,
        weighted_voting: bool = True
    ):
        """
        Initialize ensemble strategy
        
        Args:
            default_weights: Default model weights
            confidence_thresholds: Confidence thresholds for each model
            cascade_enabled: Whether to use cascade strategy
            weighted_voting: Whether to use weighted voting
        """
        self.default_weights = default_weights or {
            'rule_based': 0.3,
            'bert': 0.4,
            'llm': 0.3
        }
        
        self.confidence_thresholds = confidence_thresholds or {
            'rule_based': 0.8,
            'bert': 0.7,
            'llm': 0.6
        }
        
        self.cascade_enabled = cascade_enabled
        self.weighted_voting = weighted_voting
        
        # Cascade order (rule-based -> BERT -> LLM)
        self.cascade_order = ['rule_based', 'bert', 'llm']
        
        logger.info("EnsembleStrategy initialized",
                   cascade_enabled=cascade_enabled,
                   weighted_voting=weighted_voting)
    
    def combine_predictions(
        self, 
        predictions: List[Dict[str, Any]], 
        action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Combine predictions from multiple models
        
        Args:
            predictions: List of model predictions
            action: RL action for dynamic strategy adjustment
            
        Returns:
            Combined ensemble result
        """
        if not predictions:
            return self._create_fallback_result()
        
        # Convert predictions to Prediction objects
        prediction_objects = self._convert_predictions(predictions)
        
        # Apply dynamic strategy based on action
        strategy_config = self._get_strategy_config(action)
        
        # Choose combination method
        if strategy_config.get('use_cascade', self.cascade_enabled):
            result = self._cascade_strategy(prediction_objects, strategy_config)
        elif strategy_config.get('use_weighted_voting', self.weighted_voting):
            result = self._weighted_voting_strategy(prediction_objects, strategy_config)
        else:
            result = self._confidence_based_strategy(prediction_objects, strategy_config)
        
        return result
    
    def _convert_predictions(self, predictions: List[Dict[str, Any]]) -> List[Prediction]:
        """Convert prediction dictionaries to Prediction objects"""
        prediction_objects = []
        
        for pred in predictions:
            try:
                prediction_obj = Prediction(
                    model_name=pred.get('model_name', 'unknown'),
                    classification=pred.get('classification', 'Unknown'),
                    confidence=pred.get('confidence', 0.0),
                    reasoning=pred.get('reasoning', ''),
                    processing_time_ms=pred.get('processing_time_ms', 0),
                    cost_estimate=pred.get('cost_estimate', 0.0),
                    timestamp=datetime.utcnow()
                )
                prediction_objects.append(prediction_obj)
            except Exception as e:
                logger.warning(f"Failed to convert prediction: {e}")
                continue
        
        return prediction_objects
    
    def _get_strategy_config(self, action: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get strategy configuration based on RL action"""
        config = {
            'use_cascade': self.cascade_enabled,
            'use_weighted_voting': self.weighted_voting,
            'weights': self.default_weights.copy(),
            'confidence_thresholds': self.confidence_thresholds.copy(),
            'cost_budget': float('inf'),
            'time_budget_ms': float('inf')
        }
        
        if not action:
            return config
        
        # Apply action-based adjustments
        if 'model_weights' in action:
            config['weights'].update(action['model_weights'])
        
        if 'confidence_thresholds' in action:
            config['confidence_thresholds'].update(action['confidence_thresholds'])
        
        if 'cost_budget' in action:
            config['cost_budget'] = action['cost_budget']
        
        if 'time_budget_ms' in action:
            config['time_budget_ms'] = action['time_budget_ms']
        
        return config
    
    def _cascade_strategy(
        self, 
        predictions: List[Prediction], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cascade strategy: use models in order until confidence threshold is met"""
        used_models = []
        decision_path = []
        
        for model_name in self.cascade_order:
            # Find prediction from this model
            model_prediction = next(
                (p for p in predictions if p.model_name == model_name), 
                None
            )
            
            if not model_prediction:
                continue
            
            used_models.append(model_name)
            decision_path.append(f"{model_name}:{model_prediction.classification}")
            
            # Check if confidence meets threshold
            threshold = config['confidence_thresholds'].get(model_name, 0.7)
            if model_prediction.confidence >= threshold:
                # High confidence prediction, use it
                return {
                    'classification': model_prediction.classification,
                    'confidence': model_prediction.confidence,
                    'reasoning': f"Cascade: {model_prediction.reasoning}",
                    'models_used': used_models,
                    'decision_path': " -> ".join(decision_path),
                    'individual_predictions': [model_prediction],
                    'ensemble_metadata': {
                        'strategy': 'cascade',
                        'stopped_at': model_name,
                        'threshold_met': True
                    }
                }
        
        # If no model met threshold, use weighted voting of all predictions
        return self._weighted_voting_strategy(predictions, config)
    
    def _weighted_voting_strategy(
        self, 
        predictions: List[Prediction], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Weighted voting strategy: combine predictions with weights"""
        if not predictions:
            return self._create_fallback_result()
        
        # Calculate weighted scores for each classification
        classification_scores = {}
        total_weight = 0.0
        
        for prediction in predictions:
            model_name = prediction.model_name
            weight = config['weights'].get(model_name, 0.1)
            classification = prediction.classification
            confidence = prediction.confidence
            
            if classification not in classification_scores:
                classification_scores[classification] = 0.0
            
            classification_scores[classification] += weight * confidence
            total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            for classification in classification_scores:
                classification_scores[classification] /= total_weight
        
        # Find best classification
        best_classification = max(classification_scores, key=classification_scores.get)
        best_confidence = classification_scores[best_classification]
        
        # Create reasoning
        reasoning_parts = []
        for prediction in predictions:
            reasoning_parts.append(f"{prediction.model_name}: {prediction.classification} ({prediction.confidence:.2f})")
        
        reasoning = f"Weighted voting: {'; '.join(reasoning_parts)}"
        
        return {
            'classification': best_classification,
            'confidence': best_confidence,
            'reasoning': reasoning,
            'models_used': [p.model_name for p in predictions],
            'decision_path': f"weighted_voting({len(predictions)}_models)",
            'individual_predictions': predictions,
            'ensemble_metadata': {
                'strategy': 'weighted_voting',
                'classification_scores': classification_scores,
                'total_weight': total_weight
            }
        }
    
    def _confidence_based_strategy(
        self, 
        predictions: List[Prediction], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Confidence-based strategy: use highest confidence prediction"""
        if not predictions:
            return self._create_fallback_result()
        
        # Find prediction with highest confidence
        best_prediction = max(predictions, key=lambda p: p.confidence)
        
        return {
            'classification': best_prediction.classification,
            'confidence': best_prediction.confidence,
            'reasoning': f"Highest confidence: {best_prediction.reasoning}",
            'models_used': [best_prediction.model_name],
            'decision_path': f"confidence_based({best_prediction.model_name})",
            'individual_predictions': [best_prediction],
            'ensemble_metadata': {
                'strategy': 'confidence_based',
                'selected_model': best_prediction.model_name,
                'all_confidences': {p.model_name: p.confidence for p in predictions}
            }
        }
    
    def _create_fallback_result(self) -> Dict[str, Any]:
        """Create fallback result when no predictions available"""
        return {
            'classification': 'Unknown',
            'confidence': 0.0,
            'reasoning': 'No model predictions available',
            'models_used': [],
            'decision_path': 'fallback',
            'individual_predictions': [],
            'ensemble_metadata': {
                'strategy': 'fallback',
                'error': 'No predictions available'
            }
        }
    
    def get_strategy_metrics(self, predictions: List[Prediction]) -> Dict[str, Any]:
        """Get metrics about the ensemble strategy"""
        if not predictions:
            return {'error': 'No predictions available'}
        
        # Calculate agreement metrics
        classifications = [p.classification for p in predictions]
        unique_classifications = set(classifications)
        agreement_ratio = 1.0 - (len(unique_classifications) - 1) / len(predictions)
        
        # Calculate confidence statistics
        confidences = [p.confidence for p in predictions]
        avg_confidence = np.mean(confidences)
        max_confidence = np.max(confidences)
        min_confidence = np.min(confidences)
        confidence_std = np.std(confidences)
        
        # Calculate cost and time metrics
        total_cost = sum(p.cost_estimate for p in predictions)
        total_time = sum(p.processing_time_ms for p in predictions)
        avg_time = total_time / len(predictions)
        
        return {
            'agreement_ratio': agreement_ratio,
            'unique_classifications': len(unique_classifications),
            'avg_confidence': avg_confidence,
            'max_confidence': max_confidence,
            'min_confidence': min_confidence,
            'confidence_std': confidence_std,
            'total_cost': total_cost,
            'total_time_ms': total_time,
            'avg_time_ms': avg_time,
            'num_predictions': len(predictions)
        }
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update model weights"""
        self.default_weights.update(new_weights)
        logger.info("Model weights updated", weights=self.default_weights)
    
    def update_confidence_thresholds(self, new_thresholds: Dict[str, float]):
        """Update confidence thresholds"""
        self.confidence_thresholds.update(new_thresholds)
        logger.info("Confidence thresholds updated", thresholds=self.confidence_thresholds)
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current strategy configuration"""
        return {
            'weights': self.default_weights.copy(),
            'confidence_thresholds': self.confidence_thresholds.copy(),
            'cascade_enabled': self.cascade_enabled,
            'weighted_voting': self.weighted_voting,
            'cascade_order': self.cascade_order.copy()
        }
