"""
FDA OpenFDA Data Connector
==========================

Connector for the FDA OpenFDA API (https://open.fda.gov/).
Provides access to adverse events, drug labels, and other FDA data.

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

class FDAConnector(AbstractDataSource):
    """
    FDA OpenFDA data connector
    
    Provides access to FDA data including:
    - Drug adverse events
    - Drug labels
    - Device recalls
    - Food recalls
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://api.fda.gov"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.api_key = api_key  # Optional for OpenFDA
    
    @property
    def source_name(self) -> str:
        return "fda"
    
    @property
    def display_name(self) -> str:
        return "FDA OpenFDA"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.REGULATORY
    
    @property
    def supported_document_types(self) -> List[DocumentType]:
        return [DocumentType.ADVERSE_EVENT, DocumentType.DRUG_LABEL]
    
    @property
    def description(self) -> str:
        return "US Food and Drug Administration open data including adverse events, drug labels, and recalls"
    
    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "requests_per_second": 1,  # OpenFDA rate limit
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
    
    def supports_full_text(self) -> bool:
        return True  # FDA provides detailed descriptions
    
    def supports_real_time_updates(self) -> bool:
        return True  # Can poll for new data
    
    async def search(
        self, 
        query: str, 
        max_results: int = 100,
        filters: Optional[Dict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """
        Search FDA OpenFDA across multiple endpoints
        
        Args:
            query: Search query (searches drug names, adverse events, etc.)
            max_results: Maximum number of results
            filters: Additional filters like endpoint, drug_name, etc.
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            List of FDA documents as StandardDocument
        """
        try:
            documents = []
            
            # Search adverse events
            if not filters or filters.get("endpoint") != "labels":
                ae_docs = await self._search_adverse_events(
                    query, max_results // 2, date_from, date_to
                )
                documents.extend(ae_docs)
            
            # Search drug labels
            if not filters or filters.get("endpoint") != "adverse_events":
                label_docs = await self._search_drug_labels(
                    query, max_results // 2, date_from, date_to
                )
                documents.extend(label_docs)
            
            # Limit total results
            return documents[:max_results]
            
        except Exception as e:
            raise DataSourceError(f"Error searching FDA OpenFDA: {e}")
    
    async def _search_adverse_events(
        self, 
        query: str, 
        max_results: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search adverse events endpoint"""
        try:
            url = f"{self.base_url}/drug/event.json"
            params = {
                "search": f"patient.drug.medicinalproduct:\"{query}\"",
                "limit": min(max_results, 1000),  # API limit
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Add date filters
            if date_from:
                params["search"] += f"+receivedate:[{date_from.strftime('%Y%m%d')}+TO+*]"
            if date_to:
                params["search"] += f"+receivedate:[*+TO+{date_to.strftime('%Y%m%d')}]"
            
            self.logger.info(f"Searching FDA adverse events: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"FDA API error: {response.status}")
                    
                    data = await response.json()
            
            events = data.get("results", [])
            self.logger.info(f"Found {len(events)} adverse events")
            
            documents = []
            for event in events:
                try:
                    doc = self._transform_adverse_event(event)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform adverse event: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing FDA adverse events: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching FDA adverse events: {e}")
    
    async def _search_drug_labels(
        self, 
        query: str, 
        max_results: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[StandardDocument]:
        """Search drug labels endpoint"""
        try:
            url = f"{self.base_url}/drug/label.json"
            params = {
                "search": f"openfda.brand_name:\"{query}\"",
                "limit": min(max_results, 1000),  # API limit
                "format": "json"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Add date filters
            if date_from:
                params["search"] += f"+effective_time:[{date_from.strftime('%Y%m%d')}+TO+*]"
            if date_to:
                params["search"] += f"+effective_time:[*+TO+{date_to.strftime('%Y%m%d')}]"
            
            self.logger.info(f"Searching FDA drug labels: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise NetworkError(f"FDA API error: {response.status}")
                    
                    data = await response.json()
            
            labels = data.get("results", [])
            self.logger.info(f"Found {len(labels)} drug labels")
            
            documents = []
            for label in labels:
                try:
                    doc = self._transform_drug_label(label)
                    documents.append(doc)
                except Exception as e:
                    self.logger.error(f"Failed to transform drug label: {e}")
                    continue
            
            return documents
            
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error accessing FDA drug labels: {e}")
        except Exception as e:
            raise DataSourceError(f"Error searching FDA drug labels: {e}")
    
    async def fetch_by_id(self, source_id: str) -> StandardDocument:
        """
        Fetch a specific FDA document by ID
        
        Args:
            source_id: FDA document ID
            
        Returns:
            Document as StandardDocument
        """
        try:
            # Try adverse events first
            try:
                url = f"{self.base_url}/drug/event.json"
                params = {"search": f"safetyreportid:{source_id}", "limit": 1}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            events = data.get("results", [])
                            if events:
                                return self._transform_adverse_event(events[0])
            except:
                pass
            
            # Try drug labels
            try:
                url = f"{self.base_url}/drug/label.json"
                params = {"search": f"id:{source_id}", "limit": 1}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            labels = data.get("results", [])
                            if labels:
                                return self._transform_drug_label(labels[0])
            except:
                pass
            
            raise DataSourceError(f"FDA document not found: {source_id}")
            
        except DataSourceError:
            raise
        except Exception as e:
            raise DataSourceError(f"Error fetching FDA document {source_id}: {e}")
    
    async def get_full_text(self, source_id: str) -> Optional[str]:
        """Get full text of FDA document"""
        try:
            doc = await self.fetch_by_id(source_id)
            return doc.content
        except Exception as e:
            self.logger.error(f"Failed to get full text for {source_id}: {e}")
            return None
    
    def _transform_adverse_event(self, raw_data: Dict) -> StandardDocument:
        """Transform FDA adverse event to StandardDocument"""
        try:
            # Extract basic info
            safety_report_id = raw_data.get("safetyreportid", "")
            received_date = raw_data.get("receivedate", "")
            serious = raw_data.get("serious", 0)
            company_numb = raw_data.get("companynumb", "")
            
            # Extract patient info
            patient = raw_data.get("patient", {})
            patient_age = patient.get("patientonsetage", "")
            patient_sex = patient.get("patientsex", "")
            
            # Extract drug info
            drugs = patient.get("drug", [])
            drug_names = []
            drug_manufacturers = []
            
            for drug in drugs:
                if drug.get("medicinalproduct"):
                    drug_names.append(drug["medicinalproduct"])
                if drug.get("openfda", {}).get("manufacturer_name"):
                    drug_manufacturers.extend(drug["openfda"]["manufacturer_name"])
            
            # Extract reactions
            reactions = patient.get("reaction", [])
            reaction_terms = [r.get("reactionmeddrapt", "") for r in reactions if r.get("reactionmeddrapt")]
            
            # Extract indications
            indications = []
            for drug in drugs:
                if drug.get("drugindication"):
                    indications.append(drug["drugindication"])
            
            # Build title and content
            primary_drug = drug_names[0] if drug_names else "Unknown Drug"
            primary_reaction = reaction_terms[0] if reaction_terms else "Adverse Event"
            
            title = f"Adverse Event Report: {primary_drug} - {primary_reaction}"
            
            content_parts = []
            if drug_names:
                content_parts.append(f"Drug(s): {', '.join(drug_names)}")
            if reaction_terms:
                content_parts.append(f"Reaction(s): {', '.join(reaction_terms)}")
            if indications:
                content_parts.append(f"Indication(s): {', '.join(indications)}")
            if patient_age:
                content_parts.append(f"Patient Age: {patient_age}")
            if patient_sex:
                content_parts.append(f"Patient Sex: {patient_sex}")
            
            content = "\n".join(content_parts)
            
            # Extract entities
            entities = {
                "DRUG": [],
                "DISEASE": [],
                "ORGANIZATION": []
            }
            
            # Drug entities
            for drug_name in drug_names:
                entities["DRUG"].append(Entity(
                    value=drug_name,
                    normalized_value=drug_name.lower(),
                    entity_type="DRUG",
                    confidence=0.9,
                    source="fda"
                ))
            
            # Disease/reaction entities
            for reaction in reaction_terms:
                entities["DISEASE"].append(Entity(
                    value=reaction,
                    normalized_value=reaction.lower(),
                    entity_type="DISEASE",
                    confidence=0.8,
                    source="fda"
                ))
            
            # Manufacturer entities
            for manufacturer in drug_manufacturers:
                entities["ORGANIZATION"].append(Entity(
                    value=manufacturer,
                    normalized_value=manufacturer.lower(),
                    entity_type="ORGANIZATION",
                    confidence=0.9,
                    source="fda"
                ))
            
            # Parse date
            publication_date = None
            if received_date:
                try:
                    publication_date = datetime.strptime(received_date, "%Y%m%d")
                except:
                    pass
            
            # Calculate quality score
            quality_score = 0.0
            if safety_report_id: quality_score += 10
            if drug_names: quality_score += 20
            if reaction_terms: quality_score += 20
            if content: quality_score += 20
            if publication_date: quality_score += 10
            if serious: quality_score += 10  # Serious events are more valuable
            if patient_age: quality_score += 5
            if patient_sex: quality_score += 5
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="fda",
                source_id=safety_report_id,
                title=title,
                abstract=f"FDA adverse event report for {primary_drug}",
                content=content,
                document_type=DocumentType.ADVERSE_EVENT,
                publication_date=publication_date,
                authors=[],  # No authors for adverse events
                url=f"https://open.fda.gov/drug/event/",
                entities=entities,
                relationships=[],
                key_concepts=[
                    f"Serious: {'Yes' if serious else 'No'}",
                    f"Company: {company_numb}" if company_numb else "Unknown Company"
                ],
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "safety_report_id": safety_report_id,
                    "received_date": received_date,
                    "serious": bool(serious),
                    "company_number": company_numb,
                    "patient_age": patient_age,
                    "patient_sex": patient_sex,
                    "drug_names": drug_names,
                    "reaction_terms": reaction_terms,
                    "indications": indications,
                    "drug_manufacturers": drug_manufacturers,
                    "raw_data": raw_data  # Keep original for reference
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming FDA adverse event: {e}")
            raise DataSourceError(f"Failed to transform adverse event: {e}")
    
    def _transform_drug_label(self, raw_data: Dict) -> StandardDocument:
        """Transform FDA drug label to StandardDocument"""
        try:
            # Extract basic info
            label_id = raw_data.get("id", "")
            effective_time = raw_data.get("effective_time", "")
            openfda = raw_data.get("openfda", {})
            
            # Extract drug names
            brand_name = openfda.get("brand_name", [""])[0] if openfda.get("brand_name") else ""
            generic_name = openfda.get("generic_name", [""])[0] if openfda.get("generic_name") else ""
            product_ndc = openfda.get("product_ndc", [""])[0] if openfda.get("product_ndc") else ""
            
            # Extract manufacturer
            manufacturer = openfda.get("manufacturer_name", [""])[0] if openfda.get("manufacturer_name") else ""
            
            # Extract indications and warnings
            indications = raw_data.get("indications_and_usage", [])
            warnings = raw_data.get("warnings", [])
            contraindications = raw_data.get("contraindications", [])
            
            # Build title and content
            drug_name = brand_name or generic_name or "Unknown Drug"
            title = f"Drug Label: {drug_name}"
            
            content_parts = []
            if indications:
                content_parts.append(f"Indications: {' '.join(indications)}")
            if warnings:
                content_parts.append(f"Warnings: {' '.join(warnings)}")
            if contraindications:
                content_parts.append(f"Contraindications: {' '.join(contraindications)}")
            
            content = "\n\n".join(content_parts)
            
            # Extract entities
            entities = {
                "DRUG": [],
                "DISEASE": [],
                "ORGANIZATION": []
            }
            
            # Drug entities
            if brand_name:
                entities["DRUG"].append(Entity(
                    value=brand_name,
                    normalized_value=brand_name.lower(),
                    entity_type="DRUG",
                    confidence=0.95,
                    source="fda"
                ))
            
            if generic_name:
                entities["DRUG"].append(Entity(
                    value=generic_name,
                    normalized_value=generic_name.lower(),
                    entity_type="DRUG",
                    confidence=0.9,
                    source="fda"
                ))
            
            # Manufacturer entity
            if manufacturer:
                entities["ORGANIZATION"].append(Entity(
                    value=manufacturer,
                    normalized_value=manufacturer.lower(),
                    entity_type="ORGANIZATION",
                    confidence=0.9,
                    source="fda"
                ))
            
            # Parse date
            publication_date = None
            if effective_time:
                try:
                    publication_date = datetime.strptime(effective_time, "%Y%m%d")
                except:
                    pass
            
            # Calculate quality score
            quality_score = 0.0
            if label_id: quality_score += 10
            if drug_name: quality_score += 20
            if content: quality_score += 30
            if publication_date: quality_score += 10
            if manufacturer: quality_score += 10
            if product_ndc: quality_score += 10
            if indications: quality_score += 5
            if warnings: quality_score += 5
            
            return StandardDocument(
                id=str(uuid.uuid4()),
                source="fda",
                source_id=label_id,
                title=title,
                abstract=f"FDA drug label for {drug_name}",
                content=content,
                document_type=DocumentType.DRUG_LABEL,
                publication_date=publication_date,
                authors=[],  # No authors for drug labels
                url=f"https://open.fda.gov/drug/label/",
                entities=entities,
                relationships=[],
                key_concepts=[
                    f"Brand: {brand_name}" if brand_name else "",
                    f"Generic: {generic_name}" if generic_name else "",
                    f"NDC: {product_ndc}" if product_ndc else ""
                ],
                quality_score=quality_score,
                processing_status="completed",
                metadata={
                    "label_id": label_id,
                    "effective_time": effective_time,
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "product_ndc": product_ndc,
                    "manufacturer": manufacturer,
                    "indications": indications,
                    "warnings": warnings,
                    "contraindications": contraindications,
                    "openfda": openfda,
                    "raw_data": raw_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming FDA drug label: {e}")
            raise DataSourceError(f"Failed to transform drug label: {e}")
    
    def transform_to_standard(self, raw_data: Dict) -> StandardDocument:
        """Convert FDA data to StandardDocument (delegates to specific methods)"""
        # This method is called by the base class, but we handle transformation
        # in the specific search methods. This is a fallback.
        if "safetyreportid" in raw_data:
            return self._transform_adverse_event(raw_data)
        elif "id" in raw_data and "openfda" in raw_data:
            return self._transform_drug_label(raw_data)
        else:
            raise DataSourceError("Unknown FDA data format")
    
    def validate_config(self) -> bool:
        """FDA OpenFDA doesn't require API key for basic usage"""
        return True
    
    def get_citation_format(self, doc: StandardDocument) -> str:
        """Generate proper citation for FDA document"""
        if doc.document_type == DocumentType.ADVERSE_EVENT:
            report_id = doc.metadata.get("safety_report_id", "")
            year = doc.publication_date.year if doc.publication_date else "Unknown"
            return f"FDA ({year}). Adverse Event Report {report_id}. {doc.title}"
        else:
            drug_name = doc.metadata.get("brand_name", doc.metadata.get("generic_name", "Unknown"))
            year = doc.publication_date.year if doc.publication_date else "Unknown"
            return f"FDA ({year}). Drug Label: {drug_name}. {doc.title}"
    
    def get_quality_indicators(self, doc: StandardDocument) -> Dict[str, Any]:
        """Get quality indicators specific to FDA documents"""
        base_indicators = super().get_quality_indicators(doc)
        
        if doc.document_type == DocumentType.ADVERSE_EVENT:
            fda_indicators = {
                "has_safety_report_id": bool(doc.metadata.get("safety_report_id")),
                "is_serious": doc.metadata.get("serious", False),
                "has_drug_names": bool(doc.metadata.get("drug_names")),
                "has_reactions": bool(doc.metadata.get("reaction_terms")),
                "has_patient_info": bool(doc.metadata.get("patient_age") or doc.metadata.get("patient_sex")),
                "has_company": bool(doc.metadata.get("company_number"))
            }
        else:  # DRUG_LABEL
            fda_indicators = {
                "has_label_id": bool(doc.metadata.get("label_id")),
                "has_brand_name": bool(doc.metadata.get("brand_name")),
                "has_generic_name": bool(doc.metadata.get("generic_name")),
                "has_manufacturer": bool(doc.metadata.get("manufacturer")),
                "has_indications": bool(doc.metadata.get("indications")),
                "has_warnings": bool(doc.metadata.get("warnings")),
                "has_ndc": bool(doc.metadata.get("product_ndc"))
            }
        
        base_indicators.update(fda_indicators)
        return base_indicators
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if FDA OpenFDA is accessible"""
        try:
            start_time = datetime.now()
            
            # Try a simple search
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/drug/event.json", 
                                     params={"search": "aspirin", "limit": 1}) as response:
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
