"""
ICSR Narrative Generator
Generates comprehensive, regulatory-compliant ICSR narratives using AI
"""
import os
import structlog
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from icsr_extractor import ICSRData

logger = structlog.get_logger(__name__)


class ICSRNarrativeGenerator:
    """
    Generates comprehensive ICSR narratives following regulatory guidelines
    (FDA, EMA, ICH E2B)
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.model = "gpt-4o"
        logger.info("ICSR Narrative Generator initialized")
    
    async def generate_narrative(
        self,
        icsr_data: ICSRData,
        original_text: str
    ) -> str:
        """
        Generate comprehensive ICSR narrative from extracted data
        
        Args:
            icsr_data: Extracted ICSR data
            original_text: Original article text for context
            
        Returns:
            Comprehensive ICSR narrative
        """
        try:
            logger.info("Generating ICSR narrative")
            
            # Build narrative prompt
            prompt = self._build_narrative_prompt(icsr_data, original_text)
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert medical writer specializing in pharmacovigilance ICSR narratives.

Your task is to write a comprehensive, regulatory-compliant ICSR narrative following FDA, EMA, and ICH E2B guidelines.

The narrative must:
1. Present information in logical chronological order
2. Include all relevant clinical information
3. Be objective and factual
4. Use proper medical terminology
5. Follow the structure: Patient → Medical History → Drug Exposure → Event Onset → Clinical Course → Outcome → Assessment
6. Be comprehensive yet concise (typically 200-500 words)
7. Include relevant laboratory values with normal ranges
8. State causality assessment if available

Write in third person, past tense. Be professional and precise."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Balanced for medical writing
                max_tokens=1500
            )
            
            narrative = response.choices[0].message.content.strip()
            
            logger.info(
                "ICSR narrative generated",
                length=len(narrative),
                word_count=len(narrative.split())
            )
            
            return narrative
            
        except Exception as e:
            logger.error("Narrative generation failed", error=str(e), exc_info=True)
            raise
    
    def _build_narrative_prompt(
        self,
        icsr_data: ICSRData,
        original_text: str
    ) -> str:
        """Build prompt for narrative generation"""
        
        # Format extracted data for prompt
        data_summary = self._format_data_summary(icsr_data)
        
        prompt = f"""Generate a comprehensive ICSR (Individual Case Safety Report) narrative based on the following extracted data and original source.

**Extracted ICSR Data:**
{data_summary}

**Original Source Text (for context):**
{original_text[:4000]}

**Generate a comprehensive ICSR narrative following this structure:**

1. **Patient Information & Medical History:**
   - Demographics (age, gender, relevant characteristics)
   - Relevant medical history and concurrent conditions
   - Baseline clinical status

2. **Drug Exposure:**
   - Suspect drug(s) with indication, dose, route, frequency, duration
   - Concomitant medications
   - Start and stop dates

3. **Event Onset & Description:**
   - When event(s) occurred relative to drug start
   - Detailed description of adverse event(s)
   - Seriousness criteria (death, hospitalization, etc.)

4. **Clinical Course:**
   - Progression of event(s)
   - Therapeutic measures taken
   - Laboratory findings with normal ranges
   - Response to treatment

5. **Outcome:**
   - Final outcome of event(s)
   - Drug action taken (discontinued, dose reduced, etc.)
   - Dechallenge/rechallenge results if available

6. **Assessment:**
   - Temporal relationship
   - Causality assessment if stated
   - Reporter's conclusion

**Requirements:**
- Write in third person, past tense
- Present information chronologically
- Include specific dates, doses, and lab values
- Be objective and factual
- Use proper medical terminology
- Length: 200-500 words
- Do NOT include section headers in the output - write as flowing paragraphs

Generate the narrative now:"""
        
        return prompt
    
    def _format_data_summary(self, icsr_data: ICSRData) -> str:
        """Format ICSR data into readable summary"""
        
        summary_parts = []
        
        # Patient
        if icsr_data.patient:
            p = icsr_data.patient
            patient_info = f"Patient: {p.age} {p.age_unit} {p.gender}"
            if p.medical_history:
                patient_info += f", Medical History: {p.medical_history}"
            summary_parts.append(patient_info)
        
        # Suspect Products
        if icsr_data.suspect_products:
            for prod in icsr_data.suspect_products:
                prod_info = f"Suspect Drug: {prod.generic_name or prod.brand_name}"
                if prod.dose:
                    prod_info += f", Dose: {prod.dose}"
                if prod.route:
                    prod_info += f", Route: {prod.route}"
                if prod.indication:
                    prod_info += f", Indication: {prod.indication}"
                if prod.start_date:
                    prod_info += f", Started: {prod.start_date}"
                if prod.action_taken:
                    prod_info += f", Action: {prod.action_taken}"
                summary_parts.append(prod_info)
        
        # Events
        if icsr_data.events:
            for event in icsr_data.events:
                event_info = f"Event: {event.description}"
                if event.onset_date:
                    event_info += f", Onset: {event.onset_date}"
                if event.outcome:
                    event_info += f", Outcome: {event.outcome}"
                if event.seriousness_criteria:
                    event_info += f", Serious: {', '.join(event.seriousness_criteria)}"
                summary_parts.append(event_info)
        
        # Lab Data
        if icsr_data.lab_data:
            lab_summary = "Lab Data: " + "; ".join([
                f"{lab.test_name}: {lab.result_value} {lab.unit or ''} ({lab.result_status or 'Unknown'})"
                for lab in icsr_data.lab_data[:5]  # Limit to first 5
            ])
            summary_parts.append(lab_summary)
        
        # Death Details
        if icsr_data.death_details and icsr_data.death_details.cause_of_death:
            summary_parts.append(f"Death: {icsr_data.death_details.cause_of_death}")
        
        return "\n".join(summary_parts)


# Initialize service
narrative_generator = ICSRNarrativeGenerator()

