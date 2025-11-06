import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  Box, Button, Typography, Chip, Snackbar, Alert, Paper,
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  Stop as StopIcon,
  Refresh as ResetIcon,
} from '@mui/icons-material';
import PVWorkflowNode from '../components/PVWorkflowNode';
import PVNodePalette from '../components/PVNodePalette';
import { WorkflowSimulator } from '../utils/workflowSimulation';

const nodeTypes = {
  ncbi: PVWorkflowNode,
  pubmed: PVWorkflowNode,
  chembl: PVWorkflowNode,
  cochrane: PVWorkflowNode,
  fda: PVWorkflowNode,
  preprocessing: PVWorkflowNode,
  ner: PVWorkflowNode,
  ingestion: PVWorkflowNode,
  s3: PVWorkflowNode,
  box: PVWorkflowNode,
  minio: PVWorkflowNode,
  gdrive: PVWorkflowNode,
  classification: PVWorkflowNode,
  monitoring: PVWorkflowNode,
};

const nodeLabels = {
  ncbi: 'NCBI Source',
  pubmed: 'PubMed Source',
  chembl: 'ChEMBL Source',
  cochrane: 'Cochrane Source',
  fda: 'FDA Source',
  preprocessing: 'Preprocessing',
  ner: 'NER & Relations',
  ingestion: 'Ingestion',
  s3: 'AWS S3',
  box: 'Box',
  minio: 'MinIO',
  gdrive: 'Google Drive',
  classification: 'Classification',
  monitoring: 'Monitoring',
};

let nodeId = 0;
const getId = () => `node_${nodeId++}`;

// Demo workflow - Multi-source to Multi-destination
const initialNodes = [
  // LEFT SIDE: Data Sources
  {
    id: 'source-1',
    type: 'ncbi',
    position: { x: 50, y: 100 },
    data: {
      label: 'NCBI Source',
      type: 'ncbi',
      status: 'pending',
      progress: 0,
      config: { maxDocuments: 100 },
      metrics: {},
    },
  },
  {
    id: 'source-2',
    type: 'pubmed',
    position: { x: 50, y: 220 },
    data: {
      label: 'PubMed Source',
      type: 'pubmed',
      status: 'pending',
      progress: 0,
      config: { maxDocuments: 100 },
      metrics: {},
    },
  },
  {
    id: 'source-3',
    type: 'chembl',
    position: { x: 50, y: 340 },
    data: {
      label: 'ChEMBL Source',
      type: 'chembl',
      status: 'pending',
      progress: 0,
      config: { maxDocuments: 100 },
      metrics: {},
    },
  },
  {
    id: 'source-4',
    type: 'cochrane',
    position: { x: 50, y: 460 },
    data: {
      label: 'Cochrane Source',
      type: 'cochrane',
      status: 'pending',
      progress: 0,
      config: { maxDocuments: 100 },
      metrics: {},
    },
  },
  // CENTER: Processing Pipeline
  {
    id: 'process-1',
    type: 'preprocessing',
    position: { x: 450, y: 250 },
    data: {
      label: 'Preprocessing',
      type: 'preprocessing',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
      subProcesses: {
        ocr: { status: 'pending', progress: 0 },
        htmlCleaning: { status: 'pending', progress: 0 },
        normalization: { status: 'pending', progress: 0 },
      },
    },
  },
  {
    id: 'process-2',
    type: 'ner',
    position: { x: 850, y: 250 },
    data: {
      label: 'NER & Relations',
      type: 'ner',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
    },
  },
  // RIGHT SIDE: Storage Destinations
  {
    id: 'storage-1',
    type: 's3',
    position: { x: 1250, y: 100 },
    data: {
      label: 'AWS S3',
      type: 's3',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
    },
  },
  {
    id: 'storage-2',
    type: 'box',
    position: { x: 1250, y: 220 },
    data: {
      label: 'Box',
      type: 'box',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
    },
  },
  {
    id: 'storage-3',
    type: 'minio',
    position: { x: 1250, y: 340 },
    data: {
      label: 'MinIO',
      type: 'minio',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
    },
  },
  {
    id: 'storage-4',
    type: 'gdrive',
    position: { x: 1250, y: 460 },
    data: {
      label: 'Google Drive',
      type: 'gdrive',
      status: 'pending',
      progress: 0,
      config: {},
      metrics: {},
    },
  },
];

const initialEdges = [
  // Sources to Preprocessing
  {
    id: 'e-s1-p1',
    source: 'source-1',
    target: 'process-1',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#06B6D4' },
  },
  {
    id: 'e-s2-p1',
    source: 'source-2',
    target: 'process-1',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#06B6D4' },
  },
  {
    id: 'e-s3-p1',
    source: 'source-3',
    target: 'process-1',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#06B6D4' },
  },
  {
    id: 'e-s4-p1',
    source: 'source-4',
    target: 'process-1',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#06B6D4' },
  },
  // Preprocessing to NER
  {
    id: 'e-p1-p2',
    source: 'process-1',
    target: 'process-2',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#8B5CF6' },
  },
  // NER to Storage Destinations
  {
    id: 'e-p2-st1',
    source: 'process-2',
    target: 'storage-1',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#EC4899' },
  },
  {
    id: 'e-p2-st2',
    source: 'process-2',
    target: 'storage-2',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#EC4899' },
  },
  {
    id: 'e-p2-st3',
    source: 'process-2',
    target: 'storage-3',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#EC4899' },
  },
  {
    id: 'e-p2-st4',
    source: 'process-2',
    target: 'storage-4',
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2, stroke: '#EC4899' },
  },
];

