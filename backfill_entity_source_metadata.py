#!/usr/bin/env python3
"""
Backfill source metadata (has_pdf, has_external) for entities in Neo4j
based on their relationships to Document nodes.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

NEO4J_URL = "http://localhost:7474/db/neo4j/tx/commit"
NEO4J_AUTH = ("neo4j", "password")

async def execute_cypher(cypher: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a Cypher query via Neo4j HTTP API"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "statements": [
                {
                    "statement": cypher,
                    "parameters": params or {}
                }
            ]
        }
        
        response = await client.post(
            NEO4J_URL,
            json=payload,
            auth=NEO4J_AUTH
        )
        
        return response.json()

async def backfill_entity_sources():
    """
    Update entities with source metadata based on their document relationships.
    
    Logic:
    - has_pdf = TRUE if entity is mentioned in any Document with source='unknown' (PDFs)
    - has_external = TRUE if entity is mentioned in any Document with source != 'unknown'
    - source_types = list of unique sources
    - source_count = count of unique documents
    """
    
    print("🔄 Backfilling entity source metadata...")
    print("=" * 60)
    
    # Step 1: Update all entities with source metadata
    cypher = """
    MATCH (e)
    WHERE NOT e:Document 
      AND NOT e:User 
      AND NOT e:InvestigationBoard 
      AND NOT e:PinnedEntity
      AND NOT e:Finding
    OPTIONAL MATCH (e)-[:MENTIONS]-(d:Document)
    WITH e, 
         collect(DISTINCT d.source) as sources,
         count(DISTINCT d) as docCount,
         any(doc IN collect(d) WHERE doc.source = 'unknown') as hasPDF,
         any(doc IN collect(d) WHERE doc.source <> 'unknown' AND doc.source IS NOT NULL) as hasExternal
    SET e.has_pdf = hasPDF,
        e.has_external = hasExternal,
        e.source_types = sources,
        e.source_count = docCount
    RETURN labels(e)[0] as entityType, count(*) as updated
    """
    
    print("\n📊 Executing backfill query...")
    result = await execute_cypher(cypher)
    
    if result.get("errors"):
        print(f"\n❌ Errors: {result['errors']}")
        return
    
    # Print results
    print("\n✅ Backfill completed!")
    print("\nEntities updated by type:")
    print("-" * 40)
    
    if result.get("results") and result["results"][0].get("data"):
        for row_data in result["results"][0]["data"]:
            row = row_data.get("row", [])
            if len(row) >= 2:
                entity_type = row[0]
                count = row[1]
                print(f"  {entity_type:20s}: {count:4d} entities")
    
    # Step 2: Verify the results
    print("\n\n🔍 Verification:")
    print("-" * 40)
    
    verify_cypher = """
    MATCH (e)
    WHERE NOT e:Document AND NOT e:User AND NOT e:InvestigationBoard
    WITH labels(e)[0] as entityType, 
         sum(CASE WHEN e.has_pdf THEN 1 ELSE 0 END) as fromPDF,
         sum(CASE WHEN e.has_external THEN 1 ELSE 0 END) as fromExternal,
         sum(CASE WHEN e.has_pdf AND e.has_external THEN 1 ELSE 0 END) as crossSource,
         count(*) as total
    RETURN entityType, fromPDF, fromExternal, crossSource, total
    ORDER BY total DESC
    LIMIT 10
    """
    
    verify_result = await execute_cypher(verify_cypher)
    
    if verify_result.get("results") and verify_result["results"][0].get("data"):
        print(f"\n{'Entity Type':<20} {'PDF':<8} {'External':<10} {'Cross':<8} {'Total':<8}")
        print("-" * 60)
        for row_data in verify_result["results"][0]["data"]:
            row = row_data.get("row", [])
            if len(row) >= 5:
                print(f"{row[0]:<20} {row[1]:<8} {row[2]:<10} {row[3]:<8} {row[4]:<8}")
    
    print("\n✅ Source metadata backfill complete!")
    print("\n💡 Now the Knowledge Hub source filters will work correctly.")

if __name__ == "__main__":
    asyncio.run(backfill_entity_sources())

