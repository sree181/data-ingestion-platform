"""
RL-Enhanced Ensemble Controller
Controls entire classification pipeline using RL optimization
"""

import asyncio
import structlog
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
import torch
import json
from dataclasses import dataclass
from pathlib import Path
import sys

# Add RL optimization path
sys.path.append('/Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion/rl_optimization')

from rl_training.rl_agent import MultiObjectiveRLAgent, RLState, RLAction, RLReward
from rl_training.ip_enhanced_rl_agent import IPEnhancedRLAgent
from rl_training.training_engine import RLTrainingEngine
from monitoring.training_monitor import TrainingMonitor
from optimization.optimization_integration import create_optimization_integration
from security.security_manager import create_security_manager

logger = structlog.get_logger(__name__)

@dataclass
class RLClassificationResult:
    """RL-enhanced classification result"""
    classification: str
    confidence: float
    reasoning: str
    models_used: List[str]
    rl_decision_path: str
    performance_metrics: Dict[str, float]
    cost_estimate: float
    processing_time: float
    rl_optimization_applied: bool
    key_entities: List[Dict] = None

@dataclass
class RLPerformanceMetrics:
    """Real-time performance metrics"""
    accuracy: float
    cost_efficiency: float
    processing_speed: float
    domain_specialization: float
    total_reward: float
    timestamp: datetime
    document_count: int
    rl_episodes_completed: int

