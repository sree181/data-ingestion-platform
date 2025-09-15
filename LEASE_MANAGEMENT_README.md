# 🏢 Lease Management System

A specialized lease obligation extraction and comparative analysis system designed for professional contract management companies.

## 🎯 Use Cases

### 1. **Lease Negotiation Efficiency**
- Extract and compare obligations across complex contracts
- Strengthen negotiation positions with data-driven insights
- Identify leverage opportunities and risk factors

### 2. **Transition Management**
- Reduce downtime between leases
- Ensure faster, more accurate validation of records and conditions
- Streamline lease transition processes

### 3. **Obligation Assurance**
- Continuously monitor that lessees meet maintenance and documentation obligations
- Reduce end-of-lease disputes
- Proactive compliance tracking

## 🏗️ Architecture

### Backend Services

#### 1. **Lease Obligation Extractor** (Port 8005)
- **Purpose**: Extract lease-specific obligations and clauses
- **Features**:
  - 10 specialized obligation types (Maintenance, Renewal, Termination, etc.)
  - AI-powered extraction using GPT-4
  - Pattern-based extraction for reliability
  - Risk assessment and scoring
  - Negotiation leverage analysis
  - Market standard compliance checking

#### 2. **Lease Comparison Engine** (Port 8006)
- **Purpose**: Advanced comparative analysis and risk scoring
- **Features**:
  - Side-by-side document comparison
  - Risk scoring and assessment
  - Negotiation leverage analysis
  - Market benchmarking
  - Strategic recommendations

### Frontend Interface

#### **Lease Management Dashboard** (`/lease-management`)
- **Extraction Tab**: Configure and run obligation extraction
- **Comparison Tab**: Compare multiple lease documents
- **Configuration Tab**: Manage extraction rules and settings

## 🚀 Quick Start

### 1. **Start Services**
```bash
./start-lease-services.sh
```

### 2. **Access Frontend**
Navigate to: `http://localhost:3000/lease-management`

### 3. **API Documentation**
- Lease Extractor: `http://localhost:8005/docs`
- Comparison Engine: `http://localhost:8006/docs`

## 📋 Obligation Types

| Type | Description | Risk Factors |
|------|-------------|--------------|
| **MAINTENANCE_OBLIGATIONS** | Maintenance and repair responsibilities | Unlimited, sole discretion |
| **RENEWAL_TERMS** | Lease renewal options and conditions | Automatic renewal, penalties |
| **TERMINATION_RIGHTS** | Termination procedures and conditions | Immediate termination, no cure period |
| **RENT_ESCALATION** | Rent increase mechanisms | Unlimited increase, compounding |
| **SECURITY_DEPOSIT** | Security deposit terms and conditions | Non-refundable, forfeiture |
| **INSURANCE_REQUIREMENTS** | Insurance coverage obligations | Unlimited coverage, additional insured |
| **ASSIGNMENT_RIGHTS** | Assignment and subletting rights | Prohibited, restricted |
| **IMPROVEMENT_OBLIGATIONS** | Tenant improvement requirements | No approval, irreversible |
| **COMPLIANCE_REQUIREMENTS** | Regulatory compliance obligations | Strict compliance, immediate |
| **FORCE_MAJEURE** | Force majeure provisions | Excluded events, limited scope |

## 🔧 Configuration

### Extraction Rules
```json
{
  "obligation_types": [
    "MAINTENANCE_OBLIGATIONS",
    "RENEWAL_TERMS",
    "TERMINATION_RIGHTS"
  ],
  "risk_categories": {
    "LOW": {"score": 1, "description": "Standard market terms"},
    "MEDIUM": {"score": 2, "description": "Some unusual terms"},
    "HIGH": {"score": 3, "description": "Significant risk factors"},
    "CRITICAL": {"score": 4, "description": "Extreme risk"}
  }
}
```

### Comparison Settings
```json
{
  "risk_tolerance": "MEDIUM",
  "focus_areas": ["maintenance", "renewal", "termination"],
  "enable_risk_analysis": true,
  "enable_negotiation_analysis": true,
  "enable_market_benchmarking": true
}
```

## 📊 API Endpoints

### Lease Obligation Extractor

#### Extract Obligations
```http
POST /api/v1/lease/extract
Content-Type: application/json

{
  "document_id": "doc_123",
  "document_content": "Lease agreement text...",
  "focus_areas": ["maintenance", "renewal"],
  "extraction_rules": {}
}
```

#### Get Configuration
```http
GET /api/v1/lease/config/rules
```

#### Update Configuration
```http
POST /api/v1/lease/config/rules
Content-Type: application/json

{
  "obligation_types": [...],
  "risk_categories": {...}
}
```

### Lease Comparison Engine

