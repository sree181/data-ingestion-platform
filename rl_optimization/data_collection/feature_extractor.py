"""
Feature Extractor for RL Data Collection
Extracts document features and classification outcomes for RL training
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog
import numpy as np
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class DocumentFeatures:
    """Structured document features for RL training"""
    # Basic document info
    title: str
    abstract: str
    mesh_terms: List[str]
    publication_types: List[str]
    
    # Text features
    word_count: int
    sentence_count: int
    technical_term_count: int
    medical_term_count: int
    
    # Keyword features (from rule-based classifier)
    patient_mentions: int
    drug_mentions: int
    adverse_event_mentions: int
    temporal_mentions: int
    
    # MeSH term features
    icsr_mesh_count: int
    non_icsr_mesh_count: int
    rejected_signals: int
    
    # Context features
    domain: str
    complexity_score: float
    confidence_indicators: Dict[str, float]
    
    # Timestamp
    extracted_at: datetime


@dataclass
class ClassificationOutcome:
    """Classification outcome for RL training"""
    # Classification results
    true_classification: str
    predicted_classification: str
    confidence: float
    reasoning: str
    
    # Model usage
    models_used: List[str]
    decision_path: str
    processing_time_ms: int
    cost_estimate: float
    
    # Performance metrics
    is_correct: bool
    confidence_penalty: float
    cost_efficiency: float
    
    # Timestamp
    classified_at: datetime


class DocumentFeatureExtractor:
    """
    Extracts comprehensive features from documents for RL training
    """
    
    def __init__(self):
        # Medical terminology patterns
        self.medical_terms = {
            'adverse_events': [
                'adverse', 'reaction', 'side effect', 'toxicity', 'complication',
                'injury', 'death', 'hospitalization', 'discontinued', 'withdrawn',
                'hepatotoxicity', 'nephrotoxicity', 'cardiotoxicity', 'neurotoxicity',
                'anaphylaxis', 'hypersensitivity', 'allergic', 'rash', 'fever'
            ],
            'clinical_terms': [
                'patient', 'case report', 'diagnosed', 'presented', 'developed',
                'experienced', 'symptoms', 'treatment', 'therapy', 'medication',
                'dose', 'dosage', 'mg', 'tablet', 'injection', 'administration'
            ],
            'temporal_terms': [
                'after', 'following', 'within', 'days', 'weeks', 'months',
                'onset', 'duration', 'rechallenge', 'dechallenge', 'recovery'
            ]
        }
        
        # Technical/scientific terms
        self.technical_terms = [
            'in vitro', 'in vivo', 'animal model', 'cell culture', 'molecular',
            'docking', 'simulation', 'protein', 'structure', 'crystal',
            'polymorphism', 'pharmacokinetics', 'pharmacodynamics', 'metabolism'
        ]
        
        # ICSR MeSH terms (from rule-based classifier)
        self.icsr_mesh_terms = {
            'Case Reports',
            'Drug-Related Side Effects and Adverse Reactions',
            'Adverse Drug Reaction Reporting Systems',
            'Product Surveillance, Postmarketing',
            'Pharmacovigilance',
            'Drug Toxicity',
            'Drug Hypersensitivity',
            'Drug-Induced Liver Injury',
            'Stevens-Johnson Syndrome',
            'Anaphylaxis',
            'Drug Eruptions'
        }
        
        # Non-ICSR MeSH terms
        self.non_icsr_mesh_terms = {
            'Meta-Analysis',
            'Randomized Controlled Trial',
            'Clinical Trial',
            'Multicenter Study',
            'Review',
            'Systematic Review',
            'Animals',
            'In Vitro Techniques',
            'Cell Line',
            'Molecular Structure'
        }
        
        # Rejected keywords
        self.rejected_keywords = [
            'in vitro', 'in vivo', 'animal model', 'cell culture', 'molecular docking',
            'computational', 'simulation', 'protein structure', 'crystal structure',
            'genetic polymorphism', 'pharmacokinetics study'
        ]
        
        logger.info("Document feature extractor initialized")
    
    def extract_features(self, document_data: Dict[str, Any]) -> DocumentFeatures:
        """
        Extract comprehensive features from document data
        
        Args:
            document_data: Dictionary containing document information
            
        Returns:
            DocumentFeatures object with extracted features
        """
        title = document_data.get('title', '')
        abstract = document_data.get('abstract', '')
        mesh_terms = document_data.get('mesh_terms', [])
        publication_types = document_data.get('publication_types', [])
        
        # Combine text for analysis
        full_text = f"{title} {abstract}".lower()
        
        # Basic text features
        word_count = len(full_text.split())
        sentence_count = len(re.split(r'[.!?]+', full_text))
        
        # Medical terminology counts
        medical_term_count = self._count_medical_terms(full_text)
        technical_term_count = self._count_technical_terms(full_text)
        
        # Keyword features (from rule-based classifier)
        patient_mentions = self._count_keywords(full_text, self.medical_terms['clinical_terms'])
        drug_mentions = self._count_keywords(full_text, self.medical_terms['clinical_terms'])
        adverse_event_mentions = self._count_keywords(full_text, self.medical_terms['adverse_events'])
        temporal_mentions = self._count_keywords(full_text, self.medical_terms['temporal_terms'])
        
        # MeSH term analysis
        mesh_set = set(mesh_terms)
        icsr_mesh_count = len(mesh_set & self.icsr_mesh_terms)
        non_icsr_mesh_count = len(mesh_set & self.non_icsr_mesh_terms)
        
        # Rejected signals
        rejected_signals = sum(1 for keyword in self.rejected_keywords if keyword in full_text)
        
        # Domain classification
        domain = self._classify_domain(mesh_terms, publication_types, full_text)
        
        # Complexity score
        complexity_score = self._calculate_complexity_score(
            word_count, sentence_count, medical_term_count, technical_term_count
        )
        
        # Confidence indicators
        confidence_indicators = self._calculate_confidence_indicators(
            patient_mentions, drug_mentions, adverse_event_mentions,
            temporal_mentions, icsr_mesh_count, non_icsr_mesh_count
        )
        
        return DocumentFeatures(
            title=title,
            abstract=abstract,
            mesh_terms=mesh_terms,
            publication_types=publication_types,
            word_count=word_count,
            sentence_count=sentence_count,
            technical_term_count=technical_term_count,
            medical_term_count=medical_term_count,
            patient_mentions=patient_mentions,
            drug_mentions=drug_mentions,
            adverse_event_mentions=adverse_event_mentions,
            temporal_mentions=temporal_mentions,
            icsr_mesh_count=icsr_mesh_count,
            non_icsr_mesh_count=non_icsr_mesh_count,
            rejected_signals=rejected_signals,
            domain=domain,
            complexity_score=complexity_score,
            confidence_indicators=confidence_indicators,
            extracted_at=datetime.utcnow()
        )
    
    def _count_medical_terms(self, text: str) -> int:
        """Count medical terminology in text"""
        count = 0
        for category, terms in self.medical_terms.items():
            count += self._count_keywords(text, terms)
        return count
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical/scientific terms in text"""
        return self._count_keywords(text, self.technical_terms)
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count keyword occurrences in text"""
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        return count
    
    def _classify_domain(self, mesh_terms: List[str], pub_types: List[str], text: str) -> str:
        """Classify document domain based on MeSH terms and content"""
        mesh_set = set(mesh_terms)
        pub_set = set(pub_types)
        
        # Liver/hepatology domain
        liver_terms = ['liver', 'hepat', 'biliary', 'hepatotoxicity']
        if any(term in text for term in liver_terms) or any('liver' in mesh.lower() for mesh in mesh_terms):
            return 'hepatology'
        
        # Cardiology domain
        cardio_terms = ['cardiac', 'heart', 'cardiovascular', 'myocardial']
        if any(term in text for term in cardio_terms) or any('cardiac' in mesh.lower() for mesh in mesh_terms):
            return 'cardiology'
        
        # Neurology domain
        neuro_terms = ['neurological', 'brain', 'neural', 'cognitive', 'seizure']
        if any(term in text for term in neuro_terms) or any('neurological' in mesh.lower() for mesh in mesh_terms):
            return 'neurology'
        
        # Oncology domain
        onco_terms = ['cancer', 'tumor', 'neoplasm', 'oncology', 'chemotherapy']
        if any(term in text for term in onco_terms) or any('neoplasm' in mesh.lower() for mesh in mesh_terms):
            return 'oncology'
        
        # General medicine
        return 'general_medicine'
    
    def _calculate_complexity_score(self, word_count: int, sentence_count: int, 
                                  medical_terms: int, technical_terms: int) -> float:
        """Calculate document complexity score (0-1)"""
        # Normalize factors
        word_factor = min(word_count / 1000, 1.0)  # Cap at 1000 words
        sentence_factor = min(sentence_count / 50, 1.0)  # Cap at 50 sentences
        medical_factor = min(medical_terms / 20, 1.0)  # Cap at 20 medical terms
        technical_factor = min(technical_terms / 10, 1.0)  # Cap at 10 technical terms
        
        # Weighted combination
        complexity = (
            word_factor * 0.3 +
            sentence_factor * 0.2 +
            medical_factor * 0.3 +
            technical_factor * 0.2
        )
        
        return min(complexity, 1.0)
    
    def _calculate_confidence_indicators(self, patient_mentions: int, drug_mentions: int,
                                       adverse_event_mentions: int, temporal_mentions: int,
                                       icsr_mesh_count: int, non_icsr_mesh_count: int) -> Dict[str, float]:
        """Calculate confidence indicators for different classification paths"""
        indicators = {}
        
        # ICSR confidence indicators
        icsr_evidence = patient_mentions + drug_mentions + adverse_event_mentions + temporal_mentions
        indicators['icsr_evidence_strength'] = min(icsr_evidence / 10, 1.0)
        
        # MeSH term confidence
        total_mesh = icsr_mesh_count + non_icsr_mesh_count
        if total_mesh > 0:
            indicators['icsr_mesh_ratio'] = icsr_mesh_count / total_mesh
            indicators['non_icsr_mesh_ratio'] = non_icsr_mesh_count / total_mesh
        else:
            indicators['icsr_mesh_ratio'] = 0.0
            indicators['non_icsr_mesh_ratio'] = 0.0
        
        # Temporal evidence strength
        indicators['temporal_evidence'] = min(temporal_mentions / 5, 1.0)
        
        # Overall confidence
        indicators['overall_confidence'] = (
            indicators['icsr_evidence_strength'] * 0.4 +
            indicators['icsr_mesh_ratio'] * 0.3 +
            indicators['temporal_evidence'] * 0.3
        )
        
        return indicators


class ClassificationOutcomeTracker:
    """
    Tracks classification outcomes for RL training
    """
    
    def __init__(self):
        logger.info("Classification outcome tracker initialized")
    
    def track_outcome(self, classification_result: Dict[str, Any], 
                     true_classification: Optional[str] = None) -> ClassificationOutcome:
        """
        Track classification outcome for RL training
        
        Args:
            classification_result: Result from ensemble classifier
            true_classification: Ground truth classification (if available)
            
        Returns:
            ClassificationOutcome object
        """
        predicted_classification = classification_result.get('classification', 'Unknown')
        confidence = classification_result.get('classification_confidence', 0.0)
        reasoning = classification_result.get('reasoning', '')
        models_used = classification_result.get('models_used', [])
        decision_path = classification_result.get('decision_path', 'unknown')
        processing_time_ms = classification_result.get('processing_time_ms', 0)
        cost_estimate = classification_result.get('cost_estimate', 0.0)
        
        # Calculate performance metrics
        is_correct = self._calculate_accuracy(predicted_classification, true_classification)
        confidence_penalty = self._calculate_confidence_penalty(confidence, is_correct)
        cost_efficiency = self._calculate_cost_efficiency(confidence, cost_estimate, is_correct)
        
        return ClassificationOutcome(
            true_classification=true_classification or 'Unknown',
            predicted_classification=predicted_classification,
            confidence=confidence,
            reasoning=reasoning,
            models_used=models_used,
            decision_path=decision_path,
            processing_time_ms=processing_time_ms,
            cost_estimate=cost_estimate,
            is_correct=is_correct,
            confidence_penalty=confidence_penalty,
            cost_efficiency=cost_efficiency,
            classified_at=datetime.utcnow()
        )
    
    def _calculate_accuracy(self, predicted: str, true: Optional[str]) -> bool:
        """Calculate if prediction is correct"""
        if true is None:
            return False
        return predicted == true
    
    def _calculate_confidence_penalty(self, confidence: float, is_correct: bool) -> float:
        """Calculate confidence penalty for RL reward"""
        if is_correct:
            return confidence  # Reward high confidence when correct
        else:
            return -confidence  # Penalize high confidence when wrong
    
    def _calculate_cost_efficiency(self, confidence: float, cost: float, is_correct: bool) -> float:
        """Calculate cost efficiency metric"""
        if cost == 0:
            return 1.0  # Perfect efficiency for free predictions
        
        # Efficiency = (accuracy * confidence) / cost
        accuracy_score = 1.0 if is_correct else 0.0
        return (accuracy_score * confidence) / max(cost, 0.001)


class RLDataCollector:
    """
    Main data collector for RL training
    Combines feature extraction and outcome tracking
    """
    
    def __init__(self):
        self.feature_extractor = DocumentFeatureExtractor()
        self.outcome_tracker = ClassificationOutcomeTracker()
        logger.info("RL data collector initialized")
    
    def collect_training_data(self, document_data: Dict[str, Any], 
                            classification_result: Dict[str, Any],
                            true_classification: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect complete training data for RL
        
        Args:
            document_data: Document information
            classification_result: Classification result from ensemble
            true_classification: Ground truth (if available)
            
        Returns:
            Complete training data dictionary
        """
        # Extract features
        features = self.feature_extractor.extract_features(document_data)
        
        # Track outcome
        outcome = self.outcome_tracker.track_outcome(classification_result, true_classification)
        
        # Combine into training data
        training_data = {
            'features': features,
            'outcome': outcome,
            'collected_at': datetime.utcnow(),
            'data_id': f"{features.title[:50]}_{datetime.utcnow().timestamp()}"
        }
        
        logger.info("Training data collected", 
                   data_id=training_data['data_id'],
                   domain=features.domain,
                   classification=outcome.predicted_classification,
                   is_correct=outcome.is_correct)
        
        return training_data
    
    def save_training_data(self, training_data: Dict[str, Any], filepath: str):
        """Save training data to file"""
        # Convert dataclasses to dictionaries for JSON serialization
        data_to_save = {
            'features': {
                'title': training_data['features'].title,
                'abstract': training_data['features'].abstract,
                'mesh_terms': training_data['features'].mesh_terms,
                'publication_types': training_data['features'].publication_types,
                'word_count': training_data['features'].word_count,
                'sentence_count': training_data['features'].sentence_count,
                'technical_term_count': training_data['features'].technical_term_count,
                'medical_term_count': training_data['features'].medical_term_count,
                'patient_mentions': training_data['features'].patient_mentions,
                'drug_mentions': training_data['features'].drug_mentions,
                'adverse_event_mentions': training_data['features'].adverse_event_mentions,
                'temporal_mentions': training_data['features'].temporal_mentions,
                'icsr_mesh_count': training_data['features'].icsr_mesh_count,
                'non_icsr_mesh_count': training_data['features'].non_icsr_mesh_count,
                'rejected_signals': training_data['features'].rejected_signals,
                'domain': training_data['features'].domain,
                'complexity_score': training_data['features'].complexity_score,
                'confidence_indicators': training_data['features'].confidence_indicators,
                'extracted_at': training_data['features'].extracted_at.isoformat()
            },
            'outcome': {
                'true_classification': training_data['outcome'].true_classification,
                'predicted_classification': training_data['outcome'].predicted_classification,
                'confidence': training_data['outcome'].confidence,
                'reasoning': training_data['outcome'].reasoning,
                'models_used': training_data['outcome'].models_used,
                'decision_path': training_data['outcome'].decision_path,
                'processing_time_ms': training_data['outcome'].processing_time_ms,
                'cost_estimate': training_data['outcome'].cost_estimate,
                'is_correct': training_data['outcome'].is_correct,
                'confidence_penalty': training_data['outcome'].confidence_penalty,
                'cost_efficiency': training_data['outcome'].cost_efficiency,
                'classified_at': training_data['outcome'].classified_at.isoformat()
            },
            'collected_at': training_data['collected_at'].isoformat(),
            'data_id': training_data['data_id']
        }
        
        with open(filepath, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        logger.info("Training data saved", filepath=filepath)


# Example usage and testing
if __name__ == "__main__":
    # Test the data collector
    collector = RLDataCollector()
    
    # Sample document data
    sample_document = {
        'title': 'Case report of severe hepatotoxicity in patient taking acetaminophen',
        'abstract': 'A 45-year-old male patient developed severe liver injury after taking acetaminophen for 3 days. The patient presented with jaundice and elevated liver enzymes.',
        'mesh_terms': ['Case Reports', 'Drug-Induced Liver Injury', 'Acetaminophen'],
        'publication_types': ['Case Report']
    }
    
    # Sample classification result
    sample_result = {
        'ensemble_result': 'ICSR',
        'confidence': 0.92,
        'reasoning': 'High confidence: Case Report publication type with ICSR MeSH terms',
        'models_used': ['rule_based'],
        'decision_path': 'rule_based_only',
        'processing_time_ms': 15,
        'cost_estimate': 0.0
    }
    
    # Collect training data
    training_data = collector.collect_training_data(
        sample_document, 
        sample_result, 
        'ICSR'  # Ground truth
    )
    
    print("Training data collected successfully!")
    print(f"Domain: {training_data['features'].domain}")
    print(f"Classification: {training_data['outcome'].predicted_classification}")
    print(f"Correct: {training_data['outcome'].is_correct}")
    print(f"Cost efficiency: {training_data['outcome'].cost_efficiency:.3f}")
