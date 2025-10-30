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
        
        # Classification prompt template
        self.classification_prompt = """
You are a medical literature classification expert. Classify the following document into one of these categories:

1. **ICSR** (Individual Case Safety Report) - Individual patient case reports of adverse drug reactions
2. **Safety_Information** - General safety information, warnings, or guidelines
3. **Non-ICSR** - Research studies, reviews, or other non-case report literature
4. **Rejected** - Not relevant to pharmacovigilance

Document Information:
Title: {title}
Abstract: {abstract}
MeSH Terms: {mesh_terms}
Publication Type: {publication_types}

Respond with ONLY the classification category name (ICSR, Safety_Information, Non-ICSR, or Rejected) and a brief reasoning.

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
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "top_p": 0.9,
                    "max_tokens": 200
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
