"""
Legal Clause Extractor - Custom entity extraction for legal documents
Extracts specific legal clauses, terms, and contractual elements
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

class LegalClauseExtractor:
    """Extract legal clauses and contractual terms using custom patterns and AI"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize the legal clause extractor"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
        # Define legal clause patterns and keywords
        self.legal_clauses = {
            "Parties": {
                "keywords": ["party", "parties", "agreement between", "contract between", "hereinafter"],
                "pattern": r"(?:party|parties|agreement between|contract between|hereinafter)\s+([A-Z][^.]*?)(?:\s+and\s+([A-Z][^.]*?))?",
                "type": "LEGAL_PARTY"
            },
            "Agreement Date": {
                "keywords": ["agreement date", "effective date", "dated", "entered into"],
                "pattern": r"(?:agreement date|effective date|dated|entered into)\s*:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})",
                "type": "LEGAL_DATE"
            },
            "Governing Law": {
                "keywords": ["governing law", "jurisdiction", "laws of", "state of", "country of"],
                "pattern": r"(?:governing law|jurisdiction|laws of|state of|country of)\s*:?\s*([A-Za-z\s]+(?:state|country|jurisdiction)?)",
                "type": "LEGAL_JURISDICTION"
            },
            "Termination": {
                "keywords": ["termination", "terminate", "expire", "expiration", "end of agreement"],
                "pattern": r"(?:termination|terminate|expire|expiration|end of agreement)\s*:?\s*([^.]*?)(?:\s+upon|\s+if|\s+when)",
                "type": "LEGAL_TERMINATION"
            },
            "Non-Compete": {
                "keywords": ["non-compete", "non compete", "competition", "competing business"],
                "pattern": r"(?:non-compete|non compete|competition|competing business)\s*:?\s*([^.]*?)(?:\s+for|\s+during|\s+period)",
                "type": "LEGAL_NON_COMPETE"
            },
            "Confidentiality": {
                "keywords": ["confidential", "confidentiality", "proprietary", "trade secret"],
                "pattern": r"(?:confidential|confidentiality|proprietary|trade secret)\s*:?\s*([^.]*?)(?:\s+information|\s+data)",
                "type": "LEGAL_CONFIDENTIALITY"
            },
            "Intellectual Property": {
                "keywords": ["intellectual property", "ip", "patent", "copyright", "trademark"],
                "pattern": r"(?:intellectual property|ip|patent|copyright|trademark)\s*:?\s*([^.]*?)(?:\s+rights|\s+ownership)",
                "type": "LEGAL_IP"
            },
            "Liability": {
                "keywords": ["liability", "damages", "indemnification", "warranty"],
                "pattern": r"(?:liability|damages|indemnification|warranty)\s*:?\s*([^.]*?)(?:\s+shall|\s+will|\s+may)",
                "type": "LEGAL_LIABILITY"
            },
            "Payment Terms": {
                "keywords": ["payment", "fee", "compensation", "royalty", "revenue"],
                "pattern": r"(?:payment|fee|compensation|royalty|revenue)\s*:?\s*([^.]*?)(?:\s+shall|\s+will|\s+amount)",
                "type": "LEGAL_PAYMENT"
            },
            "Force Majeure": {
                "keywords": ["force majeure", "act of god", "unforeseen circumstances", "beyond control"],
                "pattern": r"(?:force majeure|act of god|unforeseen circumstances|beyond control)\s*:?\s*([^.]*?)(?:\s+shall|\s+will)",
                "type": "LEGAL_FORCE_MAJEURE"
            }
        }
        
        logger.info("Legal Clause Extractor initialized", model=model)
    
    async def extract_legal_clauses(self, text: str, document_title: str = "") -> Dict[str, Any]:
        """
        Extract legal clauses and terms from text
        
        Args:
            text: Document text content
            document_title: Title of the document for context
            
        Returns:
            Dict containing legal clauses, terms, and metadata
        """
        try:
            logger.info("Starting legal clause extraction", 
                       text_length=len(text), 
                       title=document_title)
            
            # Extract clauses using pattern matching
            pattern_clauses = self._extract_pattern_clauses(text)
            
            # Extract clauses using AI for complex cases
            ai_clauses = await self._extract_ai_clauses(text, document_title)
            
            # Combine and deduplicate results
            all_clauses = self._combine_clauses(pattern_clauses, ai_clauses)
            
            # Extract paragraph contexts
            clause_contexts = self._extract_clause_contexts(text, all_clauses)
            
            result = {
                "legal_clauses": all_clauses,
                "clause_contexts": clause_contexts,
                "clause_count": len(all_clauses),
                "extraction_method": "legal_clause_extractor",
                "document_title": document_title,
                "metadata": {
                    "pattern_matches": len(pattern_clauses),
                    "ai_matches": len(ai_clauses),
                    "total_clauses": len(all_clauses)
                }
            }
            
            logger.info("Legal clause extraction completed", 
                       clause_count=len(all_clauses),
                       pattern_matches=len(pattern_clauses),
                       ai_matches=len(ai_clauses))
            
            return result
            
        except Exception as e:
            logger.error("Legal clause extraction failed", error=str(e))
            return {
                "legal_clauses": [],
                "clause_contexts": [],
                "clause_count": 0,
                "extraction_method": "legal_clause_extractor",
                "error": str(e)
            }
    
    def _extract_pattern_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Extract clauses using regex patterns"""
        clauses = []
        
        for clause_name, config in self.legal_clauses.items():
            pattern = config["pattern"]
            clause_type = config["type"]
            
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                clause_text = match.group(0).strip()
                start_pos = match.start()
                end_pos = match.end()
                
                clauses.append({
                    "text": clause_text,
                    "type": clause_type,
                    "clause_name": clause_name,
                    "confidence": 0.8,  # High confidence for pattern matches
                    "start_char": start_pos,
                    "end_char": end_pos,
                    "extraction_method": "pattern_matching"
                })
        
        return clauses
    
    async def _extract_ai_clauses(self, text: str, document_title: str) -> List[Dict[str, Any]]:
        """Extract clauses using AI for complex cases"""
        try:
            # Truncate text if too long
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = self._create_legal_clause_prompt(text, document_title)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal document analysis expert. Extract specific legal clauses and contractual terms from documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error("AI legal clause extraction failed", error=str(e))
            return []
    
    def _create_legal_clause_prompt(self, text: str, document_title: str) -> str:
        """Create prompt for AI legal clause extraction"""
        return f"""