class RLEnsembleController:
    """
    RL-Enhanced Ensemble Controller
    Controls entire classification pipeline using RL optimization
    """
    
    def __init__(self, 
                 rl_model_path: str = "rl_optimization/training_results/final_model.pt",
                 enable_monitoring: bool = True,
                 enable_optimization: bool = True,
                 enable_security: bool = True):
        
        self.rl_model_path = rl_model_path
        self.enable_monitoring = enable_monitoring
        self.enable_optimization = enable_optimization
        self.enable_security = enable_security
        
        # Initialize RL Agent
        self.rl_agent = self._load_rl_agent()
        
        # Initialize monitoring
        self.monitor = self._initialize_monitoring()
        
        # Initialize optimization
        self.optimization = self._initialize_optimization()
        
        # Initialize security
        self.security_manager = self._initialize_security()
        
        # Performance tracking
        self.performance_metrics = RLPerformanceMetrics(
            accuracy=0.0,
            cost_efficiency=0.0,
            processing_speed=0.0,
            domain_specialization=0.0,
            total_reward=0.0,
            timestamp=datetime.utcnow(),
            document_count=0,
            rl_episodes_completed=0
        )
        
        # Real-time metrics storage
        self.real_time_metrics = []
        self.classification_history = []
        
        logger.info("RL Ensemble Controller initialized", 
                   model_path=rl_model_path,
                   monitoring=enable_monitoring,
                   optimization=enable_optimization,
                   security=enable_security)
    
    def _load_rl_agent(self) -> IPEnhancedRLAgent:
        """Load trained RL agent"""
        try:
            # Load the trained RL agent
            agent = IPEnhancedRLAgent()
            
            # Load trained weights if available
            if Path(self.rl_model_path).exists():
                checkpoint = torch.load(self.rl_model_path, map_location='cpu')
                agent.load_state_dict(checkpoint.get('model_state_dict', {}))
                logger.info("RL agent loaded from checkpoint", path=self.rl_model_path)
            else:
                logger.warning("RL model not found, using default weights", path=self.rl_model_path)
            
            return agent
            
        except Exception as e:
            logger.error("Failed to load RL agent", error=str(e))
            # Fallback to basic RL agent
            return MultiObjectiveRLAgent()
    
    def _initialize_monitoring(self) -> Optional[TrainingMonitor]:
        """Initialize monitoring system"""
        if not self.enable_monitoring:
            return None
            
        try:
            from monitoring.training_monitor import create_training_monitor
            return create_training_monitor(
                enable_monitoring=True,
                output_dir="rl_optimization/monitoring_output"
            )
        except Exception as e:
            logger.warning("Failed to initialize monitoring", error=str(e))
            return None
    
    def _initialize_optimization(self) -> Optional[Any]:
        """Initialize optimization system"""
        if not self.enable_optimization:
            return None
            
        try:
            return create_optimization_integration(
                enable_caching=True,
                enable_performance_optimization=True,
                enable_model_optimization=True,
                cache_size_mb=500
            )
        except Exception as e:
            logger.warning("Failed to initialize optimization", error=str(e))
            return None
    
    def _initialize_security(self) -> Optional[Any]:
        """Initialize security system"""
        if not self.enable_security:
            return None
            
        try:
            return create_security_manager(
                enable_encryption=True,
                enable_authentication=True,
                enable_authorization=True,
                enable_audit_logging=True,
                enable_compliance=True
            )
        except Exception as e:
            logger.warning("Failed to initialize security", error=str(e))
            return None
    
    async def classify_document(self, 
                              title: str,
                              abstract: Optional[str] = None,
                              mesh_terms: Optional[List[str]] = None,
                              publication_types: Optional[List[str]] = None,
                              document_id: Optional[str] = None) -> RLClassificationResult:
        """
        Classify document using RL-controlled ensemble
        
        Args:
            title: Document title
            abstract: Document abstract
            mesh_terms: MeSH terms
            publication_types: Publication types
            document_id: Optional document ID
            
        Returns:
            RLClassificationResult with classification and metrics
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Extract features for RL analysis
            features = self._extract_document_features(title, abstract, mesh_terms, publication_types)
            
            # Step 2: Create RL state
            rl_state = self._create_rl_state(features)
            
            # Step 3: RL Agent decision making
            rl_action = self.rl_agent.select_action(rl_state)
            
            # Step 4: Apply RL-optimized classification
            classification_result = await self._execute_rl_classification(
                title, abstract, mesh_terms, publication_types, rl_action
            )
            
            # Step 5: Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                classification_result, rl_action, start_time
            )
            
            # Step 6: Update RL agent with feedback
            self._update_rl_agent(rl_state, rl_action, performance_metrics)
            
            # Step 7: Update real-time metrics
            self._update_real_time_metrics(performance_metrics)
            
            # Step 8: Record in monitoring system
            if self.monitor:
                self._record_classification_event(classification_result, performance_metrics)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RLClassificationResult(
                classification=classification_result['classification'],
                confidence=classification_result['confidence'],
                reasoning=classification_result['reasoning'],
                models_used=classification_result['models_used'],
                rl_decision_path=rl_action.model_selection,
                performance_metrics=performance_metrics,
                cost_estimate=classification_result.get('cost_estimate', 0.0),
                processing_time=processing_time,
                rl_optimization_applied=True,
                key_entities=classification_result.get('key_entities', [])
            )
            
        except Exception as e:
            logger.error("RL classification failed", error=str(e), document_id=document_id)
            # Fallback to basic classification
            return await self._fallback_classification(title, abstract, mesh_terms, publication_types)
    
    def _extract_document_features(self, title: str, abstract: str, 
                                 mesh_terms: List[str], publication_types: List[str]) -> Dict[str, Any]:
        """Extract features for RL analysis"""
        features = {
            'title_length': len(title) if title else 0,
            'abstract_length': len(abstract) if abstract else 0,
            'mesh_count': len(mesh_terms) if mesh_terms else 0,
            'publication_type_count': len(publication_types) if publication_types else 0,
            'complexity_score': self._calculate_complexity_score(title, abstract, mesh_terms),
            'domain_specialization': self._calculate_domain_specialization(mesh_terms),
            'temporal_indicators': self._extract_temporal_indicators(title, abstract),
            'adverse_event_indicators': self._extract_adverse_event_indicators(title, abstract),
            'patient_indicators': self._extract_patient_indicators(title, abstract),
            'drug_indicators': self._extract_drug_indicators(title, abstract)
        }
        
        return features
    
    def _create_rl_state(self, features: Dict[str, Any]) -> RLState:
        """Create RL state from document features"""
        # Convert features to RL state format
        state_vector = np.array([
            features['complexity_score'],
            features['domain_specialization'],
            features['title_length'] / 1000.0,  # Normalize
            features['abstract_length'] / 10000.0,  # Normalize
            features['mesh_count'] / 20.0,  # Normalize
            features['temporal_indicators'],
            features['adverse_event_indicators'],
            features['patient_indicators'],
            features['drug_indicators'],
            self.performance_metrics.accuracy,
            self.performance_metrics.cost_efficiency,
            self.performance_metrics.processing_speed,
            self.performance_metrics.domain_specialization,
            self.performance_metrics.total_reward,
            len(self.classification_history) / 1000.0  # Normalize history length
        ])
        
        return RLState(
            document_features=state_vector,
            current_performance=self.performance_metrics.__dict__,
            context={'timestamp': datetime.utcnow().isoformat()}
        )
    
    async def _execute_rl_classification(self, title: str, abstract: str, 
                                       mesh_terms: List[str], publication_types: List[str],
                                       rl_action: RLAction) -> Dict[str, Any]:
        """Execute classification using RL-optimized parameters"""
        
        # Apply RL-optimized thresholds and weights
        optimized_config = {
            'confidence_thresholds': rl_action.rule_modifications['confidence_thresholds'],
            'model_weights': rl_action.rule_modifications['model_weights'],
            'cost_budget': rl_action.cost_budget
        }
        
        # Import ensemble classifier
        from ensemble_classifier import EnsembleClassifier
        
        # Create ensemble with RL-optimized configuration
        ensemble = EnsembleClassifier()
        
        # Override ensemble parameters with RL optimization
        ensemble.CONFIDENCE_THRESHOLDS = optimized_config['confidence_thresholds']
        ensemble.MODEL_WEIGHTS = optimized_config['model_weights']
        
        # Execute classification
        result = await ensemble.classify(
            title=title,
            abstract=abstract,
            mesh_terms=mesh_terms,
            publication_types=publication_types,
            force_ensemble=rl_action.model_selection == ['rule_based', 'bert', 'llm']
        )
        
        return result
    
    def _calculate_performance_metrics(self, classification_result: Dict[str, Any], 
                                     rl_action: RLAction, start_time: datetime) -> Dict[str, float]:
        """Calculate performance metrics for RL feedback"""
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Simulate performance metrics (in production, these would be real measurements)
        metrics = {
            'accuracy': self._estimate_accuracy(classification_result),
            'cost_efficiency': self._calculate_cost_efficiency(classification_result, rl_action),
            'processing_speed': 1.0 / max(processing_time, 0.001),  # Speed = 1/time
            'domain_specialization': self._calculate_domain_specialization_score(classification_result),
            'total_reward': 0.0  # Will be calculated by RL agent
        }
        
        return metrics
    
    def _update_rl_agent(self, rl_state: RLState, rl_action: RLAction, 
                        performance_metrics: Dict[str, float]):
        """Update RL agent with performance feedback"""
        try:
            # Create reward from performance metrics
            reward = RLReward(
                accuracy_reward=performance_metrics['accuracy'],
                cost_efficiency_reward=performance_metrics['cost_efficiency'],
                processing_speed_reward=performance_metrics['processing_speed'],
                stability_reward=0.8,  # Assume stable for now
                domain_specialization_reward=performance_metrics['domain_specialization'],
                total_reward=0.0  # Will be calculated by agent
            )
            
            # Create next state (simplified)
            next_state = rl_state  # In practice, this would be the next document's state
            
            # Store experience for learning
            self.rl_agent.store_experience(rl_state, rl_action, reward, next_state, False)
            
            # Update agent if enough experiences
            if len(self.rl_agent.memory) >= self.rl_agent.batch_size:
                self.rl_agent.train()
            
        except Exception as e:
            logger.warning("Failed to update RL agent", error=str(e))
    
    def _update_real_time_metrics(self, performance_metrics: Dict[str, float]):
        """Update real-time performance metrics"""
        # Update running averages
        alpha = 0.1  # Learning rate for exponential moving average
        
        self.performance_metrics.accuracy = (
            alpha * performance_metrics['accuracy'] + 
            (1 - alpha) * self.performance_metrics.accuracy
        )
        
        self.performance_metrics.cost_efficiency = (
            alpha * performance_metrics['cost_efficiency'] + 
            (1 - alpha) * self.performance_metrics.cost_efficiency
        )
        
        self.performance_metrics.processing_speed = (
            alpha * performance_metrics['processing_speed'] + 
            (1 - alpha) * self.performance_metrics.processing_speed
        )
        
        self.performance_metrics.domain_specialization = (
            alpha * performance_metrics['domain_specialization'] + 
            (1 - alpha) * self.performance_metrics.domain_specialization
        )
        
        # Update counters
        self.performance_metrics.document_count += 1
        self.performance_metrics.timestamp = datetime.utcnow()
        
        # Store in history
        self.real_time_metrics.append({
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': performance_metrics.copy(),
            'document_count': self.performance_metrics.document_count
        })
        
        # Keep only last 1000 entries
        if len(self.real_time_metrics) > 1000:
            self.real_time_metrics = self.real_time_metrics[-1000:]
    
    def _record_classification_event(self, classification_result: Dict[str, Any], 
                                   performance_metrics: Dict[str, float]):
        """Record classification event in monitoring system"""
        if not self.monitor:
            return
            
        try:
            self.monitor.record_episode(
                episode_idx=self.performance_metrics.document_count,
                reward=performance_metrics.get('total_reward', 0.0),
                length=1,  # Single document
                loss=0.0,  # No loss for inference
                epsilon=self.rl_agent.epsilon if hasattr(self.rl_agent, 'epsilon') else 0.0,
                memory_size=len(self.rl_agent.memory) if hasattr(self.rl_agent, 'memory') else 0,
                domain="pharmacovigilance"
            )
        except Exception as e:
            logger.warning("Failed to record monitoring event", error=str(e))
    
    async def _fallback_classification(self, title: str, abstract: str, 
                                     mesh_terms: List[str], publication_types: List[str]) -> RLClassificationResult:
        """Fallback classification when RL fails"""
        logger.warning("Using fallback classification")
        
        # Use basic ensemble without RL optimization
        from ensemble_classifier import EnsembleClassifier
        ensemble = EnsembleClassifier()
        
        result = await ensemble.classify(
            title=title,
            abstract=abstract,
            mesh_terms=mesh_terms,
            publication_types=publication_types
        )
        
        return RLClassificationResult(
            classification=result['ensemble_result'],
            confidence=result['confidence'],
            reasoning=result['reasoning'],
            models_used=result['models_used'],
            rl_decision_path='fallback',
            performance_metrics={'accuracy': 0.8, 'cost_efficiency': 0.5, 'processing_speed': 1.0, 'domain_specialization': 0.6, 'total_reward': 0.0},
            cost_estimate=result.get('cost_estimate', 0.0),
            processing_time=0.1,
            rl_optimization_applied=False
        )
    
    # Helper methods for feature extraction
    def _calculate_complexity_score(self, title: str, abstract: str, mesh_terms: List[str]) -> float:
        """Calculate document complexity score"""
        score = 0.0
        
        # Title complexity
        if title:
            score += min(len(title.split()) / 20.0, 1.0) * 0.3
        
        # Abstract complexity
        if abstract:
            score += min(len(abstract.split()) / 200.0, 1.0) * 0.4
        
        # MeSH terms complexity
        if mesh_terms:
            score += min(len(mesh_terms) / 10.0, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _calculate_domain_specialization(self, mesh_terms: List[str]) -> float:
        """Calculate domain specialization score"""
        if not mesh_terms:
            return 0.0
        
        # Medical domain keywords
        medical_keywords = [
            'pharmacology', 'drug', 'adverse', 'reaction', 'toxicity',
            'cardiology', 'neurology', 'oncology', 'hepatology'
        ]
        
        matches = sum(1 for term in mesh_terms if any(keyword in term.lower() for keyword in medical_keywords))
        return min(matches / len(mesh_terms), 1.0)
    
    def _extract_temporal_indicators(self, title: str, abstract: str) -> float:
        """Extract temporal indicators"""
        text = f"{title} {abstract}".lower()
        temporal_words = ['time', 'duration', 'follow', 'long', 'short', 'acute', 'chronic']
        return sum(1 for word in temporal_words if word in text) / len(temporal_words)
    
    def _extract_adverse_event_indicators(self, title: str, abstract: str) -> float:
        """Extract adverse event indicators"""
        text = f"{title} {abstract}".lower()
        adverse_words = ['adverse', 'side effect', 'toxicity', 'reaction', 'complication']
        return sum(1 for word in adverse_words if word in text) / len(adverse_words)
    
    def _extract_patient_indicators(self, title: str, abstract: str) -> float:
        """Extract patient indicators"""
        text = f"{title} {abstract}".lower()
        patient_words = ['patient', 'case', 'individual', 'subject', 'participant']
        return sum(1 for word in patient_words if word in text) / len(patient_words)
    
    def _extract_drug_indicators(self, title: str, abstract: str) -> float:
        """Extract drug indicators"""
        text = f"{title} {abstract}".lower()
        drug_words = ['drug', 'medication', 'therapy', 'treatment', 'dose']
        return sum(1 for word in drug_words if word in text) / len(drug_words)
    
    def _estimate_accuracy(self, classification_result: Dict[str, Any]) -> float:
        """Estimate classification accuracy"""
        confidence = classification_result.get('confidence', 0.5)
        models_used = classification_result.get('models_used', [])
        
        # Higher confidence and more models generally mean higher accuracy
        base_accuracy = confidence
        model_bonus = len(models_used) * 0.05
        
        return min(base_accuracy + model_bonus, 1.0)
    
    def _calculate_cost_efficiency(self, classification_result: Dict[str, Any], rl_action: RLAction) -> float:
        """Calculate cost efficiency"""
        cost_estimate = classification_result.get('cost_estimate', 0.0)
        cost_budget = rl_action.cost_budget
        
        if cost_budget > 0:
            return max(0.0, 1.0 - (cost_estimate / cost_budget))
        else:
            return 0.5  # Default efficiency
    
    def _calculate_domain_specialization_score(self, classification_result: Dict[str, Any]) -> float:
        """Calculate domain specialization score"""
        # This would be based on the classification result and domain knowledge
        return 0.7  # Default specialization score
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        return {
            'current_metrics': self.performance_metrics.__dict__,
            'recent_metrics': self.real_time_metrics[-10:] if self.real_time_metrics else [],
            'total_documents': self.performance_metrics.document_count,
            'rl_episodes': self.performance_metrics.rl_episodes_completed
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'accuracy': f"{self.performance_metrics.accuracy:.4f}",
            'cost_efficiency': f"{self.performance_metrics.cost_efficiency:.4f}",
            'processing_speed': f"{self.performance_metrics.processing_speed:.4f}",
            'domain_specialization': f"{self.performance_metrics.domain_specialization:.4f}",
            'total_documents_processed': self.performance_metrics.document_count,
            'last_updated': self.performance_metrics.timestamp.isoformat()
        }
