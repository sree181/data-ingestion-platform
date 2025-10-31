#!/usr/bin/env python3
"""
CORRECTED Entity Type Migration Script
Reclassifies existing entities in Neo4j based on their ACTUAL type property values
"""

import asyncio
import os
from neo4j import AsyncGraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping from ACTUAL Neo4j type property values to target labels
TYPE_TO_LABEL_MAPPING = {
    # Medical Conditions → Disease
    "Medical Condition": "Disease",
    "medical_condition": "Disease",
    "Adverse Reaction": "Disease",
    "Disease": "Disease",
    "Condition": "Disease",
    "Disorder": "Disease",
    "Syndrome": "Disease",
    "Symptom": "Disease",
    
    # Drugs & Chemicals → Drug
    "Drug": "Drug",
    "Medication": "Drug",
    "Pharmaceutical": "Drug",
    "Chemical": "Drug",
    "Chemical Substance": "Drug",
    "Substance": "Drug",
    "Compound": "Drug",
    "Vaccine": "Drug",
    
    # Medical Procedures → Procedure
    "Medical Procedure": "Procedure",
    "Medical Treatment": "Procedure",
    "Medical Test": "Procedure",
    "Procedure": "Procedure",
    "Treatment": "Procedure",
    "Therapy": "Procedure",
    "Intervention": "Procedure",
    "Surgery": "Procedure",
    "Test": "Procedure",
    "Exam": "Procedure",
    
    # Organizations → Organization
    "Organization": "Organization",
    "Org": "Organization",
    "Company": "Organization",
    "Manufacturer": "Organization",
    "Hospital": "Organization",
    "Institution": "Organization",
    
    # People → Person
    "Person": "Person",
    "Author": "Person",
    "Patient": "Person",
    "Doctor": "Person",
    "Physician": "Person",
    "Researcher": "Person",
    "Demographic Group": "Person",
}

async def migrate_entity_types_correct():
    """Migrate existing entities to enhanced types based on ACTUAL type property"""
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        async with driver.session() as session:
            # Get all Entity nodes with their type property
            logger.info("Fetching all Entity nodes...")
            result = await session.run("""
                MATCH (e:Entity)
                RETURN e.id as id, e.name as name, coalesce(e.type, e.entity_type, 'unknown') as type_property
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
                entity_name = entity['name'] or 'unknown'
                type_property = entity['type_property']
                
                # Determine new label from type property
                new_label = TYPE_TO_LABEL_MAPPING.get(type_property, None)
                
                if new_label and new_label != "Entity":
                    try:
                        # Remove Entity label and add new label
                        await session.run(f"""
                            MATCH (e:Entity {{id: $id}})
                            REMOVE e:Entity
                            SET e:{new_label}
                            RETURN e
                        """, {"id": entity_id})
                        
                        reclassified[new_label] += 1
                        if reclassified[new_label] <= 5:  # Log first 5 of each type
                            logger.info(f"✅ {type_property} → {new_label}: {entity_name[:50]}")
                    except Exception as e:
                        logger.error(f"Failed to reclassify {entity_name}: {e}")
                else:
                    reclassified["Entity"] += 1
                    if reclassified["Entity"] <= 3:
                        logger.debug(f"⚫ Keeping as Entity: {entity_name[:50]} (type: {type_property})")
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("MIGRATION SUMMARY")
            logger.info("="*60)
            logger.info(f"Total entities processed: {len(entities)}")
            logger.info(f"\n✅ Reclassified:")
            for label, count in reclassified.items():
                if count > 0:
                    percentage = (count / len(entities) * 100) if entities else 0
                    color = {"Drug": "🟢", "Disease": "🔴", "Procedure": "🔵", 
                            "Organization": "🟠", "Person": "🟣", "Entity": "⚫"}.get(label, "⚪")
                    logger.info(f"  {color} {label}: {count} ({percentage:.1f}%)")
            logger.info("="*60)
            
            # Verify the changes
            logger.info("\n🔍 Verifying migration...")
            verify_result = await session.run("""
                MATCH (n)
                WHERE NOT n:User AND NOT n:Document AND NOT n:ClinicalTrial AND NOT n:FDADocument
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            verify_data = await verify_result.data()
            
            logger.info("Current label distribution in Neo4j:")
            for row in verify_data:
                logger.info(f"  {row['label']}: {row['count']}")
            
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(migrate_entity_types_correct())

