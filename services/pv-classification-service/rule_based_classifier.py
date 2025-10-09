"""
Rule-Based PV Classifier
Fast pre-filter using heuristics, MeSH terms, and publication types
"""

import re
from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class RuleBasedClassifier:
    """
    Fast rule-based classifier for obvious PV classification cases
    Uses MeSH terms, publication types, and keyword patterns
    """
    
    # ICH E2D ICSR keywords
    ICSR_KEYWORDS = {
        'patient': ['patient', 'case report', 'year-old', 'month-old', 'male', 'female', 
                   'diagnosed with', 'presented with', 'developed', 'experienced'],
        'drug': ['administered', 'prescribed', 'treatment with', 'therapy with', 'received', 
                'medication', 'dose', 'dosage', 'mg', 'tablet', 'injection'],
        'adverse_event': ['adverse', 'reaction', 'side effect', 'toxicity', 'complication',
                         'injury', 'death', 'hospitalization', 'discontinued', 'withdrawn'],
        'temporal': ['after', 'following', 'within', 'days', 'weeks', 'months', 'onset',
                    'duration', 'rechallenge', 'dechallenge']
    }
    
    # MeSH terms strongly associated with ICSRs
    ICSR_MESH_TERMS = {
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
    
    # MeSH terms that indicate non-ICSR
    NON_ICSR_MESH_TERMS = {
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
    
    # Publication types
    ICSR_PUBLICATION_TYPES = {
        'Case Reports',
        'Letter',
        'Case Report'
    }
    
    NON_ICSR_PUBLICATION_TYPES = {
        'Meta-Analysis',
        'Randomized Controlled Trial',
        'Clinical Trial',
        'Multicenter Study',
        'Review',
        'Systematic Review'
    }
    
    REJECTED_KEYWORDS = [
        'in vitro', 'in vivo', 'animal model', 'cell culture', 'molecular docking',
        'computational', 'simulation', 'protein structure', 'crystal structure',
        'genetic polymorphism', 'pharmacokinetics study'
    ]
    
    def __init__(self):
        logger.info("Rule-based classifier initialized")
    
    def classify(
        self, 
        title: str, 
        abstract: Optional[str] = None,
        mesh_terms: Optional[List[str]] = None,
        publication_types: Optional[List[str]] = None
    ) -> Tuple[str, float, str, Dict[str, int]]:
        """
        Classify a document using rule-based heuristics
        
        Returns:
            (classification, confidence, reasoning, evidence_scores)
        """
        text = f"{title} {abstract or ''}".lower()
        mesh_set = set(mesh_terms or [])
        pub_types = set(publication_types or [])
        
        # Calculate evidence scores
        evidence = self._calculate_evidence(text, mesh_set, pub_types)
        
        logger.debug("Rule-based evidence", evidence=evidence)
        
        # Decision logic
        classification, confidence, reasoning = self._make_decision(evidence, mesh_set, pub_types)
        
        return classification, confidence, reasoning, evidence
    
    def _calculate_evidence(
        self, 
        text: str, 
        mesh_set: set, 
        pub_types: set
    ) -> Dict[str, int]:
        """Calculate evidence scores for each category"""
        
        evidence = {
            'patient_mentions': 0,
            'drug_mentions': 0,
            'adverse_event_mentions': 0,
            'temporal_mentions': 0,
            'icsr_mesh_count': 0,
            'non_icsr_mesh_count': 0,
            'rejected_signals': 0
        }
        
        # Count keyword occurrences
        for keyword in self.ICSR_KEYWORDS['patient']:
            evidence['patient_mentions'] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        
        for keyword in self.ICSR_KEYWORDS['drug']:
            evidence['drug_mentions'] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        
        for keyword in self.ICSR_KEYWORDS['adverse_event']:
            evidence['adverse_event_mentions'] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        
        for keyword in self.ICSR_KEYWORDS['temporal']:
            evidence['temporal_mentions'] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        
        # Count MeSH term matches
        evidence['icsr_mesh_count'] = len(mesh_set & self.ICSR_MESH_TERMS)
        evidence['non_icsr_mesh_count'] = len(mesh_set & self.NON_ICSR_MESH_TERMS)
        
        # Check for rejection signals
        for keyword in self.REJECTED_KEYWORDS:
            if keyword in text:
                evidence['rejected_signals'] += 1
        
        return evidence
    
    def _make_decision(
        self, 
        evidence: Dict[str, int],
        mesh_set: set,
        pub_types: set
    ) -> Tuple[str, float, str]:
        """
        Make classification decision based on evidence
        
        Returns:
            (classification, confidence, reasoning)
        """
        
        # HIGH CONFIDENCE ICSR RULES
        # Rule 1: Case Report publication type + ICSR MeSH terms
        if (pub_types & self.ICSR_PUBLICATION_TYPES) and evidence['icsr_mesh_count'] >= 1:
            if evidence['patient_mentions'] >= 2 and evidence['adverse_event_mentions'] >= 1:
                return (
                    "ICSR",
                    0.95,
                    "High confidence: Case Report publication type with ICSR MeSH terms and clear patient-drug-event narrative"
                )
        
        # Rule 2: Strong ICSR signals
        if (evidence['patient_mentions'] >= 3 and 
            evidence['drug_mentions'] >= 2 and 
            evidence['adverse_event_mentions'] >= 2 and
            evidence['temporal_mentions'] >= 1):
            return (
                "ICSR",
                0.90,
                "High confidence: Strong presence of all four ICSR elements (patient, drug, event, temporal)"
            )
        
        # HIGH CONFIDENCE NON-ICSR RULES
        # Rule 3: Review or RCT publication types
        if pub_types & self.NON_ICSR_PUBLICATION_TYPES:
            return (
                "Non-ICSR",
                0.95,
                "High confidence: Publication type indicates systematic review or clinical trial, not individual case report"
            )
        
        # Rule 4: Strong non-ICSR signals
        if evidence['non_icsr_mesh_count'] >= 2:
            return (
                "Non-ICSR",
                0.88,
                "High confidence: Multiple non-ICSR MeSH terms suggest research study or review article"
            )
        
        # HIGH CONFIDENCE REJECTED RULES
        # Rule 5: In vitro/animal studies
        if evidence['rejected_signals'] >= 2:
            return (
                "Rejected",
                0.92,
                "High confidence: Multiple signals indicate non-clinical research (in vitro, animal models, computational)"
            )
        
        # MEDIUM CONFIDENCE ICSR RULES
        # Rule 6: Moderate ICSR evidence
        if (evidence['patient_mentions'] >= 1 and 
            evidence['adverse_event_mentions'] >= 1 and
            evidence['drug_mentions'] >= 1):
            return (
                "ICSR",
                0.70,
                "Medium confidence: Presence of patient, drug, and adverse event mentions suggest possible ICSR"
            )
        
        # MEDIUM CONFIDENCE SAFETY INFO RULES
        # Rule 7: Safety-related but no patient details
        if evidence['adverse_event_mentions'] >= 2 and evidence['patient_mentions'] == 0:
            return (
                "Safety_Information",
                0.75,
                "Medium confidence: Discusses adverse events but lacks identifiable patient information"
            )
        
        # LOW CONFIDENCE - DEFER TO ML MODELS
        # Rule 8: Insufficient evidence
        return (
            "Non-ICSR",
            0.50,
            "Low confidence: Insufficient rule-based evidence, defer to ML models for better classification"
        )
    
    def should_use_ml(self, confidence: float, threshold: float = 0.85) -> bool:
        """
        Determine if ML models should be consulted
        
        Args:
            confidence: Rule-based confidence score
            threshold: Confidence threshold below which ML is needed
            
        Returns:
            True if ML models should be used
        """
        return confidence < threshold


# Singleton instance
rule_based_classifier = RuleBasedClassifier()

