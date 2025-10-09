# Neo4j Knowledge Graph Visualization Guide

## 🌐 Access Neo4j Browser

1. Open your browser: `http://localhost:7474`
2. Login:
   - **Username**: `neo4j`
   - **Password**: `password123`

## 📊 Sample Cypher Queries to Explore Your Knowledge Graph

### 1. View All Nodes and Relationships
```cypher
MATCH (n)
RETURN n
LIMIT 100
```

### 2. Count Nodes by Type
```cypher
MATCH (n)
RETURN labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC
```

### 3. View All Drugs
```cypher
MATCH (d:Drug)
RETURN d
LIMIT 25
```

### 4. View All Diseases
```cypher
MATCH (d:Disease)
RETURN d
LIMIT 25
```

### 5. View Drug-Disease Relationships (Treatment Connections)
```cypher
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
RETURN drug, r, disease
LIMIT 25
```

### 6. View All Relationships
```cypher
MATCH ()-[r]->()
RETURN type(r) as RelationshipType, count(r) as Count
ORDER BY Count DESC
```

### 7. Find Pembrolizumab and Its Connections
```cypher
MATCH (p:Drug {name: "Pembrolizumab"})-[r]-(connected)
RETURN p, r, connected
LIMIT 50
```

### 8. Find All Drugs That Treat Cancer
```cypher
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
WHERE disease.name =~ '(?i).*cancer.*'
RETURN drug.name as Drug, disease.name as Disease, r.efficacy as Efficacy
ORDER BY r.efficacy DESC
LIMIT 25
```

### 9. View Documents and Their Mentioned Entities
```cypher
MATCH (doc:Document)-[r:MENTIONS]->(entity)
RETURN doc.title as Document, labels(entity) as EntityType, entity.name as Entity
LIMIT 25
```

### 10. Find Knowledge Hub Around an Entity (2-hop connections)
```cypher
MATCH (center:Drug {name: "Pembrolizumab"})-[r1*1..2]-(connected)
RETURN center, r1, connected
LIMIT 100
```

### 11. Find Research Papers
```cypher
MATCH (p:ResearchPaper)
RETURN p.title as Title, p.publication_date as Date
ORDER BY p.publication_date DESC
LIMIT 10
```

### 12. Find Organizations and Their Research
```cypher
MATCH (org:Organization)-[r]-(entity)
RETURN org.name as Organization, type(r) as Relationship, labels(entity) as EntityType
LIMIT 25
```

### 13. Find Entities with High Confidence
```cypher
MATCH (n)
WHERE n.confidence_score > 0.8
RETURN labels(n) as Type, n.name as Name, n.confidence_score as Confidence, n.source_count as Sources
ORDER BY n.confidence_score DESC
LIMIT 25
```

### 14. Find Entities from Multiple Sources (Consolidated)
```cypher
MATCH (n)
WHERE n.source_count > 1
RETURN labels(n) as Type, n.name as Name, n.source_count as Sources, n.sources as SourceList
ORDER BY n.source_count DESC
LIMIT 25
```

### 15. View Complete Subgraph Around a Disease
```cypher
MATCH path = (disease:Disease {name: "Triple Negative Breast Cancer"})-[*1..2]-(connected)
RETURN path
LIMIT 100
```

## 🎨 Visualization Tips

### Customize Node Colors
In Neo4j Browser, you can customize how nodes appear:
1. Click on a node type in the sidebar (e.g., Drug, Disease)
2. Choose a color, size, and caption property
3. Common caption properties:
   - `name` - Show the entity name
   - `title` - Show document titles
   - `confidence_score` - Show confidence values

### Expand Nodes
- Click on a node to see its details
- Click the "+" icon on a node to expand its relationships
- Double-click a node to expand all relationships

### Filter Results
- Use `WHERE` clauses to filter:
  ```cypher
  MATCH (d:Drug)
  WHERE d.confidence_score > 0.9
  RETURN d
  ```

### Aggregate Statistics
```cypher
MATCH (d:Drug)-[r:TREATS]->(disease:Disease)
RETURN d.name as Drug, count(disease) as DiseasesT reated
ORDER BY DiseasesT reated DESC
LIMIT 10
```

## 📈 Advanced Queries

### Find Shortest Path Between Two Entities
```cypher
MATCH path = shortestPath(
  (drug:Drug {name: "Pembrolizumab"})-[*]-(disease:Disease {name: "Triple Negative Breast Cancer"})
)
RETURN path
```

### Find All Paths of Length 2
```cypher
MATCH path = (start)-[*2]-(end)
WHERE id(start) < id(end)
RETURN path
LIMIT 25
```

### Community Detection (Find Clusters)
```cypher
CALL gds.louvain.stream('myGraph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS name, communityId
ORDER BY communityId ASC
```

## 🔍 Search for Specific Entities

### Search by Name (Case-Insensitive)
```cypher
MATCH (n)
WHERE n.name =~ '(?i).*pembrolizumab.*'
RETURN n
```

### Search Across All Properties
```cypher
MATCH (n)
WHERE any(prop in keys(n) WHERE toString(n[prop]) =~ '(?i).*cancer.*')
RETURN n
LIMIT 50
```

## 📊 Export Data

### Export to CSV
```cypher
// Export all drugs
MATCH (d:Drug)
RETURN d.name as Name, d.confidence_score as Confidence, d.source_count as Sources
```
Then click "Download" in the results panel.

### Export Relationships
```cypher
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
RETURN drug.name as Drug, disease.name as Disease, r.efficacy as Efficacy, r.confidence as Confidence
```

## 🎯 Quick Start Commands

After logging in, try these commands in order:

1. **See what you have**:
   ```cypher
   CALL db.schema.visualization()
   ```

2. **Count everything**:
   ```cypher
   MATCH (n) RETURN count(n) as TotalNodes
   ```

3. **View sample data**:
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

4. **Find interesting connections**:
   ```cypher
   MATCH path = (a)-[r]->(b)
   RETURN path
   LIMIT 50
   ```

## 🛠️ Troubleshooting

### No Data Showing?
Run the entity sync:
```python
python3 test_neo4j_integration.py
```

### Want Fresh Start?
```cypher
// WARNING: This deletes ALL data
MATCH (n) DETACH DELETE n
```

### Check Database Stats
```cypher
CALL apoc.meta.stats()
```

## 📚 Resources

- Neo4j Browser Guide: https://neo4j.com/developer/neo4j-browser/
- Cypher Query Language: https://neo4j.com/docs/cypher-manual/current/
- Graph Visualization Best Practices: https://neo4j.com/developer/guide-data-visualization/


