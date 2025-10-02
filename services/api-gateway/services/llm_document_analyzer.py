"""
LLM-based Document Structure Analysis Service
Intelligently identifies and frames cohesive sections in documents
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import os
from datetime import datetime
import asyncio
import httpx

@dataclass
class DocumentSection:
    """Represents a document section identified by LLM"""
    id: str
    title: str
    start_position: int
    end_position: int
    content: str
    section_type: str  # abstract, introduction, methods, results, discussion, conclusion, etc.
    confidence: float
    word_count: int
    key_points: List[str]
    page_number: Optional[int] = None

@dataclass
class DocumentStructure:
    """Complete document structure analysis"""
    sections: List[DocumentSection]
    document_type: str  # research_paper, legal_document, medical_report, etc.
    total_pages: int
    total_words: int
    confidence: float
    analysis_timestamp: str
    fallback_navigation: Dict[str, Any]  # For documents without clear sections

class LLMDocumentAnalyzer:
    """Service for analyzing document structure using LLM"""
    
    def __init__(self):
        # Get OpenAI API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.use_openai = bool(self.openai_api_key)
        
        if self.use_openai:
            print("🤖 LLM Analyzer initialized with OpenAI GPT-4")
        else:
            print("🔄 LLM Analyzer using mock implementation (no OpenAI API key)")
        
        # Enhanced section type mappings for different document types
        self.section_patterns = {
            "research_paper": [
                "abstract", "introduction", "core_theme", "literature_review", 
                "literature_section", "gap", "problem_statement", "methodology", 
                "methods", "contribution", "results", "findings", "discussion", 
                "risk", "conclusion", "references", "acknowledgments", "appendix"
            ],
            "legal_document": [
                "preamble", "parties", "recitals", "definitions", "terms_conditions",
                "obligations", "representations", "warranties", "liability", 
                "indemnification", "termination", "governing_law", "dispute_resolution"
            ],
            "medical_report": [
                "patient_info", "chief_complaint", "history", "examination", 
                "assessment", "diagnosis", "treatment", "recommendations", 
                "follow_up", "prognosis", "risk"
            ],
            "case_study": [
                "background", "case_description", "core_theme", "problem_statement",
                "clinical_course", "discussion", "conclusion", "references"
            ]
        }
        
        # Section color mappings for frontend highlighting
        self.section_colors = {
            "core_theme": "#e3f2fd",        # Light blue - primary theme
            "problem_statement": "#ffebee",  # Light red - problem identification
            "gap": "#fff3e0",               # Light orange - research gap
            "literature_section": "#f3e5f5", # Light purple - literature review
            "literature_review": "#f3e5f5",  # Light purple - literature review
            "methodology": "#e8f5e8",       # Light green - methods
            "methods": "#e8f5e8",           # Light green - methods
            "contribution": "#fff8e1",      # Light yellow - contributions
            "risk": "#ffebee",              # Light red - risk assessment
            "conclusion": "#f1f8e9",        # Light lime - conclusions
            "results": "#e0f2f1",           # Light teal - results
            "findings": "#e0f2f1",          # Light teal - findings
            "discussion": "#fce4ec",        # Light pink - discussion
            "abstract": "#f5f5f5",          # Light gray - abstract
            "introduction": "#e8eaf6",      # Light indigo - introduction
            "references": "#efebe9",        # Light brown - references
            # Legal risk-based colors
            "high_risk_clause": "#ffcdd2",   # Light red - high risk
            "medium_risk_clause": "#fff3e0", # Light orange - medium risk  
            "low_risk_clause": "#e8f5e8",    # Light green - low risk
            "liability": "#f8bbd9",          # Pink - liability clauses
            "indemnification": "#ffcdd2",    # Light red - indemnification
            "termination": "#ffab91",        # Orange - termination clauses
            "default": "#fafafa"            # Very light gray - default
        }
        
        # Legal risk patterns for automatic risk assessment
        self.legal_risk_patterns = {
            "high_risk": [
                r"unlimited liability",
                r"personal guarantee",
                r"liquidated damages",
                r"consequential damages",
                r"punitive damages",
                r"indemnify.*hold harmless",
                r"defend.*indemnify",
                r"sole discretion",
                r"without notice",
                r"immediate termination",
                r"breach.*material",
                r"waive.*right",
                r"waiver.*claims"
            ],
            "medium_risk": [
                r"reasonable efforts",
                r"best efforts",
                r"commercially reasonable",
                r"dispute resolution",
                r"arbitration",
                r"governing law",
                r"force majeure",
                r"assignment.*consent",
                r"confidential.*information",
                r"intellectual property",
                r"limitation.*liability"
            ],
            "low_risk": [
                r"definitions",
                r"interpretation",
                r"headings",
                r"severability",
                r"entire agreement",
                r"counterparts",
                r"effective date",
                r"recitals",
                r"whereas"
            ]
        }

    async def analyze_document_structure(self, content: str, document_title: str = "") -> DocumentStructure:
        """
        Main method to analyze document structure using OpenAI GPT-4 or fallback to mock
        """
        try:
            if self.use_openai:
                return await self._analyze_with_openai(content, document_title)
            else:
                return await self._analyze_with_mock(content, document_title)
        except Exception as e:
            print(f"Error in LLM analysis, falling back to mock: {e}")
            return await self._analyze_with_mock(content, document_title)

    async def _analyze_with_openai(self, content: str, title: str) -> DocumentStructure:
        """Analyze document structure using OpenAI GPT-4"""
        try:
            # Step 1: Identify document type
            doc_type = await self._identify_document_type_openai(content, title)
            
            # Step 2: Extract sections using OpenAI
            sections = await self._extract_sections_openai(content, doc_type)
            
            # Step 3: Calculate metadata
            total_words = len(content.split())
            total_pages = max(1, total_words // 300)  # Rough estimate: 300 words per page
            
            # Step 4: Analyze legal risks if this is a legal document
            risk_analysis = None
            if doc_type == "legal_document":
                risk_analysis = self.analyze_legal_risks(content, sections)
            
            # Step 5: Create fallback navigation
            fallback_nav = self._create_fallback_navigation(content, sections)
            
            # Add risk analysis to fallback navigation if available
            if risk_analysis:
                fallback_nav["risk_analysis"] = risk_analysis
            
            return DocumentStructure(
                sections=sections,
                document_type=doc_type,
                total_pages=total_pages,
                total_words=total_words,
                confidence=0.95,  # Higher confidence for OpenAI
                analysis_timestamp=datetime.now().isoformat(),
                fallback_navigation=fallback_nav
            )
            
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return await self._analyze_with_mock(content, title)

    async def _identify_document_type_openai(self, content: str, title: str) -> str:
        """Identify document type using OpenAI"""
        try:
            prompt = f"""
            Analyze the following document and identify its type. Consider the title and content structure.
            
            Title: {title}
            Content (first 2000 characters): {content[:2000]}
            
            Choose the most appropriate document type from:
            - research_paper
            - legal_document  
            - medical_report
            - clinical_trial
            - case_study
            - general_document
            
            Respond with only the document type, no explanation.
            """
            
            response = await self._call_openai(prompt, max_tokens=50)
            doc_type = response.strip().lower()
            
            # Validate response
            valid_types = ["research_paper", "legal_document", "medical_report", "clinical_trial", "case_study", "general_document"]
            if doc_type in valid_types:
                return doc_type
            else:
                return "general_document"
                
        except Exception as e:
            print(f"Document type identification failed: {e}")
            return "general_document"

    async def _extract_sections_openai(self, content: str, doc_type: str) -> List[DocumentSection]:
        """Extract document sections using OpenAI with academic focus"""
        try:
            # Split content into chunks for analysis (GPT-4 has token limits)
            chunks = self._split_content_into_chunks(content, max_chunk_size=3000)
            all_sections = []
            
            for i, chunk in enumerate(chunks):
                chunk_sections = await self._analyze_chunk_openai(chunk, doc_type, i * 3000, content)
                all_sections.extend(chunk_sections)
            
            # Merge and deduplicate sections
            merged_sections = self._merge_sections(all_sections)
            
            if not merged_sections:
                # Fallback to mock if OpenAI returns no sections
                return self._mock_extract_sections(content, doc_type)
            
            return merged_sections
            
        except Exception as e:
            print(f"Section extraction failed: {e}")
            return self._mock_extract_sections(content, doc_type)

    async def _analyze_chunk_openai(self, chunk: str, doc_type: str, offset: int, full_content: str) -> List[DocumentSection]:
        """Analyze a chunk of content using OpenAI with academic focus"""
        try:
            prompt = f"""
            Analyze this document chunk and identify distinct sections with focus on academic research structure. This is a {doc_type}.
            
            Content: {chunk}
            
            Pay special attention to identifying these academic section types:
            - core_theme: Main research theme or focus
            - problem_statement: Research problem definition
            - gap: Research gaps or knowledge gaps
            - literature_section: Literature review or related work
            - methodology: Research methods and approaches
            - contribution: Novel contributions or innovations
            - risk: Risk assessment, limitations, or threats
            - results: Findings and outcomes
            - discussion: Analysis and interpretation
            - conclusion: Summary and conclusions
            
            For each section you identify, provide:
            1. A clear section title
            2. The section type (prioritize the academic types above, or use: abstract, introduction, references, etc.)
            3. The approximate start and end positions within the chunk
            4. 2-3 key points from that section
            5. Confidence level (0.0-1.0)
            
            Respond in this JSON format:
            {{
                "sections": [
                    {{
                        "title": "Section Title",
                        "section_type": "section_type",
                        "start_pos": 0,
                        "end_pos": 500,
                        "key_points": ["Point 1", "Point 2"],
                        "confidence": 0.9
                    }}
                ]
            }}
            
            Only identify clear, meaningful sections. If no clear sections exist, return empty array.
            """
            
            response = await self._call_openai(prompt, max_tokens=1000)
            
            try:
                parsed = json.loads(response)
                sections = []
                
                for i, section_data in enumerate(parsed.get("sections", [])):
                    section_content = chunk[section_data["start_pos"]:section_data["end_pos"]]
                    
                    section = DocumentSection(
                        id=f"section_{offset//1000}_{i+1}",
                        title=section_data["title"],
                        start_position=offset + section_data["start_pos"],
                        end_position=offset + section_data["end_pos"],
                        content=section_content,
                        section_type=section_data["section_type"],
                        confidence=section_data["confidence"],
                        word_count=len(section_content.split()),
                        key_points=section_data["key_points"][:3],
                        page_number=self._estimate_page_number(full_content, offset + section_data["start_pos"])
                    )
                    sections.append(section)
                
                return sections
                
            except json.JSONDecodeError:
                print(f"Failed to parse OpenAI response as JSON: {response}")
                return []
                
        except Exception as e:
            print(f"Chunk analysis failed: {e}")
            return []

    async def _call_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Make API call to OpenAI using httpx"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [
                            {"role": "system", "content": "You are an expert academic document analyzer. Identify document sections with focus on research structure including core themes, problem statements, gaps, contributions, and risks."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3
                    },
                    timeout=30.0  # Reduced timeout for on-demand analysis
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            raise

    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 3000) -> List[str]:
        """Split content into manageable chunks for OpenAI processing"""
        words = content.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _merge_sections(self, sections: List[DocumentSection]) -> List[DocumentSection]:
        """Merge overlapping or duplicate sections"""
        if not sections:
            return []
        
        # Sort by start position
        sorted_sections = sorted(sections, key=lambda s: s.start_position)
        merged = [sorted_sections[0]]
        
        for current in sorted_sections[1:]:
            last = merged[-1]
            
            # Check for overlap or very close sections
            if current.start_position <= last.end_position + 100:
                # Merge sections
                merged_content = last.content + " " + current.content
                merged_section = DocumentSection(
                    id=last.id,
                    title=last.title if len(last.title) > len(current.title) else current.title,
                    start_position=last.start_position,
                    end_position=max(last.end_position, current.end_position),
                    content=merged_content,
                    section_type=last.section_type,
                    confidence=max(last.confidence, current.confidence),
                    word_count=len(merged_content.split()),
                    key_points=list(set(last.key_points + current.key_points))[:3],
                    page_number=last.page_number
                )
                merged[-1] = merged_section
            else:
                merged.append(current)
        
        return merged

    async def _analyze_with_mock(self, content: str, title: str) -> DocumentStructure:
        """Fallback mock analysis when OpenAI is not available"""
        try:
            # Step 1: Identify document type
            doc_type = self._mock_identify_document_type(content, title)
            
            # Step 2: Extract sections using mock implementation
            sections = self._mock_extract_sections(content, doc_type)
            
            # Step 3: Calculate metadata
            total_words = len(content.split())
            total_pages = max(1, total_words // 300)
            
            # Step 4: Analyze legal risks if this is a legal document
            risk_analysis = None
            if doc_type == "legal_document":
                risk_analysis = self.analyze_legal_risks(content, sections)
            
            # Step 5: Create fallback navigation
            fallback_nav = self._create_fallback_navigation(content, sections)
            
            # Add risk analysis to fallback navigation if available
            if risk_analysis:
                fallback_nav["risk_analysis"] = risk_analysis
            
            return DocumentStructure(
                sections=sections,
                document_type=doc_type,
                total_pages=total_pages,
                total_words=total_words,
                confidence=0.75,  # Lower confidence for mock
                analysis_timestamp=datetime.now().isoformat(),
                fallback_navigation=fallback_nav
            )
            
        except Exception as e:
            print(f"Error in mock analysis: {e}")
            return self._create_fallback_structure(content)

    async def _identify_document_type(self, content: str, title: str = "") -> str:
        """Identify the type of document using LLM (with mock fallback)"""
        
        # Mock implementation for testing (replace with actual LLM call when API key is available)
        if not openai.api_key:
            return self._mock_identify_document_type(content, title)
        
        # Use first 2000 characters for type identification
        sample_content = content[:2000]
        
        prompt = f"""
        Analyze the following document excerpt and title to determine the document type.
        
        Title: {title}
        
        Content excerpt:
        {sample_content}
        
        Based on the content, structure, and language used, classify this document as one of:
        - research_paper
        - legal_document  
        - medical_report
        - case_study
        - technical_manual
        - business_report
        - other
        
        Respond with only the document type (no explanation needed).
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            doc_type = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            valid_types = ["research_paper", "legal_document", "medical_report", "case_study", "technical_manual", "business_report", "other"]
            if doc_type not in valid_types:
                doc_type = "other"
                
            return doc_type
            
        except Exception as e:
            print(f"Error identifying document type: {e}")
            return self._mock_identify_document_type(content, title)

    def _mock_identify_document_type(self, content: str, title: str = "") -> str:
        """Mock document type identification for testing"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Simple keyword-based classification
        if any(word in content_lower for word in ['abstract', 'methodology', 'results', 'discussion', 'references']):
            return "research_paper"
        elif any(word in content_lower for word in ['patient', 'diagnosis', 'treatment', 'clinical', 'medical']):
            return "medical_report"
        elif any(word in content_lower for word in ['case', 'pericarditis', 'vaccination', 'covid']):
            return "case_study"
        elif any(word in content_lower for word in ['contract', 'agreement', 'party', 'terms', 'conditions']):
            return "legal_document"
        else:
            return "research_paper"  # Default for academic papers

    async def _extract_sections_with_llm(self, content: str, doc_type: str) -> List[DocumentSection]:
        """Extract document sections using LLM analysis (with mock fallback)"""
        
        # Mock implementation for testing
        if not openai.api_key:
            return self._mock_extract_sections(content, doc_type)
        
        # Get expected section types for this document type
        expected_sections = self.section_patterns.get(doc_type, [])
        
        prompt = f"""
        Analyze the following document and identify its main sections. This appears to be a {doc_type}.
        
        For each section you identify, provide:
        1. Section title (clear, descriptive name)
        2. Section type (from this list if applicable: {', '.join(expected_sections)})
        3. Start position (character position where section begins)
        4. Key points (2-3 main points from that section)
        5. Confidence level (0.0 to 1.0)
        
        Document content:
        {content[:8000]}  # Limit content to avoid token limits
        
        Respond in JSON format:
        {{
            "sections": [
                {{
                    "title": "Section Title",
                    "section_type": "introduction",
                    "start_position": 123,
                    "key_points": ["Point 1", "Point 2"],
                    "confidence": 0.9
                }}
            ]
        }}
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2
            )
            
            # Parse LLM response
            llm_response = json.loads(response.choices[0].message.content)
            sections = []
            
            for i, section_data in enumerate(llm_response.get("sections", [])):
                # Find actual content boundaries
                start_pos = section_data.get("start_position", 0)
                end_pos = self._find_section_end(content, start_pos, i, len(llm_response["sections"]))
                
                section_content = content[start_pos:end_pos]
                
                section = DocumentSection(
                    id=f"section-{i+1}",
                    title=section_data.get("title", f"Section {i+1}"),
                    start_position=start_pos,
                    end_position=end_pos,
                    content=section_content,
                    section_type=section_data.get("section_type", "other"),
                    confidence=section_data.get("confidence", 0.7),
                    word_count=len(section_content.split()),
                    key_points=section_data.get("key_points", []),
                    page_number=self._estimate_page_number(content, start_pos)
                )
                sections.append(section)
            
            return sections
            
        except Exception as e:
            print(f"Error in LLM section extraction: {e}")
            return self._mock_extract_sections(content, doc_type)

    def _mock_extract_sections(self, content: str, doc_type: str) -> List[DocumentSection]:
        """Mock section extraction for testing"""
        sections = []
        
        # Look for clear structural markers first
        if "=== PAGE" in content:
            # Page-based sections
            page_splits = re.split(r'(=== PAGE \d+ ===)', content)
            current_pos = 0
            
            for i in range(1, len(page_splits), 2):  # Every other element is a page marker
                if i + 1 < len(page_splits):
                    page_marker = page_splits[i]
                    page_content = page_splits[i + 1]
                    page_num = int(re.search(r'PAGE (\d+)', page_marker).group(1))
                    
                    # Extract meaningful title from page content
                    lines = [line.strip() for line in page_content.split('\n')[:10] if line.strip()]
                    title = self._extract_meaningful_title(lines, page_num)
                    
                    # Determine section type based on content
                    section_type = self._determine_section_type(page_content, doc_type)
                    
                    # Extract key points
                    key_points = self._extract_key_points(page_content)
                    
                    section = DocumentSection(
                        id=f"page-{page_num}",
                        title=title,
                        start_position=current_pos,
                        end_position=current_pos + len(page_marker) + len(page_content),
                        content=page_content,
                        section_type=section_type,
                        confidence=0.85,
                        word_count=len(page_content.split()),
                        key_points=key_points,
                        page_number=page_num
                    )
                    sections.append(section)
                    current_pos += len(page_marker) + len(page_content)
        else:
            # Fallback to basic sections
            return self._create_basic_sections(content)
        
        return sections

    def _extract_meaningful_title(self, lines: List[str], page_num: int) -> str:
        """Extract a meaningful title from page content"""
        for line in lines:
            # Skip very short or very long lines
            if 10 <= len(line) <= 80:
                # Look for title-like patterns
                if (line[0].isupper() and 
                    not line.isupper() and 
                    not line.startswith('The ') and
                    not any(char.isdigit() for char in line[:20])):
                    return line
        
        # Fallback titles based on common patterns
        content_lower = ' '.join(lines).lower()
        if 'introduction' in content_lower:
            return "Introduction"
        elif 'method' in content_lower:
            return "Methods"
        elif 'result' in content_lower:
            return "Results"
        elif 'discussion' in content_lower:
            return "Discussion"
        elif 'conclusion' in content_lower:
            return "Conclusion"
        elif 'clinical' in content_lower:
            return "Clinical Course"
        elif 'case' in content_lower:
            return "Case Description"
        else:
            return f"Section {page_num}"

    def _determine_section_type(self, content: str, doc_type: str) -> str:
        """Enhanced section type determination with academic research focus"""
        content_lower = content.lower()
        
        # Enhanced section type indicators with academic research focus
        
        # Core academic sections
        if any(phrase in content_lower for phrase in ['core theme', 'main theme', 'central theme', 'key theme']):
            return 'core_theme'
        elif any(phrase in content_lower for phrase in ['problem statement', 'research problem', 'problem definition']):
            return 'problem_statement'
        elif any(phrase in content_lower for phrase in ['research gap', 'knowledge gap', 'gap in literature', 'literature gap']):
            return 'gap'
        elif any(phrase in content_lower for phrase in ['literature review', 'related work', 'previous work', 'literature section']):
            return 'literature_section'
        elif any(phrase in content_lower for phrase in ['contribution', 'contributions', 'novel contribution', 'key contribution']):
            return 'contribution'
        elif any(phrase in content_lower for phrase in ['risk assessment', 'risks', 'limitations', 'threats']):
            return 'risk'
        
        # Standard academic sections
        elif 'abstract' in content_lower:
            return 'abstract'
        elif any(word in content_lower for word in ['introduction', 'background', 'overview']):
            return 'introduction'
        elif any(word in content_lower for word in ['methodology', 'methods', 'approach', 'technique']):
            return 'methodology'
        elif any(word in content_lower for word in ['results', 'findings', 'outcomes']):
            return 'results'
        elif 'discussion' in content_lower:
            return 'discussion'
        elif any(word in content_lower for word in ['conclusion', 'conclusions', 'summary']):
            return 'conclusion'
        elif any(word in content_lower for word in ['references', 'bibliography', 'citations']):
            return 'references'
        
        # Medical/Clinical sections
        elif any(word in content_lower for word in ['clinical', 'course', 'patient']):
            return 'clinical_course'
        elif 'case' in content_lower:
            return 'case_description'
        
        # Default fallback
        else:
            return 'other'

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from section content"""
        key_points = []
        
        # Look for sentences with important indicators
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences[:10]:  # Only check first 10 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Look for key indicators
                if any(indicator in sentence.lower() for indicator in [
                    'significant', 'important', 'key', 'main', 'primary', 
                    'showed', 'demonstrated', 'found', 'revealed', 'indicated',
                    'diagnosed', 'treatment', 'conclusion', 'result'
                ]):
                    key_points.append(sentence)
                    if len(key_points) >= 3:  # Limit to 3 key points
                        break
        
        return key_points

    def _find_section_end(self, content: str, start_pos: int, section_index: int, total_sections: int) -> int:
        """Find where a section ends based on content analysis"""
        
        # If this is the last section, end at document end
        if section_index == total_sections - 1:
            return len(content)
        
        # Look for natural breaks like double newlines, page breaks, or new headings
        search_start = start_pos + 100  # Give some minimum content
        search_end = min(len(content), start_pos + 3000)  # Don't search too far
        
        # Look for common section separators
        separators = [
            r'\n\n[A-Z][A-Z\s]{5,}\n',  # All caps headings
            r'\n\n\d+\.\s+[A-Z]',        # Numbered sections
            r'=== PAGE \d+ ===',         # Page breaks
            r'\n\n[A-Z][a-z]+:',         # Colon-ended headings
        ]
        
        for separator in separators:
            matches = list(re.finditer(separator, content[search_start:search_end]))
            if matches:
                return search_start + matches[0].start()
        
        # Default: split roughly evenly
        remaining_content = len(content) - start_pos
        sections_remaining = total_sections - section_index
        return start_pos + (remaining_content // sections_remaining)

    def _estimate_page_number(self, content: str, position: int) -> int:
        """Estimate page number based on position in document"""
        
        # Look for explicit page markers
        page_markers = list(re.finditer(r'=== PAGE (\d+) ===', content[:position]))
        if page_markers:
            return int(page_markers[-1].group(1))
        
        # Estimate based on position (rough calculation)
        words_per_page = 400  # Average words per page
        words_before = len(content[:position].split())
        return max(1, words_before // words_per_page + 1)

    def _count_pages(self, content: str) -> int:
        """Count total pages in document"""
        page_markers = re.findall(r'=== PAGE (\d+) ===', content)
        if page_markers:
            return max(int(p) for p in page_markers)
        
        # Estimate based on word count
        total_words = len(content.split())
        return max(1, total_words // 400)

    def _create_basic_sections(self, content: str) -> List[DocumentSection]:
        """Create basic sections when LLM analysis fails"""
        
        sections = []
        
        # Look for page breaks first
        pages = re.split(r'=== PAGE \d+ ===', content)
        
        if len(pages) > 1:
            # Create sections based on pages
            current_pos = 0
            for i, page_content in enumerate(pages[1:], 1):  # Skip first empty split
                if page_content.strip():
                    # Try to find a meaningful title from the page content
                    lines = page_content.strip().split('\n')[:5]
                    title = self._extract_title_from_lines(lines) or f"Page {i}"
                    
                    section = DocumentSection(
                        id=f"page-{i}",
                        title=title,
                        start_position=current_pos,
                        end_position=current_pos + len(page_content),
                        content=page_content,
                        section_type="page",
                        confidence=0.8,
                        word_count=len(page_content.split()),
                        key_points=[],
                        page_number=i
                    )
                    sections.append(section)
                    current_pos += len(page_content)
        else:
            # Split into equal parts if no clear structure
            content_length = len(content)
            num_sections = min(5, max(1, content_length // 2000))  # Create 2-5 sections
            
            for i in range(num_sections):
                start = i * (content_length // num_sections)
                end = (i + 1) * (content_length // num_sections) if i < num_sections - 1 else content_length
                
                section_content = content[start:end]
                title = self._extract_title_from_content(section_content) or f"Section {i+1}"
                
                section = DocumentSection(
                    id=f"auto-section-{i+1}",
                    title=title,
                    start_position=start,
                    end_position=end,
                    content=section_content,
                    section_type="auto",
                    confidence=0.6,
                    word_count=len(section_content.split()),
                    key_points=[],
                    page_number=self._estimate_page_number(content, start)
                )
                sections.append(section)
        
        return sections

    def _extract_title_from_lines(self, lines: List[str]) -> Optional[str]:
        """Extract a meaningful title from the first few lines of content"""
        for line in lines:
            line = line.strip()
            if line and len(line) > 5 and len(line) < 100:
                # Check if it looks like a title (not all caps, has some structure)
                if not line.isupper() and any(c.isupper() for c in line):
                    return line
        return None

    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from content chunk"""
        lines = content.strip().split('\n')[:10]
        return self._extract_title_from_lines(lines)

    def _create_fallback_navigation(self, content: str, sections: List[DocumentSection]) -> Dict[str, Any]:
        """Create fallback navigation options"""
        
        fallback = {
            "page_navigation": [],
            "paragraph_navigation": [],
            "search_highlights": []
        }
        
        # Page-based navigation
        page_matches = list(re.finditer(r'=== PAGE (\d+) ===', content))
        for match in page_matches:
            fallback["page_navigation"].append({
                "page": int(match.group(1)),
                "position": match.start(),
                "title": f"Page {match.group(1)}"
            })
        
        # Paragraph-based navigation (for dense documents)
        paragraphs = content.split('\n\n')
        current_pos = 0
        for i, para in enumerate(paragraphs[:20]):  # Limit to first 20 paragraphs
            if len(para.strip()) > 100:  # Only substantial paragraphs
                title = para.strip()[:50] + "..." if len(para.strip()) > 50 else para.strip()
                fallback["paragraph_navigation"].append({
                    "id": f"para-{i+1}",
                    "title": title,
                    "position": current_pos
                })
            current_pos += len(para) + 2  # +2 for \n\n
        
        return fallback

    def _create_fallback_structure(self, content: str) -> DocumentStructure:
        """Create a basic fallback structure when LLM analysis completely fails"""
        
        sections = self._create_basic_sections(content)
        fallback_nav = self._create_fallback_navigation(content, sections)
        
        return DocumentStructure(
            sections=sections,
            document_type="unknown",
            total_pages=self._count_pages(content),
            total_words=len(content.split()),
            confidence=0.5,
            analysis_timestamp=datetime.now().isoformat(),
            fallback_navigation=fallback_nav
        )

    def analyze_legal_risks(self, content: str, sections: List[DocumentSection]) -> Dict[str, Any]:
        """Analyze legal risks in document sections for risk-based redlining"""
        
        risk_analysis = {
            "overall_risk_score": 0.0,
            "high_risk_sections": [],
            "medium_risk_sections": [],
            "low_risk_sections": [],
            "risk_highlights": []
        }
        
        content_lower = content.lower()
        
        # Analyze each section for legal risks
        for section in sections:
            section_content = section.content.lower()
            section_risk_score = 0.0
            risk_factors = []
            
            # Check for high-risk patterns
            for pattern in self.legal_risk_patterns["high_risk"]:
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                if matches:
                    section_risk_score += len(matches) * 3.0  # High weight
                    risk_factors.extend([f"High risk: {match}" for match in matches])
            
            # Check for medium-risk patterns
            for pattern in self.legal_risk_patterns["medium_risk"]:
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                if matches:
                    section_risk_score += len(matches) * 2.0  # Medium weight
                    risk_factors.extend([f"Medium risk: {match}" for match in matches])
            
            # Check for low-risk patterns
            for pattern in self.legal_risk_patterns["low_risk"]:
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                if matches:
                    section_risk_score += len(matches) * 0.5  # Low weight
                    risk_factors.extend([f"Low risk: {match}" for match in matches])
            
            # Categorize section by risk level
            section_risk_data = {
                "section_id": section.id,
                "section_title": section.title,
                "risk_score": section_risk_score,
                "risk_factors": risk_factors,
                "start_position": section.start_position,
                "end_position": section.end_position
            }
            
            if section_risk_score >= 6.0:
                risk_analysis["high_risk_sections"].append(section_risk_data)
                # Update section color for high risk
                section.section_type = "high_risk_clause"
            elif section_risk_score >= 3.0:
                risk_analysis["medium_risk_sections"].append(section_risk_data)
                section.section_type = "medium_risk_clause"
            elif section_risk_score > 0:
                risk_analysis["low_risk_sections"].append(section_risk_data)
                section.section_type = "low_risk_clause"
        
        # Calculate overall document risk score
        total_sections = len(sections)
        if total_sections > 0:
            high_risk_weight = len(risk_analysis["high_risk_sections"]) * 3
            medium_risk_weight = len(risk_analysis["medium_risk_sections"]) * 2
            low_risk_weight = len(risk_analysis["low_risk_sections"]) * 1
            
            risk_analysis["overall_risk_score"] = (
                (high_risk_weight + medium_risk_weight + low_risk_weight) / total_sections
            )
        
        # Find specific risk highlights for redlining
        for pattern_type, patterns in self.legal_risk_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    risk_analysis["risk_highlights"].append({
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "risk_level": pattern_type,
                        "color": self.section_colors.get(f"{pattern_type}_clause", "#ffcdd2")
                    })
        
        return risk_analysis

# Global instance
llm_analyzer = LLMDocumentAnalyzer()
