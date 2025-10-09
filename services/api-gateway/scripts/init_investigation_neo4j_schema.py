"""
Initialize Neo4j schema for Investigation Boards
Run this script to create necessary constraints and indexes
"""
import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def init_investigation_schema():
    """Create constraints and indexes for Investigation Board nodes"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    schema_queries = [
        # Constraints for unique IDs
        "CREATE CONSTRAINT investigation_board_id IF NOT EXISTS FOR (b:InvestigationBoard) REQUIRE b.id IS UNIQUE",
        "CREATE CONSTRAINT pinned_entity_id IF NOT EXISTS FOR (pe:PinnedEntity) REQUIRE pe.id IS UNIQUE",
        "CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (f:Finding) REQUIRE f.id IS UNIQUE",
        
        # Indexes for common queries
        "CREATE INDEX investigation_board_user IF NOT EXISTS FOR (b:InvestigationBoard) ON (b.user_id)",
        "CREATE INDEX investigation_board_space IF NOT EXISTS FOR (b:InvestigationBoard) ON (b.space_id)",
        "CREATE INDEX investigation_board_status IF NOT EXISTS FOR (b:InvestigationBoard) ON (b.status)",
        "CREATE INDEX pinned_entity_name IF NOT EXISTS FOR (pe:PinnedEntity) ON (pe.entity_name)",
        "CREATE INDEX finding_user IF NOT EXISTS FOR (f:Finding) ON (f.user_id)"
    ]
    
    try:
        with driver.session() as session:
            for query in schema_queries:
                try:
                    session.run(query)
                    print(f"✅ Executed: {query[:80]}...")
                except Exception as e:
                    # Constraint might already exist, that's fine
                    if "EquivalentSchemaRuleAlreadyExists" in str(e) or "already exists" in str(e):
                        print(f"⏭️  Already exists: {query[:80]}...")
                    else:
                        print(f"❌ Failed: {query[:80]}... - {e}")
        
        print("\n✅ Investigation Board Neo4j schema initialized successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize schema: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    print("🔧 Initializing Investigation Board Neo4j Schema...")
    init_investigation_schema()

