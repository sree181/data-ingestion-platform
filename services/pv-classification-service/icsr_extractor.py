"""
ICSR Data Extraction Service
Extracts comprehensive ICSR data from classified literature using OpenAI GPT-4
"""
import os
import json
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


# Pydantic models for structured extraction
class ReporterInfo(BaseModel):
    """Reporter information"""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    is_hcp: Optional[bool] = None
    institution: Optional[str] = None
    institution_id: Optional[str] = None
    is_primary_reporter: Optional[bool] = None
    occupation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class LiteratureInfo(BaseModel):
    """Literature source information"""
    author: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pubmed_id: Optional[str] = None


class PatientInfo(BaseModel):
    """Patient demographics and details"""
    initials: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    age_unit: Optional[str] = None
    age_group: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    is_pregnant: Optional[bool] = None
    is_breastfeeding: Optional[bool] = None
    race: Optional[str] = None
    medical_history: Optional[str] = None
    relevant_history: Optional[str] = None


class DeathDetails(BaseModel):
    """Death information if applicable"""
    cause_of_death: Optional[str] = None
    autopsy_result: Optional[str] = None
    date_of_death: Optional[str] = None


class LabData(BaseModel):
    """Laboratory test data"""
    test_name: str
    date: Optional[str] = None
    result_value: Optional[str] = None
    result_status: Optional[str] = None  # Normal, High, Low, Unknown
    unit: Optional[str] = None


class ProductInfo(BaseModel):
    """Suspect or concomitant product information"""
    product_type: str  # Suspect or Concomitant
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    indication: Optional[str] = None
    country: Optional[str] = None
    dosage_form: Optional[str] = None
    dose: Optional[str] = None
    strength: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    batch_number: Optional[str] = None
    action_taken: Optional[str] = None
    dechallenge: Optional[str] = None
    rechallenge: Optional[str] = None
    additional_info: List[str] = []  # Abuse, Overdose, Off-label, etc.


class EventInfo(BaseModel):
    """Adverse event information"""
    description: str
    meddra_pt: Optional[str] = None
    meddra_llt: Optional[str] = None
    onset_date: Optional[str] = None
    end_date: Optional[str] = None
    outcome: Optional[str] = None
    is_medically_confirmed: Optional[bool] = None
    seriousness_criteria: List[str] = []  # Death, Hospitalization, etc.
    is_listed: Optional[bool] = None
    action_taken: Optional[str] = None
    dechallenge_result: Optional[str] = None
    rechallenge_result: Optional[str] = None


class ICSRData(BaseModel):
    """Complete ICSR extracted data"""
    # General Information
    report_type: str = "Literature"
    country_of_incidence: Optional[str] = None
    initial_receipt_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    is_medically_confirmed: Optional[bool] = None
    
    # Reporter
    reporter: Optional[ReporterInfo] = None
    
    # Literature
    literature: Optional[LiteratureInfo] = None
    
    # Patient
    patient: Optional[PatientInfo] = None
    death_details: Optional[DeathDetails] = None
    lab_data: List[LabData] = []
    
    # Products
    suspect_products: List[ProductInfo] = []
    concomitant_products: List[ProductInfo] = []
    
    # Events
    events: List[EventInfo] = []
    
    # Analysis
    case_narrative: Optional[str] = None
    
    # Additional
    reference_id: Optional[str] = None
    
    # Metadata
    extraction_date: str
    extraction_confidence: float


class ICSRExtractor:
    """
    Extracts comprehensive ICSR data from literature using OpenAI GPT-4
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.model = "gpt-4o"  # Using GPT-4o for complex extraction
        logger.info("ICSR Extractor initialized", model=self.model)
    
    async def extract_icsr_data(
        self,
        title: str,
        abstract: str,
        full_text: Optional[str] = None,
        pmid: Optional[str] = None,
        doi: Optional[str] = None
    ) -> ICSRData:
        """
        Extract comprehensive ICSR data from literature
        
        Args:
            title: Article title
            abstract: Article abstract
            full_text: Full article text if available
            pmid: PubMed ID
            doi: Digital Object Identifier
            
        Returns:
            ICSRData with all extracted fields
        """
        try:
            logger.info("Extracting ICSR data", pmid=pmid, title=title[:100])
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(title, abstract, full_text)
            
            # Call OpenAI with structured output
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert pharmacovigilance data extractor specializing in ICSR (Individual Case Safety Report) data extraction from medical literature.

Your task is to extract ALL relevant ICSR data fields according to ICH E2B guidelines and regulatory standards (FDA, EMA).

Extract data ONLY if explicitly stated or strongly implied in the text. Use null for missing data. Be precise and conservative.

Return ONLY valid JSON matching the exact schema provided."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=4000
            )
            
            # Parse response
            extracted_json = json.loads(response.choices[0].message.content)
            
            # Add metadata
            extracted_json["extraction_date"] = datetime.utcnow().isoformat()
            extracted_json["extraction_confidence"] = 0.85  # Can be refined based on completeness
            
            # Add literature info if available
            if not extracted_json.get("literature"):
                extracted_json["literature"] = {}
            extracted_json["literature"]["pubmed_id"] = pmid
            extracted_json["literature"]["doi"] = doi
            extracted_json["literature"]["title"] = title
            
            # Convert to Pydantic model for validation
            icsr_data = ICSRData(**extracted_json)
            
            logger.info(
                "ICSR extraction completed",
                pmid=pmid,
                num_events=len(icsr_data.events),
                num_suspect_products=len(icsr_data.suspect_products),
                has_narrative=bool(icsr_data.case_narrative)
            )
            
            return icsr_data
            
        except Exception as e:
            logger.error("ICSR extraction failed", pmid=pmid, error=str(e), exc_info=True)
            raise
    
    def _build_extraction_prompt(
        self,
        title: str,
        abstract: str,
        full_text: Optional[str] = None
    ) -> str:
        """Build comprehensive extraction prompt"""
        
        # Use full text if available, otherwise abstract
        content = full_text if full_text else abstract
        
        prompt = f"""Extract ICSR (Individual Case Safety Report) data from the following medical literature.

