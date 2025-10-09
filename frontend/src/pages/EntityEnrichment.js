import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Grid,
  Alert,
  IconButton,
  Tooltip,
  Badge,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  ListItemText,
  OutlinedInput,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Launch as LaunchIcon,
  Visibility as VisibilityIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

// Add keyframes for pulse animation
const pulseKeyframes = `
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(25, 118, 210, 0); }
    100% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); }
  }
`;

// Inject styles into head
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.type = 'text/css';
  styleSheet.innerText = pulseKeyframes;
  document.head.appendChild(styleSheet);
}

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
});

// Separate API instance for enrichment with longer timeout
const enrichmentApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 120000, // 2 minutes for web scraping
});

// Entity type icons and colors
const ENTITY_CONFIG = {
  PERSON: { icon: PersonIcon, color: '#2196F3', label: 'Person' },
  ORGANIZATION: { icon: BusinessIcon, color: '#4CAF50', label: 'Organization' },
  LOCATION: { icon: LocationIcon, color: '#FF9800', label: 'Location' },
  EVENT: { icon: TrendingUpIcon, color: '#9C27B0', label: 'Event' },
  PRODUCT: { icon: PsychologyIcon, color: '#F44336', label: 'Product' },
  OTHER: { icon: InfoIcon, color: '#757575', label: 'Other' },
};

