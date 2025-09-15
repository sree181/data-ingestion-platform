# Nuve Platform - Architecture Diagrams

This directory contains comprehensive architecture diagrams for the Nuve Platform (Enterprise Document Intelligence) in Draw.io format.

## 📊 Available Diagrams

### 1. System Architecture Overview (`01_system_architecture_overview.drawio`)
**Purpose**: High-level view of the entire system architecture
**Best for**: Executive presentations, system overview, infrastructure planning

**Key Components**:
- User Interface Layer (React Frontend, API Docs)
- API Gateway Layer (FastAPI with Auth & Routing)
- Processing Services (Document Processing, Chat, Entity Enrichment)
- Storage & Database Layer (Elasticsearch, Neo4j, PostgreSQL, MinIO, Redis)
- Streaming & Message Queue (Kafka, Zookeeper)
- Data Processing Engine (Apache Spark)
- Monitoring & Observability (Grafana, Prometheus, Kibana)
- External Services (LlamaParse, OpenAI, Firecrawl)

### 2. Data Flow End-to-End (`02_data_flow_end_to_end.drawio`)
**Purpose**: Shows the complete data journey from ingestion to user interaction
**Best for**: Process documentation, data flow analysis, stakeholder education

**Flow Stages**:
1. **Data Ingestion**: User uploads, batch processing, streaming data
2. **Initial Processing**: API Gateway authentication and event queuing
3. **Document Processing**: LlamaParse, OCR, structure analysis
4. **Content Analysis**: NLP, vector embeddings, entity extraction
5. **Knowledge Construction**: Graph building, enrichment, classification
6. **Storage & Indexing**: Multi-database storage strategy
7. **AI-Powered Services**: Chat, insights, recommendations
8. **User Interface**: Dashboards, search, visualization, chat interfaces

### 3. Technical Component Interactions (`03_technical_component_interactions.drawio`)
**Purpose**: Detailed technical view of component relationships and capabilities
**Best for**: Technical teams, system integration, development planning

**Technical Details**:
- **Frontend**: React UI with theme toggle, Nuve logo, Inter font
- **Microservices**: Document processor, chat bot, entity service, knowledge builder
- **Data Storage**: Specialized databases for different data types
- **Event Streaming**: Kafka-based real-time processing
- **Processing Engine**: Spark for distributed computing
- **Monitoring**: Comprehensive observability stack
- **External APIs**: AI and web scraping integrations

## 🔧 How to Use These Diagrams

### Opening in Draw.io
1. **Online**: Go to [app.diagrams.net](https://app.diagrams.net)
2. **Desktop**: Download Draw.io desktop application
3. **VS Code**: Install Draw.io Integration extension

### Opening Steps
1. Open Draw.io
2. Click "Open Existing Diagram"
3. Select the `.drawio` file you want to view
4. The diagram will load with all formatting intact

### Editing and Customization
- **Colors**: Each layer uses distinct color coding for easy identification
- **Fonts**: All text uses Inter font family for consistency
- **Connections**: Arrows show data flow and relationships
- **Layout**: Organized in logical layers and sections

### Export Options
From Draw.io, you can export to:
- **PNG/JPG**: For presentations and documentation
- **PDF**: For high-quality prints and formal documents
- **SVG**: For web integration and scalable graphics
- **HTML**: For interactive web viewing

## 🎨 Design Standards

### Color Coding
- **Blue (`#e1f5fe`)**: User Interface components
- **Purple (`#f3e5f5`)**: API Gateway and routing
- **Green (`#e8f5e8`)**: Processing services and microservices
- **Orange (`#fff3e0`)**: Storage and databases
- **Pink (`#fce4ec`)**: Streaming and messaging
- **Teal (`#e0f2f1`)**: Processing engines
- **Light Green (`#f1f8e9`)**: Monitoring and observability
- **Yellow (`#fff8e1`)**: External services and APIs

### Typography
- **Font Family**: Inter (modern, clean, professional)
- **Headings**: Bold, larger sizes for section titles
- **Body Text**: Regular weight for component descriptions
- **Technical Details**: Smaller text for detailed capabilities

### Layout Principles
- **Left-to-Right Flow**: Data flows from left to right where possible
- **Layered Architecture**: Components grouped by function
- **Clear Connections**: Arrows indicate data flow and relationships
- **Consistent Spacing**: Uniform padding and margins

## 📋 Usage Scenarios

### For Business Stakeholders
- Use **System Architecture Overview** for high-level discussions
- Focus on business value and capabilities
- Highlight scalability and modern architecture

### For Technical Teams
- Use **Technical Component Interactions** for implementation planning
- Reference specific ports, protocols, and technologies
- Plan integration strategies

### For Process Documentation
- Use **Data Flow End-to-End** for workflow documentation
- Explain data transformation processes
- Document quality assurance checkpoints

### For Client Presentations
- Start with **System Architecture Overview**
- Deep dive with **Data Flow** for process explanation
- Technical details with **Component Interactions** as needed

## 🔄 Maintenance

### Updating Diagrams
1. Keep diagrams synchronized with actual system changes
2. Update component descriptions when features are added
3. Maintain consistent color coding and fonts
4. Version control diagram files alongside code

### Best Practices
- Update diagrams before major releases
- Include diagrams in architecture review processes
- Use diagrams in onboarding documentation
- Reference diagrams in technical specifications

## 📞 Support

For questions about these diagrams or the architecture they represent:
- Review the main project README
- Check technical documentation in `/docs`
- Contact the development team for clarifications

---

**Note**: These diagrams represent the current Nuve Platform architecture including the latest UI enhancements (theme toggle, logo integration, Inter font) and all backend services.
