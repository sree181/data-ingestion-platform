import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  Card,
  CardContent,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Cloud as CloudIcon,
  Computer as LocalIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

const ModelSelector = ({ 
  open, 
  onClose, 
  selectedModel, 
  onModelSelect, 
  spaceId 
}) => {
  const [availableModels, setAvailableModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modelStatus, setModelStatus] = useState({});
  const [testingModel, setTestingModel] = useState(null);

  // Fetch available models
  const fetchAvailableModels = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/models/available');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
      } else {
        throw new Error('Failed to fetch models');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching models:', err);
    } finally {
      setLoading(false);
    }
  };

  // Test model availability
  const testModel = async (modelName) => {
    setTestingModel(modelName);
    setModelStatus(prev => ({ ...prev, [modelName]: 'testing' }));
    
    try {
      const response = await fetch(`/api/v1/models/test/${encodeURIComponent(modelName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ space_id: spaceId })
      });
      
      if (response.ok) {
        setModelStatus(prev => ({ ...prev, [modelName]: 'available' }));
      } else {
        setModelStatus(prev => ({ ...prev, [modelName]: 'unavailable' }));
      }
    } catch (err) {
      setModelStatus(prev => ({ ...prev, [modelName]: 'unavailable' }));
    } finally {
      setTestingModel(null);
    }
  };

  // Test all models
  const testAllModels = async () => {
    for (const model of availableModels) {
      await testModel(model.name);
    }
  };

  useEffect(() => {
    if (open) {
      fetchAvailableModels();
    }
  }, [open]);

  const handleModelSelect = (modelName) => {
    onModelSelect(modelName);
    onClose();
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'openai':
        return <CloudIcon color="primary" />;
      case 'ollama':
        return <LocalIcon color="success" />;
      default:
        return <AIIcon />;
    }
  };

  const getStatusIcon = (modelName) => {
    const status = modelStatus[modelName];
    if (status === 'testing') {
      return <CircularProgress size={16} />;
    } else if (status === 'available') {
      return <CheckIcon color="success" size="small" />;
    } else if (status === 'unavailable') {
      return <ErrorIcon color="error" size="small" />;
    }
    return null;
  };

  const getStatusColor = (modelName) => {
    const status = modelStatus[modelName];
    switch (status) {
      case 'available': return 'success';
      case 'unavailable': return 'error';
      case 'testing': return 'info';
      default: return 'default';
    }
  };

  const groupModelsByProvider = () => {
    const grouped = {};
    availableModels.forEach(model => {
      if (!grouped[model.provider]) {
        grouped[model.provider] = [];
      }
      grouped[model.provider].push(model);
    });
    return grouped;
  };

  const groupedModels = groupModelsByProvider();

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" component="div">
            Select AI Model
          </Typography>
          <Box>
            <Tooltip title="Test All Models">
              <IconButton onClick={testAllModels} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Choose an AI model for document processing. Local models (Ollama) run on your infrastructure, 
              while cloud models (OpenAI) use external APIs.
            </Typography>

            {Object.entries(groupedModels).map(([provider, models]) => (
              <Box key={provider} sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getProviderIcon(provider)}
                  {provider === 'openai' ? 'OpenAI Models' : 
                   provider === 'ollama' ? 'Ollama Models (Local)' : 
                   `${provider.charAt(0).toUpperCase() + provider.slice(1)} Models`}
                </Typography>

                <Grid container spacing={2}>
                  {models.map((model) => (
                    <Grid item xs={12} sm={6} md={4} key={model.name}>
                      <Card 
                        sx={{ 
                          cursor: 'pointer',
                          border: selectedModel === model.name ? 2 : 1,
                          borderColor: selectedModel === model.name ? 'primary.main' : 'divider',
                          '&:hover': {
                            boxShadow: 2
                          }
                        }}
                        onClick={() => handleModelSelect(model.name)}
                      >
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                            <Typography variant="h6" component="div" noWrap>
                              {model.name}
                            </Typography>
                            <Box display="flex" alignItems="center" gap={1}>
                              {getStatusIcon(model.name)}
                              <Chip 
                                label={model.is_local ? 'Local' : 'Cloud'} 
                                size="small" 
                                color={model.is_local ? 'success' : 'primary'}
                                variant="outlined"
                              />
                            </Box>
                          </Box>

                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {model.description}
                          </Typography>

                          <Box display="flex" flexWrap="wrap" gap={0.5} mb={1}>
                            {model.capabilities?.map((capability) => (
                              <Chip 
                                key={capability} 
                                label={capability.replace('_', ' ')} 
                                size="small" 
                                variant="outlined"
                              />
                            ))}
                          </Box>

                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="caption" color="text.secondary">
                              Max Tokens: {model.max_tokens?.toLocaleString()}
                            </Typography>
                            {model.cost_per_1k_tokens !== undefined && (
                              <Typography variant="caption" color="text.secondary">
                                ${model.cost_per_1k_tokens}/1k tokens
                              </Typography>
                            )}
                          </Box>

                          {model.requires_api_key && (
                            <Alert severity="warning" sx={{ mt: 1, fontSize: '0.75rem' }}>
                              Requires API key
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>

                <Divider sx={{ mt: 2 }} />
              </Box>
            ))}

            {availableModels.length === 0 && !loading && (
              <Box textAlign="center" p={4}>
                <Typography variant="body1" color="text.secondary">
                  No models available. Please check your configuration.
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button 
          onClick={fetchAvailableModels} 
          disabled={loading}
          startIcon={<RefreshIcon />}
        >
          Refresh
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ModelSelector;