// Enhanced Status configurations with live tracking
const STATUS_CONFIG = {
  not_scraped: { 
    color: '#757575', 
    label: 'Not Enriched', 
    icon: ScheduleIcon,
    description: 'Ready for enrichment',
    bgColor: '#f5f5f5'
  },
  scraping: { 
    color: '#FF9800', 
    label: 'Enriching...', 
    icon: CircularProgress,
    description: 'Gathering data from sources',
    bgColor: '#fff3e0',
    animated: true
  },
  completed: { 
    color: '#4CAF50', 
    label: 'Enriched', 
    icon: CheckCircleIcon,
    description: 'Data enrichment completed',
    bgColor: '#e8f5e8'
  },
  failed: { 
    color: '#F44336', 
    label: 'Failed', 
    icon: ErrorIcon,
    description: 'Enrichment encountered errors',
    bgColor: '#ffebee'
  },
  // Handle backend status values
  pending: { 
    color: '#757575', 
    label: 'Pending', 
    icon: ScheduleIcon,
    description: 'Queued for processing',
    bgColor: '#f5f5f5'
  },
  processing: { 
    color: '#2196F3', 
    label: 'Processing...', 
    icon: CircularProgress,
    description: 'AI analysis in progress',
    bgColor: '#e3f2fd',
    animated: true
  },
  // Additional status mappings for consistency
  'not_scraped': { color: '#757575', label: 'Not Enriched', icon: ScheduleIcon, description: 'Ready for enrichment', bgColor: '#f5f5f5' },
  'scraping': { color: '#FF9800', label: 'Enriching...', icon: CircularProgress, description: 'Gathering data from sources', bgColor: '#fff3e0', animated: true },
  'completed': { color: '#4CAF50', label: 'Enriched', icon: CheckCircleIcon, description: 'Data enrichment completed', bgColor: '#e8f5e8' },
  'failed': { color: '#F44336', label: 'Failed', icon: ErrorIcon, description: 'Enrichment encountered errors', bgColor: '#ffebee' },
};

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`entity-tabpanel-${index}`}
      aria-labelledby={`entity-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function EntityEnrichment() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedEntities, setSelectedEntities] = useState([]);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [enrichmentFilters, setEnrichmentFilters] = useState({
    entityTypes: [],
    status: [],
    minFrequency: 1,
  });

  const queryClient = useQueryClient();

  // Fetch all entities (Gateway-first; service fallback)
  const { data: entitiesData, isLoading: entitiesLoading, error: entitiesError } = useQuery(
    'entities',
    async () => {
      try {
        // 1) Prefer API Gateway search (single call, includes entities)
        const res = await api.get(`/search?q=*&size=1000`);
        const results = res.data?.results || [];

        const entitiesMap = {};
        results.forEach((hit) => {
          const source = hit?._source || {};
          const title = source.title || 'Untitled';
          const ents = source.openai_entities || [];
          ents.forEach((e) => {
            const name = (e?.text || '').trim();
            const type = (e?.type || 'UNKNOWN').toUpperCase();
            if (!name) return;
            const key = `${name}_${type}`;
            if (!entitiesMap[key]) {
              entitiesMap[key] = {
                id: key,
                name,
                type,
                frequency: 0,
                documents: [],
                enrichment_status: 'not_scraped',
                last_updated: null,
              };
            }
            entitiesMap[key].frequency += 1;
            entitiesMap[key].documents.push({ id: hit._id, title });
          });
        });

        const entities = Object.values(entitiesMap).sort((a, b) => b.frequency - a.frequency);
        
        // 2) Check enrichment status for each entity
        try {
          const enrichmentResponse = await api.get('/entities');
          const enrichedEntities = enrichmentResponse.data?.entities || [];
          
          // Create a map of enriched entities for quick lookup
          const enrichmentMap = {};
          enrichedEntities.forEach(enriched => {
            enrichmentMap[enriched.entity_id] = enriched;
          });
          
          // Update entities with enrichment status
          entities.forEach(entity => {
            const enriched = enrichmentMap[entity.id];
            if (enriched) {
              entity.enrichment_status = enriched.status || 'not_scraped';
              entity.enrichment_data = enriched;
              entity.last_updated = enriched.updated_at;
            }
          });
        } catch (enrichmentErr) {
          console.warn('Failed to fetch enrichment status:', enrichmentErr);
          // Continue with default status if enrichment service is unavailable
        }
        
        return { total: entities.length, entities };
      } catch (err) {
        // 3) Fallback attempt - but keep using gateway
        try {
          const response = await api.get('/entities');
          return response.data;
        } catch (e) {
          throw err;
        }
      }
    },
    {
      refetchInterval: 30000, // Poll every 30 seconds to avoid infinite loops
      staleTime: 10000,
      retry: 1, // Reduce retries
    }
  );

  // Enhanced state for notifications and tracking
  const [notification, setNotification] = useState(null);
  const [trackingEntities, setTrackingEntities] = useState(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Optimistic UI state management
  const [optimisticUpdates, setOptimisticUpdates] = useState(new Map());
  const [lastRefreshTime, setLastRefreshTime] = useState(Date.now());

  // Enhanced entity enrichment mutation with robust tracking
  const enrichMutation = useMutation(
    async (entityIds) => {
      console.log('🚀 Starting enrichment for entities:', entityIds);
      
      const response = await api.post('/entities/enrich', 
        { 
          entity_ids: entityIds,
          max_sources: 3 
        }
      );
      
      console.log('✅ Enrichment started successfully:', response.data);
      
      // Start tracking the enrichment progress
      startEnrichmentTracking(entityIds);
      
      return response.data;
    },
    {
      onSuccess: (data, entityIds) => {
        console.log('📊 Enrichment initiated for:', entityIds);
        
        // IMMEDIATE OPTIMISTIC UI UPDATE - Show progress instantly
        const updates = new Map(optimisticUpdates);
        entityIds.forEach(entityId => {
          updates.set(entityId, {
            status: 'processing',
            timestamp: Date.now(),
            message: 'Starting enrichment...'
          });
        });
        setOptimisticUpdates(updates);
        
        // Start tracking the enrichment progress
        startEnrichmentTracking(entityIds);
        
        // Refresh entities data
        queryClient.invalidateQueries('entities');
        setSelectedEntities([]);
        
        // Show success message
        setNotification({
          type: 'success',
          message: `🚀 Enrichment started for ${entityIds.length} entities. Watch live progress!`
        });
      },
      onError: (error) => {
        console.error('❌ Enrichment failed:', error);
        setNotification({
          type: 'error',
          message: `❌ Enrichment failed: ${error.response?.data?.message || error.message}`
        });
      }
    }
  );

  // Enhanced enrichment tracking function
  const startEnrichmentTracking = (entityIds) => {
    console.log('🔄 Starting live tracking for:', entityIds);
    
    // Add entities to tracking set
    setTrackingEntities(prev => {
      const newSet = new Set(prev);
      entityIds.forEach(id => newSet.add(id));
      return newSet;
    });

    // Track each entity individually
    entityIds.forEach(entityId => {
      trackEntityProgress(entityId);
    });
  };

  // Individual entity progress tracking
  const trackEntityProgress = async (entityId) => {
    let attempts = 0;
    const maxAttempts = 60; // Track for up to 5 minutes (60 * 5 seconds)
    
    const checkProgress = async () => {
      try {
        attempts++;
        console.log(`📊 Checking progress for ${entityId} (attempt ${attempts})`);
        
        const response = await api.get(`/entities/status/${entityId}`);
        const status = response.data.status;
        
        console.log(`🎯 ${entityId} status:`, status);
        
        if (status === 'completed' || status === 'failed') {
          console.log(`✅ ${entityId} finished with status: ${status}`);
          
          // IMMEDIATE OPTIMISTIC UI UPDATE - Show completion instantly
          const updates = new Map(optimisticUpdates);
          updates.set(entityId, {
            status: status,
            timestamp: Date.now(),
            message: status === 'completed' ? 'Enrichment completed!' : 'Enrichment failed',
            score: response.data.enrichment_score || null
          });
          setOptimisticUpdates(updates);
          
          // Remove from tracking
          setTrackingEntities(prev => {
            const newSet = new Set(prev);
            newSet.delete(entityId);
            return newSet;
          });
          
          // MULTIPLE REFRESH STRATEGIES for robustness
          queryClient.invalidateQueries('entities');
          setTimeout(() => queryClient.refetchQueries('entities'), 1000); // Delayed fallback
          setTimeout(() => queryClient.invalidateQueries('entities'), 3000); // Double fallback
          
          // Show completion notification
          const entityName = entityId.split('_')[0];
          setNotification({
            type: status === 'completed' ? 'success' : 'warning',
            message: status === 'completed' 
              ? `✅ ${entityName} enrichment completed! Click "View Results" to see details.` 
              : `⚠️ ${entityName} enrichment failed!`
          });
          
          return; // Stop tracking
        } else {
          // Update progress status
          const updates = new Map(optimisticUpdates);
          updates.set(entityId, {
            status: status,
            timestamp: Date.now(),
            message: status === 'scraping' ? 'Collecting data...' : 'Processing...'
          });
          setOptimisticUpdates(updates);
        }
        
        if (attempts < maxAttempts) {
          // Continue tracking
          setTimeout(checkProgress, 5000); // Check every 5 seconds
        } else {
          console.log(`⏰ Tracking timeout for ${entityId}`);
          setTrackingEntities(prev => {
            const newSet = new Set(prev);
            newSet.delete(entityId);
            return newSet;
          });
        }
        
      } catch (error) {
        console.error(`❌ Error tracking ${entityId}:`, error);
        
        if (attempts < maxAttempts) {
          setTimeout(checkProgress, 10000); // Retry in 10 seconds on error
        } else {
          setTrackingEntities(prev => {
            const newSet = new Set(prev);
            newSet.delete(entityId);
            return newSet;
          });
        }
      }
    };
    
    // Start checking after 2 seconds
    setTimeout(checkProgress, 2000);
  };

  // Get entity details
  const { data: entityDetails, isLoading: detailsLoading } = useQuery(
    ['entityDetails', selectedEntity?.id],
    async () => {
      if (!selectedEntity?.id) return null;
      const response = await api.get(`/entities/${selectedEntity.id}`);
      return response.data;
    },
    {
      enabled: !!selectedEntity?.id && (detailDialogOpen || resultsDialogOpen),
    }
  );

  const entities = entitiesData?.entities || [];
  const totalEntities = entitiesData?.total || 0;

  // Filter entities based on current filters
  const filteredEntities = entities.filter(entity => {
    if (enrichmentFilters.entityTypes.length > 0 && 
        !enrichmentFilters.entityTypes.includes(entity.type)) {
      return false;
    }
    if (enrichmentFilters.status.length > 0 && 
        !enrichmentFilters.status.includes(entity.enrichment_status)) {
      return false;
    }
    if (entity.frequency < enrichmentFilters.minFrequency) {
      return false;
    }
    return true;
  });

  // Entity statistics
  const entityStats = {
    total: totalEntities,
    byType: entities.reduce((acc, entity) => {
      acc[entity.type] = (acc[entity.type] || 0) + 1;
      return acc;
    }, {}),
    byStatus: entities.reduce((acc, entity) => {
      acc[entity.enrichment_status] = (acc[entity.enrichment_status] || 0) + 1;
      return acc;
    }, {}),
    highFrequency: entities.filter(e => e.frequency >= 5).length,
  };

  const handleEntitySelect = (entityId) => {
    setSelectedEntities(prev => 
      prev.includes(entityId) 
        ? prev.filter(id => id !== entityId)
        : [...prev, entityId]
    );
  };

  const handleSelectAll = () => {
    if (selectedEntities.length === filteredEntities.length) {
      setSelectedEntities([]);
    } else {
      setSelectedEntities(filteredEntities.map(e => e.id));
    }
  };

  const handleEnrichSelected = () => {
    if (selectedEntities.length > 0) {
      enrichMutation.mutate(selectedEntities);
    }
  };

  const handleEntityDetail = (entity) => {
    setSelectedEntity(entity);
    setDetailDialogOpen(true);
  };

  const handleQuickEnrichOrganizations = () => {
    if (selectedEntities.length > 0) {
      enrichMutation.mutate(selectedEntities);
    }
  };

  const handleSelectTopOrganizations = () => {
    const topOrgs = entities
      .filter(e => e.type === 'ORGANIZATION')
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10)
      .map(e => e.id);
    setSelectedEntities(topOrgs);
  };

  const getEntityIcon = (type) => {
    const config = ENTITY_CONFIG[type] || ENTITY_CONFIG.OTHER;
    const Icon = config.icon;
    return <Icon sx={{ color: config.color, fontSize: 20 }} />;
  };

  const getStatusChip = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.not_scraped;
    const Icon = config.icon;
    
    return (
      <Chip
        icon={status === 'scraping' ? <CircularProgress size={16} /> : <Icon />}
        label={config.label}
        size="small"
        sx={{ 
          backgroundColor: config.color,
          color: 'white',
          '& .MuiChip-icon': { color: 'white' }
        }}
      />
    );
  };

  // Enhanced status chip with optimistic updates and live tracking
  const getEnhancedStatusChip = (entity) => {
    const baseStatus = entity.enrichment_status || 'not_scraped';
    
    // CHECK OPTIMISTIC UPDATES FIRST - Immediate UI feedback
    const optimisticUpdate = optimisticUpdates.get(entity.id);
    const status = optimisticUpdate ? optimisticUpdate.status : baseStatus;
    const score = optimisticUpdate?.score || entity.enrichment_score;
    
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.not_scraped;
    const Icon = config.icon;
    const isBeingTracked = trackingEntities.has(entity.id);
    const isAnimated = config.animated && (status === 'scraping' || status === 'processing') || isBeingTracked;
    
    // Show live tracking status if being tracked
    const displayStatus = isBeingTracked && status === 'not_scraped' ? 'processing' : status;
    const displayConfig = STATUS_CONFIG[displayStatus] || config;
    
    // VISUAL FEEDBACK: Show if using optimistic data
    const isOptimistic = !!optimisticUpdate;
    const timeSinceUpdate = optimisticUpdate ? Date.now() - optimisticUpdate.timestamp : 0;
    
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 0.5 }}>
        <Chip
          icon={isAnimated ? <CircularProgress size={16} /> : <Icon />}
          label={
            isOptimistic && optimisticUpdate?.message ? 
              optimisticUpdate.message : 
              (isBeingTracked ? 'Live Tracking...' : displayConfig.label)
          }
          size="small"
          sx={{ 
            backgroundColor: isOptimistic ? '#e8f5e8' : (isBeingTracked ? '#e3f2fd' : (displayConfig.bgColor || displayConfig.color)),
            color: isOptimistic ? '#2e7d32' : (isBeingTracked ? '#1976d2' : 
                   (status === 'completed' ? '#4CAF50' : status === 'failed' ? '#F44336' : '#757575')),
            border: `2px solid ${isOptimistic ? '#4CAF50' : (isBeingTracked ? '#1976d2' : displayConfig.color)}`,
            '& .MuiChip-icon': { 
              color: isOptimistic ? '#2e7d32' : (isBeingTracked ? '#1976d2' : 
                     (status === 'completed' ? '#4CAF50' : status === 'failed' ? '#F44336' : '#757575'))
            },
            animation: (isBeingTracked || isOptimistic) ? 'pulse 2s infinite' : 'none',
            boxShadow: isOptimistic ? '0 0 10px rgba(76, 175, 80, 0.3)' : 'none'
          }}
        />
        
        {/* OPTIMISTIC UPDATE INDICATOR */}
        {isOptimistic && (
          <Typography variant="caption" sx={{ color: '#2e7d32', fontSize: '0.65rem', fontWeight: 'bold' }}>
            ⚡ Real-time Update
          </Typography>
        )}
        
        {/* PROGRESS MESSAGE */}
        {(displayConfig.description || isBeingTracked) && !isOptimistic && (
          <Typography variant="caption" sx={{ color: '#666', fontSize: '0.7rem' }}>
            {isBeingTracked ? 'Actively monitoring progress...' : displayConfig.description}
          </Typography>
        )}
        
        {/* COMPLETION DATE */}
        {entity.last_updated && status === 'completed' && !isOptimistic && (
          <Typography variant="caption" sx={{ color: '#999', fontSize: '0.65rem' }}>
            {new Date(entity.last_updated).toLocaleDateString()}
          </Typography>
        )}
        
        {/* LIVE TRACKING INDICATOR */}
        {isBeingTracked && !isOptimistic && (
          <Typography variant="caption" sx={{ color: '#1976d2', fontSize: '0.65rem', fontWeight: 'bold' }}>
            🔄 Live Updates Active
          </Typography>
        )}
      </Box>
    );
  };

  // Display enrichment score with optimistic updates
  const getEnrichmentScore = (entity) => {
    // Check optimistic updates first
    const optimisticUpdate = optimisticUpdates.get(entity.id);
    const status = optimisticUpdate ? optimisticUpdate.status : (entity.enrichment_status || 'not_scraped');
    const score = optimisticUpdate?.score || entity.enrichment_score || entity.enrichment_data?.enrichment_score;
    
    // Show loading for in-progress enrichments
    if (status === 'processing' || status === 'scraping') {
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
          <CircularProgress size={20} />
          <Typography variant="caption" sx={{ color: '#1976d2', fontSize: '0.7rem' }}>
            Processing...
          </Typography>
        </Box>
      );
    }
    
    if (!score || status !== 'completed') {
      return (
        <Typography variant="body2" sx={{ color: '#999' }}>
          --
        </Typography>
      );
    }

    const percentage = Math.round(score * 100);
    const color = percentage >= 80 ? '#4CAF50' : percentage >= 60 ? '#FF9800' : '#F44336';
    const isOptimistic = !!optimisticUpdate;
    
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
        <Typography 
          variant="body2" 
          sx={{ 
            fontWeight: 'bold', 
            color,
            textShadow: isOptimistic ? '0 0 5px rgba(76, 175, 80, 0.5)' : 'none'
          }}
        >
          {percentage}%
        </Typography>
        <LinearProgress 
          variant="determinate" 
          value={percentage} 
          sx={{ 
            width: 40, 
            height: 4,
            '& .MuiLinearProgress-bar': { 
              backgroundColor: color,
              boxShadow: isOptimistic ? `0 0 5px ${color}` : 'none'
            }
          }} 
        />
        {isOptimistic && (
          <Typography variant="caption" sx={{ color: '#2e7d32', fontSize: '0.6rem' }}>
            ⚡ Live
          </Typography>
        )}
      </Box>
    );
  };

  // AI Insights mutation
  const aiInsightsMutation = useMutation(
    async (entityId) => {
      console.log('🤖 Generating AI insights for:', entityId);
      const response = await enrichmentApi.post(`/entities/${entityId}/insights`);
      return response.data;
    },
    {
      onSuccess: (data, entityId) => {
        console.log('✨ AI insights generated for:', entityId);
        setNotification({
          type: 'success',
          message: '✨ AI insights generated successfully!'
        });
        // Refresh entity details
        queryClient.invalidateQueries(['entityDetails', entityId]);
      },
      onError: (error) => {
        console.error('❌ AI insights failed:', error);
        setNotification({
          type: 'error',
          message: `❌ AI insights failed: ${error.response?.data?.message || error.message}`
        });
      }
    }
  );

  // Handle viewing enrichment results
  const handleViewResults = (entity) => {
    setSelectedEntity(entity);
    setResultsDialogOpen(true);
  };

  // Generate AI insights for entity
  const generateInsights = (entityId) => {
    aiInsightsMutation.mutate(entityId);
  };

  if (entitiesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading entities...
        </Typography>
      </Box>
    );
  }

  if (entitiesError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load entities: {entitiesError.message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Entity Enrichment 🔍
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            disabled={selectedEntities.length === 0 || enrichMutation.isLoading}
            onClick={handleEnrichSelected}
          >
            {enrichMutation.isLoading ? 'Enriching...' : `Enrich Selected (${selectedEntities.length})`}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={async () => {
              if (isRefreshing) return;
              
              setIsRefreshing(true);
              console.log('🔄 Force refreshing entities data...');
              
              try {
                await queryClient.invalidateQueries('entities');
                await queryClient.refetchQueries('entities');
                
                setNotification({
                  type: 'success',
                  message: '✅ Entities data refreshed successfully!'
                });
              } catch (error) {
                console.error('❌ Refresh failed:', error);
                setNotification({
                  type: 'error',
                  message: '❌ Refresh failed. Please try again.'
                });
              } finally {
                setTimeout(() => setIsRefreshing(false), 2000); // Prevent rapid clicking
              }
            }}
            disabled={isRefreshing}
            sx={{ 
              color: '#1976d2', 
              borderColor: '#1976d2',
              '&:hover': { backgroundColor: '#e3f2fd' }
            }}
          >
            {isRefreshing ? 'Refreshing...' : 'Force Refresh'}
          </Button>
          
          {/* DATA VERIFICATION BUTTON - For troubleshooting */}
          <Button
            variant="text"
            size="small"
            onClick={async () => {
              console.log('🔍 Data Verification Check:');
              console.log('Optimistic Updates:', Object.fromEntries(optimisticUpdates));
              console.log('Tracking Entities:', Array.from(trackingEntities));
              
              // Direct API check
              try {
                const response = await api.get('/entities');
                const enrichedEntities = response.data.entities?.filter(e => e.enrichment_status === 'completed') || [];
                console.log('🔍 Backend Enriched Entities:', enrichedEntities.map(e => ({name: e.entity_name, status: e.enrichment_status, score: e.enrichment_score})));
                
                setNotification({
                  type: 'info',
                  message: `🔍 Found ${enrichedEntities.length} enriched entities in backend. Check console for details.`
                });
              } catch (error) {
                console.error('🔍 Verification failed:', error);
              }
            }}
            sx={{ color: '#9e9e9e', fontSize: '0.7rem' }}
          >
            🔍 Debug
          </Button>
        </Box>
      </Box>

      {/* Enhanced Notification System */}
      {notification && (
        <Alert 
          severity={notification.type} 
          sx={{ mb: 2 }}
          onClose={() => setNotification(null)}
        >
          <Typography variant="body1" sx={{ fontWeight: 500 }}>
            {notification.message}
          </Typography>
        </Alert>
      )}

      {/* Live Tracking Indicator */}
      {trackingEntities.size > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={20} />
            <Typography variant="body1">
              🔄 Live tracking {trackingEntities.size} entities in progress...
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Entities
              </Typography>
              <Typography variant="h4">
                {(entityStats.total || 0).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                High Frequency
              </Typography>
              <Typography variant="h4" color="primary">
                {entityStats.highFrequency}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                5+ occurrences
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Enriched
              </Typography>
              <Typography variant="h4" color="success.main">
                {entityStats.byStatus.completed || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Pending
              </Typography>
              <Typography variant="h4" color="warning.main">
                {entityStats.byStatus.not_scraped || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Card>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Entity List" />
            <Tab label="Type Overview" />
            <Tab label="Enrichment Queue" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            {/* Filters */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Entity Types</InputLabel>
                <Select
                  multiple
                  value={enrichmentFilters.entityTypes}
                  onChange={(e) => setEnrichmentFilters(prev => ({ ...prev, entityTypes: e.target.value }))}
                  input={<OutlinedInput label="Entity Types" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={ENTITY_CONFIG[value]?.label || value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {Object.keys(ENTITY_CONFIG).map((type) => (
                    <MenuItem key={type} value={type}>
                      <Checkbox checked={enrichmentFilters.entityTypes.indexOf(type) > -1} />
                      <ListItemText primary={ENTITY_CONFIG[type].label} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  multiple
                  value={enrichmentFilters.status}
                  onChange={(e) => setEnrichmentFilters(prev => ({ ...prev, status: e.target.value }))}
                  input={<OutlinedInput label="Status" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={STATUS_CONFIG[value]?.label || value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {Object.keys(STATUS_CONFIG).map((status) => (
                    <MenuItem key={status} value={status}>
                      <Checkbox checked={enrichmentFilters.status.indexOf(status) > -1} />
                      <ListItemText primary={STATUS_CONFIG[status].label} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            {/* Quick Actions */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                disabled={selectedEntities.length === 0 || enrichMutation.isLoading}
                onClick={() => handleQuickEnrichOrganizations()}
                startIcon={enrichMutation.isLoading ? <CircularProgress size={20} /> : <SearchIcon />}
              >
                {enrichMutation.isLoading ? 'Enriching...' : `Enrich Selected (${selectedEntities.length})`}
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => handleSelectTopOrganizations()}
                startIcon={<BusinessIcon />}
              >
                Select Top 10 Organizations
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => setSelectedEntities([])}
                disabled={selectedEntities.length === 0}
              >
                Clear Selection
              </Button>
            </Box>

            {/* Entity Table */}
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedEntities.length === filteredEntities.length && filteredEntities.length > 0}
                        indeterminate={selectedEntities.length > 0 && selectedEntities.length < filteredEntities.length}
                        onChange={handleSelectAll}
                      />
                    </TableCell>
                    <TableCell>Entity Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Frequency</TableCell>
                    <TableCell>Documents</TableCell>
                    <TableCell>Enrichment Status</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredEntities.slice(0, 50).map((entity) => (
                    <TableRow key={entity.id} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedEntities.includes(entity.id)}
                          onChange={() => handleEntitySelect(entity.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getEntityIcon(entity.type)}
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {entity.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={ENTITY_CONFIG[entity.type]?.label || entity.type}
                          size="small"
                          sx={{ backgroundColor: ENTITY_CONFIG[entity.type]?.color, color: 'white' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Badge badgeContent={entity.frequency} color="primary" max={99}>
                          <TrendingUpIcon />
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {entity.documents?.length || 0} docs
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {getEnhancedStatusChip(entity)}
                      </TableCell>
                      <TableCell>
                        {getEnrichmentScore(entity)}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="View Details">
                            <IconButton size="small" onClick={() => handleEntityDetail(entity)}>
                              <LaunchIcon />
                            </IconButton>
                          </Tooltip>
                          {(() => {
                            // Check optimistic updates for completed status
                            const optimisticUpdate = optimisticUpdates.get(entity.id);
                            const status = optimisticUpdate ? optimisticUpdate.status : entity.enrichment_status;
                            const isCompleted = status === 'completed';
                            const isOptimistic = !!optimisticUpdate && optimisticUpdate.status === 'completed';
                            
                            return isCompleted && (
                              <Tooltip title={isOptimistic ? "View Results (Live Data)" : "View Enrichment Results"}>
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleViewResults(entity)}
                                  sx={{
                                    color: isOptimistic ? '#4CAF50' : '#1976d2',
                                    backgroundColor: isOptimistic ? 'rgba(76, 175, 80, 0.1)' : 'transparent',
                                    '&:hover': {
                                      backgroundColor: isOptimistic ? 'rgba(76, 175, 80, 0.2)' : 'rgba(25, 118, 210, 0.1)'
                                    }
                                  }}
                                >
                                  <VisibilityIcon />
                                </IconButton>
                              </Tooltip>
                            );
                          })()}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {filteredEntities.length > 50 && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Showing first 50 of {filteredEntities.length} entities
                </Typography>
              </Box>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              {Object.entries(entityStats.byType).map(([type, count]) => {
                const config = ENTITY_CONFIG[type] || ENTITY_CONFIG.OTHER;
                const Icon = config.icon;
                return (
                  <Grid item xs={12} sm={6} md={4} key={type}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Icon sx={{ color: config.color, fontSize: 40 }} />
                          <Box>
                            <Typography variant="h5">{count}</Typography>
                            <Typography color="text.secondary">{config.label}</Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>Enrichment Queue Status</Typography>
            <Box sx={{ mt: 2 }}>
              {Object.entries(entityStats.byStatus).map(([status, count]) => {
                const config = STATUS_CONFIG[status] || STATUS_CONFIG.not_scraped;
                return (
                  <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    {getStatusChip(status)}
                    <Typography>{count} entities</Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={(count / totalEntities) * 100} 
                      sx={{ flexGrow: 1, ml: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {Math.round((count / totalEntities) * 100)}%
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Entity Detail Dialog */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Entity Details: {selectedEntity?.name}
        </DialogTitle>
        <DialogContent>
          {detailsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : entityDetails ? (
            <Box>
              <Typography variant="h6" gutterBottom>Basic Information</Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Typography color="text.secondary">Type:</Typography>
                  <Typography>{ENTITY_CONFIG[entityDetails.entity_type]?.label || entityDetails.entity_type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography color="text.secondary">Status:</Typography>
                  {getStatusChip(entityDetails.status || selectedEntity?.enrichment_status)}
                </Grid>
              </Grid>

              {entityDetails.consolidated_data && Object.keys(entityDetails.consolidated_data).length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>Enriched Data</Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(entityDetails.consolidated_data, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}

              {entityDetails.sources && entityDetails.sources.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>Sources</Typography>
                  {entityDetails.sources.map((source, index) => (
                    <Chip key={index} label={source} sx={{ mr: 1, mb: 1 }} />
                  ))}
                </Box>
              )}

              {entityDetails.conflicts && entityDetails.conflicts.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Alert severity="warning">
                    <Typography variant="subtitle2">Data Conflicts Detected</Typography>
                    {entityDetails.conflicts.map((conflict, index) => (
                      <Typography key={index} variant="body2">
                        {conflict.field}: {conflict.source1} says "{conflict.value1}" vs {conflict.source2} says "{conflict.value2}"
                      </Typography>
                    ))}
                  </Alert>
                </Box>
              )}
            </Box>
          ) : (
            <Typography>No enrichment data available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Enhanced Enrichment Results Dialog */}
      <Dialog 
        open={resultsDialogOpen} 
        onClose={() => setResultsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h5">
              🎯 Enrichment Results: {selectedEntity?.name}
            </Typography>
            {selectedEntity?.enrichment_score && (
              <Chip 
                label={`${Math.round(selectedEntity.enrichment_score * 100)}% Confidence`}
                color={selectedEntity.enrichment_score >= 0.8 ? 'success' : selectedEntity.enrichment_score >= 0.6 ? 'warning' : 'error'}
                sx={{ fontWeight: 'bold' }}
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          {detailsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Loading enrichment results...</Typography>
            </Box>
          ) : entityDetails?.consolidated_data ? (
            <Box>
              {/* Key Information Section */}
              {entityDetails.consolidated_data.name && (
                <Card sx={{ mb: 3, p: 2, backgroundColor: '#f8f9fa' }}>
                  <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
                    📊 Key Information
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(entityDetails.consolidated_data).slice(0, 8).map(([key, value]) => (
                      value && (
                        <Grid item xs={6} key={key}>
                          <Typography variant="subtitle2" sx={{ color: '#666', textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}:
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 500 }}>
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </Typography>
                        </Grid>
                      )
                    ))}
                  </Grid>
                </Card>
              )}

              {/* AI Summary Section */}
              {entityDetails.ai_summary && (
                <Card sx={{ mb: 3, p: 2, backgroundColor: '#e8f5e8' }}>
                  <Typography variant="h6" sx={{ mb: 2, color: '#2e7d32' }}>
                    🤖 AI Summary
                  </Typography>
                  <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                    {entityDetails.ai_summary}
                  </Typography>
                </Card>
              )}

              {/* Sources Section */}
              {entityDetails.sources && entityDetails.sources.length > 0 && (
                <Card sx={{ mb: 3, p: 2 }}>
                  <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
                    🌐 Data Sources ({entityDetails.sources.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {entityDetails.sources.map((source, index) => (
                      <Chip 
                        key={index} 
                        label={source.replace('https://', '').replace('www.', '')} 
                        variant="outlined"
                        sx={{ 
                          backgroundColor: '#e3f2fd',
                          '&:hover': { backgroundColor: '#bbdefb' }
                        }}
                      />
                    ))}
                  </Box>
                </Card>
              )}

              {/* Complete Data Section */}
              <Card sx={{ mb: 3, p: 2 }}>
                <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
                  📋 Complete Enriched Data
                </Typography>
                <Paper sx={{ p: 2, backgroundColor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                    {JSON.stringify(entityDetails.consolidated_data, null, 2)}
                  </pre>
                </Paper>
              </Card>

              {/* Conflicts Section */}
              {entityDetails.conflicts && entityDetails.conflicts.length > 0 && (
                <Card sx={{ p: 2 }}>
                  <Alert severity="warning">
                    <Typography variant="h6" gutterBottom>⚠️ Data Conflicts Detected</Typography>
                    {entityDetails.conflicts.map((conflict, index) => (
                      <Typography key={index} variant="body2" sx={{ mt: 1 }}>
                        <strong>{conflict.field}:</strong> {conflict.source1} says "{conflict.value1}" vs {conflict.source2} says "{conflict.value2}"
                      </Typography>
                    ))}
                  </Alert>
                </Card>
              )}
            </Box>
          ) : (
            <Alert severity="info">
              <Typography variant="h6">No enrichment data available</Typography>
              <Typography>This entity has not been enriched yet or enrichment failed.</Typography>
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
          <Button onClick={() => setResultsDialogOpen(false)} variant="outlined">
            Close
          </Button>
          
          {selectedEntity?.enrichment_status === 'completed' && (
            <>
              <Button 
                variant="outlined"
                startIcon={<PsychologyIcon />}
                onClick={() => generateInsights(selectedEntity.id)}
                disabled={aiInsightsMutation.isLoading}
                sx={{ color: '#9C27B0', borderColor: '#9C27B0' }}
              >
                {aiInsightsMutation.isLoading ? 'Generating...' : '🤖 Generate AI Insights'}
              </Button>
              
              <Button 
                variant="contained" 
                startIcon={<RefreshIcon />}
                onClick={() => {
                  // Re-enrich this entity
                  enrichMutation.mutate([selectedEntity.id]);
                  setResultsDialogOpen(false);
                }}
              >
                Re-Enrich
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default EntityEnrichment;