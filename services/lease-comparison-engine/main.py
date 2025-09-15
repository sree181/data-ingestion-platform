#!/usr/bin/env python3
"""
Lease Comparison Engine Service
Advanced comparative analysis and risk scoring for lease documents
"""

from fastapi import FastAPI, HTTPException, Depends
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
from processors.comparison_engine import ComparisonEngine
from processors.risk_scorer import RiskScorer
from processors.negotiation_analyzer import NegotiationAnalyzer

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
comparison_engine = None
risk_scorer = None
negotiation_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global comparison_engine, risk_scorer, negotiation_analyzer
    
    logger.info("🚀 Starting Lease Comparison Engine Service...")
    
    try:
        # Initialize services
        comparison_engine = ComparisonEngine()
        risk_scorer = RiskScorer()
        negotiation_analyzer = NegotiationAnalyzer()
        
        logger.info("✅ Lease Comparison Engine Service initialized")
        
        yield
        
    except Exception as e:
        logger.error("❌ Failed to start services", error=str(e))
        raise
    finally:
        logger.info("🔄 Lease Comparison Engine Service stopped")

# Create FastAPI app
app = FastAPI(
    title="Lease Comparison Engine",
    description="Advanced comparative analysis and risk scoring for lease documents",
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
class LeaseComparisonRequest(BaseModel):
    """Request model for lease comparison"""
    document_ids: List[str] = Field(..., description="List of document IDs to compare")
    comparison_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Comparison configuration and settings"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus comparison on"
    )
    risk_tolerance: Optional[str] = Field(
        default="MEDIUM",
        description="Risk tolerance level: LOW, MEDIUM, HIGH"
    )

class ComparisonResult(BaseModel):
    """Individual comparison result"""
    obligation_type: str = Field(..., description="Type of obligation being compared")
    documents: Dict[str, Any] = Field(..., description="Obligation data per document")
    differences: List[str] = Field(..., description="Key differences identified")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    negotiation_opportunities: List[str] = Field(..., description="Negotiation opportunities")
    market_benchmark: Dict[str, Any] = Field(..., description="Market benchmark data")
    similarity_score: float = Field(..., description="Similarity score between documents (0-1)")

class RiskAnalysis(BaseModel):
    """Risk analysis result"""
    overall_risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_distribution: Dict[str, int] = Field(..., description="Risk level distribution")
    high_risk_obligations: List[str] = Field(..., description="High-risk obligation types")
    risk_factors: List[str] = Field(..., description="Key risk factors identified")
    mitigation_strategies: List[str] = Field(..., description="Recommended mitigation strategies")

class NegotiationAnalysis(BaseModel):
    """Negotiation analysis result"""
    overall_leverage_score: float = Field(..., description="Overall negotiation leverage score (0-100)")
    leverage_distribution: Dict[str, int] = Field(..., description="Leverage level distribution")
    high_leverage_opportunities: List[str] = Field(..., description="High-leverage opportunities")
    negotiation_strategies: List[str] = Field(..., description="Recommended negotiation strategies")
    market_position: str = Field(..., description="Overall market position: STRONG, MODERATE, WEAK")

class LeaseComparisonResponse(BaseModel):
    """Response model for lease comparison"""
    comparison_id: str = Field(..., description="Unique comparison ID")
    document_ids: List[str] = Field(..., description="Compared document IDs")
    results: List[ComparisonResult] = Field(..., description="Comparison results")
    risk_analysis: RiskAnalysis = Field(..., description="Risk analysis")
    negotiation_analysis: NegotiationAnalysis = Field(..., description="Negotiation analysis")
    recommendations: List[str] = Field(..., description="Strategic recommendations")
    metadata: Dict[str, Any] = Field(..., description="Comparison metadata")

class BenchmarkRequest(BaseModel):
    """Request model for market benchmarking"""
    obligation_type: str = Field(..., description="Type of obligation to benchmark")
    current_terms: List[Dict[str, Any]] = Field(..., description="Current terms to benchmark")
    market_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional market data for benchmarking"
    )

