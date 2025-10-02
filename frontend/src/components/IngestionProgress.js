import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import ingestionService from '../services/ingestionService';

const IngestionProgress = ({ projectId, onStatusChange }) => {
  const [ingestionStatus, setIngestionStatus] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [recentFiles, setRecentFiles] = useState([]);

  useEffect(() => {
    if (!projectId) return;

    // Subscribe to ingestion updates
    const unsubscribe = ingestionService.subscribeToProject(projectId, (data) => {
      console.log('📊 Ingestion update received:', data);
      
      switch (data.type) {
        case 'ingestion_status_update':
          setIngestionStatus(data.status);
          onStatusChange?.(data.status);
          
          // Update recent files list
          if (data.status.last_processed) {
            setRecentFiles(prev => [
              {
                filename: data.status.last_processed,
                status: data.status.failed_files > 0 ? 'failed' : 'success',
                timestamp: new Date().toISOString()
              },
              ...prev.slice(0, 9) // Keep only last 10 files
            ]);
          }
          break;

        case 'ingestion_cleared':
          setIngestionStatus(null);
          onStatusChange?.(null);
          break;

        case 'document_count_update':
          // Handle document count updates if needed
          break;
      }
    });

    // Get initial status
    const initialStatus = ingestionService.getIngestionStatus(projectId);
    if (initialStatus) {
      setIngestionStatus(initialStatus);
      onStatusChange?.(initialStatus);
    }

    return unsubscribe;
  }, [projectId, onStatusChange]);

  if (!ingestionStatus) {
    return null;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <UploadIcon />;
      case 'completed': return <CheckIcon />;
      case 'failed': return <ErrorIcon />;
      default: return <UploadIcon />;
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getProgressValue = () => {
    if (ingestionStatus.progress_percentage !== undefined) {
      return ingestionStatus.progress_percentage;
    }
    if (ingestionStatus.total_files && ingestionStatus.processed_files) {
      return Math.round((ingestionStatus.processed_files / ingestionStatus.total_files) * 100);
    }
    return 0;
  };

  return (
    <Card 
      sx={{ 
        mb: 2, 
        border: '2px solid',
        borderColor: getStatusColor(ingestionStatus.status) + '.main',
        borderRadius: 2,
        backgroundColor: getStatusColor(ingestionStatus.status) + '.light',
        opacity: 0.95
      }}
    >
      <CardContent sx={{ p: 2 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getStatusIcon(ingestionStatus.status)}
            <Typography variant="h6" fontWeight={600}>
              Document Ingestion {ingestionStatus.status === 'completed' ? 'Completed' : 'In Progress'}
            </Typography>
            <Chip 
              label={ingestionStatus.status.toUpperCase()} 
              color={getStatusColor(ingestionStatus.status)}
              size="small"
            />
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="text.secondary">
              {ingestionStatus.processed_files || 0}/{ingestionStatus.total_files || 0} files
            </Typography>
            
            <Tooltip title={isExpanded ? 'Collapse' : 'Expand'}>
              <IconButton 
                size="small" 
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Tooltip>
            
            {ingestionStatus.status === 'completed' || ingestionStatus.status === 'failed' ? (
              <Tooltip title="Close">
                <IconButton 
                  size="small" 
                  onClick={() => {
                    setIngestionStatus(null);
                    onStatusChange?.(null);
                  }}
                >
                  <CloseIcon />
                </IconButton>
              </Tooltip>
            ) : null}
          </Box>
        </Box>

        {/* Progress Bar */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" fontWeight={500}>
              Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {getProgressValue()}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={getProgressValue()}
            sx={{ 
              height: 8, 
              borderRadius: 4,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                backgroundColor: getStatusColor(ingestionStatus.status) + '.main'
              }
            }}
          />
        </Box>

        {/* Stats */}
        <Box display="flex" justifyContent="space-between" mb={2}>
          <Box textAlign="center">
            <Typography variant="h6" color="success.main" fontWeight={600}>
              {ingestionStatus.successful_files || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Successful
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" color="error.main" fontWeight={600}>
              {ingestionStatus.failed_files || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Failed
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" color="primary.main" fontWeight={600}>
              {ingestionStatus.processed_files || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Processed
            </Typography>
          </Box>
        </Box>

        {/* Current File */}
        {ingestionStatus.current_file && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Currently processing:
            </Typography>
            <Typography variant="body2" fontWeight={500} noWrap>
              {ingestionStatus.current_file}
            </Typography>
          </Box>
        )}

        {/* Error Message */}
        {ingestionStatus.status === 'failed' && ingestionStatus.error && (
          <Box mb={2} p={2} sx={{ backgroundColor: 'error.light', borderRadius: 1 }}>
            <Typography variant="body2" color="error.dark">
              <strong>Error:</strong> {ingestionStatus.error}
            </Typography>
          </Box>
        )}

        {/* Expanded Details */}
        <Collapse in={isExpanded}>
          <Divider sx={{ my: 2 }} />
          
          {/* Timing Information */}
          <Box mb={2}>
            <Typography variant="body2" fontWeight={500} gutterBottom>
              Timing Information
            </Typography>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">
                Started: {formatTime(ingestionStatus.start_time)}
              </Typography>
              {ingestionStatus.end_time && (
                <Typography variant="caption" color="text.secondary">
                  Completed: {formatTime(ingestionStatus.end_time)}
                </Typography>
              )}
            </Box>
          </Box>

          {/* Recent Files */}
          {recentFiles.length > 0 && (
            <Box>
              <Typography variant="body2" fontWeight={500} gutterBottom>
                Recent Files
              </Typography>
              <List dense>
                {recentFiles.slice(0, 5).map((file, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      {file.status === 'success' ? (
                        <CheckIcon color="success" fontSize="small" />
                      ) : (
                        <ErrorIcon color="error" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={file.filename}
                      secondary={formatTime(file.timestamp)}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default IngestionProgress;

