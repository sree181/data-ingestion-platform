#!/usr/bin/env python3
"""
Risk Scorer
Advanced risk analysis and scoring for lease obligations
"""

import json
from typing import Dict, List, Any, Optional, Tuple
import structlog
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime

logger = structlog.get_logger(__name__)

class RiskScorer:
    """Advanced risk analysis and scoring for lease obligations"""
    
    def __init__(self):
        # Risk category definitions
        self.risk_categories = {
            "CRITICAL": {
                "score": 4,
                "description": "Extreme risk requiring immediate attention",
                "threshold": 75,
                "mitigation_priority": "IMMEDIATE"
            },
            "HIGH": {
                "score": 3,
                "description": "Significant risk requiring attention",
                "threshold": 50,
                "mitigation_priority": "HIGH"
            },
            "MEDIUM": {
                "score": 2,
                "description": "Moderate risk requiring monitoring",
                "threshold": 25,
                "mitigation_priority": "MEDIUM"
            },
            "LOW": {
                "score": 1,
                "description": "Low risk, acceptable level",
                "threshold": 0,
                "mitigation_priority": "LOW"
            }
        }
        
        # Risk factor weights
        self.risk_factor_weights = {
            "obligation_type": 0.3,
            "risk_level": 0.4,
            "market_standard": 0.2,
            "negotiation_leverage": 0.1
        }
        
        # Risk mitigation strategies
        self.mitigation_strategies = {
            "MAINTENANCE_OBLIGATIONS": [
                "Define specific maintenance responsibilities",
                "Establish maintenance standards and procedures",
                "Include maintenance cost sharing provisions",
                "Require regular maintenance reporting"
            ],
            "RENEWAL_TERMS": [
                "Clarify renewal notice requirements",
                "Establish renewal terms and conditions",
                "Include renewal option expiration dates",
                "Define renewal rent adjustment mechanisms"
            ],
            "TERMINATION_RIGHTS": [
                "Establish clear termination procedures",
                "Define cure periods for breaches",
                "Include termination notice requirements",
                "Clarify termination consequences"
            ],
            "RENT_ESCALATION": [
                "Cap annual rent increases",
                "Base increases on objective criteria (CPI, market rates)",
                "Include rent review mechanisms",
                "Provide advance notice of increases"
            ],
            "SECURITY_DEPOSIT": [
                "Define deposit amount and terms",
                "Establish deposit return conditions",
                "Include deposit interest provisions",
                "Clarify deposit deduction procedures"
            ],
            "INSURANCE_REQUIREMENTS": [
                "Specify required insurance coverage",
                "Establish insurance certificate requirements",
                "Include additional insured provisions",
                "Define insurance renewal obligations"
            ],
            "ASSIGNMENT_RIGHTS": [
                "Clarify assignment and subletting rights",
                "Establish consent procedures",
                "Include assignment fee provisions",
                "Define assignment restrictions"
            ],
            "IMPROVEMENT_OBLIGATIONS": [
                "Define improvement approval procedures",
                "Establish improvement standards",
                "Include restoration requirements",
                "Clarify improvement ownership"
            ],
            "COMPLIANCE_REQUIREMENTS": [
                "Specify compliance obligations",
                "Establish compliance monitoring",
                "Include compliance reporting requirements",
                "Define compliance consequences"
            ],
            "FORCE_MAJEURE": [
                "Define force majeure events",
                "Establish force majeure procedures",
                "Include force majeure consequences",
                "Clarify force majeure limitations"
            ]
        }
        
        logger.info("Risk Scorer initialized")

    async def analyze_risk(
        self,
        comparison_result: Dict[str, Any],
        risk_tolerance: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Analyze risk across all obligation types
        
        Args:
            comparison_result: Comparison results from comparison engine
            risk_tolerance: Risk tolerance level (LOW, MEDIUM, HIGH)
            
        Returns:
            Comprehensive risk analysis
        """
        try:
            logger.info("Starting risk analysis", risk_tolerance=risk_tolerance)
            
            results = comparison_result.get("results", [])
            if not results:
                return {
                    "overall_risk_score": 0,
                    "risk_distribution": {},
                    "high_risk_obligations": [],
                    "risk_factors": [],
                    "mitigation_strategies": []
                }
            
            # Calculate risk scores for each obligation type
            obligation_risk_scores = {}
            risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            high_risk_obligations = []
            risk_factors = []
            
            for result in results:
                obligation_type = result["obligation_type"]
                documents = result["documents"]
                
                # Calculate risk score for this obligation type
                obligation_risk = self._calculate_obligation_risk(obligation_type, documents)
                obligation_risk_scores[obligation_type] = obligation_risk
                
                # Update risk distribution
                risk_level = self._get_risk_level(obligation_risk)
                risk_distribution[risk_level] += 1
                
                # Identify high-risk obligations
                if risk_level in ["HIGH", "CRITICAL"]:
                    high_risk_obligations.append({
                        "obligation_type": obligation_type,
                        "risk_score": obligation_risk,
                        "risk_level": risk_level,
                        "documents_affected": list(documents.keys())
                    })
                
                # Identify risk factors
                obligation_risk_factors = self._identify_risk_factors(obligation_type, documents)
                risk_factors.extend(obligation_risk_factors)
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(obligation_risk_scores)
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(high_risk_obligations, risk_factors)
            
            # Assess risk tolerance compliance
            risk_tolerance_assessment = self._assess_risk_tolerance(overall_risk_score, risk_tolerance)
            
            logger.info("Risk analysis completed",
                       overall_risk_score=overall_risk_score,
                       high_risk_count=len(high_risk_obligations))
            
            return {
                "overall_risk_score": overall_risk_score,
                "risk_distribution": risk_distribution,
                "high_risk_obligations": high_risk_obligations,
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
                "risk_tolerance_assessment": risk_tolerance_assessment
            }
            
        except Exception as e:
            logger.error("Risk analysis failed", error=str(e))
            raise

    async def analyze_documents(
        self,
        document_ids: List[str],
        risk_tolerance: str = "MEDIUM",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze risk for specific documents
        
        Args:
            document_ids: List of document IDs to analyze
            risk_tolerance: Risk tolerance level
            focus_areas: Specific areas to focus on
            
        Returns:
            Document-specific risk analysis
        """
        try:
            logger.info("Starting document risk analysis",
                       document_count=len(document_ids),
                       focus_areas=focus_areas)
            
            # This would typically fetch obligation data from database
            # For now, we'll simulate the analysis
            document_risks = {}
            overall_risk_score = 0
            
            for doc_id in document_ids:
                # Simulate risk analysis for each document
                doc_risk = self._simulate_document_risk_analysis(doc_id, focus_areas)
                document_risks[doc_id] = doc_risk
                overall_risk_score += doc_risk["risk_score"]
            
            # Calculate average risk score
            if document_ids:
                overall_risk_score = overall_risk_score / len(document_ids)
            
            # Generate document-specific recommendations
            recommendations = self._generate_document_recommendations(document_risks, risk_tolerance)
            
            logger.info("Document risk analysis completed",
                       overall_risk_score=overall_risk_score)
            
            return {
                "document_risks": document_risks,
                "overall_risk_score": overall_risk_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error("Document risk analysis failed", error=str(e))
            raise

    def _calculate_obligation_risk(self, obligation_type: str, documents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate risk score for a specific obligation type"""
        if not documents:
            return 0.0
        
        total_risk = 0
        total_weight = 0
        
        for doc_id, obligations in documents.items():
            for obligation in obligations:
                # Calculate individual obligation risk
                obligation_risk = self._calculate_individual_obligation_risk(obligation, obligation_type)
                
                # Weight by confidence
                confidence = obligation.get("confidence", 0.5)
                weight = confidence
                
                total_risk += obligation_risk * weight
                total_weight += weight
        
        return total_risk / total_weight if total_weight > 0 else 0.0

    def _calculate_individual_obligation_risk(self, obligation: Dict[str, Any], obligation_type: str) -> float:
        """Calculate risk score for an individual obligation"""
        # Base risk from risk level
        risk_level = obligation.get("risk_level", "MEDIUM")
        base_risk = self.risk_categories[risk_level]["score"]
        
        # Adjust for market standard compliance
        market_standard = obligation.get("market_standard", True)
        if not market_standard:
            base_risk += 0.5  # Increase risk for non-standard terms
        
        # Adjust for negotiation leverage
        negotiation_leverage = obligation.get("negotiation_leverage", "LEVERAGE_MEDIUM")
        if negotiation_leverage == "LEVERAGE_NEGATIVE":
            base_risk += 1.0  # Increase risk for negative leverage
        elif negotiation_leverage == "LEVERAGE_LOW":
            base_risk += 0.5  # Increase risk for low leverage
        
        # Adjust for obligation type specific factors
        type_risk_adjustment = self._get_obligation_type_risk_adjustment(obligation_type)
        base_risk += type_risk_adjustment
        
        return min(base_risk, 4.0)  # Cap at maximum risk level

    def _get_obligation_type_risk_adjustment(self, obligation_type: str) -> float:
        """Get risk adjustment based on obligation type"""
        # Some obligation types are inherently riskier
        high_risk_types = ["TERMINATION_RIGHTS", "IMPROVEMENT_OBLIGATIONS", "FORCE_MAJEURE"]
        medium_risk_types = ["RENEWAL_TERMS", "RENT_ESCALATION", "ASSIGNMENT_RIGHTS"]
        
        if obligation_type in high_risk_types:
            return 0.5
        elif obligation_type in medium_risk_types:
            return 0.25
        else:
            return 0.0

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 3.5:
            return "CRITICAL"
        elif risk_score >= 2.5:
            return "HIGH"
        elif risk_score >= 1.5:
            return "MEDIUM"
        else:
            return "LOW"

    def _identify_risk_factors(self, obligation_type: str, documents: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Identify specific risk factors for an obligation type"""
        risk_factors = []
        
        # Check for non-standard terms
        non_standard_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if not obligation.get("market_standard", True):
                    non_standard_count += 1
        
        if non_standard_count > 0:
            risk_factors.append(f"Non-standard terms in {non_standard_count} obligations")
        
        # Check for high-risk terms
        high_risk_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if obligation.get("risk_level") in ["HIGH", "CRITICAL"]:
                    high_risk_count += 1
        
        if high_risk_count > 0:
            risk_factors.append(f"High-risk terms in {high_risk_count} obligations")
        
        # Check for negative leverage
        negative_leverage_count = 0
        for obligations in documents.values():
            for obligation in obligations:
                if obligation.get("negotiation_leverage") == "LEVERAGE_NEGATIVE":
                    negative_leverage_count += 1
        
        if negative_leverage_count > 0:
            risk_factors.append(f"Negative negotiation leverage in {negative_leverage_count} obligations")
        
        # Check for inconsistency across documents
        if len(documents) > 1:
            risk_levels = []
            for obligations in documents.values():
                for obligation in obligations:
                    risk_levels.append(obligation.get("risk_level", "MEDIUM"))
            
            if len(set(risk_levels)) > 1:
                risk_factors.append("Inconsistent risk levels across documents")
        
        return risk_factors

    def _calculate_overall_risk_score(self, obligation_risk_scores: Dict[str, float]) -> float:
        """Calculate overall risk score across all obligation types"""
        if not obligation_risk_scores:
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
        
        total_weighted_risk = 0
        total_weight = 0
        
        for obligation_type, risk_score in obligation_risk_scores.items():
            weight = type_weights.get(obligation_type, 0.05)  # Default weight for unknown types
            total_weighted_risk += risk_score * weight
            total_weight += weight
        
        return (total_weighted_risk / total_weight) * 25 if total_weight > 0 else 0.0  # Scale to 0-100

    def _generate_mitigation_strategies(
        self,
        high_risk_obligations: List[Dict[str, Any]],
        risk_factors: List[str]
    ) -> List[str]:
        """Generate mitigation strategies based on risk analysis"""
        strategies = []
        
        # Generate strategies for high-risk obligations
        for obligation in high_risk_obligations:
            obligation_type = obligation["obligation_type"]
            if obligation_type in self.mitigation_strategies:
                strategies.extend(self.mitigation_strategies[obligation_type])
        
        # Generate general risk mitigation strategies
        if "Non-standard terms" in str(risk_factors):
            strategies.append("Standardize non-standard terms to reduce complexity and risk")
        
        if "High-risk terms" in str(risk_factors):
            strategies.append("Negotiate high-risk terms to more acceptable levels")
        
        if "Negative negotiation leverage" in str(risk_factors):
            strategies.append("Improve negotiation leverage through better terms and conditions")
        
        if "Inconsistent risk levels" in str(risk_factors):
            strategies.append("Standardize risk levels across all documents for consistency")
        
        # Remove duplicates and return
        return list(set(strategies))

    def _assess_risk_tolerance(self, overall_risk_score: float, risk_tolerance: str) -> Dict[str, Any]:
        """Assess compliance with risk tolerance level"""
        tolerance_thresholds = {
            "LOW": 25,
            "MEDIUM": 50,
            "HIGH": 75
        }
        
        threshold = tolerance_thresholds.get(risk_tolerance, 50)
        
        if overall_risk_score <= threshold:
            status = "COMPLIANT"
            message = f"Risk score ({overall_risk_score:.1f}) is within {risk_tolerance} tolerance threshold ({threshold})"
        else:
            status = "NON_COMPLIANT"
            message = f"Risk score ({overall_risk_score:.1f}) exceeds {risk_tolerance} tolerance threshold ({threshold})"
        
        return {
            "status": status,
            "message": message,
            "risk_score": overall_risk_score,
            "threshold": threshold,
            "tolerance_level": risk_tolerance
        }

    def _simulate_document_risk_analysis(self, doc_id: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simulate risk analysis for a document (for testing purposes)"""
        # This would typically analyze actual document data
        # For now, we'll return simulated results
        
        import random
        
        risk_score = random.uniform(20, 80)  # Simulate risk score between 20-80
        risk_level = self._get_risk_level(risk_score / 25)  # Convert to 0-4 scale
        
        return {
            "document_id": doc_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": [
                "Simulated risk factor 1",
                "Simulated risk factor 2"
            ],
            "mitigation_opportunities": [
                "Simulated mitigation 1",
                "Simulated mitigation 2"
            ]
        }

    def _generate_document_recommendations(
        self,
        document_risks: Dict[str, Any],
        risk_tolerance: str
    ) -> List[str]:
        """Generate recommendations based on document risk analysis"""
        recommendations = []
        
        # Analyze overall risk distribution
        risk_scores = [doc["risk_score"] for doc in document_risks.values()]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        if avg_risk >= 70:
            recommendations.append("CRITICAL: Overall document risk is very high - immediate review required")
        elif avg_risk >= 50:
            recommendations.append("HIGH: Document risk is elevated - develop mitigation strategies")
        elif avg_risk >= 30:
            recommendations.append("MEDIUM: Document risk is moderate - monitor and address specific issues")
        else:
            recommendations.append("LOW: Document risk is acceptable - maintain current risk management")
        
        # Document-specific recommendations
        for doc_id, doc_risk in document_risks.items():
            if doc_risk["risk_score"] >= 60:
                recommendations.append(f"Document {doc_id}: High risk - focus on risk mitigation")
            elif doc_risk["risk_score"] >= 40:
                recommendations.append(f"Document {doc_id}: Moderate risk - monitor and address issues")
        
        return recommendations
