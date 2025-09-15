"""
Entity Manager
Handles entity extraction, processing, and management
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

class EntityManager:
    def __init__(self):
        self.entity_types = {
            "PERSON": ["person", "individual", "people"],
            "ORGANIZATION": ["organization", "company", "corp", "inc", "ltd", "llc"],
            "LOCATION": ["location", "place", "city", "country", "state"],
            "EVENT": ["event", "meeting", "conference"],
            "PRODUCT": ["product", "service", "software"],
            "OTHER": ["other", "misc", "unknown"]
        }
    
    def normalize_entity_type(self, entity_type: str) -> str:
        """Normalize entity type to standard categories"""
        entity_type = entity_type.upper().strip()
        
        # Direct match
        if entity_type in self.entity_types:
            return entity_type
        
        # Fuzzy matching
        entity_lower = entity_type.lower()
        for standard_type, variants in self.entity_types.items():
            if any(variant in entity_lower for variant in variants):
                return standard_type
        
        return "OTHER"
    
    def clean_entity_name(self, entity_name: str) -> str:
        """Clean and normalize entity name"""
        if not entity_name:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', entity_name.strip())
        
        # Remove common prefixes/suffixes for organizations
        org_suffixes = ['Inc.', 'LLC', 'Corp.', 'Ltd.', 'Co.', 'Company']
        for suffix in org_suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        return cleaned
    
    def validate_entity(self, entity_name: str, entity_type: str) -> bool:
        """Validate if entity is worth enriching"""
        if not entity_name or len(entity_name.strip()) < 2:
            return False
        
        # Skip very common/generic terms
        generic_terms = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'them', 'they', 'their', 'there', 'here', 'where', 'when',
            'why', 'how', 'what', 'which', 'who', 'whom', 'whose'
        }
        
        if entity_name.lower().strip() in generic_terms:
            return False
        
        # Skip single characters
        if len(entity_name.strip()) == 1:
            return False
        
        # Skip numbers only
        if entity_name.strip().isdigit():
            return False
        
        return True
    
    def prioritize_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize entities for enrichment based on frequency and type"""
        
        # Define type priorities (higher = more important)
        type_priorities = {
            "ORGANIZATION": 3,
            "PERSON": 2,
            "LOCATION": 1,
            "EVENT": 1,
            "PRODUCT": 1,
            "OTHER": 0
        }
        
        # Calculate priority score
        for entity in entities:
            frequency = entity.get("frequency", 1)
            entity_type = entity.get("type", "OTHER")
            type_priority = type_priorities.get(entity_type, 0)
            
            # Priority score: frequency * type_weight + base_type_score
            entity["priority_score"] = (frequency * 10) + (type_priority * 5)
        
        # Sort by priority score (descending)
        return sorted(entities, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    def group_similar_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group similar entities to avoid duplicate enrichment"""
        grouped = {}
        
        for entity in entities:
            entity_name = entity.get("name", "").lower().strip()
            entity_type = entity.get("type", "OTHER")
            
            # Create a normalized key
            normalized_key = f"{entity_name}_{entity_type}"
            
            if normalized_key in grouped:
                # Merge with existing entity
                grouped[normalized_key]["frequency"] += entity.get("frequency", 1)
                grouped[normalized_key]["documents"].extend(entity.get("documents", []))
            else:
                grouped[normalized_key] = entity.copy()
        
        return list(grouped.values())
    
    def extract_entity_relationships(self, entities: List[Dict[str, Any]], document_content: str) -> List[Dict[str, Any]]:
        """Extract potential relationships between entities"""
        relationships = []
        
        # Simple co-occurrence based relationship detection
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1["type"] != entity2["type"]:  # Only cross-type relationships
                    # Check if entities appear close to each other in text
                    if self._entities_are_related(entity1["name"], entity2["name"], document_content):
                        relationships.append({
                            "entity1": entity1["name"],
                            "entity1_type": entity1["type"],
                            "entity2": entity2["name"],
                            "entity2_type": entity2["type"],
                            "relationship_type": self._infer_relationship_type(entity1["type"], entity2["type"]),
                            "confidence": 0.7  # Basic confidence
                        })
        
        return relationships
    
    def _entities_are_related(self, entity1: str, entity2: str, content: str, window_size: int = 100) -> bool:
        """Check if two entities appear close to each other in content"""
        if not content:
            return False
        
        content_lower = content.lower()
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()
        
        # Find all occurrences of both entities
        entity1_positions = [m.start() for m in re.finditer(re.escape(entity1_lower), content_lower)]
        entity2_positions = [m.start() for m in re.finditer(re.escape(entity2_lower), content_lower)]
        
        # Check if any occurrences are within the window
        for pos1 in entity1_positions:
            for pos2 in entity2_positions:
                if abs(pos1 - pos2) <= window_size:
                    return True
        
        return False
    
    def _infer_relationship_type(self, type1: str, type2: str) -> str:
        """Infer relationship type between two entity types"""
        relationship_map = {
            ("PERSON", "ORGANIZATION"): "WORKS_AT",
            ("ORGANIZATION", "PERSON"): "EMPLOYS",
            ("PERSON", "LOCATION"): "LOCATED_IN",
            ("ORGANIZATION", "LOCATION"): "HEADQUARTERED_IN",
            ("PERSON", "EVENT"): "ATTENDED",
            ("ORGANIZATION", "EVENT"): "PARTICIPATED_IN",
            ("PERSON", "PRODUCT"): "CREATED",
            ("ORGANIZATION", "PRODUCT"): "PRODUCES"
        }
        
        return relationship_map.get((type1, type2), "RELATED_TO")