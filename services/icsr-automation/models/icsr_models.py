"""
ICSR Automation Data Models
Pydantic models for ICSR data extraction, validation, and XML generation
Based on Appendix-01 detailed data extraction scope
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

# Enums for ICSR data validation
class ReportType(str, Enum):
    LITERATURE = "Literature"
    SPONTANEOUS = "Spontaneous"
    CLINICAL_TRIAL = "Clinical trial"
    REGULATORY_AUTHORITY = "Regulatory Authority"
    LEGAL_CASE = "Legal Case"
    SOLICITED = "Solicited"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"

class AgeUnit(str, Enum):
    DAYS = "Days"
    WEEKS = "Weeks"
    MONTHS = "Months"
    YEARS = "Years"
    DECADES = "Decades"

class Outcome(str, Enum):
    UNKNOWN = "Unknown"
    FATAL = "Fatal"
    RECOVERING = "Recovering"
    NOT_RECOVERED = "Not Recovered"
    RECOVERED = "Recovered"
    RECOVERED_WITH_SEQUELAE = "Recovered with Sequelae"

class SeriousnessCriteria(str, Enum):
    DEATH = "Death"
    HOSPITALIZED = "Hospitalized/Prolonged hospitalization"
    DISABILITY = "Disability"
    MEDICALLY_SIGNIFICANT = "Medically Significant"
    LIFE_THREATENING = "Life-threatening"
    CONGENITAL_ANOMALY = "Congenital Anomaly"

class ActionTaken(str, Enum):
    UNKNOWN = "Unknown"
    DOSE_DECREASED = "Dose Decreased"
    DOSE_INCREASED = "Dose Increased"
    TEMPORARY_WITHDRAWAL = "Temporary Withdrawal"
    PERMANENTLY_DISCONTINUED = "Permanently Discontinued"
    DOSE_NOT_CHANGED = "Dose Not Changed"
    NOT_APPLICABLE = "Not Applicable"

# General Information Models
class StudyInformation(BaseModel):
    study_id: Optional[str] = Field(None, description="Study identifier")
    study_title: Optional[str] = Field(None, description="Study title")
    study_type: Optional[str] = Field(None, description="Study type")
    protocol_number: Optional[str] = Field(None, description="Protocol number")

class ReporterInformation(BaseModel):
    first_name: Optional[str] = Field(None, description="Reporter first name")
    middle_name: Optional[str] = Field(None, description="Reporter middle name")
    last_name: Optional[str] = Field(None, description="Reporter last name")
    country: Optional[str] = Field(None, description="Reporter country")
    postal_address: Optional[str] = Field(None, description="Reporter postal address")
    city: Optional[str] = Field(None, description="Reporter city")
    state: Optional[str] = Field(None, description="Reporter state")
    postal_code: Optional[str] = Field(None, description="Reporter postal code")
    healthcare_professional: Optional[bool] = Field(None, description="Is healthcare professional")
    institution: Optional[str] = Field(None, description="Institution name")
    institution_id: Optional[str] = Field(None, description="Institution ID")
    primary_reporter: Optional[bool] = Field(None, description="Is primary reporter")
    occupation: Optional[str] = Field(None, description="Reporter occupation")
    phone_number: Optional[str] = Field(None, description="Phone number")
    email_address: Optional[str] = Field(None, description="Email address")

class LiteratureInformation(BaseModel):
    author: Optional[str] = Field(None, description="Article author")
    title: Optional[str] = Field(None, description="Article title")
    journal: Optional[str] = Field(None, description="Journal name")
    year_of_publication: Optional[int] = Field(None, description="Year of publication")
    volume: Optional[str] = Field(None, description="Journal volume")
    pages: Optional[str] = Field(None, description="Page numbers")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")

class GeneralInformation(BaseModel):
    report_type: ReportType = Field(..., description="Type of report")
    country: str = Field(..., description="Country of incidence")
    initial_receipt_date: datetime = Field(..., description="Initial receipt date (Day 0)")
    follow_up_receipt_date: Optional[datetime] = Field(None, description="Follow up receipt date")
    medically_confirmed: bool = Field(..., description="Medically confirmed (Yes/No)")
    study_information: Optional[StudyInformation] = Field(None, description="Study information")
    reporter_information: Optional[ReporterInformation] = Field(None, description="Reporter information")
    literature_information: Optional[LiteratureInformation] = Field(None, description="Literature information")

# Patient Information Models
class PatientDetails(BaseModel):
    gender: Optional[Gender] = Field(None, description="Patient gender")
    gender_at_birth: Optional[Gender] = Field(None, description="Gender at birth")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    age: Optional[int] = Field(None, description="Patient age")
    age_group: Optional[str] = Field(None, description="Age group (adolescent, adult, elderly)")
    age_unit: Optional[AgeUnit] = Field(None, description="Age unit")
    height: Optional[float] = Field(None, description="Height")
    height_unit: Optional[str] = Field(None, description="Height unit (cm/in)")
    weight: Optional[float] = Field(None, description="Weight")
    weight_unit: Optional[str] = Field(None, description="Weight unit (kgs/lbs)")
    pregnant: Optional[bool] = Field(None, description="Is pregnant (female patients)")
    last_menstrual_period: Optional[date] = Field(None, description="Date of last menstrual period")
    breastfeeding: Optional[bool] = Field(None, description="Is breastfeeding (female patients)")
    race: Optional[str] = Field(None, description="Race information")

class EventDeathDetails(BaseModel):
    cause_of_death: Optional[str] = Field(None, description="Cause of death")
    autopsy_result: Optional[str] = Field(None, description="Autopsy result")
    date_of_death: Optional[date] = Field(None, description="Date of death")

class OtherRelevantHistory(BaseModel):
    current_condition: Optional[str] = Field(None, description="Current condition")
    historical_condition: Optional[str] = Field(None, description="Historical condition")
    medical_history: Optional[str] = Field(None, description="Medical history")
    relevant_family_history: Optional[str] = Field(None, description="Relevant family history")
    procedure: Optional[str] = Field(None, description="Procedure")
    past_drug: Optional[str] = Field(None, description="Past drug history")

class LabData(BaseModel):
    test_name: Optional[str] = Field(None, description="Lab test name")
    date: Optional[date] = Field(None, description="Lab test date")
    result: Optional[str] = Field(None, description="Lab result")
    result_value: Optional[float] = Field(None, description="Lab result value")
    result_status: Optional[str] = Field(None, description="Normal/High/Low/Unknown")
    lab_unit: Optional[str] = Field(None, description="Lab unit")

class PatientInformation(BaseModel):
    unique_identifier: Optional[str] = Field(None, description="Patient unique identifier/initials")
    state: Optional[str] = Field(None, description="Patient state")
    postal_code: Optional[str] = Field(None, description="Patient postal code")
    email_address: Optional[str] = Field(None, description="Patient email address")
    patient_details: Optional[PatientDetails] = Field(None, description="Patient details")
    event_death_details: Optional[EventDeathDetails] = Field(None, description="Event death details")
    other_relevant_history: Optional[OtherRelevantHistory] = Field(None, description="Other relevant history")
    lab_data: List[LabData] = Field(default=[], description="Lab data")

# Product Information Models
class SuspectProduct(BaseModel):
    brand_name: Optional[str] = Field(None, description="Brand name")
    generic_name: Optional[str] = Field(None, description="Generic name")
    marketing_authorization_number: Optional[str] = Field(None, description="Marketing authorization number")
    indication: Optional[str] = Field(None, description="Indication for use")
    obtain_drug_country: Optional[str] = Field(None, description="Country where drug was obtained")
    drug_authorization_country: Optional[str] = Field(None, description="Country of drug authorization")
    daily_dose: Optional[float] = Field(None, description="Daily dose")
    dose_units: Optional[str] = Field(None, description="Dose units (mg, ml, mg/kg)")
    regimen: Optional[str] = Field(None, description="Dosage regimen")
    dosage_form: Optional[str] = Field(None, description="Dosage form")
    strength: Optional[float] = Field(None, description="Strength")
    strength_units: Optional[str] = Field(None, description="Strength units")
    route_of_administration: Optional[str] = Field(None, description="Route of administration")
    duration: Optional[str] = Field(None, description="Duration of regimen")
    start_date: Optional[datetime] = Field(None, description="Start date and time")
    stop_date: Optional[datetime] = Field(None, description="Stop date and time")
    batch_lot_number: Optional[str] = Field(None, description="Batch/lot number")
    action_taken: Optional[ActionTaken] = Field(None, description="Action taken")
    dechallenge: Optional[str] = Field(None, description="Dechallenge information")
    rechallenge: Optional[str] = Field(None, description="Rechallenge information")
    additional_information: Optional[Dict[str, bool]] = Field(None, description="Additional drug information flags")

class ConcomitantMedication(BaseModel):
    brand_name: Optional[str] = Field(None, description="Brand name")
    generic_name: Optional[str] = Field(None, description="Generic name")
    indication: Optional[str] = Field(None, description="Indication for use")
    obtain_drug_country: Optional[str] = Field(None, description="Country where drug was obtained")
    drug_authorization_country: Optional[str] = Field(None, description="Country of drug authorization")
    dosage_form: Optional[str] = Field(None, description="Dosage form")
    dose: Optional[float] = Field(None, description="Dose")
    strength: Optional[float] = Field(None, description="Strength")
    strength_units: Optional[str] = Field(None, description="Strength units")
    frequency: Optional[str] = Field(None, description="Frequency")
    route_of_administration: Optional[str] = Field(None, description="Route of administration")
    start_date: Optional[datetime] = Field(None, description="Start date and time")
    stop_date: Optional[datetime] = Field(None, description="Stop date and time")
    batch_lot_number: Optional[str] = Field(None, description="Batch/lot number")

class ProductInformation(BaseModel):
    suspect_products: List[SuspectProduct] = Field(default=[], description="Suspect products")
    concomitant_medications: List[ConcomitantMedication] = Field(default=[], description="Concomitant medications")

# Event Information Models
class EventInformation(BaseModel):
    description_as_reported: Optional[str] = Field(None, description="Event description as reported")
    preferred_term: Optional[str] = Field(None, description="MedDRA preferred term")
    lower_level_term: Optional[str] = Field(None, description="MedDRA lower level term")
    onset_date: Optional[datetime] = Field(None, description="Onset date/time")
    end_date: Optional[datetime] = Field(None, description="End date/time")
    outcome: Optional[Outcome] = Field(None, description="Outcome of event")
    medical_confirmation_by_hcp: Optional[bool] = Field(None, description="Medical confirmation by HCP")
    seriousness_criteria: List[SeriousnessCriteria] = Field(default=[], description="Seriousness criteria")
    event_assessment: Optional[str] = Field(None, description="Event assessment (Listedness)")
    action_taken: Optional[ActionTaken] = Field(None, description="Action taken")
    dechallenge_results: Optional[str] = Field(None, description="Dechallenge results")
    rechallenge_results: Optional[str] = Field(None, description="Rechallenge results")
    lack_of_efficacy: Optional[bool] = Field(None, description="Lack of efficacy")
    progression_of_disease: Optional[bool] = Field(None, description="Progression of disease")
    infection: Optional[bool] = Field(None, description="Infection")
    emergency_room_visit: Optional[bool] = Field(None, description="Emergency room visit (not hospitalized)")
    adverse_drug_withdrawal_reaction: Optional[bool] = Field(None, description="Adverse drug withdrawal reaction")

# Analysis and Additional Information
class Analysis(BaseModel):
    case_summary: Optional[str] = Field(None, description="Complete case summary")
    narrative: Optional[str] = Field(None, description="AI-generated narrative")

class AdditionalInformation(BaseModel):
    reference_id: Optional[str] = Field(None, description="Reference ID (PubMed ID, WWID, partner reference)")
    source_document_attachments: List[str] = Field(default=[], description="Source document attachments")

# Main ICSR Data Model
class ICSRData(BaseModel):
    icsr_id: str = Field(..., description="Unique ICSR identifier")
    general_information: GeneralInformation = Field(..., description="General information")
    patient_information: PatientInformation = Field(..., description="Patient information")
    product_information: ProductInformation = Field(..., description="Product information")
    event_information: EventInformation = Field(..., description="Event information")
    analysis: Optional[Analysis] = Field(None, description="Analysis and narrative")
    additional_information: Optional[AdditionalInformation] = Field(None, description="Additional information")
    created_date: datetime = Field(default_factory=datetime.now, description="ICSR creation date")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last updated date")
    status: str = Field(default="draft", description="ICSR status")

# Request/Response Models for API
class EmailProcessingRequest(BaseModel):
    email_id: str = Field(..., description="Email identifier")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    attachments: List[Dict[str, Any]] = Field(default=[], description="Email attachments")
    sender: str = Field(..., description="Email sender")

class EmailProcessingResponse(BaseModel):
    success: bool = Field(..., description="Processing success status")
    classification: str = Field(..., description="Email classification (Valid/Invalid/Rejection/Irrelevant)")
    confidence: float = Field(..., description="Classification confidence")
    extracted_icsr_data: Optional[ICSRData] = Field(None, description="Extracted ICSR data")
    processing_errors: List[str] = Field(default=[], description="Processing errors")

class ICSRValidationRequest(BaseModel):
    icsr_id: str = Field(..., description="ICSR identifier")
    icsr_data: ICSRData = Field(..., description="ICSR data to validate")
    validation_rules: List[str] = Field(default=[], description="Validation rules to apply")

class ICSRValidationResponse(BaseModel):
    success: bool = Field(..., description="Validation success status")
    is_valid: bool = Field(..., description="ICSR data validity")
    validation_errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    recommendations: List[str] = Field(default=[], description="Recommendations")

class XMLGenerationRequest(BaseModel):
    icsr_id: str = Field(..., description="ICSR identifier")
    icsr_data: ICSRData = Field(..., description="ICSR data for XML generation")
    format_version: str = Field(default="R3", description="ICH E2B format version (R2/R3)")
    include_attachments: bool = Field(default=True, description="Include attachments in XML")

class XMLGenerationResponse(BaseModel):
    success: bool = Field(..., description="XML generation success status")
    xml_content: str = Field(..., description="Generated XML content")
    file_name: str = Field(..., description="Generated XML file name")
    validation_status: str = Field(..., description="XML validation status")

