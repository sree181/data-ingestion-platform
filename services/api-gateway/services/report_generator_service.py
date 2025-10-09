"""
AI-Powered Investigation Report Generator
Generates comprehensive, cohesive narrative reports from Investigation Boards
"""
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import httpx
from collections import Counter

logger = logging.getLogger(__name__)


class ReportGeneratorService:
    """Service for generating AI-powered investigation reports with cohesive narratives"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = bool(self.openai_key)
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    
    async def generate_report(
        self, 
        board_data: Dict[str, Any],
        documents: List[Dict[str, Any]],
        format: str = "markdown",
        template: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, cohesive investigation report
        """
        try:
            logger.info(f"Generating {template} report in {format} format")
            
            # Extract key information
            entities = self._extract_entities(board_data)
            relationships = self._extract_relationships(board_data)
            findings = self._extract_findings(board_data)
            
            # Fetch documents from Elasticsearch directly (more comprehensive)
            all_documents = await self._fetch_comprehensive_documents(entities)
            
            logger.info(f"Fetched {len(all_documents)} documents for report")
            
            # Analyze documents
            doc_analysis = self._analyze_documents(all_documents, entities)
            
            # Generate cohesive narrative sections
            report_sections = await self._generate_cohesive_narrative(
                board_data=board_data,
                entities=entities,
                relationships=relationships,
                findings=findings,
                doc_analysis=doc_analysis,
                template=template
            )
            
            # Format report
            formatted_report = self._format_report(report_sections, board_data, entities, relationships, doc_analysis, findings, format)
            
            return {
                "success": True,
                "report": formatted_report,
                "metadata": {
                    "board_title": board_data.get("title", "Untitled Investigation"),
                    "generated_at": datetime.now().isoformat(),
                    "entity_count": len(entities),
                    "relationship_count": len(relationships),
                    "finding_count": len(findings),
                    "source_document_count": len(all_documents),
                    "format": format,
                    "template": template
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_comprehensive_documents(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch documents from Elasticsearch with comprehensive search"""
        try:
            entity_names = [e["name"] for e in entities]
            
            # Build comprehensive query
            should_clauses = []
            for name in entity_names:
                should_clauses.extend([
                    {"match": {"content": {"query": name, "boost": 2.0}}},
                    {"match": {"openai_entities.name": {"query": name, "boost": 3.0}}},
                    {"match": {"title": {"query": name, "boost": 1.5}}}
                ])
            
            query = {
                "query": {
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                },
                "size": 100,  # Get up to 100 documents
                "_source": ["title", "content", "openai_entities", "openai_relationships", 
                           "openai_summary", "source_type", "document_id", "snippets"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.es_url}/documents/_search", json=query)
                response.raise_for_status()
                results = response.json()
            
            documents = []
            for hit in results.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                documents.append({
                    "document_id": source.get("document_id", hit.get("_id")),
                    "title": source.get("title", "Untitled"),
                    "content": source.get("content", "")[:2000],  # First 2000 chars
                    "openai_entities": source.get("openai_entities", []),
                    "openai_relationships": source.get("openai_relationships", []),
                    "openai_summary": source.get("openai_summary", ""),
                    "source_type": source.get("source_type", "PDF"),
                    "snippets": source.get("snippets", [])
                })
            
            logger.info(f"Found {len(documents)} documents in Elasticsearch")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to fetch documents from Elasticsearch: {e}")
            return []
    
    def _extract_entities(self, board_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and enrich entity data"""
        entities = []
        for ew in board_data.get("pinned_entities", []):
            if ew.get("entity"):
                entity = ew["entity"]
                entities.append({
                    "name": entity.get("entity_name"),
                    "type": entity.get("entity_type", "Entity"),
                    "pin_reason": entity.get("pin_reason"),
                    "created_at": entity.get("created_at"),
                    "findings": ew.get("findings", [])
                })
        return entities
    
    def _extract_relationships(self, board_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationship data"""
        relationships = []
        
        # Map pin IDs to entity names
        id_to_name = {}
        for ew in board_data.get("pinned_entities", []):
            if ew.get("entity"):
                id_to_name[ew["entity"]["id"]] = ew["entity"]["entity_name"]
        
        for conn in board_data.get("connections", []):
            source_id = conn.get("source_id")
            target_id = conn.get("target_id")
            
            if source_id and target_id:
                relationships.append({
                    "source": id_to_name.get(source_id, "Unknown"),
                    "target": id_to_name.get(target_id, "Unknown"),
                    "type": conn.get("connection_type", "related_to"),
                    "notes": conn.get("notes"),
                    "confidence": conn.get("confidence", 0.7),
                    "created_at": conn.get("created_at")
                })
        return relationships
    
    def _extract_findings(self, board_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all findings from entities"""
        findings = []
        for ew in board_data.get("pinned_entities", []):
            entity_name = ew.get("entity", {}).get("entity_name")
            for finding in ew.get("findings", []):
                findings.append({
                    "entity": entity_name,
                    "content": finding.get("content"),
                    "created_at": finding.get("created_at")
                })
        return findings
    
    def _analyze_documents(
        self, 
        documents: List[Dict[str, Any]], 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze document corpus for insights"""
        entity_names = [e["name"].lower() for e in entities]
        
        # Document type distribution
        source_types = Counter([doc.get("source_type", "PDF") for doc in documents])
        
        # Entity mentions across documents
        entity_mentions = {}
        for entity in entities:
            name = entity["name"]
            name_lower = name.lower()
            mentions = sum(1 for doc in documents 
                          if name_lower in doc.get("content", "").lower() or
                             any(ent.get("name", "").lower() == name_lower 
                                 for ent in doc.get("openai_entities", [])))
            entity_mentions[name] = mentions
        
        # Extract key snippets
        key_excerpts = []
        for doc in documents[:10]:
            content = doc.get("content", "")
            summary = doc.get("openai_summary", "")
            
            # Find relevant snippet
            snippet = summary if summary else (content[:300] if content else "")
            
            if snippet:
                key_excerpts.append({
                    "document": doc.get("title", "Untitled"),
                    "snippet": snippet,
                    "source_type": doc.get("source_type", "PDF")
                })
        
        # Extract relationships from documents
        doc_relationships = []
        for doc in documents:
            doc_rels = doc.get("openai_relationships", [])
            for rel in doc_rels:
                if rel.get("source") and rel.get("target"):
                    doc_relationships.append(rel)
        
        return {
            "total_documents": len(documents),
            "source_type_distribution": dict(source_types),
            "entity_mentions": entity_mentions,
            "key_excerpts": key_excerpts,
            "document_relationships": doc_relationships
        }
    
    async def _generate_cohesive_narrative(
        self,
        board_data: Dict[str, Any],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any],
        template: str
    ) -> Dict[str, str]:
        """Generate cohesive narrative sections using LLM"""
        
        sections = {}
        
        # Generate comprehensive prompt for full narrative
        full_context = self._build_full_context(
            board_data, entities, relationships, findings, doc_analysis
        )
        
        # 1. Executive Summary - Cohesive narrative
        sections["executive_summary"] = await self._generate_executive_summary_narrative(full_context)
        
        # 2. Entity Analysis - Cohesive analysis for each entity
        sections["entity_analysis"] = await self._generate_entity_narratives(
            entities, relationships, doc_analysis
        )
        
        # 3. Relationship Analysis - Cohesive network narrative
        sections["relationship_analysis"] = await self._generate_relationship_narrative(
            relationships, entities, doc_analysis
        )
        
        # 4. Findings Synthesis - Cohesive synthesis
        sections["findings_synthesis"] = await self._generate_findings_narrative(
            findings, entities, relationships, doc_analysis
        )
        
        # 5. Insights & Recommendations - Strategic narrative
        sections["insights"] = await self._generate_insights_narrative(full_context)
        
        return sections
    
    def _build_full_context(
        self,
        board_data: Dict[str, Any],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any]
    ) -> str:
        """Build comprehensive context for LLM"""
        
        context = f"""INVESTIGATION CONTEXT:

Title: {board_data.get('title', 'Untitled Investigation')}
Description: {board_data.get('description', 'No description provided')}

ENTITIES ({len(entities)}):
"""
        for e in entities:
            context += f"- {e['name']} ({e['type']})"
            if e.get('pin_reason'):
                context += f": {e['pin_reason']}"
            context += f"\n  Documents mentioning this: {doc_analysis['entity_mentions'].get(e['name'], 0)}\n"
        
        context += f"\nRELATIONSHIPS ({len(relationships)}):\n"
        for r in relationships:
            context += f"- {r['source']} --[{r['type']}]--> {r['target']}"
            if r.get('notes'):
                context += f" (Evidence: {r['notes']})"
            context += "\n"
        
        context += f"\nUSER FINDINGS ({len(findings)}):\n"
        for f in findings:
            context += f"- [{f['entity']}] {f['content']}\n"
        
        context += f"\nSOURCE DOCUMENTS: {doc_analysis['total_documents']} documents analyzed\n"
        context += f"Sources: {', '.join(doc_analysis['source_type_distribution'].keys())}\n"
        
        if doc_analysis['key_excerpts']:
            context += "\nKEY DOCUMENT EXCERPTS:\n"
            for i, exc in enumerate(doc_analysis['key_excerpts'][:3], 1):
                context += f"{i}. {exc['document']}: {exc['snippet'][:200]}...\n"
        
        if doc_analysis.get('document_relationships'):
            context += f"\nRELATIONSHIPS FROM DOCUMENTS:\n"
            for rel in doc_analysis['document_relationships'][:5]:
                context += f"- {rel.get('source')} --[{rel.get('type')}]--> {rel.get('target')}\n"
        
        return context
    
    async def _generate_executive_summary_narrative(self, full_context: str) -> str:
        """Generate cohesive executive summary narrative"""
        
        prompt = f"""{full_context}

Based on this investigation, write a cohesive, professional executive summary (3-4 sentences) that:
1. Describes what was investigated and why it matters
2. Highlights the key entities and their relationships
3. Summarizes the most significant findings or patterns
4. Provides context on the evidence base

Write in a clear, professional tone suitable for executive stakeholders. Make it read like a coherent narrative, not bullet points."""

        return await self._call_llm(prompt, max_tokens=400)
    
    async def _generate_entity_narratives(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any]
    ) -> str:
        """Generate cohesive narratives for each entity"""
        
        narratives = []
        
        for entity in entities:
            # Find relationships involving this entity
            entity_rels = [r for r in relationships 
                          if r['source'] == entity['name'] or r['target'] == entity['name']]
            
            mentions = doc_analysis['entity_mentions'].get(entity['name'], 0)
            
            prompt = f"""Write a cohesive 2-3 sentence analysis for this entity in an investigation:

Entity: {entity['name']} ({entity['type']})
Why it was included: {entity.get('pin_reason', 'Part of the investigation')}
Document mentions: {mentions} times
Connected entities: {len(entity_rels)} relationships

Relationships:
{chr(10).join([f"- {r['source']} --[{r['type']}]--> {r['target']}" for r in entity_rels]) if entity_rels else '- No documented relationships yet'}

Write a professional analysis that explains this entity's role and significance in the investigation. Write as a cohesive narrative paragraph."""

            narrative = await self._call_llm(prompt, max_tokens=250)
            
            narratives.append(f"**{entity['name']}** ({entity['type']})\n\n{narrative}\n\n"
                            f"*Evidence base: {mentions} document mentions, {len(entity_rels)} documented relationships*")
        
        return "\n\n".join(narratives)
    
    async def _generate_relationship_narrative(
        self,
        relationships: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any]
    ) -> str:
        """Generate cohesive narrative about the relationship network"""
        
        if not relationships:
            return "This investigation has not yet established explicit relationships between the entities under study. Further analysis of the source documents may reveal connections."
        
        # Group relationships by type
        rel_by_type = {}
        for rel in relationships:
            rel_type = rel['type']
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append(rel)
        
        prompt = f"""Write a cohesive narrative analyzing this relationship network:

Total relationships: {len(relationships)}

Relationship breakdown:
{chr(10).join([f"- {rtype}: {len(rels)} connections" for rtype, rels in rel_by_type.items()])}

Key relationships:
{chr(10).join([f"- {r['source']} --[{r['type']}]--> {r['target']}" + (f" (Evidence: {r['notes']})" if r.get('notes') else '') for r in relationships[:10]])}

Write a 3-4 sentence cohesive narrative that:
1. Describes the overall structure and pattern of the network
2. Highlights the most significant or revealing connections
3. Notes any central entities or clusters
4. Comments on the strength of evidence for these relationships

Write as a flowing narrative paragraph, not bullet points."""

        narrative = await self._call_llm(prompt, max_tokens=400)
        
        # Add relationship list
        narrative += "\n\n**Documented Connections:**\n\n"
        for rel in relationships:
            narrative += f"- **{rel['source']}** → **{rel['target']}** (_{rel['type']}_)"
            if rel.get('notes'):
                narrative += f"\n  - Evidence: {rel['notes']}"
            narrative += "\n"
        
        return narrative
    
    async def _generate_findings_narrative(
        self,
        findings: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any]
    ) -> str:
        """Generate cohesive synthesis of user findings"""
        
        if not findings:
            return "No specific findings have been documented by the investigator yet. As the investigation progresses, key observations and conclusions should be recorded here."
        
        # Group findings by entity
        findings_by_entity = {}
        for finding in findings:
            entity = finding['entity']
            if entity not in findings_by_entity:
                findings_by_entity[entity] = []
            findings_by_entity[entity].append(finding)
        
        prompt = f"""Write a cohesive synthesis of these investigation findings:

{chr(10).join([f"[{f['entity']}] {f['content']}" for f in findings])}

Write a 2-3 sentence narrative that:
1. Synthesizes the key findings into a coherent story
2. Notes any patterns or themes across the findings
3. Connects findings to the entities and relationships in the investigation

Write as a flowing narrative, not a list."""

        synthesis = await self._call_llm(prompt, max_tokens=300)
        
        # Add structured findings
        synthesis += "\n\n**Detailed Findings:**\n\n"
        for entity, ent_findings in findings_by_entity.items():
            synthesis += f"**{entity}**\n"
            for i, finding in enumerate(ent_findings, 1):
                synthesis += f"{i}. {finding['content']}\n"
            synthesis += "\n"
        
        return synthesis
    
    async def _generate_insights_narrative(self, full_context: str) -> str:
        """Generate strategic insights and recommendations"""
        
        prompt = f"""{full_context}

Based on this investigation, provide strategic insights and recommendations. Write a cohesive narrative (4-5 sentences) that:

1. Identifies 2-3 key insights or patterns from the investigation
2. Assesses what has been learned and what remains unclear
3. Provides 2-3 specific, actionable recommendations for next steps
4. Comments on the strength and limitations of the evidence

Write as a professional strategic analysis suitable for decision-makers. Use a flowing narrative style."""

        return await self._call_llm(prompt, max_tokens=500)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM (OpenAI or Ollama) for text generation"""
        
        try:
            if self.use_openai:
                return await self._call_openai(prompt, max_tokens)
            else:
                return await self._call_ollama(prompt, max_tokens)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return informative fallback instead of error message
            return f"[AI analysis is being generated. Please ensure LLM service is running.]"
    
    async def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
    
    async def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call Ollama (local LLM)"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            result = response.json()
            return result.get("response", "").strip()
    
    def _format_report(
        self, 
        sections: Dict[str, str],
        board_data: Dict[str, Any],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any],
        findings: List[Dict[str, Any]],
        format: str
    ) -> str:
        """Format report sections into final cohesive output"""
        
        if format == "markdown":
            return self._format_markdown(sections, board_data, entities, relationships, doc_analysis, findings)
        elif format == "json":
            return json.dumps(sections, indent=2)
        else:
            return self._format_markdown(sections, board_data, entities, relationships, doc_analysis, findings)
    
    def _format_markdown(
        self,
        sections: Dict[str, str],
        board_data: Dict[str, Any],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        doc_analysis: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> str:
        """Format report as cohesive Markdown document"""
        
        report = f"""# {board_data.get('title', 'Investigation Report')}

*Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}*

---

## Executive Summary

{sections.get('executive_summary', '')}

---

## Investigation Scope

**Purpose:** {board_data.get('description', 'Systematic analysis of entities and their relationships')}

**Timeline:** Created {datetime.fromisoformat(board_data.get('created_at', datetime.now().isoformat())).strftime("%B %d, %Y")}

**Scale of Analysis:**
- {len(entities)} entities under investigation
- {len(relationships)} documented relationships
- {doc_analysis['total_documents']} source documents analyzed
- {', '.join(doc_analysis['source_type_distribution'].keys()) if doc_analysis['source_type_distribution'] else 'Multiple data sources'}

---

## Entity Analysis

{sections.get('entity_analysis', '')}

---

## Relationship Network

{sections.get('relationship_analysis', '')}

---

## Key Findings & Observations

{sections.get('findings_synthesis', '')}

---

## Evidence Base

This investigation draws upon **{doc_analysis['total_documents']} source documents** from the following sources:

"""
        
        if doc_analysis['source_type_distribution']:
            for source_type, count in doc_analysis['source_type_distribution'].items():
                report += f"- **{source_type}**: {count} documents\n"
        else:
            report += "- Investigation based on knowledge graph analysis and manual documentation\n"
        
        if doc_analysis['key_excerpts']:
            report += "\n**Representative Document Excerpts:**\n\n"
            for i, exc in enumerate(doc_analysis['key_excerpts'][:5], 1):
                report += f"**{i}. {exc['document']}** ({exc['source_type']})\n\n"
                report += f"> {exc['snippet']}\n\n"
        
        report += f"""
---

## Strategic Insights & Recommendations

{sections.get('insights', '')}

---

## Methodology

This investigation employed a systematic approach combining:

- **Entity Identification**: {len(entities)} key entities identified through domain expertise and AI-assisted extraction
- **Relationship Mapping**: {len(relationships)} connections documented through document analysis, knowledge graph traversal, and manual validation
- **Evidence Collection**: {doc_analysis['total_documents']} source documents retrieved and analyzed
- **Synthesis**: AI-powered narrative generation combined with human oversight and domain expertise

All findings are grounded in documentary evidence and subject to ongoing validation as the investigation proceeds.

---

*Report generated by Enterprise Document Intelligence Platform*  
*Investigation Board: {board_data.get('title')}*  
*Report ID: {board_data.get('id', 'N/A')}*
"""
        return report
