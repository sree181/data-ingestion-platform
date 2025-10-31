#!/usr/bin/env python3
"""
Entity Type Migration Script
Reclassifies existing entities in Neo4j with enhanced pharmacovigilance types
"""

import asyncio
import os
from neo4j import AsyncGraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced mapping (same as neo4j_service.py)
LABEL_MAPPING = {
    # Medical/Pharmacovigilance Entities
    "DRUG": "Drug",
    "MEDICATION": "Drug",
    "PHARMACEUTICAL": "Drug",
    "CHEMICAL": "Drug",
    "SUBSTANCE": "Drug",
    "COMPOUND": "Drug",
    
    # Diseases & Conditions
    "DISEASE": "Disease",
    "CONDITION": "Disease",
    "DISORDER": "Disease",
    "SYNDROME": "Disease",
    "SYMPTOM": "Disease",
    "ADVERSE_EVENT": "Disease",
    "SIDE_EFFECT": "Disease",
    "ADVERSE EVENT": "Disease",
    
    # Medical Procedures
    "PROCEDURE": "Procedure",
    "TREATMENT": "Procedure",
    "THERAPY": "Procedure",
    "INTERVENTION": "Procedure",
    "SURGERY": "Procedure",
    "TEST": "Procedure",
    "EXAM": "Procedure",
    
    # Organizations
    "ORG": "Organization",
    "ORGANIZATION": "Organization",
    "COMPANY": "Organization",
    "MANUFACTURER": "Organization",
    "HOSPITAL": "Organization",
    "INSTITUTION": "Organization",
    
    # People
    "PERSON": "Person",
    "PATIENT": "Person",
    "DOCTOR": "Person",
    "PHYSICIAN": "Person",
    "RESEARCHER": "Person",
}

# Keyword-based inference for untyped entities
ENTITY_NAME_PATTERNS = {
    "Drug": [
        "drug", "medication", "pharmaceutical", "compound", 
        "mg", "dose", "tablet", "capsule", "injection", "therapy",
        "acetaminophen", "ibuprofen", "aspirin", "toxicity"
    ],
    "Disease": [
        "disease", "syndrome", "disorder", "condition",
        "adverse event", "reaction", "toxicity", "injury",
        "hepatotoxicity", "nephrotoxicity", "cardiotoxicity",
        "failure", "damage", "dysfunction"
    ],
    "Procedure": [
        "treatment", "surgery", "procedure", "test",
        "screening", "intervention", "therapy", "examination"
    ],
}

async def migrate_entity_types():
    """Migrate existing entities to enhanced types"""
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        async with driver.session() as session:
            # Get all Entity nodes
            logger.info("Fetching all Entity nodes...")
            result = await session.run("""
                MATCH (e:Entity)
                RETURN e.id as id, e.name as name, e.type as type, labels(e) as labels
            """)
            
            entities = await result.data()
            logger.info(f"Found {len(entities)} Entity nodes to process")
            
            # Reclassify each entity
            reclassified = {
                "Drug": 0,
                "Disease": 0,
                "Procedure": 0,
                "Organization": 0,
                "Person": 0,
                "Entity": 0
            }
            
            for entity in entities:
                entity_id = entity['id']
                entity_name = (entity['name'] or '').lower()
                entity_type = (entity['type'] or '').upper()
                
                # Determine new label
                new_label = None
                
                # 1. Try direct type mapping
                if entity_type and entity_type in LABEL_MAPPING:
                    new_label = LABEL_MAPPING[entity_type]
                    logger.info(f"Direct mapping: {entity_name} ({entity_type}) → {new_label}")
                
                # 2. Try keyword-based inference
                if not new_label or new_label == "Entity":
                    for label, keywords in ENTITY_NAME_PATTERNS.items():
                        if any(keyword in entity_name for keyword in keywords):
                            new_label = label
                            logger.info(f"Keyword inference: {entity_name} → {new_label}")
                            break
                
                # 3. Fallback to Entity
                if not new_label:
                    new_label = "Entity"
                
                # Update node with new label
                if new_label and new_label != "Entity":
                    try:
                        await session.run(f"""
                            MATCH (e:Entity {{id: $id}})
                            REMOVE e:Entity
                            SET e:{new_label}
                            RETURN e
                        """, {"id": entity_id})
                        
                        reclassified[new_label] += 1
                        logger.debug(f"Reclassified: {entity_name} → {new_label}")
                    except Exception as e:
                        logger.error(f"Failed to reclassify {entity_name}: {e}")
                else:
                    reclassified["Entity"] += 1
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("MIGRATION SUMMARY")
            logger.info("="*50)
            logger.info(f"Total entities processed: {len(entities)}")
            logger.info(f"\nReclassified:")
            for label, count in reclassified.items():
                if count > 0:
                    percentage = (count / len(entities) * 100) if entities else 0
                    logger.info(f"  {label}: {count} ({percentage:.1f}%)")
            logger.info("="*50)
            
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(migrate_entity_types())

