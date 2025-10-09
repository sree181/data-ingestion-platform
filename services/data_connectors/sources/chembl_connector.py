"""
ChEMBL Data Connector
=====================

Connector for the ChEMBL API (https://www.ebi.ac.uk/chembl/).
Provides access to 2.3M+ chemical compounds and 19M+ bioactivity data points.

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
    Author, Entity, Relationship, DataSourceError, NetworkError, AuthenticationError
)

logger = logging.getLogger(__name__)

class ChEMBLConnector(AbstractDataSource):
    """
    ChEMBL data connector
    
    Provides access to:
    - Chemical compounds (2.3M+)
    - Bioactivity data (19M+)
    - Drug targets and mechanisms
    - Clinical trials data
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://www.ebi.ac.uk/chembl/api/data"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.api_key = api_key  # Required for ChEMBL
    
    @property
    def source_name(self) -> str:
        return "chembl"
    
    @property
    def display_name(self) -> str:
        return "ChEMBL"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.CHEMICAL
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.CHEMICAL_COMPOUND, DocumentType.CLINICAL_TRIAL]
    
    @property
    def description(self) -> str:
        return "EMBL-EBI chemical database of bioactive molecules with 2.3M+ compounds and 19M+ bioactivity data points"
    
    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "requests_per_second": 2,  # ChEMBL rate limit
            "requests_per_minute": 120,
            "requests_per_hour": 7200,
            "requests_per_day": 100000
        }
    
    def supports_full_text(self) -> bool:
        return True  # ChEMBL provides detailed compound information
    
    def supports_real_time_updates(self) -> bool:
        return True  # Can poll for new compounds
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """
        Search ChEMBL for compounds and bioactivity data
        
        Args:
            query: Search query (compound name, ChEMBL ID, etc.)
            max_results: Maximum number of results
            filters: Additional filters like molecule_type, max_phase, etc.
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            List of ChEMBL documents as StandardDocument
        """
        try:
            documents = []
            
            # Search molecules
            if not filters or filters.get("endpoint") != "activities":
                molecule_docs = await self._search_molecules(
                    query, max_results // 2, date_from, date_to
                )
                documents.extend(molecule_docs)
            
            # Search activities
            if not filters or filters.get("endpoint") != "molecules":
                activity_docs = await self._search_activities(
                    query, max_results // 2, date_from, date_to
                )
                documents.extend(activity_docs)
            
            # Limit total results
            return documents[:max_results]
            
        except Exception as e:
            raise DataSourceError(f"Error searching ChEMBL: {e}")
    
    async def _search_molecules(
        self, 
        query: str, 
        max_results: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search molecules endpoint"""
        try:
            url = f"{self.base_url}/molecule"
            params = {
                "search": query,
                "limit": min(max_results, 1000),  # API limit
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            self.logger.info(f"Searching ChEMBL molecules: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 401:
                        raise AuthenticationError("ChEMBL API key required or invalid")
                    elif response.status != 200:
                        raise NetworkError(f"ChEMBL API error: {response.status}")
                    
                    data = await response.json()
            
            molecules = data.get("molecules", [])
            self.logger.info(f"Found {len(molecules)} molecules")
            
            documents = []
            for molecule in molecules:
                try:
                    doc = self._transform_molecule(molecule)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform molecule: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing ChEMBL molecules: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching ChEMBL molecules: {e}")
    
    async def _search_activities(
        self, 
        query: str, 
        max_results: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search activities endpoint"""
        try:
            url = f"{self.base_url}/activity"
            params = {
                "search": query,
                "limit": min(max_results, 1000),  # API limit
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            self.logger.info(f"Searching ChEMBL activities: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 401:
                        raise AuthenticationError("ChEMBL API key required or invalid")
                    elif response.status != 200:
                        raise NetworkError(f"ChEMBL API error: {response.status}")
                    
                    data = await response.json()
            
            activities = data.get("activities", [])
            self.logger.info(f"Found {len(activities)} activities")
            
            documents = []
            for activity in activities:
                try:
                    doc = self._transform_activity(activity)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform activity: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing ChEMBL activities: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching ChEMBL activities: {e}")
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific ChEMBL document by ID
        
        Args:
            source_id: ChEMBL ID (e.g., CHEMBL25)
            
        Returns:
            Document as StandardDocument
        """
        try:
            # Try molecules first
            try:
                url = f"{self.base_url}/molecule/{source_id}"
                params = {"format": "json"}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._transform_molecule(data)
            except:
                pass
            
            # Try activities
            try:
                url = f"{self.base_url}/activity/{source_id}"
                params = {"format": "json"}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._transform_activity(data)
            except:
                pass
            
            raise DataSourceError(f"ChEMBL document not found: {source_id}")
            
        except DataSourceError:
            raise
        except Exception as e:
            raise DataSourceError(f"Error fetching ChEMBL document {source_id}: {e}")
    
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """Get full text of ChEMBL document"""
        try:
            doc = await self.fetch_by_id(source_id)
            return doc.content
        except Exception as e:
            self.logger.error(f"Failed to get full text for {source_id}: {e}")
            return None
    
    def _transform_molecule(self, raw_data: Dict) -> StandardDocument:
        """Transform ChEMBL molecule to StandardDocument"""
        try:
            # Extract basic info
            chembl_id = raw_data.get("molecule_chembl_id", "")
            pref_name = raw_data.get("pref_name", "")
            molecule_type = raw_data.get("molecule_type", "")
            max_phase = raw_data.get("max_phase", 0)
            first_approval = raw_data.get("first_approval", "")
            
            # Extract synonyms
            synonyms = raw_data.get("molecule_synonyms", [])
            synonym_names = [s.get("molecule_synonym", "") for s in synonyms if s.get("molecule_synonym")]
            
            # Extract properties
            properties = raw_data.get("molecule_properties", {})
            mw_freebase = properties.get("mw_freebase")
            mw_monoisotopic = properties.get("mw_monoisotopic")
            logp = properties.get("alogp")
            hba = properties.get("hba")
            hbd = properties.get("hbd")
            psa = properties.get("psa")
            
            # Extract indications
            indications = raw_data.get("indication_class", [])
            indication_names = [i.get("indication_class", "") for i in indications if i.get("indication_class")]
            
            # Extract mechanisms
            mechanisms = raw_data.get("mechanism_of_action", [])
            mechanism_descriptions = [m.get("mechanism_of_action", "") for m in mechanisms if m.get("mechanism_of_action")]
            
            # Build title and content
            compound_name = pref_name or synonym_names[0] if synonym_names else chembl_id
            title = f"Chemical Compound: {compound_name}"
            
            content_parts = []
            if molecule_type:
                content_parts.append(f"Type: {molecule_type}")
            if max_phase:
                content_parts.append(f"Max Phase: {max_phase}")
            if first_approval:
                content_parts.append(f"First Approval: {first_approval}")
            if indication_names:
                content_parts.append(f"Indications: {', '.join(indication_names)}")
            if mechanism_descriptions:
                content_parts.append(f"Mechanism: {'; '.join(mechanism_descriptions)}")
            
            # Add properties
            if mw_freebase:
                content_parts.append(f"Molecular Weight: {mw_freebase}")
            if logp:
                content_parts.append(f"LogP: {logp}")
            if hba:
                content_parts.append(f"HBA: {hba}")
            if hbd:
                content_parts.append(f"HBD: {hbd}")
            
            content = "\n".join(content_parts)
            
            # Extract entities
            entities = {
                "DRUG": [],
                "DISEASE": [],
                "TARGET": []
            }
            
            # Drug entity
            entities["DRUG"].append(Entity(
                value=compound_name,
                normalized_value=compound_name.lower(),
                entity_type="DRUG",
                confidence=0.95,
                source="chembl"
            ))
            
            # Add synonyms as drug entities
            for synonym in synonym_names[:5]:  # Limit to first 5
                entities["DRUG"].append(Entity(
                    value=synonym,
                    normalized_value=synonym.lower(),
                    entity_type="DRUG",
                    confidence=0.8,
                    source="chembl"
                ))
            
            # Disease entities from indications
            for indication in indication_names:
                entities["DISEASE"].append(Entity(
                    value=indication,
                    normalized_value=indication.lower(),
                    entity_type="DISEASE",
                    confidence=0.7,
                    source="chembl"
                ))
            
            # Parse date
            publication_date = None
            if first_approval:
                try:
                    publication_date = datetime.strptime(first_approval, "%Y-%m-%d")
                except:
                    pass
            
            # Calculate quality score
            quality_score = 0.0
            if chembl_id: quality_score += 10
            if compound_name: quality_score += 20
            if content: quality_score += 20
            if publication_date: quality_score += 10
            if max_phase > 0: quality_score += 15  # Higher phase = more valuable
            if indication_names: quality_score += 10
            if mechanism_descriptions: quality_score += 10
            if properties: quality_score += 5
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="chembl",
                source_id=chembl_id,
                title=title,
                abstract=f"ChEMBL compound {compound_name}",
                content=content,
                document_type=DocumentType.CHEMICAL_COMPOUND,
                publication_date=publication_date,
                authors=[],  # No authors for compounds
                url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
                entities=entities,
                relationships=[],
                key_concepts=[
                    f"Type: {molecule_type}" if molecule_type else "",
                    f"Phase: {max_phase}" if max_phase else "",
                    f"Approved: {first_approval}" if first_approval else ""
                ],
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "chembl_id": chembl_id,
                    "pref_name": pref_name,
                    "molecule_type": molecule_type,
                    "max_phase": max_phase,
                    "first_approval": first_approval,
                    "synonyms": synonym_names,
                    "indications": indication_names,
                    "mechanisms": mechanism_descriptions,
                    "properties": properties,
                    "raw_data": raw_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming ChEMBL molecule: {e}")
            raise DataSourceError(f"Failed to transform molecule: {e}")
    
    def _transform_activity(self, raw_data: Dict) -> StandardDocument:
        """Transform ChEMBL activity to StandardDocument"""
        try:
            # Extract basic info
            activity_id = raw_data.get("activity_id", "")
            assay_id = raw_data.get("assay_id", "")
            assay_type = raw_data.get("assay_type", "")
            assay_description = raw_data.get("assay_description", "")
            
            # Extract compound info
            molecule_chembl_id = raw_data.get("molecule_chembl_id", "")
            molecule_pref_name = raw_data.get("molecule_pref_name", "")
            
            # Extract target info
            target_chembl_id = raw_data.get("target_chembl_id", "")
            target_pref_name = raw_data.get("target_pref_name", "")
            target_organism = raw_data.get("target_organism", "")
            
            # Extract activity values
            standard_type = raw_data.get("standard_type", "")
            standard_value = raw_data.get("standard_value", "")
            standard_units = raw_data.get("standard_units", "")
            activity_comment = raw_data.get("activity_comment", "")
            
            # Build title and content
            compound_name = molecule_pref_name or molecule_chembl_id
            target_name = target_pref_name or target_chembl_id
            title = f"Bioactivity: {compound_name} on {target_name}"
            
            content_parts = []
            if assay_description:
                content_parts.append(f"Assay: {assay_description}")
            if standard_type and standard_value:
                content_parts.append(f"Activity: {standard_value} {standard_units} ({standard_type})")
            if target_organism:
                content_parts.append(f"Organism: {target_organism}")
            if activity_comment:
                content_parts.append(f"Comment: {activity_comment}")
            
            content = "\n".join(content_parts)
            
            # Extract entities
            entities = {
                "DRUG": [],
                "TARGET": [],
                "ORGANISM": []
            }
            
            # Drug entity
            if compound_name:
                entities["DRUG"].append(Entity(
                    value=compound_name,
                    normalized_value=compound_name.lower(),
                    entity_type="DRUG",
                    confidence=0.9,
                    source="chembl"
                ))
            
            # Target entity
            if target_name:
                entities["TARGET"].append(Entity(
                    value=target_name,
                    normalized_value=target_name.lower(),
                    entity_type="TARGET",
                    confidence=0.9,
                    source="chembl"
                ))
            
            # Organism entity
            if target_organism:
                entities["ORGANISM"].append(Entity(
                    value=target_organism,
                    normalized_value=target_organism.lower(),
                    entity_type="ORGANISM",
                    confidence=0.8,
                    source="chembl"
                ))
            
            # Calculate quality score
            quality_score = 0.0
            if activity_id: quality_score += 10
            if compound_name: quality_score += 15
            if target_name: quality_score += 15
            if content: quality_score += 20
            if standard_value: quality_score += 15
            if assay_description: quality_score += 10
            if target_organism: quality_score += 5
            if activity_comment: quality_score += 5
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="chembl",
                source_id=activity_id,
                title=title,
                abstract=f"Bioactivity data for {compound_name}",
                content=content,
                document_type=DocumentType.CHEMICAL_COMPOUND,  # Activities are compound-related
                publication_date=None,  # Activities don't have publication dates
                authors=[],  # No authors for activities
                url=f"https://www.ebi.ac.uk/chembl/assay_report_card/{assay_id}/",
                entities=entities,
                relationships=[],
                key_concepts=[
                    f"Assay Type: {assay_type}" if assay_type else "",
                    f"Activity: {standard_value} {standard_units}" if standard_value else "",
                    f"Target: {target_name}" if target_name else ""
                ],
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "activity_id": activity_id,
                    "assay_id": assay_id,
                    "assay_type": assay_type,
                    "assay_description": assay_description,
                    "molecule_chembl_id": molecule_chembl_id,
                    "molecule_pref_name": molecule_pref_name,
                    "target_chembl_id": target_chembl_id,
                    "target_pref_name": target_pref_name,
                    "target_organism": target_organism,
                    "standard_type": standard_type,
                    "standard_value": standard_value,
                    "standard_units": standard_units,
                    "activity_comment": activity_comment,
                    "raw_data": raw_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming ChEMBL activity: {e}")
            raise DataSourceError(f"Failed to transform activity: {e}")
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert ChEMBL data to StandardDocument (delegates to specific methods)"""
        if "molecule_chembl_id" in raw_data:
            return self._transform_molecule(raw_data)
        elif "activity_id" in raw_data:
            return self._transform_activity(raw_data)
        else:
            raise DataSourceError("Unknown ChEMBL data format")
    
    def validate_config(self) -> bool:
        """ChEMBL requires API key for most operations"""
        return bool(self.api_key)
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for ChEMBL document"""
        compound_name = doc.metadata.get("pref_name", doc.metadata.get("molecule_pref_name", "Unknown"))
        chembl_id = doc.source_id
        year = doc.publication_date.year if doc.publication_date else "Unknown"
        return f"ChEMBL ({year}). {compound_name} ({chembl_id}). {doc.title}"
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to ChEMBL documents"""
        base_indicators = super().get_quality_indicators(doc)
        
        if "molecule_chembl_id" in doc.metadata:
            # Molecule indicators
            chembl_indicators = {
                "has_chembl_id": bool(doc.metadata.get("chembl_id")),
                "has_pref_name": bool(doc.metadata.get("pref_name")),
                "has_synonyms": bool(doc.metadata.get("synonyms")),
                "has_indications": bool(doc.metadata.get("indications")),
                "has_mechanisms": bool(doc.metadata.get("mechanisms")),
                "has_properties": bool(doc.metadata.get("properties")),
                "is_approved": doc.metadata.get("max_phase", 0) > 0,
                "has_approval_date": bool(doc.metadata.get("first_approval"))
            }
        else:
            # Activity indicators
            chembl_indicators = {
                "has_activity_id": bool(doc.metadata.get("activity_id")),
                "has_compound": bool(doc.metadata.get("molecule_pref_name")),
                "has_target": bool(doc.metadata.get("target_pref_name")),
                "has_activity_value": bool(doc.metadata.get("standard_value")),
                "has_assay_description": bool(doc.metadata.get("assay_description")),
                "has_organism": bool(doc.metadata.get("target_organism"))
            }
        
        base_indicators.update(chembl_indicators)
        return base_indicators
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if ChEMBL is accessible"""
        try:
            start_time = datetime.now()
            
            # Try a simple search
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/molecule", 
                                     params={"search": "aspirin", "limit": 1, "api_key": self.api_key or ""}) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        return {
                            "status": "healthy",
                            "response_time_ms": int(response_time),
                            "last_check": datetime.now().isoformat(),
                            "api_status": "accessible"
                        }
                    elif response.status == 401:
                        return {
                            "status": "unhealthy",
                            "error": "API key required or invalid",
                            "last_check": datetime.now().isoformat()
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
