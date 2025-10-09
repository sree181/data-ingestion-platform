"""
Ensemble Classifier
Combines rule-based, BERT, and LLM classifiers with intelligent voting
"""

from typing import Dict, List, Optional, Tuple
import structlog
from datetime import datetime
import statistics

from rule_based_classifier import rule_based_classifier
from bert_classifier import bert_classifier

logger = structlog.get_logger(__name__)


class EnsembleClassifier:
    """
    Ensemble classifier that combines multiple models with weighted voting
    
    Strategy:
    1. Try rule-based first (fastest, cheapest)
    2. If low confidence, add BERT (medium speed/cost)
    3. If still low confidence, add LLM (slowest, most expensive)
    4. Aggregate results with weighted voting
    """
    
    # Model weights for voting (can be tuned based on validation performance)
    MODEL_WEIGHTS = {
        'rule_based': 0.25,
        'bert': 0.35,
        'llm': 0.40
    }
    
    # Confidence thresholds for triggering next model
    CONFIDENCE_THRESHOLDS = {
        'rule_based': 0.85,  # If rule-based confidence < 0.85, use BERT
        'bert': 0.75,        # If BERT confidence < 0.75, use LLM
    }
    
    def __init__(self, llm_classifier=None):
        """
        Initialize ensemble classifier
        
        Args:
            llm_classifier: LLM classifier instance (injected to avoid circular imports)
        """
        self.llm_classifier = llm_classifier
        logger.info("Ensemble classifier initialized")
    
    async def classify(
        self,
        title: str,
        abstract: Optional[str] = None,
        mesh_terms: Optional[List[str]] = None,
        publication_types: Optional[List[str]] = None,
        force_ensemble: bool = False
    ) -> Dict:
        """
        Classify document using ensemble approach
        
        Args:
            title: Document title
            abstract: Document abstract
            mesh_terms: MeSH terms
            publication_types: Publication types
            force_ensemble: If True, always use all models (for comparison)
            
        Returns:
            Dictionary with classification results and metadata
        """
        start_time = datetime.utcnow()
        
        results = {
            'models_used': [],
            'individual_results': {},
            'ensemble_result': None,
            'confidence': 0.0,
            'reasoning': '',
            'processing_time_ms': 0,
            'cost_estimate': 0.0
        }
        
        # Step 1: Rule-based classification (always run, it's fast and free)
        logger.info("Running rule-based classifier")
        rule_class, rule_conf, rule_reason, rule_evidence = rule_based_classifier.classify(
            title, abstract, mesh_terms, publication_types
        )
        
        results['models_used'].append('rule_based')
        results['individual_results']['rule_based'] = {
            'classification': rule_class,
            'confidence': rule_conf,
            'reasoning': rule_reason,
            'evidence': rule_evidence
        }
        
        # Check if rule-based is confident enough
        if not force_ensemble and rule_conf >= self.CONFIDENCE_THRESHOLDS['rule_based']:
            # High confidence from rules, use this result
            results['ensemble_result'] = rule_class
            results['confidence'] = rule_conf
            results['reasoning'] = f"High-confidence rule-based classification: {rule_reason}"
            results['decision_path'] = 'rule_based_only'
            
            logger.info("Using rule-based result", 
                       classification=rule_class, 
                       confidence=rule_conf,
                       reason="High confidence from rules")
        else:
            # Step 2: BERT classification (medium cost)
            logger.info("Running BERT classifier")
            bert_class, bert_conf, bert_reason = bert_classifier.classify(
                title, abstract, mesh_terms
            )
            
            results['models_used'].append('bert')
            results['individual_results']['bert'] = {
                'classification': bert_class,
                'confidence': bert_conf,
                'reasoning': bert_reason
            }
            
            # Check if we have enough confidence from rule + BERT
            if not force_ensemble and bert_conf >= self.CONFIDENCE_THRESHOLDS['bert']:
                # Use weighted vote of rule-based + BERT
                ensemble_result = self._vote_two_models(
                    (rule_class, rule_conf),
                    (bert_class, bert_conf)
                )
                
                results['ensemble_result'] = ensemble_result['classification']
                results['confidence'] = ensemble_result['confidence']
                results['reasoning'] = ensemble_result['reasoning']
                results['decision_path'] = 'rule_based_and_bert'
                
                logger.info("Using rule-based + BERT result", 
                           classification=ensemble_result['classification'],
                           confidence=ensemble_result['confidence'])
            else:
                # Step 3: LLM classification (highest cost, best accuracy)
                if self.llm_classifier:
                    logger.info("Running LLM classifier")
                    llm_result = await self.llm_classifier.classify_document_llm_only(
                        title, abstract, mesh_terms, publication_types
                    )
                    
                    results['models_used'].append('llm')
                    results['individual_results']['llm'] = {
                        'classification': llm_result.classification,
                        'confidence': llm_result.confidence,
                        'reasoning': llm_result.reasoning,
                        'key_entities': [e.dict() for e in llm_result.key_entities]
                    }
                    results['cost_estimate'] += 0.005  # ~$0.005 per LLM call
                    
                    # Full ensemble vote (all three models)
                    ensemble_result = self._vote_three_models(
                        (rule_class, rule_conf),
                        (bert_class, bert_conf),
                        (llm_result.classification, llm_result.confidence)
                    )
                    
                    results['ensemble_result'] = ensemble_result['classification']
                    results['confidence'] = ensemble_result['confidence']
                    results['reasoning'] = ensemble_result['reasoning']
                    results['decision_path'] = 'full_ensemble'
                    
                    logger.info("Using full ensemble result",
                               classification=ensemble_result['classification'],
                               confidence=ensemble_result['confidence'])
                else:
                    # No LLM available, use rule + BERT
                    ensemble_result = self._vote_two_models(
                        (rule_class, rule_conf),
                        (bert_class, bert_conf)
                    )
                    
                    results['ensemble_result'] = ensemble_result['classification']
                    results['confidence'] = ensemble_result['confidence']
                    results['reasoning'] = f"No LLM available. {ensemble_result['reasoning']}"
                    results['decision_path'] = 'rule_based_and_bert'
        
        # Calculate processing time
        end_time = datetime.utcnow()
        results['processing_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info("Ensemble classification complete",
                   classification=results['ensemble_result'],
                   confidence=results['confidence'],
                   models_used=results['models_used'],
                   processing_time_ms=results['processing_time_ms'])
        
        return results
    
    def _vote_two_models(
        self,
        model1: Tuple[str, float],
        model2: Tuple[str, float]
    ) -> Dict:
        """
        Vote between two models (rule-based + BERT)
        
        Args:
            model1: (classification, confidence) tuple
            model2: (classification, confidence) tuple
            
        Returns:
            Ensemble result dictionary
        """
        class1, conf1 = model1
        class2, conf2 = model2
        
        # If both agree, high confidence
        if class1 == class2:
            avg_confidence = (conf1 + conf2) / 2
            return {
                'classification': class1,
                'confidence': min(avg_confidence * 1.1, 0.98),  # Boost for agreement, cap at 0.98
                'reasoning': f"Both rule-based and BERT agree on {class1} (avg confidence: {avg_confidence:.2f})"
            }
        
        # If they disagree, use weighted voting
        weights = {
            'model1': self.MODEL_WEIGHTS['rule_based'],
            'model2': self.MODEL_WEIGHTS['bert']
        }
        
        # Normalize weights
        total_weight = weights['model1'] + weights['model2']
        weights['model1'] /= total_weight
        weights['model2'] /= total_weight
        
        # Calculate weighted scores
        score1 = conf1 * weights['model1']
        score2 = conf2 * weights['model2']
        
        if score1 > score2:
            return {
                'classification': class1,
                'confidence': min(score1 / weights['model1'] * 0.85, 0.90),  # Penalize disagreement
                'reasoning': f"Rule-based prediction {class1} (weighted score: {score1:.2f}) beats BERT {class2} (score: {score2:.2f})"
            }
        else:
            return {
                'classification': class2,
                'confidence': min(score2 / weights['model2'] * 0.85, 0.90),
                'reasoning': f"BERT prediction {class2} (weighted score: {score2:.2f}) beats rule-based {class1} (score: {score1:.2f})"
            }
    
    def _vote_three_models(
        self,
        model1: Tuple[str, float],
        model2: Tuple[str, float],
        model3: Tuple[str, float]
    ) -> Dict:
        """
        Vote between three models (rule-based + BERT + LLM)
        
        Args:
            model1: (classification, confidence) tuple for rule-based
            model2: (classification, confidence) tuple for BERT
            model3: (classification, confidence) tuple for LLM
            
        Returns:
            Ensemble result dictionary
        """
        class1, conf1 = model1
        class2, conf2 = model2
        class3, conf3 = model3
        
        # Count votes for each class
        votes = {}
        for cls, conf in [(class1, conf1), (class2, conf2), (class3, conf3)]:
            if cls not in votes:
                votes[cls] = {'count': 0, 'total_conf': 0.0}
            votes[cls]['count'] += 1
            votes[cls]['total_conf'] += conf
        
        # If all three agree, very high confidence
        if len(votes) == 1:
            unanimous_class = list(votes.keys())[0]
            avg_confidence = (conf1 + conf2 + conf3) / 3
            return {
                'classification': unanimous_class,
                'confidence': min(avg_confidence * 1.15, 0.99),  # Boost for unanimous agreement
                'reasoning': f"Unanimous agreement: all three models classify as {unanimous_class} (avg confidence: {avg_confidence:.2f})"
            }
        
        # If two agree, use majority vote with boosted confidence
        max_votes = max(v['count'] for v in votes.values())
        if max_votes == 2:
            majority_class = [cls for cls, v in votes.items() if v['count'] == 2][0]
            avg_confidence = votes[majority_class]['total_conf'] / 2
            return {
                'classification': majority_class,
                'confidence': min(avg_confidence * 1.05, 0.95),  # Small boost for majority
                'reasoning': f"Majority vote (2/3): {majority_class} with avg confidence {avg_confidence:.2f}"
            }
        
        # All three disagree - use weighted voting
        weights = self.MODEL_WEIGHTS
        weighted_scores = {
            class1: conf1 * weights['rule_based'],
            class2: conf2 * weights['bert'],
            class3: conf3 * weights['llm']
        }
        
        # Get highest weighted score
        best_class = max(weighted_scores, key=weighted_scores.get)
        best_score = weighted_scores[best_class]
        
        # Calculate confidence (penalize for full disagreement)
        original_conf = {class1: conf1, class2: conf2, class3: conf3}
        final_confidence = min(original_conf[best_class] * 0.80, 0.85)  # Penalty for disagreement
        
        return {
            'classification': best_class,
            'confidence': final_confidence,
            'reasoning': f"Three-way disagreement resolved by weighted voting: {best_class} (weighted score: {best_score:.3f}, models: rule={class1}, bert={class2}, llm={class3})"
        }
    
    def get_feature_importance(self, results: Dict) -> Dict[str, float]:
        """
        Calculate feature importance for explainability
        
        Args:
            results: Ensemble classification results
            
        Returns:
            Dictionary of feature importance scores
        """
        importance = {}
        
        # Model contribution
        for model_name in results['models_used']:
            weight = self.MODEL_WEIGHTS.get(model_name, 0.0)
            importance[f"{model_name}_contribution"] = weight
        
        # Confidence contribution
        for model_name, model_result in results['individual_results'].items():
            importance[f"{model_name}_confidence"] = model_result['confidence']
        
        # Agreement metrics
        if len(results['individual_results']) >= 2:
            classifications = [r['classification'] for r in results['individual_results'].values()]
            agreement_rate = len(set(classifications)) / len(classifications)
            importance['model_agreement'] = 1.0 - agreement_rate  # Higher = more agreement
        
        return importance


# Singleton instance will be created after LLM classifier is initialized
ensemble_classifier = None


def initialize_ensemble(llm_classifier):
    """Initialize ensemble classifier with LLM classifier instance"""
    global ensemble_classifier
    ensemble_classifier = EnsembleClassifier(llm_classifier)
    logger.info("Ensemble classifier initialized with LLM")
    return ensemble_classifier

