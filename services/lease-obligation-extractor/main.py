#!/usr/bin/env python3
"""
Lease Obligation Extractor Service
Specialized service for extracting lease-specific obligations and clauses
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import asyncio
import json
import uuid
from datetime import datetime
import structlog
from contextlib import asynccontextmanager

# Import our processors
from processors.lease_clause_extractor import LeaseClauseExtractor
from processors.obligation_analyzer import ObligationAnalyzer

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
lease_extractor = None
obligation_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global lease_extractor, obligation_analyzer
    
    logger.info("🚀 Starting Lease Obligation Extractor Service...")
    
    try:
        # Initialize lease clause extractor
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        lease_extractor = LeaseClauseExtractor(api_key=openai_api_key)
        obligation_analyzer = ObligationAnalyzer()
        
        logger.info("✅ Lease Obligation Extractor Service initialized")
        
        yield
        
    except Exception as e:
        logger.error("❌ Failed to start services", error=str(e))
        raise
    finally:
        logger.info("🔄 Lease Obligation Extractor Service stopped")

# Create FastAPI app
app = FastAPI(
    title="Lease Obligation Extractor",
    description="Specialized service for extracting lease-specific obligations and clauses",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class LeaseExtractionRequest(BaseModel):
    """Request model for lease extraction"""
    document_id: str = Field(..., description="Document ID to extract from")
    document_content: str = Field(..., description="Full document content")
    extraction_rules: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Custom extraction rules and configurations"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus extraction on (e.g., 'maintenance', 'renewal')"
    )

class ObligationResult(BaseModel):
    """Individual obligation extraction result"""
    obligation_type: str = Field(..., description="Type of obligation (e.g., MAINTENANCE, RENEWAL)")
    clause_text: str = Field(..., description="Extracted clause text")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    confidence: float = Field(..., description="Extraction confidence score")
    context: str = Field(..., description="Surrounding context")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    negotiation_leverage: str = Field(..., description="Negotiation leverage potential")
    market_standard: bool = Field(..., description="Whether this is a standard market term")

class LeaseExtractionResponse(BaseModel):
    """Response model for lease extraction"""
    document_id: str = Field(..., description="Document ID")
    extraction_id: str = Field(..., description="Unique extraction ID")
    obligations: List[ObligationResult] = Field(..., description="Extracted obligations")
    summary: Dict[str, Any] = Field(..., description="Extraction summary")
    metadata: Dict[str, Any] = Field(..., description="Extraction metadata")

class ComparisonRequest(BaseModel):
    """Request model for lease comparison"""
    document_ids: List[str] = Field(..., description="List of document IDs to compare")
    comparison_focus: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus comparison on"
    )

class ComparisonResult(BaseModel):
    """Individual comparison result"""
    obligation_type: str = Field(..., description="Type of obligation being compared")
    documents: Dict[str, Any] = Field(..., description="Obligation data per document")
    differences: List[str] = Field(..., description="Key differences identified")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    negotiation_opportunities: List[str] = Field(..., description="Negotiation opportunities")
    market_benchmark: Dict[str, Any] = Field(..., description="Market benchmark data")

class LeaseComparisonResponse(BaseModel):
    """Response model for lease comparison"""
    comparison_id: str = Field(..., description="Unique comparison ID")
    document_ids: List[str] = Field(..., description="Compared document IDs")
    results: List[ComparisonResult] = Field(..., description="Comparison results")
    overall_risk_score: float = Field(..., description="Overall risk score (0-100)")
    negotiation_summary: Dict[str, Any] = Field(..., description="Negotiation summary")
    recommendations: List[str] = Field(..., description="Strategic recommendations")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "lease-obligation-extractor",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Lease extraction endpoint
@app.post("/api/v1/lease/extract", response_model=LeaseExtractionResponse)
async def extract_lease_obligations(request: LeaseExtractionRequest):
    """
    Extract lease obligations from document content
    
    Args:
        request: Lease extraction request with document content and rules
        
    Returns:
        Extracted obligations with analysis and risk assessment
    """
    try:
        logger.info(
            "🔍 Starting lease obligation extraction",
            document_id=request.document_id,
            content_length=len(request.document_content),
            focus_areas=request.focus_areas
        )
        
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        # Extract obligations
        extraction_result = await lease_extractor.extract_obligations(
            document_content=request.document_content,
            document_id=request.document_id,
            extraction_rules=request.extraction_rules,
            focus_areas=request.focus_areas
        )
        
        # Generate extraction ID
        extraction_id = f"lease_extract_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Build response
        response = LeaseExtractionResponse(
            document_id=request.document_id,
            extraction_id=extraction_id,
            obligations=extraction_result["obligations"],
            summary=extraction_result["summary"],
            metadata={
                "extraction_timestamp": datetime.now().isoformat(),
                "content_length": len(request.document_content),
                "obligation_count": len(extraction_result["obligations"]),
                "focus_areas": request.focus_areas,
                "extraction_rules": request.extraction_rules
            }
        )
        
        logger.info(
            "✅ Lease obligation extraction completed",
            extraction_id=extraction_id,
            obligation_count=len(extraction_result["obligations"])
        )
        
        return response
        
    except Exception as e:
        logger.error("❌ Lease extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Lease extraction failed: {str(e)}")

# Lease comparison endpoint
@app.post("/api/v1/lease/compare", response_model=LeaseComparisonResponse)
async def compare_lease_obligations(request: ComparisonRequest):
    """
    Compare lease obligations across multiple documents
    
    Args:
        request: Comparison request with document IDs and focus areas
        
    Returns:
        Comparative analysis with risk scoring and negotiation opportunities
    """
    try:
        logger.info(
            "🔍 Starting lease comparison",
            document_count=len(request.document_ids),
            focus_areas=request.comparison_focus
        )
        
        if not obligation_analyzer:
            raise HTTPException(status_code=503, detail="Obligation analyzer not available")
        
        # Perform comparison
        comparison_result = await obligation_analyzer.compare_obligations(
            document_ids=request.document_ids,
            focus_areas=request.comparison_focus
        )
        
        # Generate comparison ID
        comparison_id = f"lease_compare_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Build response
        response = LeaseComparisonResponse(
            comparison_id=comparison_id,
            document_ids=request.document_ids,
            results=comparison_result["results"],
            overall_risk_score=comparison_result["overall_risk_score"],
            negotiation_summary=comparison_result["negotiation_summary"],
            recommendations=comparison_result["recommendations"]
        )
        
        logger.info(
            "✅ Lease comparison completed",
            comparison_id=comparison_id,
            risk_score=comparison_result["overall_risk_score"]
        )
        
        return response
        
    except Exception as e:
        logger.error("❌ Lease comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Lease comparison failed: {str(e)}")

# Configuration endpoint for extraction rules
@app.get("/api/v1/lease/config/rules")
async def get_extraction_rules():
    """Get available extraction rules and configurations"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        rules = await lease_extractor.get_available_rules()
        return {
            "obligation_types": rules["obligation_types"],
            "risk_categories": rules["risk_categories"],
            "negotiation_factors": rules["negotiation_factors"],
            "market_standards": rules["market_standards"]
        }
        
    except Exception as e:
        logger.error("❌ Failed to get extraction rules", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get extraction rules: {str(e)}")

# New endpoints for dynamic clause management and visual comparison

@app.get("/api/v1/lease/categories")
async def get_clause_categories():
    """Get all available clause categories"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        categories = await lease_extractor.get_clause_categories()
        return {
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error("❌ Failed to get clause categories", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get clause categories: {str(e)}")

@app.post("/api/v1/lease/categories")
async def add_clause_category(category_data: Dict[str, Any]):
    """Add a new custom clause category"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        category_id = category_data.get("category_id")
        if not category_id:
            raise HTTPException(status_code=400, detail="category_id is required")
        
        success = await lease_extractor.add_custom_clause_category(category_id, category_data)
        
        if success:
            return {"message": f"Category '{category_id}' added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add category")
        
    except Exception as e:
        logger.error("❌ Failed to add clause category", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add clause category: {str(e)}")

@app.put("/api/v1/lease/categories/{category_id}")
async def update_clause_category(category_id: str, updates: Dict[str, Any]):
    """Update an existing clause category"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        success = await lease_extractor.update_clause_category(category_id, updates)
        
        if success:
            return {"message": f"Category '{category_id}' updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Category not found")
        
    except Exception as e:
        logger.error("❌ Failed to update clause category", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update clause category: {str(e)}")

@app.delete("/api/v1/lease/categories/{category_id}")
async def remove_clause_category(category_id: str):
    """Remove a clause category"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        success = await lease_extractor.remove_clause_category(category_id)
        
        if success:
            return {"message": f"Category '{category_id}' removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Category not found")
        
    except Exception as e:
        logger.error("❌ Failed to remove clause category", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to remove clause category: {str(e)}")

@app.post("/api/v1/lease/compare-clauses")
async def compare_clauses(request: Dict[str, Any]):
    """Extract and compare clauses across multiple documents"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        documents = request.get("documents", [])
        focus_categories = request.get("focus_categories", [])
        
        if not documents:
            raise HTTPException(status_code=400, detail="documents list is required")
        
        comparison_result = await lease_extractor.extract_clauses_for_comparison(
            documents=documents,
            focus_categories=focus_categories
        )
        
        return comparison_result
        
    except Exception as e:
        logger.error("❌ Failed to compare clauses", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to compare clauses: {str(e)}")

@app.post("/api/v1/lease/compare-specific-clause")
async def compare_specific_clause(request: Dict[str, Any]):
    """Compare a specific clause across multiple documents"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        clause_text = request.get("clause_text")
        clause_category = request.get("clause_category")
        documents = request.get("documents", [])
        
        if not clause_text or not clause_category or not documents:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: clause_text, clause_category, documents"
            )
        
        logger.info("Starting specific clause comparison", 
                   clause_category=clause_category,
                   document_count=len(documents))
        
        # Extract clauses from all documents
        all_clauses = []
        for doc in documents:
            doc_id = doc["document_id"]
            doc_content = doc["content"]
            
            # Extract obligations for this document
            obligations = await lease_extractor.extract_obligations(
                document_content=doc_content,
                document_id=doc_id,
                focus_areas=[clause_category.lower()]
            )
            
            # Find similar clauses to the target clause
            similar_clauses = []
            for obligation in obligations["obligations"]:
                if obligation["obligation_type"] == clause_category:
                    # Check similarity to target clause
                    similarity = lease_extractor._clauses_are_similar(
                        {"text": clause_text}, 
                        {"text": obligation["clause_text"]}
                    )
                    if similarity:
                        similar_clauses.append({
                            "document_id": doc_id,
                            "document_metadata": doc.get("metadata", {}),
                            "clause_text": obligation["clause_text"],
                            "context": obligation["context"],
                            "risk_level": obligation["risk_level"],
                            "negotiation_leverage": obligation["negotiation_leverage"],
                            "market_standard": obligation["market_standard"],
                            "confidence": obligation["confidence"],
                            "extracted_fields": lease_extractor._extract_comparison_fields(obligation)
                        })
            
            all_clauses.extend(similar_clauses)
        
        # Group by similarity and build comparison
        comparison_result = {
            "target_clause": {
                "text": clause_text,
                "category": clause_category
            },
            "similar_clauses": all_clauses,
            "comparison_summary": {
                "total_matches": len(all_clauses),
                "documents_with_matches": len(set(clause["document_id"] for clause in all_clauses)),
                "risk_distribution": {},
                "leverage_distribution": {},
                "field_differences": []
            }
        }
        
        # Analyze risk and leverage distribution
        risk_counts = {}
        leverage_counts = {}
        for clause in all_clauses:
            risk_level = clause["risk_level"]
            leverage = clause["negotiation_leverage"]
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            leverage_counts[leverage] = leverage_counts.get(leverage, 0) + 1
        
        comparison_result["comparison_summary"]["risk_distribution"] = risk_counts
        comparison_result["comparison_summary"]["leverage_distribution"] = leverage_counts
        
        # Find field differences
        if len(all_clauses) > 1:
            field_differences = []
            for i, clause1 in enumerate(all_clauses):
                for clause2 in all_clauses[i+1:]:
                    diffs = lease_extractor._compare_extracted_fields(
                        clause1["extracted_fields"],
                        clause2["extracted_fields"]
                    )
                    if diffs:
                        field_differences.append({
                            "documents": [clause1["document_id"], clause2["document_id"]],
                            "differences": diffs
                        })
            comparison_result["comparison_summary"]["field_differences"] = field_differences
        
        logger.info("Specific clause comparison completed",
                   matches_found=len(all_clauses))
        
        return comparison_result
        
    except Exception as e:
        logger.error("❌ Failed to compare specific clause", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to compare specific clause: {str(e)}")

# Update extraction rules endpoint
@app.post("/api/v1/lease/config/rules")
async def update_extraction_rules(rules: Dict[str, Any]):
    """Update extraction rules and configurations"""
    try:
        if not lease_extractor:
            raise HTTPException(status_code=503, detail="Lease extractor not available")
        
        await lease_extractor.update_rules(rules)
        
        logger.info("✅ Extraction rules updated successfully")
        return {"message": "Extraction rules updated successfully"}
        
    except Exception as e:
        logger.error("❌ Failed to update extraction rules", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update extraction rules: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
