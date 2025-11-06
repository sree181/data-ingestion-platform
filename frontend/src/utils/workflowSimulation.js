// Workflow Simulation Engine for PV Document Processing
// Provides realistic dummy data simulation for all node types

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export class WorkflowSimulator {
  constructor(updateNodeCallback) {
    this.updateNode = updateNodeCallback;
    this.isRunning = false;
  }

  stop() {
    this.isRunning = false;
  }

  // Simulate Source Document Fetch (NCBI, PubMed, ChEMBL, FDA)
  async simulateSourceFetch(nodeId, config) {
    const maxDocs = config.maxDocuments || 100;
    const fetchDuration = 15000; // 15 seconds
    const updateInterval = 200; // Update every 200ms
    const stepsCount = fetchDuration / updateInterval;
    
    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        documentsFound: 0,
        documentsFetched: 0,
        startTime: new Date(),
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = Math.min(100, (i / stepsCount) * 100);
      const docsFetched = Math.floor((progress / 100) * maxDocs);
      
      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          documentsFound: docsFetched,
          documentsFetched: docsFetched,
          startTime: new Date(Date.now() - (i * updateInterval)),
          duration: i * updateInterval,
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          documentsFound: maxDocs,
          documentsFetched: maxDocs,
          duration: fetchDuration,
          endTime: new Date(),
        }
      });
    }
  }

  // Simulate Preprocessing (OCR, HTML Cleaning, Normalization)
  async simulatePreprocessing(nodeId, inputDocs = 100) {
    const processingDuration = 20000; // 20 seconds
    const updateInterval = 300;
    const stepsCount = processingDuration / updateInterval;

    const subProcesses = {
      ocr: { status: 'pending', progress: 0, documentsProcessed: 0 },
      htmlCleaning: { status: 'pending', progress: 0, documentsProcessed: 0 },
      normalization: { status: 'pending', progress: 0, documentsProcessed: 0 },
    };

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      subProcesses,
      metrics: {
        documentsProcessed: 0,
        totalDocuments: inputDocs,
        startTime: new Date(),
      }
    });

    // Process each sub-process sequentially with overlap
    const subProcessKeys = Object.keys(subProcesses);
    
    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const overallProgress = (i / stepsCount) * 100;
      
      // Update sub-processes with staggered start
      subProcessKeys.forEach((key, index) => {
        const startDelay = index * 0.2; // 20% delay between processes
        const adjustedProgress = Math.max(0, (overallProgress - (startDelay * 100)) / (1 - startDelay));
        
        if (adjustedProgress > 0) {
          subProcesses[key] = {
            status: adjustedProgress >= 100 ? 'complete' : 'running',
            progress: Math.min(100, Math.floor(adjustedProgress)),
            documentsProcessed: Math.floor((Math.min(100, adjustedProgress) / 100) * inputDocs),
          };
        }
      });

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(overallProgress),
        subProcesses: { ...subProcesses },
        metrics: {
          documentsProcessed: Math.floor((overallProgress / 100) * inputDocs),
          totalDocuments: inputDocs,
          duration: i * updateInterval,
          averageTimePerDoc: ((i * updateInterval) / Math.max(1, Math.floor((overallProgress / 100) * inputDocs))),
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        subProcesses: {
          ocr: { status: 'complete', progress: 100, documentsProcessed: inputDocs },
          htmlCleaning: { status: 'complete', progress: 100, documentsProcessed: inputDocs },
          normalization: { status: 'complete', progress: 100, documentsProcessed: inputDocs },
        },
        metrics: {
          documentsProcessed: inputDocs,
          totalDocuments: inputDocs,
          duration: processingDuration,
          endTime: new Date(),
        }
      });
    }
  }

  // Simulate NER (Named Entity Recognition & Relationships)
  async simulateNER(nodeId, inputDocs = 100) {
    const nerDuration = 25000; // 25 seconds
    const updateInterval = 250;
    const stepsCount = nerDuration / updateInterval;

    // Realistic entity counts
    const avgEntitiesPerDoc = 15;
    const avgRelationsPerDoc = 8;
    const totalEntities = inputDocs * avgEntitiesPerDoc;
    const totalRelations = inputDocs * avgRelationsPerDoc;

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        documentsProcessed: 0,
        totalDocuments: inputDocs,
        entitiesExtracted: 0,
        relationshipsExtracted: 0,
        startTime: new Date(),
        entityBreakdown: {
          drug: 0,
          disease: 0,
          adverse_event: 0,
          gene: 0,
        }
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = (i / stepsCount) * 100;
      const docsProcessed = Math.floor((progress / 100) * inputDocs);
      const entitiesExtracted = Math.floor((progress / 100) * totalEntities);
      const relationsExtracted = Math.floor((progress / 100) * totalRelations);

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          documentsProcessed: docsProcessed,
          totalDocuments: inputDocs,
          entitiesExtracted,
          relationshipsExtracted: relationsExtracted,
          duration: i * updateInterval,
          entityBreakdown: {
            drug: Math.floor(entitiesExtracted * 0.35),
            disease: Math.floor(entitiesExtracted * 0.25),
            adverse_event: Math.floor(entitiesExtracted * 0.30),
            gene: Math.floor(entitiesExtracted * 0.10),
          }
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          documentsProcessed: inputDocs,
          totalDocuments: inputDocs,
          entitiesExtracted: totalEntities,
          relationshipsExtracted: totalRelations,
          duration: nerDuration,
          endTime: new Date(),
          entityBreakdown: {
            drug: Math.floor(totalEntities * 0.35),
            disease: Math.floor(totalEntities * 0.25),
            adverse_event: Math.floor(totalEntities * 0.30),
            gene: Math.floor(totalEntities * 0.10),
          }
        }
      });
    }
  }

  // Simulate Ingestion (Elasticsearch & Neo4j)
  async simulateIngestion(nodeId, inputDocs = 100, entities = 1500, relations = 800) {
    const ingestionDuration = 18000; // 18 seconds
    const updateInterval = 200;
    const stepsCount = ingestionDuration / updateInterval;

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        elasticsearch: {
          documentsIngested: 0,
          totalDocuments: inputDocs,
          progress: 0,
          status: 'ingesting',
        },
        neo4j: {
          nodesCreated: 0,
          relationshipsCreated: 0,
          progress: 0,
          status: 'ingesting',
        }
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = (i / stepsCount) * 100;
      
      // Elasticsearch slightly ahead of Neo4j
      const esProgress = Math.min(100, progress * 1.1);
      const neo4jProgress = Math.min(100, progress * 0.9);

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          elasticsearch: {
            documentsIngested: Math.floor((esProgress / 100) * inputDocs),
            totalDocuments: inputDocs,
            progress: Math.floor(esProgress),
            status: esProgress >= 100 ? 'complete' : 'ingesting',
          },
          neo4j: {
            nodesCreated: Math.floor((neo4jProgress / 100) * entities),
            relationshipsCreated: Math.floor((neo4jProgress / 100) * relations),
            progress: Math.floor(neo4jProgress),
            status: neo4jProgress >= 100 ? 'complete' : 'ingesting',
          }
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          elasticsearch: {
            documentsIngested: inputDocs,
            totalDocuments: inputDocs,
            progress: 100,
            status: 'complete',
          },
          neo4j: {
            nodesCreated: entities,
            relationshipsCreated: relations,
            progress: 100,
            status: 'complete',
          }
        }
      });
    }
  }

  // Simulate Classification
  async simulateClassification(nodeId, inputDocs = 100) {
    const classificationDuration = 22000; // 22 seconds
    const updateInterval = 250;
    const stepsCount = classificationDuration / updateInterval;

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        documentsClassified: 0,
        totalDocuments: inputDocs,
        averageConfidence: 0,
        startTime: new Date(),
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = (i / stepsCount) * 100;
      const docsClassified = Math.floor((progress / 100) * inputDocs);
      
      // Simulate increasing confidence as model processes more
      const avgConfidence = 0.65 + (progress / 100) * 0.25; // 65% to 90%

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          documentsClassified: docsClassified,
          totalDocuments: inputDocs,
          averageConfidence: avgConfidence,
          duration: i * updateInterval,
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          documentsClassified: inputDocs,
          totalDocuments: inputDocs,
          averageConfidence: 0.87,
          duration: classificationDuration,
          endTime: new Date(),
        }
      });
    }
  }

  // Simulate Storage (S3, Box, MinIO, Google Drive)
  async simulateStorage(nodeId, inputDocs = 100) {
    const storageDuration = 12000; // 12 seconds
    const updateInterval = 200;
    const stepsCount = storageDuration / updateInterval;

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        filesStored: 0,
        totalFiles: inputDocs,
        storageUsed: '0 MB',
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = (i / stepsCount) * 100;
      const filesStored = Math.floor((progress / 100) * inputDocs);
      const storageMB = Math.floor((progress / 100) * inputDocs * 2.5); // ~2.5MB per file

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          filesStored,
          totalFiles: inputDocs,
          storageUsed: `${storageMB} MB`,
          duration: i * updateInterval,
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          filesStored: inputDocs,
          totalFiles: inputDocs,
          storageUsed: `${Math.floor(inputDocs * 2.5)} MB`,
          duration: storageDuration,
          endTime: new Date(),
        }
      });
    }
  }

  // Simulate Monitoring
  async simulateMonitoring(nodeId) {
    const monitoringDuration = 10000; // 10 seconds
    const updateInterval = 500;
    const stepsCount = monitoringDuration / updateInterval;

    this.updateNode(nodeId, {
      status: 'running',
      progress: 0,
      metrics: {
        accuracy: 0,
        precision: 0,
        recall: 0,
        f1Score: 0,
        latency: 0,
        throughput: 0,
        startTime: new Date(),
      }
    });

    for (let i = 0; i <= stepsCount && this.isRunning; i++) {
      await delay(updateInterval);
      const progress = (i / stepsCount) * 100;
      
      // Simulate converging metrics
      const accuracy = 0.70 + (progress / 100) * 0.17; // 70% to 87%
      const precision = 0.68 + (progress / 100) * 0.20; // 68% to 88%
      const recall = 0.72 + (progress / 100) * 0.16; // 72% to 88%
      const f1Score = 2 * (precision * recall) / (precision + recall);
      const latency = 150 + Math.random() * 50; // 150-200ms
      const throughput = 8 + Math.random() * 4; // 8-12 docs/sec

      this.updateNode(nodeId, {
        status: 'running',
        progress: Math.floor(progress),
        metrics: {
          accuracy,
          precision,
          recall,
          f1Score,
          latency,
          throughput,
          duration: i * updateInterval,
        }
      });
    }

    if (this.isRunning) {
      this.updateNode(nodeId, {
        status: 'complete',
        progress: 100,
        metrics: {
          accuracy: 0.87,
          precision: 0.88,
          recall: 0.88,
          f1Score: 0.88,
          latency: 175,
          throughput: 10.5,
          duration: monitoringDuration,
          endTime: new Date(),
        }
      });
    }
  }

  // Main execution method
  async executeWorkflow(nodes, edges) {
    this.isRunning = true;
    
    // Build dependency graph
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const dependencies = new Map();
    
    nodes.forEach(node => {
      const incomingEdges = edges.filter(e => e.target === node.id);
      dependencies.set(node.id, incomingEdges.map(e => e.source));
    });

    // Topological sort to determine execution order
    const executionOrder = this.topologicalSort(nodes, dependencies);
    
    // Execute nodes in order
    for (const nodeId of executionOrder) {
      if (!this.isRunning) break;
      
      const node = nodeMap.get(nodeId);
      const nodeType = node.data.type;
      const config = node.data.config || {};

      // Simulate based on node type
      switch (nodeType) {
        case 'ncbi':
        case 'pubmed':
        case 'chembl':
        case 'cochrane':
        case 'fda':
          await this.simulateSourceFetch(nodeId, config);
          break;
        case 's3':
        case 'box':
        case 'minio':
        case 'gdrive':
          await this.simulateStorage(nodeId, config.maxDocuments || 100);
          break;
        case 'preprocessing':
          await this.simulatePreprocessing(nodeId, config.maxDocuments || 100);
          break;
        case 'ner':
          await this.simulateNER(nodeId, config.maxDocuments || 100);
          break;
        case 'ingestion':
          await this.simulateIngestion(nodeId, config.maxDocuments || 100);
          break;
        case 'classification':
          await this.simulateClassification(nodeId, config.maxDocuments || 100);
          break;
        case 'monitoring':
          await this.simulateMonitoring(nodeId);
          break;
        default:
          console.warn(`Unknown node type: ${nodeType}`);
      }
    }

    return this.isRunning;
  }

  // Topological sort for workflow execution order
  topologicalSort(nodes, dependencies) {
    const visited = new Set();
    const result = [];

    const visit = (nodeId) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      
      const deps = dependencies.get(nodeId) || [];
      deps.forEach(depId => visit(depId));
      
      result.push(nodeId);
    };

    nodes.forEach(node => visit(node.id));
    return result;
  }
}

