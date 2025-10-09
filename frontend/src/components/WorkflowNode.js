import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Card, CardContent, Box, Typography, Chip } from '@mui/material';
import {
  Description as UploadIcon,
  Psychology as AIIcon,
  Hub as GraphIcon,
  Assessment as ReportIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

const iconMap = {
  upload: UploadIcon,
  aiProcessing: AIIcon,
  knowledgeGraph: GraphIcon,
  report: ReportIcon,
};

const colorMap = {
  upload: '#3b82f6',
  aiProcessing: '#ec4899',
  knowledgeGraph: '#8b5cf6',
  report: '#10b981',
};

const WorkflowNode = ({ data, isConnectable }) => {
  const Icon = iconMap[data.type] || UploadIcon;
  const baseColor = colorMap[data.type] || '#64748b';

  // Get color based on status
  const getStatusColor = () => {
    switch (data.status) {
      case 'completed':
        return '#10b981'; // Green
      case 'running':
        return '#3b82f6'; // Blue
      case 'failed':
        return '#ef4444'; // Red
      default:
        return baseColor; // Original color for pending
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'completed':
        return <CompletedIcon sx={{ fontSize: 16, color: '#10b981' }} />;
      case 'running':
        return <PendingIcon sx={{ fontSize: 16, color: '#3b82f6' }} />;
      case 'failed':
        return <ErrorIcon sx={{ fontSize: 16, color: '#ef4444' }} />;
      default:
        return null;
    }
  };

  const color = getStatusColor();
  const isRunning = data.status === 'running';

  return (
    <Card
      sx={{
        minWidth: 220,
        border: `2px solid ${color}`,
        borderRadius: 2,
        boxShadow: data.selected ? `0 0 0 2px ${color}40` : 2,
        transition: 'all 0.2s',
        backgroundColor: data.status === 'completed' ? '#f0fdf4' : 
                         data.status === 'running' ? '#eff6ff' : 
                         data.status === 'failed' ? '#fef2f2' : 
                         'white',
        animation: isRunning ? 'pulse 1.5s ease-in-out infinite' : 'none',
        '@keyframes pulse': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.7 },
        },
        '&:hover': {
          boxShadow: 4,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        style={{
          background: color,
          width: 12,
          height: 12,
          border: '2px solid white',
        }}
      />

      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Icon sx={{ fontSize: 24, color }} />
          <Typography variant="subtitle2" fontWeight={600} flex={1}>
            {data.label}
          </Typography>
          {getStatusIcon()}
        </Box>

        {data.description && (
          <Typography variant="caption" color="text.secondary" display="block" mb={1}>
            {data.description}
          </Typography>
        )}

        {data.config && (
          <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
            {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
              <Chip
                key={key}
                label={`${key}: ${value}`}
                size="small"
                sx={{ fontSize: '0.65rem', height: 20 }}
              />
            ))}
          </Box>
        )}

        {data.status && (
          <Chip
            label={data.status}
            size="small"
            color={
              data.status === 'completed'
                ? 'success'
                : data.status === 'running'
                ? 'warning'
                : data.status === 'failed'
                ? 'error'
                : 'default'
            }
            sx={{ mt: 1, fontSize: '0.7rem', height: 22 }}
          />
        )}
      </CardContent>

      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        style={{
          background: color,
          width: 12,
          height: 12,
          border: '2px solid white',
        }}
      />
    </Card>
  );
};

export default memo(WorkflowNode);
