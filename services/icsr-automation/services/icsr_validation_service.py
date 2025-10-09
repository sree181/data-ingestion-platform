"""
ICSR Validation Service
Validates ICSR data against business rules and regulatory requirements
"""

import asyncio
from typing import Dict, Any, List
import structlog
from datetime import datetime, date

from models.simple_icsr_models import ICSRData, ICSRValidationResponse

logger = structlog.get_logger()

class ICSRValidationService:
    def __init__(self):
        self.required_fields = {
            'general_information': ['country', 'initial_receipt_date', 'medically_confirmed'],
            'event_information': ['description_as_reported'],
            'product_information': ['suspect_products']
        }
        
        self.validation_rules = {
            'required_fields': self._validate_required_fields,
            'data_format': self._validate_data_format,
            'business_rules': self._validate_business_rules,
            'ich_e2b_compliance': self._validate_ich_e2b_compliance
        }
    
    async def validate_icsr(
        self,
        icsr_data: ICSRData,
        validation_rules: List[str] = None
    ) -> ICSRValidationResponse:
        """
        Validate ICSR data using specified validation rules
        """
        logger.info("Starting ICSR validation", icsr_id=icsr_data.icsr_id)
        
        try:
            validation_errors = []
            warnings = []
            recommendations = []
            
            # Apply validation rules
            rules_to_apply = validation_rules or list(self.validation_rules.keys())
            
            for rule in rules_to_apply:
                if rule in self.validation_rules:
                    rule_errors, rule_warnings, rule_recommendations = await self.validation_rules[rule](icsr_data)
                    validation_errors.extend(rule_errors)
                    warnings.extend(rule_warnings)
                    recommendations.extend(rule_recommendations)
            
            # Determine overall validity
            is_valid = len(validation_errors) == 0
            
            logger.info("ICSR validation completed", 
                       icsr_id=icsr_data.icsr_id,
                       is_valid=is_valid,
                       errors=len(validation_errors),
                       warnings=len(warnings))
            
            return ICSRValidationResponse(
                success=True,
                is_valid=is_valid,
                validation_errors=validation_errors,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error("ICSR validation failed", error=str(e))
            return ICSRValidationResponse(
                success=False,
                is_valid=False,
                validation_errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                recommendations=[]
            )
    
    async def _validate_required_fields(self, icsr_data: ICSRData) -> tuple[List[str], List[str], List[str]]:
        """Validate required fields are present"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check general information
        if not icsr_data.general_information.country or icsr_data.general_information.country == "Unknown":
            errors.append("Country is required and must be specified")
        
        if not icsr_data.general_information.initial_receipt_date:
            errors.append("Initial receipt date is required")
        
        # Check event information
        if not icsr_data.event_information.description_as_reported:
            errors.append("Event description is required")
        
        # Check product information
        if not icsr_data.product_information.suspect_products:
            errors.append("At least one suspect product is required")
        
        # Check patient information (warnings only)
        if not icsr_data.patient_information.patient_details:
            warnings.append("Patient information is missing - consider adding if available")
        
        return errors, warnings, recommendations
    
    async def _validate_data_format(self, icsr_data: ICSRData) -> tuple[List[str], List[str], List[str]]:
        """Validate data format and types"""
        errors = []
        warnings = []
        recommendations = []
        
        # Validate dates
        if icsr_data.general_information.initial_receipt_date:
            if icsr_data.general_information.initial_receipt_date > datetime.now():
                errors.append("Initial receipt date cannot be in the future")
        
        # Validate patient age
        if icsr_data.patient_information.patient_details:
            age = icsr_data.patient_information.patient_details.get('age')
            if age is not None:
                if not isinstance(age, int) or age < 0 or age > 150:
                    errors.append("Patient age must be a valid integer between 0 and 150")
        
        # Validate email format
        if icsr_data.general_information.reporter_information:
            email = icsr_data.general_information.reporter_information.get('email_address')
            if email and '@' not in email:
                errors.append("Reporter email address format is invalid")
        
        # Validate product information
        for product in icsr_data.product_information.suspect_products:
            if product.get('daily_dose') is not None:
                try:
                    dose = float(product['daily_dose'])
                    if dose <= 0:
                        errors.append("Product daily dose must be greater than 0")
                except (ValueError, TypeError):
                    errors.append("Product daily dose must be a valid number")
        
        return errors, warnings, recommendations
    
    async def _validate_business_rules(self, icsr_data: ICSRData) -> tuple[List[str], List[str], List[str]]:
        """Validate business-specific rules"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check for duplicate products
        product_names = [p.get('generic_name', '') for p in icsr_data.product_information.suspect_products]
        if len(product_names) != len(set(product_names)):
            warnings.append("Duplicate suspect products detected")
        
        # Check for serious events without proper documentation
        if icsr_data.event_information.seriousness_criteria:
            if not icsr_data.event_information.medical_confirmation_by_hcp:
                warnings.append("Serious event should be medically confirmed by healthcare professional")
        
        # Check for missing outcome information
        if not icsr_data.event_information.outcome:
            recommendations.append("Consider adding event outcome information if available")
        
        # Check for missing patient demographics
        if icsr_data.patient_information.patient_details:
            if not icsr_data.patient_information.patient_details.get('gender'):
                recommendations.append("Patient gender information is recommended")
            if not icsr_data.patient_information.patient_details.get('age'):
                recommendations.append("Patient age information is recommended")
        
        return errors, warnings, recommendations
    
    async def _validate_ich_e2b_compliance(self, icsr_data: ICSRData) -> tuple[List[str], List[str], List[str]]:
        """Validate ICH E2B R3 compliance"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check for required ICH E2B fields
        if not icsr_data.general_information.country:
            errors.append("Country is required for ICH E2B compliance")
        
        if not icsr_data.event_information.description_as_reported:
            errors.append("Event description is required for ICH E2B compliance")
        
        if not icsr_data.product_information.suspect_products:
            errors.append("Suspect product information is required for ICH E2B compliance")
        
        # Check for MedDRA coding
        if not icsr_data.event_information.preferred_term:
            warnings.append("MedDRA preferred term is recommended for ICH E2B compliance")
        
        # Check for reporter information
        if not icsr_data.general_information.reporter_information:
            warnings.append("Reporter information is recommended for ICH E2B compliance")
        
        # Check for patient information
        if not icsr_data.patient_information.patient_details:
            warnings.append("Patient information is recommended for ICH E2B compliance")
        
        # Check for seriousness criteria
        if not icsr_data.event_information.seriousness_criteria:
            recommendations.append("Seriousness criteria should be specified if applicable")
        
        return errors, warnings, recommendations