nodeId = 11; // Start after demo nodes

const PVWorkflowBuilder = () => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const simulatorRef = useRef(null);

  const updateNodeData = useCallback((nodeId, updates) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...updates } }
          : node
      )
    );
  }, [setNodes]);

  const onConnect = useCallback(
    (params) => {
      const sourceNode = nodes.find(n => n.id === params.source);
      const color = sourceNode ? (
        {
          ncbi: '#06B6D4',
          pubmed: '#06B6D4',
          chembl: '#06B6D4',
          fda: '#06B6D4',
          preprocessing: '#8B5CF6',
          ner: '#EC4899',
          ingestion: '#F59E0B',
          classification: '#10B981',
          monitoring: '#6366F1',
        }[sourceNode.data.type] || '#64748b'
      ) : '#64748b';

      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: false,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
            },
            style: { strokeWidth: 2, stroke: color },
          },
          eds
        )
      );
    },
    [setEdges, nodes]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: getId(),
        type,
        position,
        data: {
          label: nodeLabels[type],
          type,
          status: 'pending',
          progress: 0,
          config: { maxDocuments: 100 },
          metrics: {},
          ...(type === 'preprocessing' && {
            subProcesses: {
              ocr: { status: 'pending', progress: 0 },
              htmlCleaning: { status: 'pending', progress: 0 },
              normalization: { status: 'pending', progress: 0 },
            },
          }),
          ...(type === 'ingestion' && {
            metrics: {
              elasticsearch: { progress: 0, status: 'pending' },
              neo4j: { progress: 0, status: 'pending' },
            },
          }),
        },
      };

      setNodes((nds) => nds.concat(newNode));
      setSnackbar({ open: true, message: `Added ${nodeLabels[type]} node`, severity: 'success' });
    },
    [reactFlowInstance, setNodes]
  );

  const handleRunWorkflow = async () => {
    if (nodes.length === 0) {
      setSnackbar({ open: true, message: 'Add nodes to the workflow first', severity: 'warning' });
      return;
    }

    try {
      setIsRunning(true);
      setSnackbar({ open: true, message: '🚀 Starting workflow simulation...', severity: 'info' });

      // Reset node statuses
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { ...node.data, status: 'pending', progress: 0 }
        }))
      );

      // Animate edges
      setEdges((eds) =>
        eds.map((edge) => ({ ...edge, animated: true }))
      );

      // Create and run simulator
      simulatorRef.current = new WorkflowSimulator(updateNodeData);
      const completed = await simulatorRef.current.executeWorkflow(nodes, edges);

      if (completed) {
        setSnackbar({ open: true, message: '✅ Workflow completed successfully!', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: '⏹️ Workflow stopped', severity: 'info' });
      }
    } catch (error) {
      console.error('Workflow execution error:', error);
      setSnackbar({ open: true, message: `❌ Error: ${error.message}`, severity: 'error' });
    } finally {
      setIsRunning(false);
      setEdges((eds) =>
        eds.map((edge) => ({ ...edge, animated: false }))
      );
    }
  };

  const handleStopWorkflow = () => {
    if (simulatorRef.current) {
      simulatorRef.current.stop();
    }
    setIsRunning(false);
    setSnackbar({ open: true, message: 'Workflow stopped', severity: 'info' });
  };

  const handleResetWorkflow = () => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    nodeId = 7;
    setSnackbar({ open: true, message: 'Workflow reset to demo', severity: 'info' });
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (simulatorRef.current) {
        simulatorRef.current.stop();
      }
    };
  }, []);

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)', bgcolor: 'background.default' }}>
      {/* Node Palette Sidebar */}
      <PVNodePalette />

      {/* Main Canvas */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Paper
          elevation={0}
          sx={{
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            borderRadius: 0,
          }}
        >
          <Box flex={1}>
            <Typography variant="h5" fontWeight={700}>
              🧪 Pharmacovigilance Workflow Builder
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Visual pipeline for PV document processing • Drag nodes from left panel and connect them
            </Typography>
          </Box>

          <Chip
            label={`${nodes.length} nodes`}
            size="small"
            color="primary"
            variant="outlined"
          />

          {isRunning ? (
            <Button
              variant="contained"
              color="error"
              startIcon={<StopIcon />}
              onClick={handleStopWorkflow}
            >
              Stop
            </Button>
          ) : (
            <>
              <Button
                variant="outlined"
                color="secondary"
                startIcon={<ResetIcon />}
                onClick={handleResetWorkflow}
                disabled={isRunning}
              >
                Reset
              </Button>

              <Button
                variant="contained"
                startIcon={<RunIcon />}
                onClick={handleRunWorkflow}
                disabled={nodes.length === 0}
                sx={{
                  background: 'linear-gradient(45deg, #10b981 30%, #059669 90%)',
                  boxShadow: '0 3px 5px 2px rgba(16, 185, 129, .3)',
                }}
              >
                Run Simulation
              </Button>
            </>
          )}
        </Paper>

        {/* React Flow Canvas */}
        <Box ref={reactFlowWrapper} sx={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
            defaultEdgeOptions={{
              animated: false,
              type: 'smoothstep',
            }}
            connectionLineType="smoothstep"
            connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
          >
            <Background color="#aaa" gap={20} size={1} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const colorMap = {
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
                return colorMap[node.type] || '#64748b';
              }}
              nodeStrokeWidth={3}
              zoomable
              pannable
            />
          </ReactFlow>
        </Box>
      </Box>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PVWorkflowBuilder;

