"""
Neo4j Knowledge Graph Schema Definition
Supports medical and legal domain entities with cross-source consolidation
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class Neo4jSchema:
    """Defines the knowledge graph schema for medical and legal domains"""
    
    # Medical Entity Types
    MEDICAL_ENTITIES = {
        "DRUG": {
            "label": "Drug",
            "properties": {
                "name": "string",
                "generic_name": "string", 
                "brand_names": "string[]",
                "drug_class": "string",
                "mechanism_of_action": "string",
                "indications": "string[]",
                "contraindications": "string[]",
                "side_effects": "string[]",
                "dosage_forms": "string[]",
                "route_of_administration": "string[]",
                "fda_approval_date": "date",
                "fda_approval_indication": "string",
                "patent_expiry": "date",
                "manufacturer": "string",
                "atc_code": "string",
                "cas_number": "string",
                "molecular_formula": "string",
                "molecular_weight": "float",
                "half_life": "string",
                "bioavailability": "string",
                "protein_binding": "string",
                "metabolism": "string",
                "excretion": "string",
                "pregnancy_category": "string",
                "breastfeeding_safety": "string",
                "pediatric_use": "string",
                "geriatric_use": "string",
                "hepatic_impairment": "string",
                "renal_impairment": "string",
                "black_box_warnings": "string[]",
                "boxed_warnings": "string[]",
                "recall_history": "string[]",
                "adverse_events_count": "integer",
                "clinical_trials_count": "integer",
                "publications_count": "integer",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "DISEASE": {
            "label": "Disease", 
            "properties": {
                "name": "string",
                "synonyms": "string[]",
                "icd10_codes": "string[]",
                "icd11_codes": "string[]",
                "snomed_codes": "string[]",
                "disease_category": "string",
                "pathophysiology": "string",
                "symptoms": "string[]",
                "signs": "string[]",
                "diagnostic_criteria": "string[]",
                "differential_diagnosis": "string[]",
                "complications": "string[]",
                "prognosis": "string",
                "epidemiology": "string",
                "risk_factors": "string[]",
                "prevention": "string[]",
                "screening_tests": "string[]",
                "severity_stages": "string[]",
                "age_of_onset": "string",
                "gender_prevalence": "string",
                "ethnicity_prevalence": "string",
                "geographic_distribution": "string[]",
                "seasonal_patterns": "string",
                "mortality_rate": "float",
                "morbidity_rate": "float",
                "prevalence": "float",
                "incidence": "float",
                "heritability": "float",
                "environmental_factors": "string[]",
                "genetic_factors": "string[]",
                "infectious_agents": "string[]",
                "autoimmune_components": "boolean",
                "cancer_related": "boolean",
                "rare_disease": "boolean",
                "orphan_disease": "boolean",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "SYMPTOM": {
            "label": "Symptom",
            "properties": {
                "name": "string",
                "description": "string",
                "severity_levels": "string[]",
                "duration_patterns": "string[]",
                "triggers": "string[]",
                "relieving_factors": "string[]",
                "associated_conditions": "string[]",
                "differential_diagnosis": "string[]",
                "measurement_scales": "string[]",
                "patient_reported": "boolean",
                "clinician_observed": "boolean",
                "objective_measures": "string[]",
                "subjective_measures": "string[]",
                "quality_of_life_impact": "string",
                "work_impact": "string",
                "social_impact": "string",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "PROCEDURE": {
            "label": "Procedure",
            "properties": {
                "name": "string",
                "description": "string",
                "cpt_codes": "string[]",
                "icd10_pcs_codes": "string[]",
                "procedure_type": "string",
                "body_system": "string",
                "body_part": "string",
                "approach": "string",
                "technique": "string",
                "equipment": "string[]",
                "anesthesia_required": "boolean",
                "inpatient": "boolean",
                "outpatient": "boolean",
                "emergency": "boolean",
                "elective": "boolean",
                "diagnostic": "boolean",
                "therapeutic": "boolean",
                "preventive": "boolean",
                "palliative": "boolean",
                "cosmetic": "boolean",
                "experimental": "boolean",
                "minimally_invasive": "boolean",
                "robotic": "boolean",
                "laparoscopic": "boolean",
                "endoscopic": "boolean",
                "duration_minutes": "integer",
                "recovery_time": "string",
                "success_rate": "float",
                "complication_rate": "float",
                "mortality_rate": "float",
                "indications": "string[]",
                "contraindications": "string[]",
                "risks": "string[]",
                "benefits": "string[]",
                "alternatives": "string[]",
                "cost": "float",
                "insurance_coverage": "string",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "TRIAL": {
            "label": "ClinicalTrial",
            "properties": {
                "nct_id": "string",
                "title": "string",
                "description": "string",
                "phase": "string",
                "status": "string",
                "study_type": "string",
                "allocation": "string",
                "intervention_model": "string",
                "primary_purpose": "string",
                "masking": "string",
                "enrollment": "integer",
                "actual_enrollment": "integer",
                "start_date": "date",
                "completion_date": "date",
                "primary_completion_date": "date",
                "study_completion_date": "date",
                "primary_endpoint": "string",
                "secondary_endpoints": "string[]",
                "inclusion_criteria": "string[]",
                "exclusion_criteria": "string[]",
                "age_min": "integer",
                "age_max": "integer",
                "gender": "string",
                "healthy_volunteers": "boolean",
                "sponsor": "string",
                "collaborators": "string[]",
                "investigators": "string[]",
                "locations": "string[]",
                "countries": "string[]",
                "funding_source": "string",
                "results_available": "boolean",
                "publications": "string[]",
                "outcome_measures": "string[]",
                "adverse_events": "string[]",
                "serious_adverse_events": "string[]",
                "efficacy_results": "string",
                "safety_results": "string",
                "statistical_significance": "boolean",
                "p_value": "float",
                "confidence_interval": "string",
                "effect_size": "float",
                "number_needed_to_treat": "float",
                "number_needed_to_harm": "float",
                "hazard_ratio": "float",
                "odds_ratio": "float",
                "relative_risk": "float",
                "absolute_risk_reduction": "float",
                "relative_risk_reduction": "float",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "ORGANIZATION": {
            "label": "Organization",
            "properties": {
                "name": "string",
                "type": "string",
                "subtype": "string",
                "description": "string",
                "website": "string",
                "headquarters": "string",
                "countries": "string[]",
                "founded_year": "integer",
                "size": "string",
                "revenue": "float",
                "employees": "integer",
                "stock_symbol": "string",
                "parent_company": "string",
                "subsidiaries": "string[]",
                "accreditations": "string[]",
                "certifications": "string[]",
                "licenses": "string[]",
                "regulatory_approvals": "string[]",
                "patents": "string[]",
                "products": "string[]",
                "services": "string[]",
                "research_areas": "string[]",
                "specializations": "string[]",
                "awards": "string[]",
                "recognition": "string[]",
                "controversies": "string[]",
                "legal_issues": "string[]",
                "regulatory_actions": "string[]",
                "recalls": "string[]",
                "fines": "float",
                "settlements": "float",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "PERSON": {
            "label": "Person",
            "properties": {
                "name": "string",
                "first_name": "string",
                "last_name": "string",
                "middle_name": "string",
                "suffix": "string",
                "title": "string",
                "credentials": "string[]",
                "specialties": "string[]",
                "expertise_areas": "string[]",
                "affiliations": "string[]",
                "institutions": "string[]",
                "departments": "string[]",
                "positions": "string[]",
                "education": "string[]",
                "degrees": "string[]",
                "certifications": "string[]",
                "licenses": "string[]",
                "publications": "integer",
                "citations": "integer",
                "h_index": "integer",
                "research_interests": "string[]",
                "clinical_interests": "string[]",
                "awards": "string[]",
                "honors": "string[]",
                "grants": "string[]",
                "patents": "string[]",
                "clinical_trials": "string[]",
                "speaking_engagements": "string[]",
                "media_appearances": "string[]",
                "social_media": "string[]",
                "contact_info": "string",
                "location": "string",
                "country": "string",
                "languages": "string[]",
                "gender": "string",
                "ethnicity": "string",
                "age_range": "string",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        }
    }
    
    # Legal Entity Types
    LEGAL_ENTITIES = {
        "CASE": {
            "label": "LegalCase",
            "properties": {
                "case_number": "string",
                "title": "string",
                "description": "string",
                "case_type": "string",
                "jurisdiction": "string",
                "court": "string",
                "judge": "string",
                "status": "string",
                "filing_date": "date",
                "trial_date": "date",
                "settlement_date": "date",
                "verdict_date": "date",
                "closing_date": "date",
                "outcome": "string",
                "damages_awarded": "float",
                "settlement_amount": "float",
                "legal_fees": "float",
                "plaintiffs": "string[]",
                "defendants": "string[]",
                "attorneys": "string[]",
                "witnesses": "string[]",
                "expert_witnesses": "string[]",
                "legal_issues": "string[]",
                "causes_of_action": "string[]",
                "defenses": "string[]",
                "evidence": "string[]",
                "precedents": "string[]",
                "statutes": "string[]",
                "regulations": "string[]",
                "appeals": "string[]",
                "related_cases": "string[]",
                "media_coverage": "string[]",
                "public_interest": "boolean",
                "class_action": "boolean",
                "multidistrict_litigation": "boolean",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "STATUTE": {
            "label": "Statute",
            "properties": {
                "name": "string",
                "title": "string",
                "section": "string",
                "subsection": "string",
                "paragraph": "string",
                "text": "string",
                "summary": "string",
                "jurisdiction": "string",
                "level": "string",
                "category": "string",
                "effective_date": "date",
                "amendment_date": "date",
                "repeal_date": "date",
                "status": "string",
                "authority": "string",
                "purpose": "string",
                "scope": "string",
                "penalties": "string[]",
                "exceptions": "string[]",
                "definitions": "string[]",
                "requirements": "string[]",
                "prohibitions": "string[]",
                "rights": "string[]",
                "obligations": "string[]",
                "enforcement": "string",
                "regulations": "string[]",
                "guidance": "string[]",
                "interpretations": "string[]",
                "court_decisions": "string[]",
                "amendments": "string[]",
                "related_statutes": "string[]",
                "superseded_by": "string[]",
                "supersedes": "string[]",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "REGULATION": {
            "label": "Regulation",
            "properties": {
                "name": "string",
                "title": "string",
                "number": "string",
                "text": "string",
                "summary": "string",
                "agency": "string",
                "department": "string",
                "category": "string",
                "effective_date": "date",
                "compliance_date": "date",
                "sunset_date": "date",
                "status": "string",
                "purpose": "string",
                "scope": "string",
                "applicability": "string[]",
                "requirements": "string[]",
                "prohibitions": "string[]",
                "standards": "string[]",
                "procedures": "string[]",
                "documentation": "string[]",
                "reporting": "string[]",
                "record_keeping": "string[]",
                "training": "string[]",
                "monitoring": "string[]",
                "auditing": "string[]",
                "penalties": "string[]",
                "enforcement": "string",
                "exemptions": "string[]",
                "waivers": "string[]",
                "interpretations": "string[]",
                "guidance": "string[]",
                "amendments": "string[]",
                "related_regulations": "string[]",
                "superseded_by": "string[]",
                "supersedes": "string[]",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        }
    }
    
    # Document Types
    DOCUMENT_TYPES = {
        "RESEARCH_PAPER": {
            "label": "ResearchPaper",
            "properties": {
                "title": "string",
                "abstract": "string",
                "authors": "string[]",
                "journal": "string",
                "volume": "string",
                "issue": "string",
                "pages": "string",
                "publication_date": "date",
                "doi": "string",
                "pmid": "string",
                "pmcid": "string",
                "url": "string",
                "keywords": "string[]",
                "mesh_terms": "string[]",
                "study_type": "string",
                "methodology": "string",
                "sample_size": "integer",
                "population": "string",
                "intervention": "string",
                "outcomes": "string[]",
                "results": "string",
                "conclusions": "string",
                "limitations": "string[]",
                "funding": "string[]",
                "conflicts_of_interest": "string[]",
                "peer_reviewed": "boolean",
                "open_access": "boolean",
                "citation_count": "integer",
                "impact_factor": "float",
                "h_index": "integer",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "CLINICAL_TRIAL": {
            "label": "ClinicalTrial",
            "properties": {
                "nct_id": "string",
                "title": "string",
                "description": "string",
                "phase": "string",
                "status": "string",
                "study_type": "string",
                "enrollment": "integer",
                "start_date": "date",
                "completion_date": "date",
                "primary_endpoint": "string",
                "secondary_endpoints": "string[]",
                "sponsor": "string",
                "investigators": "string[]",
                "locations": "string[]",
                "results_available": "boolean",
                "publications": "string[]",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "FDA_DOCUMENT": {
            "label": "FDADocument",
            "properties": {
                "document_id": "string",
                "title": "string",
                "type": "string",
                "description": "string",
                "date": "date",
                "url": "string",
                "drug_name": "string",
                "manufacturer": "string",
                "indication": "string",
                "adverse_events": "string[]",
                "warnings": "string[]",
                "precautions": "string[]",
                "contraindications": "string[]",
                "dosage": "string",
                "administration": "string",
                "storage": "string",
                "handling": "string",
                "patient_counseling": "string[]",
                "clinical_pharmacology": "string",
                "nonclinical_toxicology": "string",
                "clinical_studies": "string[]",
                "how_supplied": "string",
                "storage_and_handling": "string",
                "patient_information": "string",
                "confidence_score": "float",
                "source_count": "integer",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        }
    }
    
    # Relationship Types
    RELATIONSHIPS = {
        # Medical Relationships
        "TREATS": {
            "description": "Drug treats disease/condition",
            "properties": {
                "efficacy": "float",
                "confidence": "float",
                "evidence_level": "string",
                "study_count": "integer",
                "patient_count": "integer",
                "response_rate": "float",
                "duration": "string",
                "dosage": "string",
                "route": "string",
                "indication": "string",
                "contraindication": "string",
                "warnings": "string[]",
                "side_effects": "string[]",
                "interactions": "string[]",
                "monitoring": "string[]",
                "cost": "float",
                "insurance_coverage": "string",
                "fda_approval": "boolean",
                "off_label": "boolean",
                "first_line": "boolean",
                "second_line": "boolean",
                "adjuvant": "boolean",
                "neoadjuvant": "boolean",
                "maintenance": "boolean",
                "palliative": "boolean",
                "curative": "boolean",
                "preventive": "boolean",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "CAUSES": {
            "description": "Drug/condition causes side effect/outcome",
            "properties": {
                "frequency": "float",
                "severity": "string",
                "confidence": "float",
                "evidence_level": "string",
                "mechanism": "string",
                "risk_factors": "string[]",
                "prevention": "string[]",
                "management": "string[]",
                "reversibility": "boolean",
                "dose_related": "boolean",
                "time_to_onset": "string",
                "duration": "string",
                "monitoring": "string[]",
                "contraindications": "string[]",
                "warnings": "string[]",
                "black_box": "boolean",
                "fda_warning": "boolean",
                "recall": "boolean",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "STUDIED_IN": {
            "description": "Drug/condition studied in clinical trial",
            "properties": {
                "phase": "string",
                "status": "string",
                "enrollment": "integer",
                "primary_endpoint": "string",
                "results": "string",
                "efficacy": "float",
                "safety": "string",
                "confidence": "float",
                "evidence_level": "string",
                "sponsor": "string",
                "investigators": "string[]",
                "locations": "string[]",
                "start_date": "date",
                "completion_date": "date",
                "publication_date": "date",
                "publications": "string[]",
                "regulatory_submission": "boolean",
                "fda_approval": "boolean",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "APPROVED_BY": {
            "description": "Drug approved by regulatory agency",
            "properties": {
                "agency": "string",
                "approval_date": "date",
                "indication": "string",
                "dosage": "string",
                "route": "string",
                "population": "string",
                "age_group": "string",
                "gender": "string",
                "conditions": "string[]",
                "restrictions": "string[]",
                "requirements": "string[]",
                "monitoring": "string[]",
                "post_marketing": "string[]",
                "label_changes": "string[]",
                "withdrawals": "string[]",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "ASSOCIATED_WITH": {
            "description": "Disease associated with symptom/condition",
            "properties": {
                "strength": "float",
                "frequency": "float",
                "confidence": "float",
                "evidence_level": "string",
                "mechanism": "string",
                "severity": "string",
                "progression": "string",
                "prognosis": "string",
                "risk_factors": "string[]",
                "protective_factors": "string[]",
                "complications": "string[]",
                "differential_diagnosis": "string[]",
                "diagnostic_criteria": "string[]",
                "screening": "string[]",
                "monitoring": "string[]",
                "treatment": "string[]",
                "prevention": "string[]",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "RESEARCHED_BY": {
            "description": "Person/organization researched topic",
            "properties": {
                "role": "string",
                "contribution": "string",
                "expertise": "string[]",
                "publications": "integer",
                "citations": "integer",
                "h_index": "integer",
                "funding": "string[]",
                "grants": "string[]",
                "patents": "string[]",
                "awards": "string[]",
                "collaborations": "string[]",
                "institutions": "string[]",
                "departments": "string[]",
                "positions": "string[]",
                "credentials": "string[]",
                "specialties": "string[]",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "CITED_IN": {
            "description": "Document cited in another document",
            "properties": {
                "citation_type": "string",
                "context": "string",
                "relevance": "float",
                "agreement": "boolean",
                "disagreement": "boolean",
                "supporting": "boolean",
                "contradicting": "boolean",
                "extending": "boolean",
                "refuting": "boolean",
                "methodology": "string",
                "results": "string",
                "conclusions": "string",
                "limitations": "string[]",
                "strengths": "string[]",
                "weaknesses": "string[]",
                "bias": "string[]",
                "conflicts_of_interest": "string[]",
                "funding": "string[]",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "SIMILAR_TO": {
            "description": "Entities are similar or related",
            "properties": {
                "similarity_score": "float",
                "similarity_type": "string",
                "shared_properties": "string[]",
                "differences": "string[]",
                "comparison": "string",
                "equivalence": "boolean",
                "substitution": "boolean",
                "alternative": "boolean",
                "precursor": "boolean",
                "successor": "boolean",
                "variant": "boolean",
                "isomer": "boolean",
                "metabolite": "boolean",
                "prodrug": "boolean",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "CONTRAINDICATED_WITH": {
            "description": "Drug contraindicated with condition/other drug",
            "properties": {
                "severity": "string",
                "risk_level": "string",
                "mechanism": "string",
                "interaction_type": "string",
                "clinical_significance": "string",
                "management": "string[]",
                "monitoring": "string[]",
                "alternatives": "string[]",
                "dose_adjustment": "string",
                "timing": "string",
                "duration": "string",
                "reversibility": "boolean",
                "fda_warning": "boolean",
                "black_box": "boolean",
                "recall": "boolean",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        },
        "ENHANCES": {
            "description": "Drug enhances effect of another drug",
            "properties": {
                "enhancement_type": "string",
                "magnitude": "float",
                "mechanism": "string",
                "clinical_significance": "string",
                "dose_adjustment": "string",
                "monitoring": "string[]",
                "benefits": "string[]",
                "risks": "string[]",
                "indications": "string[]",
                "contraindications": "string[]",
                "timing": "string",
                "duration": "string",
                "confidence": "float",
                "source_documents": "string[]",
                "last_updated": "datetime",
                "created_at": "datetime"
            }
        }
    }
    
    @classmethod
    def get_all_entity_types(cls) -> Dict[str, Dict]:
        """Get all entity types (medical + legal + documents)"""
        return {
            **cls.MEDICAL_ENTITIES,
            **cls.LEGAL_ENTITIES,
            **cls.DOCUMENT_TYPES
        }
    
    @classmethod
    def get_medical_entity_types(cls) -> Dict[str, Dict]:
        """Get medical entity types"""
        return cls.MEDICAL_ENTITIES
    
    @classmethod
    def get_legal_entity_types(cls) -> Dict[str, Dict]:
        """Get legal entity types"""
        return cls.LEGAL_ENTITIES
    
    @classmethod
    def get_document_types(cls) -> Dict[str, Dict]:
        """Get document types"""
        return cls.DOCUMENT_TYPES
    
    @classmethod
    def get_relationship_types(cls) -> Dict[str, Dict]:
        """Get relationship types"""
        return cls.RELATIONSHIPS
    
    @classmethod
    def create_schema_cypher(cls) -> List[str]:
        """Generate Cypher statements to create the schema"""
        statements = []
        
        # Create constraints and indexes for all entity types
        all_entities = cls.get_all_entity_types()
        
        for entity_type, config in all_entities.items():
            label = config["label"]
            
            # Create unique constraint on id
            statements.append(f"""
            CREATE CONSTRAINT {label.lower()}_id_unique IF NOT EXISTS
            FOR (n:{label}) REQUIRE n.id IS UNIQUE
            """)
            
            # Create index on name for search
            statements.append(f"""
            CREATE INDEX {label.lower()}_name_index IF NOT EXISTS
            FOR (n:{label}) ON (n.name)
            """)
            
            # Create index on type for filtering
            statements.append(f"""
            CREATE INDEX {label.lower()}_type_index IF NOT EXISTS
            FOR (n:{label}) ON (n.type)
            """)
            
            # Create index on confidence for ranking
            statements.append(f"""
            CREATE INDEX {label.lower()}_confidence_index IF NOT EXISTS
            FOR (n:{label}) ON (n.confidence_score)
            """)
            
            # Create index on source_count for popularity
            statements.append(f"""
            CREATE INDEX {label.lower()}_source_count_index IF NOT EXISTS
            FOR (n:{label}) ON (n.source_count)
            """)
        
        # Create indexes for relationships
        for rel_type, config in cls.RELATIONSHIPS.items():
            statements.append(f"""
            CREATE INDEX {rel_type.lower()}_confidence_index IF NOT EXISTS
            FOR ()-[r:{rel_type}]-() ON (r.confidence)
            """)
            
            statements.append(f"""
            CREATE INDEX {rel_type.lower()}_created_at_index IF NOT EXISTS
            FOR ()-[r:{rel_type}]-() ON (r.created_at)
            """)
        
        return statements
