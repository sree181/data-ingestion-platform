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
  Box, Button, Typography, IconButton, Chip, Snackbar, Alert,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControlLabel, Checkbox,
  List, ListItem, ListItemText, ListItemButton, ListItemSecondaryAction,
  Grid, Card, CardContent, CardActions, Divider
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  Save as SaveIcon,
  Delete as ClearIcon,
  Info as InfoIcon,
  FolderOpen as LoadIcon,
  ViewModule as TemplatesIcon,
  Close as CloseIcon,
  DeleteOutline as DeleteIcon,
} from '@mui/icons-material';
import WorkflowNode from '../components/WorkflowNode';
import NodePalette from '../components/NodePalette';
import apiService from '../services/api';

const nodeTypes = {
  upload: WorkflowNode,
  aiProcessing: WorkflowNode,
  knowledgeGraph: WorkflowNode,
  report: WorkflowNode,
};

const nodeLabels = {
  upload: 'Upload Documents',
  aiProcessing: 'AI Processing',
  knowledgeGraph: 'Knowledge Graph',
  report: 'Generate Report',
};

const nodeDescriptions = {
  upload: 'Upload PDF files for processing',
  aiProcessing: 'Extract entities and relationships using AI',
  knowledgeGraph: 'Build interactive graph visualization',
  report: 'Create comprehensive investigation report',
};

let nodeId = 0;
const getId = () => `node_${nodeId++}`;

// Initial demo workflow
const initialNodes = [
  {
    id: 'demo-1',
    type: 'upload',
    position: { x: 100, y: 200 },
    data: {
      label: 'Upload Documents',
      description: 'Upload PDF files for processing',
      type: 'upload',
      status: 'pending',
    },
  },
  {
    id: 'demo-2',
    type: 'aiProcessing',
    position: { x: 400, y: 200 },
    data: {
      label: 'AI Processing',
      description: 'Extract entities & relationships using AI',
      type: 'aiProcessing',
      status: 'pending',
    },
  },
  {
    id: 'demo-3',
    type: 'knowledgeGraph',
    position: { x: 700, y: 200 },
    data: {
      label: 'Knowledge Graph',
      description: 'Build interactive graph visualization',
      type: 'knowledgeGraph',
      status: 'pending',
    },
  },
  {
    id: 'demo-4',
    type: 'report',
    position: { x: 1000, y: 200 },
    data: {
      label: 'Generate Report',
      description: 'Create comprehensive investigation report',
      type: 'report',
      status: 'pending',
    },
  },
];

const initialEdges = [
  {
    id: 'e1-2',
    source: 'demo-1',
    target: 'demo-2',
    type: 'smoothstep',
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e2-3',
    source: 'demo-2',
    target: 'demo-3',
    type: 'smoothstep',
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e3-4',
    source: 'demo-3',
    target: 'demo-4',
    type: 'smoothstep',
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
  },
];

nodeId = 5; // Start after demo nodes

