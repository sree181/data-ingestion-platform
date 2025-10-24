"""
Main Data Collector for RL Training
Orchestrates data collection from the current PV classification system
"""

import json
import os
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import structlog
import pandas as pd
from pathlib import Path

from feature_extractor import RLDataCollector, DocumentFeatures, ClassificationOutcome
from data_validator import DataValidator, ValidationResult

logger = structlog.get_logger(__name__)


class RLDataCollectionOrchestrator:
    """
    Main orchestrator for collecting RL training data
    """
    
    def __init__(self, output_dir: str = "rl_optimization/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.data_collector = RLDataCollector()
        self.validator = DataValidator()
        
        # Data storage
        self.training_data = []
        self.validation_results = []
        
        # Collection statistics
        self.stats = {
            'total_collected': 0,
            'valid_entries': 0,
            'invalid_entries': 0,
            'domains': {},
            'classifications': {},
            'decision_paths': {},
            'start_time': None,
            'end_time': None
        }
        
        logger.info("RL data collection orchestrator initialized", output_dir=str(self.output_dir))
    
    async def collect_from_classification_service(self, 
                                                classification_service_url: str,
                                                max_documents: int = 1000,
                                                batch_size: int = 50) -> Dict[str, Any]:
        """
        Collect data from the running classification service
        
        Args:
            classification_service_url: URL of the classification service
            max_documents: Maximum number of documents to collect
            batch_size: Number of documents to process in each batch
            
        Returns:
            Collection summary
        """
        logger.info("Starting data collection from classification service",
                   service_url=classification_service_url,
                   max_documents=max_documents)
        
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            # This would integrate with the actual classification service
            # For now, we'll simulate the collection process
            collected_data = await self._simulate_data_collection(
                max_documents, batch_size
            )
            
            # Process collected data
            for data in collected_data:
                await self._process_training_data(data)
            
            # Generate final report
            report = self._generate_collection_report()
            
            # Save data and report
            await self._save_collection_data()
            
            self.stats['end_time'] = datetime.utcnow()
            
            logger.info("Data collection completed",
                       total_collected=self.stats['total_collected'],
                       valid_entries=self.stats['valid_entries'],
                       invalid_entries=self.stats['invalid_entries'])
            
            return report
            
        except Exception as e:
            logger.error("Data collection failed", error=str(e))
            raise
    
    async def collect_from_elasticsearch(self, 
                                       elasticsearch_url: str,
                                       index_name: str = "documents",
                                       max_documents: int = 1000) -> Dict[str, Any]:
        """
        Collect data from Elasticsearch index
        
        Args:
            elasticsearch_url: Elasticsearch URL
            index_name: Index name containing documents
            max_documents: Maximum number of documents to collect
            
        Returns:
            Collection summary
        """
        logger.info("Starting data collection from Elasticsearch",
                   es_url=elasticsearch_url,
                   index=index_name,
                   max_documents=max_documents)
        
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            # This would integrate with Elasticsearch
            # For now, we'll simulate the collection process
            collected_data = await self._simulate_elasticsearch_collection(
                max_documents
            )
            
            # Process collected data
            for data in collected_data:
                await self._process_training_data(data)
            
            # Generate final report
            report = self._generate_collection_report()
            
            # Save data and report
            await self._save_collection_data()
            
            self.stats['end_time'] = datetime.utcnow()
            
            logger.info("Elasticsearch data collection completed",
                       total_collected=self.stats['total_collected'],
                       valid_entries=self.stats['valid_entries'])
            
            return report
            
        except Exception as e:
            logger.error("Elasticsearch data collection failed", error=str(e))
            raise
    
    async def collect_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Collect data from a JSON file containing classification results
        
        Args:
            file_path: Path to JSON file with classification data
            
        Returns:
            Collection summary
        """
        logger.info("Starting data collection from file", file_path=file_path)
        
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Process each entry
            if isinstance(data, list):
                for entry in data:
                    await self._process_training_data(entry)
            else:
                await self._process_training_data(data)
            
            # Generate final report
            report = self._generate_collection_report()
            
            # Save data and report
            await self._save_collection_data()
            
            self.stats['end_time'] = datetime.utcnow()
            
            logger.info("File data collection completed",
                       total_collected=self.stats['total_collected'],
                       valid_entries=self.stats['valid_entries'])
            
            return report
            
        except Exception as e:
            logger.error("File data collection failed", error=str(e))
            raise
    
    async def _process_training_data(self, raw_data: Dict[str, Any]) -> None:
        """
        Process raw data into training format
        
        Args:
            raw_data: Raw data from source
        """
        try:
            # Extract document data
            document_data = self._extract_document_data(raw_data)
            
            # Extract classification result
            classification_result = self._extract_classification_result(raw_data)
            
            # Extract ground truth (if available)
            true_classification = self._extract_ground_truth(raw_data)
            
            # Collect training data
            training_data = self.data_collector.collect_training_data(
                document_data, classification_result, true_classification
            )
            
            # Validate training data
            validation_result = self.validator.validate_training_data(training_data)
            
            # Store data
            self.training_data.append(training_data)
            self.validation_results.append(validation_result)
            
            # Update statistics
            self.stats['total_collected'] += 1
            if validation_result.is_valid:
                self.stats['valid_entries'] += 1
            else:
                self.stats['invalid_entries'] += 1
            
            # Update domain statistics
            domain = training_data['features'].domain
            self.stats['domains'][domain] = self.stats['domains'].get(domain, 0) + 1
            
            # Update classification statistics
            classification = training_data['outcome'].predicted_classification
            self.stats['classifications'][classification] = self.stats['classifications'].get(classification, 0) + 1
            
            # Update decision path statistics
            decision_path = training_data['outcome'].decision_path
            self.stats['decision_paths'][decision_path] = self.stats['decision_paths'].get(decision_path, 0) + 1
            
        except Exception as e:
            logger.error("Failed to process training data", error=str(e))
            self.stats['invalid_entries'] += 1
    
    def _extract_document_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract document data from raw input"""
        return {
            'title': raw_data.get('title', ''),
            'abstract': raw_data.get('abstract', ''),
            'mesh_terms': raw_data.get('mesh_terms', []),
            'publication_types': raw_data.get('publication_types', [])
        }
    
    def _extract_classification_result(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract classification result from raw input"""
        return {
            'ensemble_result': raw_data.get('classification', 'Unknown'),
            'confidence': raw_data.get('classification_confidence', 0.0),
            'reasoning': raw_data.get('reasoning', ''),
            'models_used': raw_data.get('models_used', ['rule_based']),
            'decision_path': raw_data.get('decision_path', 'rule_based_only'),
            'processing_time_ms': raw_data.get('processing_time_ms', 0),
            'cost_estimate': raw_data.get('cost_estimate', 0.0)
        }
    
    def _extract_ground_truth(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract ground truth classification if available"""
        return raw_data.get('true_classification')
    
    async def _simulate_data_collection(self, max_documents: int, batch_size: int) -> List[Dict[str, Any]]:
        """Simulate data collection from classification service"""
        logger.info("Simulating data collection", max_documents=max_documents)
        
        # This would be replaced with actual API calls to the classification service
        simulated_data = []
        
        for i in range(min(max_documents, 100)):  # Limit simulation to 100 documents
            # Simulate document data
            document_data = {
                'title': f'Simulated Document {i+1}',
                'abstract': f'This is a simulated abstract for document {i+1}. It contains medical terminology and case report information.',
                'mesh_terms': ['Case Reports', 'Drug-Related Side Effects and Adverse Reactions'],
                'publication_types': ['Case Report']
            }
            
            # Simulate classification result
            classification_result = {
                'classification': 'ICSR' if i % 3 == 0 else 'Non-ICSR',
                'classification_confidence': 0.8 + (i % 10) * 0.02,
                'reasoning': f'Simulated reasoning for document {i+1}',
                'models_used': ['rule_based'],
                'decision_path': 'rule_based_only',
                'processing_time_ms': 10 + (i % 5) * 2,
                'cost_estimate': 0.0
            }
            
            # Simulate ground truth
            true_classification = 'ICSR' if i % 4 == 0 else 'Non-ICSR'
            
            # Combine data
            combined_data = {
                **document_data,
                **classification_result,
                'true_classification': true_classification
            }
            
            simulated_data.append(combined_data)
            
            # Simulate processing delay
            await asyncio.sleep(0.01)
        
        return simulated_data
    
    async def _simulate_elasticsearch_collection(self, max_documents: int) -> List[Dict[str, Any]]:
        """Simulate data collection from Elasticsearch"""
        logger.info("Simulating Elasticsearch data collection", max_documents=max_documents)
        
        # This would be replaced with actual Elasticsearch queries
        simulated_data = []
        
        for i in range(min(max_documents, 50)):  # Limit simulation to 50 documents
            # Simulate document from Elasticsearch
            document_data = {
                'title': f'Elasticsearch Document {i+1}',
                'abstract': f'This document was retrieved from Elasticsearch index. It contains medical case information.',
                'mesh_terms': ['Pharmacovigilance', 'Adverse Drug Reaction Reporting Systems'],
                'publication_types': ['Case Report']
            }
            
            # Simulate classification result
            classification_result = {
                'classification': 'ICSR' if i % 2 == 0 else 'Safety_Information',
                'classification_confidence': 0.75 + (i % 8) * 0.03,
                'reasoning': f'Elasticsearch document {i+1} classification reasoning',
                'models_used': ['rule_based', 'bert'],
                'decision_path': 'rule_based_and_bert',
                'processing_time_ms': 50 + (i % 10) * 5,
                'cost_estimate': 0.002
            }
            
            # Simulate ground truth
            true_classification = 'ICSR' if i % 3 == 0 else 'Safety_Information'
            
            # Combine data
            combined_data = {
                **document_data,
                **classification_result,
                'true_classification': true_classification
            }
            
            simulated_data.append(combined_data)
            
            # Simulate processing delay
            await asyncio.sleep(0.02)
        
        return simulated_data
    
    def _generate_collection_report(self) -> Dict[str, Any]:
        """Generate collection report"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Calculate quality metrics
        valid_rate = self.stats['valid_entries'] / max(self.stats['total_collected'], 1)
        
        # Calculate average quality score
        quality_scores = [r.quality_score for r in self.validation_results if r.quality_score > 0]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        report = {
            'collection_summary': {
                'total_collected': self.stats['total_collected'],
                'valid_entries': self.stats['valid_entries'],
                'invalid_entries': self.stats['invalid_entries'],
                'valid_rate': valid_rate,
                'avg_quality_score': avg_quality_score,
                'duration_seconds': duration
            },
            'domain_distribution': self.stats['domains'],
            'classification_distribution': self.stats['classifications'],
            'decision_path_distribution': self.stats['decision_paths'],
            'quality_analysis': self._analyze_quality(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _analyze_quality(self) -> Dict[str, Any]:
        """Analyze data quality"""
        if not self.validation_results:
            return {}
        
        # Count issues and warnings
        total_issues = sum(len(r.issues) for r in self.validation_results)
        total_warnings = sum(len(r.warnings) for r in self.validation_results)
        
        # Most common issues
        issue_counts = {}
        for result in self.validation_results:
            for issue in result.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        most_common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_issues': total_issues,
            'total_warnings': total_warnings,
            'avg_issues_per_entry': total_issues / len(self.validation_results),
            'avg_warnings_per_entry': total_warnings / len(self.validation_results),
            'most_common_issues': most_common_issues
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on collection results"""
        recommendations = []
        
        # Quality recommendations
        valid_rate = self.stats['valid_entries'] / max(self.stats['total_collected'], 1)
        if valid_rate < 0.8:
            recommendations.append("Data quality is low - consider improving data collection process")
        
        # Size recommendations
        if self.stats['total_collected'] < 100:
            recommendations.append("Dataset is small - collect more data for better RL training")
        
        # Balance recommendations
        total = self.stats['total_collected']
        for classification, count in self.stats['classifications'].items():
            if count / total < 0.1:
                recommendations.append(f"Consider collecting more {classification} examples for better balance")
        
        # Domain recommendations
        if len(self.stats['domains']) < 3:
            recommendations.append("Consider collecting data from more diverse medical domains")
        
        return recommendations
    
    async def _save_collection_data(self) -> None:
        """Save collected data to files"""
        # Save training data
        training_data_file = self.output_dir / f"training_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert dataclasses to dictionaries for JSON serialization
        serializable_data = []
        for entry in self.training_data:
            serializable_entry = {
                'features': {
                    'title': entry['features'].title,
                    'abstract': entry['features'].abstract,
                    'mesh_terms': entry['features'].mesh_terms,
                    'publication_types': entry['features'].publication_types,
                    'word_count': entry['features'].word_count,
                    'sentence_count': entry['features'].sentence_count,
                    'technical_term_count': entry['features'].technical_term_count,
                    'medical_term_count': entry['features'].medical_term_count,
                    'patient_mentions': entry['features'].patient_mentions,
                    'drug_mentions': entry['features'].drug_mentions,
                    'adverse_event_mentions': entry['features'].adverse_event_mentions,
                    'temporal_mentions': entry['features'].temporal_mentions,
                    'icsr_mesh_count': entry['features'].icsr_mesh_count,
                    'non_icsr_mesh_count': entry['features'].non_icsr_mesh_count,
                    'rejected_signals': entry['features'].rejected_signals,
                    'domain': entry['features'].domain,
                    'complexity_score': entry['features'].complexity_score,
                    'confidence_indicators': entry['features'].confidence_indicators,
                    'extracted_at': entry['features'].extracted_at.isoformat()
                },
                'outcome': {
                    'true_classification': entry['outcome'].true_classification,
                    'predicted_classification': entry['outcome'].predicted_classification,
                    'confidence': entry['outcome'].confidence,
                    'reasoning': entry['outcome'].reasoning,
                    'models_used': entry['outcome'].models_used,
                    'decision_path': entry['outcome'].decision_path,
                    'processing_time_ms': entry['outcome'].processing_time_ms,
                    'cost_estimate': entry['outcome'].cost_estimate,
                    'is_correct': entry['outcome'].is_correct,
                    'confidence_penalty': entry['outcome'].confidence_penalty,
                    'cost_efficiency': entry['outcome'].cost_efficiency,
                    'classified_at': entry['outcome'].classified_at.isoformat()
                },
                'collected_at': entry['collected_at'].isoformat(),
                'data_id': entry['data_id']
            }
            serializable_data.append(serializable_entry)
        
        with open(training_data_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        # Save validation results
        validation_file = self.output_dir / f"validation_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        validation_data = []
        for result in self.validation_results:
            validation_data.append({
                'is_valid': result.is_valid,
                'quality_score': result.quality_score,
                'issues': result.issues,
                'warnings': result.warnings,
                'recommendations': result.recommendations,
                'statistics': result.statistics
            })
        
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        # Save collection report
        report_file = self.output_dir / f"collection_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report = self._generate_collection_report()
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Collection data saved",
                   training_data_file=str(training_data_file),
                   validation_file=str(validation_file),
                   report_file=str(report_file))
    
    def get_training_data_summary(self) -> Dict[str, Any]:
        """Get summary of collected training data"""
        if not self.training_data:
            return {}
        
        # Calculate basic statistics
        total_entries = len(self.training_data)
        valid_entries = sum(1 for r in self.validation_results if r.is_valid)
        
        # Calculate accuracy
        correct_predictions = sum(1 for entry in self.training_data if entry['outcome'].is_correct)
        accuracy = correct_predictions / total_entries if total_entries > 0 else 0
        
        # Calculate average confidence
        confidences = [entry['outcome'].confidence for entry in self.training_data]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Calculate average processing time
        processing_times = [entry['outcome'].processing_time_ms for entry in self.training_data]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Calculate average cost
        costs = [entry['outcome'].cost_estimate for entry in self.training_data]
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'avg_processing_time_ms': avg_processing_time,
            'avg_cost': avg_cost,
            'domain_distribution': self.stats['domains'],
            'classification_distribution': self.stats['classifications'],
            'decision_path_distribution': self.stats['decision_paths']
        }


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Test the data collection orchestrator
        orchestrator = RLDataCollectionOrchestrator()
        
        # Test simulation
        print("Testing data collection simulation...")
        report = await orchestrator.collect_from_classification_service(
            "http://localhost:8012",
            max_documents=50,
            batch_size=10
        )
        
        print("\nCollection Report:")
        print(f"Total collected: {report['collection_summary']['total_collected']}")
        print(f"Valid entries: {report['collection_summary']['valid_entries']}")
        print(f"Valid rate: {report['collection_summary']['valid_rate']:.2%}")
        print(f"Average quality score: {report['collection_summary']['avg_quality_score']:.2f}")
        
        print("\nDomain Distribution:")
        for domain, count in report['domain_distribution'].items():
            print(f"  {domain}: {count}")
        
        print("\nClassification Distribution:")
        for classification, count in report['classification_distribution'].items():
            print(f"  {classification}: {count}")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    # Run the test
    asyncio.run(main())
