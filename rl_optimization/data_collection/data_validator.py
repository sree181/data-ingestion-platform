"""
Data Validator for RL Training Data
Validates data quality and integrity for RL training
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import structlog
import numpy as np
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    quality_score: float
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    statistics: Dict[str, Any]


class DataValidator:
    """
    Validates RL training data for quality and consistency
    """
    
    def __init__(self):
        # Validation thresholds
        self.thresholds = {
            'min_word_count': 10,
            'max_word_count': 10000,
            'min_confidence': 0.0,
            'max_confidence': 1.0,
            'min_processing_time': 1,  # ms
            'max_processing_time': 30000,  # ms
            'min_cost': 0.0,
            'max_cost': 1.0,
            'min_accuracy_rate': 0.0,
            'max_accuracy_rate': 1.0
        }
        
        # Required fields
        self.required_feature_fields = [
            'title', 'abstract', 'mesh_terms', 'publication_types',
            'word_count', 'sentence_count', 'technical_term_count',
            'medical_term_count', 'patient_mentions', 'drug_mentions',
            'adverse_event_mentions', 'temporal_mentions', 'icsr_mesh_count',
            'non_icsr_mesh_count', 'rejected_signals', 'domain',
            'complexity_score', 'confidence_indicators'
        ]
        
        self.required_outcome_fields = [
            'true_classification', 'predicted_classification', 'confidence',
            'reasoning', 'models_used', 'decision_path', 'processing_time_ms',
            'cost_estimate', 'is_correct', 'confidence_penalty', 'cost_efficiency'
        ]
        
        # Valid classification categories
        self.valid_classifications = ['ICSR', 'Safety_Information', 'Non-ICSR', 'Rejected']
        
        # Valid domains
        self.valid_domains = ['hepatology', 'cardiology', 'neurology', 'oncology', 'general_medicine']
        
        # Valid decision paths
        self.valid_decision_paths = ['rule_based_only', 'rule_based_and_bert', 'full_ensemble']
        
        logger.info("Data validator initialized")
    
    def _convert_features_to_dict(self, features) -> Dict[str, Any]:
        """Convert DocumentFeatures object to dictionary"""
        if isinstance(features, dict):
            return features
        return {
            'title': features.title,
            'abstract': features.abstract,
            'mesh_terms': features.mesh_terms,
            'publication_types': features.publication_types,
            'word_count': features.word_count,
            'sentence_count': features.sentence_count,
            'technical_term_count': features.technical_term_count,
            'medical_term_count': features.medical_term_count,
            'patient_mentions': features.patient_mentions,
            'drug_mentions': features.drug_mentions,
            'adverse_event_mentions': features.adverse_event_mentions,
            'temporal_mentions': features.temporal_mentions,
            'icsr_mesh_count': features.icsr_mesh_count,
            'non_icsr_mesh_count': features.non_icsr_mesh_count,
            'rejected_signals': features.rejected_signals,
            'domain': features.domain,
            'complexity_score': features.complexity_score,
            'confidence_indicators': features.confidence_indicators
        }
    
    def _convert_outcome_to_dict(self, outcome) -> Dict[str, Any]:
        """Convert ClassificationOutcome object to dictionary"""
        if isinstance(outcome, dict):
            return outcome
        return {
            'true_classification': outcome.true_classification,
            'predicted_classification': outcome.predicted_classification,
            'confidence': outcome.confidence,
            'reasoning': outcome.reasoning,
            'models_used': outcome.models_used,
            'decision_path': outcome.decision_path,
            'processing_time_ms': outcome.processing_time_ms,
            'cost_estimate': outcome.cost_estimate,
            'is_correct': outcome.is_correct,
            'confidence_penalty': outcome.confidence_penalty,
            'cost_efficiency': outcome.cost_efficiency
        }
    
    def validate_training_data(self, training_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate single training data entry
        
        Args:
            training_data: Training data dictionary
            
        Returns:
            ValidationResult object
        """
        issues = []
        warnings = []
        recommendations = []
        
        # Check required fields
        issues.extend(self._validate_required_fields(training_data))
        
        # Validate feature data
        if 'features' in training_data:
            # Convert DocumentFeatures object to dictionary for validation
            features_dict = self._convert_features_to_dict(training_data['features'])
            issues.extend(self._validate_features(features_dict))
            warnings.extend(self._validate_feature_quality(features_dict))
        
        # Validate outcome data
        if 'outcome' in training_data:
            # Convert ClassificationOutcome object to dictionary for validation
            outcome_dict = self._convert_outcome_to_dict(training_data['outcome'])
            issues.extend(self._validate_outcome(outcome_dict))
            warnings.extend(self._validate_outcome_quality(outcome_dict))
        
        # Validate data consistency
        if 'features' in training_data and 'outcome' in training_data:
            features_dict = self._convert_features_to_dict(training_data['features'])
            outcome_dict = self._convert_outcome_to_dict(training_data['outcome'])
            issues.extend(self._validate_consistency(features_dict, outcome_dict))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(issues, warnings)
        
        # Generate recommendations
        recommendations.extend(self._generate_recommendations(issues, warnings, training_data))
        
        # Calculate statistics
        statistics = self._calculate_statistics(training_data)
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            statistics=statistics
        )
    
    def validate_dataset(self, dataset: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate entire dataset
        
        Args:
            dataset: List of training data entries
            
        Returns:
            ValidationResult object
        """
        issues = []
        warnings = []
        recommendations = []
        
        if not dataset:
            issues.append("Dataset is empty")
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations,
                statistics={}
            )
        
        # Validate each entry
        individual_results = []
        for i, entry in enumerate(dataset):
            result = self.validate_training_data(entry)
            individual_results.append(result)
            
            # Collect issues with entry index
            for issue in result.issues:
                issues.append(f"Entry {i}: {issue}")
            for warning in result.warnings:
                warnings.append(f"Entry {i}: {warning}")
        
        # Dataset-level validation
        issues.extend(self._validate_dataset_consistency(dataset))
        warnings.extend(self._validate_dataset_quality(dataset))
        
        # Calculate overall quality score
        individual_scores = [r.quality_score for r in individual_results]
        quality_score = np.mean(individual_scores) if individual_scores else 0.0
        
        # Generate dataset-level recommendations
        recommendations.extend(self._generate_dataset_recommendations(dataset, individual_results))
        
        # Calculate dataset statistics
        statistics = self._calculate_dataset_statistics(dataset)
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            statistics=statistics
        )
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """Validate required fields are present"""
        issues = []
        
        if 'features' not in data:
            issues.append("Missing 'features' field")
            return issues
        
        if 'outcome' not in data:
            issues.append("Missing 'outcome' field")
            return issues
        
        # Check feature fields
        features_dict = self._convert_features_to_dict(data['features'])
        for field in self.required_feature_fields:
            if field not in features_dict:
                issues.append(f"Missing required feature field: {field}")
        
        # Check outcome fields
        outcome_dict = self._convert_outcome_to_dict(data['outcome'])
        for field in self.required_outcome_fields:
            if field not in outcome_dict:
                issues.append(f"Missing required outcome field: {field}")
        
        return issues
    
    def _validate_features(self, features: Dict[str, Any]) -> List[str]:
        """Validate feature data"""
        issues = []
        
        # Validate text fields
        if not isinstance(features.get('title', ''), str) or not features['title'].strip():
            issues.append("Title must be a non-empty string")
        
        if not isinstance(features.get('abstract', ''), str):
            issues.append("Abstract must be a string")
        
        # Validate lists
        if not isinstance(features.get('mesh_terms', []), list):
            issues.append("mesh_terms must be a list")
        
        if not isinstance(features.get('publication_types', []), list):
            issues.append("publication_types must be a list")
        
        # Validate numeric fields
        numeric_fields = ['word_count', 'sentence_count', 'technical_term_count', 
                         'medical_term_count', 'patient_mentions', 'drug_mentions',
                         'adverse_event_mentions', 'temporal_mentions', 'icsr_mesh_count',
                         'non_icsr_mesh_count', 'rejected_signals']
        
        for field in numeric_fields:
            if field in features:
                value = features[field]
                if not isinstance(value, (int, float)) or value < 0:
                    issues.append(f"{field} must be a non-negative number")
        
        # Validate domain
        domain = features.get('domain', '')
        if domain not in self.valid_domains:
            issues.append(f"Invalid domain: {domain}. Must be one of {self.valid_domains}")
        
        # Validate complexity score
        complexity = features.get('complexity_score', 0)
        if not isinstance(complexity, (int, float)) or not (0 <= complexity <= 1):
            issues.append("complexity_score must be between 0 and 1")
        
        # Validate confidence indicators
        confidence_indicators = features.get('confidence_indicators', {})
        if not isinstance(confidence_indicators, dict):
            issues.append("confidence_indicators must be a dictionary")
        else:
            for key, value in confidence_indicators.items():
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    issues.append(f"confidence_indicators.{key} must be between 0 and 1")
        
        return issues
    
    def _validate_outcome(self, outcome: Dict[str, Any]) -> List[str]:
        """Validate outcome data"""
        issues = []
        
        # Validate classifications
        true_class = outcome.get('true_classification', '')
        pred_class = outcome.get('predicted_classification', '')
        
        if true_class not in self.valid_classifications:
            issues.append(f"Invalid true_classification: {true_class}")
        
        if pred_class not in self.valid_classifications:
            issues.append(f"Invalid predicted_classification: {pred_class}")
        
        # Validate confidence
        confidence = outcome.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            issues.append("confidence must be between 0 and 1")
        
        # Validate processing time
        processing_time = outcome.get('processing_time_ms', 0)
        if not isinstance(processing_time, (int, float)) or processing_time < 0:
            issues.append("processing_time_ms must be a non-negative number")
        
        # Validate cost
        cost = outcome.get('cost_estimate', 0)
        if not isinstance(cost, (int, float)) or cost < 0:
            issues.append("cost_estimate must be a non-negative number")
        
        # Validate boolean fields
        is_correct = outcome.get('is_correct', False)
        if not isinstance(is_correct, bool):
            issues.append("is_correct must be a boolean")
        
        # Validate decision path
        decision_path = outcome.get('decision_path', '')
        if decision_path not in self.valid_decision_paths:
            issues.append(f"Invalid decision_path: {decision_path}")
        
        # Validate models_used
        models_used = outcome.get('models_used', [])
        if not isinstance(models_used, list):
            issues.append("models_used must be a list")
        else:
            valid_models = ['rule_based', 'bert', 'llm']
            for model in models_used:
                if model not in valid_models:
                    issues.append(f"Invalid model in models_used: {model}")
        
        return issues
    
    def _validate_feature_quality(self, features: Dict[str, Any]) -> List[str]:
        """Validate feature quality (warnings)"""
        warnings = []
        
        # Check word count
        word_count = features.get('word_count', 0)
        if word_count < self.thresholds['min_word_count']:
            warnings.append(f"Very low word count: {word_count}")
        elif word_count > self.thresholds['max_word_count']:
            warnings.append(f"Very high word count: {word_count}")
        
        # Check complexity score
        complexity = features.get('complexity_score', 0)
        if complexity < 0.1:
            warnings.append("Very low complexity score - document may be too simple")
        elif complexity > 0.9:
            warnings.append("Very high complexity score - document may be too complex")
        
        # Check confidence indicators
        confidence_indicators = features.get('confidence_indicators', {})
        overall_confidence = confidence_indicators.get('overall_confidence', 0)
        if overall_confidence < 0.3:
            warnings.append("Low overall confidence indicators")
        
        return warnings
    
    def _validate_outcome_quality(self, outcome: Dict[str, Any]) -> List[str]:
        """Validate outcome quality (warnings)"""
        warnings = []
        
        # Check confidence
        confidence = outcome.get('confidence', 0)
        if confidence < 0.5:
            warnings.append("Low confidence prediction")
        
        # Check processing time
        processing_time = outcome.get('processing_time_ms', 0)
        if processing_time > 10000:  # 10 seconds
            warnings.append("High processing time")
        
        # Check cost efficiency
        cost_efficiency = outcome.get('cost_efficiency', 0)
        if cost_efficiency < 0.5:
            warnings.append("Low cost efficiency")
        
        return warnings
    
    def _validate_consistency(self, features: Dict[str, Any], outcome: Dict[str, Any]) -> List[str]:
        """Validate consistency between features and outcome"""
        issues = []
        
        # Check if confidence indicators align with outcome confidence
        confidence_indicators = features.get('confidence_indicators', {})
        overall_confidence = confidence_indicators.get('overall_confidence', 0)
        outcome_confidence = outcome.get('confidence', 0)
        
        if abs(overall_confidence - outcome_confidence) > 0.5:
            issues.append("Large discrepancy between feature confidence indicators and outcome confidence")
        
        # Check if decision path makes sense given models used
        decision_path = outcome.get('decision_path', '')
        models_used = outcome.get('models_used', [])
        
        if decision_path == 'rule_based_only' and len(models_used) > 1:
            issues.append("Decision path says rule_based_only but multiple models were used")
        elif decision_path == 'rule_based_and_bert' and 'llm' in models_used:
            issues.append("Decision path says rule_based_and_bert but LLM was used")
        
        return issues
    
    def _validate_dataset_consistency(self, dataset: List[Dict[str, Any]]) -> List[str]:
        """Validate dataset-level consistency"""
        issues = []
        
        if not dataset:
            return issues
        
        # Check for duplicate entries
        data_ids = [entry.get('data_id', '') for entry in dataset]
        if len(data_ids) != len(set(data_ids)):
            issues.append("Duplicate data_id found in dataset")
        
        # Check classification distribution
        classifications = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('predicted_classification', '') for entry in dataset]
        classification_counts = {}
        for cls in classifications:
            classification_counts[cls] = classification_counts.get(cls, 0) + 1
        
        # Check for extreme imbalance
        total = len(classifications)
        for cls, count in classification_counts.items():
            if count / total < 0.05:  # Less than 5%
                issues.append(f"Very low representation of classification: {cls} ({count}/{total})")
        
        return issues
    
    def _validate_dataset_quality(self, dataset: List[Dict[str, Any]]) -> List[str]:
        """Validate dataset-level quality (warnings)"""
        warnings = []
        
        if not dataset:
            return warnings
        
        # Check accuracy rate
        correct_predictions = sum(1 for entry in dataset if self._convert_outcome_to_dict(entry.get('outcome', {})).get('is_correct', False))
        accuracy_rate = correct_predictions / len(dataset)
        
        if accuracy_rate < 0.7:
            warnings.append(f"Low accuracy rate: {accuracy_rate:.2f}")
        
        # Check average confidence
        confidences = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('confidence', 0) for entry in dataset]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        if avg_confidence < 0.6:
            warnings.append(f"Low average confidence: {avg_confidence:.2f}")
        
        # Check cost distribution
        costs = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('cost_estimate', 0) for entry in dataset]
        avg_cost = np.mean(costs) if costs else 0
        
        if avg_cost > 0.01:  # More than 1 cent average
            warnings.append(f"High average cost: {avg_cost:.4f}")
        
        return warnings
    
    def _calculate_quality_score(self, issues: List[str], warnings: List[str]) -> float:
        """Calculate overall quality score (0-1)"""
        # Base score
        score = 1.0
        
        # Penalize issues heavily
        score -= len(issues) * 0.2
        
        # Penalize warnings moderately
        score -= len(warnings) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(self, issues: List[str], warnings: List[str], 
                                training_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for data improvement"""
        recommendations = []
        
        # Issue-based recommendations
        if any("Missing required" in issue for issue in issues):
            recommendations.append("Ensure all required fields are present in training data")
        
        if any("Invalid domain" in issue for issue in issues):
            recommendations.append("Use valid domain classifications: hepatology, cardiology, neurology, oncology, general_medicine")
        
        if any("confidence must be between" in issue for issue in issues):
            recommendations.append("Ensure confidence scores are between 0 and 1")
        
        # Warning-based recommendations
        if any("Very low word count" in warning for warning in warnings):
            recommendations.append("Consider filtering out very short documents")
        
        if any("Low confidence prediction" in warning for warning in warnings):
            recommendations.append("Review low-confidence predictions for potential data quality issues")
        
        if any("High processing time" in warning for warning in warnings):
            recommendations.append("Investigate high processing times - may indicate system issues")
        
        return recommendations
    
    def _generate_dataset_recommendations(self, dataset: List[Dict[str, Any]], 
                                        individual_results: List[ValidationResult]) -> List[str]:
        """Generate dataset-level recommendations"""
        recommendations = []
        
        # Check overall quality
        avg_quality = np.mean([r.quality_score for r in individual_results])
        if avg_quality < 0.8:
            recommendations.append("Overall dataset quality is low - consider data cleaning")
        
        # Check size
        if len(dataset) < 100:
            recommendations.append("Dataset is small - consider collecting more data for better RL training")
        
        # Check balance
        classifications = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('predicted_classification', '') for entry in dataset]
        classification_counts = {}
        for cls in classifications:
            classification_counts[cls] = classification_counts.get(cls, 0) + 1
        
        total = len(classifications)
        for cls, count in classification_counts.items():
            if count / total < 0.1:  # Less than 10%
                recommendations.append(f"Consider collecting more examples of {cls} classification")
        
        return recommendations
    
    def _calculate_statistics(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics for single training data entry"""
        features = self._convert_features_to_dict(training_data.get('features', {}))
        outcome = self._convert_outcome_to_dict(training_data.get('outcome', {}))
        
        return {
            'word_count': features.get('word_count', 0),
            'complexity_score': features.get('complexity_score', 0),
            'confidence': outcome.get('confidence', 0),
            'processing_time_ms': outcome.get('processing_time_ms', 0),
            'cost_estimate': outcome.get('cost_estimate', 0),
            'is_correct': outcome.get('is_correct', False)
        }
    
    def _calculate_dataset_statistics(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate dataset-level statistics"""
        if not dataset:
            return {}
        
        # Extract metrics
        word_counts = [self._convert_features_to_dict(entry.get('features', {})).get('word_count', 0) for entry in dataset]
        complexity_scores = [self._convert_features_to_dict(entry.get('features', {})).get('complexity_score', 0) for entry in dataset]
        confidences = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('confidence', 0) for entry in dataset]
        processing_times = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('processing_time_ms', 0) for entry in dataset]
        costs = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('cost_estimate', 0) for entry in dataset]
        is_correct = [self._convert_outcome_to_dict(entry.get('outcome', {})).get('is_correct', False) for entry in dataset]
        
        # Calculate statistics
        return {
            'total_entries': len(dataset),
            'accuracy_rate': sum(is_correct) / len(is_correct),
            'avg_word_count': np.mean(word_counts),
            'avg_complexity_score': np.mean(complexity_scores),
            'avg_confidence': np.mean(confidences),
            'avg_processing_time_ms': np.mean(processing_times),
            'avg_cost': np.mean(costs),
            'total_cost': sum(costs),
            'classification_distribution': {
                cls: sum(1 for entry in dataset 
                        if self._convert_outcome_to_dict(entry.get('outcome', {})).get('predicted_classification') == cls)
                for cls in self.valid_classifications
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the validator
    validator = DataValidator()
    
    # Sample training data
    sample_data = {
        'features': {
            'title': 'Case report of hepatotoxicity',
            'abstract': 'Patient developed liver injury after medication',
            'mesh_terms': ['Case Reports', 'Drug-Induced Liver Injury'],
            'publication_types': ['Case Report'],
            'word_count': 15,
            'sentence_count': 2,
            'technical_term_count': 0,
            'medical_term_count': 5,
            'patient_mentions': 1,
            'drug_mentions': 1,
            'adverse_event_mentions': 1,
            'temporal_mentions': 1,
            'icsr_mesh_count': 2,
            'non_icsr_mesh_count': 0,
            'rejected_signals': 0,
            'domain': 'hepatology',
            'complexity_score': 0.3,
            'confidence_indicators': {
                'icsr_evidence_strength': 0.8,
                'icsr_mesh_ratio': 1.0,
                'temporal_evidence': 0.6,
                'overall_confidence': 0.8
            }
        },
        'outcome': {
            'true_classification': 'ICSR',
            'predicted_classification': 'ICSR',
            'confidence': 0.92,
            'reasoning': 'High confidence rule-based classification',
            'models_used': ['rule_based'],
            'decision_path': 'rule_based_only',
            'processing_time_ms': 15,
            'cost_estimate': 0.0,
            'is_correct': True,
            'confidence_penalty': 0.92,
            'cost_efficiency': 1.0
        },
        'data_id': 'test_001'
    }
    
    # Validate the data
    result = validator.validate_training_data(sample_data)
    
    print("Validation Result:")
    print(f"Valid: {result.is_valid}")
    print(f"Quality Score: {result.quality_score:.2f}")
    print(f"Issues: {len(result.issues)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Recommendations: {len(result.recommendations)}")
    
    if result.issues:
        print("\nIssues:")
        for issue in result.issues:
            print(f"  - {issue}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
