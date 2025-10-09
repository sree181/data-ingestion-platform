import React from 'react';
import { Box, Typography, Card, CardContent, Divider } from '@mui/material';
import {
  Description as UploadIcon,
  Psychology as AIIcon,
  Hub as GraphIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';

const nodeTypes = [
  {
    type: 'upload',
    label: 'Upload Documents',
    description: 'Upload PDF files for processing',
    icon: UploadIcon,
    color: '#3b82f6',
    category: 'Input',
  },
  {
    type: 'aiProcessing',
    label: 'AI Processing',
    description: 'Extract entities and relationships',
    icon: AIIcon,
    color: '#ec4899',
    category: 'Processing',
  },
  {
    type: 'knowledgeGraph',
    label: 'Knowledge Graph',
    description: 'Build interactive graph visualization',
    icon: GraphIcon,
    color: '#8b5cf6',
    category: 'Analysis',
  },
  {
    type: 'report',
    label: 'Generate Report',
    description: 'Create investigation report',
    icon: ReportIcon,
    color: '#10b981',
    category: 'Output',
  },
];

const NodePalette = () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const categories = ['Input', 'Processing', 'Analysis', 'Output'];

  return (
    <Box
      sx={{
        width: 280,
        height: '100%',
        bgcolor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
        overflowY: 'auto',
        p: 2,
      }}
    >
      <Typography variant="h6" fontWeight={700} gutterBottom>
        Workflow Nodes
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" mb={2}>
        Drag nodes to the canvas to build your workflow
      </Typography>

      {categories.map((category) => (
        <Box key={category} mb={3}>
          <Typography
            variant="overline"
            color="text.secondary"
            fontWeight={600}
            display="block"
            mb={1}
          >
            {category}
          </Typography>

          {nodeTypes
            .filter((node) => node.category === category)
            .map((node) => {
              const Icon = node.icon;
              return (
                <Card
                  key={node.type}
                  draggable
                  onDragStart={(e) => onDragStart(e, node.type)}
                  sx={{
                    mb: 1.5,
                    cursor: 'grab',
                    border: `1px solid ${node.color}40`,
                    transition: 'all 0.2s',
                    '&:hover': {
                      borderColor: node.color,
                      boxShadow: 2,
                      transform: 'translateX(4px)',
                    },
                    '&:active': {
                      cursor: 'grabbing',
                    },
                  }}
                >
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                      <Icon sx={{ fontSize: 20, color: node.color }} />
                      <Typography variant="subtitle2" fontWeight={600} fontSize="0.85rem">
                        {node.label}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" fontSize="0.7rem">
                      {node.description}
                    </Typography>
                  </CardContent>
                </Card>
              );
            })}
        </Box>
      ))}

      <Divider sx={{ my: 2 }} />

      <Box
        sx={{
          p: 2,
          bgcolor: 'primary.50',
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'primary.200',
        }}
      >
        <Typography variant="caption" fontWeight={600} display="block" mb={0.5}>
          💡 Quick Tip
        </Typography>
        <Typography variant="caption" color="text.secondary" fontSize="0.7rem">
          Connect nodes by dragging from the right handle to the left handle of another node
        </Typography>
      </Box>
    </Box>
  );
};

export default NodePalette;