class BenchmarkResponse(BaseModel):
    """Response model for market benchmarking"""
    obligation_type: str = Field(..., description="Type of obligation benchmarked")
    market_position: str = Field(..., description="Market position: ABOVE, AT, BELOW")
    benchmark_score: float = Field(..., description="Benchmark score (0-100)")
    market_standards: List[str] = Field(..., description="Market standard terms")
    improvement_opportunities: List[str] = Field(..., description="Improvement opportunities")
    competitive_advantages: List[str] = Field(..., description="Competitive advantages")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "lease-comparison-engine",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Main comparison endpoint
@app.post("/api/v1/lease/compare", response_model=LeaseComparisonResponse)
async def compare_leases(request: LeaseComparisonRequest):
    """
    Compare lease documents with advanced analysis
    
    Args:
        request: Lease comparison request with document IDs and configuration
        
    Returns:
        Comprehensive comparison analysis with risk scoring and negotiation insights
    """
    try:
        logger.info(
            "🔍 Starting comprehensive lease comparison",
            document_count=len(request.document_ids),
            focus_areas=request.focus_areas,
            risk_tolerance=request.risk_tolerance
        )
        
        if not comparison_engine:
            raise HTTPException(status_code=503, detail="Comparison engine not available")
        
        # Perform comprehensive comparison
        comparison_result = await comparison_engine.compare_documents(
            document_ids=request.document_ids,
            comparison_config=request.comparison_config,
            focus_areas=request.focus_areas
        )
        
        # Perform risk analysis
        risk_analysis = await risk_scorer.analyze_risk(
            comparison_result=comparison_result,
            risk_tolerance=request.risk_tolerance
        )
        
        # Perform negotiation analysis
        negotiation_analysis = await negotiation_analyzer.analyze_negotiation(
            comparison_result=comparison_result,
            risk_analysis=risk_analysis
        )
        
        # Generate strategic recommendations
        recommendations = await comparison_engine.generate_recommendations(
            comparison_result=comparison_result,
            risk_analysis=risk_analysis,
            negotiation_analysis=negotiation_analysis
        )
        
        # Generate comparison ID
        comparison_id = f"lease_compare_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Build response
        response = LeaseComparisonResponse(
            comparison_id=comparison_id,
            document_ids=request.document_ids,
            results=comparison_result["results"],
            risk_analysis=risk_analysis,
            negotiation_analysis=negotiation_analysis,
            recommendations=recommendations,
            metadata={
                "comparison_timestamp": datetime.now().isoformat(),
                "document_count": len(request.document_ids),
                "focus_areas": request.focus_areas,
                "risk_tolerance": request.risk_tolerance,
                "comparison_config": request.comparison_config
            }
        )
        
        logger.info(
            "✅ Comprehensive lease comparison completed",
            comparison_id=comparison_id,
            risk_score=risk_analysis.overall_risk_score,
            leverage_score=negotiation_analysis.overall_leverage_score
        )
        
        return response
        
    except Exception as e:
        logger.error("❌ Lease comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Lease comparison failed: {str(e)}")

# Market benchmarking endpoint
@app.post("/api/v1/lease/benchmark", response_model=BenchmarkResponse)
async def benchmark_lease_terms(request: BenchmarkRequest):
    """
    Benchmark lease terms against market standards
    
    Args:
        request: Benchmarking request with obligation type and current terms
        
    Returns:
        Market benchmark analysis with improvement opportunities
    """
    try:
        logger.info(
            "📊 Starting market benchmarking",
            obligation_type=request.obligation_type,
            term_count=len(request.current_terms)
        )
        
        if not comparison_engine:
            raise HTTPException(status_code=503, detail="Comparison engine not available")
        
        # Perform market benchmarking
        benchmark_result = await comparison_engine.benchmark_against_market(
            obligation_type=request.obligation_type,
            current_terms=request.current_terms,
            market_data=request.market_data
        )
        
        logger.info(
            "✅ Market benchmarking completed",
            obligation_type=request.obligation_type,
            benchmark_score=benchmark_result["benchmark_score"]
        )
        
        return BenchmarkResponse(**benchmark_result)
        
    except Exception as e:
        logger.error("❌ Market benchmarking failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Market benchmarking failed: {str(e)}")

