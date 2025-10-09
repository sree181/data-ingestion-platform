"""
ClinicalTrials.gov Data Connector
=================================

Connector for the ClinicalTrials.gov API (https://clinicaltrials.gov/api/v2/studies).
Provides access to 400K+ clinical trials worldwide.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import aiohttp
import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import json

from ..base.abstract_data_source import (
    AbstractDataSource, StandardDocument, SourceType, DocumentType, 
    Author, Entity, Relationship, DataSourceError, NetworkError
)

logger = logging.getLogger(__name__)

class ClinicalTrialsConnector(AbstractDataSource):
    """
    ClinicalTrials.gov data connector
    
    Provides access to clinical trials data from the US National Library of Medicine.
    No API key required, but rate limiting applies.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    @property
    def source_name(self) -> str:
        return "clinicaltrials"
    
    @property
    def display_name(self) -> str:
        return "ClinicalTrials.gov"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.CLINICAL_TRIAL
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.CLINICAL_TRIAL]
    
    @property
    def description(self) -> str:
        return "US National Library of Medicine clinical trials database with 400K+ trials worldwide"
    
    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "requests_per_second": 1,  # Conservative limit
            "requests_per_minute": 60,
            "requests_per_hour": 3600,
            "requests_per_day": 100000
        }
    
    def supports_full_text(self) -> bool:
        return True  # ClinicalTrials.gov provides detailed descriptions
    
    def supports_real_time_updates(self) -> bool:
        return True  # Can poll for new trials
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """
        Search ClinicalTrials.gov for clinical trials
        
        Args:
            query: Search query (searches across multiple fields)
            max_results: Maximum number of results (max 1000 per API)
            filters: Additional filters like condition, intervention, status
            date_from: Start date for trial start date
            date_to: End date for trial start date
            
        Returns:
            List of clinical trials as StandardDocument
        """
        try:
            # Build query parameters
            params = {
                "query.term": query,
                "pageSize": min(max_results, 1000),  # API limit
                "format": "json"
            }
            
            # Add filters
            if filters:
                if filters.get("condition"):
                    params["query.cond"] = filters["condition"]
                if filters.get("intervention"):
                    params["query.intr"] = filters["intervention"]
                if filters.get("status"):
                    params["filter.overallStatus"] = filters["status"]
                if filters.get("phase"):
                    params["filter.phase"] = filters["phase"]
                if filters.get("sponsor"):
                    params["query.spons"] = filters["sponsor"]
                if filters.get("location"):
                    params["query.locn"] = filters["location"]
            
            # Add date filters
            if date_from:
                params["filter.startDate"] = date_from.strftime("%Y-%m-%d")
            if date_to:
                params["filter.endDate"] = date_to.strftime("%Y-%m-%d")
            
            self.logger.info(f"Searching ClinicalTrials.gov: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"ClinicalTrials.gov API error: {response.status}")
                    
                    data = await response.json()
            
            # Extract studies
            studies = data.get("studies", [])
            self.logger.info(f"Found {len(studies)} clinical trials")
            
            # Transform to StandardDocument
            documents = []
            for study in studies:
                try:
                    doc = self.transform_to_standard(study)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform study {study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'unknown')}: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing ClinicalTrials.gov: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching ClinicalTrials.gov: {e}")
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific clinical trial by NCT ID
        
        Args:
            source_id: NCT ID (e.g., "NCT12345678")
            
        Returns:
            Clinical trial as StandardDocument
        """
        try:
            # ClinicalTrials.gov API doesn't have a direct single-study endpoint
            # So we search for the specific NCT ID
            params = {
                "query.term": source_id,
                "pageSize": 1,
                "format": "json"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"ClinicalTrials.gov API error: {response.status}")
                    
                    data = await response.json()
            
            studies = data.get("studies", [])
            if not studies:
                raise DataSourceError(f"Clinical trial not found: {source_id}")
            
            return self.transform_to_standard(studies[0])
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error fetching trial {source_id}: {e}")
        except Exception as e:
            raise DataSourceError(f"Error fetching trial {source_id}: {e}")
    
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """
        Get full text description of a clinical trial
        
        Args:
            source_id: NCT ID
            
        Returns:
            Full text description or None
        """
        try:
            doc = await self.fetch_by_id(source_id)
            return doc.content
        except Exception as e:
            self.logger.error(f"Failed to get full text for {source_id}: {e}")
            return None
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """
        Convert ClinicalTrials.gov JSON to StandardDocument
        
        Args:
            raw_data: Raw study data from ClinicalTrials.gov API
            
        Returns:
            StandardDocument instance
        """
        try:
            protocol = raw_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            conditions = protocol.get("conditionsModule", {})
            interventions = protocol.get("armsInterventionsModule", {})
            outcomes = protocol.get("outcomesModule", {})
            contacts = protocol.get("contactsLocationsModule", {})
            sponsor = protocol.get("sponsorCollaboratorsModule", {})
            
            # Extract basic info
            nct_id = identification.get("nctId", "")
            brief_title = identification.get("briefTitle", "")
            official_title = identification.get("officialTitle", "")
            brief_summary = description.get("briefSummary", "")
            detailed_description = description.get("detailedDescription", "")
            
            # Extract dates
            start_date = None
            if status.get("startDateStruct", {}).get("date"):
                try:
                    start_date = datetime.fromisoformat(status["startDateStruct"]["date"])
                except:
                    pass
            
            # Extract authors (investigators)
            authors = []
            if contacts.get("overallOfficial"):
                for i, official in enumerate(contacts["overallOfficial"]):
                    authors.append(Author(
                        name=official.get("name", ""),
                        affiliation=official.get("affiliation", ""),
                        position=i
                    ))
            
            # Extract entities (conditions, interventions)
            entities = {
                "DISEASE": [],
                "INTERVENTION": [],
                "ORGANIZATION": []
            }
            
            # Conditions
            for condition in conditions.get("conditions", []):
                entities["DISEASE"].append(Entity(
                    value=condition,
                    normalized_value=condition.lower(),
                    entity_type="DISEASE",
                    confidence=0.9,
                    source="clinicaltrials"
                ))
            
            # Interventions
            for intervention in interventions.get("interventions", []):
                intervention_name = intervention.get("name", "")
                if intervention_name:
                    entities["INTERVENTION"].append(Entity(
                        value=intervention_name,
                        normalized_value=intervention_name.lower(),
                        entity_type="INTERVENTION",
                        confidence=0.9,
                        source="clinicaltrials"
                    ))
            
            # Sponsor
            lead_sponsor = sponsor.get("leadSponsor", {})
            if lead_sponsor.get("name"):
                entities["ORGANIZATION"].append(Entity(
                    value=lead_sponsor["name"],
                    normalized_value=lead_sponsor["name"].lower(),
                    entity_type="ORGANIZATION",
                    confidence=0.95,
                    source="clinicaltrials"
                ))
            
            # Extract key concepts
            key_concepts = []
            if design.get("phases"):
                key_concepts.extend([f"Phase {phase}" for phase in design["phases"]])
            if status.get("overallStatus"):
                key_concepts.append(f"Status: {status['overallStatus']}")
            if design.get("studyType"):
                key_concepts.append(f"Study Type: {design['studyType']}")
            
            # Create relationships
            relationships = []
            if entities["DISEASE"] and entities["INTERVENTION"]:
                for disease in entities["DISEASE"]:
                    for intervention in entities["INTERVENTION"]:
                        relationships.append(Relationship(
                            subject=intervention.normalized_value,
                            predicate="TREATS",
                            object=disease.normalized_value,
                            confidence=0.8,
                            source="clinicaltrials"
                        ))
            
            # Build content
            content_parts = []
            if brief_summary:
                content_parts.append(f"Summary: {brief_summary}")
            if detailed_description:
                content_parts.append(f"Description: {detailed_description}")
            
            content = "\n\n".join(content_parts) if content_parts else None
            
            # Calculate quality score
            quality_score = 0.0
            if brief_title: quality_score += 10
            if brief_summary: quality_score += 20
            if detailed_description: quality_score += 30
            if nct_id: quality_score += 10
            if authors: quality_score += 10
            if start_date: quality_score += 10
            if entities["DISEASE"]: quality_score += 5
            if entities["INTERVENTION"]: quality_score += 5
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="clinicaltrials",
                source_id=nct_id,
                title=official_title or brief_title,
                abstract=brief_summary,
                content=content,
                document_type=DocumentType.CLINICAL_TRIAL,
                publication_date=start_date,
                authors=authors,
                url=f"https://clinicaltrials.gov/study/{nct_id}",
                entities=entities,
                relationships=relationships,
                key_concepts=key_concepts,
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "nct_id": nct_id,
                    "brief_title": brief_title,
                    "official_title": official_title,
                    "sponsor": lead_sponsor.get("name"),
                    "phase": design.get("phases", []),
                    "status": status.get("overallStatus"),
                    "enrollment": status.get("enrollmentInfo", {}).get("count"),
                    "conditions": conditions.get("conditions", []),
                    "interventions": [
                        {
                            "name": intv.get("name"),
                            "type": intv.get("type"),
                            "description": intv.get("description")
                        } for intv in interventions.get("interventions", [])
                    ],
                    "outcomes": outcomes,
                    "locations": [
                        {
                            "name": loc.get("name"),
                            "city": loc.get("city"),
                            "state": loc.get("state"),
                            "country": loc.get("country")
                        } for loc in contacts.get("locations", [])
                    ],
                    "study_type": design.get("studyType"),
                    "allocation": design.get("allocation"),
                    "intervention_model": design.get("interventionModel"),
                    "primary_purpose": design.get("primaryPurpose"),
                    "masking": design.get("masking"),
                    "start_date": status.get("startDateStruct", {}).get("date"),
                    "completion_date": status.get("completionDateStruct", {}).get("date"),
                    "last_update": status.get("lastUpdateDateStruct", {}).get("date")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming ClinicalTrials.gov data: {e}")
            raise DataSourceError(f"Failed to transform clinical trial data: {e}")
    
    def validate_config(self) -> bool:
        """ClinicalTrials.gov doesn't require API key"""
        return True
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for clinical trial"""
        nct_id = doc.metadata.get("nct_id", "")
        sponsor = doc.metadata.get("sponsor", "Unknown Sponsor")
        year = doc.publication_date.year if doc.publication_date else "Unknown"
        
        return f"{sponsor} ({year}). {doc.title}. ClinicalTrials.gov Identifier: {nct_id}"
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to clinical trials"""
        base_indicators = super().get_quality_indicators(doc)
        
        # Clinical trial specific indicators
        trial_indicators = {
            "has_nct_id": bool(doc.metadata.get("nct_id")),
            "has_sponsor": bool(doc.metadata.get("sponsor")),
            "has_phase": bool(doc.metadata.get("phase")),
            "has_conditions": bool(doc.metadata.get("conditions")),
            "has_interventions": bool(doc.metadata.get("interventions")),
            "has_enrollment": bool(doc.metadata.get("enrollment")),
            "is_recruiting": doc.metadata.get("status") == "Recruiting",
            "has_locations": bool(doc.metadata.get("locations"))
        }
        
        base_indicators.update(trial_indicators)
        return base_indicators
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if ClinicalTrials.gov is accessible"""
        try:
            start_time = datetime.now()
            
            # Try a simple search
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(self.base_url, params={"query.term": "cancer", "pageSize": 1}) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        return {
                            "status": "healthy",
                            "response_time_ms": int(response_time),
                            "last_check": datetime.now().isoformat(),
                            "api_status": "accessible"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"API returned status {response.status}",
                            "last_check": datetime.now().isoformat()
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
