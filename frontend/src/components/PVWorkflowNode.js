import React from 'react';
import { Handle, Position } from 'reactflow';
import { Box, Typography, LinearProgress, Chip, IconButton, Tooltip } from '@mui/material';
import {
  CloudDownload as SourceIcon,
  AutoAwesome as PreprocessIcon,
  Label as NERIcon,
  Storage as IngestionIcon,
  Category as ClassificationIcon,
  Visibility as MonitoringIcon,
  Settings as SettingsIcon,
  CheckCircle as CompleteIcon,
  Error as ErrorIcon,
  PlayArrow as RunningIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';

const PVWorkflowNode = ({ data, isConnectable }) => {
  const { 
    label, 
    type, 
    status = 'pending',
    progress = 0,
    metrics = {},
    subProcesses = {},
    config = {}
  } = data;

  // Status colors
  const statusColors = {
    pending: '#6B7280',
    running: '#3B82F6',
    complete: '#10B981',
    error: '#EF4444',
  };

  // Node type colors
  const typeColors = {
    ncbi: '#06B6D4',
    pubmed: '#06B6D4',
    chembl: '#06B6D4',
    cochrane: '#06B6D4',
    fda: '#06B6D4',
    preprocessing: '#8B5CF6',
    ner: '#EC4899',
    ingestion: '#F59E0B',
    s3: '#FF9900',
    box: '#0061D5',
    minio: '#C72E49',
    gdrive: '#4285F4',
    classification: '#10B981',
    monitoring: '#6366F1',
  };

  // Get icon based on type
  const getIcon = () => {
    const iconMap = {
      ncbi: <SourceIcon />,
      pubmed: <SourceIcon />,
      chembl: <SourceIcon />,
      cochrane: <SourceIcon />,
      fda: <SourceIcon />,
      preprocessing: <PreprocessIcon />,
      ner: <NERIcon />,
      ingestion: <IngestionIcon />,
      s3: <IngestionIcon />,
      box: <IngestionIcon />,
      minio: <IngestionIcon />,
      gdrive: <IngestionIcon />,
      classification: <ClassificationIcon />,
      monitoring: <MonitoringIcon />,
    };
    return iconMap[type] || <SourceIcon />;
  };

  // Get status icon
  const getStatusIcon = () => {
    const iconMap = {
      pending: <PendingIcon fontSize="small" />,
      running: <RunningIcon fontSize="small" />,
      complete: <CompleteIcon fontSize="small" />,
      error: <ErrorIcon fontSize="small" />,
    };
    return iconMap[status] || <PendingIcon fontSize="small" />;
  };

  // Format duration
  const formatDuration = (ms) => {
    if (!ms) return '00:00:00';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  };

  return (
    <Box
      sx={{
        width: 320,
        borderRadius: 2,
        border: '2px solid',
        borderColor: status === 'running' ? typeColors[type] : statusColors[status],
        bgcolor: 'background.paper',
        boxShadow: status === 'running' ? `0 0 20px ${typeColors[type]}40` : 2,
        transition: 'all 0.3s ease',
        animation: status === 'running' ? 'pulse 2s infinite' : 'none',
        '@keyframes pulse': {
          '0%, 100%': { borderColor: typeColors[type] },
          '50%': { borderColor: `${typeColors[type]}80` },
        },
      }}
    >
      {/* Input Handle */}
      {type !== 'ncbi' && type !== 'pubmed' && type !== 'chembl' && type !== 'cochrane' && type !== 'fda' && (
        <Handle
          type="target"
          position={Position.Left}
          isConnectable={isConnectable}
          style={{
            background: typeColors[type],
            width: 12,
            height: 12,
            border: '2px solid white',
          }}
        />
      )}

      {/* Header */}
      <Box
        sx={{
          p: 1.5,
          bgcolor: `${typeColors[type]}15`,
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Box sx={{ color: typeColors[type], display: 'flex' }}>
          {getIcon()}
        </Box>
        <Typography variant="subtitle2" fontWeight={600} flex={1}>
          {label}
        </Typography>
        <Tooltip title="Configure">
          <IconButton size="small" sx={{ color: 'text.secondary' }}>
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Status Row */}
      <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ color: statusColors[status], display: 'flex' }}>
          {getStatusIcon()}
        </Box>
        <Typography variant="caption" fontWeight={600} textTransform="capitalize">
          {status}
        </Typography>
        {metrics.duration && (
          <Typography variant="caption" color="text.secondary" ml="auto">
            {formatDuration(metrics.duration)}
          </Typography>
        )}
      </Box>

      {/* Progress Bar */}
      {(status === 'running' || progress > 0) && (
        <Box sx={{ px: 1.5, pb: 1 }}>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              height: 6,
              borderRadius: 1,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                bgcolor: typeColors[type],
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" mt={0.5}>
            {progress}% complete
          </Typography>
        </Box>
      )}

      {/* Metrics Section */}
      <Box sx={{ px: 1.5, pb: 1.5 }}>
        {/* Source Node Metrics */}
        {(type === 'ncbi' || type === 'pubmed' || type === 'chembl' || type === 'cochrane' || type === 'fda') && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Documents: {metrics.documentsFetched || 0} / {config.maxDocuments || 0}
            </Typography>
          </Box>
        )}

        {/* Storage Node Metrics */}
        {(type === 's3' || type === 'box' || type === 'minio' || type === 'gdrive') && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Files Stored: {metrics.filesStored || 0}
            </Typography>
            {metrics.storageUsed && (
              <Typography variant="caption" color="text.secondary" display="block">
                Storage: {metrics.storageUsed}
              </Typography>
            )}
          </Box>
        )}

        {/* Preprocessing Sub-processes */}
        {type === 'preprocessing' && subProcesses && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {Object.entries(subProcesses).map(([key, value]) => (
              <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={key.toUpperCase()}
                  size="small"
                  color={value.status === 'complete' ? 'success' : value.status === 'running' ? 'primary' : 'default'}
                  sx={{ minWidth: 80, fontSize: '0.65rem' }}
                />
                <LinearProgress
                  variant="determinate"
                  value={value.progress || 0}
                  sx={{ flex: 1, height: 4, borderRadius: 1 }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
                  {value.progress || 0}%
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {/* NER Metrics */}
        {type === 'ner' && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Entities: {metrics.entitiesExtracted || 0} | Relations: {metrics.relationshipsExtracted || 0}
            </Typography>
            {metrics.entityBreakdown && (
              <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                {Object.entries(metrics.entityBreakdown).slice(0, 3).map(([key, value]) => (
                  <Chip key={key} label={`${key}: ${value}`} size="small" variant="outlined" />
                ))}
              </Box>
            )}
          </Box>
        )}

        {/* Ingestion Dual Metrics */}
        {type === 'ingestion' && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Chip label="Elasticsearch" size="small" color="primary" sx={{ minWidth: 100 }} />
                <Typography variant="caption" color="text.secondary">
                  {metrics.elasticsearch?.documentsIngested || 0} docs
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={metrics.elasticsearch?.progress || 0}
                sx={{ height: 4, borderRadius: 1 }}
              />
            </Box>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Chip label="Neo4j" size="small" color="secondary" sx={{ minWidth: 100 }} />
                <Typography variant="caption" color="text.secondary">
                  {metrics.neo4j?.nodesCreated || 0} nodes
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={metrics.neo4j?.progress || 0}
                sx={{ height: 4, borderRadius: 1 }}
                color="secondary"
              />
            </Box>
          </Box>
        )}

        {/* Classification Metrics */}
        {type === 'classification' && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              Classified: {metrics.documentsClassified || 0} / {metrics.totalDocuments || 0}
            </Typography>
            {metrics.averageConfidence && (
              <Typography variant="caption" color="text.secondary" display="block">
                Avg Confidence: {(metrics.averageConfidence * 100).toFixed(1)}%
              </Typography>
            )}
          </Box>
        )}

        {/* Monitoring Metrics */}
        {type === 'monitoring' && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {metrics.accuracy !== undefined && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">Accuracy:</Typography>
                <Typography variant="caption" fontWeight={600}>{(metrics.accuracy * 100).toFixed(1)}%</Typography>
              </Box>
            )}
            {metrics.throughput !== undefined && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">Throughput:</Typography>
                <Typography variant="caption" fontWeight={600}>{metrics.throughput.toFixed(1)} docs/s</Typography>
              </Box>
            )}
          </Box>
        )}
      </Box>

      {/* Output Handle */}
      {type !== 'monitoring' && type !== 's3' && type !== 'box' && type !== 'minio' && type !== 'gdrive' && (
        <Handle
          type="source"
          position={Position.Right}
          isConnectable={isConnectable}
          style={{
            background: typeColors[type],
            width: 12,
            height: 12,
            border: '2px solid white',
          }}
        />
      )}
    </Box>
  );
};

export default PVWorkflowNode;

