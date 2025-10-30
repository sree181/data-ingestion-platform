import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Paper
} from '@mui/material';
import {
  Psychology as RLIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  TrendingUp as AccuracyIcon,
  Memory as MemoryIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';

const RLMetricsPanel = ({ projectId, onRLConfigChange }) => {
  const [refreshKey, setRefreshKey] = useState(0);
  
  // Fetch RL metrics
  const { data: rlMetrics, isLoading, error, refetch } = useQuery(
    ['rl-metrics', projectId, refreshKey],
    () => apiService.rl.getRLMetrics(projectId),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 10000,
      onError: (error) => {
        console.error('RL metrics fetch error:', error);
      }
    }
  );

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    refetch();
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Loading RL metrics...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            Failed to load RL metrics. Please check if the RL service is running.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const metrics = rlMetrics || {
    accuracy: 0.0,
    confidence: 0.0,
    processing_time: 0,
    cost_efficiency: 0.0,
    model_performance: {},
    recent_decisions: [],
    status: 'inactive'
  };

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
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <RLIcon color="primary" />
            <Typography variant="h6">RL Performance Metrics</Typography>
            <Chip
              icon={getStatusIcon(metrics.status)}
              label={metrics.status?.toUpperCase() || 'UNKNOWN'}
              color={getStatusColor(metrics.status)}
              size="small"
            />
          </Box>
        }
        action={
          <Tooltip title="Refresh RL Metrics">
            <IconButton onClick={handleRefresh} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* Key Metrics */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Performance Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <AccuracyIcon color="primary" />
                  <Typography variant="h6" color="primary">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Accuracy
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <SpeedIcon color="secondary" />
                  <Typography variant="h6" color="secondary">
                    {metrics.processing_time}ms
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Avg Processing
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Grid>

          {/* Confidence Score */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Classification Confidence
            </Typography>
            <Box display="flex" alignItems="center" gap={2}>
              <LinearProgress
                variant="determinate"
                value={metrics.confidence * 100}
                sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" fontWeight="bold">
                {(metrics.confidence * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Grid>

          {/* Model Performance */}
          {metrics.model_performance && Object.keys(metrics.model_performance).length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                Model Performance
              </Typography>
              <List dense>
                {Object.entries(metrics.model_performance).map(([model, performance]) => (
                  <ListItem key={model} sx={{ px: 0 }}>
                    <ListItemIcon>
                      <TrendingUpIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={model.replace('_', ' ').toUpperCase()}
                      secondary={`${(performance * 100).toFixed(1)}% accuracy`}
                    />
                    <Chip
                      label={`${(performance * 100).toFixed(0)}%`}
                      size="small"
                      color={performance > 0.8 ? 'success' : performance > 0.6 ? 'warning' : 'error'}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          )}

          {/* Recent Decisions */}
          {metrics.recent_decisions && metrics.recent_decisions.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                Recent RL Decisions
              </Typography>
              <List dense>
                {metrics.recent_decisions.slice(0, 3).map((decision, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon>
                      <MemoryIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={decision.action || 'Unknown Action'}
                      secondary={`Confidence: ${((decision.confidence || 0) * 100).toFixed(1)}%`}
                    />
                    <Chip
                      label={decision.status || 'pending'}
                      size="small"
                      color={decision.status === 'success' ? 'success' : 'default'}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          )}

          {/* Cost Efficiency */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Cost Efficiency
            </Typography>
            <Box display="flex" alignItems="center" gap={2}>
              <LinearProgress
                variant="determinate"
                value={metrics.cost_efficiency * 100}
                sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                color="success"
              />
              <Typography variant="body2" fontWeight="bold">
                ${(metrics.cost_efficiency * 100).toFixed(2)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />

        {/* Action Buttons */}
        <Box display="flex" gap={1} justifyContent="flex-end">
          <Tooltip title="Configure RL Parameters">
            <IconButton
              size="small"
              onClick={() => onRLConfigChange && onRLConfigChange()}
            >
              <InfoIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};

export default RLMetricsPanel;
