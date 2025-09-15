#!/usr/bin/env python3
"""
Obligation Analyzer
Comparative analysis engine for lease obligations across multiple documents
"""

import json
from typing import Dict, List, Any, Optional, Tuple
import structlog
from collections import defaultdict, Counter
import difflib

logger = structlog.get_logger(__name__)

class ObligationAnalyzer:
    """Analyzer for comparing lease obligations across multiple documents"""
    
    def __init__(self):
        # Market benchmark data (would typically come from a database)
        self.market_benchmarks = {
            "MAINTENANCE_OBLIGATIONS": {
                "standard_terms": ["reasonable maintenance", "normal wear and tear", "tenant responsibility"],
                "risk_indicators": ["unlimited", "all repairs", "any damage", "sole discretion"],
                "market_standard_score": 0.7
            },
            "RENEWAL_TERMS": {
                "standard_terms": ["option to renew", "mutual agreement", "notice period"],
                "risk_indicators": ["automatic renewal", "penalty for non-renewal", "mandatory"],
                "market_standard_score": 0.8
            },
            "TERMINATION_RIGHTS": {
                "standard_terms": ["breach of lease", "cure period", "notice requirements"],
                "risk_indicators": ["immediate termination", "no cure period", "sole discretion"],
                "market_standard_score": 0.6
            },
            "RENT_ESCALATION": {
                "standard_terms": ["annual increase", "CPI adjustment", "market rate"],
                "risk_indicators": ["unlimited increase", "compounding", "retroactive"],
                "market_standard_score": 0.75
            },
            "SECURITY_DEPOSIT": {
                "standard_terms": ["refundable", "damage deduction", "return conditions"],
                "risk_indicators": ["non-refundable", "forfeiture", "additional deposits"],
                "market_standard_score": 0.85
            },
            "INSURANCE_REQUIREMENTS": {
                "standard_terms": ["liability coverage", "property insurance", "commercial policy"],
                "risk_indicators": ["unlimited coverage", "additional insured", "waiver of subrogation"],
                "market_standard_score": 0.7
            },
            "ASSIGNMENT_RIGHTS": {
                "standard_terms": ["consent required", "assignment permitted", "subletting allowed"],
                "risk_indicators": ["prohibited", "restricted", "sole discretion"],
                "market_standard_score": 0.65
            },
            "IMPROVEMENT_OBLIGATIONS": {
                "standard_terms": ["approval required", "permanent improvements", "restoration"],
                "risk_indicators": ["no approval", "irreversible", "costly requirements"],
                "market_standard_score": 0.6
            },
            "COMPLIANCE_REQUIREMENTS": {
                "standard_terms": ["comply with law", "regulatory requirements", "building codes"],
                "risk_indicators": ["strict compliance", "immediate", "penalty"],
                "market_standard_score": 0.8
            },
            "FORCE_MAJEURE": {
                "standard_terms": ["unforeseeable", "beyond control", "act of god"],
                "risk_indicators": ["excluded events", "limited scope", "notice requirements"],
                "market_standard_score": 0.7
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
        
        logger.info("Obligation Analyzer initialized")

    async def compare_obligations(
        self, 
        document_ids: List[str], 
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare obligations across multiple documents
        
        Args:
            document_ids: List of document IDs to compare
            focus_areas: Specific areas to focus comparison on
            
        Returns:
            Comparative analysis results
        """
        try:
            logger.info("Starting obligation comparison", 
                       document_count=len(document_ids),
                       focus_areas=focus_areas)
            
            # This would typically fetch obligation data from a database
            # For now, we'll simulate the data structure
            obligations_data = await self._fetch_obligations_data(document_ids)
            
            if not obligations_data:
                return {
                    "results": [],
                    "overall_risk_score": 0,
                    "negotiation_summary": {},
                    "recommendations": ["No obligation data available for comparison"]
                }
            
            # Group obligations by type
            grouped_obligations = self._group_obligations_by_type(obligations_data)
            
            # Compare each obligation type across documents
            comparison_results = []
            for obligation_type, obligations in grouped_obligations.items():
                if focus_areas and obligation_type.lower() not in [area.lower() for area in focus_areas]:
                    continue
                    
                comparison_result = self._compare_obligation_type(obligation_type, obligations)
                comparison_results.append(comparison_result)
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(comparison_results)
            
            # Generate negotiation summary
            negotiation_summary = self._generate_negotiation_summary(comparison_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(comparison_results, overall_risk_score)
            
            logger.info("Obligation comparison completed",
                       risk_score=overall_risk_score,
                       comparison_count=len(comparison_results))
            
            return {
                "results": comparison_results,
                "overall_risk_score": overall_risk_score,
                "negotiation_summary": negotiation_summary,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error("Obligation comparison failed", error=str(e))
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
                    "market_standard": True
                },
                {
                    "obligation_type": "RENEWAL_TERMS",
                    "clause_text": "Option to renew for additional 5-year term",
                    "risk_level": "MEDIUM",
                    "negotiation_leverage": "LEVERAGE_HIGH",
                    "market_standard": True
                }
            ],
            "doc_2": [
                {
                    "obligation_type": "MAINTENANCE_OBLIGATIONS",
                    "clause_text": "Tenant responsible for all maintenance and repairs",
                    "risk_level": "HIGH",
                    "negotiation_leverage": "LEVERAGE_LOW",
                    "market_standard": False
                },
                {
                    "obligation_type": "RENEWAL_TERMS",
                    "clause_text": "Automatic renewal unless terminated",
                    "risk_level": "CRITICAL",
                    "negotiation_leverage": "LEVERAGE_NEGATIVE",
                    "market_standard": False
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

    def _compare_obligation_type(self, obligation_type: str, obligations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare obligations of a specific type across documents"""
        
        # Group by document
        by_document = defaultdict(list)
        for obligation in obligations:
            doc_id = obligation["document_id"]
            by_document[doc_id].append(obligation)
        
        # Analyze differences
        differences = self._identify_differences(obligations)
        
        # Assess risk
        risk_assessment = self._assess_obligation_risk(obligations, obligation_type)
        
        # Identify negotiation opportunities
        negotiation_opportunities = self._identify_negotiation_opportunities(obligations, obligation_type)
        
        # Get market benchmark
        market_benchmark = self._get_market_benchmark(obligation_type, obligations)
        
        return {
            "obligation_type": obligation_type,
            "documents": dict(by_document),
            "differences": differences,
            "risk_assessment": risk_assessment,
            "negotiation_opportunities": negotiation_opportunities,
            "market_benchmark": market_benchmark
        }

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
        
        # Compare clause text similarity
        clause_texts = [obl["clause_text"] for obl in obligations]
        similarity_scores = []
        for i in range(len(clause_texts)):
            for j in range(i + 1, len(clause_texts)):
                similarity = difflib.SequenceMatcher(None, clause_texts[i], clause_texts[j]).ratio()
                similarity_scores.append(similarity)
        
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            if avg_similarity < 0.5:
                differences.append(f"Clause text significantly different (avg similarity: {avg_similarity:.2f})")
        
        return differences

    def _assess_obligation_risk(self, obligations: List[Dict[str, Any]], obligation_type: str) -> str:
        """Assess overall risk for an obligation type across documents"""
        risk_scores = [self.risk_weights[obl["risk_level"]] for obl in obligations]
        avg_risk_score = sum(risk_scores) / len(risk_scores)
        
        # Get market benchmark for this obligation type
        market_benchmark = self.market_benchmarks.get(obligation_type, {}).get("market_standard_score", 0.5)
        
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
        
        return {
            "market_standard_score": benchmark.get("market_standard_score", 0.5),
            "current_compliance": compliance_percentage,
            "current_risk_score": avg_risk_score,
            "standard_terms": benchmark.get("standard_terms", []),
            "risk_indicators": benchmark.get("risk_indicators", []),
            "compliance_status": "ABOVE_MARKET" if compliance_percentage > benchmark.get("market_standard_score", 0.5) * 100 else "BELOW_MARKET"
        }

    def _calculate_overall_risk_score(self, comparison_results: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score across all obligation types"""
        if not comparison_results:
            return 0.0
        
        total_risk = 0
        total_weight = 0
        
        for result in comparison_results:
            obligation_type = result["obligation_type"]
            documents = result["documents"]
            
            # Calculate risk for this obligation type
            obligation_risks = []
            for doc_obligations in documents.values():
                for obligation in doc_obligations:
                    risk_score = self.risk_weights[obligation["risk_level"]]
                    obligation_risks.append(risk_score)
            
            if obligation_risks:
                avg_risk = sum(obligation_risks) / len(obligation_risks)
                # Weight by number of documents with this obligation
                weight = len(documents)
                total_risk += avg_risk * weight
                total_weight += weight
        
        return (total_risk / total_weight) * 25 if total_weight > 0 else 0.0  # Scale to 0-100

    def _generate_negotiation_summary(self, comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate negotiation summary across all obligation types"""
        summary = {
            "high_leverage_opportunities": 0,
            "standardization_opportunities": 0,
            "risk_balancing_opportunities": 0,
            "critical_attention_needed": 0,
            "overall_negotiation_potential": "LOW"
        }
        
        for result in comparison_results:
            opportunities = result["negotiation_opportunities"]
            
            for opportunity in opportunities:
                if "High negotiation leverage" in opportunity:
                    summary["high_leverage_opportunities"] += 1
                elif "Non-standard terms" in opportunity:
                    summary["standardization_opportunities"] += 1
                elif "Risk level variations" in opportunity:
                    summary["risk_balancing_opportunities"] += 1
                elif "Negative leverage" in opportunity:
                    summary["critical_attention_needed"] += 1
        
        # Determine overall negotiation potential
        total_opportunities = sum(summary.values())
        if total_opportunities >= 8:
            summary["overall_negotiation_potential"] = "HIGH"
        elif total_opportunities >= 4:
            summary["overall_negotiation_potential"] = "MEDIUM"
        else:
            summary["overall_negotiation_potential"] = "LOW"
        
        return summary

    def _generate_recommendations(self, comparison_results: List[Dict[str, Any]], overall_risk_score: float) -> List[str]:
        """Generate strategic recommendations based on comparison results"""
        recommendations = []
        
        # Risk-based recommendations
        if overall_risk_score >= 75:
            recommendations.append("CRITICAL: Overall risk score is very high - immediate review and renegotiation recommended")
        elif overall_risk_score >= 50:
            recommendations.append("HIGH: Risk score is elevated - consider renegotiating high-risk terms")
        elif overall_risk_score >= 25:
            recommendations.append("MEDIUM: Risk score is moderate - monitor and address specific high-risk areas")
        else:
            recommendations.append("LOW: Risk score is acceptable - maintain current terms with regular monitoring")
        
        # Opportunity-based recommendations
        high_leverage_count = sum(1 for result in comparison_results 
                                if any("High negotiation leverage" in opp for opp in result["negotiation_opportunities"]))
        if high_leverage_count > 0:
            recommendations.append(f"Leverage {high_leverage_count} high-negotiation-leverage opportunities to improve terms")
        
        non_standard_count = sum(1 for result in comparison_results 
                               if any("Non-standard terms" in opp for opp in result["negotiation_opportunities"]))
        if non_standard_count > 0:
            recommendations.append(f"Standardize {non_standard_count} non-standard terms to reduce complexity and risk")
        
        # Specific obligation type recommendations
        critical_obligations = [result for result in comparison_results 
                              if result["risk_assessment"].startswith("CRITICAL")]
        if critical_obligations:
            obligation_types = [result["obligation_type"] for result in critical_obligations]
            recommendations.append(f"Focus immediate attention on: {', '.join(obligation_types)}")
        
        # Market compliance recommendations
        below_market_count = sum(1 for result in comparison_results 
                               if result["market_benchmark"]["compliance_status"] == "BELOW_MARKET")
        if below_market_count > 0:
            recommendations.append(f"Improve market compliance for {below_market_count} obligation types")
        
        return recommendations
