#!/usr/bin/env python3
"""
Comparison Engine
Advanced document comparison and analysis engine
"""

import json
from typing import Dict, List, Any, Optional, Tuple
import structlog
from collections import defaultdict, Counter
import difflib
import numpy as np
from datetime import datetime

logger = structlog.get_logger(__name__)

class ComparisonEngine:
    """Advanced comparison engine for lease documents"""
    
    def __init__(self):
        # Market benchmark data
        self.market_benchmarks = {
            "MAINTENANCE_OBLIGATIONS": {
                "standard_terms": ["reasonable maintenance", "normal wear and tear", "tenant responsibility"],
                "risk_indicators": ["unlimited", "all repairs", "any damage", "sole discretion"],
                "market_standard_score": 0.7,
                "typical_risk_level": "LOW"
            },
            "RENEWAL_TERMS": {
                "standard_terms": ["option to renew", "mutual agreement", "notice period"],
                "risk_indicators": ["automatic renewal", "penalty for non-renewal", "mandatory"],
                "market_standard_score": 0.8,
                "typical_risk_level": "MEDIUM"
            },
            "TERMINATION_RIGHTS": {
                "standard_terms": ["breach of lease", "cure period", "notice requirements"],
                "risk_indicators": ["immediate termination", "no cure period", "sole discretion"],
                "market_standard_score": 0.6,
                "typical_risk_level": "HIGH"
            },
            "RENT_ESCALATION": {
                "standard_terms": ["annual increase", "CPI adjustment", "market rate"],
                "risk_indicators": ["unlimited increase", "compounding", "retroactive"],
                "market_standard_score": 0.75,
                "typical_risk_level": "MEDIUM"
            },
            "SECURITY_DEPOSIT": {
                "standard_terms": ["refundable", "damage deduction", "return conditions"],
                "risk_indicators": ["non-refundable", "forfeiture", "additional deposits"],
                "market_standard_score": 0.85,
                "typical_risk_level": "LOW"
            },
            "INSURANCE_REQUIREMENTS": {
                "standard_terms": ["liability coverage", "property insurance", "commercial policy"],
                "risk_indicators": ["unlimited coverage", "additional insured", "waiver of subrogation"],
                "market_standard_score": 0.7,
                "typical_risk_level": "MEDIUM"
            },
            "ASSIGNMENT_RIGHTS": {
                "standard_terms": ["consent required", "assignment permitted", "subletting allowed"],
                "risk_indicators": ["prohibited", "restricted", "sole discretion"],
                "market_standard_score": 0.65,
                "typical_risk_level": "MEDIUM"
            },
            "IMPROVEMENT_OBLIGATIONS": {
                "standard_terms": ["approval required", "permanent improvements", "restoration"],
                "risk_indicators": ["no approval", "irreversible", "costly requirements"],
                "market_standard_score": 0.6,
                "typical_risk_level": "HIGH"
            },
            "COMPLIANCE_REQUIREMENTS": {
                "standard_terms": ["comply with law", "regulatory requirements", "building codes"],
                "risk_indicators": ["strict compliance", "immediate", "penalty"],
                "market_standard_score": 0.8,
                "typical_risk_level": "LOW"
            },
            "FORCE_MAJEURE": {
                "standard_terms": ["unforeseeable", "beyond control", "act of god"],
                "risk_indicators": ["excluded events", "limited scope", "notice requirements"],
                "market_standard_score": 0.7,
                "typical_risk_level": "MEDIUM"
            }
        }
        
        # Risk scoring weights
        self.risk_weights = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        
        # Negotiation leverage weights
        self.leverage_weights = {
            "LEVERAGE_HIGH": 4,
            "LEVERAGE_MEDIUM": 3,
            "LEVERAGE_LOW": 2,
            "LEVERAGE_NEGATIVE": 1
        }
        
        logger.info("Comparison Engine initialized")

    async def compare_documents(
        self,
        document_ids: List[str],
        comparison_config: Optional[Dict[str, Any]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare documents with advanced analysis
        
        Args:
            document_ids: List of document IDs to compare
            comparison_config: Comparison configuration
            focus_areas: Specific areas to focus on
            
        Returns:
            Comprehensive comparison results
        """
        try:
            logger.info("Starting document comparison",
                       document_count=len(document_ids),
                       focus_areas=focus_areas)
            
            # Fetch obligation data for documents
            obligations_data = await self._fetch_obligations_data(document_ids)
            
            if not obligations_data:
                return {
                    "results": [],
                    "summary": {"message": "No obligation data available for comparison"}
                }
            
            # Group obligations by type
            grouped_obligations = self._group_obligations_by_type(obligations_data)
            
            # Compare each obligation type
            comparison_results = []
            for obligation_type, obligations in grouped_obligations.items():
                if focus_areas and obligation_type.lower() not in [area.lower() for area in focus_areas]:
                    continue
                
                comparison_result = await self._compare_obligation_type(
                    obligation_type, obligations, comparison_config
                )
                comparison_results.append(comparison_result)
            
            # Calculate overall similarity
            overall_similarity = self._calculate_overall_similarity(comparison_results)
            
            # Generate summary
            summary = self._generate_comparison_summary(comparison_results, overall_similarity)
            
            logger.info("Document comparison completed",
                       result_count=len(comparison_results),
                       overall_similarity=overall_similarity)
            
            return {
                "results": comparison_results,
                "overall_similarity": overall_similarity,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Document comparison failed", error=str(e))
            raise

    async def _fetch_obligations_data(self, document_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch obligation data for documents
        In a real implementation, this would query a database
        """
        # Simulate data structure - in reality, this would come from the database
        # where obligations are stored after extraction
        sample_data = {
            "doc_1": [
                {
                    "obligation_type": "MAINTENANCE_OBLIGATIONS",
                    "clause_text": "Tenant shall maintain the premises in good condition",
                    "risk_level": "LOW",
                    "negotiation_leverage": "LEVERAGE_MEDIUM",
                    "market_standard": True,
                    "confidence": 0.9
                },
                {
                    "obligation_type": "RENEWAL_TERMS",
                    "clause_text": "Option to renew for additional 5-year term",
                    "risk_level": "MEDIUM",
                    "negotiation_leverage": "LEVERAGE_HIGH",
                    "market_standard": True,
                    "confidence": 0.85
                }
            ],
            "doc_2": [
                {
                    "obligation_type": "MAINTENANCE_OBLIGATIONS",
                    "clause_text": "Tenant responsible for all maintenance and repairs",
                    "risk_level": "HIGH",
                    "negotiation_leverage": "LEVERAGE_LOW",
                    "market_standard": False,
                    "confidence": 0.8
                },
                {
                    "obligation_type": "RENEWAL_TERMS",
                    "clause_text": "Automatic renewal unless terminated",
                    "risk_level": "CRITICAL",
                    "negotiation_leverage": "LEVERAGE_NEGATIVE",
                    "market_standard": False,
                    "confidence": 0.9
                }
            ]
        }
        
        return {doc_id: sample_data.get(doc_id, []) for doc_id in document_ids}

    def _group_obligations_by_type(self, obligations_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group obligations by type across all documents"""
        grouped = defaultdict(list)
        
        for doc_id, obligations in obligations_data.items():
            for obligation in obligations:
                obligation_type = obligation["obligation_type"]
                obligation_with_doc = {**obligation, "document_id": doc_id}
                grouped[obligation_type].append(obligation_with_doc)
        
        return dict(grouped)

    async def _compare_obligation_type(
        self,
        obligation_type: str,
        obligations: List[Dict[str, Any]],
        comparison_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compare obligations of a specific type across documents"""
        
        # Group by document
        by_document = defaultdict(list)
        for obligation in obligations:
            doc_id = obligation["document_id"]
            by_document[doc_id].append(obligation)
        
        # Calculate similarity scores
        similarity_scores = self._calculate_similarity_scores(obligations)
        
        # Analyze differences
        differences = self._identify_differences(obligations)
        
        # Assess risk
        risk_assessment = self._assess_obligation_risk(obligations, obligation_type)
        
        # Identify negotiation opportunities
        negotiation_opportunities = self._identify_negotiation_opportunities(obligations, obligation_type)
        
        # Get market benchmark
        market_benchmark = self._get_market_benchmark(obligation_type, obligations)
        
        # Calculate overall similarity for this obligation type
        avg_similarity = np.mean(similarity_scores) if similarity_scores else 0.0
        
        return {
            "obligation_type": obligation_type,
            "documents": dict(by_document),
            "differences": differences,
            "risk_assessment": risk_assessment,
            "negotiation_opportunities": negotiation_opportunities,
            "market_benchmark": market_benchmark,
            "similarity_score": float(avg_similarity)
        }

    def _calculate_similarity_scores(self, obligations: List[Dict[str, Any]]) -> List[float]:
        """Calculate similarity scores between obligation clauses"""
        if len(obligations) < 2:
            return [1.0]  # Single obligation is 100% similar to itself
        
        similarity_scores = []
        clause_texts = [obl["clause_text"] for obl in obligations]
        
        for i in range(len(clause_texts)):
            for j in range(i + 1, len(clause_texts)):
                similarity = difflib.SequenceMatcher(None, clause_texts[i], clause_texts[j]).ratio()
                similarity_scores.append(similarity)
        
        return similarity_scores

    def _identify_differences(self, obligations: List[Dict[str, Any]]) -> List[str]:
        """Identify key differences between obligations of the same type"""
        differences = []
        
        if len(obligations) < 2:
            return ["Only one document contains this obligation type"]
        
        # Compare risk levels
        risk_levels = [obl["risk_level"] for obl in obligations]
        if len(set(risk_levels)) > 1:
            risk_distribution = Counter(risk_levels)
            differences.append(f"Risk levels vary: {dict(risk_distribution)}")
        
        # Compare negotiation leverage
        leverage_levels = [obl["negotiation_leverage"] for obl in obligations]
        if len(set(leverage_levels)) > 1:
            leverage_distribution = Counter(leverage_levels)
            differences.append(f"Negotiation leverage varies: {dict(leverage_distribution)}")
        
        # Compare market standard compliance
        market_standards = [obl["market_standard"] for obl in obligations]
        if len(set(market_standards)) > 1:
            standard_count = sum(market_standards)
            differences.append(f"Market standard compliance: {standard_count}/{len(obligations)} documents")
        
        # Compare confidence scores
        confidence_scores = [obl["confidence"] for obl in obligations]
        if len(set(confidence_scores)) > 1:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            differences.append(f"Confidence scores vary (avg: {avg_confidence:.2f})")
        
        return differences

    def _assess_obligation_risk(self, obligations: List[Dict[str, Any]], obligation_type: str) -> str:
        """Assess overall risk for an obligation type across documents"""
        risk_scores = [self.risk_weights[obl["risk_level"]] for obl in obligations]
        avg_risk_score = sum(risk_scores) / len(risk_scores)
        
        # Get market benchmark for this obligation type
        market_benchmark = self.market_benchmarks.get(obligation_type, {}).get("market_standard_score", 0.5)
        typical_risk = self.market_benchmarks.get(obligation_type, {}).get("typical_risk_level", "MEDIUM")
        typical_risk_score = self.risk_weights[typical_risk]
        
        # Compare to market benchmark
        if avg_risk_score >= 3.5:
            return "CRITICAL - Significantly above market risk"
        elif avg_risk_score >= 2.5:
            return "HIGH - Above market risk"
        elif avg_risk_score >= 1.5:
            return "MEDIUM - Near market risk"
        else:
            return "LOW - Below market risk"

    def _identify_negotiation_opportunities(self, obligations: List[Dict[str, Any]], obligation_type: str) -> List[str]:
        """Identify negotiation opportunities for an obligation type"""
        opportunities = []
        
        # Find documents with high negotiation leverage
        high_leverage_docs = [obl for obl in obligations if obl["negotiation_leverage"] in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"]]
        if high_leverage_docs:
            opportunities.append(f"High negotiation leverage in {len(high_leverage_docs)} documents")
        
        # Find non-standard terms that could be negotiated
        non_standard_docs = [obl for obl in obligations if not obl["market_standard"]]
        if non_standard_docs:
            opportunities.append(f"Non-standard terms in {len(non_standard_docs)} documents - opportunity for standardization")
        
        # Find risk variations that could be balanced
        risk_levels = [obl["risk_level"] for obl in obligations]
        if len(set(risk_levels)) > 1:
            opportunities.append("Risk level variations present - opportunity to standardize terms")
        
        # Find documents with negative leverage that need attention
        negative_leverage_docs = [obl for obl in obligations if obl["negotiation_leverage"] == "LEVERAGE_NEGATIVE"]
        if negative_leverage_docs:
            opportunities.append(f"Negative leverage terms in {len(negative_leverage_docs)} documents - requires immediate attention")
        
        return opportunities

    def _get_market_benchmark(self, obligation_type: str, obligations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get market benchmark data for an obligation type"""
        benchmark = self.market_benchmarks.get(obligation_type, {})
        
        # Calculate current portfolio compliance
        market_standard_count = sum(1 for obl in obligations if obl["market_standard"])
        compliance_percentage = (market_standard_count / len(obligations)) * 100 if obligations else 0
        
        # Calculate average risk score
        risk_scores = [self.risk_weights[obl["risk_level"]] for obl in obligations]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Calculate average leverage score
        leverage_scores = [self.leverage_weights[obl["negotiation_leverage"]] for obl in obligations]
        avg_leverage_score = sum(leverage_scores) / len(leverage_scores) if leverage_scores else 0
        
        return {
            "market_standard_score": benchmark.get("market_standard_score", 0.5),
            "current_compliance": compliance_percentage,
            "current_risk_score": avg_risk_score,
            "current_leverage_score": avg_leverage_score,
            "standard_terms": benchmark.get("standard_terms", []),
            "risk_indicators": benchmark.get("risk_indicators", []),
            "compliance_status": "ABOVE_MARKET" if compliance_percentage > benchmark.get("market_standard_score", 0.5) * 100 else "BELOW_MARKET"
        }

    def _calculate_overall_similarity(self, comparison_results: List[Dict[str, Any]]) -> float:
        """Calculate overall similarity across all obligation types"""
        if not comparison_results:
            return 0.0
        
        similarity_scores = [result["similarity_score"] for result in comparison_results]
        return float(np.mean(similarity_scores))

    def _generate_comparison_summary(self, comparison_results: List[Dict[str, Any]], overall_similarity: float) -> Dict[str, Any]:
        """Generate summary of comparison results"""
        if not comparison_results:
            return {"message": "No comparison results available"}
        
        # Count obligation types
        obligation_types = [result["obligation_type"] for result in comparison_results]
        
        # Count risk assessments
        risk_assessments = [result["risk_assessment"] for result in comparison_results]
        risk_distribution = Counter(risk_assessments)
        
        # Count negotiation opportunities
        total_opportunities = sum(len(result["negotiation_opportunities"]) for result in comparison_results)
        
        # Count market compliance
        market_compliance = [result["market_benchmark"]["compliance_status"] for result in comparison_results]
        above_market_count = sum(1 for status in market_compliance if status == "ABOVE_MARKET")
        
        return {
            "total_obligation_types": len(obligation_types),
            "obligation_types": obligation_types,
            "overall_similarity": overall_similarity,
            "risk_distribution": dict(risk_distribution),
            "total_negotiation_opportunities": total_opportunities,
            "market_compliance": {
                "above_market": above_market_count,
                "below_market": len(market_compliance) - above_market_count
            },
            "similarity_interpretation": self._interpret_similarity(overall_similarity)
        }

    def _interpret_similarity(self, similarity: float) -> str:
        """Interpret similarity score"""
        if similarity >= 0.8:
            return "Very similar - documents are highly consistent"
        elif similarity >= 0.6:
            return "Moderately similar - some variations present"
        elif similarity >= 0.4:
            return "Somewhat different - significant variations present"
        else:
            return "Very different - documents are highly inconsistent"

    async def benchmark_against_market(
        self,
        obligation_type: str,
        current_terms: List[Dict[str, Any]],
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Benchmark current terms against market standards
        
        Args:
            obligation_type: Type of obligation to benchmark
            current_terms: Current terms to benchmark
            market_data: Additional market data
            
        Returns:
            Market benchmark analysis
        """
        try:
            logger.info("Starting market benchmarking", obligation_type=obligation_type)
            
            benchmark = self.market_benchmarks.get(obligation_type, {})
            
            # Calculate current terms metrics
            current_risk_scores = [self.risk_weights[term.get("risk_level", "MEDIUM")] for term in current_terms]
            avg_risk_score = sum(current_risk_scores) / len(current_risk_scores) if current_risk_scores else 0
            
            current_leverage_scores = [self.leverage_weights[term.get("negotiation_leverage", "LEVERAGE_MEDIUM")] for term in current_terms]
            avg_leverage_score = sum(current_leverage_scores) / len(current_leverage_scores) if current_leverage_scores else 0
            
            market_standard_count = sum(1 for term in current_terms if term.get("market_standard", False))
            compliance_percentage = (market_standard_count / len(current_terms)) * 100 if current_terms else 0
            
            # Calculate benchmark score
            benchmark_score = self._calculate_benchmark_score(
                compliance_percentage,
                avg_risk_score,
                avg_leverage_score,
                benchmark
            )
            
            # Determine market position
            market_position = self._determine_market_position(benchmark_score)
            
            # Generate improvement opportunities
            improvement_opportunities = self._generate_improvement_opportunities(
                current_terms, benchmark, market_position
            )
            
            # Generate competitive advantages
            competitive_advantages = self._generate_competitive_advantages(
                current_terms, benchmark, market_position
            )
            
            logger.info("Market benchmarking completed",
                       obligation_type=obligation_type,
                       benchmark_score=benchmark_score,
                       market_position=market_position)
            
            return {
                "obligation_type": obligation_type,
                "market_position": market_position,
                "benchmark_score": benchmark_score,
                "market_standards": benchmark.get("standard_terms", []),
                "improvement_opportunities": improvement_opportunities,
                "competitive_advantages": competitive_advantages
            }
            
        except Exception as e:
            logger.error("Market benchmarking failed", error=str(e))
            raise

    def _calculate_benchmark_score(
        self,
        compliance_percentage: float,
        avg_risk_score: float,
        avg_leverage_score: float,
        benchmark: Dict[str, Any]
    ) -> float:
        """Calculate overall benchmark score"""
        # Weight factors
        compliance_weight = 0.4
        risk_weight = 0.3
        leverage_weight = 0.3
        
        # Normalize scores
        compliance_score = compliance_percentage / 100
        risk_score = 1 - (avg_risk_score - 1) / 3  # Normalize 1-4 to 0-1
        leverage_score = (avg_leverage_score - 1) / 3  # Normalize 1-4 to 0-1
        
        # Calculate weighted score
        benchmark_score = (
            compliance_score * compliance_weight +
            risk_score * risk_weight +
            leverage_score * leverage_weight
        )
        
        return min(max(benchmark_score * 100, 0), 100)  # Scale to 0-100

    def _determine_market_position(self, benchmark_score: float) -> str:
        """Determine market position based on benchmark score"""
        if benchmark_score >= 80:
            return "ABOVE"
        elif benchmark_score >= 60:
            return "AT"
        else:
            return "BELOW"

    def _generate_improvement_opportunities(
        self,
        current_terms: List[Dict[str, Any]],
        benchmark: Dict[str, Any],
        market_position: str
    ) -> List[str]:
        """Generate improvement opportunities based on current terms"""
        opportunities = []
        
        # Check market standard compliance
        non_standard_count = sum(1 for term in current_terms if not term.get("market_standard", False))
        if non_standard_count > 0:
            opportunities.append(f"Standardize {non_standard_count} non-standard terms to improve market compliance")
        
        # Check risk levels
        high_risk_count = sum(1 for term in current_terms if term.get("risk_level") in ["HIGH", "CRITICAL"])
        if high_risk_count > 0:
            opportunities.append(f"Address {high_risk_count} high-risk terms to reduce overall risk exposure")
        
        # Check negotiation leverage
        low_leverage_count = sum(1 for term in current_terms if term.get("negotiation_leverage") in ["LEVERAGE_LOW", "LEVERAGE_NEGATIVE"])
        if low_leverage_count > 0:
            opportunities.append(f"Improve negotiation leverage for {low_leverage_count} terms")
        
        # Market position specific opportunities
        if market_position == "BELOW":
            opportunities.append("Overall terms are below market standards - consider comprehensive review")
        elif market_position == "AT":
            opportunities.append("Terms are at market level - consider optimization for competitive advantage")
        else:
            opportunities.append("Terms are above market - maintain current standards and consider leveraging for better deals")
        
        return opportunities

    def _generate_competitive_advantages(
        self,
        current_terms: List[Dict[str, Any]],
        benchmark: Dict[str, Any],
        market_position: str
    ) -> List[str]:
        """Generate competitive advantages based on current terms"""
        advantages = []
        
        # Market standard compliance advantages
        standard_count = sum(1 for term in current_terms if term.get("market_standard", False))
        if standard_count > 0:
            advantages.append(f"Strong market compliance with {standard_count} standard terms")
        
        # Low risk advantages
        low_risk_count = sum(1 for term in current_terms if term.get("risk_level") == "LOW")
        if low_risk_count > 0:
            advantages.append(f"Low risk exposure with {low_risk_count} low-risk terms")
        
        # High leverage advantages
        high_leverage_count = sum(1 for term in current_terms if term.get("negotiation_leverage") in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"])
        if high_leverage_count > 0:
            advantages.append(f"Strong negotiation position with {high_leverage_count} high-leverage terms")
        
        # Market position advantages
        if market_position == "ABOVE":
            advantages.append("Above-market terms provide competitive advantage in negotiations")
        elif market_position == "AT":
            advantages.append("Market-standard terms provide solid foundation for negotiations")
        
        return advantages

    async def generate_recommendations(
        self,
        comparison_result: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        negotiation_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate strategic recommendations based on analysis results"""
        recommendations = []
        
        # Risk-based recommendations
        overall_risk_score = risk_analysis.get("overall_risk_score", 0)
        if overall_risk_score >= 75:
            recommendations.append("CRITICAL: High overall risk score - immediate risk mitigation required")
        elif overall_risk_score >= 50:
            recommendations.append("HIGH: Elevated risk score - develop risk mitigation strategies")
        elif overall_risk_score >= 25:
            recommendations.append("MEDIUM: Moderate risk level - monitor and address specific risks")
        else:
            recommendations.append("LOW: Acceptable risk level - maintain current risk management")
        
        # Negotiation-based recommendations
        overall_leverage_score = negotiation_analysis.get("overall_leverage_score", 0)
        if overall_leverage_score >= 75:
            recommendations.append("STRONG: High negotiation leverage - capitalize on favorable position")
        elif overall_leverage_score >= 50:
            recommendations.append("MODERATE: Good negotiation position - identify key leverage points")
        elif overall_leverage_score >= 25:
            recommendations.append("WEAK: Limited negotiation leverage - focus on risk mitigation")
        else:
            recommendations.append("CRITICAL: Very weak negotiation position - immediate attention required")
        
        # Similarity-based recommendations
        overall_similarity = comparison_result.get("overall_similarity", 0)
        if overall_similarity < 0.5:
            recommendations.append("HIGH VARIANCE: Documents are very different - standardize terms for consistency")
        elif overall_similarity < 0.7:
            recommendations.append("MODERATE VARIANCE: Some document differences - consider standardization")
        else:
            recommendations.append("CONSISTENT: Documents are similar - maintain current standards")
        
        # Market compliance recommendations
        market_compliance = comparison_result.get("summary", {}).get("market_compliance", {})
        below_market_count = market_compliance.get("below_market", 0)
        if below_market_count > 0:
            recommendations.append(f"MARKET COMPLIANCE: {below_market_count} obligation types below market - improve compliance")
        
        return recommendations
