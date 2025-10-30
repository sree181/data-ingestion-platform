"""
Pharmacovigilance Classification Service
Standalone microservice for classifying medical literature into PV categories
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import structlog
import json
import httpx
import asyncio
from datetime import datetime
import uvicorn
import os
from openai import AsyncOpenAI

# Import ICSR extraction services (with error handling)
try:
    from icsr_extractor import icsr_extractor, ICSRData
    from icsr_narrative_generator import narrative_generator
    from ich_e2b_xml_generator import xml_generator
    ICSR_SERVICES_AVAILABLE = True
except Exception as e:
    print(f"⚠️  ICSR services not available: {e}")
    ICSR_SERVICES_AVAILABLE = False

# Import ensemble classifier components
from ensemble_classifier import initialize_ensemble
from rule_based_classifier import rule_based_classifier
from bert_classifier import bert_classifier

# Import RL-enhanced components
try:
    from rl_api_endpoints import router as rl_router
    RL_AVAILABLE = True
except Exception as e:
    print(f"⚠️  RL components not available: {e}")
    RL_AVAILABLE = False

# Import Ollama LLM classifier
from ollama_llm_classifier import ollama_llm_classifier

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title="PV Classification Service",
    description="Pharmacovigilance classification service for medical literature",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class ClassificationEntity(BaseModel):
    """Entity extracted during classification"""
    entity: str = Field(..., description="Entity text")
    type: str = Field(..., description="Entity type (drug, event, patient_info, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    relevance: str = Field(..., description="Why this entity is relevant for classification")


class ClassificationResult(BaseModel):
    """Classification result for a document"""
    classification: str = Field(..., description="ICSR | Non-ICSR | Safety_Information | Rejected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Explanation for classification decision")
    key_entities: List[ClassificationEntity] = Field(default_factory=list, description="Entities that drove classification")
    regulatory_elements: Dict[str, bool] = Field(default_factory=dict, description="ICH E2D elements present")


class Document(BaseModel):
    """Document to classify"""
    id: str
    title: str
    abstract: Optional[str] = None
    mesh_terms: Optional[List[str]] = None
    publication_types: Optional[List[str]] = None


class ClassificationRequest(BaseModel):
    """Request to classify a document"""
    document: Document


class ClassificationResponse(BaseModel):
    """Response after classification"""
    success: bool
    document_id: str
    classification: ClassificationResult
    processed_at: str


class BatchClassificationRequest(BaseModel):
    """Request to classify multiple documents"""
    documents: List[Document]


class BatchClassificationResponse(BaseModel):
    """Response after batch classification"""
    success: bool
    total: int
    results: List[ClassificationResponse]
    processing_time_seconds: float


# Classification Prompts
PHARMACOVIGILANCE_EXPERT_PROMPT = """
You are an expert pharmacovigilance (PV) reviewer trained in EMA GVP Module VI and FDA FAERS reporting standards.
Your goal is to classify biomedical literature records (titles + abstracts) into pharmacovigilance categories based on the
presence and completeness of Individual Case Safety Report (ICSR) information.

Follow ICH E2D and WHO-UMC principles:
An ICSR must describe at least one identifiable patient, one identifiable reporter, one suspected medicinal product,
and one suspected adverse event (AE).

Possible output categories:

1. **ICSR (Individual Case Safety Report)**
   The article clearly describes one or more identifiable patient cases where:
   - A medicinal product was administered/exposed;
   - An adverse event, reaction, or outcome was observed;
   - Sufficient clinical detail exists (age/sex, timeline, dose, dechallenge/rechallenge, outcome);
   - The report can be used for regulatory PV case processing.

2. **Non-ICSR**
   The article concerns drugs or AEs but **does not contain identifiable patient-level data**.
   Examples: reviews, RCTs, mechanistic studies, meta-analyses, signal-detection studies, animal or in-vitro research.

3. **Safety_Information**
   The article discusses safety, toxicity, or risk without individual cases.
   Examples:
   - Reports of dose-response, adverse-effect mechanisms, or class safety;
   - Epidemiological or pharmacological safety data;
   - Aggregated summaries of spontaneous reports.

4. **Rejected**
   The article is irrelevant for PV purposes.
   Examples:
   - No medicinal product or AE mentioned;
   - Editorials, news, letters without scientific case data;
   - Animal/in-vitro studies outside PV scope;
   - Diagnostic or therapeutic method papers unrelated to safety.

You must produce a structured JSON output that includes the classification label, confidence score,
a rationale explaining the decision, and extracted evidence.

Be conservative when labeling ICSR: only classify as ICSR if the core four elements (drug, event, patient, reporter context)
are clearly or strongly implied.

**Document to Classify:**

**Title:** {title}

**Abstract:** {abstract}

**MeSH Terms:** {mesh_terms}

**Publication Types:** {publication_types}

**Instructions:**
1. Identify the four core ICSR elements:
   - Identifiable patient (age, gender, demographics)
   - Medicinal product (drug name, vaccine, etc.)
   - Adverse event/reaction (specific outcome)
   - Reporter context (case report, clinical observation)

2. Assess completeness and regulatory relevance

3. Classify conservatively

**Output Format (JSON only, no additional text):**
{{
  "classification": "ICSR|Non-ICSR|Safety_Information|Rejected",
  "confidence": 0.0-1.0,
  "reasoning": "2-4 sentences explaining the classification decision based on ICH E2D principles",
  "key_entities": [
    {{
      "entity": "extracted text",
      "type": "drug|adverse_event|patient_info|temporal|outcome|dose|route",
      "confidence": 0.0-1.0,
      "relevance": "why this entity is important for classification"
    }}
  ],
  "regulatory_elements": {{
    "identifiable_patient": true/false,
    "medicinal_product": true/false,
    "adverse_event": true/false,
    "reporter_context": true/false
  }}
}}

