import React from 'react';
import { Box, Typography, Paper, Divider, Tooltip } from '@mui/material';
import {
  CloudDownload as SourceIcon,
  AutoAwesome as PreprocessIcon,
  Label as NERIcon,
  Storage as IngestionIcon,
  Category as ClassificationIcon,
  Visibility as MonitoringIcon,
} from '@mui/icons-material';

const PVNodePalette = () => {
  const onDragStart = (event, nodeType, label) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const sourceNodes = [
    { type: 'ncbi', label: 'NCBI', icon: <SourceIcon />, color: '#06B6D4', description: 'Fetch documents from NCBI database' },
    { type: 'pubmed', label: 'PubMed', icon: <SourceIcon />, color: '#06B6D4', description: 'Fetch documents from PubMed' },
    { type: 'chembl', label: 'ChEMBL', icon: <SourceIcon />, color: '#06B6D4', description: 'Fetch chemical data from ChEMBL' },
    { type: 'fda', label: 'FDA', icon: <SourceIcon />, color: '#06B6D4', description: 'Fetch FDA adverse event reports' },
  ];

  const processingNodes = [
    { type: 'preprocessing', label: 'Preprocessing', icon: <PreprocessIcon />, color: '#8B5CF6', description: 'OCR, HTML cleaning, normalization' },
    { type: 'ner', label: 'NER & Relations', icon: <NERIcon />, color: '#EC4899', description: 'Extract entities and relationships' },
  ];

  const storageNodes = [
    { type: 'ingestion', label: 'Ingestion', icon: <IngestionIcon />, color: '#F59E0B', description: 'Store in Elasticsearch & Neo4j' },
  ];

  const analysisNodes = [
    { type: 'classification', label: 'Classification', icon: <ClassificationIcon />, color: '#10B981', description: 'Classify documents with ML models' },
    { type: 'monitoring', label: 'Monitoring', icon: <MonitoringIcon />, color: '#6366F1', description: 'Monitor model performance' },
  ];

  const NodeCard = ({ node }) => (
    <Tooltip title={node.description} placement="right" arrow>
      <Paper
        elevation={2}
        draggable
        onDragStart={(e) => onDragStart(e, node.type, node.label)}
        sx={{
          p: 1.5,
          mb: 1,
          cursor: 'grab',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          borderLeft: '4px solid',
          borderLeftColor: node.color,
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateX(4px)',
            boxShadow: 4,
            bgcolor: `${node.color}08`,
          },
          '&:active': {
            cursor: 'grabbing',
            transform: 'scale(0.98)',
          },
        }}
      >
        <Box sx={{ color: node.color, display: 'flex' }}>
          {node.icon}
        </Box>
        <Box flex={1}>
          <Typography variant="body2" fontWeight={600}>
            {node.label}
          </Typography>
        </Box>
      </Paper>
    </Tooltip>
  );

  return (
    <Box
      sx={{
        width: 280,
        height: '100%',
        bgcolor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
        overflow: 'auto',
        p: 2,
      }}
    >
      <Typography variant="h6" fontWeight={700} mb={2}>
        Node Palette
      </Typography>
      <Typography variant="caption" color="text.secondary" mb={2} display="block">
        Drag nodes to the canvas to build your workflow
      </Typography>

      {/* Source Nodes */}
      <Typography variant="subtitle2" fontWeight={600} color="primary" mb={1} mt={2}>
        SOURCE NODES
      </Typography>
      <Divider sx={{ mb: 1 }} />
      {sourceNodes.map((node) => (
        <NodeCard key={node.type} node={node} />
      ))}

      {/* Processing Nodes */}
      <Typography variant="subtitle2" fontWeight={600} color="primary" mb={1} mt={3}>
        PROCESSING
      </Typography>
      <Divider sx={{ mb: 1 }} />
      {processingNodes.map((node) => (
        <NodeCard key={node.type} node={node} />
      ))}

      {/* Storage Nodes */}
      <Typography variant="subtitle2" fontWeight={600} color="primary" mb={1} mt={3}>
        STORAGE
      </Typography>
      <Divider sx={{ mb: 1 }} />
      {storageNodes.map((node) => (
        <NodeCard key={node.type} node={node} />
      ))}

      {/* Analysis Nodes */}
      <Typography variant="subtitle2" fontWeight={600} color="primary" mb={1} mt={3}>
        ANALYSIS
      </Typography>
      <Divider sx={{ mb: 1 }} />
      {analysisNodes.map((node) => (
        <NodeCard key={node.type} node={node} />
      ))}

      {/* Instructions */}
      <Box
        sx={{
          mt: 4,
          p: 2,
          bgcolor: 'info.lighter',
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'info.light',
        }}
      >
        <Typography variant="caption" color="info.dark" fontWeight={600} display="block" mb={0.5}>
          💡 Quick Tips
        </Typography>
        <Typography variant="caption" color="info.dark" display="block" mb={0.5}>
          • Drag nodes to canvas
        </Typography>
        <Typography variant="caption" color="info.dark" display="block" mb={0.5}>
          • Connect nodes by dragging from handles
        </Typography>
        <Typography variant="caption" color="info.dark" display="block">
          • Click Run to simulate execution
        </Typography>
      </Box>
    </Box>
  );
};

export default PVNodePalette;

