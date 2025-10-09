"""
Email Processing Service
Handles email classification and ICSR data extraction from safety emails
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from models.simple_icsr_models import (
    ICSRData, EmailProcessingResponse, ReportType, Gender, Outcome
)

logger = structlog.get_logger()

class EmailProcessingService:
    def __init__(self):
        self.classification_keywords = {
            'valid': ['adverse event', 'side effect', 'adverse reaction', 'adr', 'ae', 'safety concern'],
            'invalid': ['spam', 'test', 'unsubscribe', 'marketing'],
            'rejection': ['not related', 'wrong department', 'inquiry'],
            'irrelevant': ['general inquiry', 'product information', 'pricing']
        }
    
    async def process_email(
        self,
        email_id: str,
        subject: str,
        body: str,
        attachments: List[Dict[str, Any]],
        sender: str
    ) -> EmailProcessingResponse:
        """
        Process email for ICSR classification and data extraction
        """
        logger.info("Processing email", email_id=email_id, sender=sender)
        
        try:
            # Classify email
            classification, confidence = await self._classify_email(subject, body, sender)
            
            extracted_icsr_data = None
            processing_errors = []
            
            if classification == "Valid":
                # Extract ICSR data
                extracted_icsr_data = await self._extract_icsr_from_email(subject, body, attachments)
                if not extracted_icsr_data:
                    processing_errors.append("Failed to extract ICSR data from valid email")
            
            logger.info("Email processing completed", 
                       email_id=email_id, 
                       classification=classification,
                       confidence=confidence)
            
            return EmailProcessingResponse(
                success=True,
                classification=classification,
                confidence=confidence,
                extracted_icsr_data=extracted_icsr_data,
                processing_errors=processing_errors
            )
            
        except Exception as e:
            logger.error("Email processing failed", error=str(e))
            return EmailProcessingResponse(
                success=False,
                classification="Invalid",
                confidence=0.0,
                extracted_icsr_data=None,
                processing_errors=[f"Processing failed: {str(e)}"]
            )
    
    async def _classify_email(self, subject: str, body: str, sender: str) -> tuple[str, float]:
        """Classify email using keyword matching and AI"""
        text = f"{subject} {body}".lower()
        
        # Calculate scores for each category
        scores = {}
        for category, keywords in self.classification_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score
        
        # Determine classification
        if scores['invalid'] > 0:
            return "Invalid", 0.8
        elif scores['rejection'] > 0:
            return "Rejection", 0.7
        elif scores['irrelevant'] > 0:
            return "Irrelevant", 0.6
        elif scores['valid'] > 0:
            return "Valid", min(0.9, 0.5 + (scores['valid'] * 0.1))
        else:
            return "Invalid", 0.3
    
    async def _extract_icsr_from_email(
        self, 
        subject: str, 
        body: str, 
        attachments: List[Dict[str, Any]]
    ) -> Optional[ICSRData]:
        """Extract ICSR data from email content"""
        try:
            # Extract basic information
            general_info = self._extract_general_info(subject, body)
            patient_info = self._extract_patient_info(body)
            product_info = self._extract_product_info(body)
            event_info = self._extract_event_info(body)
            
            # Create ICSR data
            icsr_data = ICSRData(
                icsr_id=f"EMAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                general_information=general_info,
                patient_information=patient_info,
                product_information=product_info,
                event_information=event_info
            )
            
            return icsr_data
            
        except Exception as e:
            logger.error("ICSR extraction from email failed", error=str(e))
            return None
    
    def _extract_general_info(self, subject: str, body: str) -> Dict[str, Any]:
        """Extract general information from email"""
        return {
            "report_type": ReportType.SPONTANEOUS,
            "country": self._extract_country(body),
            "initial_receipt_date": datetime.now(),
            "medically_confirmed": self._is_medically_confirmed(body),
            "reporter_information": {
                "email_address": self._extract_email_address(body)
            }
        }
    
    def _extract_patient_info(self, body: str) -> Dict[str, Any]:
        """Extract patient information from email body"""
        return {
            "patient_details": {
                "gender": self._extract_gender(body),
                "age": self._extract_age(body),
                "age_unit": self._extract_age_unit(body)
            },
            "other_relevant_history": {
                "medical_history": self._extract_medical_history(body)
            }
        }
    
    def _extract_product_info(self, body: str) -> Dict[str, Any]:
        """Extract product information from email body"""
        return {
            "suspect_products": self._extract_suspect_products(body),
            "concomitant_medications": self._extract_concomitant_medications(body)
        }
    
    def _extract_event_info(self, body: str) -> Dict[str, Any]:
        """Extract event information from email body"""
        return {
            "description_as_reported": self._extract_event_description(body),
            "outcome": self._extract_outcome(body),
            "seriousness_criteria": self._extract_seriousness_criteria(body)
        }
    
    def _extract_country(self, text: str) -> str:
        """Extract country from text"""
        country_patterns = [
            r'country[:\s]+([A-Za-z\s]+)',
            r'from\s+([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s+patient'
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown"
    
    def _is_medically_confirmed(self, text: str) -> bool:
        """Check if case is medically confirmed"""
        hcp_indicators = ['physician', 'doctor', 'nurse', 'pharmacist', 'hcp']
        return any(indicator in text.lower() for indicator in hcp_indicators)
    
    def _extract_email_address(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_gender(self, text: str) -> Optional[Gender]:
        """Extract patient gender"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['male', 'man', 'boy']):
            return Gender.MALE
        elif any(word in text_lower for word in ['female', 'woman', 'girl']):
            return Gender.FEMALE
        return Gender.UNKNOWN
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract patient age"""
        age_patterns = [
            r'age[:\s]+(\d+)',
            r'(\d+)\s*years?\s*old',
            r'aged\s+(\d+)'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    age = int(match.group(1))
                    if 0 <= age <= 150:
                        return age
                except ValueError:
                    continue
        return None
    
    def _extract_age_unit(self, text: str) -> Optional[AgeUnit]:
        """Extract age unit"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['days', 'day-old']):
            return AgeUnit.DAYS
        elif any(word in text_lower for word in ['weeks', 'week-old']):
            return AgeUnit.WEEKS
        elif any(word in text_lower for word in ['months', 'month-old']):
            return AgeUnit.MONTHS
        return AgeUnit.YEARS
    
    def _extract_medical_history(self, text: str) -> Optional[str]:
        """Extract medical history"""
        history_patterns = [
            r'medical history[:\s]+([^.]+)',
            r'past history[:\s]+([^.]+)',
            r'history of[:\s]+([^.]+)'
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_suspect_products(self, text: str) -> List[Dict[str, Any]]:
        """Extract suspect products"""
        products = []
        drug_patterns = [
            r'(\w+)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g)',
            r'(\w+)\s+(\d+(?:\.\d+)?)\s*(mg/kg)'
        ]
        
        for pattern in drug_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                drug_name = match.group(1).strip()
                dose = match.group(2)
                unit = match.group(3)
                
                if len(drug_name) > 2:
                    products.append({
                        'generic_name': drug_name,
                        'daily_dose': float(dose),
                        'dose_units': unit
                    })
        
        return products
    
    def _extract_concomitant_medications(self, text: str) -> List[Dict[str, Any]]:
        """Extract concomitant medications"""
        medications = []
        concomitant_keywords = ['concomitant', 'concurrent', 'co-administered']
        
        for keyword in concomitant_keywords:
            if keyword in text.lower():
                pattern = rf'{keyword}[:\s]+([^.]+)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    med_text = match.group(1)
                    med_names = re.findall(r'\b[A-Z][a-z]+\b', med_text)
                    for med_name in med_names:
                        if len(med_name) > 2:
                            medications.append({'generic_name': med_name})
        
        return medications
    
    def _extract_event_description(self, text: str) -> Optional[str]:
        """Extract event description"""
        event_patterns = [
            r'adverse event[:\s]+([^.]+)',
            r'side effect[:\s]+([^.]+)',
            r'adverse reaction[:\s]+([^.]+)',
            r'event[:\s]+([^.]+)'
        ]
        
        for pattern in event_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_outcome(self, text: str) -> Optional[Outcome]:
        """Extract event outcome"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['fatal', 'death', 'died']):
            return Outcome.FATAL
        elif any(word in text_lower for word in ['recovered', 'resolved']):
            return Outcome.RECOVERED
        elif any(word in text_lower for word in ['recovering', 'improving']):
            return Outcome.RECOVERING
        return Outcome.UNKNOWN
    
    def _extract_seriousness_criteria(self, text: str) -> List[str]:
        """Extract seriousness criteria"""
        criteria = []
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['death', 'fatal', 'died']):
            criteria.append('Death')
        if any(word in text_lower for word in ['hospitalized', 'hospitalization']):
            criteria.append('Hospitalized/Prolonged hospitalization')
        if any(word in text_lower for word in ['disability', 'disabled']):
            criteria.append('Disability')
        if any(word in text_lower for word in ['life-threatening', 'life threatening']):
            criteria.append('Life-threatening')
        
        return criteria
