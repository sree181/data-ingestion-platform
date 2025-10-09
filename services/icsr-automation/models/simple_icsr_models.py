"""
Simplified ICSR Models for Testing
Basic Pydantic models to avoid recursion issues
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

# Basic Enums
class ReportType(str, Enum):
    LITERATURE = "Literature"
    SPONTANEOUS = "Spontaneous"
    CLINICAL_TRIAL = "Clinical trial"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"

class Outcome(str, Enum):
    UNKNOWN = "Unknown"
    FATAL = "Fatal"
    RECOVERING = "Recovering"
    RECOVERED = "Recovered"

# Basic ICSR Data Model
class ICSRData(BaseModel):
    report_id: str = Field(..., description="Unique identifier for the ICSR report")
    report_type: ReportType = Field(..., description="Type of report")
    country_of_occurrence: Optional[str] = None
    report_start_date: Optional[date] = None
    medically_confirmed: Optional[bool] = None
    narrative_summary: Optional[str] = None

# Request/Response Models
class EmailProcessingRequest(BaseModel):
    email_id: str
    subject: str
    body: str
    sender: str

class EmailProcessingResponse(BaseModel):
    success: bool
    classification: str
    confidence: float
    narrative: Optional[str] = None

class ICSRValidationRequest(BaseModel):
    icsr_id: str
    icsr_data: ICSRData

class ICSRValidationResponse(BaseModel):
    success: bool
    is_valid: bool
    validation_errors: List[str] = []

class XMLGenerationRequest(BaseModel):
    icsr_id: str
    icsr_data: ICSRData

class XMLGenerationResponse(BaseModel):
    success: bool
    xml_content: str
    file_name: str

class ICSRExtractionRequest(BaseModel):
    article_id: str
    title: str
    abstract: Optional[str] = None
    content: Optional[str] = None

class ICSRExtractionResponse(BaseModel):
    success: bool
    extracted_data: Dict[str, Any]
    confidence: float
    validation_errors: List[str] = []

