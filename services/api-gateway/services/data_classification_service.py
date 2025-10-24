"""
Data Classification Management Service
Comprehensive data classification and handling policies
"""

import re
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.data_classification import (
    DataClassificationLevel, DataCategory, DataSensitivity, ClassificationMethod,
    DataHandlingAction, ComplianceRequirement, DataClassificationRule,
    DataClassificationPolicy, DataClassificationResult, DataClassificationRequest,
    BulkClassificationRequest, ClassificationRuleRequest, ClassificationPolicyRequest,
    ClassificationQuery, ClassificationStats, ClassificationAuditLog, ClassificationReport
)
# Database will be accessed through the main app's db_manager

logger = structlog.get_logger(__name__)

class DataClassificationService:
    """Data classification management service"""
    
    def __init__(self):
        self.logger = logger
        self.classification_rules: Dict[str, DataClassificationRule] = {}
        self.classification_policies: Dict[str, DataClassificationPolicy] = {}
        self.ai_classification_enabled = True
        self.rule_engine_enabled = True
        
        # Initialize default rules and policies
        self._initialize_default_rules()
        self._initialize_default_policies()
    
    async def classify_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        classification_method: Optional[ClassificationMethod] = None,
        force_reclassification: bool = False,
        user_id: str = "system"
    ) -> DataClassificationResult:
        """Classify a document using available methods"""
        
        metadata = metadata or {}
        
        # Check if document is already classified (unless force reclassification)
        if not force_reclassification:
            existing_classification = await self._get_existing_classification(document_id)
            if existing_classification:
                return existing_classification
        
        # Determine classification method
        if not classification_method:
            classification_method = self._determine_classification_method(content, metadata)
        
        # Perform classification based on method
        if classification_method == ClassificationMethod.AI_POWERED:
            result = await self._classify_with_ai(document_id, content, metadata, user_id)
        elif classification_method == ClassificationMethod.RULE_BASED:
            result = await self._classify_with_rules(document_id, content, metadata, user_id)
        elif classification_method == ClassificationMethod.POLICY_BASED:
            result = await self._classify_with_policies(document_id, content, metadata, user_id)
        else:
            result = await self._classify_automatic(document_id, content, metadata, user_id)
        
        # Store classification result
        await self._store_classification_result(result)
        
        # Log classification audit
        await self._log_classification_audit(
            document_id, "classify", None, result.classification_level,
            None, result.data_category, None, result.sensitivity,
            f"Document classified using {classification_method.value} method",
            user_id
        )
        
        return result
    
    async def classify_documents_bulk(
        self,
        document_ids: List[str],
        classification_method: Optional[ClassificationMethod] = None,
        force_reclassification: bool = False,
        user_id: str = "system"
    ) -> List[DataClassificationResult]:
        """Classify multiple documents in bulk"""
        
        results = []
        
        # Process documents in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(document_ids), batch_size):
            batch = document_ids[i:i + batch_size]
            
            # Process batch concurrently
            tasks = []
            for doc_id in batch:
                task = self._classify_single_document(
                    doc_id, classification_method, force_reclassification, user_id
                )
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error("Classification error", error=str(result))
                    continue
                results.append(result)
        
        return results
    
    async def create_classification_rule(
        self,
        rule_data: ClassificationRuleRequest,
        user_id: str
    ) -> DataClassificationRule:
        """Create a new classification rule"""
        
        rule = DataClassificationRule(
            name=rule_data.name,
            description=rule_data.description,
            pattern=rule_data.pattern,
            pattern_type=rule_data.pattern_type,
            classification_level=rule_data.classification_level,
            data_category=rule_data.data_category,
            sensitivity=rule_data.sensitivity,
            confidence_threshold=rule_data.confidence_threshold,
            handling_actions=rule_data.handling_actions,
            compliance_requirements=rule_data.compliance_requirements,
            is_active=rule_data.is_active,
            priority=rule_data.priority,
            created_by=user_id
        )
        
        # Store rule in database
        await self._store_classification_rule(rule)
        
        # Add to in-memory cache
        self.classification_rules[str(rule.id)] = rule
        
        self.logger.info("Classification rule created", rule_id=str(rule.id), name=rule.name)
        return rule
    
    async def create_classification_policy(
        self,
        policy_data: ClassificationPolicyRequest,
        user_id: str
    ) -> DataClassificationPolicy:
        """Create a new classification policy"""
        
        policy = DataClassificationPolicy(
            name=policy_data.name,
            description=policy_data.description,
            classification_level=policy_data.classification_level,
            data_category=policy_data.data_category,
            sensitivity=policy_data.sensitivity,
            handling_actions=policy_data.handling_actions,
            compliance_requirements=policy_data.compliance_requirements,
            retention_period_days=policy_data.retention_period_days,
            access_controls=policy_data.access_controls,
            sharing_restrictions=policy_data.sharing_restrictions,
            encryption_required=policy_data.encryption_required,
            audit_required=policy_data.audit_required,
            backup_required=policy_data.backup_required,
            is_active=policy_data.is_active,
            created_by=user_id
        )
        
        # Store policy in database
        await self._store_classification_policy(policy)
        
        # Add to in-memory cache
        self.classification_policies[str(policy.id)] = policy
        
        self.logger.info("Classification policy created", policy_id=str(policy.id), name=policy.name)
        return policy
    
    async def get_classification_results(
        self,
        query: ClassificationQuery
    ) -> Tuple[List[DataClassificationResult], int]:
        """Get classification results with filtering"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build SQL query
            sql_query = self._build_classification_query_sql(query)
            params = self._build_classification_query_params(query)
            
            # Execute query
            result = await db.execute(text(sql_query), params)
            rows = result.fetchall()
            
            # Get total count
            count_sql = self._build_classification_count_sql(query)
            count_result = await db.execute(text(count_sql), params)
            total_count = count_result.scalar()
            
            # Convert rows to DataClassificationResult objects
            results = []
            for row in rows:
                result = DataClassificationResult(
                    document_id=row.document_id,
                    classification_level=DataClassificationLevel(row.classification_level),
                    data_category=DataCategory(row.data_category),
                    sensitivity=DataSensitivity(row.sensitivity),
                    confidence_score=row.confidence_score,
                    classification_method=ClassificationMethod(row.classification_method),
                    applied_rules=json.loads(row.applied_rules) if row.applied_rules else [],
                    handling_actions=[DataHandlingAction(action) for action in json.loads(row.handling_actions)],
                    compliance_requirements=[ComplianceRequirement(req) for req in json.loads(row.compliance_requirements)],
                    classification_reasoning=row.classification_reasoning,
                    classified_by=row.classified_by,
                    classified_at=row.classified_at,
                    requires_review=row.requires_review,
                    review_notes=row.review_notes
                )
                results.append(result)
            
            return results, total_count
    
    async def get_classification_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ClassificationStats:
        """Get classification statistics"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build base WHERE clause
            where_conditions = []
            params = {}
            
            if start_date:
                where_conditions.append("classified_at >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                where_conditions.append("classified_at <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Get statistics
            stats_queries = {
                "total_documents": f"SELECT COUNT(DISTINCT document_id) FROM data_classifications WHERE {where_clause}",
                "classified_documents": f"SELECT COUNT(*) FROM data_classifications WHERE {where_clause}",
                "unclassified_documents": f"SELECT COUNT(*) FROM documents WHERE id NOT IN (SELECT DISTINCT document_id FROM data_classifications)",
                "classification_by_level": f"SELECT classification_level, COUNT(*) FROM data_classifications WHERE {where_clause} GROUP BY classification_level",
                "classification_by_category": f"SELECT data_category, COUNT(*) FROM data_classifications WHERE {where_clause} GROUP BY data_category",
                "classification_by_sensitivity": f"SELECT sensitivity, COUNT(*) FROM data_classifications WHERE {where_clause} GROUP BY sensitivity",
                "classification_by_method": f"SELECT classification_method, COUNT(*) FROM data_classifications WHERE {where_clause} GROUP BY classification_method",
                "compliance_coverage": f"SELECT compliance_requirements, COUNT(*) FROM data_classifications WHERE {where_clause} GROUP BY compliance_requirements",
                "requires_review_count": f"SELECT COUNT(*) FROM data_classifications WHERE {where_clause} AND requires_review = true",
                "average_confidence": f"SELECT AVG(confidence_score) FROM data_classifications WHERE {where_clause}",
                "classification_accuracy": f"SELECT AVG(CASE WHEN requires_review = false THEN 1.0 ELSE 0.0 END) FROM data_classifications WHERE {where_clause}"
            }
            
            results = {}
            for stat_name, query in stats_queries.items():
                if stat_name in ["classification_by_level", "classification_by_category", "classification_by_sensitivity", "classification_by_method", "compliance_coverage"]:
                    result = await db.execute(text(query), params)
                    rows = result.fetchall()
                    results[stat_name] = {row[0]: row[1] for row in rows}
                else:
                    result = await db.execute(text(query), params)
                    results[stat_name] = result.scalar() or 0
            
            return ClassificationStats(
                total_documents=results["total_documents"],
                classified_documents=results["classified_documents"],
                unclassified_documents=results["unclassified_documents"],
                classification_by_level=results["classification_by_level"],
                classification_by_category=results["classification_by_category"],
                classification_by_sensitivity=results["classification_by_sensitivity"],
                classification_by_method=results["classification_by_method"],
                compliance_coverage=results["compliance_coverage"],
                requires_review_count=results["requires_review_count"],
                average_confidence=results["average_confidence"],
                classification_accuracy=results["classification_accuracy"]
            )
    
    async def update_classification(
        self,
        document_id: str,
        new_classification: DataClassificationLevel,
        new_category: DataCategory,
        new_sensitivity: DataSensitivity,
        reason: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DataClassificationResult:
        """Update document classification"""
        
        # Get current classification
        current = await self._get_existing_classification(document_id)
        if not current:
            raise ValueError("Document not found or not classified")
        
        # Create updated classification result
        updated_result = DataClassificationResult(
            document_id=document_id,
            classification_level=new_classification,
            data_category=new_category,
            sensitivity=new_sensitivity,
            confidence_score=current.confidence_score,
            classification_method=ClassificationMethod.MANUAL,
            applied_rules=current.applied_rules,
            handling_actions=self._get_handling_actions_for_classification(new_classification, new_category, new_sensitivity),
            compliance_requirements=self._get_compliance_requirements_for_classification(new_classification, new_category),
            classification_reasoning=f"Manually updated: {reason}",
            classified_by=user_id,
            requires_review=False
        )
        
        # Store updated classification
        await self._store_classification_result(updated_result)
        
        # Log classification audit
        await self._log_classification_audit(
            document_id, "update", current.classification_level, new_classification,
            current.data_category, new_category, current.sensitivity, new_sensitivity,
            reason, user_id, ip_address, user_agent
        )
        
        return updated_result
    
    async def get_classification_audit_logs(
        self,
        document_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ClassificationAuditLog]:
        """Get classification audit logs"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            where_conditions = []
            params = {"limit": limit, "offset": offset}
            
            if document_id:
                where_conditions.append("document_id = :document_id")
                params["document_id"] = document_id
            
            if start_date:
                where_conditions.append("changed_at >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                where_conditions.append("changed_at <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql_query = f"""
                SELECT * FROM classification_audit_logs 
                WHERE {where_clause}
                ORDER BY changed_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = await db.execute(text(sql_query), params)
            rows = result.fetchall()
            
            audit_logs = []
            for row in rows:
                audit_log = ClassificationAuditLog(
                    id=row.id,
                    document_id=row.document_id,
                    action=row.action,
                    old_classification=DataClassificationLevel(row.old_classification) if row.old_classification else None,
                    new_classification=DataClassificationLevel(row.new_classification) if row.new_classification else None,
                    old_category=DataCategory(row.old_category) if row.old_category else None,
                    new_category=DataCategory(row.new_category) if row.new_category else None,
                    old_sensitivity=DataSensitivity(row.old_sensitivity) if row.old_sensitivity else None,
                    new_sensitivity=DataSensitivity(row.new_sensitivity) if row.new_sensitivity else None,
                    reason=row.reason,
                    changed_by=row.changed_by,
                    changed_at=row.changed_at,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    additional_data=json.loads(row.additional_data) if row.additional_data else {}
                )
                audit_logs.append(audit_log)
            
            return audit_logs
    
    def _initialize_default_rules(self):
        """Initialize default classification rules"""
        
        default_rules = [
            {
                "name": "Personal Data Detection",
                "description": "Detect personal data patterns",
                "pattern": r"\b(?:ssn|social security|credit card|phone|email|address|name|birth|age)\b",
                "pattern_type": "regex",
                "classification_level": DataClassificationLevel.CONFIDENTIAL,
                "data_category": DataCategory.PERSONAL_DATA,
                "sensitivity": DataSensitivity.HIGH,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG],
                "compliance_requirements": [ComplianceRequirement.GDPR, ComplianceRequirement.CCPA]
            },
            {
                "name": "Financial Data Detection",
                "description": "Detect financial data patterns",
                "pattern": r"\b(?:account|balance|transaction|payment|invoice|receipt|tax|financial)\b",
                "pattern_type": "regex",
                "classification_level": DataClassificationLevel.CONFIDENTIAL,
                "data_category": DataCategory.FINANCIAL_DATA,
                "sensitivity": DataSensitivity.HIGH,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG],
                "compliance_requirements": [ComplianceRequirement.SOX, ComplianceRequirement.PCI_DSS]
            },
            {
                "name": "Health Data Detection",
                "description": "Detect health data patterns",
                "pattern": r"\b(?:medical|health|patient|diagnosis|treatment|medication|hospital|clinic)\b",
                "pattern_type": "regex",
                "classification_level": DataClassificationLevel.RESTRICTED,
                "data_category": DataCategory.HEALTH_DATA,
                "sensitivity": DataSensitivity.CRITICAL,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG, DataHandlingAction.ANONYMIZE],
                "compliance_requirements": [ComplianceRequirement.HIPAA]
            },
            {
                "name": "Intellectual Property Detection",
                "description": "Detect intellectual property patterns",
                "pattern": r"\b(?:patent|copyright|trademark|proprietary|confidential|trade secret|invention)\b",
                "pattern_type": "regex",
                "classification_level": DataClassificationLevel.RESTRICTED,
                "data_category": DataCategory.INTELLECTUAL_PROPERTY,
                "sensitivity": DataSensitivity.CRITICAL,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG, DataHandlingAction.SHARING_RESTRICTED],
                "compliance_requirements": []
            }
        ]
        
        for rule_data in default_rules:
            rule = DataClassificationRule(
                name=rule_data["name"],
                description=rule_data["description"],
                pattern=rule_data["pattern"],
                pattern_type=rule_data["pattern_type"],
                classification_level=rule_data["classification_level"],
                data_category=rule_data["data_category"],
                sensitivity=rule_data["sensitivity"],
                handling_actions=rule_data["handling_actions"],
                compliance_requirements=rule_data["compliance_requirements"],
                created_by="system"
            )
            self.classification_rules[str(rule.id)] = rule
    
    def _initialize_default_policies(self):
        """Initialize default classification policies"""
        
        default_policies = [
            {
                "name": "Public Data Policy",
                "description": "Policy for public data",
                "classification_level": DataClassificationLevel.PUBLIC,
                "data_category": DataCategory.OPERATIONAL_DATA,
                "sensitivity": DataSensitivity.LOW,
                "handling_actions": [DataHandlingAction.AUDIT_LOG],
                "encryption_required": False,
                "audit_required": True,
                "backup_required": False
            },
            {
                "name": "Internal Data Policy",
                "description": "Policy for internal data",
                "classification_level": DataClassificationLevel.INTERNAL,
                "data_category": DataCategory.OPERATIONAL_DATA,
                "sensitivity": DataSensitivity.MEDIUM,
                "handling_actions": [DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG],
                "encryption_required": False,
                "audit_required": True,
                "backup_required": True
            },
            {
                "name": "Confidential Data Policy",
                "description": "Policy for confidential data",
                "classification_level": DataClassificationLevel.CONFIDENTIAL,
                "data_category": DataCategory.PERSONAL_DATA,
                "sensitivity": DataSensitivity.HIGH,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG, DataHandlingAction.BACKUP_REQUIRED],
                "compliance_requirements": [ComplianceRequirement.GDPR],
                "encryption_required": True,
                "audit_required": True,
                "backup_required": True
            },
            {
                "name": "Restricted Data Policy",
                "description": "Policy for restricted data",
                "classification_level": DataClassificationLevel.RESTRICTED,
                "data_category": DataCategory.HEALTH_DATA,
                "sensitivity": DataSensitivity.CRITICAL,
                "handling_actions": [DataHandlingAction.ENCRYPT, DataHandlingAction.ACCESS_CONTROL, DataHandlingAction.AUDIT_LOG, DataHandlingAction.BACKUP_REQUIRED, DataHandlingAction.SHARING_RESTRICTED],
                "compliance_requirements": [ComplianceRequirement.HIPAA],
                "encryption_required": True,
                "audit_required": True,
                "backup_required": True
            }
        ]
        
        for policy_data in default_policies:
            policy = DataClassificationPolicy(
                name=policy_data["name"],
                description=policy_data["description"],
                classification_level=policy_data["classification_level"],
                data_category=policy_data["data_category"],
                sensitivity=policy_data["sensitivity"],
                handling_actions=policy_data["handling_actions"],
                compliance_requirements=policy_data.get("compliance_requirements", []),
                encryption_required=policy_data["encryption_required"],
                audit_required=policy_data["audit_required"],
                backup_required=policy_data["backup_required"],
                created_by="system"
            )
            self.classification_policies[str(policy.id)] = policy
    
    def _determine_classification_method(self, content: str, metadata: Dict[str, Any]) -> ClassificationMethod:
        """Determine the best classification method for content"""
        
        # Check if AI classification is available and content is suitable
        if self.ai_classification_enabled and len(content) > 100:
            return ClassificationMethod.AI_POWERED
        
        # Check if rule-based classification is available
        if self.rule_engine_enabled:
            return ClassificationMethod.RULE_BASED
        
        # Fall back to policy-based classification
        return ClassificationMethod.POLICY_BASED
    
    async def _classify_with_ai(self, document_id: str, content: str, metadata: Dict[str, Any], user_id: str) -> DataClassificationResult:
        """Classify document using AI"""
        
        # Mock AI classification - in production, this would call an AI service
        # For now, we'll use a simple heuristic based on content analysis
        
        classification_level = DataClassificationLevel.INTERNAL
        data_category = DataCategory.OPERATIONAL_DATA
        sensitivity = DataSensitivity.MEDIUM
        confidence_score = 0.7
        applied_rules = []
        
        # Analyze content for sensitive information
        sensitive_patterns = {
            DataClassificationLevel.CONFIDENTIAL: [
                r"\b(?:ssn|social security|credit card|phone|email)\b",
                r"\b(?:account|balance|transaction|payment)\b"
            ],
            DataClassificationLevel.RESTRICTED: [
                r"\b(?:medical|health|patient|diagnosis)\b",
                r"\b(?:patent|copyright|trademark|proprietary)\b"
            ]
        }
        
        for level, patterns in sensitive_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    classification_level = level
                    confidence_score = 0.9
                    applied_rules.append(f"AI Pattern: {pattern}")
                    break
        
        # Determine data category based on content
        if any(keyword in content.lower() for keyword in ["medical", "health", "patient", "diagnosis"]):
            data_category = DataCategory.HEALTH_DATA
            sensitivity = DataSensitivity.CRITICAL
        elif any(keyword in content.lower() for keyword in ["financial", "account", "payment", "transaction"]):
            data_category = DataCategory.FINANCIAL_DATA
            sensitivity = DataSensitivity.HIGH
        elif any(keyword in content.lower() for keyword in ["personal", "name", "address", "phone"]):
            data_category = DataCategory.PERSONAL_DATA
            sensitivity = DataSensitivity.HIGH
        
        return DataClassificationResult(
            document_id=document_id,
            classification_level=classification_level,
            data_category=data_category,
            sensitivity=sensitivity,
            confidence_score=confidence_score,
            classification_method=ClassificationMethod.AI_POWERED,
            applied_rules=applied_rules,
            handling_actions=self._get_handling_actions_for_classification(classification_level, data_category, sensitivity),
            compliance_requirements=self._get_compliance_requirements_for_classification(classification_level, data_category),
            classification_reasoning=f"AI-powered classification based on content analysis",
            classified_by=user_id,
            requires_review=confidence_score < 0.8
        )
    
    async def _classify_with_rules(self, document_id: str, content: str, metadata: Dict[str, Any], user_id: str) -> DataClassificationResult:
        """Classify document using rules"""
        
        best_match = None
        best_confidence = 0.0
        applied_rules = []
        
        # Apply all active rules
        for rule in self.classification_rules.values():
            if not rule.is_active:
                continue
            
            confidence = self._evaluate_rule(rule, content, metadata)
            if confidence >= rule.confidence_threshold and confidence > best_confidence:
                best_match = rule
                best_confidence = confidence
                applied_rules.append(rule.name)
        
        if best_match:
            return DataClassificationResult(
                document_id=document_id,
                classification_level=best_match.classification_level,
                data_category=best_match.data_category,
                sensitivity=best_match.sensitivity,
                confidence_score=best_confidence,
                classification_method=ClassificationMethod.RULE_BASED,
                applied_rules=applied_rules,
                handling_actions=best_match.handling_actions,
                compliance_requirements=best_match.compliance_requirements,
                classification_reasoning=f"Rule-based classification using {len(applied_rules)} rules",
                classified_by=user_id,
                requires_review=best_confidence < 0.8
            )
        else:
            # Fall back to default classification
            return await self._classify_with_policies(document_id, content, metadata, user_id)
    
    async def _classify_with_policies(self, document_id: str, content: str, metadata: Dict[str, Any], user_id: str) -> DataClassificationResult:
        """Classify document using policies"""
        
        # Find matching policy based on content characteristics
        matching_policy = None
        
        for policy in self.classification_policies.values():
            if not policy.is_active:
                continue
            
            # Simple policy matching based on content length and keywords
            if self._policy_matches_content(policy, content, metadata):
                matching_policy = policy
                break
        
        if not matching_policy:
            # Use default internal policy
            matching_policy = self.classification_policies[list(self.classification_policies.keys())[1]]  # Internal policy
        
        return DataClassificationResult(
            document_id=document_id,
            classification_level=matching_policy.classification_level,
            data_category=matching_policy.data_category,
            sensitivity=matching_policy.sensitivity,
            confidence_score=0.6,  # Lower confidence for policy-based classification
            classification_method=ClassificationMethod.POLICY_BASED,
            applied_rules=[],
            handling_actions=matching_policy.handling_actions,
            compliance_requirements=matching_policy.compliance_requirements,
            classification_reasoning=f"Policy-based classification using {matching_policy.name}",
            classified_by=user_id,
            requires_review=True  # Policy-based classifications should be reviewed
        )
    
    async def _classify_automatic(self, document_id: str, content: str, metadata: Dict[str, Any], user_id: str) -> DataClassificationResult:
        """Automatic classification using best available method"""
        
        # Try AI first, then rules, then policies
        if self.ai_classification_enabled:
            return await self._classify_with_ai(document_id, content, metadata, user_id)
        elif self.rule_engine_enabled:
            return await self._classify_with_rules(document_id, content, metadata, user_id)
        else:
            return await self._classify_with_policies(document_id, content, metadata, user_id)
    
    def _evaluate_rule(self, rule: DataClassificationRule, content: str, metadata: Dict[str, Any]) -> float:
        """Evaluate a classification rule against content"""
        
        if rule.pattern_type == "regex":
            matches = re.findall(rule.pattern, content, re.IGNORECASE)
            if matches:
                # Confidence based on number of matches and content length
                match_ratio = len(matches) / max(len(content.split()), 1)
                return min(match_ratio * 2, 1.0)
        elif rule.pattern_type == "keyword":
            keywords = rule.pattern.lower().split(",")
            matches = sum(1 for keyword in keywords if keyword.strip() in content.lower())
            if matches > 0:
                return min(matches / len(keywords), 1.0)
        
        return 0.0
    
    def _policy_matches_content(self, policy: DataClassificationPolicy, content: str, metadata: Dict[str, Any]) -> bool:
        """Check if a policy matches content characteristics"""
        
        # Simple matching based on content length and basic characteristics
        content_length = len(content)
        
        if policy.classification_level == DataClassificationLevel.PUBLIC:
            return content_length < 1000  # Short content likely public
        elif policy.classification_level == DataClassificationLevel.INTERNAL:
            return 1000 <= content_length < 5000  # Medium content likely internal
        elif policy.classification_level == DataClassificationLevel.CONFIDENTIAL:
            return content_length >= 5000  # Long content likely confidential
        
        return False
    
    def _get_handling_actions_for_classification(
        self,
        classification_level: DataClassificationLevel,
        data_category: DataCategory,
        sensitivity: DataSensitivity
    ) -> List[DataHandlingAction]:
        """Get handling actions for a classification"""
        
        actions = [DataHandlingAction.AUDIT_LOG]  # Always audit
        
        if classification_level in [DataClassificationLevel.CONFIDENTIAL, DataClassificationLevel.RESTRICTED]:
            actions.append(DataHandlingAction.ENCRYPT)
            actions.append(DataHandlingAction.ACCESS_CONTROL)
            actions.append(DataHandlingAction.BACKUP_REQUIRED)
        
        if sensitivity in [DataSensitivity.HIGH, DataSensitivity.CRITICAL]:
            actions.append(DataHandlingAction.SHARING_RESTRICTED)
        
        if data_category == DataCategory.PERSONAL_DATA:
            actions.append(DataHandlingAction.ANONYMIZE)
        
        if data_category == DataCategory.HEALTH_DATA:
            actions.append(DataHandlingAction.PSEUDONYMIZE)
        
        return actions
    
    def _get_compliance_requirements_for_classification(
        self,
        classification_level: DataClassificationLevel,
        data_category: DataCategory
    ) -> List[ComplianceRequirement]:
        """Get compliance requirements for a classification"""
        
        requirements = []
        
        if data_category == DataCategory.PERSONAL_DATA:
            requirements.extend([ComplianceRequirement.GDPR, ComplianceRequirement.CCPA])
        
        if data_category == DataCategory.HEALTH_DATA:
            requirements.append(ComplianceRequirement.HIPAA)
        
        if data_category == DataCategory.FINANCIAL_DATA:
            requirements.extend([ComplianceRequirement.SOX, ComplianceRequirement.PCI_DSS])
        
        return requirements
    
    async def _classify_single_document(
        self,
        document_id: str,
        classification_method: Optional[ClassificationMethod],
        force_reclassification: bool,
        user_id: str
    ) -> DataClassificationResult:
        """Classify a single document (helper for bulk operations)"""
        
        # In a real implementation, you would fetch the document content here
        # For now, we'll use mock content
        content = f"Mock content for document {document_id}"
        metadata = {"document_id": document_id}
        
        return await self.classify_document(
            document_id, content, metadata, classification_method, force_reclassification, user_id
        )
    
    async def _get_existing_classification(self, document_id: str) -> Optional[DataClassificationResult]:
        """Get existing classification for a document"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            result = await db.execute(
                text("SELECT * FROM data_classifications WHERE document_id = :document_id ORDER BY classified_at DESC LIMIT 1"),
                {"document_id": document_id}
            )
            row = result.fetchone()
            
            if row:
                return DataClassificationResult(
                    document_id=row.document_id,
                    classification_level=DataClassificationLevel(row.classification_level),
                    data_category=DataCategory(row.data_category),
                    sensitivity=DataSensitivity(row.sensitivity),
                    confidence_score=row.confidence_score,
                    classification_method=ClassificationMethod(row.classification_method),
                    applied_rules=json.loads(row.applied_rules) if row.applied_rules else [],
                    handling_actions=[DataHandlingAction(action) for action in json.loads(row.handling_actions)],
                    compliance_requirements=[ComplianceRequirement(req) for req in json.loads(row.compliance_requirements)],
                    classification_reasoning=row.classification_reasoning,
                    classified_by=row.classified_by,
                    classified_at=row.classified_at,
                    requires_review=row.requires_review,
                    review_notes=row.review_notes
                )
        
        return None
    
    async def _store_classification_result(self, result: DataClassificationResult):
        """Store classification result in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO data_classifications 
                (document_id, classification_level, data_category, sensitivity, confidence_score,
                 classification_method, applied_rules, handling_actions, compliance_requirements,
                 classification_reasoning, classified_by, classified_at, requires_review, review_notes)
                VALUES (:document_id, :classification_level, :data_category, :sensitivity, :confidence_score,
                        :classification_method, :applied_rules, :handling_actions, :compliance_requirements,
                        :classification_reasoning, :classified_by, :classified_at, :requires_review, :review_notes)
                ON CONFLICT (document_id) DO UPDATE SET
                    classification_level = EXCLUDED.classification_level,
                    data_category = EXCLUDED.data_category,
                    sensitivity = EXCLUDED.sensitivity,
                    confidence_score = EXCLUDED.confidence_score,
                    classification_method = EXCLUDED.classification_method,
                    applied_rules = EXCLUDED.applied_rules,
                    handling_actions = EXCLUDED.handling_actions,
                    compliance_requirements = EXCLUDED.compliance_requirements,
                    classification_reasoning = EXCLUDED.classification_reasoning,
                    classified_by = EXCLUDED.classified_by,
                    classified_at = EXCLUDED.classified_at,
                    requires_review = EXCLUDED.requires_review,
                    review_notes = EXCLUDED.review_notes
            """), {
                "document_id": result.document_id,
                "classification_level": result.classification_level.value,
                "data_category": result.data_category.value,
                "sensitivity": result.sensitivity.value,
                "confidence_score": result.confidence_score,
                "classification_method": result.classification_method.value,
                "applied_rules": json.dumps(result.applied_rules),
                "handling_actions": json.dumps([action.value for action in result.handling_actions]),
                "compliance_requirements": json.dumps([req.value for req in result.compliance_requirements]),
                "classification_reasoning": result.classification_reasoning,
                "classified_by": result.classified_by,
                "classified_at": result.classified_at,
                "requires_review": result.requires_review,
                "review_notes": result.review_notes
            })
            await db.commit()
    
    async def _store_classification_rule(self, rule: DataClassificationRule):
        """Store classification rule in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO classification_rules 
                (id, name, description, pattern, pattern_type, classification_level, data_category,
                 sensitivity, confidence_threshold, handling_actions, compliance_requirements,
                 is_active, priority, created_by, created_at, updated_at)
                VALUES (:id, :name, :description, :pattern, :pattern_type, :classification_level, :data_category,
                        :sensitivity, :confidence_threshold, :handling_actions, :compliance_requirements,
                        :is_active, :priority, :created_by, :created_at, :updated_at)
            """), {
                "id": str(rule.id),
                "name": rule.name,
                "description": rule.description,
                "pattern": rule.pattern,
                "pattern_type": rule.pattern_type,
                "classification_level": rule.classification_level.value,
                "data_category": rule.data_category.value,
                "sensitivity": rule.sensitivity.value,
                "confidence_threshold": rule.confidence_threshold,
                "handling_actions": json.dumps([action.value for action in rule.handling_actions]),
                "compliance_requirements": json.dumps([req.value for req in rule.compliance_requirements]),
                "is_active": rule.is_active,
                "priority": rule.priority,
                "created_by": rule.created_by,
                "created_at": rule.created_at,
                "updated_at": rule.updated_at
            })
            await db.commit()
    
    async def _store_classification_policy(self, policy: DataClassificationPolicy):
        """Store classification policy in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO classification_policies 
                (id, name, description, classification_level, data_category, sensitivity,
                 handling_actions, compliance_requirements, retention_period_days, access_controls,
                 sharing_restrictions, encryption_required, audit_required, backup_required,
                 is_active, created_by, created_at, updated_at)
                VALUES (:id, :name, :description, :classification_level, :data_category, :sensitivity,
                        :handling_actions, :compliance_requirements, :retention_period_days, :access_controls,
                        :sharing_restrictions, :encryption_required, :audit_required, :backup_required,
                        :is_active, :created_by, :created_at, :updated_at)
            """), {
                "id": str(policy.id),
                "name": policy.name,
                "description": policy.description,
                "classification_level": policy.classification_level.value,
                "data_category": policy.data_category.value,
                "sensitivity": policy.sensitivity.value,
                "handling_actions": json.dumps([action.value for action in policy.handling_actions]),
                "compliance_requirements": json.dumps([req.value for req in policy.compliance_requirements]),
                "retention_period_days": policy.retention_period_days,
                "access_controls": json.dumps(policy.access_controls),
                "sharing_restrictions": json.dumps(policy.sharing_restrictions),
                "encryption_required": policy.encryption_required,
                "audit_required": policy.audit_required,
                "backup_required": policy.backup_required,
                "is_active": policy.is_active,
                "created_by": policy.created_by,
                "created_at": policy.created_at,
                "updated_at": policy.updated_at
            })
            await db.commit()
    
    async def _log_classification_audit(
        self,
        document_id: str,
        action: str,
        old_classification: Optional[DataClassificationLevel],
        new_classification: Optional[DataClassificationLevel],
        old_category: Optional[DataCategory],
        new_category: Optional[DataCategory],
        old_sensitivity: Optional[DataSensitivity],
        new_sensitivity: Optional[DataSensitivity],
        reason: str,
        changed_by: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log classification audit event"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO classification_audit_logs 
                (document_id, action, old_classification, new_classification, old_category, new_category,
                 old_sensitivity, new_sensitivity, reason, changed_by, changed_at, ip_address, user_agent)
                VALUES (:document_id, :action, :old_classification, :new_classification, :old_category, :new_category,
                        :old_sensitivity, :new_sensitivity, :reason, :changed_by, :changed_at, :ip_address, :user_agent)
            """), {
                "document_id": document_id,
                "action": action,
                "old_classification": old_classification.value if old_classification else None,
                "new_classification": new_classification.value if new_classification else None,
                "old_category": old_category.value if old_category else None,
                "new_category": new_category.value if new_category else None,
                "old_sensitivity": old_sensitivity.value if old_sensitivity else None,
                "new_sensitivity": new_sensitivity.value if new_sensitivity else None,
                "reason": reason,
                "changed_by": changed_by,
                "changed_at": datetime.now(timezone.utc),
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            await db.commit()
    
    def _build_classification_query_sql(self, query: ClassificationQuery) -> str:
        """Build SQL query for classification results"""
        
        where_conditions = []
        params = {}
        
        if query.classification_level:
            where_conditions.append("classification_level = :classification_level")
            params["classification_level"] = query.classification_level.value
        
        if query.data_category:
            where_conditions.append("data_category = :data_category")
            params["data_category"] = query.data_category.value
        
        if query.sensitivity:
            where_conditions.append("sensitivity = :sensitivity")
            params["sensitivity"] = query.sensitivity.value
        
        if query.compliance_requirement:
            where_conditions.append("compliance_requirements LIKE :compliance_requirement")
            params["compliance_requirement"] = f"%{query.compliance_requirement.value}%"
        
        if query.classification_method:
            where_conditions.append("classification_method = :classification_method")
            params["classification_method"] = query.classification_method.value
        
        if query.requires_review is not None:
            where_conditions.append("requires_review = :requires_review")
            params["requires_review"] = query.requires_review
        
        if query.start_date:
            where_conditions.append("classified_at >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("classified_at <= :end_date")
            params["end_date"] = query.end_date
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"""
            SELECT * FROM data_classifications 
            WHERE {where_clause}
            ORDER BY classified_at DESC
            LIMIT :limit OFFSET :offset
        """
    
    def _build_classification_count_sql(self, query: ClassificationQuery) -> str:
        """Build SQL query for classification count"""
        
        where_conditions = []
        params = {}
        
        if query.classification_level:
            where_conditions.append("classification_level = :classification_level")
            params["classification_level"] = query.classification_level.value
        
        if query.data_category:
            where_conditions.append("data_category = :data_category")
            params["data_category"] = query.data_category.value
        
        if query.sensitivity:
            where_conditions.append("sensitivity = :sensitivity")
            params["sensitivity"] = query.sensitivity.value
        
        if query.compliance_requirement:
            where_conditions.append("compliance_requirements LIKE :compliance_requirement")
            params["compliance_requirement"] = f"%{query.compliance_requirement.value}%"
        
        if query.classification_method:
            where_conditions.append("classification_method = :classification_method")
            params["classification_method"] = query.classification_method.value
        
        if query.requires_review is not None:
            where_conditions.append("requires_review = :requires_review")
            params["requires_review"] = query.requires_review
        
        if query.start_date:
            where_conditions.append("classified_at >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("classified_at <= :end_date")
            params["end_date"] = query.end_date
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"SELECT COUNT(*) FROM data_classifications WHERE {where_clause}"
    
    def _build_classification_query_params(self, query: ClassificationQuery) -> Dict[str, Any]:
        """Build query parameters for classification results"""
        
        params = {
            "limit": query.limit,
            "offset": query.offset
        }
        
        if query.classification_level:
            params["classification_level"] = query.classification_level.value
        
        if query.data_category:
            params["data_category"] = query.data_category.value
        
        if query.sensitivity:
            params["sensitivity"] = query.sensitivity.value
        
        if query.compliance_requirement:
            params["compliance_requirement"] = f"%{query.compliance_requirement.value}%"
        
        if query.classification_method:
            params["classification_method"] = query.classification_method.value
        
        if query.requires_review is not None:
            params["requires_review"] = query.requires_review
        
        if query.start_date:
            params["start_date"] = query.start_date
        
        if query.end_date:
            params["end_date"] = query.end_date
        
        return params
