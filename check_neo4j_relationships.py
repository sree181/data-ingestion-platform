#!/usr/bin/env python3
"""
Quick script to check Neo4j relationship types
"""
import os
import requests
from requests.auth import HTTPBasicAuth

# Neo4j credentials
NEO4J_URL = os.getenv("NEO4J_URL", "http://neo4j:7474")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "pharmacovigilance2024")

# Query to get relationship types
cypher = """
MATCH ()-[r]->()
WHERE NOT r:User AND NOT r:InvestigationBoard
RETURN DISTINCT type(r) as rel_type, 
       r.predicate as predicate,
       count(*) as count
ORDER BY count DESC
LIMIT 20
"""

try:
    response = requests.post(
        f"{NEO4J_URL}/db/data/transaction/commit",
        json={
            "statements": [{
                "statement": cypher,
                "resultDataContents": ["row"]
            }]
        },
        auth=HTTPBasicAuth(NEO4J_USER, NEO4J_PASSWORD),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('results') and data['results'][0].get('data'):
            print("\n" + "="*80)
            print("RELATIONSHIP TYPES IN NEO4J")
            print("="*80)
            print(f"{'Type':<30} {'Predicate':<30} {'Count':>10}")
            print("-"*80)
            
            for row in data['results'][0]['data']:
                rel_type = row['row'][0]
                predicate = row['row'][1] or 'NULL'
                count = row['row'][2]
                print(f"{rel_type:<30} {predicate:<30} {count:>10}")
        else:
            print("No relationships found")
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Failed to query Neo4j: {e}")

