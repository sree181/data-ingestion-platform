import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Grid,
  Paper,
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
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button
} from '@mui/material';
import {
  Psychology as RLIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  TrendingUp as AccuracyIcon,
  Memory as MemoryIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';

const RLDecisionVisualization = ({ documentId, onDecisionSelect }) => {
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  
  // Fetch RL decision data
  const { data: decisionData, isLoading, error, refetch } = useQuery(
    ['rl-decisions', documentId],
    () => apiService.getRLDecisions(documentId),
    {
      enabled: !!documentId,
      refetchInterval: 5000, // Refresh every 5 seconds
      staleTime: 2000,
    }
  );

  const handleDecisionSelect = (decision) => {
    setSelectedDecision(decision);
    onDecisionSelect && onDecisionSelect(decision);
  };

  const startAnimation = () => {
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 3000);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
            <Typography variant="body2" sx={{ ml: 2 }}>
              Loading RL decisions...
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
            Failed to load RL decision data. Please check if the RL service is running.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const decisions = decisionData?.decisions || [];
  const currentDecision = decisionData?.current_decision;

  const getDecisionStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getDecisionStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircleIcon />;
      case 'processing': return <CircularProgress size={16} />;
      case 'failed': return <ErrorIcon />;
      default: return <WarningIcon />;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <RLIcon color="primary" />
            <Typography variant="h6">RL Decision Visualization</Typography>
            <Chip
              icon={<TimelineIcon />}
              label={`${decisions.length} Decisions`}
              color="primary"
              size="small"
            />
          </Box>
        }
        action={
          <Box display="flex" gap={1}>
            <Tooltip title="Start Animation">
              <IconButton onClick={startAnimation} size="small">
                <PlayIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh Decisions">
              <IconButton onClick={() => refetch()} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <CardContent>
        {/* Current Decision */}
        {currentDecision && (
          <Box mb={3}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Current Decision
            </Typography>
            <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <Typography variant="h6">
                    {currentDecision.action || 'Unknown Action'}
                  </Typography>
                  <Typography variant="body2">
                    {currentDecision.reasoning || 'No reasoning provided'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    <Chip
                      icon={getDecisionStatusIcon(currentDecision.status)}
                      label={currentDecision.status?.toUpperCase() || 'UNKNOWN'}
                      color={getDecisionStatusColor(currentDecision.status)}
                      size="small"
                    />
                    <Chip
                      label={`${((currentDecision.confidence || 0) * 100).toFixed(1)}%`}
                      color="secondary"
                      size="small"
                    />
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Box>
        )}

        {/* Decision Timeline */}
        <Typography variant="subtitle2" gutterBottom color="text.secondary">
          Decision Timeline
        </Typography>
        
        <Stepper orientation="vertical" sx={{ mb: 3 }}>
          {decisions.map((decision, index) => (
            <Step key={index} active={selectedDecision?.id === decision.id}>
              <StepLabel
                icon={
                  <Badge
                    badgeContent={index + 1}
                    color="primary"
                    sx={{ '& .MuiBadge-badge': { fontSize: '0.7rem' } }}
                  >
                    {getDecisionStatusIcon(decision.status)}
                  </Badge>
                }
                onClick={() => handleDecisionSelect(decision)}
                sx={{ cursor: 'pointer' }}
              >
                <Box>
                  <Typography variant="subtitle2">
                    {decision.action || 'Unknown Action'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </Typography>
                </Box>
              </StepLabel>
              <StepContent>
                <Paper sx={{ p: 2, mt: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" gutterBottom>
                        <strong>Reasoning:</strong> {decision.reasoning || 'No reasoning provided'}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Models Used:</strong> {decision.models_used?.join(', ') || 'None'}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Processing Time:</strong> {decision.processing_time || 0}ms
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box display="flex" flexDirection="column" gap={1}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2">Confidence:</Typography>
                          <LinearProgress
                            variant="determinate"
                            value={(decision.confidence || 0) * 100}
                            sx={{ flexGrow: 1, height: 6 }}
                          />
                          <Typography variant="caption">
                            {((decision.confidence || 0) * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2">Cost:</Typography>
                          <LinearProgress
                            variant="determinate"
                            value={(decision.cost_estimate || 0) * 100}
                            sx={{ flexGrow: 1, height: 6 }}
                            color="secondary"
                          />
                          <Typography variant="caption">
                            ${(decision.cost_estimate || 0).toFixed(2)}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </Paper>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        {/* Decision Details */}
        {selectedDecision && (
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">
                Decision Details: {selectedDecision.action}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <AccuracyIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Accuracy"
                        secondary={`${((selectedDecision.accuracy || 0) * 100).toFixed(1)}%`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <SpeedIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Processing Time"
                        secondary={`${selectedDecision.processing_time || 0}ms`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <MemoryIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Memory Usage"
                        secondary={`${selectedDecision.memory_usage || 0}MB`}
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    RL Parameters
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="State Space"
                        secondary={`${selectedDecision.state_dimensions || 0} dimensions`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Action Space"
                        secondary={`${selectedDecision.action_dimensions || 0} actions`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Reward"
                        secondary={`${(selectedDecision.reward || 0).toFixed(3)}`}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Animation Controls */}
        <Box mt={2} display="flex" justifyContent="center" gap={2}>
          <Button
            variant="outlined"
            startIcon={<PlayIcon />}
            onClick={startAnimation}
            disabled={isAnimating}
            size="small"
          >
            Animate
          </Button>
          <Button
            variant="outlined"
            startIcon={<PauseIcon />}
            onClick={() => setIsAnimating(false)}
            disabled={!isAnimating}
            size="small"
          >
            Pause
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default RLDecisionVisualization;
