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
        'adverse_event': [
            # General terms
            'adverse', 'reaction', 'side effect', 'toxicity', 'complication',
            'injury', 'death', 'hospitalization', 'discontinued', 'withdrawn',
            # Specific adverse events
            'anaphylaxis', 'anaphylactic', 'rash', 'urticaria', 'angioedema',
            'hepatotoxicity', 'liver injury', 'nephrotoxicity', 'kidney injury',
            'cardiotoxicity', 'arrhythmia', 'stevens-johnson', 'dress syndrome',
            'rhabdomyolysis', 'seizure', 'hypersensitivity', 'allergy', 'allergic',
            'dermatitis', 'exanthema', 'pruritus', 'nausea', 'vomiting', 'diarrhea',
            'headache', 'dizziness', 'fatigue', 'fever', 'chills'
        ],
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
    
    # MeSH terms for Safety_Information
    SAFETY_INFO_MESH_TERMS = {
        'Pharmacovigilance',
        'Drug Safety',
        'Product Surveillance, Postmarketing',
        'Adverse Drug Reaction Reporting Systems',
        'Clinical Trials, Phase I',
        'Clinical Trials, Phase II',
        'Clinical Trials, Phase III',
        'Clinical Trials, Phase IV',
        'Meta-Analysis',
        'Systematic Review',
        'Risk Assessment',
        'Drug Monitoring',
        'Safety Management',
        'Drug Toxicity',
        'Observational Study'
    }
    
    # MeSH terms that indicate non-ICSR
    NON_ICSR_MESH_TERMS = {
        'Animals',
        'In Vitro Techniques',
        'Cell Line',
        'Molecular Structure',
        'Review Literature'
    }
    
    # Publication types
    ICSR_PUBLICATION_TYPES = {
        'Case Reports',
        'Letter',
        'Case Report'
    }
    
    SAFETY_INFO_PUBLICATION_TYPES = {
        'Clinical Trial',
        'Clinical Trial, Phase I',
        'Clinical Trial, Phase II',
        'Clinical Trial, Phase III',
        'Clinical Trial, Phase IV',
        'Meta-Analysis',
        'Systematic Review',
        'Observational Study',
        'Cohort Study',
        'Multicenter Study',
        'Randomized Controlled Trial'
    }
    
    NON_ICSR_PUBLICATION_TYPES = {
        'Review',
        'Guideline',
        'Practice Guideline',
        'Research Support'
    }
    
    # Safety_Information keywords
    SAFETY_INFO_KEYWORDS = [
        'safety profile', 'safety analysis', 'safety data', 'tolerability',
        'safety and efficacy', 'post-marketing', 'surveillance',
        'pharmacovigilance', 'risk assessment', 'safety monitoring',
        'clinical trial safety', 'adverse events', 'safety study'
    ]
    
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
            'safety_info_mesh_count': 0,
            'safety_info_keywords': 0,
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
        evidence['safety_info_mesh_count'] = len(mesh_set & self.SAFETY_INFO_MESH_TERMS)
        
        # Count safety_info keywords
        for keyword in self.SAFETY_INFO_KEYWORDS:
            if keyword in text:
                evidence['safety_info_keywords'] += 1
        
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
        Priority order: Rejected > ICSR > Safety_Information > Non-ICSR
        
        Returns:
            (classification, confidence, reasoning)
        """
        
        # ============================================================================
        # PRIORITY 1: REJECTED RULES (Check first to filter out invalid documents)
        # ============================================================================
        
        # Rule R1: Retracted publications
        if any('RETRACT' in str(term).upper() for term in mesh_set):
            return (
                "Rejected",
                0.95,
                "High confidence: Retracted publication detected via MeSH terms"
            )
        
        # Rule R2: Duplicate publications
        if any('DUPLICATE' in str(term).upper() for term in mesh_set):
            return (
                "Rejected",
                0.95,
                "High confidence: Duplicate publication detected"
            )
        
        # Rule R3: In vitro/animal studies (non-clinical)
        if evidence['rejected_signals'] >= 2:
            return (
                "Rejected",
                0.90,
                "High confidence: Multiple signals indicate non-clinical research (in vitro, animal models, computational)"
            )
        
        # ============================================================================
        # PRIORITY 2: ICSR RULES (Individual case safety reports)
        # ============================================================================
        
        # Rule I1: Case Report publication type + ICSR evidence
        # PRIORITIZE Case Reports even if other publication types present
        if pub_types & self.ICSR_PUBLICATION_TYPES:
            # Check if this is truly a case report (not just a review mentioning cases)
            if evidence['icsr_mesh_count'] >= 1 or (
                evidence['patient_mentions'] >= 2 and 
                evidence['adverse_event_mentions'] >= 1
            ):
                return (
                    "ICSR",
                    0.95,
                    "High confidence: Case Report publication type with ICSR evidence"
                )
        
        # Rule I2: Strong ICSR signals (all four elements present)
        if (evidence['patient_mentions'] >= 3 and 
            evidence['drug_mentions'] >= 2 and 
            evidence['adverse_event_mentions'] >= 2 and
            evidence['temporal_mentions'] >= 1):
            return (
                "ICSR",
                0.90,
                "High confidence: Strong presence of all four ICSR elements (patient, drug, event, temporal)"
            )
        
        # Rule I3: Moderate ICSR evidence
        if (evidence['patient_mentions'] >= 1 and 
            evidence['adverse_event_mentions'] >= 1 and
            evidence['drug_mentions'] >= 1):
            return (
                "ICSR",
                0.70,
                "Medium confidence: Presence of patient, drug, and adverse event mentions suggest possible ICSR"
            )
        
        # ============================================================================
        # PRIORITY 3: SAFETY_INFORMATION RULES (Aggregate safety data)
        # ============================================================================
        
        # Rule S1: Clinical trial or meta-analysis with safety focus
        if (pub_types & self.SAFETY_INFO_PUBLICATION_TYPES) and (
            evidence['safety_info_keywords'] >= 2 or 
            evidence['safety_info_mesh_count'] >= 1
        ):
            return (
                "Safety_Information",
                0.85,
                "High confidence: Clinical trial/meta-analysis with safety focus"
            )
        
        # Rule S2: Pharmacovigilance/surveillance study
        if evidence['safety_info_mesh_count'] >= 2:
            return (
                "Safety_Information",
                0.80,
                "High confidence: Multiple pharmacovigilance/safety MeSH terms"
            )
        
        # Rule S3: Safety keywords without individual case
        if (evidence['safety_info_keywords'] >= 3 and 
            evidence['patient_mentions'] < 2):
            return (
                "Safety_Information",
                0.75,
                "Moderate confidence: Safety-focused content without individual case reports"
            )
        
        # Rule S4: Safety-related adverse events but no patient details
        if evidence['adverse_event_mentions'] >= 2 and evidence['patient_mentions'] == 0:
            return (
                "Safety_Information",
                0.70,
                "Moderate confidence: Discusses adverse events but lacks identifiable patient information"
            )
        
        # ============================================================================
        # PRIORITY 4: NON-ICSR RULES (Reviews, mechanistic studies, etc.)
        # ============================================================================
        
        # Rule N1: Review or guideline publication types
        if pub_types & self.NON_ICSR_PUBLICATION_TYPES:
            return (
                "Non-ICSR",
                0.90,
                "High confidence: Publication type indicates review or guideline, not case report or safety study"
            )
        
        # Rule N2: Strong non-ICSR signals
        if evidence['non_icsr_mesh_count'] >= 2:
            return (
                "Non-ICSR",
                0.85,
                "High confidence: Multiple non-ICSR MeSH terms suggest research study or review article"
            )
        
        # ============================================================================
        # DEFAULT: LOW CONFIDENCE - DEFER TO ML MODELS
        # ============================================================================
        
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


