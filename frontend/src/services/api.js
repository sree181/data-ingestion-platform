import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1', // Use relative URL - nginx will proxy to backend
  timeout: 90000, // 90 seconds timeout (LLM responses can take 30-60s)
  maxRedirects: 5, // Follow redirects
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await api.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Authentication functions
export const authService = {
  // Login with email and password
  login: async (email, password, mfaToken = null) => {
    const response = await api.post('/auth/login', {
      email,
      password,
      mfa_token: mfaToken
    });
    
    // Store tokens
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    
    return response.data;
  },
  
  // Setup MFA
  setupMfa: async (userId) => {
    const response = await api.post('/auth/mfa/setup', {
      user_id: userId
    });
    return response.data;
  },
  
  // Verify MFA setup
  verifyMfa: async (userId, token, secret) => {
    const response = await api.post('/auth/mfa/verify', {
      user_id: userId,
      token,
      secret
    });
    return response.data;
  },
  
  // Refresh token
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    
    // Update stored token
    localStorage.setItem('access_token', response.data.access_token);
    
    return response.data;
  },
  
  // Get current user info
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  // Logout
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
};

// API service functions
export const apiService = {
  // Search documents
  searchDocuments: async (query, filters = {}) => {
    try {
      const params = new URLSearchParams();
      params.append('q', query);
      
      // Add filters if provided
      if (filters.category) params.append('category', filters.category);
      if (filters.fileType) params.append('file_type', filters.fileType);
      if (filters.dateRange) params.append('date_range', filters.dateRange);
      
      const response = await api.get(`/search?${params.toString()}`);
      
      // Transform the Elasticsearch response to match our UI format
      return {
        total: response.data.total || 0,
        results: (response.data.results || []).map(transformElasticsearchResult),
      };
    } catch (error) {
      console.error('Search API error:', error);
      throw new Error('Failed to search documents');
    }
  },

  // Get all documents with pagination
  getDocuments: async (page = 0, size = 25, filters = {}) => {
    try {
      // Use the documents search endpoint
      const params = new URLSearchParams();
      params.append('q', '*'); // Query for all documents (wildcard)
      params.append('page', page.toString());
      params.append('size', size.toString());
      
      // Add filters if provided
      if (filters.classification) {
        params.append('classification', filters.classification);
      }
      if (filters.source) {
        params.append('source', filters.source);
      }
      
      console.log(`🔍 API Request: page=${page}, size=${size}`);
      const response = await api.get(`/search?${params.toString()}`);
      
      console.log(`📊 API Response: total=${response.data.total}, results=${response.data.results?.length}`);
      if (response.data.results && response.data.results.length > 0) {
        console.log(`📄 First doc:`, response.data.results[0]?._source?.title);
        console.log(`📄 Last doc:`, response.data.results[response.data.results.length - 1]?._source?.title);
      }
      
      return response.data; // Return the whole response (already has results array)
    } catch (error) {
      console.error('Documents API error:', error);
      throw new Error('Failed to fetch documents');
    }
  },

  // Get document by ID
  getDocument: async (id) => {
    try {
      const response = await api.get(`/documents/${id}`);
      return response.data;
    } catch (error) {
      console.error('Get document API error:', error);
      throw new Error('Failed to fetch document');
    }
  },

  // Delete document
  deleteDocument: async (id) => {
    try {
      console.log('Attempting to delete document with ID:', id);
      const response = await api.delete(`/documents/${id}`);
      console.log('Delete response:', response);
      return response.data;
    } catch (error) {
      console.error('Delete document API error:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new Error(`Failed to delete document: ${error.response?.data?.detail || error.message}`);
    }
  },

  // Update document
  updateDocument: async (id, updateData) => {
    try {
      console.log('Attempting to update document with ID:', id, 'Data:', updateData);
      const response = await api.put(`/documents/${id}`, updateData);
      console.log('Update response:', response);
      return response.data;
    } catch (error) {
      console.error('Update document API error:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new Error(`Failed to update document: ${error.response?.data?.detail || error.message}`);
    }
  },

  // Download document
  downloadDocument: async (id) => {
    try {
      const response = await api.get(`/documents/${id}/download`, {
        responseType: 'blob', // Important for file downloads
      });
      return response;
    } catch (error) {
      console.error('Download document API error:', error);
      throw new Error('Failed to download document');
    }
  },

  // Upload documents
  uploadDocuments: async (files, onProgress = null, spaceId = null) => {
    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });
      
      // Add space_id if provided
      if (spaceId) {
        formData.append('space_id', spaceId);
      }

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout for large uploads and processing
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(progress);
          }
        },
      });

      return response.data;
    } catch (error) {
      console.error('Upload API error:', error);
      if (error.code === 'ECONNABORTED') {
        throw new Error('Upload timed out. Large files may take longer to process.');
      }
      throw new Error(`Failed to upload documents: ${error.message}`);
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check API error:', error);
      throw new Error('Health check failed');
    }
  },

  // Get knowledge graph data
  getKnowledgeGraphData: async () => {
    try {
      const response = await api.get('/knowledge-graph');
      return response.data;
    } catch (error) {
      console.error('Knowledge graph API error:', error);
      throw new Error('Failed to fetch knowledge graph data');
    }
  },

  // Get analytics data
  getAnalytics: async () => {
    try {
      const response = await api.get('/analytics');
      return response.data;
    } catch (error) {
      console.error('Analytics API error:', error);
      // Return mock data if analytics endpoint doesn't exist yet
      return {
        totalDocuments: 100,
        categories: [
          { name: 'Medical', count: 45, percentage: 45 },
          { name: 'Legal', count: 35, percentage: 35 },
          { name: 'Government', count: 15, percentage: 15 },
          { name: 'Research', count: 5, percentage: 5 },
        ],
        processingStats: {
          processed: 100,
          failed: 0,
          pending: 0,
        },
      };
    }
  },

  // Investigation Management APIs - Palantir-style
  createInvestigation: async (investigation) => {
    try {
      const response = await api.post('/investigations', investigation);
      return response.data;
    } catch (error) {
      console.error('Create investigation API error:', error);
      throw new Error('Failed to create investigation');
    }
  },

  getInvestigations: async () => {
    try {
      const response = await api.get('/investigations');
      return response.data;
    } catch (error) {
      console.error('Get investigations API error:', error);
      throw new Error('Failed to fetch investigations');
    }
  },

  // Entity Exploration APIs - Gotham-style
  exploreEntity: async (entityId, depth = 2, confidenceThreshold = 0.5) => {
    try {
      const params = {
        depth: depth,
        confidence_threshold: confidenceThreshold
      };
      const response = await api.get(`/entities/${encodeURIComponent(entityId)}/explore`, { params });
      return response.data;
    } catch (error) {
      console.error('Explore entity API error:', error);
      throw new Error('Failed to explore entity');
    }
  },

  getEntityNetworkByEntityId: async (entityId, depth = 2, confidenceThreshold = 0.5) => {
    try {
      const params = {
        depth: depth,
        confidence_threshold: confidenceThreshold
      };
      const response = await api.get(`/entities/${encodeURIComponent(entityId)}/network`, { params });
      return response.data;
    } catch (error) {
      console.error('Get entity network API error:', error);
      throw new Error('Failed to get entity network');
    }
  },

  // Timeline Analysis APIs - Foundry-style
  getTimeline: async (caseId = 'default', startDate = '2024-01-01', endDate = '2025-12-31') => {
    try {
      const params = {
        case_id: caseId,
        start_date: startDate,
        end_date: endDate
      };
      const response = await api.get('/temporal/timeline', { params });
      return response.data;
    } catch (error) {
      console.error('Get timeline API error:', error);
      throw new Error('Failed to get timeline');
    }
  },

  // Advanced Search APIs - Palantir search capabilities
  advancedSearch: async (query = '', entityTypes = null, confidenceThreshold = 0.5, size = 20, from = 0) => {
    try {
      const params = {
        q: query,
        confidence_threshold: confidenceThreshold,
        size: size,
        from: from
      };
      
      if (entityTypes) {
        params.entity_types = entityTypes;
      }
      
      const response = await api.get('/search/advanced', { params });
      return response.data;
    } catch (error) {
      console.error('Advanced search API error:', error);
      throw new Error('Failed to perform advanced search');
    }
  },

  // Project Spaces API
  getProjectSpaces: async () => {
    try {
      const response = await api.get('/spaces/');
      return response.data;
    } catch (error) {
      console.error('Get project spaces API error:', error);
      throw new Error('Failed to get project spaces');
    }
  },

  createProjectSpace: async (spaceData) => {
    try {
      const response = await api.post('/spaces/', spaceData);
      return response.data;
    } catch (error) {
      console.error('Create project space API error:', error);
      throw new Error('Failed to create project space');
    }
  },

  getProjectSpace: async (spaceId) => {
    try {
      const response = await api.get(`/spaces/${spaceId}`);
      return response.data;
    } catch (error) {
      console.error('Get project space API error:', error);
      throw new Error('Failed to get project space');
    }
  },

  updateProjectSpace: async (spaceId, spaceData) => {
    try {
      const response = await api.put(`/spaces/${spaceId}`, spaceData);
      return response.data;
    } catch (error) {
      console.error('Update project space API error:', error);
      throw new Error('Failed to update project space');
    }
  },

  deleteProjectSpace: async (spaceId, authLevel = 'owner') => {
    try {
      // Pass auth_level as a query parameter with proper encoding
      const params = new URLSearchParams({ auth_level: authLevel });
      const response = await api.delete(`/spaces/${spaceId}?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Delete project space API error:', error);
      // Include backend error details if available
      const errorMessage = error.response?.data?.detail || 'Failed to delete project space';
      throw new Error(errorMessage);
    }
  },

  getSpaceAnalytics: async (spaceId) => {
    try {
      const response = await api.get(`/spaces/${spaceId}/analytics`);
      return response.data;
    } catch (error) {
      console.error('Get space analytics API error:', error);
      throw new Error('Failed to get space analytics');
    }
  },

  // Document Ingestion APIs
  getLocalFiles: async (spaceId, fileType = null) => {
    try {
      const params = fileType ? { file_type: fileType } : {};
      const response = await api.get(`/spaces/${spaceId}/ingestion/local-files`, { params });
      return response.data;
    } catch (error) {
      console.error('Get local files API error:', error);
      throw new Error('Failed to get local files');
    }
  },

  startBatchIngestion: async (spaceId, ingestionRequest) => {
    try {
      console.log('📤 Sending batch ingestion request to:', `/spaces/${spaceId}/ingestion/start`);
      console.log('📤 Request payload:', JSON.stringify(ingestionRequest, null, 2));
      
      const response = await api.post(`/spaces/${spaceId}/ingestion/start`, ingestionRequest);
      return response.data;
    } catch (error) {
      console.error('Start batch ingestion API error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new Error(`Failed to start batch ingestion: ${error.response?.data?.detail || error.message}`);
    }
  },

  getIngestionStatus: async (spaceId) => {
    try {
      const response = await api.get(`/spaces/${spaceId}/ingestion/status`);
      return response.data;
    } catch (error) {
      console.error('Get ingestion status API error:', error);
      throw new Error('Failed to get ingestion status');
    }
  },

  // LLM-based document structure analysis
  analyzeDocumentStructure: async (documentId) => {
    try {
      const response = await api.get(`/documents/${documentId}/structure`, {
        timeout: 180000  // 3 minutes timeout for OpenAI GPT-4 analysis
      });
      return response.data;
    } catch (error) {
      console.error('Document structure analysis API error:', error);
      throw new Error('Failed to analyze document structure');
    }
  },

  // Advanced Analytics - Real Data Features
  getTopicExtraction: () => api.get('/analytics/topic-extraction'),
  getDocumentRelationships: () => api.get('/analytics/document-relationships'),
  getLegalRiskAssessment: () => api.get('/analytics/legal-risk-assessment'),
  getEntityNetwork: () => api.get('/analytics/entity-network'),
  getSentimentAnalysis: () => api.get('/analytics/sentiment-analysis'),
  getContentFlow: () => api.get('/analytics/content-flow'),
  getTemporalEvolution: () => api.get('/analytics/temporal-evolution'),

  // RL (Reinforcement Learning) API methods
  rl: {
    // RL Status and Configuration
    getRLStatus: async () => {
      console.log('🤖 Fetching RL status from apiService.rl...');
      try {
        const response = await api.get('/rl/status');
        return response.data;
      } catch (error) {
        console.error('Get RL status API error:', error);
        // Return mock data if RL service is not available
        return {
          status: 'inactive',
          metrics: {
            accuracy: 0.0,
            confidence: 0.0,
            processing_time: 0,
            cost_efficiency: 0.0,
            memory_usage: 0
          },
          model_performance: {},
          recent_activity: []
        };
      }
    },

    getRLConfig: async () => {
      try {
        const response = await api.get('/rl/config');
        return response.data;
      } catch (error) {
        console.error('Get RL config API error:', error);
        return {
          enabled: false,
          optimization_targets: [],
          thresholds: {}
        };
      }
    },

    updateRLConfig: async (config) => {
      try {
        const response = await api.put('/rl/config', config);
        return response.data;
      } catch (error) {
        console.error('Update RL config API error:', error);
        throw error;
      }
    },

    startRLTraining: async (params) => {
      try {
        const response = await api.post('/rl/training/start', params);
        return response.data;
      } catch (error) {
        console.error('Start RL training API error:', error);
        throw error;
      }
    },

    stopRLTraining: async () => {
      try {
        const response = await api.post('/rl/training/stop');
        return response.data;
      } catch (error) {
        console.error('Stop RL training API error:', error);
        throw error;
      }
    },

    getRLMetrics: async (projectId) => {
      try {
        const response = await api.get(`/rl/metrics${projectId ? `?project_id=${projectId}` : ''}`);
        return response.data;
      } catch (error) {
        console.error('Get RL metrics API error:', error);
        return {
          accuracy: 0,
          precision: 0,
          recall: 0,
          f1_score: 0
        };
      }
    },

    getRLModels: async () => {
      try {
        const response = await api.get('/rl/models');
        return response.data;
      } catch (error) {
        console.error('Get RL models API error:', error);
        return [];
      }
    },

    updateRLModel: async (modelName, config) => {
      try {
        const response = await api.put(`/rl/models/${modelName}`, config);
        return response.data;
      } catch (error) {
        console.error('Update RL model API error:', error);
        throw error;
      }
    },

    getRecentDocuments: async (params = {}) => {
      try {
        const queryParams = new URLSearchParams(params).toString();
        const response = await api.get(`/rl/documents/recent${queryParams ? `?${queryParams}` : ''}`);
        return response.data;
      } catch (error) {
        console.error('Get recent documents API error:', error);
        // Return mock data
        return {
          documents: [
            {
              id: 'doc-1',
              title: 'Adverse event report analysis',
              classification: 'ICSR',
              confidence: 0.95,
              timestamp: new Date().toISOString(),
              rl_optimized: true
            },
            {
              id: 'doc-2',
              title: 'Clinical trial safety analysis',
              classification: 'Safety_Information',
              confidence: 0.87,
              timestamp: new Date(Date.now() - 3600000).toISOString(),
              rl_optimized: false
            }
          ],
          total: 2
        };
      }
    }
  }
};

// Add new API methods for unified search and source management
const extendedApiService = {
  ...apiService,
  
  // Unified search endpoints
  unifiedSearch: async (params) => {
    try {
      const response = await api.get('/unified-search/', { params });
      return response.data;
    } catch (error) {
      console.error('Unified search API error:', error);
      throw new Error('Failed to perform unified search');
    }
  },

  // Source management endpoints (using new source-config API)
  getSources: async () => {
    try {
      const response = await api.get('/source-config/sources');
      return response.data;
    } catch (error) {
      console.error('Get sources API error:', error);
      throw new Error('Failed to get sources');
    }
  },

  getSourceHealth: async () => {
    try {
      const response = await api.get('/source-config/health');
      return response.data;
    } catch (error) {
      console.error('Get source health API error:', error);
      throw new Error('Failed to get source health');
    }
  },

  enableSource: async (sourceId) => {
    try {
      const response = await api.post(`/source-config/sources/${sourceId}/toggle`, {
        enabled: true
      });
      return response.data;
    } catch (error) {
      console.error('Enable source API error:', error);
      throw new Error('Failed to enable source');
    }
  },

  disableSource: async (sourceId) => {
    try {
      const response = await api.post(`/source-config/sources/${sourceId}/toggle`, {
        enabled: false
      });
      return response.data;
    } catch (error) {
      console.error('Disable source API error:', error);
      throw new Error('Failed to disable source');
    }
  },

  updateSourceConfig: async (sourceId, config) => {
    try {
      const response = await api.put(`/source-config/sources/${sourceId}`, config);
      return response.data;
    } catch (error) {
      console.error('Update source config API error:', error);
      throw new Error('Failed to update source config');
    }
  },

  testSourceConnection: async (sourceId) => {
    try {
      const response = await api.post(`/source-config/sources/${sourceId}/health-check`);
      return response.data;
    } catch (error) {
      console.error('Test source connection API error:', error);
      throw new Error('Failed to test source connection');
    }
  },
  
  refreshSource: async (sourceId) => {
    try {
      const response = await api.post(`/source-config/sources/${sourceId}/refresh`);
      return response.data;
    } catch (error) {
      console.error('Refresh source API error:', error);
      throw new Error('Failed to refresh source');
    }
  },
  
  getSourceStatistics: async () => {
    try {
      const response = await api.get('/source-config/statistics');
      return response.data;
    } catch (error) {
      console.error('Get source statistics API error:', error);
      throw new Error('Failed to get source statistics');
    }
  },

  // Multi-source ingestion endpoints
  startIngestion: async (params) => {
    try {
      const response = await api.post('/ingestion/start', params);
      return response.data;
    } catch (error) {
      console.error('Start ingestion API error:', error);
      throw new Error('Failed to start ingestion');
    }
  },

  getIngestionJobStatus: async (jobId) => {
    try {
      const response = await api.get(`/ingestion/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Get ingestion job status API error:', error);
      throw new Error('Failed to get ingestion job status');
    }
  },

  listIngestionJobs: async () => {
    try {
      const response = await api.get('/ingestion/jobs');
      return response.data;
    } catch (error) {
      console.error('List ingestion jobs API error:', error);
      throw new Error('Failed to list ingestion jobs');
    }
  },

  // Knowledge Hub endpoints
  getKnowledgeHubStatistics: async () => {
    try {
      const response = await api.get('/knowledge-hub/statistics');
      return response.data;
    } catch (error) {
      console.error('Get knowledge hub statistics API error:', error);
      throw new Error('Failed to get knowledge hub statistics');
    }
  },

  getKnowledgeHubFullGraph: async () => {
    try {
      const response = await api.get('/knowledge-hub/full-graph');
      return response.data;
    } catch (error) {
      console.error('Get full knowledge hub graph API error:', error);
      throw new Error('Failed to get full knowledge hub graph');
    }
  },

  getKnowledgeHubEntityTypes: async () => {
    try {
      const response = await api.get('/knowledge-hub/entity-types');
      return response.data;
    } catch (error) {
      console.error('Get knowledge hub entity types API error:', error);
      throw new Error('Failed to get knowledge hub entity types');
    }
  },

  searchKnowledgeHubEntities: async (query, entityTypes = null, limit = 10) => {
    try {
      const params = { query, limit };
      if (entityTypes && entityTypes.length > 0) {
        params.entity_types = entityTypes.join(',');
      }
      const response = await api.get('/knowledge-hub/search', { params });
      return response.data;
    } catch (error) {
      console.error('Search knowledge hub entities API error:', error);
      throw new Error('Failed to search knowledge hub entities');
    }
  },

  getEntitySourceDocuments: async (entityId) => {
    try {
      const response = await api.get(`/knowledge-hub/entities/${entityId}/source-documents`);
      return response.data;
    } catch (error) {
      console.error('Get entity source documents API error:', error);
      // Return empty result instead of throwing to allow graceful degradation
      return { documents: [] };
    }
  },

  getKnowledgeHubEntity: async (entityName, depth = 2) => {
    try {
      const response = await api.get(`/knowledge-hub/entity/${encodeURIComponent(entityName)}`, {
        params: { depth }
      });
      return response.data;
    } catch (error) {
      console.error('Get knowledge hub entity API error:', error);
      throw new Error('Failed to get knowledge hub entity');
    }
  },

  getKnowledgeHubEntityDetails: async (entityId) => {
    try {
      const response = await api.get(`/knowledge-hub/entity/details/${encodeURIComponent(entityId)}`);
      return response.data;
    } catch (error) {
      console.error('Get knowledge hub entity details API error:', error);
      throw new Error('Failed to get knowledge hub entity details');
    }
  },

  getKnowledgeHubPath: async (fromEntity, toEntity, maxDepth = 5) => {
    try {
      const response = await api.get('/knowledge-hub/path', {
        params: { from: fromEntity, to: toEntity, max_depth: maxDepth }
      });
      return response.data;
    } catch (error) {
      console.error('Get knowledge hub path API error:', error);
      throw new Error('Failed to get knowledge hub path');
    }
  },

  // Get entity source documents
  getEntitySources: async (entityName, spaceId = null, limit = 20) => {
    try {
      const response = await api.get(`/knowledge-hub/entity/${encodeURIComponent(entityName)}/sources`, {
        params: { space_id: spaceId, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Get entity sources API error:', error);
      throw new Error('Failed to get entity source documents');
    }
  },

  // Entity chat endpoint
  chatWithEntity: async (entityName, message, conversationHistory = [], spaceId = null) => {
    try {
      const response = await api.post(`/knowledge-hub/entity/${encodeURIComponent(entityName)}/chat`, {
        message,
        conversation_history: conversationHistory,
        space_id: spaceId
      });
      return response.data;
    } catch (error) {
      console.error('Entity chat API error:', error);
      throw new Error('Failed to chat with entity');
    }
  },

  // RL (Reinforcement Learning) API methods
  rl: {
    // RL Status and Configuration
    getRLStatus: async () => {
      console.log('🤖 Fetching RL status from apiService.rl...');
      try {
        const response = await api.get('/rl/status');
        return response.data;
      } catch (error) {
        console.error('Get RL status API error:', error);
        // Return mock data if RL service is not available
        return {
          status: 'inactive',
          metrics: {
            accuracy: 0.0,
            confidence: 0.0,
            processing_time: 0,
            cost_efficiency: 0.0,
            memory_usage: 0
          },
          model_performance: {},
          recent_activity: []
        };
      }
    },

    getRLConfig: async () => {
      try {
        const response = await api.get('/rl/config');
        return response.data;
      } catch (error) {
        console.error('Get RL config API error:', error);
        return {
          enabled: false,
          optimization_targets: [],
          thresholds: {}
        };
      }
    },

    updateRLConfig: async (config) => {
      try {
        const response = await api.put('/rl/config', config);
        return response.data;
      } catch (error) {
        console.error('Update RL config API error:', error);
        throw error;
      }
    },

    startRLTraining: async (params) => {
      try {
        const response = await api.post('/rl/training/start', params);
        return response.data;
      } catch (error) {
        console.error('Start RL training API error:', error);
        throw error;
      }
    },

    stopRLTraining: async () => {
      try {
        const response = await api.post('/rl/training/stop');
        return response.data;
      } catch (error) {
        console.error('Stop RL training API error:', error);
        throw error;
      }
    },

    getRLMetrics: async (projectId) => {
      try {
        const response = await api.get(`/rl/metrics${projectId ? `?project_id=${projectId}` : ''}`);
        return response.data;
      } catch (error) {
        console.error('Get RL metrics API error:', error);
        return {
          accuracy: 0,
          precision: 0,
          recall: 0,
          f1_score: 0
        };
      }
    },

    getRLModels: async () => {
      try {
        const response = await api.get('/rl/models');
        return response.data;
      } catch (error) {
        console.error('Get RL models API error:', error);
        return [];
      }
    },

    updateRLModel: async (modelName, config) => {
      try {
        const response = await api.put(`/rl/models/${modelName}`, config);
        return response.data;
      } catch (error) {
        console.error('Update RL model API error:', error);
        throw error;
      }
    },

    getRecentDocuments: async (params = {}) => {
      try {
        const queryParams = new URLSearchParams(params).toString();
        const response = await api.get(`/rl/documents/recent${queryParams ? `?${queryParams}` : ''}`);
        return response.data;
      } catch (error) {
        console.error('Get recent documents API error:', error);
        // Return mock data
        return {
          documents: [
            {
              id: 'doc-1',
              title: 'Adverse event report analysis',
              classification: 'ICSR',
              confidence: 0.95,
              timestamp: new Date().toISOString(),
              rl_optimized: true
            },
            {
              id: 'doc-2',
              title: 'Clinical trial safety analysis',
              classification: 'Safety_Information',
              confidence: 0.87,
              timestamp: new Date(Date.now() - 3600000).toISOString(),
              rl_optimized: false
            }
          ],
          total: 2
        };
      }
    }
  }
};

// Transform Elasticsearch result to UI format
function transformElasticsearchResult(esResult) {
  const source = esResult._source || {};
  const metadata = source.metadata || {};
  
  // Handle external documents vs regular documents
  const isExternalDocument = source.external_source === true;
  
  // For external documents, use keywords as tags
  const tags = isExternalDocument ? (source.keywords || []) : (source.tags || []);
  const categories = isExternalDocument ? [] : (source.categories || []);
  
  return {
    id: esResult._id,
    title: source.title || metadata.filename || 'Untitled Document',
    content: source.content || '',
    category: getCategoryFromTags(categories.length > 0 ? categories : tags),
    date: formatDate(metadata.upload_date || source.created_at || new Date().toISOString()),
    fileType: source.file_type || getFileTypeFromFilename(metadata.filename || ''),
    size: formatFileSize(metadata.file_size || 0),
    highlights: extractHighlights(tags),
    score: esResult._score || 0,
    tags: tags,
    categories: categories,
    metadata: metadata,
    filename: metadata.filename || '',
    uploadDate: metadata.upload_date || source.created_at || '',
    processingStatus: source.processing_status || 'completed',
    // Add fields expected by DataGrid
    file_type: source.file_type || 'Unknown',
    created_at: source.created_at || metadata.upload_date || '',
    extraction_method: source.extraction_method || 'Basic',
    entities: source.openai_entities?.length || 0,
    confidence: source.confidence || 0,
    // Add external document specific fields
    ai_processed: source.ai_processed || false,
    external_source: source.external_source || false,
    source: source.source || 'unknown',
    document_type: source.document_type || 'unknown',
  };
}

// Helper functions
function getCategoryFromTags(categories) {
  if (Array.isArray(categories) && categories.length > 0) {
    const categoryMap = {
      health: 'Medical',
      medical: 'Medical',
      legal: 'Legal',
      court: 'Legal',
      government: 'Government',
      regulatory: 'Regulatory',
      fda: 'Regulatory',
      research: 'Research',
      // External document specific mappings
      'clinical_trial': 'Clinical Trial',
      'drug_label': 'Drug Label',
      'research_paper': 'Research Paper',
      'chemical_compound': 'Chemical Compound',
      'phase': 'Clinical Trial',
      'status': 'Clinical Trial',
      'study type': 'Clinical Trial',
    };
    
    for (const category of categories) {
      const mapped = categoryMap[category.toLowerCase()];
      if (mapped) return mapped;
    }
    
    // Capitalize first letter of first category
    return categories[0].charAt(0).toUpperCase() + categories[0].slice(1);
  }
  return 'General';
}

function getFileTypeFromFilename(filename) {
  const extension = filename.split('.').pop()?.toUpperCase();
  return extension || 'FILE';
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateString) {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch (error) {
    return 'Unknown Date';
  }
}

function extractHighlights(tags) {
  return Array.isArray(tags) ? tags.slice(0, 5) : [];
}

// Investigation Board API methods
extendedApiService.investigationBoard = {
  // Board operations
  getBoards: async (spaceId = null) => {
    const params = spaceId ? { space_id: spaceId } : {};
    const response = await api.get('/investigations/boards', { params });
    return response.data;
  },
  
  createBoard: async (boardData) => {
    const response = await api.post('/investigations/boards', boardData);
    return response.data;
  },
  
  getBoard: async (boardId) => {
    const response = await api.get(`/investigations/boards/${boardId}`);
    return response.data;
  },
  
  updateBoard: async (boardId, updates) => {
    const response = await api.put(`/investigations/boards/${boardId}`, updates);
    return response.data;
  },
  
  deleteBoard: async (boardId) => {
    await api.delete(`/investigations/boards/${boardId}`);
  },
  
  // Entity operations
  pinEntity: async (pinData) => {
    const response = await api.post('/investigations/pin', pinData);
    return response.data;
  },
  
  unpinEntity: async (pinId, boardId) => {
    await api.delete(`/investigations/pin/${pinId}`, { 
      params: { board_id: boardId }
    });
  },
  
  updatePinnedEntity: async (pinId, updates) => {
    const response = await api.put(`/investigations/pin/${pinId}`, updates);
    return response.data;
  },
  
  // Finding operations
  addFinding: async (findingData) => {
    const response = await api.post('/investigations/findings', findingData);
    return response.data;
  },
  
  updateFinding: async (findingId, updates) => {
    const response = await api.put(`/investigations/findings/${findingId}`, updates);
    return response.data;
  },
  
  deleteFinding: async (findingId) => {
    await api.delete(`/investigations/findings/${findingId}`);
  },
  
  // Connection operations
  createConnection: async (connectionData) => {
    const response = await api.post('/investigations/connections', connectionData);
    return response.data;
  },
  
  deleteConnection: async (boardId, sourceEntityId, targetEntityId) => {
    await api.delete('/investigations/connections', {
      params: { board_id: boardId, source_entity_id: sourceEntityId, target_entity_id: targetEntityId }
    });
  },
  
  // Export
  exportBoard: async (boardId) => {
    const response = await api.get(`/investigations/boards/${boardId}/export`);
    return response.data;
  },
  
  // Get documents for a pinned entity
  getEntityDocuments: async (pinId) => {
    const response = await api.get(`/investigations/pin/${pinId}/documents`);
    return response.data;
  },
  
  // Get entity-specific AI suggestions
  getEntitySuggestions: async (pinId, limit = 10) => {
    const response = await api.get(`/investigations/pin/${pinId}/suggestions`, {
      params: { limit }
    });
    return response.data;
  },
  
  // Generate AI investigation report
  generateReport: async (boardId, format = 'markdown', template = 'comprehensive') => {
    const response = await api.post(`/investigations/boards/${boardId}/generate-report`, null, {
      params: { format, template }
    });
    return response.data;
  },
  
  // AI Suggestions
  getSuggestions: async (boardId, limit = 10) => {
    const response = await api.get(`/investigations/boards/${boardId}/suggestions`, {
      params: { limit }
    });
    return response.data;
  },
  
  getMissingConnections: async (boardId) => {
    const response = await api.get(`/investigations/boards/${boardId}/missing-connections`);
    return response.data;
  },
  
  batchAddSuggestions: async (boardId, entityNames, connections) => {
    const response = await api.post(`/investigations/boards/${boardId}/suggestions/batch-add`, {
      entity_names: entityNames,
      connections: connections
    });
    return response.data;
  }
};

// ============ Workflow Builder API (Standalone Service) ============
// Create separate axios instance for workflow service
// Use relative URL so it goes through nginx proxy
const workflowApi = axios.create({
  baseURL: '/api/v1', // Proxied through nginx to workflow-builder:8008
  timeout: 90000,
});

// Add auth interceptor for workflow API
workflowApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

extendedApiService.workflow = {
  // Execute a workflow
  execute: async (workflowId, nodes, edges) => {
    const response = await workflowApi.post('/workflows/execute', {
      workflow_id: workflowId,
      nodes,
      edges
    });
    return response.data;
  },
  
  // Get execution status
  getStatus: async (executionId) => {
    const response = await workflowApi.get(`/workflows/execution/${executionId}/status`);
    return response.data;
  },
  
  // Save workflow
  save: async (title, description, nodes, edges, tags = [], isTemplate = false) => {
    const response = await workflowApi.post('/workflows/save', {
      title,
      description,
      nodes,
      edges,
      tags,
      is_template: isTemplate
    });
    return response.data;
  },
  
  // List workflows
  list: async (isTemplate = null) => {
    const params = isTemplate !== null ? { is_template: isTemplate } : {};
    const response = await workflowApi.get('/workflows/list', { params });
    return response.data;
  },
  
  // Get workflow by ID
  get: async (workflowId) => {
    const response = await workflowApi.get(`/workflows/${workflowId}`);
    return response.data;
  },
  
  // Delete workflow
  delete: async (workflowId) => {
    const response = await workflowApi.delete(`/workflows/${workflowId}`);
    return response.data;
  },
  
  // List templates
  listTemplates: async () => {
    const response = await workflowApi.get('/workflows/templates/list');
    return response.data;
  },
  
  // Use template
  useTemplate: async (templateId) => {
    const response = await workflowApi.post(`/workflows/templates/${templateId}/use`);
    return response.data;
  },
  
  // Health check
  health: async () => {
    const response = await workflowApi.get('/../../health'); // Root health endpoint
    return response.data;
  }
};

// ICSR Review API methods
extendedApiService.icsr = {
  // List pending ICSRs
  listPending: async () => {
    const response = await api.get('/icsr/list/pending');
    return response.data;
  },
  
  // Extract ICSR data
  extract: async (documentId) => {
    const response = await api.post(`/icsr/extract/${documentId}`);
    return response.data;
  },
  
  // Get ICSR data
  get: async (documentId) => {
    const response = await api.get(`/icsr/${documentId}`);
    return response.data;
  },
  
  // Update ICSR data
  update: async (documentId, data) => {
    const response = await api.put(`/icsr/${documentId}`, data);
    return response.data;
  },
  
  // Approve ICSR
  approve: async (data) => {
    const response = await api.post('/icsr/approve', data);
    return response.data;
  },
  
  // Download XML
  downloadXML: async (documentId) => {
    const response = await api.get(`/icsr/${documentId}/xml`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// Security API methods
const securityApi = {
  // Audit Logging
  audit: {
    // Log audit event
    log: async (eventData) => {
      const response = await api.post('/audit/log', eventData);
      return response.data;
    },
    
    // Get audit events
    getEvents: async (params = {}) => {
      const response = await api.get('/audit/events', { params });
      return response.data;
    },
    
    // Get audit statistics
    getStatistics: async (params = {}) => {
      const response = await api.get('/audit/statistics', { params });
      return response.data;
    },
    
    // Get events requiring review
    getEventsRequiringReview: async (params = {}) => {
      const response = await api.get('/audit/events/requiring-review', { params });
      return response.data;
    },
    
    // Get high-risk events
    getHighRiskEvents: async (params = {}) => {
      const response = await api.get('/audit/events/high-risk', { params });
      return response.data;
    },
    
    // Get recent events
    getRecentEvents: async (hours = 24, params = {}) => {
      const response = await api.get('/audit/events/recent', { 
        params: { hours, ...params } 
      });
      return response.data;
    },
    
    // Create retention policy
    createRetentionPolicy: async (policyData) => {
      const response = await api.post('/audit/retention-policies', policyData);
      return response.data;
    },
    
    // Create alert
    createAlert: async (alertData) => {
      const response = await api.post('/audit/alerts', alertData);
      return response.data;
    },
    
    // Export audit events
    exportEvents: async (exportConfig) => {
      const response = await api.post('/audit/export', exportConfig);
      return response.data;
    },
    
    // Health check
    healthCheck: async () => {
      const response = await api.get('/audit/health');
      return response.data;
    }
  },
  
  // Security Dashboard Data
  dashboard: {
    // Get security overview
    getSecurityOverview: async () => {
      try {
        // Mock data for now - in production this would call real endpoints
        return {
          securityStatus: 'ACTIVE',
          activeAlerts: 3,
          complianceScore: 98,
          auditEvents: 1247,
          alerts: {
            critical: 2,
            high: 1,
            medium: 0,
            low: 0
          },
          compliance: {
            gdpr: true,
            hipaa: true,
            sox: true,
            pci: false
          }
        };
      } catch (error) {
        console.error('Security overview API error:', error);
        throw error;
      }
    },
    
    // Get security metrics
    getSecurityMetrics: async () => {
      try {
        // Mock data for now
        return {
          loginSuccessRate: 94.2,
          mfaAdoption: 87.5,
          encryptionCoverage: 100,
          complianceScore: 98.1,
          riskDistribution: {
            low: 65,
            medium: 25,
            high: 8,
            critical: 2
          }
        };
      } catch (error) {
        console.error('Security metrics API error:', error);
        throw error;
      }
    },
    
    // Get security events timeline
    getSecurityEventsTimeline: async (hours = 24) => {
      try {
        // Mock data for now
        return [
          { time: '00:00', login: 45, failed: 2, blocked: 0 },
          { time: '04:00', login: 32, failed: 1, blocked: 0 },
          { time: '08:00', login: 78, failed: 5, blocked: 1 },
          { time: '12:00', login: 95, failed: 3, blocked: 0 },
          { time: '16:00', login: 67, failed: 4, blocked: 2 },
          { time: '20:00', login: 52, failed: 2, blocked: 1 },
          { time: '24:00', login: 38, failed: 1, blocked: 0 }
        ];
      } catch (error) {
        console.error('Security events timeline API error:', error);
        throw error;
      }
    },
    
    // Get recent security alerts
    getRecentSecurityAlerts: async (limit = 10) => {
      try {
        // Mock data for now
        return [
          {
            id: 'alert-1',
            time: '14:32:15',
            event: 'Multiple failed login attempts',
            severity: 'Critical',
            user: 'admin@company.com',
            ipAddress: '203.0.113.45',
            status: 'Blocked'
          },
          {
            id: 'alert-2',
            time: '13:45:22',
            event: 'Unauthorized data access attempt',
            severity: 'High',
            user: 'user123@company.com',
            ipAddress: '192.168.1.100',
            status: 'Investigated'
          },
          {
            id: 'alert-3',
            time: '12:18:33',
            event: 'Suspicious file download pattern',
            severity: 'Medium',
            user: 'researcher@company.com',
            ipAddress: '10.0.0.50',
            status: 'Pending'
          },
          {
            id: 'alert-4',
            time: '11:05:47',
            event: 'MFA bypass attempt detected',
            severity: 'Critical',
            user: 'manager@company.com',
            ipAddress: '172.16.0.25',
            status: 'Resolved'
          }
        ];
      } catch (error) {
        console.error('Recent security alerts API error:', error);
        throw error;
      }
    },
    
    // Get user activity
    getUserActivity: async (hours = 24) => {
      try {
        // Mock data for now
        return {
          topActiveUsers: [
            { name: 'John Doe', role: 'Admin', activity: 47, status: 'online' },
            { name: 'Jane Smith', role: 'Researcher', activity: 32, status: 'online' },
            { name: 'Mike Johnson', role: 'Analyst', activity: 28, status: 'away' },
            { name: 'Sarah Wilson', role: 'Manager', activity: 24, status: 'offline' },
            { name: 'David Brown', role: 'Developer', activity: 19, status: 'online' }
          ],
          recentSecurityEvents: [
            { event: 'Successful MFA login', user: 'admin@company.com', time: '2 min ago', type: 'success' },
            { event: 'Document access granted', user: 'researcher@company.com', time: '5 min ago', type: 'info' },
            { event: 'Failed login attempt', user: 'unknown@external.com', time: '8 min ago', type: 'warning' },
            { event: 'Password changed', user: 'manager@company.com', time: '12 min ago', type: 'info' },
            { event: 'Suspicious download', user: 'analyst@company.com', time: '15 min ago', type: 'warning' }
          ]
        };
      } catch (error) {
        console.error('User activity API error:', error);
        throw error;
      }
    }
  },

  // RL (Reinforcement Learning) API methods - UPDATED 2025
  rl: {
    // RL Status and Configuration
    getRLStatus: async () => {
      console.log('🤖 Fetching RL status...');
      try {
        const response = await api.get('/rl/status');
        return response.data;
      } catch (error) {
        console.error('Get RL status API error:', error);
        // Return mock data if RL service is not available
        return {
          status: 'inactive',
          metrics: {
            accuracy: 0.0,
            confidence: 0.0,
            processing_time: 0,
            cost_efficiency: 0.0,
            memory_usage: 0
          },
          model_performance: {},
          recent_activity: []
        };
      }
    },

    getRLConfig: async () => {
      try {
        const response = await api.get('/rl/config');
        return response.data;
      } catch (error) {
        console.error('Get RL config API error:', error);
        // Return mock data if RL service is not available
        return {
          learning_rate: 0.001,
          batch_size: 32,
          episodes: 1000,
          epsilon: 0.1,
          gamma: 0.95,
          target_update_frequency: 100,
          memory_size: 10000,
          model_architecture: {
            hidden_layers: [256, 128, 64],
            activation: 'relu',
            optimizer: 'adam'
          }
        };
      }
    },

    updateRLConfig: async (config) => {
      try {
        const response = await api.put('/rl/config', config);
        return response.data;
      } catch (error) {
        console.error('Update RL config API error:', error);
        throw new Error('Failed to update RL configuration');
      }
    },

    startRLTraining: async (params) => {
      try {
        const response = await api.post('/rl/training/start', params);
        return response.data;
      } catch (error) {
        console.error('Start RL training API error:', error);
        throw new Error('Failed to start RL training');
      }
    },

    stopRLTraining: async () => {
      try {
        const response = await api.post('/rl/training/stop');
        return response.data;
      } catch (error) {
        console.error('Stop RL training API error:', error);
        throw new Error('Failed to stop RL training');
      }
    },

    getRLMetrics: async (projectId) => {
      try {
        const response = await api.get(`/rl/metrics?project_id=${projectId}`);
        return response.data;
      } catch (error) {
        console.error('Get RL metrics API error:', error);
        // Return mock data if RL service is not available
        return {
          accuracy: 0.85,
          confidence: 0.78,
          processing_time: 1.2,
          cost_efficiency: 0.92,
          memory_usage: 0.45,
          model_performance: {
            rule_based: { accuracy: 0.75, confidence: 0.70 },
            bert: { accuracy: 0.82, confidence: 0.80 },
            llm: { accuracy: 0.88, confidence: 0.85 }
          },
          recent_activity: [
            { timestamp: new Date().toISOString(), action: 'model_training', status: 'completed' },
            { timestamp: new Date(Date.now() - 3600000).toISOString(), action: 'document_classification', status: 'success' }
          ]
        };
      }
    },

    getRLModels: async () => {
      try {
        const response = await api.get('/rl/models');
        return response.data;
      } catch (error) {
        console.error('Get RL models API error:', error);
        // Return mock data if RL service is not available
        return {
          models: [
            { name: 'rule_based', status: 'active', accuracy: 0.75 },
            { name: 'bert', status: 'active', accuracy: 0.82 },
            { name: 'llm', status: 'active', accuracy: 0.88 }
          ]
        };
      }
    },

    updateRLModel: async (modelName, config) => {
      try {
        const response = await api.put(`/rl/models/${modelName}`, config);
        return response.data;
      } catch (error) {
        console.error('Update RL model API error:', error);
        throw new Error('Failed to update RL model');
      }
    },

    // Get recent documents for RL analysis
    getRecentDocuments: async (params = {}) => {
      try {
        const response = await api.get('/rl/documents/recent', { params });
        return response.data;
      } catch (error) {
        console.error('Get recent documents API error:', error);
        // Return mock data if RL service is not available
        return {
          documents: [
            {
              id: 'doc-1',
              title: 'Adverse drug reaction case study',
              classification: 'ICSR',
              confidence: 0.92,
              timestamp: new Date().toISOString(),
              rl_optimized: true
            },
            {
              id: 'doc-2',
              title: 'Clinical trial safety analysis',
              classification: 'Safety_Information',
              confidence: 0.87,
              timestamp: new Date(Date.now() - 3600000).toISOString(),
              rl_optimized: false
            }
          ],
          total: 2
        };
      }
    }
  }
};

// Debug: Log apiService structure
console.log('🔍 apiService exported:', Object.keys(apiService));
console.log('🔍 apiService.rl exists?', !!apiService.rl);
if (apiService.rl) {
  console.log('🔍 apiService.rl methods:', Object.keys(apiService.rl));
}

// RL (Reinforcement Learning) API methods
const rlApi = {
  // RL Status and Configuration
  getRLStatus: async () => {
    try {
      const response = await api.get('/rl/status');
      return response.data;
    } catch (error) {
      console.error('Get RL status API error:', error);
      // Return mock data if RL service is not available
      return {
        status: 'inactive',
        metrics: {
          accuracy: 0.0,
          confidence: 0.0,
          processing_time: 0,
          cost_efficiency: 0.0,
          memory_usage: 0
        },
        model_performance: {},
        recent_activity: []
      };
    }
  },

  getRLConfig: async () => {
    try {
      const response = await api.get('/rl/config');
      return response.data;
    } catch (error) {
      console.error('Get RL config API error:', error);
      // Return default config if RL service is not available
      return {
        enableRL: false,
        confidence_threshold: 0.75,
        cost_budget: 100,
        max_processing_time: 5000,
        model_selection: 'auto',
        optimization_mode: 'balanced'
      };
    }
  },

  updateRLConfig: async (config) => {
    try {
      const response = await api.put('/rl/config', config);
      return response.data;
    } catch (error) {
      console.error('Update RL config API error:', error);
      throw new Error('Failed to update RL configuration');
    }
  },

  // RL Metrics
  getRLMetrics: async (projectId = 'default') => {
    try {
      const response = await api.get(`/rl/metrics/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Get RL metrics API error:', error);
      // Return mock data if RL service is not available
      return {
        accuracy: 0.85,
        confidence: 0.78,
        processing_time: 1200,
        cost_efficiency: 0.92,
        model_performance: {
          rule_based: 0.75,
          bert: 0.82,
          llm: 0.88
        },
        recent_decisions: [
          {
            action: 'rule_based_classification',
            confidence: 0.85,
            status: 'success',
            timestamp: new Date().toISOString()
          },
          {
            action: 'ensemble_classification',
            confidence: 0.92,
            status: 'success',
            timestamp: new Date(Date.now() - 300000).toISOString()
          }
        ],
        status: 'active'
      };
    }
  },

  // RL Training
  startRLTraining: async (trainingParams) => {
    try {
      const response = await api.post('/rl/training/start', trainingParams);
      return response.data;
    } catch (error) {
      console.error('Start RL training API error:', error);
      throw new Error('Failed to start RL training');
    }
  },

  getRLTrainingStatus: async () => {
    try {
      const response = await api.get('/rl/training/status');
      return response.data;
    } catch (error) {
      console.error('Get RL training status API error:', error);
      return {
        status: 'idle',
        progress: 0,
        current_episode: 0,
        total_episodes: 1000,
        metrics: {}
      };
    }
  },

  stopRLTraining: async () => {
    try {
      const response = await api.post('/rl/training/stop');
      return response.data;
    } catch (error) {
      console.error('Stop RL training API error:', error);
      throw new Error('Failed to stop RL training');
    }
  },

  // RL Classification
  classifyWithRL: async (document) => {
    try {
      const response = await api.post('/rl/classify', {
        document: document,
        document_id: document.id || `doc_${Date.now()}`
      });
      return response.data;
    } catch (error) {
      console.error('RL classification API error:', error);
      throw new Error('Failed to classify document with RL');
    }
  },

  // RL Decisions
  getRLDecisions: async (documentId) => {
    try {
      const response = await api.get(`/rl/decisions/${documentId}`);
      return response.data;
    } catch (error) {
      console.error('Get RL decisions API error:', error);
      // Return mock data if RL service is not available
      return {
        decisions: [
          {
            id: 'decision-1',
            action: 'rule_based_classification',
            confidence: 0.85,
            status: 'success',
            timestamp: new Date().toISOString(),
            reasoning: 'Simple document, rule-based classification sufficient',
            models_used: ['rule_based'],
            processing_time: 150,
            cost_estimate: 0.01
          },
          {
            id: 'decision-2',
            action: 'ensemble_classification',
            confidence: 0.92,
            status: 'success',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            reasoning: 'Complex document, full ensemble classification',
            models_used: ['rule_based', 'bert', 'llm'],
            processing_time: 2500,
            cost_estimate: 0.15
          }
        ],
        current_decision: {
          action: 'ensemble_classification',
          confidence: 0.88,
          status: 'processing',
          reasoning: 'Medium complexity document, using ensemble approach'
        }
      };
    }
  },

  // RL Performance Analysis
  getRLPerformanceAnalysis: async (timeRange = '24h') => {
    try {
      const response = await api.get(`/rl/performance?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      console.error('Get RL performance analysis API error:', error);
      // Return mock data if RL service is not available
      return {
        accuracy_trend: [
          { time: '00:00', accuracy: 0.82 },
          { time: '04:00', accuracy: 0.84 },
          { time: '08:00', accuracy: 0.86 },
          { time: '12:00', accuracy: 0.88 },
          { time: '16:00', accuracy: 0.85 },
          { time: '20:00', accuracy: 0.87 }
        ],
        cost_efficiency_trend: [
          { time: '00:00', cost: 0.12 },
          { time: '04:00', cost: 0.10 },
          { time: '08:00', cost: 0.15 },
          { time: '12:00', cost: 0.18 },
          { time: '16:00', cost: 0.14 },
          { time: '20:00', cost: 0.16 }
        ],
        model_usage: {
          rule_based: 45,
          bert: 30,
          llm: 25
        }
      };
    }
  },

  // RL Model Management
  getRLModels: async () => {
    try {
      const response = await api.get('/rl/models');
      return response.data;
    } catch (error) {
      console.error('Get RL models API error:', error);
      return {
        models: [
          { name: 'rule_based', status: 'active', accuracy: 0.75 },
          { name: 'bert', status: 'active', accuracy: 0.82 },
          { name: 'llm', status: 'active', accuracy: 0.88 }
        ]
      };
    }
  },

  updateRLModel: async (modelName, config) => {
    try {
      const response = await api.put(`/rl/models/${modelName}`, config);
      return response.data;
    } catch (error) {
      console.error('Update RL model API error:', error);
      throw new Error('Failed to update RL model');
    }
  },

  // Get recent documents for RL analysis
  getRecentDocuments: async (params = {}) => {
    try {
      const response = await api.get('/rl/documents/recent', { params });
      return response.data;
    } catch (error) {
      console.error('Get recent documents API error:', error);
      // Return mock data if RL service is not available
      return {
        documents: [
          {
            id: 'doc-1',
            title: 'Adverse drug reaction case study',
            classification: 'ICSR',
            confidence: 0.92,
            timestamp: new Date().toISOString(),
            rl_optimized: true
          },
          {
            id: 'doc-2',
            title: 'Clinical trial safety analysis',
            classification: 'Safety_Information',
            confidence: 0.87,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            rl_optimized: false
          }
        ],
        total: 2
      };
    }
  }
};

// Extend the main API service with RL methods
extendedApiService.rl = rlApi;

// Extend the main API service with security methods
extendedApiService.security = securityApi;

export default extendedApiService;
export { api };// Build timestamp: Sat Oct 25 09:10:41 CDT 2025
