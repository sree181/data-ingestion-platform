import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Switch,
  FormControlLabel,
  TextField,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  Paper,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  ExpandMore as ExpandMoreIcon,
  Source as SourceIcon,
  Api as ApiIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import apiService from '../services/api';

// Source configuration data
const SOURCE_DETAILS = {
  clinicaltrials: {
    name: 'ClinicalTrials.gov',
    description: 'US National Library of Medicine clinical trials database',
    category: 'Clinical Trials',
    icon: <SourceIcon />,
    color: '#1976d2',
    status: 'active',
    lastSync: '2025-10-02T10:30:00Z',
    documentsCount: 456789,
    apiKeyRequired: false,
    rateLimit: '1 req/sec',
    endpoints: ['studies'],
    features: ['Real-time data', 'Global coverage', 'Detailed trial info'],
    setupSteps: [
      'No API key required',
      'Rate limit: 1 request per second',
      'Data updated daily'
    ]
  },
  fda: {
    name: 'FDA OpenFDA',
    description: 'US Food and Drug Administration open data',
    category: 'Regulatory',
    icon: <SecurityIcon />,
    color: '#d32f2f',
    status: 'active',
    lastSync: '2025-10-02T10:25:00Z',
    documentsCount: 1234567,
    apiKeyRequired: false,
    rateLimit: '1 req/sec',
    endpoints: ['drug/event', 'drug/label'],
    features: ['Adverse events', 'Drug labels', 'Safety data'],
    setupSteps: [
      'No API key required',
      'Rate limit: 1 request per second',
      'Data updated hourly'
    ]
  },
  chembl: {
    name: 'ChEMBL',
    description: 'EMBL-EBI chemical database of bioactive molecules',
    category: 'Chemical',
    icon: <ApiIcon />,
    color: '#388e3c',
    status: 'inactive',
    lastSync: null,
    documentsCount: 0,
    apiKeyRequired: true,
    rateLimit: '2 req/sec',
    endpoints: ['molecule', 'activity'],
    features: ['2.3M+ compounds', '19M+ bioactivity data', 'Drug targets'],
    setupSteps: [
      'Register at https://www.ebi.ac.uk/chembl/',
      'Get your API key',
      'Enter API key below',
      'Test connection'
    ]
  },
  semanticscholar: {
    name: 'Semantic Scholar',
    description: 'AI-powered research tool for scientific literature',
    category: 'Research',
    icon: <SpeedIcon />,
    color: '#7b1fa2',
    status: 'active',
    lastSync: '2025-10-02T10:20:00Z',
    documentsCount: 2345678,
    apiKeyRequired: false,
    rateLimit: '5 req/sec',
    endpoints: ['paper/search', 'paper'],
    features: ['200M+ papers', 'AI recommendations', 'Citation metrics'],
    setupSteps: [
      'No API key required',
      'Rate limit: 5 requests per second',
      'Data updated daily'
    ]
  },
  europepmc: {
    name: 'Europe PMC',
    description: 'European PubMed Central - European research papers',
    category: 'Research',
    icon: <StorageIcon />,
    color: '#f57c00',
    status: 'active',
    lastSync: '2025-10-02T10:15:00Z',
    documentsCount: 3456789,
    apiKeyRequired: false,
    rateLimit: '3 req/sec',
    endpoints: ['search'],
    features: ['European papers', 'Full text access', 'MeSH terms'],
    setupSteps: [
      'No API key required',
      'Rate limit: 3 requests per second',
      'Data updated daily'
    ]
  }
};

