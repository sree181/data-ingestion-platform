#!/usr/bin/env python3
"""
Negotiation Analyzer
Advanced negotiation leverage analysis and strategy recommendations
"""

import json
from typing import Dict, List, Any, Optional, Tuple
import structlog
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime

logger = structlog.get_logger(__name__)

class NegotiationAnalyzer:
    """Advanced negotiation leverage analysis and strategy recommendations"""
    
    def __init__(self):
        # Negotiation leverage categories
        self.leverage_categories = {
            "LEVERAGE_HIGH": {
                "score": 4,
                "description": "Strong negotiation position with favorable terms",
                "strategy": "AGGRESSIVE",
                "opportunities": ["Negotiate better terms", "Leverage for concessions", "Set favorable precedents"]
            },
            "LEVERAGE_MEDIUM": {
                "score": 3,
                "description": "Moderate negotiation opportunities available",
                "strategy": "BALANCED",
                "opportunities": ["Selective negotiation", "Target specific terms", "Build relationships"]
            },
            "LEVERAGE_LOW": {
                "score": 2,
                "description": "Limited negotiation leverage - standard terms",
                "strategy": "DEFENSIVE",
                "opportunities": ["Risk mitigation", "Protect current position", "Avoid concessions"]
            },
            "LEVERAGE_NEGATIVE": {
                "score": 1,
                "description": "Unfavorable terms - requires significant negotiation",
                "strategy": "URGENT",
                "opportunities": ["Immediate renegotiation", "Risk mitigation", "Exit strategies"]
            }
        }
        
        # Market position indicators
        self.market_position_indicators = {
            "STRONG": {
                "leverage_threshold": 75,
                "description": "Above market position with strong leverage",
                "recommendations": ["Maintain position", "Leverage for better terms", "Set market standards"]
            },
            "MODERATE": {
                "leverage_threshold": 50,
                "description": "At market position with balanced leverage",
                "recommendations": ["Optimize terms", "Selective improvements", "Maintain relationships"]
            },
            "WEAK": {
                "leverage_threshold": 25,
                "description": "Below market position with limited leverage",
                "recommendations": ["Improve terms", "Risk mitigation", "Strategic positioning"]
            }
        }
        
        # Negotiation strategies by obligation type
        self.negotiation_strategies = {
            "MAINTENANCE_OBLIGATIONS": {
                "high_leverage": [
                    "Negotiate specific maintenance responsibilities",
                    "Establish maintenance cost sharing",
                    "Define maintenance standards and procedures",
                    "Include maintenance reporting requirements"
                ],
                "low_leverage": [
                    "Minimize maintenance obligations",
                    "Define maintenance limitations",
                    "Establish maintenance cost caps",
                    "Include maintenance dispute resolution"
                ]
            },
            "RENEWAL_TERMS": {
                "high_leverage": [
                    "Negotiate favorable renewal terms",
                    "Establish renewal notice requirements",
                    "Define renewal rent adjustments",
                    "Include renewal option extensions"
                ],
                "low_leverage": [
                    "Protect against automatic renewal",
                    "Establish renewal termination rights",
                    "Define renewal rent caps",
                    "Include renewal condition requirements"
                ]
            },
            "TERMINATION_RIGHTS": {
                "high_leverage": [
                    "Negotiate favorable termination terms",
                    "Establish termination notice requirements",
                    "Define termination consequences",
                    "Include termination dispute resolution"
                ],
                "low_leverage": [
                    "Minimize termination obligations",
                    "Establish termination protections",
                    "Define termination cost limitations",
                    "Include termination notice requirements"
                ]
            },
            "RENT_ESCALATION": {
                "high_leverage": [
                    "Negotiate rent escalation caps",
                    "Establish objective escalation criteria",
                    "Define escalation notice requirements",
                    "Include escalation dispute resolution"
                ],
                "low_leverage": [
                    "Minimize rent escalation obligations",
                    "Establish escalation limitations",
                    "Define escalation cost sharing",
                    "Include escalation review rights"
                ]
            },
            "SECURITY_DEPOSIT": {
                "high_leverage": [
                    "Negotiate deposit amount and terms",
                    "Establish deposit return conditions",
                    "Define deposit interest provisions",
                    "Include deposit dispute resolution"
                ],
                "low_leverage": [
                    "Minimize deposit obligations",
                    "Establish deposit limitations",
                    "Define deposit return requirements",
                    "Include deposit protection provisions"
                ]
            },
            "INSURANCE_REQUIREMENTS": {
                "high_leverage": [
                    "Negotiate insurance coverage requirements",
                    "Establish insurance certificate requirements",
                    "Define insurance cost sharing",
                    "Include insurance dispute resolution"
                ],
                "low_leverage": [
                    "Minimize insurance obligations",
                    "Establish insurance limitations",
                    "Define insurance cost caps",
                    "Include insurance review rights"
                ]
            },
            "ASSIGNMENT_RIGHTS": {
                "high_leverage": [
                    "Negotiate assignment and subletting rights",
                    "Establish assignment procedures",
                    "Define assignment fees and terms",
                    "Include assignment dispute resolution"
                ],
                "low_leverage": [
                    "Minimize assignment restrictions",
                    "Establish assignment protections",
                    "Define assignment cost limitations",
                    "Include assignment review rights"
                ]
            },
            "IMPROVEMENT_OBLIGATIONS": {
                "high_leverage": [
                    "Negotiate improvement approval procedures",
                    "Establish improvement standards",
                    "Define improvement cost sharing",
                    "Include improvement dispute resolution"
                ],
                "low_leverage": [
                    "Minimize improvement obligations",
                    "Establish improvement limitations",
                    "Define improvement cost caps",
                    "Include improvement review rights"
                ]
            },
            "COMPLIANCE_REQUIREMENTS": {
                "high_leverage": [
                    "Negotiate compliance obligations",
                    "Establish compliance procedures",
                    "Define compliance cost sharing",
                    "Include compliance dispute resolution"
                ],
                "low_leverage": [
                    "Minimize compliance obligations",
                    "Establish compliance limitations",
                    "Define compliance cost caps",
                    "Include compliance review rights"
                ]
            },
            "FORCE_MAJEURE": {
                "high_leverage": [
                    "Negotiate force majeure provisions",
                    "Establish force majeure procedures",
                    "Define force majeure consequences",
                    "Include force majeure dispute resolution"
                ],
                "low_leverage": [
                    "Minimize force majeure obligations",
                    "Establish force majeure limitations",
                    "Define force majeure cost sharing",
                    "Include force majeure review rights"
                ]
            }
        }
        
        logger.info("Negotiation Analyzer initialized")

    async def analyze_negotiation(
        self,
        comparison_result: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze negotiation leverage and opportunities
        
        Args:
            comparison_result: Comparison results from comparison engine
            risk_analysis: Risk analysis results
            
        Returns:
            Comprehensive negotiation analysis
        """
        try:
            logger.info("Starting negotiation analysis")
            
            results = comparison_result.get("results", [])
            if not results:
                return {
                    "overall_leverage_score": 0,
                    "leverage_distribution": {},
                    "high_leverage_opportunities": [],
                    "negotiation_strategies": [],
                    "market_position": "WEAK"
                }
            
            # Calculate leverage scores for each obligation type
            obligation_leverage_scores = {}
            leverage_distribution = {"LEVERAGE_HIGH": 0, "LEVERAGE_MEDIUM": 0, "LEVERAGE_LOW": 0, "LEVERAGE_NEGATIVE": 0}
            high_leverage_opportunities = []
            negotiation_strategies = []
            
            for result in results:
                obligation_type = result["obligation_type"]
                documents = result["documents"]
                
                # Calculate leverage score for this obligation type
                obligation_leverage = self._calculate_obligation_leverage(obligation_type, documents)
                obligation_leverage_scores[obligation_type] = obligation_leverage
                
                # Update leverage distribution
                leverage_level = self._get_leverage_level(obligation_leverage)
                leverage_distribution[leverage_level] += 1
                
                # Identify high-leverage opportunities
                if leverage_level in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"]:
                    opportunities = self._identify_leverage_opportunities(obligation_type, documents, leverage_level)
                    high_leverage_opportunities.extend(opportunities)
                
                # Generate negotiation strategies
                strategies = self._generate_negotiation_strategies(obligation_type, documents, leverage_level)
                negotiation_strategies.extend(strategies)
            
            # Calculate overall leverage score
            overall_leverage_score = self._calculate_overall_leverage_score(obligation_leverage_scores)
            
            # Determine market position
            market_position = self._determine_market_position(overall_leverage_score)
            
            # Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(
                obligation_leverage_scores, risk_analysis, market_position
            )
            
            logger.info("Negotiation analysis completed",
                       overall_leverage_score=overall_leverage_score,
                       market_position=market_position)
            
            return {
                "overall_leverage_score": overall_leverage_score,
                "leverage_distribution": leverage_distribution,
                "high_leverage_opportunities": high_leverage_opportunities,
                "negotiation_strategies": negotiation_strategies,
                "market_position": market_position,
                "strategic_recommendations": strategic_recommendations
            }
            
        except Exception as e:
            logger.error("Negotiation analysis failed", error=str(e))
            raise

    async def analyze_documents(
        self,
        document_ids: List[str],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze negotiation leverage for specific documents
        
        Args:
            document_ids: List of document IDs to analyze
            focus_areas: Specific areas to focus on
            
        Returns:
            Document-specific negotiation analysis
        """
        try:
            logger.info("Starting document negotiation analysis",
                       document_count=len(document_ids),
                       focus_areas=focus_areas)
            
            # This would typically fetch obligation data from database
            # For now, we'll simulate the analysis
            document_leverages = {}
            overall_leverage_score = 0
            
            for doc_id in document_ids:
                # Simulate negotiation analysis for each document
                doc_leverage = self._simulate_document_negotiation_analysis(doc_id, focus_areas)
                document_leverages[doc_id] = doc_leverage
                overall_leverage_score += doc_leverage["leverage_score"]
            
            # Calculate average leverage score
            if document_ids:
                overall_leverage_score = overall_leverage_score / len(document_ids)
            
            # Generate document-specific recommendations
            recommendations = self._generate_document_recommendations(document_leverages)
            
            logger.info("Document negotiation analysis completed",
                       overall_leverage_score=overall_leverage_score)
            
            return {
                "document_leverages": document_leverages,
                "overall_leverage_score": overall_leverage_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error("Document negotiation analysis failed", error=str(e))
            raise

    def _calculate_obligation_leverage(self, obligation_type: str, documents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate leverage score for a specific obligation type"""
        if not documents:
            return 0.0
        
        total_leverage = 0
        total_weight = 0
        
        for doc_id, obligations in documents.items():
            for obligation in obligations:
                # Calculate individual obligation leverage
                obligation_leverage = self._calculate_individual_obligation_leverage(obligation, obligation_type)
                
                # Weight by confidence
                confidence = obligation.get("confidence", 0.5)
                weight = confidence
                
                total_leverage += obligation_leverage * weight
                total_weight += weight
        
        return total_leverage / total_weight if total_weight > 0 else 0.0

    def _calculate_individual_obligation_leverage(self, obligation: Dict[str, Any], obligation_type: str) -> float:
        """Calculate leverage score for an individual obligation"""
        # Base leverage from negotiation leverage
        negotiation_leverage = obligation.get("negotiation_leverage", "LEVERAGE_MEDIUM")
        base_leverage = self.leverage_categories[negotiation_leverage]["score"]
        
        # Adjust for market standard compliance
        market_standard = obligation.get("market_standard", True)
        if market_standard:
            base_leverage += 0.5  # Increase leverage for standard terms
        else:
            base_leverage -= 0.5  # Decrease leverage for non-standard terms
        
        # Adjust for risk level
        risk_level = obligation.get("risk_level", "MEDIUM")
        if risk_level == "LOW":
            base_leverage += 0.5  # Increase leverage for low-risk terms
        elif risk_level == "HIGH":
            base_leverage -= 0.5  # Decrease leverage for high-risk terms
        elif risk_level == "CRITICAL":
            base_leverage -= 1.0  # Significantly decrease leverage for critical risk
        
        # Adjust for obligation type specific factors
        type_leverage_adjustment = self._get_obligation_type_leverage_adjustment(obligation_type)
        base_leverage += type_leverage_adjustment
        
        return max(min(base_leverage, 4.0), 1.0)  # Cap between 1-4

    def _get_obligation_type_leverage_adjustment(self, obligation_type: str) -> float:
        """Get leverage adjustment based on obligation type"""
        # Some obligation types offer more negotiation leverage
        high_leverage_types = ["RENEWAL_TERMS", "RENT_ESCALATION", "ASSIGNMENT_RIGHTS"]
        medium_leverage_types = ["MAINTENANCE_OBLIGATIONS", "SECURITY_DEPOSIT", "INSURANCE_REQUIREMENTS"]
        
        if obligation_type in high_leverage_types:
            return 0.5
        elif obligation_type in medium_leverage_types:
            return 0.25
        else:
            return 0.0

    def _get_leverage_level(self, leverage_score: float) -> str:
        """Convert leverage score to leverage level"""
        if leverage_score >= 3.5:
            return "LEVERAGE_HIGH"
        elif leverage_score >= 2.5:
            return "LEVERAGE_MEDIUM"
        elif leverage_score >= 1.5:
            return "LEVERAGE_LOW"
        else:
            return "LEVERAGE_NEGATIVE"

    def _identify_leverage_opportunities(
        self,
        obligation_type: str,
        documents: Dict[str, List[Dict[str, Any]]],
        leverage_level: str
    ) -> List[str]:
        """Identify specific leverage opportunities for an obligation type"""
        opportunities = []
        
        # Count documents with this obligation type
        doc_count = len(documents)
        
        # Count high-leverage documents
        high_leverage_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if obligation.get("negotiation_leverage") in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"]:
                    high_leverage_count += 1
        
        if high_leverage_count > 0:
            opportunities.append(f"{obligation_type}: {high_leverage_count} high-leverage opportunities across {doc_count} documents")
        
        # Count standard terms that could be leveraged
        standard_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if obligation.get("market_standard", False):
                    standard_count += 1
        
        if standard_count > 0:
            opportunities.append(f"{obligation_type}: {standard_count} standard terms that could be leveraged for better deals")
        
        # Count low-risk terms that could be leveraged
        low_risk_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if obligation.get("risk_level") == "LOW":
                    low_risk_count += 1
        
        if low_risk_count > 0:
            opportunities.append(f"{obligation_type}: {low_risk_count} low-risk terms that provide negotiation leverage")
        
        return opportunities

    def _generate_negotiation_strategies(
        self,
        obligation_type: str,
        documents: Dict[str, List[Dict[str, Any]]],
        leverage_level: str
    ) -> List[str]:
        """Generate negotiation strategies for an obligation type"""
        strategies = []
        
        # Get base strategies for this obligation type
        if obligation_type in self.negotiation_strategies:
            if leverage_level in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"]:
                strategies.extend(self.negotiation_strategies[obligation_type]["high_leverage"])
            else:
                strategies.extend(self.negotiation_strategies[obligation_type]["low_leverage"])
        
        # Add leverage-specific strategies
        if leverage_level == "LEVERAGE_HIGH":
            strategies.append(f"Leverage strong position in {obligation_type} for better overall terms")
        elif leverage_level == "LEVERAGE_MEDIUM":
            strategies.append(f"Selectively negotiate {obligation_type} terms where beneficial")
        elif leverage_level == "LEVERAGE_LOW":
            strategies.append(f"Focus on risk mitigation for {obligation_type} terms")
        else:
            strategies.append(f"Urgently address unfavorable {obligation_type} terms")
        
        return strategies

    def _calculate_overall_leverage_score(self, obligation_leverage_scores: Dict[str, float]) -> float:
        """Calculate overall leverage score across all obligation types"""
        if not obligation_leverage_scores:
            return 0.0
        
        # Weight by obligation type importance
        type_weights = {
            "MAINTENANCE_OBLIGATIONS": 0.15,
            "RENEWAL_TERMS": 0.20,
            "TERMINATION_RIGHTS": 0.25,
            "RENT_ESCALATION": 0.15,
            "SECURITY_DEPOSIT": 0.10,
            "INSURANCE_REQUIREMENTS": 0.10,
            "ASSIGNMENT_RIGHTS": 0.05
        }
        
        total_weighted_leverage = 0
        total_weight = 0
        
        for obligation_type, leverage_score in obligation_leverage_scores.items():
            weight = type_weights.get(obligation_type, 0.05)  # Default weight for unknown types
            total_weighted_leverage += leverage_score * weight
            total_weight += weight
        
        return (total_weighted_leverage / total_weight) * 25 if total_weight > 0 else 0.0  # Scale to 0-100

    def _determine_market_position(self, overall_leverage_score: float) -> str:
        """Determine market position based on overall leverage score"""
        if overall_leverage_score >= 75:
            return "STRONG"
        elif overall_leverage_score >= 50:
            return "MODERATE"
        else:
            return "WEAK"

    def _generate_strategic_recommendations(
        self,
        obligation_leverage_scores: Dict[str, float],
        risk_analysis: Dict[str, Any],
        market_position: str
    ) -> List[str]:
        """Generate strategic recommendations based on leverage analysis"""
        recommendations = []
        
        # Market position recommendations
        if market_position == "STRONG":
            recommendations.append("STRONG POSITION: Leverage favorable market position for better terms")
            recommendations.append("MAINTAIN STANDARDS: Set and maintain high standards for future negotiations")
        elif market_position == "MODERATE":
            recommendations.append("MODERATE POSITION: Optimize current terms and build relationships")
            recommendations.append("SELECTIVE IMPROVEMENTS: Focus on high-impact negotiation opportunities")
        else:
            recommendations.append("WEAK POSITION: Focus on risk mitigation and strategic positioning")
            recommendations.append("IMPROVE TERMS: Prioritize improving unfavorable terms")
        
        # Risk-leverage balance recommendations
        overall_risk_score = risk_analysis.get("overall_risk_score", 0)
        if overall_risk_score >= 70 and market_position == "WEAK":
            recommendations.append("CRITICAL SITUATION: High risk and weak leverage - immediate action required")
        elif overall_risk_score >= 50 and market_position == "MODERATE":
            recommendations.append("BALANCED APPROACH: Moderate risk and leverage - focus on optimization")
        elif overall_risk_score <= 30 and market_position == "STRONG":
            recommendations.append("OPTIMAL POSITION: Low risk and strong leverage - capitalize on opportunities")
        
        # Obligation-specific recommendations
        for obligation_type, leverage_score in obligation_leverage_scores.items():
            if leverage_score >= 3.5:
                recommendations.append(f"LEVERAGE {obligation_type}: Strong leverage - negotiate for better terms")
            elif leverage_score <= 1.5:
                recommendations.append(f"PROTECT {obligation_type}: Weak leverage - focus on risk mitigation")
        
        return recommendations

    def _simulate_document_negotiation_analysis(self, doc_id: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simulate negotiation analysis for a document (for testing purposes)"""
        # This would typically analyze actual document data
        # For now, we'll return simulated results
        
        import random
        
        leverage_score = random.uniform(20, 80)  # Simulate leverage score between 20-80
        leverage_level = self._get_leverage_level(leverage_score / 25)  # Convert to 0-4 scale
        
        return {
            "document_id": doc_id,
            "leverage_score": leverage_score,
            "leverage_level": leverage_level,
            "leverage_opportunities": [
                "Simulated opportunity 1",
                "Simulated opportunity 2"
            ],
            "negotiation_strategies": [
                "Simulated strategy 1",
                "Simulated strategy 2"
            ]
        }

    def _generate_document_recommendations(self, document_leverages: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on document leverage analysis"""
        recommendations = []
        
        # Analyze overall leverage distribution
        leverage_scores = [doc["leverage_score"] for doc in document_leverages.values()]
        avg_leverage = sum(leverage_scores) / len(leverage_scores) if leverage_scores else 0
        
        if avg_leverage >= 70:
            recommendations.append("STRONG: Overall document leverage is strong - capitalize on opportunities")
        elif avg_leverage >= 50:
            recommendations.append("MODERATE: Document leverage is moderate - optimize and improve")
        elif avg_leverage >= 30:
            recommendations.append("WEAK: Document leverage is weak - focus on risk mitigation")
        else:
            recommendations.append("CRITICAL: Document leverage is very weak - immediate attention required")
        
        # Document-specific recommendations
        for doc_id, doc_leverage in document_leverages.items():
            if doc_leverage["leverage_score"] >= 60:
                recommendations.append(f"Document {doc_id}: Strong leverage - negotiate for better terms")
            elif doc_leverage["leverage_score"] >= 40:
                recommendations.append(f"Document {doc_id}: Moderate leverage - selective improvements")
            else:
                recommendations.append(f"Document {doc_id}: Weak leverage - focus on risk mitigation")
        
        return recommendations
