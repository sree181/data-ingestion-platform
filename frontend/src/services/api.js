import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1', // Use relative URL - nginx will proxy to backend
  timeout: 30000, // 30 seconds default timeout
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
      // Use the search endpoint with empty query to get all documents
      const params = new URLSearchParams();
      params.append('q', '*'); // Query for all documents (wildcard)
      params.append('size', size.toString());
      params.append('from', (page * size).toString());
      params.append('_t', Date.now().toString()); // Cache buster
      
      console.log(`🔍 API Request: page=${page}, size=${size}, from=${page * size}`);
      const response = await api.get(`/search?${params.toString()}`);
      
      console.log(`📊 API Response: total=${response.data.total}, results=${response.data.results?.length}`);
      console.log(`📄 First doc:`, response.data.results?.[0]?._source?.title);
      console.log(`📄 Last doc:`, response.data.results?.[response.data.results?.length - 1]?._source?.title);
      
      return {
        total: response.data.total || 0,
        documents: (response.data.results || []).map(transformElasticsearchResult),
        page,
        size,
      };
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
};

// Transform Elasticsearch result to UI format
function transformElasticsearchResult(esResult) {
  const source = esResult._source || {};
  const metadata = source.metadata || {};
  
  return {
    id: esResult._id,
    title: source.title || metadata.filename || 'Untitled Document',
    content: source.content || '',
    category: getCategoryFromTags(source.categories || source.tags || []),
    date: formatDate(metadata.upload_date || source.created_at || new Date().toISOString()),
    fileType: source.file_type || getFileTypeFromFilename(metadata.filename || ''),
    size: formatFileSize(metadata.file_size || 0),
    highlights: extractHighlights(source.tags || []),
    score: esResult._score || 0,
    tags: source.tags || [],
    categories: source.categories || [],
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

export default apiService;
export { api };