#### Compare Documents
```http
POST /api/v1/lease/compare
Content-Type: application/json

{
  "document_ids": ["doc_1", "doc_2", "doc_3"],
  "comparison_config": {...},
  "focus_areas": ["maintenance", "renewal"],
  "risk_tolerance": "MEDIUM"
}
```

#### Risk Analysis
```http
POST /api/v1/lease/risk/analyze
Content-Type: application/json

{
  "document_ids": ["doc_1", "doc_2"],
  "risk_tolerance": "MEDIUM",
  "focus_areas": ["maintenance"]
}
```

#### Negotiation Analysis
```http
POST /api/v1/lease/negotiation/analyze
Content-Type: application/json

{
  "document_ids": ["doc_1", "doc_2"],
  "focus_areas": ["maintenance", "renewal"]
}
```

## 🎨 Frontend Features

### Extraction Interface
- **Document Selection**: Choose documents for analysis
- **Focus Areas**: Select specific obligation types
- **Custom Rules**: Configure extraction parameters
- **Results Display**: View extracted obligations with risk scores

### Comparison Interface
- **Multi-Document Selection**: Compare 2+ documents
- **Risk Analysis**: Visual risk scoring and distribution
- **Negotiation Insights**: Leverage opportunities and strategies
- **Market Benchmarking**: Compare against market standards

### Configuration Interface
- **Extraction Rules**: Manage obligation types and risk categories
- **Comparison Settings**: Configure analysis parameters
- **Risk Tolerance**: Set risk acceptance levels

## 🔍 Example Workflow

### 1. **Extract Obligations**
1. Navigate to Lease Management → Extraction tab
2. Select a lease document
3. Choose focus areas (e.g., maintenance, renewal)
4. Click "Extract Obligations"
5. Review extracted obligations with risk scores

### 2. **Compare Documents**
1. Navigate to Lease Management → Comparison tab
2. Select 2+ documents to compare
3. Configure comparison settings
4. Click "Compare Documents"
5. Analyze risk scores and negotiation opportunities

### 3. **Configure Settings**
1. Navigate to Lease Management → Configuration tab
2. Adjust extraction rules and risk categories
3. Set comparison parameters
4. Save configuration

## 🛠️ Development

### Project Structure
```
services/
├── lease-obligation-extractor/
│   ├── main.py
│   ├── processors/
│   │   ├── lease_clause_extractor.py
│   │   └── obligation_analyzer.py
│   ├── requirements.txt
│   └── Dockerfile
├── lease-comparison-engine/
│   ├── main.py
│   ├── processors/
│   │   ├── comparison_engine.py
│   │   ├── risk_scorer.py
│   │   └── negotiation_analyzer.py
│   ├── requirements.txt
│   └── Dockerfile
frontend/src/pages/
└── LeaseManagement.js
```

### Adding New Obligation Types
1. Update `obligation_types` in `lease_clause_extractor.py`
2. Add extraction patterns and risk factors
3. Update frontend configuration interface
4. Test with sample documents

### Customizing Risk Assessment
1. Modify `risk_categories` in processors
2. Adjust risk scoring weights
3. Update mitigation strategies
4. Test with various document types

## 🔒 Security Considerations

- **API Keys**: Store OpenAI API keys securely in environment variables
- **Data Privacy**: Ensure document content is handled securely
- **Access Control**: Implement proper authentication and authorization
- **Audit Logging**: Track all extraction and comparison activities

## 📈 Performance Optimization

- **Caching**: Implement Redis caching for frequent queries
- **Batch Processing**: Process multiple documents in parallel
- **Database Indexing**: Optimize Elasticsearch queries
- **API Rate Limiting**: Implement rate limiting for external APIs

## 🧪 Testing

### Unit Tests
```bash
cd services/lease-obligation-extractor
python -m pytest tests/
```

### Integration Tests
```bash
# Test extraction endpoint
curl -X POST http://localhost:8005/api/v1/lease/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": "test", "document_content": "..."}'

# Test comparison endpoint
curl -X POST http://localhost:8006/api/v1/lease/compare \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["doc1", "doc2"]}'
```

## 🚀 Deployment

### Docker Compose
```bash
docker-compose -f docker-compose-lease.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/lease-management/
```

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
POSTGRES_PASSWORD=your_postgres_password
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## 📞 Support

For questions or issues:
1. Check the API documentation at `/docs` endpoints
2. Review the logs: `docker-compose -f docker-compose-lease.yml logs`
3. Test individual services: `curl http://localhost:8005/health`

## 🔄 Updates

### Version 1.0.0
- Initial release with 10 obligation types
- Basic extraction and comparison functionality
- Frontend interface for configuration and analysis

### Planned Features
- Advanced AI models for better extraction accuracy
- Integration with external lease databases
- Automated compliance monitoring
- Mobile-responsive interface
- Bulk document processing
- Custom reporting and analytics
