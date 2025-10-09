# 🚀 Quick Start: Viewing Your Knowledge Graph

## ✅ Issue Fixed!

The 502 Bad Gateway errors were caused by nginx caching an old IP address for the `api-gateway` container. This has been resolved by restarting the frontend container.

## 🌐 Access Neo4j Browser

### Step 1: Open Neo4j Browser
Open your browser and navigate to: **http://localhost:7474**

### Step 2: Login
- **Username**: `neo4j`
- **Password**: `password123`

### Step 3: Run Your First Query

Try this query to see all your data:

```cypher
MATCH (n)
RETURN n
LIMIT 50
```

Click the **Run** button (play icon) or press **Ctrl+Enter**

## 📊 Useful Queries to Get Started

### 1. See What Data You Have
```cypher
MATCH (n)
RETURN labels(n) as Type, count(n) as Count
ORDER BY Count DESC
```

### 2. View All Documents
```cypher
MATCH (d:Document)
RETURN d.title as Title, d.publication_date as Date
LIMIT 10
```

### 3. View All Drugs
```cypher
MATCH (d:Drug)
RETURN d.name as Drug, d.confidence_score as Confidence
ORDER BY d.confidence_score DESC
LIMIT 10
```

### 4. View Drug-Disease Treatment Relationships
```cypher
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
RETURN drug.name as Drug, disease.name as Disease, r.efficacy as Efficacy
LIMIT 10
```

### 5. Find Pembrolizumab and Its Connections
```cypher
MATCH (p:Drug)-[r]-(connected)
WHERE p.name =~ '(?i).*pembrolizumab.*'
RETURN p, r, connected
LIMIT 50
```

### 6. View Knowledge Hub (2-hop connections from any entity)
```cypher
MATCH (center)-[r1*1..2]-(connected)
WHERE center.name =~ '(?i).*cancer.*'
RETURN center, r1, connected
LIMIT 100
```

## 🎨 Customizing the Visualization

1. **Change Node Colors**: Click on a node type in the left sidebar
2. **Change Node Size**: Adjust the size slider in the node style panel
3. **Change Node Caption**: Select which property to display (e.g., `name`, `title`)
4. **Expand Nodes**: Click on a node and press the "+" button to see its connections

## 📈 Check Your Data Stats

```cypher
CALL {
  MATCH (n) RETURN count(n) as nodes
  UNION
  MATCH ()-[r]->() RETURN count(r) as nodes
}
RETURN sum(nodes) as total
```

## 🔍 Search for Specific Terms

```cypher
MATCH (n)
WHERE n.name =~ '(?i).*immunotherapy.*'
RETURN n
LIMIT 25
```

## 🚨 Troubleshooting

### No Data Showing?
The knowledge graph is populated automatically when you ingest documents with AI processing. Your recent ingestion processed:
- **10 documents from Europe PMC**
- **Extracted 60+ entities**
- **Created 40+ relationships**

All this data is now in Neo4j!

### Want to See Schema?
```cypher
CALL db.schema.visualization()
```

### Want to Clear All Data?
```cypher
// WARNING: This deletes everything!
MATCH (n) DETACH DELETE n
```

## 📚 Full Documentation

See `NEO4J_VISUALIZATION_GUIDE.md` for:
- Advanced queries
- Export options
- Community detection
- Shortest path algorithms
- And more!

## 🎯 Your Application is Now Working!

- ✅ Frontend: http://localhost:3000
- ✅ API Gateway: http://localhost:8000
- ✅ Neo4j Browser: http://localhost:7474
- ✅ Login: admin@company.com / admin123

All services are healthy and ready to use!