Analyze the following legal document and extract specific legal clauses and contractual terms.

Document Title: {document_title}

Focus on extracting these types of legal clauses:
- Parties involved in the agreement
- Agreement dates and effective dates
- Governing law and jurisdiction
- Termination conditions
- Non-compete clauses
- Confidentiality agreements
- Intellectual property rights
- Liability and damages
- Payment terms and compensation
- Force majeure clauses
- Renewal terms
- Notice periods
- Exclusivity clauses
- Anti-assignment clauses
- Change of control provisions

For each clause found, provide:
1. The exact text of the clause
2. The type of clause (from the list above)
3. The paragraph or section it appears in
4. A confidence score (0-1)

Document Text:
{text}

Return the results in JSON format with this structure:
{{
    "clauses": [
        {{
            "text": "exact clause text",
            "type": "clause_type",
            "clause_name": "descriptive_name",
            "confidence": 0.95,
            "paragraph_context": "surrounding paragraph text",
            "start_char": 1234,
            "end_char": 1456
        }}
    ]
}}
"""
    
    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured data"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get("clauses", [])
            return []
        except Exception as e:
            logger.error("Failed to parse AI response", error=str(e))
            return []
    
    def _combine_clauses(self, pattern_clauses: List[Dict], ai_clauses: List[Dict]) -> List[Dict]:
        """Combine and deduplicate clauses from different extraction methods"""
        all_clauses = pattern_clauses + ai_clauses
        
        # Remove duplicates based on text similarity
        unique_clauses = []
        for clause in all_clauses:
            is_duplicate = False
            for existing in unique_clauses:
                if self._clauses_similar(clause, existing):
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if clause.get("confidence", 0) > existing.get("confidence", 0):
                        unique_clauses.remove(existing)
                        unique_clauses.append(clause)
                    break
            
            if not is_duplicate:
                unique_clauses.append(clause)
        
        return unique_clauses
    
    def _clauses_similar(self, clause1: Dict, clause2: Dict) -> bool:
        """Check if two clauses are similar (for deduplication)"""
        text1 = clause1.get("text", "").lower().strip()
        text2 = clause2.get("text", "").lower().strip()
        
        # Simple similarity check
        if len(text1) < 10 or len(text2) < 10:
            return False
        
        # Check if one is contained in the other
        if text1 in text2 or text2 in text1:
            return True
        
        # Check word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        overlap = len(words1.intersection(words2))
        total_words = len(words1.union(words2))
        
        return overlap / total_words > 0.7 if total_words > 0 else False
    
    def _extract_clause_contexts(self, text: str, clauses: List[Dict]) -> List[Dict]:
        """Extract paragraph contexts for each clause"""
        contexts = []
        
        for clause in clauses:
            start_char = clause.get("start_char", 0)
            end_char = clause.get("end_char", start_char + 100)
            
            # Extract surrounding paragraph
            paragraph_start = max(0, start_char - 200)
            paragraph_end = min(len(text), end_char + 200)
            
            context_text = text[paragraph_start:paragraph_end]
            
            contexts.append({
                "clause_id": clause.get("text", "")[:50],
                "context": context_text,
                "start_char": paragraph_start,
                "end_char": paragraph_end,
                "clause_type": clause.get("type", ""),
                "clause_name": clause.get("clause_name", "")
            })
        
        return contexts
    
    def highlight_clauses_in_text(self, text: str, clauses: List[Dict]) -> str:
        """Add HTML highlighting to legal clauses in text"""
        if not clauses:
            return text
        
        # Sort clauses by start position (descending) to avoid offset issues
        sorted_clauses = sorted(clauses, key=lambda x: x.get('start_char', 0), reverse=True)
        
        highlighted_text = text
        
        for clause in sorted_clauses:
            start_char = clause.get('start_char', 0)
            end_char = clause.get('end_char', start_char + len(clause.get('text', '')))
            clause_text = clause.get('text', '')
            clause_type = clause.get('type', 'LEGAL_CLAUSE')
            confidence = clause.get('confidence', 0.8)
            
            if start_char < len(highlighted_text) and end_char <= len(highlighted_text):
                # Create the highlighted span
                highlighted_span = f'<span class="entity entity-{clause_type.lower().replace("_", "-")}" title="{clause_type}: {clause_text}" data-entity-type="{clause_type}" data-confidence="{confidence:.2f}">{clause_text}</span>'
                
                # Replace the text with highlighted version
                highlighted_text = (
                    highlighted_text[:start_char] + 
                    highlighted_span + 
                    highlighted_text[end_char:]
                )
        
        return highlighted_text