const WorkflowBuilder = () => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [executionId, setExecutionId] = useState(null);
  const statusPollInterval = useRef(null);
  
  // Save/Load/Templates state
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);
  const [templatesDialogOpen, setTemplatesDialogOpen] = useState(false);
  const [workflowTitle, setWorkflowTitle] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState(null);
  const [loadingWorkflows, setLoadingWorkflows] = useState(false);

  const onConnect = useCallback(
    (params) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: true,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
            },
            style: { strokeWidth: 2 },
          },
          eds
        )
      ),
    [setEdges]
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
          description: nodeDescriptions[type],
          type,
          status: 'pending',
        },
      };

      setNodes((nds) => nds.concat(newNode));
      setSnackbar({ open: true, message: `Added ${nodeLabels[type]} node`, severity: 'success' });
    },
    [reactFlowInstance, setNodes]
  );

  // Poll execution status
  const pollExecutionStatus = useCallback(async (execId) => {
    try {
      console.log('📊 [Workflow] Polling status for:', execId);
      const result = await apiService.workflow.getStatus(execId);
      console.log('📊 [Workflow] Status response:', result);
      
      if (result.success && result.execution) {
        const execution = result.execution;
        console.log('📊 [Workflow] Execution status:', execution.status);
        console.log('📊 [Workflow] Node statuses:', execution.nodes);
        
        // Update node statuses
        setNodes((nds) =>
          nds.map((node) => {
            const nodeStatus = execution.nodes[node.id];
            if (nodeStatus) {
              console.log(`📊 [Workflow] Updating node ${node.id} to ${nodeStatus.status}`);
              return {
                ...node,
                data: {
                  ...node.data,
                  status: nodeStatus.status,
                  result: nodeStatus.result
                }
              };
            }
            return node;
          })
        );
        
        // Check if execution is complete
        if (execution.status === 'completed') {
          console.log('✅ [Workflow] Workflow completed!');
          setIsRunning(false);
          setSnackbar({ open: true, message: 'Workflow completed successfully!', severity: 'success' });
          if (statusPollInterval.current) {
            clearInterval(statusPollInterval.current);
          }
        } else if (execution.status === 'failed') {
          console.log('❌ [Workflow] Workflow failed!');
          setIsRunning(false);
          setSnackbar({ open: true, message: `Workflow failed: ${execution.error}`, severity: 'error' });
          if (statusPollInterval.current) {
            clearInterval(statusPollInterval.current);
          }
        }
      }
    } catch (error) {
      console.error('❌ [Workflow] Failed to poll execution status:', error);
    }
  }, [setNodes]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (statusPollInterval.current) {
        clearInterval(statusPollInterval.current);
      }
    };
  }, []);

  const handleRunWorkflow = async () => {
    console.log('🚀 [Workflow] Run button clicked');
    console.log('🚀 [Workflow] Current nodes:', nodes.length);
    console.log('🚀 [Workflow] Current edges:', edges.length);
    
    if (nodes.length === 0) {
      setSnackbar({ open: true, message: 'Add nodes to the workflow first', severity: 'warning' });
      return;
    }

    try {
      setIsRunning(true);
      setSnackbar({ open: true, message: 'Starting workflow execution...', severity: 'info' });

      // Reset node statuses
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { ...node.data, status: 'pending' }
        }))
      );

      // Execute workflow via backend
      const workflowId = `workflow_${Date.now()}`;
      console.log('🚀 [Workflow] Calling API with workflow ID:', workflowId);
      console.log('🚀 [Workflow] Nodes to send:', JSON.stringify(nodes, null, 2));
      console.log('🚀 [Workflow] Edges to send:', JSON.stringify(edges, null, 2));
      
      const result = await apiService.workflow.execute(workflowId, nodes, edges);
      
      console.log('✅ [Workflow] API response:', result);

      if (result.success) {
        const execId = result.execution_id;
        setExecutionId(execId);
        console.log('✅ [Workflow] Execution started! ID:', execId);
        setSnackbar({ open: true, message: 'Workflow execution started!', severity: 'info' });

        // Start polling for status updates
        statusPollInterval.current = setInterval(() => {
          pollExecutionStatus(execId);
        }, 1000); // Poll every second

        // Initial poll
        pollExecutionStatus(execId);
      } else {
        throw new Error('Failed to start workflow execution');
      }
    } catch (error) {
      console.error('❌ [Workflow] Error:', error);
      console.error('❌ [Workflow] Error details:', error.response?.data);
      setIsRunning(false);
      setSnackbar({ 
        open: true, 
        message: `Failed to execute workflow: ${error.message}`, 
        severity: 'error' 
      });
    }
  };

  const handleClearWorkflow = () => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    nodeId = 5;
    setCurrentWorkflowId(null);
    setWorkflowTitle('');
    setWorkflowDescription('');
    setSnackbar({ open: true, message: 'Workflow reset to demo', severity: 'info' });
  };

  // Save Workflow
  const handleOpenSaveDialog = () => {
    setSaveDialogOpen(true);
  };

  const handleSaveWorkflow = async () => {
    if (!workflowTitle.trim()) {
      setSnackbar({ open: true, message: 'Please enter a workflow title', severity: 'warning' });
      return;
    }

    try {
      const result = await apiService.workflow.save(
        workflowTitle,
        workflowDescription,
        nodes,
        edges,
        [],
        saveAsTemplate
      );

      if (result.success) {
        setCurrentWorkflowId(result.workflow_id);
        setSaveDialogOpen(false);
        setSnackbar({ open: true, message: 'Workflow saved successfully!', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: result.message || 'Failed to save workflow', severity: 'error' });
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      setSnackbar({ open: true, message: `Error: ${error.message}`, severity: 'error' });
    }
  };

  // Load Workflow
  const handleOpenLoadDialog = async () => {
    setLoadDialogOpen(true);
    setLoadingWorkflows(true);
    
    try {
      const result = await apiService.workflow.list(false); // Get non-template workflows
      if (result.success) {
        setSavedWorkflows(result.workflows || []);
      }
    } catch (error) {
      console.error('Error loading workflows:', error);
      setSnackbar({ open: true, message: 'Failed to load workflows', severity: 'error' });
    } finally {
      setLoadingWorkflows(false);
    }
  };

  const handleLoadWorkflow = async (workflowId) => {
    try {
      const result = await apiService.workflow.get(workflowId);
      
      if (result.success && result.workflow) {
        const workflow = result.workflow;
        setNodes(workflow.nodes);
        setEdges(workflow.edges);
        setWorkflowTitle(workflow.title);
        setWorkflowDescription(workflow.description || '');
        setCurrentWorkflowId(workflow.id);
        setLoadDialogOpen(false);
        setSnackbar({ open: true, message: `Loaded: ${workflow.title}`, severity: 'success' });
      }
    } catch (error) {
      console.error('Error loading workflow:', error);
      setSnackbar({ open: true, message: 'Failed to load workflow', severity: 'error' });
    }
  };

  const handleDeleteWorkflow = async (workflowId) => {
    try {
      const result = await apiService.workflow.delete(workflowId);
      
      if (result.success) {
        setSavedWorkflows(savedWorkflows.filter(w => w.id !== workflowId));
        setSnackbar({ open: true, message: 'Workflow deleted', severity: 'success' });
      }
    } catch (error) {
      console.error('Error deleting workflow:', error);
      setSnackbar({ open: true, message: 'Failed to delete workflow', severity: 'error' });
    }
  };

  // Templates
  const handleOpenTemplatesDialog = async () => {
    setTemplatesDialogOpen(true);
    
    try {
      const result = await apiService.workflow.listTemplates();
      if (result.success) {
        setTemplates(result.templates || []);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      setSnackbar({ open: true, message: 'Failed to load templates', severity: 'error' });
    }
  };

  const handleUseTemplate = async (templateId) => {
    try {
      const result = await apiService.workflow.useTemplate(templateId);
      
      if (result.success && result.template) {
        const template = result.template;
        setNodes(template.nodes);
        setEdges(template.edges);
        setWorkflowTitle('');
        setWorkflowDescription('');
        setCurrentWorkflowId(null);
        setTemplatesDialogOpen(false);
        setSnackbar({ open: true, message: `Loaded template: ${template.title}`, severity: 'success' });
      }
    } catch (error) {
      console.error('Error loading template:', error);
      setSnackbar({ open: true, message: 'Failed to load template', severity: 'error' });
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)', bgcolor: 'background.default' }}>
      {/* Node Palette Sidebar */}
      <NodePalette />

      {/* Main Canvas */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box flex={1}>
            <Typography variant="h5" fontWeight={700}>
              Workflow Builder
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Drag nodes from the left panel and connect them to create your workflow
            </Typography>
          </Box>

          <Chip
            label={`${nodes.length} nodes`}
            size="small"
            color="primary"
            variant="outlined"
          />

          <Button
            variant="outlined"
            startIcon={<TemplatesIcon />}
            onClick={handleOpenTemplatesDialog}
          >
            Templates
          </Button>

          <Button
            variant="outlined"
            startIcon={<LoadIcon />}
            onClick={handleOpenLoadDialog}
          >
            Load
          </Button>

          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={handleOpenSaveDialog}
            disabled={nodes.length === 0}
          >
            Save
          </Button>

          <Button
            variant="outlined"
            color="error"
            startIcon={<ClearIcon />}
            onClick={handleClearWorkflow}
            disabled={nodes.length === 0 || isRunning}
          >
            Clear
          </Button>

          <Button
            variant="contained"
            startIcon={<RunIcon />}
            onClick={handleRunWorkflow}
            disabled={nodes.length === 0 || isRunning}
            sx={{
              background: 'linear-gradient(45deg, #10b981 30%, #059669 90%)',
              boxShadow: '0 3px 5px 2px rgba(16, 185, 129, .3)',
            }}
          >
            {isRunning ? 'Running...' : 'Run Workflow'}
          </Button>
        </Box>

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
              animated: true,
              type: 'smoothstep',
            }}
            connectionLineType="smoothstep"
            connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
          >
            <Background color="#aaa" gap={16} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const colorMap = {
                  upload: '#3b82f6',
                  aiProcessing: '#ec4899',
                  knowledgeGraph: '#8b5cf6',
                  report: '#10b981',
                };
                return colorMap[node.type] || '#64748b';
              }}
              nodeStrokeWidth={3}
              zoomable
              pannable
            />
          </ReactFlow>
        </Box>

        {/* Empty State */}
        {nodes.length === 0 && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              pointerEvents: 'none',
            }}
          >
            <InfoIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Start building your workflow
            </Typography>
            <Typography variant="body2" color="text.disabled">
              Drag nodes from the left panel to get started
            </Typography>
          </Box>
        )}
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

      {/* Save Workflow Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Save Workflow
          <IconButton
            onClick={() => setSaveDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <TextField
            label="Workflow Title"
            fullWidth
            value={workflowTitle}
            onChange={(e) => setWorkflowTitle(e.target.value)}
            placeholder="e.g., Document Analysis Pipeline"
            sx={{ mb: 2 }}
            autoFocus
          />
          <TextField
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
            placeholder="Describe what this workflow does..."
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={saveAsTemplate}
                onChange={(e) => setSaveAsTemplate(e.target.checked)}
              />
            }
            label="Save as template (reusable workflow)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveWorkflow} variant="contained" startIcon={<SaveIcon />}>
            Save Workflow
          </Button>
        </DialogActions>
      </Dialog>

      {/* Load Workflow Dialog */}
      <Dialog open={loadDialogOpen} onClose={() => setLoadDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Load Workflow
          <IconButton
            onClick={() => setLoadDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {loadingWorkflows ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography>Loading workflows...</Typography>
            </Box>
          ) : savedWorkflows.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">No saved workflows yet</Typography>
              <Typography variant="caption" color="text.disabled">
                Create and save a workflow to see it here
              </Typography>
            </Box>
          ) : (
            <List>
              {savedWorkflows.map((workflow) => (
                <ListItem key={workflow.id} divider>
                  <ListItemButton onClick={() => handleLoadWorkflow(workflow.id)}>
                    <ListItemText
                      primary={workflow.title}
                      secondary={
                        <>
                          {workflow.description && <>{workflow.description}<br /></>}
                          <Typography variant="caption" color="text.disabled">
                            {workflow.node_count} nodes • {workflow.edge_count} connections
                            {workflow.updated_at && ` • Updated: ${new Date(workflow.updated_at).toLocaleDateString()}`}
                          </Typography>
                        </>
                      }
                    />
                  </ListItemButton>
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => handleDeleteWorkflow(workflow.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoadDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Templates Gallery Dialog */}
      <Dialog open={templatesDialogOpen} onClose={() => setTemplatesDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          Workflow Templates
          <IconButton
            onClick={() => setTemplatesDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            {templates.map((template) => (
              <Grid item xs={12} md={6} lg={4} key={template.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flex: 1 }}>
                    <Typography variant="h6" gutterBottom>
                      {template.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {template.description}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                      {template.tags?.map((tag) => (
                        <Chip key={tag} label={tag} size="small" color="primary" variant="outlined" />
                      ))}
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="caption" color="text.disabled">
                      {template.nodes?.length || 0} nodes • {template.edges?.length || 0} connections
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={() => handleUseTemplate(template.id)}
                    >
                      Use Template
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplatesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkflowBuilder;