function SourceConfiguration() {
  const theme = useTheme();
  const queryClient = useQueryClient();
  
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [editingSource, setEditingSource] = useState(null);
  const [apiKeys, setApiKeys] = useState({});
  const [showApiKey, setShowApiKey] = useState({});
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [setupStep, setSetupStep] = useState(0);
  const [newApiKey, setNewApiKey] = useState('');

  // Queries
  const { data: sourcesData, isLoading: sourcesLoading, error: sourcesError } = useQuery(
    'sources',
    () => apiService.getSources(),
    { staleTime: 5 * 60 * 1000 }
  );

  const { data: healthStatus, isLoading: healthLoading } = useQuery(
    'source-health',
    () => apiService.getSourceHealth(),
    { 
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 0
    }
  );
  
  // Extract sources array from API response
  const sources = sourcesData?.sources || [];
  
  // Debug logging
  console.log('SourceConfiguration - sourcesData:', sourcesData);
  console.log('SourceConfiguration - sources:', sources);
  console.log('SourceConfiguration - sources.length:', sources.length);

  // Mutations
  const enableSourceMutation = useMutation(
    (sourceId) => apiService.enableSource(sourceId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sources');
        toast.success('Source enabled successfully');
      },
      onError: (error) => {
        toast.error(`Failed to enable source: ${error.message}`);
      }
    }
  );

  const disableSourceMutation = useMutation(
    (sourceId) => apiService.disableSource(sourceId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sources');
        toast.success('Source disabled successfully');
      },
      onError: (error) => {
        toast.error(`Failed to disable source: ${error.message}`);
      }
    }
  );

  const updateApiKeyMutation = useMutation(
    ({ sourceId, apiKey }) => apiService.updateSourceConfig(sourceId, { api_key: apiKey }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sources');
        toast.success('API key updated successfully');
      },
      onError: (error) => {
        toast.error(`Failed to update API key: ${error.message}`);
      }
    }
  );

  // Handle source toggle
  const handleSourceToggle = (sourceId, enabled) => {
    if (enabled) {
      enableSourceMutation.mutate(sourceId);
    } else {
      disableSourceMutation.mutate(sourceId);
    }
  };

  // Handle API key update
  const handleApiKeyUpdate = (sourceId) => {
    if (newApiKey.trim()) {
      updateApiKeyMutation.mutate({ sourceId, apiKey: newApiKey });
      setNewApiKey('');
      setSetupDialogOpen(false);
    }
  };

  // Handle setup dialog
  const handleSetupClick = (sourceId) => {
    setEditingSource(sourceId);
    setSetupDialogOpen(true);
    setSetupStep(0);
    setNewApiKey('');
  };

  // Get source status
  const getSourceStatus = (sourceId) => {
    const health = healthStatus?.sources?.[sourceId];
    if (!health) return 'unknown';
    return health.status;
  };

  // Get source status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'unhealthy': return 'error';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  // Get source status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'unhealthy': return <ErrorIcon color="error" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <WarningIcon color="warning" />;
    }
  };

  // Format last sync time
  const formatLastSync = (lastSync) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (sourcesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  if (sourcesError) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">
          Failed to load sources: {sourcesError.message}
        </Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'text.primary' }}>
            ⚙️ Source Configuration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage data sources, API keys, and synchronization settings
          </Typography>
        </Container>
      </Paper>

      <Container maxWidth="lg">
        {/* Tabs */}
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="All Sources" />
            <Tab label="Active Sources" />
            <Tab label="Inactive Sources" />
            <Tab label="Health Status" />
          </Tabs>
        </Paper>

        {/* Sources Grid */}
        <Grid container spacing={3}>
          {sources.map((source) => {
            const sourceId = source.id;
            const sourceDetails = SOURCE_DETAILS[sourceId] || {};
            const status = source.health_status || 'unknown';
            const isActive = source.enabled;
            const health = healthStatus?.sources?.[sourceId];
            
            return (
              <Grid item xs={12} md={6} lg={4} key={sourceId}>
                <Card 
                  elevation={2} 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    border: isActive ? `2px solid ${source.color || sourceDetails.color || '#1976d2'}` : 'none'
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    {/* Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ color: source.color || sourceDetails.color || '#1976d2' }}>
                          {sourceDetails.icon || <SourceIcon />}
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {source.display_name || source.name}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(status)}
                        <FormControlLabel
                          control={
                            <Switch
                              checked={isActive}
                              onChange={(e) => handleSourceToggle(sourceId, e.target.checked)}
                              color="primary"
                            />
                          }
                          label=""
                        />
                      </Box>
                    </Box>

                    {/* Description */}
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {source.description}
                    </Typography>

                    {/* Stats */}
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                      <Box>
                        <Typography variant="h6" color="primary">
                          {(source.documents_count || 0).toLocaleString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Documents
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h6" color="text.secondary">
                          {source.rate_limit || '1 req/sec'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Rate Limit
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h6" color="text.secondary">
                          {formatLastSync(source.last_sync_at)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Last Sync
                        </Typography>
                      </Box>
                    </Box>

                    {/* Features */}
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                        Features:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(source.features || sourceDetails.features || []).map((feature, index) => (
                          <Chip
                            key={index}
                            label={feature}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>

                    {/* API Key Status */}
                    {source.api_key_required && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          API Key:
                        </Typography>
                        <Chip
                          label={source.api_key_configured ? 'Configured' : 'Required'}
                          color={source.api_key_configured ? 'success' : 'warning'}
                          size="small"
                        />
                      </Box>
                    )}

                    {/* Health Status */}
                    {health && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          Health:
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={status}
                            color={getStatusColor(status)}
                            size="small"
                          />
                          {health.response_time_ms && (
                            <Typography variant="caption" color="text.secondary">
                              {health.response_time_ms}ms
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    )}
                  </CardContent>

                  <CardActions sx={{ p: 2, pt: 0 }}>
                    <Button
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => handleSetupClick(sourceId)}
                    >
                      Configure
                    </Button>
                    <Button
                      size="small"
                      startIcon={<RefreshIcon />}
                      onClick={() => apiService.refreshSource(sourceId).then(() => {
                        queryClient.invalidateQueries('sources');
                        queryClient.invalidateQueries('source-health');
                      })}
                    >
                      Refresh
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* Setup Dialog */}
        <Dialog 
          open={setupDialogOpen} 
          onClose={() => setSetupDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Setup {editingSource && (SOURCE_DETAILS[editingSource]?.name || sources.find(s => s.id === editingSource)?.display_name)}
          </DialogTitle>
          <DialogContent>
            {editingSource && SOURCE_DETAILS[editingSource]?.setupSteps && (
              <Stepper activeStep={setupStep} orientation="vertical">
                {SOURCE_DETAILS[editingSource].setupSteps.map((step, index) => (
                  <Step key={index}>
                    <StepLabel>{step}</StepLabel>
                    <StepContent>
                      {index === 2 && SOURCE_DETAILS[editingSource].apiKeyRequired && (
                        <Box sx={{ mt: 2 }}>
                          <TextField
                            fullWidth
                            label="API Key"
                            type={showApiKey[editingSource] ? 'text' : 'password'}
                            value={newApiKey}
                            onChange={(e) => setNewApiKey(e.target.value)}
                            InputProps={{
                              endAdornment: (
                                <IconButton
                                  onClick={() => setShowApiKey(prev => ({ ...prev, [editingSource]: !prev[editingSource] }))}
                                >
                                  {showApiKey[editingSource] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              )
                            }}
                          />
                        </Box>
                      )}
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            )}
            {editingSource && !SOURCE_DETAILS[editingSource]?.setupSteps && (
              <Box sx={{ p: 3 }}>
                <Typography variant="body1" gutterBottom>
                  Configure {sources.find(s => s.id === editingSource)?.display_name}
                </Typography>
                <TextField
                  fullWidth
                  label="API Key"
                  type={showApiKey[editingSource] ? 'text' : 'password'}
                  value={newApiKey}
                  onChange={(e) => setNewApiKey(e.target.value)}
                  sx={{ mt: 2 }}
                  InputProps={{
                    endAdornment: (
                      <IconButton
                        onClick={() => setShowApiKey(prev => ({ ...prev, [editingSource]: !prev[editingSource] }))}
                      >
                        {showApiKey[editingSource] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    )
                  }}
                />
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSetupDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={() => handleApiKeyUpdate(editingSource)}
              variant="contained"
              disabled={!newApiKey.trim()}
            >
              Save
            </Button>
          </DialogActions>
        </Dialog>

        {/* Health Status Summary */}
        {activeTab === 3 && healthStatus && (
          <Paper elevation={1} sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Health Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="success.main">
                    {healthStatus.statistics?.healthy_sources || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Healthy Sources
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="error.main">
                    {healthStatus.statistics?.unhealthy_sources || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Unhealthy Sources
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="primary.main">
                    {healthStatus.statistics?.total_sources || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Sources
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        )}
      </Container>
    </Box>
  );
}

export default SourceConfiguration;