Classify now:
"""


class PVClassificationService:
    """
    Pharmacovigilance Classification Service
    Uses Ollama LLM for classification (local, free)
    """
    
    def __init__(self, use_ollama: bool = True):
        self.use_ollama = use_ollama
        self.ollama_classifier = None
        
        if use_ollama:
            # Use Ollama LLM classifier
            self.ollama_classifier = ollama_llm_classifier
            logger.info("PV Classification Service initialized with Ollama LLM")
        else:
            # Fallback to OpenAI (requires API key)
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable must be set")
            self.client = AsyncOpenAI(api_key=openai_api_key)
            self.model = "gpt-4o-mini"
            logger.info("PV Classification Service initialized with OpenAI", model=self.model)
    
    async def classify_document_llm_only(
        self,
        title: str,
        abstract: Optional[str] = None,
        mesh_terms: Optional[List[str]] = None,
        publication_types: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Classify using LLM only (used by ensemble when needed)
        
        Args:
            title: Document title
            abstract: Document abstract
            mesh_terms: MeSH terms
            publication_types: Publication types
            
        Returns:
            Classification result
        """
        if self.use_ollama and self.ollama_classifier:
            # Use Ollama LLM classifier
            classification, confidence, reasoning, key_entities = await self.ollama_classifier.classify_document(
                title=title,
                abstract=abstract,
                mesh_terms=mesh_terms,
                publication_types=publication_types
            )
            
            return ClassificationResult(
                classification=classification,
                confidence=confidence,
                reasoning=reasoning,
                key_entities=key_entities,
                regulatory_elements={}
            )
        else:
            # Fallback to OpenAI
            document = Document(
                id="temp",
                title=title,
                abstract=abstract,
                mesh_terms=mesh_terms,
                publication_types=publication_types
            )
            return await self.classify_document(document)
    
    async def classify_document(self, document: Document) -> ClassificationResult:
        """
        Classify a single document using OpenAI GPT-4
        """
        try:
            logger.info("Classifying document", document_id=document.id, title=document.title[:100])
            
            # Format prompt
            prompt = PHARMACOVIGILANCE_EXPERT_PROMPT.format(
                title=document.title,
                abstract=document.abstract or "No abstract available",
                mesh_terms=", ".join(document.mesh_terms) if document.mesh_terms else "None",
                publication_types=", ".join(document.publication_types) if document.publication_types else "None"
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert pharmacovigilance reviewer. Always respond with valid JSON only, no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            message_content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                classification_data = json.loads(message_content)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse GPT response", error=str(e), content=message_content[:200])
                # Fallback classification
                classification_data = {
                    "classification": "Non-ICSR",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse LLM response, defaulting to Non-ICSR",
                    "key_entities": [],
                    "regulatory_elements": {}
                }
            
            # Convert to ClassificationResult (outside the try-except)
            classification_result = ClassificationResult(
                classification=classification_data.get("classification", "Non-ICSR"),
                confidence=classification_data.get("confidence", 0.5),
                reasoning=classification_data.get("reasoning", "No reasoning provided"),
                key_entities=[
                    ClassificationEntity(**entity)
                    for entity in classification_data.get("key_entities", [])
                ],
                regulatory_elements=classification_data.get("regulatory_elements", {})
            )
            
            logger.info(
                "Classification completed",
                document_id=document.id,
                classification=classification_result.classification,
                confidence=classification_result.confidence
            )
            
            return classification_result
                
        except Exception as e:
            logger.error("Classification failed", document_id=document.id, error=str(e))
            # Return fallback classification
            return ClassificationResult(
                classification="Non-ICSR",
                confidence=0.3,
                reasoning=f"Classification failed: {str(e)}",
                key_entities=[],
                regulatory_elements={}
            )
    
    async def classify_batch(self, documents: List[Document], parallel: int = 5) -> List[ClassificationResponse]:
        """
        Classify multiple documents in parallel
        """
        logger.info("Starting batch classification", total_documents=len(documents), parallel=parallel)
        
        results = []
        
        # Process in batches
        for i in range(0, len(documents), parallel):
            batch = documents[i:i+parallel]
            batch_tasks = [self.classify_document(doc) for doc in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for doc, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error("Batch classification error", document_id=doc.id, error=str(result))
                    result = ClassificationResult(
                        classification="Non-ICSR",
                        confidence=0.0,
                        reasoning=f"Error: {str(result)}",
                        key_entities=[],
                        regulatory_elements={}
                    )
                
                results.append(ClassificationResponse(
                    success=True,
                    document_id=doc.id,
                    classification=result,
                    processed_at=datetime.utcnow().isoformat()
                ))
        
        logger.info("Batch classification completed", total=len(results))
        return results


# Initialize service
pv_service = PVClassificationService()

# Initialize ensemble classifier (will be done in startup event)
ensemble = None

# Include RL router (if available)
if RL_AVAILABLE:
    app.include_router(rl_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ensemble
    
    print("🚀 Starting PV Classification Service")
    print("=" * 50)
    print("📊 Available Models:")
    print("   ✅ Rule-based Classifier (Free, Fast)")
    print("   ✅ BERT Classifier (facebook/bart-large-mnli)")
    
    # Initialize Ollama LLM classifier
    try:
        await ollama_llm_classifier.initialize()
        print("   ✅ Ollama LLM Classifier (Local, Free)")
        
        # Initialize ensemble with Ollama LLM
        from ensemble_classifier import EnsembleClassifier
        ensemble = EnsembleClassifier(llm_classifier=ollama_llm_classifier)
        print("✅ Ensemble classifier initialized with Ollama LLM support")
        
    except Exception as e:
        print(f"   ⚠️  Ollama LLM not available: {e}")
        # Initialize ensemble without LLM
        from ensemble_classifier import EnsembleClassifier
        ensemble = EnsembleClassifier(llm_classifier=None)
        print("✅ Ensemble classifier initialized (Rule-based + BERT only)")
    
    print("=" * 50)
    print("🎯 Service ready for document classification!")


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pv-classification-service",
        "version": "1.0.0"
    }


@app.post("/api/v1/classify", response_model=ClassificationResponse)
async def classify_document_endpoint(request: ClassificationRequest):
    """
    Classify a single document using LLM only (original endpoint)
    """
    try:
        start_time = datetime.utcnow()
        
        classification_result = await pv_service.classify_document(request.document)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info("Document classified", document_id=request.document.id, processing_time=processing_time)
        
        return ClassificationResponse(
            success=True,
            document_id=request.document.id,
            classification=classification_result,
            processed_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error("Classification endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/api/v1/classify/ensemble")
async def classify_document_ensemble(request: ClassificationRequest):
    """
    Classify a single document using ensemble (RECOMMENDED)
    Uses rule-based → BERT → LLM cascade for optimal speed/cost/accuracy
    """
    try:
        start_time = datetime.utcnow()
        
        # Run ensemble classification
        ensemble_result = await ensemble.classify(
            title=request.document.title,
            abstract=request.document.abstract,
            mesh_terms=request.document.mesh_terms,
            publication_types=request.document.publication_types,
            force_ensemble=False  # Use smart cascade
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Ensemble classification complete",
            document_id=request.document.id,
            classification=ensemble_result['ensemble_result'],
            models_used=ensemble_result['models_used'],
            processing_time=processing_time
        )
        
        # Convert to standard response format
        # Extract key entities from LLM if it was used
        key_entities = []
        if 'llm' in ensemble_result.get('individual_results', {}):
            llm_entities = ensemble_result['individual_results']['llm'].get('key_entities', [])
            key_entities = [ClassificationEntity(**e) if isinstance(e, dict) else e for e in llm_entities]
        
        classification_result = ClassificationResult(
            classification=ensemble_result['ensemble_result'],
            confidence=ensemble_result['confidence'],
            reasoning=ensemble_result['reasoning'],
            key_entities=key_entities,
            regulatory_elements={}
        )
        
        response = ClassificationResponse(
            success=True,
            document_id=request.document.id,
            classification=classification_result,
            processed_at=datetime.utcnow().isoformat()
        )
        
        # Add ensemble metadata
        response_dict = response.dict()
        response_dict['ensemble_metadata'] = {
            'models_used': ensemble_result['models_used'],
            'decision_path': ensemble_result['decision_path'],
            'processing_time_ms': ensemble_result['processing_time_ms'],
            'cost_estimate': ensemble_result['cost_estimate'],
            'individual_results': ensemble_result['individual_results']
        }
        
        return response_dict
        
    except Exception as e:
        logger.error("Ensemble classification error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ensemble classification failed: {str(e)}")


@app.post("/api/v1/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch(request: BatchClassificationRequest):
    """
    Classify multiple documents in parallel (LLM-only, legacy endpoint)
    Use /classify/ensemble/batch for better performance
    """
    try:
        start_time = datetime.utcnow()
        
        results = await pv_service.classify_batch(request.documents, parallel=5)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Batch classification completed",
            total_documents=len(request.documents),
            processing_time=processing_time
        )
        
        return BatchClassificationResponse(
            success=True,
            total=len(results),
            results=results,
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error("Batch classification endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")


@app.post("/api/v1/classify/ensemble/batch")
async def classify_batch_ensemble(request: BatchClassificationRequest):
    """
    Classify multiple documents using ensemble (RECOMMENDED)
    Uses intelligent cascade for each document: rule-based → BERT → LLM
    """
    try:
        start_time = datetime.utcnow()
        
        logger.info(f"Starting ensemble batch classification for {len(request.documents)} documents")
        
        # Classify documents in parallel using ensemble
        tasks = [
            ensemble.classify(
                title=doc.title,
                abstract=doc.abstract,
                mesh_terms=doc.mesh_terms,
                publication_types=doc.publication_types,
                force_ensemble=False
            )
            for doc in request.documents
        ]
        
        ensemble_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert to standard response format
        results = []
        total_cost = 0.0
        total_llm_calls = 0
        
        for i, (doc, ensemble_result) in enumerate(zip(request.documents, ensemble_results)):
            if isinstance(ensemble_result, Exception):
                logger.error(f"Document {i} classification failed", error=str(ensemble_result))
                continue
            
            # Track costs
            total_cost += ensemble_result.get('cost_estimate', 0.0)
            if 'llm' in ensemble_result.get('models_used', []):
                total_llm_calls += 1
            
            # Extract key entities from LLM if it was used
            key_entities = []
            if 'llm' in ensemble_result.get('individual_results', {}):
                llm_entities = ensemble_result['individual_results']['llm'].get('key_entities', [])
                key_entities = [ClassificationEntity(**e) if isinstance(e, dict) else e for e in llm_entities]
            
            classification_result = ClassificationResult(
                classification=ensemble_result['ensemble_result'],
                confidence=ensemble_result['confidence'],
                reasoning=ensemble_result['reasoning'],
                key_entities=key_entities,
                regulatory_elements={}
            )
            
            result = ClassificationResponse(
                success=True,
                document_id=doc.id,
                classification=classification_result,
                processed_at=datetime.utcnow().isoformat()
            )
            
            results.append(result)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Ensemble batch classification completed",
            total_documents=len(request.documents),
            successful=len(results),
            processing_time=processing_time,
            total_cost=total_cost,
            llm_calls=total_llm_calls,
            llm_percentage=f"{(total_llm_calls / len(request.documents) * 100):.1f}%"
        )
        
        # Return response with ensemble metadata
        response = BatchClassificationResponse(
            success=True,
            total=len(results),
            results=results,
            processing_time_seconds=processing_time
        )
        
        # Add ensemble stats
        response_dict = response.dict()
        response_dict['ensemble_stats'] = {
            'total_cost': total_cost,
            'llm_calls': total_llm_calls,
            'llm_percentage': total_llm_calls / len(request.documents) if len(request.documents) > 0 else 0,
            'avg_cost_per_document': total_cost / len(request.documents) if len(request.documents) > 0 else 0
        }
        
        return response_dict
        
    except Exception as e:
        logger.error("Ensemble batch classification error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ensemble batch classification failed: {str(e)}")


@app.get("/api/v1/stats")
async def get_statistics():
    """
    Get classification service statistics
    """
    return {
        "service": "pv-classification-service",
        "model": pv_service.model,
        "categories": ["ICSR", "Non-ICSR", "Safety_Information", "Rejected"],
        "status": "operational",
        "icsr_extraction": "enabled"
    }


@app.post("/api/v1/extract/icsr")
async def extract_icsr_data(request: Dict[str, Any]):
    """
    Extract comprehensive ICSR data from a classified ICSR document
    
    Request body:
    {
        "document_id": "string",
        "title": "string",
        "abstract": "string",
        "full_text": "string (optional)",
        "pmid": "string (optional)",
        "doi": "string (optional)"
    }
    """
    try:
        logger.info("ICSR extraction requested", document_id=request.get("document_id"))
        
        # Extract ICSR data
        icsr_data = await icsr_extractor.extract_icsr_data(
            title=request["title"],
            abstract=request.get("abstract", ""),
            full_text=request.get("full_text"),
            pmid=request.get("pmid"),
            doi=request.get("doi")
        )
        
        # Generate comprehensive narrative
        original_text = f"{request['title']}\n\n{request.get('abstract', '')}"
        if request.get("full_text"):
            original_text += f"\n\n{request['full_text']}"
        
        narrative = await narrative_generator.generate_narrative(
            icsr_data=icsr_data,
            original_text=original_text
        )
        
        # Update ICSR data with generated narrative
        icsr_data.case_narrative = narrative
        
        # Generate ICH E2B R3 XML
        xml_content = xml_generator.generate_xml(icsr_data)
        
        logger.info(
            "ICSR extraction completed",
            document_id=request.get("document_id"),
            num_events=len(icsr_data.events),
            num_products=len(icsr_data.suspect_products),
            narrative_length=len(narrative)
        )
        
        return {
            "success": True,
            "document_id": request.get("document_id"),
            "icsr_data": icsr_data.dict(),
            "narrative": narrative,
            "xml": xml_content,
            "extraction_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("ICSR extraction failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"ICSR extraction failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)

