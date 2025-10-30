import React from 'react';
import {
  Chip,
  Tooltip,
  Box,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper
} from '@mui/material';
import {
  Psychology as RLIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  TrendingUp as AccuracyIcon,
  Clear as ClearIcon
} from '@mui/icons-material';

const RLClassificationBadge = ({ 
  classification, 
  confidence, 
  rlOptimized = false,
  modelsUsed = [],
  processingTime = 0,
  costEstimate = 0,
  onDetailsClick
}) => {
  const [detailsOpen, setDetailsOpen] = React.useState(false);

  const getClassificationColor = (classification) => {
    switch (classification?.toLowerCase()) {
      case 'icsr': return 'error';
      case 'safety_information': return 'warning';
      case 'non_icsr': return 'info';
      case 'rejected': return 'default';
      default: return 'default';
    }
  };

  const getClassificationIcon = (classification) => {
    switch (classification?.toLowerCase()) {
      case 'icsr': return <ErrorIcon />;
      case 'safety_information': return <WarningIcon />;
      case 'non_icsr': return <CheckCircleIcon />;
      case 'rejected': return <ClearIcon />;
      default: return <InfoIcon />;
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const formatConfidence = (confidence) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  const formatProcessingTime = (time) => {
    if (time < 1000) return `${time}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  const formatCost = (cost) => {
    return `$${cost.toFixed(3)}`;
  };

  const handleDetailsClick = () => {
    setDetailsOpen(true);
    onDetailsClick && onDetailsClick();
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
  };

  return (
    <>
      <Box display="flex" alignItems="center" gap={1}>
        <Chip
          icon={getClassificationIcon(classification)}
          label={classification || 'Unknown'}
          color={getClassificationColor(classification)}
          size="small"
          variant={rlOptimized ? 'filled' : 'outlined'}
        />
        
        <Chip
          label={formatConfidence(confidence)}
          color={getConfidenceColor(confidence)}
          size="small"
          variant="outlined"
        />

        {rlOptimized && (
          <Tooltip title="RL-Enhanced Classification">
            <Chip
              icon={<RLIcon />}
              label="RL"
              color="primary"
              size="small"
              variant="filled"
            />
          </Tooltip>
        )}

        <Tooltip title="View Classification Details">
          <IconButton size="small" onClick={handleDetailsClick}>
            <InfoIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Classification Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={handleCloseDetails}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <RLIcon color="primary" />
            <Typography variant="h6">Classification Details</Typography>
            {rlOptimized && (
              <Chip
                icon={<RLIcon />}
                label="RL-Enhanced"
                color="primary"
                size="small"
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Classification Result
            </Typography>
            <Box display="flex" alignItems="center" gap={2}>
              <Chip
                icon={getClassificationIcon(classification)}
                label={classification || 'Unknown'}
                color={getClassificationColor(classification)}
                size="medium"
              />
              <Chip
                label={formatConfidence(confidence)}
                color={getConfidenceColor(confidence)}
                size="medium"
                variant="outlined"
              />
            </Box>
          </Paper>

          <List dense>
            <ListItem>
              <ListItemIcon>
                <SpeedIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Processing Time"
                secondary={formatProcessingTime(processingTime)}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                <AccuracyIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary="Cost Estimate"
                secondary={formatCost(costEstimate)}
              />
            </ListItem>

            {modelsUsed.length > 0 && (
              <>
                <Divider sx={{ my: 1 }} />
                <ListItem>
                  <ListItemText
                    primary="Models Used"
                    secondary={modelsUsed.join(', ')}
                  />
                </ListItem>
              </>
            )}

            {rlOptimized && (
              <>
                <Divider sx={{ my: 1 }} />
                <ListItem>
                  <ListItemIcon>
                    <RLIcon fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="RL Optimization"
                    secondary="Reinforcement learning enhanced classification"
                  />
                </ListItem>
              </>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RLClassificationBadge;