# Risk analysis endpoint
@app.post("/api/v1/lease/risk/analyze")
async def analyze_lease_risk(
    document_ids: List[str],
    risk_tolerance: str = "MEDIUM",
    focus_areas: Optional[List[str]] = None
):
    """
    Perform detailed risk analysis on lease documents
    
    Args:
        document_ids: List of document IDs to analyze
        risk_tolerance: Risk tolerance level
        focus_areas: Specific areas to focus on
        
    Returns:
        Detailed risk analysis with mitigation strategies
    """
    try:
        logger.info(
            "⚠️ Starting risk analysis",
            document_count=len(document_ids),
            risk_tolerance=risk_tolerance,
            focus_areas=focus_areas
        )
        
        if not risk_scorer:
            raise HTTPException(status_code=503, detail="Risk scorer not available")
        
        # Perform risk analysis
        risk_analysis = await risk_scorer.analyze_documents(
            document_ids=document_ids,
            risk_tolerance=risk_tolerance,
            focus_areas=focus_areas
        )
        
        logger.info(
            "✅ Risk analysis completed",
            overall_risk_score=risk_analysis["overall_risk_score"]
        )
        
        return risk_analysis
        
    except Exception as e:
        logger.error("❌ Risk analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")

# Negotiation analysis endpoint
@app.post("/api/v1/lease/negotiation/analyze")
async def analyze_negotiation_leverage(
    document_ids: List[str],
    focus_areas: Optional[List[str]] = None
):
    """
    Analyze negotiation leverage and opportunities
    
    Args:
        document_ids: List of document IDs to analyze
        focus_areas: Specific areas to focus on
        
    Returns:
        Negotiation analysis with leverage opportunities
    """
    try:
        logger.info(
            "💼 Starting negotiation analysis",
            document_count=len(document_ids),
            focus_areas=focus_areas
        )
        
        if not negotiation_analyzer:
            raise HTTPException(status_code=503, detail="Negotiation analyzer not available")
        
        # Perform negotiation analysis
        negotiation_analysis = await negotiation_analyzer.analyze_documents(
            document_ids=document_ids,
            focus_areas=focus_areas
        )
        
        logger.info(
            "✅ Negotiation analysis completed",
            overall_leverage_score=negotiation_analysis["overall_leverage_score"]
        )
        
        return negotiation_analysis
        
    except Exception as e:
        logger.error("❌ Negotiation analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Negotiation analysis failed: {str(e)}")

# Configuration endpoints
@app.get("/api/v1/config/risk-tolerance")
async def get_risk_tolerance_levels():
    """Get available risk tolerance levels and their descriptions"""
    return {
        "risk_tolerance_levels": {
            "LOW": {
                "description": "Conservative approach - minimize risk exposure",
                "threshold": 25,
                "recommendations": ["Avoid high-risk terms", "Prefer standard market terms", "Require extensive protections"]
            },
            "MEDIUM": {
                "description": "Balanced approach - moderate risk acceptance",
                "threshold": 50,
                "recommendations": ["Accept some risk for better terms", "Negotiate balanced protections", "Consider market standards"]
            },
            "HIGH": {
                "description": "Aggressive approach - accept higher risk for better terms",
                "threshold": 75,
                "recommendations": ["Accept higher risk for better terms", "Focus on upside potential", "Minimize protective clauses"]
            }
        }
    }

@app.get("/api/v1/config/focus-areas")
async def get_focus_areas():
    """Get available focus areas for comparison and analysis"""
    return {
        "focus_areas": [
            "maintenance",
            "renewal",
            "termination",
            "rent",
            "security",
            "insurance",
            "assignment",
            "improvements",
            "compliance",
            "force_majeure"
        ],
        "descriptions": {
            "maintenance": "Maintenance and repair obligations",
            "renewal": "Lease renewal terms and options",
            "termination": "Termination rights and conditions",
            "rent": "Rent escalation and payment terms",
            "security": "Security deposit requirements",
            "insurance": "Insurance and liability requirements",
            "assignment": "Assignment and subletting rights",
            "improvements": "Tenant improvement obligations",
            "compliance": "Regulatory compliance requirements",
            "force_majeure": "Force majeure and emergency provisions"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )
