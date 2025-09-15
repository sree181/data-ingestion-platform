
#!/usr/bin/env python3
"""
Lease Clause Extractor
Specialized processor for extracting lease-specific obligations and clauses
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
import structlog
import openai
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

class LeaseClauseExtractor:
    """Dynamic extractor for lease obligations and clauses with visual comparison support"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
        # Dynamic clause configuration - can be updated via API
        self.clause_config = {
            "categories": {
                "MAINTENANCE": {
                    "display_name": "Maintenance & Repairs",
                    "description": "Obligations related to property maintenance and repairs",
                    "keywords": ["maintenance", "repair", "upkeep", "care", "condition", "service"],
                    "patterns": [
                        r"tenant\s+shall\s+maintain",
                        r"lessee\s+agrees\s+to\s+keep",
                        r"obligation\s+to\s+repair",
                        r"responsible\s+for\s+maintenance"
                    ],
                    "risk_indicators": ["unlimited", "all", "any", "reasonable", "necessary"],
                    "comparison_fields": ["scope", "responsibility", "cost_sharing", "standards"]
                },
                "RENEWAL": {
                    "display_name": "Renewal & Extension",
                    "description": "Lease renewal options and extension terms",
                    "keywords": ["renewal", "extension", "option", "term", "period"],
                    "patterns": [
                        r"option\s+to\s+renew",
                        r"renewal\s+term",
                        r"extend\s+the\s+lease",
                        r"additional\s+period"
                    ],
                    "risk_indicators": ["automatic", "mandatory", "penalty", "notice"],
                    "comparison_fields": ["notice_period", "renewal_terms", "rent_adjustment", "conditions"]
                },
                "TERMINATION": {
                    "display_name": "Termination Rights",
                    "description": "Termination procedures and conditions",
                    "keywords": ["termination", "terminate", "end", "expire", "cancel"],
                    "patterns": [
                        r"right\s+to\s+terminate",
                        r"early\s+termination",
                        r"breach\s+of\s+lease",
                        r"default\s+provisions"
                    ],
                    "risk_indicators": ["immediate", "without notice", "penalty", "forfeiture"],
                    "comparison_fields": ["notice_period", "cure_period", "consequences", "fees"]
                },
                "RENT": {
                    "display_name": "Rent & Escalation",
                    "description": "Rent payment and escalation mechanisms",
                    "keywords": ["rent", "rental", "escalation", "increase", "adjustment"],
                    "patterns": [
                        r"rent\s+increase",
                        r"annual\s+escalation",
                        r"cost\s+of\s+living",
                        r"market\s+rate"
                    ],
                    "risk_indicators": ["unlimited", "automatic", "compounding", "retroactive"],
                    "comparison_fields": ["base_rent", "escalation_method", "frequency", "caps"]
                },
                "SECURITY": {
                    "display_name": "Security Deposits",
                    "description": "Security deposit terms and conditions",
                    "keywords": ["security", "deposit", "bond", "guarantee", "collateral"],
                    "patterns": [
                        r"security\s+deposit",
                        r"refundable\s+deposit",
                        r"damage\s+deposit",
                        r"performance\s+bond"
                    ],
                    "risk_indicators": ["non-refundable", "forfeiture", "deduction", "additional"],
                    "comparison_fields": ["amount", "refund_conditions", "interest", "forfeiture"]
                },
                "INSURANCE": {
                    "display_name": "Insurance Requirements",
                    "description": "Insurance coverage obligations",
                    "keywords": ["insurance", "coverage", "policy", "liability", "indemnity"],
                    "patterns": [
                        r"maintain\s+insurance",
                        r"liability\s+coverage",
                        r"property\s+insurance",
                        r"indemnification"
                    ],
                    "risk_indicators": ["unlimited", "comprehensive", "additional", "waiver"],
                    "comparison_fields": ["coverage_types", "limits", "additional_insured", "certificates"]
                },
                "ASSIGNMENT": {
                    "display_name": "Assignment & Subletting",
                    "description": "Assignment and subletting rights",
                    "keywords": ["assignment", "transfer", "sublet", "assign", "convey"],
                    "patterns": [
                        r"assignment\s+of\s+lease",
                        r"transfer\s+rights",
                        r"subletting\s+provisions",
                        r"consent\s+required"
                    ],
                    "risk_indicators": ["prohibited", "restricted", "consent", "approval"],
                    "comparison_fields": ["permitted_activities", "consent_requirements", "fees", "restrictions"]
                },
                "IMPROVEMENTS": {
                    "display_name": "Tenant Improvements",
                    "description": "Tenant improvement obligations and rights",
                    "keywords": ["improvement", "alteration", "modification", "construction", "renovation"],
                    "patterns": [
                        r"tenant\s+improvements",
                        r"alterations\s+permitted",
                        r"construction\s+obligations",
                        r"restoration\s+requirements"
                    ],
                    "risk_indicators": ["permanent", "irreversible", "cost", "approval"],
                    "comparison_fields": ["approval_process", "cost_responsibility", "ownership", "restoration"]
                },
                "COMPLIANCE": {
                    "display_name": "Regulatory Compliance",
                    "description": "Regulatory compliance obligations",
                    "keywords": ["compliance", "regulation", "law", "code", "standard"],
                    "patterns": [
                        r"comply\s+with\s+law",
                        r"regulatory\s+requirements",
                        r"building\s+codes",
                        r"environmental\s+standards"
                    ],
                    "risk_indicators": ["strict", "immediate", "penalty", "liability"],
                    "comparison_fields": ["compliance_scope", "reporting_requirements", "penalties", "standards"]
                },
                "FORCE_MAJEURE": {
                    "display_name": "Force Majeure",
                    "description": "Force majeure and emergency provisions",
                    "keywords": ["force majeure", "act of god", "unforeseeable", "beyond control"],
                    "patterns": [
                        r"force\s+majeure",
                        r"act\s+of\s+god",
                        r"unforeseeable\s+circumstances",
                        r"beyond\s+reasonable\s+control"
                    ],
                    "risk_indicators": ["excluded", "limited", "notice", "mitigation"],
                    "comparison_fields": ["covered_events", "notice_requirements", "consequences", "mitigation"]
                }
            },
            "comparison_settings": {
                "enable_visual_comparison": True,
                "group_by_category": True,
                "highlight_differences": True,
                "show_risk_scores": True,
                "show_negotiation_leverage": True
            }
        }
        
        # Risk assessment criteria
        self.risk_categories = {
            "LOW": {"score": 1, "description": "Standard market terms with minimal risk"},
            "MEDIUM": {"score": 2, "description": "Some unusual terms requiring attention"},
            "HIGH": {"score": 3, "description": "Significant risk factors present"},
            "CRITICAL": {"score": 4, "description": "Extreme risk requiring immediate attention"}
        }
        
        # Negotiation leverage factors
        self.negotiation_factors = {
            "LEVERAGE_HIGH": "Strong negotiation position - favorable terms",
            "LEVERAGE_MEDIUM": "Moderate negotiation opportunities available",
            "LEVERAGE_LOW": "Limited negotiation leverage - standard terms",
            "LEVERAGE_NEGATIVE": "Unfavorable terms - requires significant negotiation"
        }
        
        logger.info("Lease Clause Extractor initialized", 
                   categories=len(self.clause_config["categories"]),
                   model=model)

    async def extract_obligations(
        self, 
        document_content: str, 
        document_id: str,
        extraction_rules: Optional[Dict[str, Any]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract lease obligations from document content
        
        Args:
            document_content: Full document text
            document_id: Document identifier
            extraction_rules: Custom extraction rules
            focus_areas: Specific areas to focus on
            
        Returns:
            Dictionary containing extracted obligations and analysis
        """
        try:
            logger.info("Starting lease obligation extraction", 
                       document_id=document_id,
                       content_length=len(document_content),
                       focus_areas=focus_areas)
            
            # Determine which obligation types to extract
            target_types = self._determine_target_types(focus_areas)
            
            # Extract obligations using pattern matching
            pattern_results = self._extract_by_patterns(document_content, target_types)
            
            # Extract obligations using AI
            ai_results = await self._extract_by_ai(document_content, target_types, extraction_rules)
            
            # Combine and deduplicate results
            combined_results = self._combine_results(pattern_results, ai_results)
            
            # Analyze and score obligations
            analyzed_obligations = self._analyze_obligations(combined_results, document_content)
            
            # Generate summary
            summary = self._generate_summary(analyzed_obligations, document_id)
            
            logger.info("Lease obligation extraction completed",
                       document_id=document_id,
                       obligation_count=len(analyzed_obligations))
            
            return {
                "obligations": analyzed_obligations,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Lease obligation extraction failed", 
                        error=str(e), document_id=document_id)
            raise

    def _determine_target_types(self, focus_areas: Optional[List[str]]) -> List[str]:
        """Determine which obligation types to extract based on focus areas"""
        if not focus_areas:
            return list(self.clause_config["categories"].keys())
        
        # Map focus areas to obligation types
        focus_mapping = {
            "maintenance": ["MAINTENANCE"],
            "renewal": ["RENEWAL"],
            "termination": ["TERMINATION"],
            "rent": ["RENT"],
            "security": ["SECURITY"],
            "insurance": ["INSURANCE"],
            "assignment": ["ASSIGNMENT"],
            "improvements": ["IMPROVEMENTS"],
            "compliance": ["COMPLIANCE"],
            "force_majeure": ["FORCE_MAJEURE"]
        }
        
        target_types = []
        for area in focus_areas:
            if area.lower() in focus_mapping:
                target_types.extend(focus_mapping[area.lower()])
        
        return target_types if target_types else list(self.clause_config["categories"].keys())

    def _extract_by_patterns(self, content: str, target_types: List[str]) -> List[Dict[str, Any]]:
        """Extract obligations using regex patterns"""
        results = []
        
        for obligation_type in target_types:
            if obligation_type not in self.clause_config["categories"]:
                continue
                
            type_config = self.clause_config["categories"][obligation_type]
            patterns = type_config.get("patterns", [])
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    start_char = match.start()
                    end_char = match.end()
                    clause_text = match.group()
                    
                    # Get context around the match
                    context_start = max(0, start_char - 200)
                    context_end = min(len(content), end_char + 200)
                    context = content[context_start:context_end]
                    
                    results.append({
                        "obligation_type": obligation_type,
                        "clause_text": clause_text,
                        "start_char": start_char,
                        "end_char": end_char,
                        "context": context,
                        "extraction_method": "pattern",
                        "confidence": 0.8
                    })
        
        return results

    async def _extract_by_ai(
        self, 
        content: str, 
        target_types: List[str],
        extraction_rules: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract obligations using AI"""
        try:
            # Build prompt for AI extraction
            prompt = self._build_extraction_prompt(content, target_types, extraction_rules)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal document analysis expert specializing in lease agreements. Extract specific obligations and clauses with precise character positions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            return self._parse_ai_response(ai_content, content)
            
        except Exception as e:
            logger.error("AI extraction failed", error=str(e))
            return []

    def _build_extraction_prompt(
        self, 
        content: str, 
        target_types: List[str],
        extraction_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for AI extraction"""
        
        obligation_descriptions = []
        for obligation_type in target_types:
            if obligation_type in self.clause_config["categories"]:
                keywords = self.clause_config["categories"][obligation_type].get("keywords", [])
                obligation_descriptions.append(f"- {obligation_type}: {', '.join(keywords)}")
        
        prompt = f"""
Analyze the following lease document and extract specific obligations and clauses.

TARGET OBLIGATION TYPES:
{chr(10).join(obligation_descriptions)}

For each obligation found, provide:
1. Obligation type
2. Exact clause text
3. Start and end character positions
4. Surrounding context (200 characters before and after)
5. Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)
6. Negotiation leverage potential (LEVERAGE_HIGH, LEVERAGE_MEDIUM, LEVERAGE_LOW, LEVERAGE_NEGATIVE)
7. Whether it's a standard market term (true/false)

DOCUMENT CONTENT:
{content[:8000]}  # Limit content to avoid token limits

Return results in JSON format:
{{
    "obligations": [
        {{
            "obligation_type": "MAINTENANCE_OBLIGATIONS",
            "clause_text": "exact text here",
            "start_char": 1234,
            "end_char": 1456,
            "context": "surrounding context",
            "risk_level": "MEDIUM",
            "negotiation_leverage": "LEVERAGE_MEDIUM",
            "market_standard": true
        }}
    ]
}}
"""
        return prompt

    def _parse_ai_response(self, ai_content: str, document_content: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract obligations"""
        try:
            # Extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
            if not json_match:
                return []
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            obligations = []
            for obligation in data.get("obligations", []):
                # Validate character positions
                start_char = obligation.get("start_char", 0)
                end_char = obligation.get("end_char", 0)
                
                if start_char < len(document_content) and end_char <= len(document_content):
                    obligations.append({
                        "obligation_type": obligation.get("obligation_type", ""),
                        "clause_text": obligation.get("clause_text", ""),
                        "start_char": start_char,
                        "end_char": end_char,
                        "context": obligation.get("context", ""),
                        "extraction_method": "ai",
                        "confidence": 0.9,
                        "risk_level": obligation.get("risk_level", "MEDIUM"),
                        "negotiation_leverage": obligation.get("negotiation_leverage", "LEVERAGE_MEDIUM"),
                        "market_standard": obligation.get("market_standard", True)
                    })
            
            return obligations
            
        except Exception as e:
            logger.error("Failed to parse AI response", error=str(e))
            return []

    def _combine_results(
        self, 
        pattern_results: List[Dict[str, Any]], 
        ai_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from different extraction methods"""
        combined = []
        seen_positions = set()
        
        # Add pattern results
        for result in pattern_results:
            position_key = (result["start_char"], result["end_char"])
            if position_key not in seen_positions:
                combined.append(result)
                seen_positions.add(position_key)
        
        # Add AI results (avoiding duplicates)
        for result in ai_results:
            position_key = (result["start_char"], result["end_char"])
            if position_key not in seen_positions:
                combined.append(result)
                seen_positions.add(position_key)
        
        return combined

    def _analyze_obligations(
        self, 
        obligations: List[Dict[str, Any]], 
        document_content: str
    ) -> List[Dict[str, Any]]:
        """Analyze and score obligations"""
        analyzed = []
        
        for obligation in obligations:
            # Calculate confidence score
            confidence = self._calculate_confidence(obligation, document_content)
            
            # Assess risk level
            risk_level = self._assess_risk_level(obligation)
            
            # Determine negotiation leverage
            negotiation_leverage = self._assess_negotiation_leverage(obligation)
            
            # Check if it's a market standard
            market_standard = self._check_market_standard(obligation)
            
            analyzed.append({
                "obligation_type": obligation["obligation_type"],
                "clause_text": obligation["clause_text"],
                "start_char": obligation["start_char"],
                "end_char": obligation["end_char"],
                "confidence": confidence,
                "context": obligation["context"],
                "risk_level": risk_level,
                "negotiation_leverage": negotiation_leverage,
                "market_standard": market_standard
            })
        
        return analyzed

    def _calculate_confidence(self, obligation: Dict[str, Any], document_content: str) -> float:
        """Calculate confidence score for an obligation"""
        base_confidence = obligation.get("confidence", 0.5)
        
        # Boost confidence for longer, more specific clauses
        clause_length = len(obligation["clause_text"])
        if clause_length > 100:
            base_confidence += 0.1
        elif clause_length > 50:
            base_confidence += 0.05
        
        # Boost confidence for AI extraction
        if obligation.get("extraction_method") == "ai":
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

    def _assess_risk_level(self, obligation: Dict[str, Any]) -> str:
        """Assess risk level for an obligation"""
        obligation_type = obligation["obligation_type"]
        clause_text = obligation["clause_text"].lower()
        
        # Get risk factors for this obligation type
        risk_factors = self.clause_config["categories"].get(obligation_type, {}).get("risk_indicators", [])
        
        # Count high-risk keywords
        high_risk_count = sum(1 for factor in risk_factors if factor.lower() in clause_text)
        
        if high_risk_count >= 3:
            return "CRITICAL"
        elif high_risk_count >= 2:
            return "HIGH"
        elif high_risk_count >= 1:
            return "MEDIUM"
        else:
            return "LOW"

    def _assess_negotiation_leverage(self, obligation: Dict[str, Any]) -> str:
        """Assess negotiation leverage for an obligation"""
        clause_text = obligation["clause_text"].lower()
        
        # High leverage indicators
        high_leverage_terms = ["reasonable", "mutual", "agreed", "negotiated", "flexible"]
        high_leverage_count = sum(1 for term in high_leverage_terms if term in clause_text)
        
        # Low leverage indicators
        low_leverage_terms = ["unlimited", "absolute", "sole discretion", "non-negotiable", "mandatory"]
        low_leverage_count = sum(1 for term in low_leverage_terms if term in clause_text)
        
        if low_leverage_count >= 2:
            return "LEVERAGE_NEGATIVE"
        elif high_leverage_count >= 2:
            return "LEVERAGE_HIGH"
        elif high_leverage_count >= 1:
            return "LEVERAGE_MEDIUM"
        else:
            return "LEVERAGE_LOW"

    def _check_market_standard(self, obligation: Dict[str, Any]) -> bool:
        """Check if obligation represents standard market terms"""
        obligation_type = obligation["obligation_type"]
        clause_text = obligation["clause_text"].lower()
        
        # Standard terms for each obligation type
        standard_terms = {
            "MAINTENANCE_OBLIGATIONS": ["reasonable", "normal wear", "tenant responsibility"],
            "RENEWAL_TERMS": ["option", "notice", "mutual agreement"],
            "TERMINATION_RIGHTS": ["breach", "notice", "cure period"],
            "RENT_ESCALATION": ["annual", "cpi", "market rate"],
            "SECURITY_DEPOSIT": ["refundable", "damage", "return"],
            "INSURANCE_REQUIREMENTS": ["liability", "property", "commercial"],
            "ASSIGNMENT_RIGHTS": ["consent", "approval", "assignment"],
            "IMPROVEMENT_OBLIGATIONS": ["approval", "permanent", "restoration"],
            "COMPLIANCE_REQUIREMENTS": ["law", "regulation", "code"],
            "FORCE_MAJEURE": ["unforeseeable", "beyond control", "act of god"]
        }
        
        standard_keywords = standard_terms.get(obligation_type, [])
        return any(keyword in clause_text for keyword in standard_keywords)

    def _generate_summary(self, obligations: List[Dict[str, Any]], document_id: str) -> Dict[str, Any]:
        """Generate summary of extracted obligations"""
        if not obligations:
            return {
                "total_obligations": 0,
                "risk_distribution": {},
                "leverage_distribution": {},
                "market_standard_percentage": 0,
                "high_risk_obligations": [],
                "negotiation_opportunities": []
            }
        
        # Count by obligation type
        type_counts = {}
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        leverage_counts = {"LEVERAGE_HIGH": 0, "LEVERAGE_MEDIUM": 0, "LEVERAGE_LOW": 0, "LEVERAGE_NEGATIVE": 0}
        market_standard_count = 0
        
        for obligation in obligations:
            # Count by type
            obligation_type = obligation["obligation_type"]
            type_counts[obligation_type] = type_counts.get(obligation_type, 0) + 1
            
            # Count by risk level
            risk_level = obligation["risk_level"]
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            
            # Count by leverage
            leverage = obligation["negotiation_leverage"]
            leverage_counts[leverage] = leverage_counts.get(leverage, 0) + 1
            
            # Count market standards
            if obligation["market_standard"]:
                market_standard_count += 1
        
        # Identify high-risk obligations
        high_risk_obligations = [
            {
                "type": obl["obligation_type"],
                "clause": obl["clause_text"][:100] + "..." if len(obl["clause_text"]) > 100 else obl["clause_text"],
                "risk_level": obl["risk_level"]
            }
            for obl in obligations if obl["risk_level"] in ["HIGH", "CRITICAL"]
        ]
        
        # Identify negotiation opportunities
        negotiation_opportunities = [
            {
                "type": obl["obligation_type"],
                "clause": obl["clause_text"][:100] + "..." if len(obl["clause_text"]) > 100 else obl["clause_text"],
                "leverage": obl["negotiation_leverage"]
            }
            for obl in obligations if obl["negotiation_leverage"] in ["LEVERAGE_HIGH", "LEVERAGE_MEDIUM"]
        ]
        
        return {
            "total_obligations": len(obligations),
            "obligation_type_distribution": type_counts,
            "risk_distribution": risk_counts,
            "leverage_distribution": leverage_counts,
            "market_standard_percentage": (market_standard_count / len(obligations)) * 100,
            "high_risk_obligations": high_risk_obligations,
            "negotiation_opportunities": negotiation_opportunities
        }

    async def get_available_rules(self) -> Dict[str, Any]:
        """Get available extraction rules and configurations"""
        return {
            "obligation_types": list(self.clause_config["categories"].keys()),
            "risk_categories": self.risk_categories,
            "negotiation_factors": self.negotiation_factors,
            "market_standards": {
                "standard_terms": "Terms commonly found in market-standard leases",
                "non_standard_terms": "Terms that deviate from market standards",
                "red_flag_terms": "Terms that indicate high risk or unfavorable conditions"
            }
        }

    async def update_rules(self, rules: Dict[str, Any]) -> None:
        """Update extraction rules and configurations"""
        # Update obligation types if provided
        if "obligation_types" in rules:
            self.obligation_types.update(rules["obligation_types"])
        
        # Update risk categories if provided
        if "risk_categories" in rules:
            self.risk_categories.update(rules["risk_categories"])
        
        # Update negotiation factors if provided
        if "negotiation_factors" in rules:
            self.negotiation_factors.update(rules["negotiation_factors"])
        
        logger.info("Extraction rules updated successfully")

    # New methods for dynamic clause management and visual comparison
    
    async def add_custom_clause_category(self, category_id: str, category_config: Dict[str, Any]) -> bool:
        """Add a new custom clause category for extraction"""
        try:
            self.clause_config["categories"][category_id.upper()] = category_config
            logger.info("Custom clause category added", category_id=category_id)
            return True
        except Exception as e:
            logger.error("Failed to add custom clause category", error=str(e))
            return False

    async def update_clause_category(self, category_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing clause category"""
        try:
            if category_id.upper() in self.clause_config["categories"]:
                self.clause_config["categories"][category_id.upper()].update(updates)
                logger.info("Clause category updated", category_id=category_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to update clause category", error=str(e))
            return False

    async def remove_clause_category(self, category_id: str) -> bool:
        """Remove a clause category"""
        try:
            if category_id.upper() in self.clause_config["categories"]:
                del self.clause_config["categories"][category_id.upper()]
                logger.info("Clause category removed", category_id=category_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to remove clause category", error=str(e))
            return False

    async def get_clause_categories(self) -> Dict[str, Any]:
        """Get all available clause categories"""
        return self.clause_config["categories"]

    async def extract_clauses_for_comparison(
        self, 
        documents: List[Dict[str, Any]], 
        focus_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract clauses from multiple documents for visual comparison
        
        Args:
            documents: List of documents with content and metadata
            focus_categories: Specific categories to focus on
            
        Returns:
            Structured data for visual comparison
        """
        try:
            logger.info("Starting multi-document clause extraction for comparison",
                       document_count=len(documents),
                       focus_categories=focus_categories)
            
            comparison_data = {
                "documents": {},
                "clause_categories": {},
                "comparison_matrix": {},
                "differences": {},
                "summary": {}
            }
            
            # Extract clauses from each document
            for doc in documents:
                doc_id = doc["document_id"]
                doc_content = doc["content"]
                
                # Extract obligations for this document
                obligations = await self.extract_obligations(
                    document_content=doc_content,
                    document_id=doc_id,
                    focus_areas=focus_categories
                )
                
                # Structure data for comparison
                comparison_data["documents"][doc_id] = {
                    "metadata": doc.get("metadata", {}),
                    "clauses": self._structure_clauses_for_comparison(obligations["obligations"])
                }
            
            # Build comparison matrix
            comparison_data["comparison_matrix"] = self._build_comparison_matrix(comparison_data["documents"])
            
            # Identify differences
            comparison_data["differences"] = self._identify_clause_differences(comparison_data["documents"])
            
            # Generate summary
            comparison_data["summary"] = self._generate_comparison_summary(comparison_data)
            
            logger.info("Multi-document clause extraction completed",
                       documents_processed=len(documents))
            
            return comparison_data
            
        except Exception as e:
            logger.error("Multi-document clause extraction failed", error=str(e))
            raise

    def _structure_clauses_for_comparison(self, obligations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Structure clauses by category for easy comparison"""
        structured = {}
        
        for obligation in obligations:
            category = obligation["obligation_type"]
            if category not in structured:
                structured[category] = []
            
            # Add comparison-specific fields
            clause_data = {
                "id": f"{category}_{len(structured[category])}",
                "text": obligation["clause_text"],
                "context": obligation["context"],
                "risk_level": obligation["risk_level"],
                "negotiation_leverage": obligation["negotiation_leverage"],
                "market_standard": obligation["market_standard"],
                "confidence": obligation["confidence"],
                "position": {
                    "start_char": obligation["start_char"],
                    "end_char": obligation["end_char"]
                },
                "extracted_fields": self._extract_comparison_fields(obligation)
            }
            
            structured[category].append(clause_data)
        
        return structured

    def _extract_comparison_fields(self, obligation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific fields for comparison based on clause category"""
        category = obligation["obligation_type"]
        clause_text = obligation["clause_text"].lower()
        
        # Get comparison fields for this category
        comparison_fields = self.clause_config["categories"].get(category, {}).get("comparison_fields", [])
        
        extracted_fields = {}
        
        # Extract specific information based on category
        if category == "MAINTENANCE":
            extracted_fields = {
                "scope": self._extract_maintenance_scope(clause_text),
                "responsibility": self._extract_responsibility(clause_text),
                "cost_sharing": self._extract_cost_sharing(clause_text),
                "standards": self._extract_standards(clause_text)
            }
        elif category == "RENEWAL":
            extracted_fields = {
                "notice_period": self._extract_notice_period(clause_text),
                "renewal_terms": self._extract_renewal_terms(clause_text),
                "rent_adjustment": self._extract_rent_adjustment(clause_text),
                "conditions": self._extract_conditions(clause_text)
            }
        # Add more category-specific extractions as needed
        
        return extracted_fields

    def _extract_maintenance_scope(self, text: str) -> str:
        """Extract maintenance scope from clause text"""
        if "all" in text or "entire" in text:
            return "comprehensive"
        elif "reasonable" in text or "normal" in text:
            return "standard"
        elif "specific" in text or "limited" in text:
            return "limited"
        return "unclear"

    def _extract_responsibility(self, text: str) -> str:
        """Extract responsibility from clause text"""
        if "tenant" in text and "landlord" not in text:
            return "tenant_only"
        elif "landlord" in text and "tenant" not in text:
            return "landlord_only"
        elif "both" in text or "shared" in text:
            return "shared"
        return "unclear"

    def _extract_cost_sharing(self, text: str) -> str:
        """Extract cost sharing information"""
        if "tenant" in text and "cost" in text:
            return "tenant_pays"
        elif "landlord" in text and "cost" in text:
            return "landlord_pays"
        elif "shared" in text or "split" in text:
            return "shared"
        return "unclear"

    def _extract_standards(self, text: str) -> str:
        """Extract maintenance standards"""
        if "good condition" in text or "reasonable" in text:
            return "reasonable"
        elif "perfect" in text or "excellent" in text:
            return "high"
        elif "minimum" in text or "basic" in text:
            return "minimum"
        return "unclear"

    def _extract_notice_period(self, text: str) -> str:
        """Extract notice period from renewal clauses"""
        import re
        notice_match = re.search(r'(\d+)\s*(days?|months?|years?)', text)
        if notice_match:
            return f"{notice_match.group(1)} {notice_match.group(2)}"
        return "unclear"

    def _extract_renewal_terms(self, text: str) -> str:
        """Extract renewal terms"""
        if "automatic" in text:
            return "automatic"
        elif "option" in text:
            return "optional"
        elif "mandatory" in text:
            return "mandatory"
        return "unclear"

    def _extract_rent_adjustment(self, text: str) -> str:
        """Extract rent adjustment mechanism"""
        if "cpi" in text or "consumer price" in text:
            return "cpi_based"
        elif "market" in text:
            return "market_based"
        elif "fixed" in text:
            return "fixed"
        return "unclear"

    def _extract_conditions(self, text: str) -> str:
        """Extract renewal conditions"""
        conditions = []
        if "breach" in text:
            conditions.append("no_breach")
        if "payment" in text:
            conditions.append("payment_current")
        if "notice" in text:
            conditions.append("proper_notice")
        return ", ".join(conditions) if conditions else "unclear"

    def _build_comparison_matrix(self, documents: Dict[str, Any]) -> Dict[str, Any]:
        """Build a comparison matrix for visual comparison"""
        matrix = {}
        
        # Get all categories across all documents
        all_categories = set()
        for doc_data in documents.values():
            all_categories.update(doc_data["clauses"].keys())
        
        # Build matrix for each category
        for category in all_categories:
            matrix[category] = {
                "documents": {},
                "common_clauses": [],
                "unique_clauses": {},
                "differences": []
            }
            
            # Collect clauses from all documents for this category
            category_clauses = {}
            for doc_id, doc_data in documents.items():
                if category in doc_data["clauses"]:
                    category_clauses[doc_id] = doc_data["clauses"][category]
                    matrix[category]["documents"][doc_id] = len(doc_data["clauses"][category])
            
            # Find common and unique clauses
            if len(category_clauses) > 1:
                matrix[category]["common_clauses"] = self._find_common_clauses(category_clauses)
                matrix[category]["unique_clauses"] = self._find_unique_clauses(category_clauses)
                matrix[category]["differences"] = self._find_clause_differences(category_clauses)
        
        return matrix

    def _find_common_clauses(self, category_clauses: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Find clauses that appear in multiple documents"""
        # This is a simplified version - in practice, you'd use more sophisticated matching
        common = []
        all_clauses = []
        
        for doc_id, clauses in category_clauses.items():
            for clause in clauses:
                clause["source_document"] = doc_id
                all_clauses.append(clause)
        
        # Group by similar text (simplified)
        text_groups = {}
        for clause in all_clauses:
            text_key = clause["text"][:50]  # Use first 50 chars as key
            if text_key not in text_groups:
                text_groups[text_key] = []
            text_groups[text_key].append(clause)
        
        # Find groups with multiple documents
        for text_key, clauses in text_groups.items():
            if len(set(clause["source_document"] for clause in clauses)) > 1:
                common.append({
                    "text": clauses[0]["text"],
                    "documents": [clause["source_document"] for clause in clauses],
                    "variations": clauses
                })
        
        return common

    def _find_unique_clauses(self, category_clauses: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find clauses unique to each document"""
        unique = {}
        
        for doc_id, clauses in category_clauses.items():
            unique[doc_id] = []
            for clause in clauses:
                # Check if this clause appears in other documents
                is_unique = True
                for other_doc_id, other_clauses in category_clauses.items():
                    if other_doc_id != doc_id:
                        for other_clause in other_clauses:
                            if self._clauses_are_similar(clause, other_clause):
                                is_unique = False
                                break
                        if not is_unique:
                            break
                
                if is_unique:
                    unique[doc_id].append(clause)
        
        return unique

    def _clauses_are_similar(self, clause1: Dict[str, Any], clause2: Dict[str, Any]) -> bool:
        """Check if two clauses are similar enough to be considered the same"""
        # Simple similarity check - in practice, you'd use more sophisticated NLP
        text1 = clause1["text"].lower()
        text2 = clause2["text"].lower()
        
        # Check for common keywords
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # If more than 70% of words are common, consider them similar
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity > 0.7

    def _find_clause_differences(self, category_clauses: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Find differences between clauses across documents"""
        differences = []
        
        # Compare extracted fields across documents
        for doc_id, clauses in category_clauses.items():
            for clause in clauses:
                for other_doc_id, other_clauses in category_clauses.items():
                    if other_doc_id != doc_id:
                        for other_clause in other_clauses:
                            if self._clauses_are_similar(clause, other_clause):
                                # Compare extracted fields
                                field_diffs = self._compare_extracted_fields(
                                    clause["extracted_fields"],
                                    other_clause["extracted_fields"]
                                )
                                
                                if field_diffs:
                                    differences.append({
                                        "clause_text": clause["text"],
                                        "documents": [doc_id, other_doc_id],
                                        "differences": field_diffs
                                    })
        
        return differences

    def _compare_extracted_fields(self, fields1: Dict[str, Any], fields2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare extracted fields between two clauses"""
        differences = []
        
        all_keys = set(fields1.keys()) | set(fields2.keys())
        
        for key in all_keys:
            value1 = fields1.get(key, "not_specified")
            value2 = fields2.get(key, "not_specified")
            
            if value1 != value2:
                differences.append({
                    "field": key,
                    "document1_value": value1,
                    "document2_value": value2
                })
        
        return differences

    def _identify_clause_differences(self, documents: Dict[str, Any]) -> Dict[str, Any]:
        """Identify high-level differences between documents"""
        differences = {
            "missing_categories": {},
            "risk_differences": {},
            "leverage_differences": {},
            "market_standard_differences": {}
        }
        
        # Find missing categories
        all_categories = set()
        for doc_data in documents.values():
            all_categories.update(doc_data["clauses"].keys())
        
        for doc_id, doc_data in documents.items():
            doc_categories = set(doc_data["clauses"].keys())
            missing = all_categories - doc_categories
            if missing:
                differences["missing_categories"][doc_id] = list(missing)
        
        return differences

    def _generate_comparison_summary(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of comparison results"""
        summary = {
            "total_documents": len(comparison_data["documents"]),
            "total_categories": len(comparison_data["comparison_matrix"]),
            "common_clauses_count": 0,
            "unique_clauses_count": 0,
            "differences_count": 0,
            "risk_distribution": {},
            "leverage_distribution": {}
        }
        
        # Count common and unique clauses
        for category_data in comparison_data["comparison_matrix"].values():
            summary["common_clauses_count"] += len(category_data["common_clauses"])
            summary["unique_clauses_count"] += sum(len(clauses) for clauses in category_data["unique_clauses"].values())
            summary["differences_count"] += len(category_data["differences"])
        
        return summary
