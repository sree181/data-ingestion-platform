#!/usr/bin/env python3
"""
Comprehensive PV Classification Test Suite
Tests all classification classes and ensemble methodologies
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple
import time

# Configuration
PV_SERVICE_URL = "http://localhost:8012/api/v1/classify/ensemble"

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
MAGENTA = '\033[0;35m'
NC = '\033[0m'  # No Color

class ClassificationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def test_document(self, 
                     test_name: str,
                     document: Dict,
                     expected_class: str,
                     min_confidence: float = 0.7,
                     expected_models: List[str] = None) -> Dict:
        """Test a single document classification"""
        
        self.total_tests += 1
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{BLUE}Test #{self.total_tests}: {test_name}{NC}")
        print(f"{CYAN}{'='*80}{NC}")
        
        # Print document details
        print(f"\n{YELLOW}Document Details:{NC}")
        print(f"  Title: {document.get('title', 'N/A')[:80]}...")
        print(f"  MeSH Terms: {document.get('mesh_terms', [])[:3]}")
        print(f"  Publication Types: {document.get('publication_types', [])}")
        
        # Make classification request
        try:
            start_time = time.time()
            response = requests.post(
                PV_SERVICE_URL,
                json={"document": document},
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                print(f"{RED}✗ HTTP Error: {response.status_code}{NC}")
                self.failed_tests += 1
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
            
            result = response.json()
            classification = result.get('classification', {})
            ensemble_metadata = result.get('ensemble_metadata', {})
            
            # Extract results
            predicted_class = classification.get('classification', 'Unknown')
            confidence = classification.get('confidence', 0.0)
            reasoning = classification.get('reasoning', 'N/A')
            models_used = ensemble_metadata.get('models_used', [])
            decision_path = ensemble_metadata.get('decision_path', 'N/A')
            individual_results = ensemble_metadata.get('individual_results', {})
            
            # Print results
            print(f"\n{YELLOW}Classification Results:{NC}")
            print(f"  Predicted: {predicted_class}")
            print(f"  Confidence: {confidence:.3f}")
            print(f"  Expected: {expected_class}")
            print(f"  Models Used: {models_used}")
            print(f"  Decision Path: {decision_path}")
            print(f"  Processing Time: {elapsed_time:.3f}s")
            print(f"  Reasoning: {reasoning[:150]}...")
            
            # Print individual model results
            print(f"\n{YELLOW}Individual Model Results:{NC}")
            for model_name, model_result in individual_results.items():
                model_class = model_result.get('classification', 'N/A')
                model_conf = model_result.get('confidence', 0.0)
                print(f"  {model_name}: {model_class} ({model_conf:.3f})")
                
                # Print evidence for rule-based
                if model_name == 'rule_based' and 'evidence' in model_result:
                    evidence = model_result['evidence']
                    print(f"    Evidence:")
                    for key, value in evidence.items():
                        print(f"      - {key}: {value}")
            
            # Validate results
            class_match = predicted_class == expected_class
            confidence_ok = confidence >= min_confidence
            models_ok = True
            if expected_models:
                models_ok = all(m in models_used for m in expected_models)
            
            # Determine test status
            if class_match and confidence_ok and models_ok:
                print(f"\n{GREEN}✓ TEST PASSED{NC}")
                self.passed_tests += 1
                status = "passed"
            else:
                print(f"\n{RED}✗ TEST FAILED{NC}")
                if not class_match:
                    print(f"  {RED}× Classification mismatch: expected {expected_class}, got {predicted_class}{NC}")
                if not confidence_ok:
                    print(f"  {RED}× Low confidence: {confidence:.3f} < {min_confidence}{NC}")
                if not models_ok:
                    print(f"  {RED}× Expected models {expected_models} not all used{NC}")
                self.failed_tests += 1
                status = "failed"
            
            # Store result
            test_result = {
                "test_name": test_name,
                "status": status,
                "expected": expected_class,
                "predicted": predicted_class,
                "confidence": confidence,
                "models_used": models_used,
                "decision_path": decision_path,
                "processing_time": elapsed_time,
                "class_match": class_match,
                "confidence_ok": confidence_ok,
                "models_ok": models_ok
            }
            self.results.append(test_result)
            
            return test_result
            
        except Exception as e:
            print(f"{RED}✗ Exception: {str(e)}{NC}")
            self.failed_tests += 1
            return {"status": "failed", "error": str(e)}
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{MAGENTA}{'='*80}{NC}")
        print(f"{MAGENTA}TEST SUMMARY{NC}")
        print(f"{MAGENTA}{'='*80}{NC}\n")
        
        print(f"Total Tests: {self.total_tests}")
        print(f"{GREEN}Passed: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%){NC}")
        print(f"{RED}Failed: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%){NC}")
        
        # Classification breakdown
        print(f"\n{YELLOW}Classification Breakdown:{NC}")
        class_counts = {}
        for result in self.results:
            predicted = result.get('predicted', 'Unknown')
            class_counts[predicted] = class_counts.get(predicted, 0) + 1
        
        for class_name, count in sorted(class_counts.items()):
            print(f"  {class_name}: {count}")
        
        # Model usage
        print(f"\n{YELLOW}Model Usage:{NC}")
        model_counts = {}
        for result in self.results:
            models = result.get('models_used', [])
            for model in models:
                model_counts[model] = model_counts.get(model, 0) + 1
        
        for model_name, count in sorted(model_counts.items()):
            print(f"  {model_name}: {count} times")
        
        # Decision paths
        print(f"\n{YELLOW}Decision Paths:{NC}")
        path_counts = {}
        for result in self.results:
            path = result.get('decision_path', 'Unknown')
            path_counts[path] = path_counts.get(path, 0) + 1
        
        for path_name, count in sorted(path_counts.items()):
            print(f"  {path_name}: {count}")
        
        # Average metrics
        avg_confidence = sum(r.get('confidence', 0) for r in self.results) / len(self.results) if self.results else 0
        avg_time = sum(r.get('processing_time', 0) for r in self.results) / len(self.results) if self.results else 0
        
        print(f"\n{YELLOW}Average Metrics:{NC}")
        print(f"  Confidence: {avg_confidence:.3f}")
        print(f"  Processing Time: {avg_time:.3f}s")
        
        print(f"\n{MAGENTA}{'='*80}{NC}\n")


def main():
    """Run comprehensive classification tests"""
    
    print(f"{MAGENTA}{'='*80}{NC}")
    print(f"{MAGENTA}COMPREHENSIVE PV CLASSIFICATION TEST SUITE{NC}")
    print(f"{MAGENTA}{'='*80}{NC}")
    print(f"\nTesting Service: {PV_SERVICE_URL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tester = ClassificationTester()
    
    # ============================================================================
    # CATEGORY 1: ICSR (Individual Case Safety Reports)
    # ============================================================================
    
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}CATEGORY 1: ICSR (Individual Case Safety Reports){NC}")
    print(f"{CYAN}{'='*80}{NC}")
    
    # Test 1.1: Classic ICSR - Severe allergic reaction
    tester.test_document(
        test_name="ICSR - Severe Allergic Rash with Anaphylaxis",
        document={
            "id": "icsr_001",
            "title": "Severe allergic rash and anaphylaxis following penicillin administration: a case report",
            "abstract": "We report a case of a 45-year-old female patient who developed severe allergic rash with widespread urticaria and anaphylactic shock within 30 minutes of receiving intravenous penicillin for pneumonia. The patient presented with generalized erythema, angioedema, hypotension (BP 80/50), and respiratory distress. Treatment was discontinued immediately, and the patient received epinephrine, corticosteroids, and antihistamines. The patient recovered fully after 48 hours of intensive care.",
            "mesh_terms": ["Drug Hypersensitivity", "Anaphylaxis", "Urticaria", "Penicillins", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.85
    )
    
    # Test 1.2: ICSR - Stevens-Johnson Syndrome
    tester.test_document(
        test_name="ICSR - Stevens-Johnson Syndrome",
        document={
            "id": "icsr_002",
            "title": "Stevens-Johnson syndrome following amoxicillin therapy: a case report",
            "abstract": "A 32-year-old male patient developed Stevens-Johnson syndrome 7 days after starting amoxicillin 500mg TID for sinusitis. The patient presented with fever (39.2°C), widespread erythematous rash covering 25% of body surface area, mucosal involvement (oral and ocular), and skin detachment. Amoxicillin was immediately discontinued. The patient was hospitalized for supportive care including IV fluids, wound care, and pain management. Recovery occurred over 3 weeks with residual scarring.",
            "mesh_terms": ["Stevens-Johnson Syndrome", "Amoxicillin", "Drug Eruptions", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.85
    )
    
    # Test 1.3: ICSR - Drug-induced hepatotoxicity
    tester.test_document(
        test_name="ICSR - Drug-Induced Hepatotoxicity",
        document={
            "id": "icsr_003",
            "title": "Acute liver injury following acetaminophen overdose: a case report",
            "abstract": "We report a case of a 28-year-old female who developed acute liver injury after taking 8 grams of acetaminophen over 24 hours for migraine. The patient presented 48 hours later with nausea, vomiting, and right upper quadrant pain. Laboratory tests showed elevated ALT (1250 U/L), AST (980 U/L), and INR (2.8). The patient was treated with N-acetylcysteine and supportive care. Liver function normalized after 10 days.",
            "mesh_terms": ["Chemical and Drug Induced Liver Injury", "Acetaminophen", "Adverse Drug Reaction", "Overdose"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.85
    )
    
    # Test 1.4: ICSR - Multiple drugs, complex case
    tester.test_document(
        test_name="ICSR - Complex Multi-Drug Reaction",
        document={
            "id": "icsr_004",
            "title": "Severe cutaneous adverse reaction following concurrent use of allopurinol and azathioprine",
            "abstract": "A 55-year-old male patient with gout and inflammatory bowel disease developed severe cutaneous adverse reaction 3 weeks after starting concurrent therapy with allopurinol 300mg daily and azathioprine 150mg daily. The patient presented with extensive maculopapular rash, fever (38.5°C), eosinophilia (12%), and elevated liver enzymes (ALT 450 U/L). Both medications were discontinued. The patient required hospitalization and treatment with systemic corticosteroids. Complete resolution occurred after 4 weeks.",
            "mesh_terms": ["Drug Eruptions", "Allopurinol", "Azathioprine", "Drug Interactions", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.85
    )
    
    # Test 1.5: ICSR - Pediatric case
    tester.test_document(
        test_name="ICSR - Pediatric Allergic Reaction",
        document={
            "id": "icsr_005",
            "title": "Allergic rash in a 6-year-old child following cephalexin administration",
            "abstract": "A 6-year-old female child (weight 20kg) developed generalized urticarial rash 2 hours after the first dose of cephalexin 250mg for otitis media. The child presented with widespread hives, pruritus, and mild facial swelling. No respiratory symptoms were observed. Cephalexin was discontinued, and the child received oral diphenhydramine 25mg. The rash resolved completely within 24 hours. The child was advised to avoid all cephalosporin antibiotics.",
            "mesh_terms": ["Drug Hypersensitivity", "Urticaria", "Cephalexin", "Pediatrics", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.85
    )
    
    # ============================================================================
    # CATEGORY 2: Safety_Information
    # ============================================================================
    
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}CATEGORY 2: Safety_Information{NC}")
    print(f"{CYAN}{'='*80}{NC}")
    
    # Test 2.1: Clinical trial safety data
    tester.test_document(
        test_name="Safety_Info - Clinical Trial Safety Analysis",
        document={
            "id": "safety_001",
            "title": "Safety and tolerability of Drug X in patients with rheumatoid arthritis: results from a phase III clinical trial",
            "abstract": "This phase III, randomized, double-blind, placebo-controlled trial evaluated the safety of Drug X in 450 patients with rheumatoid arthritis. The most common adverse events were headache (12%), nausea (8%), and rash (5%). Serious adverse events occurred in 3% of Drug X patients vs 2% of placebo patients. Laboratory abnormalities included elevated liver enzymes in 4% of patients. Overall, Drug X demonstrated an acceptable safety profile consistent with its mechanism of action.",
            "mesh_terms": ["Clinical Trials, Phase III", "Drug Safety", "Rheumatoid Arthritis", "Adverse Events"],
            "publication_types": ["Clinical Trial", "Randomized Controlled Trial"]
        },
        expected_class="Safety_Information",
        min_confidence=0.7
    )
    
    # Test 2.2: Post-marketing surveillance
    tester.test_document(
        test_name="Safety_Info - Post-Marketing Surveillance",
        document={
            "id": "safety_002",
            "title": "Post-marketing surveillance of allergic reactions to Drug Y: a 5-year analysis",
            "abstract": "We conducted a 5-year post-marketing surveillance study of allergic reactions associated with Drug Y. Among 125,000 patients exposed to Drug Y, 1,250 allergic reactions were reported (1.0%). The most common reactions were rash (0.6%), urticaria (0.3%), and angioedema (0.1%). Anaphylaxis occurred in 12 cases (0.01%). Risk factors for allergic reactions included prior drug allergies and concurrent use of ACE inhibitors. The overall safety profile of Drug Y remains favorable.",
            "mesh_terms": ["Product Surveillance, Postmarketing", "Drug Hypersensitivity", "Pharmacovigilance", "Risk Factors"],
            "publication_types": ["Observational Study"]
        },
        expected_class="Safety_Information",
        min_confidence=0.7
    )
    
    # Test 2.3: Meta-analysis of safety
    tester.test_document(
        test_name="Safety_Info - Meta-Analysis",
        document={
            "id": "safety_003",
            "title": "Cardiovascular safety of COX-2 inhibitors: a meta-analysis of randomized controlled trials",
            "abstract": "We performed a meta-analysis of 28 randomized controlled trials (n=45,000 patients) to assess the cardiovascular safety of COX-2 inhibitors. The pooled analysis showed an increased risk of myocardial infarction (RR 1.42, 95% CI 1.13-1.78) and stroke (RR 1.35, 95% CI 1.06-1.71) compared to placebo. The risk was dose-dependent and increased with duration of therapy. These findings support careful cardiovascular risk assessment before prescribing COX-2 inhibitors.",
            "mesh_terms": ["Cyclooxygenase 2 Inhibitors", "Cardiovascular Diseases", "Meta-Analysis", "Drug Safety"],
            "publication_types": ["Meta-Analysis", "Systematic Review"]
        },
        expected_class="Safety_Information",
        min_confidence=0.7
    )
    
    # Test 2.4: Safety in special populations
    tester.test_document(
        test_name="Safety_Info - Pregnancy Safety Study",
        document={
            "id": "safety_004",
            "title": "Safety of Drug Z use during pregnancy: a cohort study of 2,500 exposed pregnancies",
            "abstract": "This cohort study evaluated pregnancy outcomes in 2,500 women exposed to Drug Z during pregnancy compared to 5,000 unexposed controls. The rate of major congenital malformations was 3.2% in exposed vs 3.0% in unexposed pregnancies (adjusted OR 1.07, 95% CI 0.82-1.39). No specific pattern of malformations was identified. Rates of preterm birth, low birth weight, and perinatal mortality were similar between groups. These findings suggest that Drug Z use during pregnancy is not associated with increased risk of adverse pregnancy outcomes.",
            "mesh_terms": ["Pregnancy", "Drug Safety", "Congenital Abnormalities", "Cohort Studies"],
            "publication_types": ["Observational Study"]
        },
        expected_class="Safety_Information",
        min_confidence=0.7
    )
    
    # ============================================================================
    # CATEGORY 3: Non-ICSR
    # ============================================================================
    
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}CATEGORY 3: Non-ICSR{NC}")
    print(f"{CYAN}{'='*80}{NC}")
    
    # Test 3.1: Review article
    tester.test_document(
        test_name="Non-ICSR - Review Article",
        document={
            "id": "non_icsr_001",
            "title": "Allergic rash: pathophysiology, diagnosis, and management - a comprehensive review",
            "abstract": "Allergic rashes are common dermatological manifestations of drug hypersensitivity. This review discusses the immunological mechanisms underlying allergic rashes, including IgE-mediated and T-cell-mediated reactions. We review diagnostic approaches including skin testing, patch testing, and in vitro assays. Management strategies include drug discontinuation, symptomatic treatment with antihistamines and corticosteroids, and prevention through careful drug history taking and patient education.",
            "mesh_terms": ["Drug Hypersensitivity", "Exanthema", "Review Literature", "Diagnosis"],
            "publication_types": ["Review"]
        },
        expected_class="Non-ICSR",
        min_confidence=0.7
    )
    
    # Test 3.2: Mechanistic study
    tester.test_document(
        test_name="Non-ICSR - Mechanistic Study",
        document={
            "id": "non_icsr_002",
            "title": "Molecular mechanisms of drug-induced skin reactions: role of cytotoxic T lymphocytes",
            "abstract": "Drug-induced skin reactions involve complex immunological mechanisms. In this study, we investigated the role of cytotoxic T lymphocytes (CTLs) in drug hypersensitivity reactions using an in vitro model. We found that drug-specific CTLs express high levels of granulysin and perforin, which mediate keratinocyte apoptosis. These findings provide insights into the pathogenesis of severe cutaneous adverse reactions and may inform development of novel therapeutic strategies.",
            "mesh_terms": ["Drug Eruptions", "T-Lymphocytes, Cytotoxic", "Apoptosis", "Keratinocytes"],
            "publication_types": ["Research Support"]
        },
        expected_class="Non-ICSR",
        min_confidence=0.7
    )
    
    # Test 3.3: Epidemiological study
    tester.test_document(
        test_name="Non-ICSR - Epidemiological Study",
        document={
            "id": "non_icsr_003",
            "title": "Incidence and risk factors for drug-induced rash: a population-based study",
            "abstract": "We conducted a population-based study to determine the incidence and risk factors for drug-induced rash. Using a database of 500,000 patients, we identified 5,000 cases of drug-induced rash over a 5-year period (incidence: 2.0 per 1,000 person-years). Risk factors included female sex (OR 1.5), age >65 years (OR 1.8), and polypharmacy (OR 2.3). Antibiotics were the most common causative agents (45%), followed by NSAIDs (20%) and anticonvulsants (15%).",
            "mesh_terms": ["Drug Eruptions", "Incidence", "Risk Factors", "Epidemiologic Studies"],
            "publication_types": ["Epidemiologic Study"]
        },
        expected_class="Non-ICSR",
        min_confidence=0.7
    )
    
    # Test 3.4: Diagnostic guidelines
    tester.test_document(
        test_name="Non-ICSR - Clinical Guidelines",
        document={
            "id": "non_icsr_004",
            "title": "Clinical practice guidelines for the diagnosis and management of drug hypersensitivity reactions",
            "abstract": "These evidence-based guidelines provide recommendations for the diagnosis and management of drug hypersensitivity reactions. Key recommendations include: (1) detailed drug history and timeline; (2) skin testing for immediate reactions; (3) patch testing for delayed reactions; (4) drug provocation testing when diagnosis is uncertain; (5) avoidance of culprit drug and cross-reactive agents; (6) consideration of desensitization when no alternative exists. The guidelines were developed by an expert panel using GRADE methodology.",
            "mesh_terms": ["Practice Guidelines", "Drug Hypersensitivity", "Diagnosis", "Disease Management"],
            "publication_types": ["Guideline", "Practice Guideline"]
        },
        expected_class="Non-ICSR",
        min_confidence=0.7
    )
    
    # ============================================================================
    # CATEGORY 4: Rejected
    # ============================================================================
    
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}CATEGORY 4: Rejected{NC}")
    print(f"{CYAN}{'='*80}{NC}")
    
    # Test 4.1: Retracted article
    tester.test_document(
        test_name="Rejected - Retracted Article",
        document={
            "id": "rejected_001",
            "title": "RETRACTED: Severe allergic reactions to Drug A: a case series",
            "abstract": "RETRACTION NOTICE: This article has been retracted by the journal due to concerns about data integrity and fabrication of patient cases. The findings should not be considered reliable. Readers are advised to disregard the conclusions of this study.",
            "mesh_terms": ["Retracted Publication", "Scientific Misconduct"],
            "publication_types": ["Retracted Publication"]
        },
        expected_class="Rejected",
        min_confidence=0.8
    )
    
    # Test 4.2: Duplicate publication
    tester.test_document(
        test_name="Rejected - Duplicate Publication",
        document={
            "id": "rejected_002",
            "title": "Allergic rash following penicillin: a case report [DUPLICATE]",
            "abstract": "EDITOR'S NOTE: This article is a duplicate publication of a case report previously published in another journal. The case describes a patient who developed allergic rash after penicillin administration. This duplicate publication violates ethical publishing standards.",
            "mesh_terms": ["Duplicate Publication", "Ethics, Publishing"],
            "publication_types": ["Duplicate Publication"]
        },
        expected_class="Rejected",
        min_confidence=0.8
    )
    
    # Test 4.3: Insufficient information
    tester.test_document(
        test_name="Rejected - Insufficient Information",
        document={
            "id": "rejected_003",
            "title": "A patient with rash",
            "abstract": "A patient developed a rash. Treatment was given. The patient improved.",
            "mesh_terms": [],
            "publication_types": []
        },
        expected_class="Rejected",
        min_confidence=0.6
    )
    
    # ============================================================================
    # EDGE CASES & ENSEMBLE TESTING
    # ============================================================================
    
    print(f"\n{CYAN}{'='*80}{NC}")
    print(f"{CYAN}EDGE CASES & ENSEMBLE TESTING{NC}")
    print(f"{CYAN}{'='*80}{NC}")
    
    # Test 5.1: Borderline case - could be ICSR or Safety_Info
    tester.test_document(
        test_name="Edge Case - Case Series (Borderline)",
        document={
            "id": "edge_001",
            "title": "Allergic reactions to Drug B: a case series of 15 patients",
            "abstract": "We report a case series of 15 patients who developed allergic reactions to Drug B over a 2-year period. Patients ranged in age from 25 to 70 years. The most common presentation was maculopapular rash (n=10), followed by urticaria (n=3) and angioedema (n=2). All patients recovered after drug discontinuation. This case series highlights the need for vigilance when prescribing Drug B.",
            "mesh_terms": ["Drug Hypersensitivity", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",  # Should be ICSR due to "Case Reports" publication type
        min_confidence=0.6
    )
    
    # Test 5.2: No metadata - text only
    tester.test_document(
        test_name="Edge Case - No Metadata (Text Only)",
        document={
            "id": "edge_002",
            "title": "Severe allergic rash in a 50-year-old patient after antibiotic treatment",
            "abstract": "A 50-year-old patient developed severe allergic rash 3 days after starting antibiotic treatment. The patient presented with widespread erythema and pruritus. The antibiotic was discontinued and the patient received antihistamines. The rash resolved after 5 days.",
            "mesh_terms": [],
            "publication_types": []
        },
        expected_class="ICSR",  # Should still detect ICSR from text
        min_confidence=0.5  # Lower confidence without metadata
    )
    
    # Test 5.3: Conflicting signals
    tester.test_document(
        test_name="Edge Case - Conflicting Signals",
        document={
            "id": "edge_003",
            "title": "Review of allergic reactions: including a case report",
            "abstract": "This article reviews the literature on allergic reactions to antibiotics. We also present a case of a 35-year-old patient who developed urticaria after amoxicillin. The patient recovered after treatment. Overall, allergic reactions to antibiotics are common and clinicians should be aware of risk factors and management strategies.",
            "mesh_terms": ["Drug Hypersensitivity", "Review Literature"],
            "publication_types": ["Review", "Case Reports"]
        },
        expected_class="ICSR",  # Case Reports should take precedence
        min_confidence=0.6
    )
    
    # Test 5.4: Very high confidence ICSR
    tester.test_document(
        test_name="Edge Case - Perfect ICSR (All Signals)",
        document={
            "id": "edge_004",
            "title": "Fatal anaphylaxis following intravenous penicillin: a case report with autopsy findings",
            "abstract": "We report a tragic case of a 42-year-old male patient with no known drug allergies who developed fatal anaphylaxis within 5 minutes of receiving intravenous penicillin G 2 million units for suspected meningitis. The patient immediately developed generalized urticaria, angioedema, bronchospasm, and cardiovascular collapse (BP 60/30, HR 140). Despite immediate treatment with epinephrine, intubation, and aggressive resuscitation, the patient died 2 hours later. Autopsy confirmed anaphylaxis with laryngeal edema, pulmonary edema, and myocardial ischemia. This case emphasizes the importance of careful allergy history and availability of emergency medications.",
            "mesh_terms": ["Anaphylaxis", "Penicillin G", "Drug Hypersensitivity", "Fatal Outcome", "Adverse Drug Reaction"],
            "publication_types": ["Case Reports"]
        },
        expected_class="ICSR",
        min_confidence=0.95
    )
    
    # Print summary
    tester.print_summary()
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"classification_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_tests": tester.total_tests,
            "passed_tests": tester.passed_tests,
            "failed_tests": tester.failed_tests,
            "pass_rate": tester.passed_tests / tester.total_tests if tester.total_tests > 0 else 0,
            "results": tester.results
        }, f, indent=2)
    
    print(f"{GREEN}Results saved to: {results_file}{NC}\n")
    
    # Return exit code
    return 0 if tester.failed_tests == 0 else 1


if __name__ == "__main__":
    exit(main())

