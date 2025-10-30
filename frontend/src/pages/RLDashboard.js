import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  Psychology as RLIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  TrendingUp as AccuracyIcon,
  Memory as MemoryIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Tune as TuneIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiService } from '../services/api';

// Import our RL components
import RLMetricsPanel from '../components/RLMetricsPanel';
import RLClassificationControls from '../components/RLClassificationControls';
import RLDecisionVisualization from '../components/RLDecisionVisualization';

const RLDashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [trainingDialogOpen, setTrainingDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  
  const queryClient = useQueryClient();

  // Fetch RL system status
  const { data: rlStatus, isLoading: statusLoading, error: statusError } = useQuery(
    'rl-status',
    () => apiService.rl.getRLStatus(),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
      staleTime: 5000,
    }
  );

  // Fetch RL configuration
  const { data: rlConfig, isLoading: configLoading } = useQuery(
    'rl-config',
    () => apiService.rl.getRLConfig(),
    {
      staleTime: 30000,
    }
  );

  // Fetch recent documents for RL analysis
  const { data: recentDocuments, isLoading: documentsLoading } = useQuery(
    'recent-documents',
    () => apiService.rl.getRecentDocuments({ limit: 10 }),
    {
      staleTime: 60000,
    }
  );

  // RL configuration mutation
  const updateRLConfig = useMutation(
    (newConfig) => apiService.rl.updateRLConfig(newConfig),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('rl-config');
        setConfigDialogOpen(false);
      },
    }
  );

  // RL training mutation
  const startRLTraining = useMutation(
    (trainingParams) => apiService.rl.startRLTraining(trainingParams),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('rl-status');
        setTrainingDialogOpen(false);
      },
    }
  );

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleRLConfigChange = (newConfig) => {
    updateRLConfig.mutate(newConfig);
  };

  const handleRLToggle = (enabled) => {
    const newConfig = { ...rlConfig, enableRL: enabled };
    updateRLConfig.mutate(newConfig);
  };

  const handleRLTraining = (trainingParams) => {
    startRLTraining.mutate(trainingParams);
  };

  const handleDocumentSelect = (document) => {
    setSelectedDocument(document);
  };

  if (statusLoading || configLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading RL Dashboard...
        </Typography>
      </Box>
    );
  }

  if (statusError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load RL Dashboard. Please check if the RL service is running.
        </Alert>
      </Box>
    );
  }

  const status = rlStatus || { status: 'inactive', metrics: {} };
  const config = rlConfig || { enableRL: false };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'training': return 'warning';
      case 'inactive': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircleIcon />;
      case 'training': return <CircularProgress size={16} />;
      case 'inactive': return <WarningIcon />;
      default: return <ErrorIcon />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <RLIcon color="primary" sx={{ fontSize: 32 }} />
          <Box>
            <Typography variant="h4" component="h1">
              RL Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Reinforcement Learning Enhanced Classification System
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2}>
          <Chip
            icon={getStatusIcon(status.status)}
            label={status.status?.toUpperCase() || 'UNKNOWN'}
            color={getStatusColor(status.status)}
            size="large"
          />
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setConfigDialogOpen(true)}
          >
            Configure
          </Button>
        </Box>
      </Box>

      {/* Status Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <AccuracyIcon color="primary" />
                <Box>
                  <Typography variant="h6" color="primary">
                    {((status.metrics?.accuracy || 0) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Accuracy
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <SpeedIcon color="secondary" />
                <Box>
                  <Typography variant="h6" color="secondary">
                    {status.metrics?.processing_time || 0}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Processing
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <MemoryIcon color="info" />
                <Box>
                  <Typography variant="h6" color="info.main">
                    {status.metrics?.memory_usage || 0}MB
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Memory Usage
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <TrendingUpIcon color="success" />
                <Box>
                  <Typography variant="h6" color="success.main">
                    ${(status.metrics?.cost_efficiency || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Cost Efficiency
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<AssessmentIcon />}
            label="Performance Metrics"
            iconPosition="start"
          />
          <Tab
            icon={<TuneIcon />}
            label="Classification Controls"
            iconPosition="start"
          />
          <Tab
            icon={<TimelineIcon />}
            label="Decision Visualization"
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <RLMetricsPanel
                projectId="default"
                onRLConfigChange={() => setConfigDialogOpen(true)}
              />
            </Grid>
            <Grid item xs={12} lg={4}>
              <Card>
                <CardHeader title="Recent Activity" />
                <CardContent>
                  <List dense>
                    {status.recent_activity?.slice(0, 5).map((activity, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircleIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={activity.action}
                          secondary={new Date(activity.timestamp).toLocaleString()}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <RLClassificationControls
                onRLConfigChange={handleRLConfigChange}
                onRLToggle={handleRLToggle}
                onRLTraining={() => setTrainingDialogOpen(true)}
                rlEnabled={config.enableRL}
                rlConfig={config}
                isTraining={status.status === 'training'}
              />
            </Grid>
            <Grid item xs={12} lg={4}>
              <Card>
                <CardHeader title="Model Performance" />
                <CardContent>
                  <List dense>
                    {status.model_performance?.map((model, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={model.name}
                          secondary={`${(model.accuracy * 100).toFixed(1)}% accuracy`}
                        />
                        <Chip
                          label={`${(model.accuracy * 100).toFixed(0)}%`}
                          size="small"
                          color={model.accuracy > 0.8 ? 'success' : 'warning'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 2 && (
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <RLDecisionVisualization
                documentId={selectedDocument?.id}
                onDecisionSelect={handleDocumentSelect}
              />
            </Grid>
            <Grid item xs={12} lg={4}>
              <Card>
                <CardHeader title="Recent Documents" />
                <CardContent>
                  <List dense>
                    {recentDocuments?.slice(0, 5).map((doc) => (
                      <ListItem
                        key={doc.id}
                        button
                        onClick={() => handleDocumentSelect(doc)}
                        selected={selectedDocument?.id === doc.id}
                      >
                        <ListItemText
                          primary={doc.title}
                          secondary={doc.classification}
                        />
                        <Chip
                          label={doc.confidence}
                          size="small"
                          color="primary"
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>

      {/* Configuration Dialog */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>RL Configuration</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Configure reinforcement learning parameters for optimal performance.
          </Typography>
          {/* Configuration form would go here */}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setConfigDialogOpen(false)}>
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>

      {/* Training Dialog */}
      <Dialog
        open={trainingDialogOpen}
        onClose={() => setTrainingDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Start RL Training</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Configure training parameters for the reinforcement learning agent.
          </Typography>
          {/* Training form would go here */}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrainingDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setTrainingDialogOpen(false)}>
            Start Training
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RLDashboard;
