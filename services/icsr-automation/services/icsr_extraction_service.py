"""
ICSR Extraction Service
AI-powered extraction of structured ICSR data from literature articles
Based on Appendix-01 detailed data extraction scope
"""

import asyncio
import json
import re
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime, date
import spacy

from models.simple_icsr_models import (
    ICSRExtractionResponse, ICSRData, ReportType, Gender, Outcome
)

logger = structlog.get_logger()

class ICSRExtractionService:
    def __init__(self):
        self.nlp = None
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP model"""
        try:
            # Load English model for medical text processing
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy NLP model initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize spaCy model", error=str(e))
            # Try to download the model
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model downloaded and initialized")
            except Exception as e2:
                logger.error("Failed to download spaCy model", error=str(e2))
                self.nlp = None
    
    async def extract_icsr_data(
        self,
        title: str,
        abstract: Optional[str],
        content: str,
        article_metadata: Optional[Dict[str, Any]] = None
    ) -> ICSRExtractionResponse:
        """
        Extract structured ICSR data from literature article
        """
        logger.info("Starting ICSR data extraction", title=title[:100])
        
        try:
            # Prepare text for extraction
            full_text = self._prepare_text_for_extraction(title, abstract, content)
            
            # Extract different sections of ICSR data
            general_info = await self._extract_general_information(full_text, article_metadata)
            patient_info = await self._extract_patient_information(full_text)
            product_info = await self._extract_product_information(full_text)
            event_info = await self._extract_event_information(full_text)
            
            # Create ICSR data object
            icsr_data = ICSRData(
                icsr_id=f"LIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                general_information=general_info,
                patient_information=patient_info,
                product_information=product_info,
                event_information=event_info
            )
            
            # Validate extracted data
            validation_errors = await self._validate_icsr_data(icsr_data)
            
            # Calculate confidence score
            confidence = self._calculate_extraction_confidence(icsr_data)
            
            logger.info("ICSR data extraction completed", 
                       icsr_id=icsr_data.icsr_id,
                       confidence=confidence,
                       validation_errors=len(validation_errors))
            
            return ICSRExtractionResponse(
                success=True,
                extracted_data=icsr_data.dict(),
                confidence=confidence,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            logger.error("ICSR data extraction failed", error=str(e))
            return ICSRExtractionResponse(
                success=False,
                extracted_data={},
                confidence=0.0,
                validation_errors=[f"Extraction failed: {str(e)}"]
            )
    
    def _prepare_text_for_extraction(self, title: str, abstract: Optional[str], content: str) -> str:
        """Prepare text for extraction by combining all available content"""
        text_parts = []
        
        if title:
            text_parts.append(f"Title: {title}")
        
        if abstract:
            text_parts.append(f"Abstract: {abstract}")
        
        if content:
            text_parts.append(f"Content: {content}")
        
        return "\n\n".join(text_parts)
    
    async def _extract_general_information(self, text: str, metadata: Optional[Dict[str, Any]]) -> GeneralInformation:
        """Extract general information section"""
        try:
            # Extract report type (default to Literature for literature articles)
            report_type = ReportType.LITERATURE
            
            # Extract country (try to find from text or metadata)
            country = self._extract_country(text, metadata)
            
            # Extract dates
            initial_receipt_date = datetime.now()
            if metadata and 'publication_date' in metadata:
                try:
                    initial_receipt_date = datetime.fromisoformat(metadata['publication_date'].replace('Z', '+00:00'))
                except:
                    pass
            
            # Determine if medically confirmed (look for healthcare professional indicators)
            medically_confirmed = self._is_medically_confirmed(text)
            
            # Extract literature information
            literature_info = self._extract_literature_information(text, metadata)
            
            return GeneralInformation(
                report_type=report_type,
                country=country,
                initial_receipt_date=initial_receipt_date,
                medically_confirmed=medically_confirmed,
                literature_information=literature_info
            )
            
        except Exception as e:
            logger.error("Failed to extract general information", error=str(e))
            return GeneralInformation(
                report_type=ReportType.LITERATURE,
                country="Unknown",
                initial_receipt_date=datetime.now(),
                medically_confirmed=False
            )
    
    async def _extract_patient_information(self, text: str) -> PatientInformation:
        """Extract patient information section"""
        try:
            # Extract patient demographics
            gender = self._extract_gender(text)
            age = self._extract_age(text)
            age_unit = self._extract_age_unit(text)
            
            # Extract medical history and conditions
            medical_history = self._extract_medical_history(text)
            
            # Extract lab data
            lab_data = self._extract_lab_data(text)
            
            return PatientInformation(
                patient_details={
                    'gender': gender,
                    'age': age,
                    'age_unit': age_unit,
                    'race': self._extract_race(text)
                },
                other_relevant_history={
                    'medical_history': medical_history,
                    'current_condition': self._extract_current_condition(text)
                },
                lab_data=lab_data
            )
            
        except Exception as e:
            logger.error("Failed to extract patient information", error=str(e))
            return PatientInformation()
    
    async def _extract_product_information(self, text: str) -> ProductInformation:
        """Extract product information section"""
        try:
            # Extract suspect products
            suspect_products = self._extract_suspect_products(text)
            
            # Extract concomitant medications
            concomitant_medications = self._extract_concomitant_medications(text)
            
            return ProductInformation(
                suspect_products=suspect_products,
                concomitant_medications=concomitant_medications
            )
            
        except Exception as e:
            logger.error("Failed to extract product information", error=str(e))
            return ProductInformation()
    
    async def _extract_event_information(self, text: str) -> EventInformation:
        """Extract event information section"""
        try:
            # Extract event description
            description = self._extract_event_description(text)
            
            # Extract MedDRA coding
            preferred_term, lower_level_term = self._extract_meddra_coding(text)
            
            # Extract dates
            onset_date = self._extract_onset_date(text)
            end_date = self._extract_end_date(text)
            
            # Extract outcome
            outcome = self._extract_outcome(text)
            
            # Extract seriousness criteria
            seriousness_criteria = self._extract_seriousness_criteria(text)
            
            return EventInformation(
                description_as_reported=description,
                preferred_term=preferred_term,
                lower_level_term=lower_level_term,
                onset_date=onset_date,
                end_date=end_date,
                outcome=outcome,
                seriousness_criteria=seriousness_criteria
            )
            
        except Exception as e:
            logger.error("Failed to extract event information", error=str(e))
            return EventInformation()
    
    def _extract_country(self, text: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Extract country from text or metadata"""
        # Try metadata first
        if metadata and 'country' in metadata:
            return metadata['country']
        
        # Look for country patterns in text
        country_patterns = [
            r'country[:\s]+([A-Za-z\s]+)',
            r'from\s+([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s+study',
            r'([A-Za-z\s]+)\s+patients'
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                if len(country) > 2 and len(country) < 50:  # Reasonable country name length
                    return country
        
        return "Unknown"
    
    def _is_medically_confirmed(self, text: str) -> bool:
        """Determine if case is medically confirmed"""
        hcp_indicators = [
            'physician', 'doctor', 'nurse', 'pharmacist', 'healthcare professional',
            'hcp', 'medical professional', 'clinician', 'practitioner'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in hcp_indicators)
    
    def _extract_literature_information(self, text: str, metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract literature information"""
        if not metadata:
            return None
        
        return {
            'author': metadata.get('authors', [''])[0] if metadata.get('authors') else None,
            'title': metadata.get('title'),
            'journal': metadata.get('journal'),
            'year_of_publication': metadata.get('publication_date', '').split('-')[0] if metadata.get('publication_date') else None,
            'doi': metadata.get('doi')
        }
    
    def _extract_gender(self, text: str) -> Optional[Gender]:
        """Extract patient gender"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['male', 'man', 'men', 'boy', 'boys']):
            return Gender.MALE
        elif any(word in text_lower for word in ['female', 'woman', 'women', 'girl', 'girls']):
            return Gender.FEMALE
        else:
            return Gender.UNKNOWN
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract patient age"""
        age_patterns = [
            r'age[:\s]+(\d+)',
            r'(\d+)\s*years?\s*old',
            r'(\d+)\s*year-old',
            r'aged\s+(\d+)'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    age = int(match.group(1))
                    if 0 <= age <= 150:  # Reasonable age range
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
        elif any(word in text_lower for word in ['years', 'year-old']):
            return AgeUnit.YEARS
        else:
            return AgeUnit.YEARS  # Default to years
    
    def _extract_race(self, text: str) -> Optional[str]:
        """Extract race information"""
        race_patterns = [
            r'race[:\s]+([A-Za-z\s]+)',
            r'ethnicity[:\s]+([A-Za-z\s]+)',
            r'(caucasian|asian|black|white|hispanic|latino)'
        ]
        
        for pattern in race_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_medical_history(self, text: str) -> Optional[str]:
        """Extract medical history"""
        history_patterns = [
            r'medical history[:\s]+([^.]+)',
            r'past history[:\s]+([^.]+)',
            r'previous history[:\s]+([^.]+)',
            r'history of[:\s]+([^.]+)'
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_current_condition(self, text: str) -> Optional[str]:
        """Extract current condition"""
        condition_patterns = [
            r'current condition[:\s]+([^.]+)',
            r'presenting with[:\s]+([^.]+)',
            r'diagnosed with[:\s]+([^.]+)',
            r'suffering from[:\s]+([^.]+)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_lab_data(self, text: str) -> List[Dict[str, Any]]:
        """Extract lab data"""
        lab_data = []
        
        # Look for lab values
        lab_patterns = [
            r'(\w+)[:\s]+(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?',
            r'(\w+)\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?'
        ]
        
        for pattern in lab_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                test_name = match.group(1).strip()
                result_value = match.group(2)
                unit = match.group(3) if match.group(3) else None
                
                if len(test_name) > 2 and len(test_name) < 50:  # Reasonable test name length
                    lab_data.append({
                        'test_name': test_name,
                        'result_value': float(result_value),
                        'lab_unit': unit
                    })
        
        return lab_data
    
    def _extract_suspect_products(self, text: str) -> List[Dict[str, Any]]:
        """Extract suspect products"""
        products = []
        
        # Look for drug names and dosages
        drug_patterns = [
            r'(\w+)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg)',
            r'(\w+)\s+(\d+(?:\.\d+)?)\s*(mg/kg|ml/kg)',
            r'(\w+)\s+(\d+(?:\.\d+)?)\s*(mg/day|ml/day)'
        ]
        
        for pattern in drug_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                drug_name = match.group(1).strip()
                dose = match.group(2)
                unit = match.group(3)
                
                if len(drug_name) > 2 and len(drug_name) < 50:
                    products.append({
                        'generic_name': drug_name,
                        'daily_dose': float(dose),
                        'dose_units': unit
                    })
        
        return products
    
    def _extract_concomitant_medications(self, text: str) -> List[Dict[str, Any]]:
        """Extract concomitant medications"""
        # Similar to suspect products but look for specific keywords
        concomitant_keywords = ['concomitant', 'concurrent', 'co-administered', 'along with']
        
        medications = []
        for keyword in concomitant_keywords:
            if keyword in text.lower():
                # Extract medications mentioned after this keyword
                pattern = rf'{keyword}[:\s]+([^.]+)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    med_text = match.group(1)
                    # Extract individual medications
                    med_names = re.findall(r'\b[A-Z][a-z]+\b', med_text)
                    for med_name in med_names:
                        if len(med_name) > 2:
                            medications.append({
                                'generic_name': med_name
                            })
        
        return medications
    
    def _extract_event_description(self, text: str) -> Optional[str]:
        """Extract event description"""
        event_patterns = [
            r'adverse event[:\s]+([^.]+)',
            r'side effect[:\s]+([^.]+)',
            r'adverse reaction[:\s]+([^.]+)',
            r'event[:\s]+([^.]+)',
            r'reaction[:\s]+([^.]+)'
        ]
        
        for pattern in event_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_meddra_coding(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract MedDRA coding (placeholder - would need MedDRA API)"""
        # This would typically involve MedDRA API integration
        return None, None
    
    def _extract_onset_date(self, text: str) -> Optional[datetime]:
        """Extract onset date"""
        date_patterns = [
            r'onset[:\s]+(\d{4}-\d{2}-\d{2})',
            r'started[:\s]+(\d{4}-\d{2}-\d{2})',
            r'began[:\s]+(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.fromisoformat(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_end_date(self, text: str) -> Optional[datetime]:
        """Extract end date"""
        date_patterns = [
            r'ended[:\s]+(\d{4}-\d{2}-\d{2})',
            r'stopped[:\s]+(\d{4}-\d{2}-\d{2})',
            r'resolved[:\s]+(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.fromisoformat(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_outcome(self, text: str) -> Optional[Outcome]:
        """Extract event outcome"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['fatal', 'death', 'died', 'deceased']):
            return Outcome.FATAL
        elif any(word in text_lower for word in ['recovered', 'resolved', 'healed']):
            return Outcome.RECOVERED
        elif any(word in text_lower for word in ['recovering', 'improving']):
            return Outcome.RECOVERING
        elif any(word in text_lower for word in ['not recovered', 'ongoing', 'persistent']):
            return Outcome.NOT_RECOVERED
        else:
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
        if any(word in text_lower for word in ['congenital', 'birth defect']):
            criteria.append('Congenital Anomaly')
        
        return criteria
    
    async def _validate_icsr_data(self, icsr_data: ICSRData) -> List[str]:
        """Validate extracted ICSR data"""
        errors = []
        
        # Check required fields
        if not icsr_data.general_information.country:
            errors.append("Country is required")
        
        if not icsr_data.event_information.description_as_reported:
            errors.append("Event description is required")
        
        if not icsr_data.product_information.suspect_products:
            errors.append("At least one suspect product is required")
        
        return errors
    
    def _calculate_extraction_confidence(self, icsr_data: ICSRData) -> float:
        """Calculate confidence score for extraction"""
        score = 0.0
        total_fields = 0
        
        # Check general information
        if icsr_data.general_information.country:
            score += 1
        total_fields += 1
        
        # Check patient information
        if icsr_data.patient_information.patient_details:
            if icsr_data.patient_information.patient_details.get('gender'):
                score += 1
            if icsr_data.patient_information.patient_details.get('age'):
                score += 1
        total_fields += 2
        
        # Check product information
        if icsr_data.product_information.suspect_products:
            score += 1
        total_fields += 1
        
        # Check event information
        if icsr_data.event_information.description_as_reported:
            score += 1
        if icsr_data.event_information.outcome:
            score += 1
        total_fields += 2
        
        return score / total_fields if total_fields > 0 else 0.0
