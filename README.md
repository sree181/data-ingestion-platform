# Data Ingestion Platform - Working Version

## 🚀 Status: STABLE WORKING VERSION
**This is the confirmed working version with all 55+ documents accessible and all features functional.**

## 📋 Overview
Production-ready data ingestion platform with document processing, search, chat functionality, and lease management capabilities.

## ✅ Confirmed Working Features
- **Document Library**: Displays all ingested documents (55+ confirmed)
- **Project Spaces**: Functional project organization
- **Document Chat**: AI-powered document Q&A
- **Investigation**: Document analysis tools
- **Entity Enrichment**: Automated entity extraction
- **Lease Management**: Specialized lease document processing
- **Search**: Full-text search across all documents
- **Dashboard**: Analytics and metrics

## 🛠 Architecture
- **Frontend**: React + Material-UI (Port 3002)
- **API Gateway**: FastAPI with unified endpoints (Port 8000)
- **Document Processing**: LlamaParse + AI enrichment
- **Search**: Elasticsearch for document indexing
- **Knowledge Graph**: Neo4j for entity relationships
- **Storage**: MinIO for file storage
- **Database**: PostgreSQL for metadata
- **Streaming**: Apache Kafka for real-time processing
- **Monitoring**: Prometheus + Grafana

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM (for Elasticsearch)
- 20GB free disk space

### Start the Platform
```bash
# Start all services
docker-compose -f docker-compose-optimized.yml up -d

# Check service status
docker-compose -f docker-compose-optimized.yml ps

# View logs
docker-compose -f docker-compose-optimized.yml logs -f
```

### Access Points
- **Frontend**: http://localhost:3002
- **API Gateway**: http://localhost:8000
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **Neo4j Browser**: http://localhost:7474
- **MinIO Console**: http://localhost:9001
- **Grafana**: http://localhost:3001

## 📊 Service Ports
| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3002 | Web UI |
| API Gateway | 8000 | Main API |
| Elasticsearch | 9200 | Search & Indexing |
| Neo4j | 7474/7687 | Knowledge Graph |
| PostgreSQL | 5432 | Metadata DB |
| MinIO | 9000/9001 | Object Storage |
| Kafka | 9092 | Message Streaming |
| Redis | 6379 | Caching |
| Grafana | 3001 | Monitoring |
| Prometheus | 9090 | Metrics |

## 🔧 Configuration
- Main config: `docker-compose-optimized.yml`
- API Gateway: `services/api-gateway/main.py` (working_main.py version)
- Frontend: React app with Material-UI components
- No security environment variables (clean setup)

## 📁 Key Directories
```
├── services/
│   ├── api-gateway/          # Main API service
│   ├── document-processor/   # Document ingestion
│   ├── document-chat-service/# AI chat functionality
│   ├── lease-obligation-extractor/  # Lease processing
│   └── lease-comparison-engine/     # Lease analysis
├── frontend/                 # React web application
├── sql/                     # Database initialization
└── docker-compose-optimized.yml    # Main deployment config
```

## 🗃 Data Storage
- **Documents**: Elasticsearch `documents` index (55+ documents confirmed)
- **Metadata**: PostgreSQL database
- **Files**: MinIO object storage
- **Knowledge Graph**: Neo4j graph database

## 🔍 API Endpoints
- `GET /api/v1/spaces` - Project spaces
- `GET /api/v1/search` - Document search
- `POST /api/v1/search` - Advanced search
- `GET /api/v1/analytics/dashboard` - Dashboard data
- `POST /api/v1/upload` - Document upload
- `POST /api/v1/chat` - Document chat

## 🚨 Important Notes
- **DO NOT MODIFY THIS MAIN BRANCH** - Create feature branches for changes
- Elasticsearch requires 2GB+ RAM allocation
- All 55+ documents are confirmed accessible
- Frontend runs on port 3002 (not 3000)
- Uses `working_main.py` as the API Gateway main file

## 🌿 Development Workflow
```bash
# Create feature branch for new work
git checkout -b feature/your-feature-name

# Make changes in feature branch
# Test thoroughly
# Commit changes

# When ready, create PR to merge back to main
```

## 📈 Monitoring
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:9090 (Prometheus)
- **Dashboards**: http://localhost:3001 (Grafana)
- **Logs**: `docker-compose logs -f [service-name]`

## 🔧 Troubleshooting
- **Elasticsearch issues**: Check memory allocation and health at http://localhost:9200/_cluster/health
- **Frontend 502 errors**: Ensure API Gateway is running and accessible
- **Document search fails**: Verify Elasticsearch has the `documents` index
- **Services won't start**: Check Docker resources and port conflicts

## 📝 Version History
- **v1.0**: Initial stable working version with all features functional
- **Date**: September 15, 2025
- **Status**: Production-ready with 55+ documents confirmed accessible

---
**⚠️ IMPORTANT: This is the stable working version. All future development should be done in feature branches to preserve this working state.**