**Article Title:** {title}

**Content:**
{content[:8000]}  # Limit to avoid token limits

**Extract the following data in JSON format:**

{{
  "report_type": "Literature",
  "country_of_incidence": "Country where event occurred (if stated)",
  "initial_receipt_date": "Date in YYYY-MM-DD format (publication date or case date)",
  "is_medically_confirmed": true/false,
  
  "reporter": {{
    "first_name": "First name of lead author",
    "last_name": "Last name of lead author",
    "is_hcp": true,
    "is_primary_reporter": true,
    "occupation": "Author's occupation if stated"
  }},
  
  "literature": {{
    "author": "All authors",
    "journal": "Journal name",
    "year": publication_year
  }},
  
  "patient": {{
    "initials": "Patient initials if stated",
    "gender": "Male/Female/Unknown",
    "age": age_in_years,
    "age_unit": "Years/Months/Days",
    "age_group": "Adolescent/Adult/Elderly/Pediatric",
    "height_cm": height_if_stated,
    "weight_kg": weight_if_stated,
    "is_pregnant": true/false/null,
    "is_breastfeeding": true/false/null,
    "medical_history": "Relevant medical history",
    "relevant_history": "Other relevant history"
  }},
  
  "death_details": {{
    "cause_of_death": "If patient died",
    "date_of_death": "YYYY-MM-DD",
    "autopsy_result": "Autopsy findings if stated"
  }},
  
  "lab_data": [
    {{
      "test_name": "Lab test name",
      "date": "YYYY-MM-DD",
      "result_value": "Value",
      "result_status": "Normal/High/Low",
      "unit": "Unit of measurement"
    }}
  ],
  
  "suspect_products": [
    {{
      "product_type": "Suspect",
      "brand_name": "Brand name if stated",
      "generic_name": "Generic/active ingredient name",
      "indication": "Why drug was prescribed",
      "dosage_form": "Tablet/Injection/etc",
      "dose": "Dose amount",
      "strength": "Strength with unit",
      "route": "Oral/IV/IM/etc",
      "frequency": "Once daily/BID/etc",
      "start_date": "YYYY-MM-DD",
      "stop_date": "YYYY-MM-DD",
      "action_taken": "Permanently Discontinued/Dose Decreased/etc",
      "dechallenge": "Positive/Negative/Not Done",
      "rechallenge": "Positive/Negative/Not Done",
      "additional_info": ["Overdose", "Off-label use", etc]
    }}
  ],
  
  "concomitant_products": [
    {{
      "product_type": "Concomitant",
      "generic_name": "Concomitant drug name",
      "indication": "Why prescribed",
      "dose": "Dose",
      "route": "Route"
    }}
  ],
  
  "events": [
    {{
      "description": "Adverse event description as reported",
      "meddra_pt": "MedDRA Preferred Term (if you can infer)",
      "onset_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "outcome": "Fatal/Recovered/Recovering/Not Recovered/Recovered with Sequelae",
      "is_medically_confirmed": true,
      "seriousness_criteria": ["Death", "Hospitalization", "Life-threatening", "Disability", "Medically Significant", "Congenital Anomaly"],
      "action_taken": "Action taken for this event",
      "dechallenge_result": "Positive/Negative",
      "rechallenge_result": "Positive/Negative"
    }}
  ],
  
  "case_narrative": "Brief chronological narrative summarizing the case: patient characteristics, drug exposure, event onset, clinical course, outcome",
  
  "reference_id": "PubMed ID or other reference"
}}

**Important Instructions:**
1. Extract ONLY information explicitly stated or strongly implied in the text
2. Use null for missing data - do NOT make assumptions
3. For dates, use YYYY-MM-DD format or null
4. For seriousness criteria, include ALL that apply from the text
5. Distinguish between suspect (causative) and concomitant (concurrent) medications
6. The case_narrative should be a concise 2-3 sentence chronological summary
7. Return ONLY the JSON object, no additional text

Extract the data now:"""
        
        return prompt


# Initialize service
icsr_extractor = ICSRExtractor()
