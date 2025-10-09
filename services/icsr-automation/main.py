"""
ICSR Automation Service
Handles email processing, ICSR extraction, and XML generation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog
from typing import List, Dict, Any
import uvicorn

from models.simple_icsr_models import (
    EmailProcessingRequest,
    EmailProcessingResponse,
    ICSRValidationRequest,
    ICSRValidationResponse,
    XMLGenerationRequest,
    XMLGenerationResponse,
    ICSRExtractionRequest,
    ICSRExtractionResponse
)
from services.email_processing_service import EmailProcessingService
from services.icsr_validation_service import ICSRValidationService
from services.xml_generation_service import XMLGenerationService
from services.icsr_extraction_service import ICSRExtractionService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="ICSR Automation Service",
    description="AI-powered ICSR processing from emails and literature",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
email_processing_service = EmailProcessingService()
icsr_validation_service = ICSRValidationService()
xml_generation_service = XMLGenerationService()
icsr_extraction_service = ICSRExtractionService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "icsr-automation"}

@app.post("/api/v1/icsr/process-email", response_model=EmailProcessingResponse)
async def process_email(request: EmailProcessingRequest):
    """Process safety email and extract ICSR data"""
    try:
        logger.info("Email processing request", email_id=request.email_id)
        
        result = await email_processing_service.process_email(
            email_id=request.email_id,
            subject=request.subject,
            body=request.body,
            attachments=request.attachments,
            sender=request.sender
        )
        
        logger.info("Email processing completed", 
                   email_id=request.email_id,
                   classification=result.classification)
        
        return EmailProcessingResponse(
            success=True,
            classification=result.classification,
            confidence=result.confidence,
            extracted_icsr_data=result.extracted_icsr_data,
            processing_errors=result.processing_errors
        )
        
    except Exception as e:
        logger.error("Email processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Email processing failed: {str(e)}")

@app.post("/api/v1/icsr/validate", response_model=ICSRValidationResponse)
async def validate_icsr(request: ICSRValidationRequest):
    """Validate ICSR data against business rules and ICH E2B R3 requirements"""
    try:
        logger.info("ICSR validation request", icsr_id=request.icsr_id)
        
        validation_result = await icsr_validation_service.validate_icsr(
            icsr_data=request.icsr_data,
            validation_rules=request.validation_rules
        )
        
        logger.info("ICSR validation completed", 
                   icsr_id=request.icsr_id,
                   is_valid=validation_result.is_valid)
        
        return ICSRValidationResponse(
            success=True,
            is_valid=validation_result.is_valid,
            validation_errors=validation_result.validation_errors,
            warnings=validation_result.warnings,
            recommendations=validation_result.recommendations
        )
        
    except Exception as e:
        logger.error("ICSR validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ICSR validation failed: {str(e)}")

@app.post("/api/v1/icsr/generate-xml", response_model=XMLGenerationResponse)
async def generate_xml(request: XMLGenerationRequest):
    """Generate ICH E2B R3 XML file from ICSR data"""
    try:
        logger.info("XML generation request", icsr_id=request.icsr_id)
        
        xml_result = await xml_generation_service.generate_ich_e2b_xml(
            icsr_data=request.icsr_data,
            format_version=request.format_version,
            include_attachments=request.include_attachments
        )
        
        logger.info("XML generation completed", 
                   icsr_id=request.icsr_id,
                   xml_size=len(xml_result.xml_content))
        
        return XMLGenerationResponse(
            success=True,
            xml_content=xml_result.xml_content,
            file_name=xml_result.file_name,
            validation_status=xml_result.validation_status
        )
        
    except Exception as e:
        logger.error("XML generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"XML generation failed: {str(e)}")

@app.post("/api/v1/icsr/extract", response_model=ICSRExtractionResponse)
async def extract_icsr_data(request: ICSRExtractionRequest):
    """Extract structured ICSR data from literature article"""
    try:
        logger.info("ICSR extraction request", article_id=request.article_id)
        
        icsr_data = await icsr_extraction_service.extract_icsr_data(
            title=request.title,
            abstract=request.abstract,
            content=request.content,
            article_metadata=request.article_metadata
        )
        
        logger.info("ICSR extraction completed", 
                   article_id=request.article_id,
                   extracted_fields=len(icsr_data.extracted_data))
        
        return ICSRExtractionResponse(
            success=True,
            extracted_data=icsr_data.extracted_data,
            confidence=icsr_data.confidence,
            validation_errors=icsr_data.validation_errors
        )
        
    except Exception as e:
        logger.error("ICSR extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ICSR extraction failed: {str(e)}")

@app.get("/api/v1/icsr/validation-rules")
async def get_validation_rules():
    """Get available ICSR validation rules"""
    return {
        "validation_rules": [
            {"id": "required_fields", "name": "Required Fields", "description": "Check for mandatory ICSR fields"},
            {"id": "data_format", "name": "Data Format", "description": "Validate data format and types"},
            {"id": "business_rules", "name": "Business Rules", "description": "Apply business-specific validation rules"},
            {"id": "ich_e2b_compliance", "name": "ICH E2B R3 Compliance", "description": "Ensure ICH E2B R3 compliance"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
