import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Switch,
  FormControlLabel,
  Slider,
  Button,
  Chip,
  Alert,
  Grid,
  Paper,
  Tooltip,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge
} from '@mui/material';
import {
  Psychology as RLIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

const RLClassificationControls = ({ 
  onRLConfigChange, 
  onRLToggle, 
  onRLTraining,
  rlEnabled = false,
  rlConfig = {},
  isTraining = false 
}) => {
  const [localConfig, setLocalConfig] = useState({
    enableRL: rlEnabled,
    confidenceThreshold: rlConfig.confidence_threshold || 0.75,
    costBudget: rlConfig.cost_budget || 100,
    maxProcessingTime: rlConfig.max_processing_time || 5000,
    modelSelection: rlConfig.model_selection || 'auto',
    optimizationMode: rlConfig.optimization_mode || 'balanced',
    ...rlConfig
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleConfigChange = (key, value) => {
    const newConfig = { ...localConfig, [key]: value };
    setLocalConfig(newConfig);
    onRLConfigChange && onRLConfigChange(newConfig);
  };

  const handleRLToggle = () => {
    const newEnabled = !localConfig.enableRL;
    handleConfigChange('enableRL', newEnabled);
    onRLToggle && onRLToggle(newEnabled);
  };

  const handleTrainingStart = () => {
    onRLTraining && onRLTraining(localConfig);
  };

  const getOptimizationModeColor = (mode) => {
    switch (mode) {
      case 'accuracy': return 'error';
      case 'speed': return 'warning';
      case 'cost': return 'info';
      case 'balanced': return 'success';
      default: return 'default';
    }
  };

  const getModelSelectionInfo = (selection) => {
    switch (selection) {
      case 'auto': return 'RL automatically selects best models';
      case 'rule_based': return 'Use only rule-based classification';
      case 'ensemble': return 'Use full ensemble (rule + BERT + LLM)';
      case 'custom': return 'Custom model combination';
      default: return 'Unknown selection';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <RLIcon color="primary" />
            <Typography variant="h6">RL Classification Controls</Typography>
            <Chip
              icon={localConfig.enableRL ? <CheckCircleIcon /> : <WarningIcon />}
              label={localConfig.enableRL ? 'ENABLED' : 'DISABLED'}
              color={localConfig.enableRL ? 'success' : 'default'}
              size="small"
            />
          </Box>
        }
        action={
          <Tooltip title="RL Configuration Info">
            <IconButton size="small">
              <InfoIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* Main Toggle */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, bgcolor: localConfig.enableRL ? 'success.light' : 'grey.100' }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={localConfig.enableRL}
                    onChange={handleRLToggle}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      Enable RL-Enhanced Classification
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Use reinforcement learning to optimize classification pipeline
                    </Typography>
                  </Box>
                }
              />
            </Paper>
          </Grid>

          {/* Basic Configuration */}
          {localConfig.enableRL && (
            <>
              {/* Confidence Threshold */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Confidence Threshold
                </Typography>
                <Slider
                  value={localConfig.confidenceThreshold}
                  onChange={(e, value) => handleConfigChange('confidenceThreshold', value)}
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  marks={[
                    { value: 0.1, label: '10%' },
                    { value: 0.5, label: '50%' },
                    { value: 0.75, label: '75%' },
                    { value: 1.0, label: '100%' }
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Typography variant="caption" color="text.secondary">
                  Minimum confidence required for classification
                </Typography>
              </Grid>

              {/* Cost Budget */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Cost Budget (per document)
                </Typography>
                <Slider
                  value={localConfig.costBudget}
                  onChange={(e, value) => handleConfigChange('costBudget', value)}
                  min={0}
                  max={500}
                  step={10}
                  marks={[
                    { value: 0, label: '$0' },
                    { value: 100, label: '$100' },
                    { value: 250, label: '$250' },
                    { value: 500, label: '$500' }
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `$${value}`}
                />
                <Typography variant="caption" color="text.secondary">
                  Maximum cost per document classification
                </Typography>
              </Grid>

              {/* Processing Time Limit */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Max Processing Time
                </Typography>
                <Slider
                  value={localConfig.maxProcessingTime}
                  onChange={(e, value) => handleConfigChange('maxProcessingTime', value)}
                  min={1000}
                  max={10000}
                  step={500}
                  marks={[
                    { value: 1000, label: '1s' },
                    { value: 3000, label: '3s' },
                    { value: 5000, label: '5s' },
                    { value: 10000, label: '10s' }
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}ms`}
                />
                <Typography variant="caption" color="text.secondary">
                  Maximum processing time per document
                </Typography>
              </Grid>

              {/* Model Selection */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Model Selection Strategy
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {['auto', 'rule_based', 'ensemble', 'custom'].map((option) => (
                    <Chip
                      key={option}
                      label={option.replace('_', ' ').toUpperCase()}
                      onClick={() => handleConfigChange('modelSelection', option)}
                      color={localConfig.modelSelection === option ? 'primary' : 'default'}
                      variant={localConfig.modelSelection === option ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {getModelSelectionInfo(localConfig.modelSelection)}
                </Typography>
              </Grid>

              {/* Optimization Mode */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Optimization Mode
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {[
                    { value: 'accuracy', label: 'Accuracy', icon: '🎯' },
                    { value: 'speed', label: 'Speed', icon: '⚡' },
                    { value: 'cost', label: 'Cost', icon: '💰' },
                    { value: 'balanced', label: 'Balanced', icon: '⚖️' }
                  ].map((option) => (
                    <Chip
                      key={option.value}
                      label={`${option.icon} ${option.label}`}
                      onClick={() => handleConfigChange('optimizationMode', option.value)}
                      color={localConfig.optimizationMode === option.value ? getOptimizationModeColor(option.value) : 'default'}
                      variant={localConfig.optimizationMode === option.value ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>
              </Grid>

              <Divider sx={{ my: 2 }} />

              {/* Advanced Configuration Toggle */}
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  startIcon={<SettingsIcon />}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  fullWidth
                >
                  {showAdvanced ? 'Hide' : 'Show'} Advanced Configuration
                </Button>
              </Grid>

              {/* Advanced Configuration */}
              {showAdvanced && (
                <Grid item xs={12}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Advanced RL parameters for fine-tuning the reinforcement learning agent
                  </Alert>
                  
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Learning Rate"
                        secondary="Controls how quickly the RL agent learns"
                      />
                      <Chip label="0.001" size="small" />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Exploration Rate"
                        secondary="Controls exploration vs exploitation"
                      />
                      <Chip label="0.1" size="small" />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Memory Size"
                        secondary="Size of the experience replay buffer"
                      />
                      <Chip label="10000" size="small" />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Training Frequency"
                        secondary="How often to update the RL agent"
                      />
                      <Chip label="Every 100 steps" size="small" />
                    </ListItem>
                  </List>
                </Grid>
              )}

              {/* Training Controls */}
              <Grid item xs={12}>
                <Box display="flex" gap={2} justifyContent="center">
                  <Button
                    variant="contained"
                    startIcon={isTraining ? <PauseIcon /> : <PlayIcon />}
                    onClick={handleTrainingStart}
                    disabled={isTraining}
                    color="primary"
                  >
                    {isTraining ? 'Training...' : 'Start RL Training'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={() => window.location.reload()}
                  >
                    Reset
                  </Button>
                </Box>
              </Grid>
            </>
          )}

          {/* Status Information */}
          {!localConfig.enableRL && (
            <Grid item xs={12}>
              <Alert severity="warning">
                RL-enhanced classification is disabled. Enable it to use intelligent model selection and optimization.
              </Alert>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default RLClassificationControls;
