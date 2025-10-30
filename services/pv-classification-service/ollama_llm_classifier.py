"""
Ollama LLM Classifier
Uses local Ollama models for LLM-based classification
"""

import asyncio
import structlog
import httpx
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = structlog.get_logger(__name__)

class OllamaLLMClassifier:
    """
    LLM classifier using Ollama models
    Supports multiple local models: Llama, Phi-3, etc.
    """
    
    def __init__(self, 
                 model_name: str = "llama3.1:8b",
                 base_url: str = "http://localhost:11434",
                 timeout: float = 120.0):
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
        self.client = None
        
        # Classification prompt template (aligned with OpenAI prompt)
        self.classification_prompt = """
You are an expert pharmacovigilance (PV) reviewer trained in EMA GVP Module VI and FDA FAERS reporting standards.
Your goal is to classify biomedical literature records into pharmacovigilance categories based on ICH E2D and WHO-UMC principles.

An ICSR must describe: (1) identifiable patient, (2) identifiable reporter, (3) suspected medicinal product, (4) suspected adverse event.

**Classification Categories:**

1. **ICSR (Individual Case Safety Report)**
   - Describes one or more identifiable patient cases with drug-event relationship
   - Contains: patient demographics, drug administered, adverse event, temporal relationship
   - Suitable for regulatory PV case processing
   - Examples: "A 45-year-old female developed rash after penicillin", "Case of hepatotoxicity following drug X"

2. **Safety_Information**
   - Discusses drug safety, tolerability, or adverse events at population/aggregate level
   - NO individual patient cases, but safety-relevant information
   - Examples: Clinical trial safety data, post-marketing surveillance, meta-analyses of safety, pharmacovigilance studies
   - Keywords: "safety profile", "tolerability", "adverse events in clinical trial", "post-marketing surveillance"

3. **Non-ICSR**
   - Concerns drugs/diseases but NOT safety-focused and NOT individual cases
   - Examples: Mechanistic studies, reviews (non-safety), efficacy studies, pharmacokinetics, guidelines
   - Keywords: "mechanism", "pathophysiology", "review of", "guidelines", "in vitro", "animal model"

4. **Rejected**
   - Irrelevant for pharmacovigilance purposes
   - Examples: Retracted articles, duplicates, insufficient information, non-drug topics
   - Keywords: "RETRACTED", "DUPLICATE", very short abstracts (<50 words)

**Classification Examples:**

Example 1 - ICSR:
Title: "Severe allergic rash in a 50-year-old patient after amoxicillin"
Abstract: "A 50-year-old male developed widespread urticaria 2 hours after receiving amoxicillin 500mg..."
→ Classification: ICSR, Confidence: 0.90
→ Reasoning: Clear patient case with drug, adverse event, and temporal relationship

Example 2 - Safety_Information:
Title: "Safety and tolerability of Drug X in Phase III trial"
Abstract: "450 patients received Drug X. Adverse events included headache (12%), nausea (8%)..."
→ Classification: Safety_Information, Confidence: 0.85
→ Reasoning: Clinical trial safety data with aggregate adverse event rates, not individual cases

Example 3 - Non-ICSR:
Title: "Mechanisms of drug-induced liver injury: a review"
Abstract: "This review discusses molecular pathways involved in hepatotoxicity..."
→ Classification: Non-ICSR, Confidence: 0.90
→ Reasoning: Review article about mechanisms, not safety data or individual cases

Example 4 - Rejected:
Title: "RETRACTED: Case report of adverse reaction"
Abstract: "This article has been retracted due to data fabrication..."
→ Classification: Rejected, Confidence: 0.95
→ Reasoning: Retracted publication, not suitable for PV purposes

**Document to Classify:**

**Title:** {title}

**Abstract:** {abstract}

**MeSH Terms:** {mesh_terms}

**Publication Types:** {publication_types}

**Classification Instructions:**
1. Identify if this describes individual patient case(s) → likely ICSR
2. Check if it's aggregate safety data (trial, surveillance) → likely Safety_Information
3. Check if it's mechanistic/review without safety focus → likely Non-ICSR
4. Check for retraction/duplicate/insufficient data → likely Rejected
5. Use publication types and MeSH terms as strong signals
6. Assign appropriate confidence based on clarity of evidence

**Confidence Guidelines:**
- High confidence (0.85-0.95): Clear, unambiguous classification
- Moderate confidence (0.65-0.84): Some ambiguity but leaning toward one class
- Low confidence (0.50-0.64): Uncertain, borderline case

Respond with the classification category (ICSR, Safety_Information, Non-ICSR, or Rejected), confidence score (0.50-0.95), and brief reasoning (2-3 sentences).

Classification:"""

    async def initialize(self) -> bool:
        """Initialize the Ollama client"""
        try:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
            
            # Test connection and model availability
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model_name in model_names:
                    logger.info("Ollama LLM classifier initialized", model=self.model_name)
                    return True
                else:
                    logger.warning("Model not found, using available model", 
                                 requested=self.model_name, 
                                 available=model_names)
                    # Use the first available model
                    if model_names:
                        self.model_name = model_names[0]
                        logger.info("Using fallback model", model=self.model_name)
                        return True
                    return False
            else:
                logger.error("Failed to connect to Ollama", status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Failed to initialize Ollama LLM classifier", error=str(e))
            return False
    
    async def classify_document(self, 
                              title: str,
                              abstract: Optional[str] = None,
                              mesh_terms: Optional[List[str]] = None,
                              publication_types: Optional[List[str]] = None) -> Tuple[str, float, str, List[Dict]]:
        """
        Classify document using Ollama LLM
        
        Returns:
            (classification, confidence, reasoning, key_entities)
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Prepare document information
            mesh_str = ", ".join(mesh_terms) if mesh_terms else "None"
            pub_types_str = ", ".join(publication_types) if publication_types else "None"
            abstract_text = abstract or "No abstract available"
            
            # Create prompt
            prompt = self.classification_prompt.format(
                title=title,
                abstract=abstract_text,
                mesh_terms=mesh_str,
                publication_types=pub_types_str
            )
            
            # Call Ollama API
            response = await self.client.post("/api/generate", json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,  # Increased from 0.1 for more variation
                    "top_p": 0.9,
                    "max_tokens": 500  # Increased for detailed reasoning
                }
            })
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                
                # Parse the response
                classification, reasoning = self._parse_classification_response(response_text)
                confidence = self._calculate_confidence(response_text, classification)
                key_entities = self._extract_entities(title, abstract, classification)
                
                logger.info("Ollama classification completed", 
                           classification=classification,
                           confidence=confidence,
                           model=self.model_name)
                
                return classification, confidence, reasoning, key_entities
            else:
                logger.error("Ollama API error", status_code=response.status_code)
                return "Non-ICSR", 0.5, "Ollama API error", []
                
        except Exception as e:
            logger.error("Ollama classification failed", error=str(e))
            return "Non-ICSR", 0.5, f"Classification error: {str(e)}", []
    
    def _parse_classification_response(self, response: str) -> Tuple[str, str]:
        """Parse the LLM response to extract classification and reasoning"""
        lines = response.strip().split('\n')
        
        # Look for classification in the response
        classification = "Non-ICSR"  # Default
        reasoning = "No specific reasoning provided"
        
        for line in lines:
            line = line.strip()
            if line.upper() in ["ICSR", "SAFETY_INFORMATION", "NON-ICSR", "REJECTED"]:
                classification = line.upper()
            elif line.startswith("Classification:"):
                # Extract classification from "Classification: ICSR" format
                parts = line.split(":", 1)
                if len(parts) > 1:
                    classification = parts[1].strip().upper()
            elif line and not line.startswith("Classification:"):
                # Use as reasoning
                reasoning = line
        
        # Validate classification
        valid_classifications = ["ICSR", "SAFETY_INFORMATION", "NON-ICSR", "REJECTED"]
        if classification not in valid_classifications:
            classification = "Non-ICSR"
        
        return classification, reasoning
    
    def _calculate_confidence(self, response: str, classification: str) -> float:
        """Calculate confidence based on response characteristics"""
        # Base confidence
        confidence = 0.7
        
        # Increase confidence for clear classifications
        if classification in ["ICSR", "Non-ICSR"]:
            confidence += 0.1
        
        # Increase confidence for longer, more detailed responses
        if len(response) > 50:
            confidence += 0.1
        
        # Increase confidence if response contains medical terms
        medical_terms = ["adverse", "reaction", "patient", "drug", "case", "safety"]
        if any(term in response.lower() for term in medical_terms):
            confidence += 0.1
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _extract_entities(self, title: str, abstract: str, classification: str) -> List[Dict]:
        """Extract key entities from the document"""
        entities = []
        
        # Extract drug mentions (simple pattern matching)
        text = f"{title} {abstract}".lower()
        drug_indicators = ["drug", "medication", "therapy", "treatment", "dose", "mg", "tablet"]
        
        for indicator in drug_indicators:
            if indicator in text:
                entities.append({
                    "entity": indicator,
                    "type": "drug_mention",
                    "confidence": 0.7,
                    "relevance": "Drug-related term for classification"
                })
        
        # Extract adverse event mentions
        adverse_indicators = ["adverse", "reaction", "side effect", "toxicity", "complication"]
        for indicator in adverse_indicators:
            if indicator in text:
                entities.append({
                    "entity": indicator,
                    "type": "adverse_event",
                    "confidence": 0.8,
                    "relevance": "Adverse event indicator for ICSR classification"
                })
        
        # Extract patient mentions
        patient_indicators = ["patient", "case", "individual", "subject"]
        for indicator in patient_indicators:
            if indicator in text:
                entities.append({
                    "entity": indicator,
                    "type": "patient_mention",
                    "confidence": 0.6,
                    "relevance": "Patient-related term for case report identification"
                })
        
        return entities
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.aclose()

# Global instance
ollama_llm_classifier = OllamaLLMClassifier()
