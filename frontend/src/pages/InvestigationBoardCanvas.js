import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  IconButton,
  Card,
  CardContent,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Menu,
  MenuItem,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  CircularProgress,
  Alert,
  Paper,
  Tabs,
  Tab,
  Grid
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  Link as LinkIcon,
  Note as NoteIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Hub as KnowledgeHubIcon,
  AutoAwesome as AISuggestionsIcon,
  Check as CheckIcon,
  Description as ReportIcon
} from '@mui/icons-material';
import apiService from '../services/api';

export default function InvestigationBoardCanvas() {
  const { boardId } = useParams();
  const navigate = useNavigate();

  // State
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  
  // Dialogs
  const [addEntityDialog, setAddEntityDialog] = useState(false);
  const [addFindingDialog, setAddFindingDialog] = useState(false);
  const [addConnectionDialog, setAddConnectionDialog] = useState(false);
  
  // Form data
  const [entityForm, setEntityForm] = useState({
    entity_name: '',
    entity_type: '',
    notes: ''
  });
  const [findingForm, setFindingForm] = useState({
    content: ''
  });
  const [connectionForm, setConnectionForm] = useState({
    target_entity_id: '',
    connection_type: 'related_to',
    notes: ''
  });
  
  // Documents state
  const [entityDocuments, setEntityDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  
  // AI Suggestions state
  const [suggestionsDrawerOpen, setSuggestionsDrawerOpen] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [missingConnections, setMissingConnections] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);
  const [selectedConnections, setSelectedConnections] = useState([]);
  
  // Report generation state
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [reportError, setReportError] = useState(null);
  
  // Entity-specific suggestions state
  const [entitySuggestionsOpen, setEntitySuggestionsOpen] = useState(false);
  const [entitySuggestions, setEntitySuggestions] = useState([]);
  const [entityConnections, setEntityConnections] = useState([]);
  const [loadingEntitySuggestions, setLoadingEntitySuggestions] = useState(false);
  const [selectedEntityForSuggestions, setSelectedEntityForSuggestions] = useState(null);

  // Load board
  useEffect(() => {
    loadBoard();
  }, [boardId]);

  const loadBoard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.investigationBoard.getBoard(boardId);
      // Backend returns {success: true, board: {...}}
      setBoard(response.board || response);
    } catch (err) {
      console.error('Failed to load board:', err);
      setError('Failed to load board. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Add entity
  const handleAddEntity = async () => {
    try {
      await apiService.investigationBoard.pinEntity({
        board_id: boardId,
        entity_name: entityForm.entity_name,
        entity_type: entityForm.entity_type,
        pin_reason: entityForm.notes,  // Backend uses pin_reason
        position_x: 100 + (board?.pinned_entities?.length || 0) * 50,
        position_y: 100 + (board?.pinned_entities?.length || 0) * 30
      });
      setAddEntityDialog(false);
      setEntityForm({ entity_name: '', entity_type: '', notes: '' });
      loadBoard();
    } catch (err) {
      console.error('Failed to add entity:', err);
      setError('Failed to add entity. Please try again.');
    }
  };

  // Delete entity
  const handleDeleteEntity = async (entityId) => {
    if (!window.confirm('Are you sure you want to remove this entity from the board?')) {
      return;
    }
    
    try {
      await apiService.investigationBoard.unpinEntity(entityId, boardId);
      setSelectedEntity(null);
      setDrawerOpen(false);
      loadBoard();
    } catch (err) {
      console.error('Failed to delete entity:', err);
      setError('Failed to delete entity. Please try again.');
    }
  };

  // Add finding
  const handleAddFinding = async () => {
    if (!selectedEntity) return;
    
    try {
      await apiService.investigationBoard.addFinding({
        pinned_entity_id: selectedEntity.id,
        content: findingForm.content
      });
      setAddFindingDialog(false);
      setFindingForm({ content: '' });
      loadBoard();
    } catch (err) {
      console.error('Failed to add finding:', err);
      setError('Failed to add finding. Please try again.');
    }
  };

  // Delete finding
  const handleDeleteFinding = async (findingId) => {
    try {
      await apiService.investigationBoard.deleteFinding(findingId);
      loadBoard();
    } catch (err) {
      console.error('Failed to delete finding:', err);
      setError('Failed to delete finding. Please try again.');
    }
  };

  // Add connection
  const handleAddConnection = async () => {
    if (!selectedEntity) return;
    
    try {
      await apiService.investigationBoard.createConnection({
        board_id: boardId,
        source_entity_id: selectedEntity.id,
        target_entity_id: connectionForm.target_entity_id,
        connection_type: connectionForm.connection_type,
        notes: connectionForm.notes
      });
      setAddConnectionDialog(false);
      setConnectionForm({ target_entity_id: '', connection_type: 'related_to', notes: '' });
      loadBoard();
    } catch (err) {
      console.error('Failed to add connection:', err);
      setError('Failed to add connection. Please try again.');
    }
  };

  // Export board
  const handleExport = async () => {
    try {
      const data = await apiService.investigationBoard.exportBoard(boardId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${board.title.replace(/\s+/g, '-')}-export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export board:', err);
      setError('Failed to export board. Please try again.');
    }
  };

  // Load documents for selected entity
  const loadEntityDocuments = async (entityId) => {
    setLoadingDocuments(true);
    try {
      const response = await apiService.investigationBoard.getEntityDocuments(entityId);
      setEntityDocuments(response.documents || []);
    } catch (err) {
      console.error('Failed to load entity documents:', err);
      setEntityDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };
  
  // Load AI suggestions
  const loadSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      const [suggestionsRes, connectionsRes] = await Promise.all([
        apiService.investigationBoard.getSuggestions(boardId, 10),
        apiService.investigationBoard.getMissingConnections(boardId)
      ]);
      
      setSuggestions(suggestionsRes.suggestions || []);
      setMissingConnections(connectionsRes.missing_connections || []);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
      setSuggestions([]);
      setMissingConnections([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };
  
  // Toggle suggestions drawer and load if needed
  const handleOpenSuggestions = () => {
    setSuggestionsDrawerOpen(true);
    if (suggestions.length === 0 && missingConnections.length === 0) {
      loadSuggestions();
    }
  };
  
  // Add selected suggestions
  const handleAddSuggestions = async () => {
    try {
      setLoadingSuggestions(true);
      const entityNames = selectedSuggestions.map(idx => suggestions[idx].entity_name);
      const connections = selectedConnections.map(idx => missingConnections[idx]);
      
      const result = await apiService.investigationBoard.batchAddSuggestions(
        boardId,
        entityNames,
        connections
      );
      
      if (result.success) {
        // Reload board
        await loadBoard();
        // Close drawer and reset selections
        setSuggestionsDrawerOpen(false);
        setSelectedSuggestions([]);
        setSelectedConnections([]);
        // Reload suggestions
        await loadSuggestions();
      }
    } catch (err) {
      console.error('Failed to add suggestions:', err);
      setError('Failed to add suggestions. Please try again.');
    } finally {
      setLoadingSuggestions(false);
    }
  };
  
  // Select entity
  const handleSelectEntity = (entityWrapper) => {
    // Extract entity and findings from the wrapper
    const entityWithFindings = {
      ...entityWrapper.entity,
      findings: entityWrapper.findings || []
    };
    setSelectedEntity(entityWithFindings);
    setDrawerOpen(true);
    
    // Load documents for this entity
    loadEntityDocuments(entityWithFindings.id);
  };
  
  // Generate AI Report
  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    setReportError(null);
    setReportDialogOpen(true);
    
    try {
      const result = await apiService.investigationBoard.generateReport(boardId, 'markdown', 'comprehensive');
      
      if (result.success) {
        setReportData(result);
      } else {
        setReportError(result.error || 'Failed to generate report');
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
      setReportError('Failed to generate report. Please try again.');
    } finally {
      setGeneratingReport(false);
    }
  };
  
  // Download report
  const handleDownloadReport = () => {
    if (!reportData || !reportData.report) return;
    
    const blob = new Blob([reportData.report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${board?.title || 'investigation'}-report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // Get Related Entities (Entity-specific suggestions)
  const handleGetRelatedEntities = async (pinId) => {
    try {
      setLoadingEntitySuggestions(true);
      setEntitySuggestionsOpen(true);
      setSelectedEntityForSuggestions(selectedEntity);
      
      const result = await apiService.investigationBoard.getEntitySuggestions(pinId, 10);
      
      if (result.success) {
        setEntitySuggestions(result.related_entities || []);
        setEntityConnections(result.suggested_connections || []);
      } else {
        console.error('Failed to load entity suggestions:', result.error);
      }
    } catch (err) {
      console.error('Failed to load entity suggestions:', err);
    } finally {
      setLoadingEntitySuggestions(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !board) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/investigations')} sx={{ mt: 2 }}>
          Back to Boards
        </Button>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2, borderRadius: 0 }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton onClick={() => navigate('/investigations')}>
                <BackIcon />
              </IconButton>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {board?.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {board?.description}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<ReportIcon />}
                onClick={handleGenerateReport}
                sx={{
                  borderColor: '#10b981',
                  color: '#10b981',
                  '&:hover': {
                    borderColor: '#059669',
                    backgroundColor: 'rgba(16, 185, 129, 0.04)'
                  }
                }}
              >
                Generate Report
              </Button>
              <Button
                variant="outlined"
                startIcon={<AISuggestionsIcon />}
                onClick={handleOpenSuggestions}
                sx={{
                  borderColor: '#764ba2',
                  color: '#764ba2',
                  '&:hover': {
                    borderColor: '#6a4293',
                    backgroundColor: 'rgba(118, 75, 162, 0.04)'
                  }
                }}
              >
                AI Suggestions
              </Button>
              <Button
                variant="outlined"
                startIcon={<ExportIcon />}
                onClick={handleExport}
              >
                Export
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setAddEntityDialog(true)}
              >
                Add Entity
              </Button>
            </Box>
          </Box>
        </Container>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Container maxWidth="xl">
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        </Container>
      )}

      {/* Main Content */}
      <Container maxWidth="xl">
        <Grid container spacing={2}>
          {/* Entities Grid */}
          {board?.pinned_entities && board.pinned_entities.length > 0 ? (
            board.pinned_entities.map((entityWrapper) => {
              const entity = entityWrapper.entity;
              return (
              <Grid item xs={12} sm={6} md={4} lg={3} key={entity.id}>
                <Card 
                  sx={{ 
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    },
                    border: selectedEntity?.id === entity.id ? '2px solid #1976d2' : 'none'
                  }}
                  onClick={() => handleSelectEntity(entityWrapper)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Chip 
                        label={entity.entity_type || 'Entity'} 
                        size="small" 
                        color="primary"
                        variant="outlined"
                      />
                      <IconButton 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteEntity(entity.id);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Typography variant="h6" gutterBottom>
                      {entity.entity_name}
                    </Typography>
                    {entity.pin_reason && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {entity.pin_reason.substring(0, 100)}
                        {entity.pin_reason.length > 100 && '...'}
                      </Typography>
                    )}
                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                      <Chip 
                        label={`${entity.findings?.length || 0} findings`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              );
            })
          ) : (
            <Grid item xs={12}>
              <Paper sx={{ p: 8, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom color="text.secondary">
                  No entities yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Start building your investigation by adding entities
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<AddIcon />}
                  onClick={() => setAddEntityDialog(true)}
                >
                  Add First Entity
                </Button>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Container>

      {/* Entity Details Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{ sx: { width: 400 } }}
      >
        {selectedEntity && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Entity Details</Typography>
              <IconButton onClick={() => setDrawerOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Box>

            <Chip label={selectedEntity.entity_type} color="primary" sx={{ mb: 2 }} />
            
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              {selectedEntity.entity_name}
            </Typography>

            {selectedEntity.pin_reason && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Pin Reason:</Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedEntity.pin_reason}
                </Typography>
              </Box>
            )}

            {/* View in Knowledge Hub button - only show if entity came from Knowledge Hub */}
            {selectedEntity.knowledge_hub_entity_id && (
              <Button
                fullWidth
                variant="outlined"
                startIcon={<KnowledgeHubIcon />}
                onClick={() => navigate('/knowledge-hub', { 
                  state: { searchEntity: selectedEntity.entity_name }
                })}
                sx={{ 
                  mb: 2,
                  borderColor: '#667eea',
                  color: '#667eea',
                  '&:hover': {
                    borderColor: '#5568d3',
                    backgroundColor: 'rgba(102, 126, 234, 0.04)'
                  }
                }}
              >
                View in Knowledge Hub
              </Button>
            )}

            {/* Get Related Entities button - Entity-specific AI suggestions */}
            <Button
              fullWidth
              variant="outlined"
              startIcon={<AISuggestionsIcon />}
              onClick={() => handleGetRelatedEntities(selectedEntity.id)}
              sx={{ 
                mb: 3,
                borderColor: '#10b981',
                color: '#10b981',
                '&:hover': {
                  borderColor: '#059669',
                  backgroundColor: 'rgba(16, 185, 129, 0.04)'
                }
              }}
            >
              Get Related Entities
            </Button>

            <Divider sx={{ my: 2 }} />

            {/* Tabs */}
            <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
              <Tab label="Findings" />
              <Tab label="Connections" />
              <Tab label="Documents" />
            </Tabs>

            {/* Findings Tab */}
            {activeTab === 0 && (
              <Box>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setAddFindingDialog(true)}
                  sx={{ mb: 2 }}
                >
                  Add Finding
                </Button>

                <List>
                  {selectedEntity.findings && selectedEntity.findings.length > 0 ? (
                    selectedEntity.findings.map((finding) => (
                      <ListItem key={finding.id} sx={{ bgcolor: '#f5f5f5', mb: 1, borderRadius: 1 }}>
                        <ListItemText
                          primary={finding.content}
                          secondary={new Date(finding.created_at).toLocaleString()}
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => handleDeleteFinding(finding.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      No findings yet
                    </Typography>
                  )}
                </List>
              </Box>
            )}

            {/* Connections Tab */}
            {activeTab === 1 && (
              <Box>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<LinkIcon />}
                  onClick={() => setAddConnectionDialog(true)}
                  sx={{ mb: 2 }}
                  disabled={!board?.pinned_entities || board.pinned_entities.length < 2}
                >
                  Add Connection
                </Button>

                <List>
                  {board?.connections && board.connections.length > 0 ? (
                    board.connections
                      .filter(conn => conn.source_id === selectedEntity.id || conn.target_id === selectedEntity.id)
                      .map((conn, idx) => {
                        const isSource = conn.source_id === selectedEntity.id;
                        const otherEntity = board.pinned_entities.find(ew => 
                          ew.entity.id === (isSource ? conn.target_id : conn.source_id)
                        )?.entity;
                        
                        return (
                          <ListItem key={idx} sx={{ bgcolor: '#f5f5f5', mb: 1, borderRadius: 1 }}>
                            <ListItemText
                              primary={`${isSource ? '→' : '←'} ${otherEntity?.entity_name || 'Unknown'}`}
                              secondary={conn.connection_type}
                            />
                          </ListItem>
                        );
                      })
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      No connections yet
                    </Typography>
                  )}
                </List>
              </Box>
            )}

            {/* Documents Tab */}
            {activeTab === 2 && (
              <Box>
                {loadingDocuments ? (
                  <Box display="flex" justifyContent="center" p={3}>
                    <CircularProgress />
                  </Box>
                ) : entityDocuments.length > 0 ? (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Found {entityDocuments.length} source document{entityDocuments.length !== 1 ? 's' : ''} mentioning <strong>{selectedEntity.entity_name}</strong>
                    </Typography>
                    <List>
                      {entityDocuments.map((doc, idx) => (
                        <Card 
                          key={idx}
                          sx={{ 
                            mb: 2, 
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                        >
                          <CardContent>
                            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                              {doc.title || 'Untitled'}
                            </Typography>
                            
                            <Box display="flex" gap={0.5} mb={1} flexWrap="wrap">
                              <Chip 
                                label={doc.source_type || 'PDF'} 
                                size="small" 
                                sx={{ 
                                  fontSize: '0.7rem',
                                  height: 20,
                                  backgroundColor: doc.is_external ? '#f97316' : '#3b82f6',
                                  color: 'white'
                                }}
                              />
                              {doc.entity_confidence && (
                                <Chip 
                                  label={`${(doc.entity_confidence * 100).toFixed(0)}% match`}
                                  size="small"
                                  sx={{
                                    fontSize: '0.7rem',
                                    height: 20,
                                    backgroundColor: doc.entity_confidence > 0.8 ? '#10b981' : '#f59e0b',
                                    color: 'white'
                                  }}
                                />
                              )}
                            </Box>
                            
                            {doc.snippets && doc.snippets.length > 0 && (
                              <Typography 
                                variant="caption" 
                                color="text.secondary"
                                sx={{
                                  display: 'block',
                                  mt: 1,
                                  fontStyle: 'italic'
                                }}
                              >
                                "{doc.snippets[0].substring(0, 150)}..."
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </List>
                  </>
                ) : (
                  <Box textAlign="center" py={4}>
                    <Typography variant="body2" color="text.secondary">
                      No source documents found for this entity
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {selectedEntity.knowledge_hub_entity_id 
                        ? 'This entity may not have associated documents in the knowledge base.'
                        : 'This entity was not linked from the Knowledge Hub.'}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        )}
      </Drawer>

      {/* Add Entity Dialog */}
      <Dialog open={addEntityDialog} onClose={() => setAddEntityDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Entity to Board</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Entity Name"
            fullWidth
            variant="outlined"
            value={entityForm.entity_name}
            onChange={(e) => setEntityForm({ ...entityForm, entity_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Entity Type"
            fullWidth
            variant="outlined"
            placeholder="e.g., Person, Organization, Drug, etc."
            value={entityForm.entity_type}
            onChange={(e) => setEntityForm({ ...entityForm, entity_type: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Notes"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={entityForm.notes}
            onChange={(e) => setEntityForm({ ...entityForm, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddEntityDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAddEntity} 
            variant="contained"
            disabled={!entityForm.entity_name.trim()}
          >
            Add Entity
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Finding Dialog */}
      <Dialog open={addFindingDialog} onClose={() => setAddFindingDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Finding</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Finding"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={findingForm.content}
            onChange={(e) => setFindingForm({ ...findingForm, content: e.target.value })}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddFindingDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAddFinding} 
            variant="contained"
            disabled={!findingForm.content.trim()}
          >
            Add Finding
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Connection Dialog */}
      <Dialog open={addConnectionDialog} onClose={() => setAddConnectionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Connection</DialogTitle>
        <DialogContent>
          <TextField
            select
            margin="dense"
            label="Connect to Entity"
            fullWidth
            variant="outlined"
            value={connectionForm.target_entity_id}
            onChange={(e) => setConnectionForm({ ...connectionForm, target_entity_id: e.target.value })}
            sx={{ mb: 2 }}
            SelectProps={{ native: true }}
          >
            <option value="">Select entity...</option>
            {board?.pinned_entities
              ?.map(ew => ew.entity)
              ?.filter(e => e.id !== selectedEntity?.id)
              .map(entity => (
                <option key={entity.id} value={entity.id}>
                  {entity.entity_name}
                </option>
              ))}
          </TextField>
          
          <TextField
            select
            margin="dense"
            label="Connection Type"
            fullWidth
            variant="outlined"
            value={connectionForm.connection_type}
            onChange={(e) => setConnectionForm({ ...connectionForm, connection_type: e.target.value })}
            sx={{ mb: 2 }}
            SelectProps={{ native: true }}
          >
            <option value="related_to">Related To</option>
            <option value="caused_by">Caused By</option>
            <option value="associated_with">Associated With</option>
            <option value="leads_to">Leads To</option>
            <option value="depends_on">Depends On</option>
          </TextField>

          <TextField
            margin="dense"
            label="Notes (optional)"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={connectionForm.notes}
            onChange={(e) => setConnectionForm({ ...connectionForm, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddConnectionDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAddConnection} 
            variant="contained"
            disabled={!connectionForm.target_entity_id}
          >
            Add Connection
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Suggestions Drawer */}
      <Drawer
        anchor="right"
        open={suggestionsDrawerOpen}
        onClose={() => setSuggestionsDrawerOpen(false)}
        PaperProps={{
          sx: { width: 450, p: 3 }
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AISuggestionsIcon sx={{ color: '#764ba2' }} />
            <Typography variant="h6" fontWeight={600}>
              AI Suggestions
            </Typography>
          </Box>
          <IconButton onClick={() => setSuggestionsDrawerOpen(false)}>
            <CloseIcon />
          </IconButton>
        </Box>

        {loadingSuggestions ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Entity Suggestions */}
            {suggestions.length > 0 && (
              <Box mb={4}>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: '#667eea' }}>
                  Related Entities ({suggestions.length})
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  Select entities to add to your investigation
                </Typography>
                
                <List>
                  {suggestions.map((suggestion, idx) => (
                    <Card
                      key={idx}
                      sx={{
                        mb: 2,
                        cursor: 'pointer',
                        border: selectedSuggestions.includes(idx) ? '2px solid #667eea' : '1px solid #e0e0e0',
                        backgroundColor: selectedSuggestions.includes(idx) ? 'rgba(102, 126, 234, 0.05)' : 'white',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3
                        }
                      }}
                      onClick={() => {
                        setSelectedSuggestions(prev =>
                          prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
                        );
                      }}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box flex={1}>
                            <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                              <Typography variant="subtitle2" fontWeight={600}>
                                {suggestion.entity_name}
                              </Typography>
                              {selectedSuggestions.includes(idx) && (
                                <CheckIcon sx={{ fontSize: 18, color: '#667eea' }} />
                              )}
                            </Box>
                            <Chip
                              label={suggestion.entity_type}
                              size="small"
                              sx={{ fontSize: '0.7rem', height: 20, mb: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary" display="block">
                              {suggestion.reason}
                            </Typography>
                            <Chip
                              label={`${Math.round(suggestion.confidence * 100)}% confidence`}
                              size="small"
                              sx={{
                                fontSize: '0.65rem',
                                height: 18,
                                mt: 1,
                                backgroundColor: suggestion.confidence > 0.7 ? '#10b981' : '#f59e0b',
                                color: 'white'
                              }}
                            />
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </List>
              </Box>
            )}

            {/* Missing Connections */}
            {missingConnections.length > 0 && (
              <Box>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: '#f97316' }}>
                  Missing Connections ({missingConnections.length})
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  Select connections to add between existing entities
                </Typography>
                
                <List>
                  {missingConnections.map((conn, idx) => (
                    <Card
                      key={idx}
                      sx={{
                        mb: 2,
                        cursor: 'pointer',
                        border: selectedConnections.includes(idx) ? '2px solid #f97316' : '1px solid #e0e0e0',
                        backgroundColor: selectedConnections.includes(idx) ? 'rgba(249, 115, 22, 0.05)' : 'white',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: 3
                        }
                      }}
                      onClick={() => {
                        setSelectedConnections(prev =>
                          prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
                        );
                      }}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box flex={1}>
                            <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                              <Typography variant="subtitle2" fontWeight={600}>
                                {conn.source_entity_name} → {conn.target_entity_name}
                              </Typography>
                              {selectedConnections.includes(idx) && (
                                <CheckIcon sx={{ fontSize: 18, color: '#f97316' }} />
                              )}
                            </Box>
                            <Chip
                              label={conn.suggested_type}
                              size="small"
                              sx={{ fontSize: '0.7rem', height: 20, mb: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary" display="block">
                              {conn.reason}
                            </Typography>
                            <Chip
                              label={`${Math.round(conn.confidence * 100)}% confidence`}
                              size="small"
                              sx={{
                                fontSize: '0.65rem',
                                height: 18,
                                mt: 1,
                                backgroundColor: conn.confidence > 0.7 ? '#10b981' : '#f59e0b',
                                color: 'white'
                              }}
                            />
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </List>
              </Box>
            )}

            {/* Empty State */}
            {suggestions.length === 0 && missingConnections.length === 0 && (
              <Box textAlign="center" py={8}>
                <AISuggestionsIcon sx={{ fontSize: 64, color: '#e0e0e0', mb: 2 }} />
                <Typography variant="body1" color="text.secondary" gutterBottom>
                  No suggestions available
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Add more entities to your board to get AI-powered suggestions
                </Typography>
              </Box>
            )}

            {/* Action Buttons */}
            {(suggestions.length > 0 || missingConnections.length > 0) && (
              <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={loadSuggestions}
                  disabled={loadingSuggestions}
                >
                  Refresh
                </Button>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleAddSuggestions}
                  disabled={selectedSuggestions.length === 0 && selectedConnections.length === 0}
                  startIcon={loadingSuggestions ? <CircularProgress size={16} /> : <AddIcon />}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #6a4293 100%)',
                    }
                  }}
                >
                  Add Selected ({selectedSuggestions.length + selectedConnections.length})
                </Button>
              </Box>
            )}
          </>
        )}
      </Drawer>

      {/* AI Report Generation Dialog */}
      <Dialog 
        open={reportDialogOpen} 
        onClose={() => !generatingReport && setReportDialogOpen(false)} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={1}>
              <ReportIcon sx={{ color: '#10b981' }} />
              <Typography variant="h6" fontWeight={600}>
                AI Investigation Report
              </Typography>
            </Box>
            {!generatingReport && (
              <IconButton onClick={() => setReportDialogOpen(false)}>
                <CloseIcon />
              </IconButton>
            )}
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {generatingReport ? (
            <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" py={8}>
              <CircularProgress size={60} sx={{ mb: 3, color: '#10b981' }} />
              <Typography variant="h6" gutterBottom>
                Generating Your Investigation Report...
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 2, maxWidth: 500 }}>
                Our AI is analyzing {board?.pinned_entities?.length || 0} entities, 
                {board?.connections?.length || 0} relationships, and source documents 
                to create a comprehensive professional report.
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                This may take 30-60 seconds...
              </Typography>
            </Box>
          ) : reportError ? (
            <Box textAlign="center" py={8}>
              <Typography variant="h6" color="error" gutterBottom>
                Failed to Generate Report
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {reportError}
              </Typography>
              <Button 
                variant="contained" 
                onClick={handleGenerateReport}
                startIcon={<ReportIcon />}
                sx={{ mt: 3 }}
              >
                Try Again
              </Button>
            </Box>
          ) : reportData ? (
            <Box>
              {/* Report Metadata */}
              <Box sx={{ mb: 3, p: 2, bgcolor: '#f0fdf4', borderRadius: 2 }}>
                <Typography variant="subtitle2" color="#059669" fontWeight={600} gutterBottom>
                  Report Generated Successfully
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={3}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Entities
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {reportData.metadata?.entity_count || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Relationships
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {reportData.metadata?.relationship_count || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Source Documents
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {reportData.metadata?.source_document_count || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Generated
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {new Date(reportData.metadata?.generated_at).toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

              {/* Report Content Preview */}
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 3, 
                  bgcolor: '#fafafa',
                  maxHeight: '500px',
                  overflow: 'auto',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  fontSize: '0.875rem',
                  lineHeight: 1.6
                }}
              >
                {reportData.report}
              </Paper>
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          {reportData && !generatingReport && (
            <>
              <Button onClick={() => setReportDialogOpen(false)}>
                Close
              </Button>
              <Button 
                variant="contained" 
                startIcon={<ExportIcon />}
                onClick={handleDownloadReport}
                sx={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                  }
                }}
              >
                Download Report
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Entity-Specific AI Suggestions Dialog */}
      <Dialog
        open={entitySuggestionsOpen}
        onClose={() => !loadingEntitySuggestions && setEntitySuggestionsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={1}>
              <AISuggestionsIcon sx={{ color: '#10b981' }} />
              <Typography variant="h6" fontWeight={600}>
                Related to {selectedEntityForSuggestions?.entity_name}
              </Typography>
            </Box>
            {!loadingEntitySuggestions && (
              <IconButton onClick={() => setEntitySuggestionsOpen(false)}>
                <CloseIcon />
              </IconButton>
            )}
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {loadingEntitySuggestions ? (
            <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" py={4}>
              <CircularProgress sx={{ color: '#10b981', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Finding related entities and connections...
              </Typography>
            </Box>
          ) : (
            <>
              {/* Related Entities */}
              {entitySuggestions.length > 0 && (
                <Box mb={3}>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: '#10b981' }}>
                    Related Entities ({entitySuggestions.length})
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                    Entities connected to {selectedEntityForSuggestions?.entity_name}
                  </Typography>
                  
                  <List>
                    {entitySuggestions.map((suggestion, idx) => (
                      <Card
                        key={idx}
                        sx={{
                          mb: 2,
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: 3
                          }
                        }}
                      >
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="start">
                            <Box flex={1}>
                              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                                {suggestion.entity_name}
                              </Typography>
                              <Chip
                                label={suggestion.entity_type}
                                size="small"
                                sx={{ fontSize: '0.7rem', height: 20, mb: 1 }}
                              />
                              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                                {suggestion.reason}
                              </Typography>
                              <Chip
                                label={`${Math.round(suggestion.confidence * 100)}% confidence`}
                                size="small"
                                sx={{
                                  fontSize: '0.65rem',
                                  height: 18,
                                  mt: 1,
                                  backgroundColor: suggestion.confidence > 0.7 ? '#10b981' : '#f59e0b',
                                  color: 'white'
                                }}
                              />
                            </Box>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={async () => {
                                try {
                                  await apiService.investigationBoard.pinEntity({
                                    board_id: boardId,
                                    entity_name: suggestion.entity_name,
                                    entity_type: suggestion.entity_type,
                                    pin_reason: suggestion.reason,
                                    position_x: Math.random() * 400,
                                    position_y: Math.random() * 300,
                                    knowledge_hub_entity_id: suggestion.entity_id
                                  });
                                  await loadBoard();
                                  setEntitySuggestionsOpen(false);
                                } catch (err) {
                                  console.error('Failed to add entity:', err);
                                }
                              }}
                              sx={{ minWidth: 80 }}
                              >
                                Add
                              </Button>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </List>
                </Box>
              )}

              {/* Suggested Connections */}
              {entityConnections.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: '#f97316' }}>
                    Suggested Connections ({entityConnections.length})
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                    Connections between {selectedEntityForSuggestions?.entity_name} and other entities on your board
                  </Typography>
                  
                  <List>
                    {entityConnections.map((conn, idx) => (
                      <Card
                        key={idx}
                        sx={{
                          mb: 2,
                          border: '1px solid #e0e0e0',
                          transition: 'all 0.2s',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: 3
                          }
                        }}
                      >
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="start">
                            <Box flex={1}>
                              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                                {conn.source_entity} → {conn.target_entity}
                              </Typography>
                              <Chip
                                label={conn.suggested_type}
                                size="small"
                                sx={{ fontSize: '0.7rem', height: 20, mb: 1 }}
                              />
                              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                                {conn.reason}
                              </Typography>
                              <Chip
                                label={`${Math.round(conn.confidence * 100)}% confidence`}
                                size="small"
                                sx={{
                                  fontSize: '0.65rem',
                                  height: 18,
                                  mt: 1,
                                  backgroundColor: conn.confidence > 0.7 ? '#10b981' : '#f59e0b',
                                  color: 'white'
                                }}
                              />
                            </Box>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={async () => {
                                // Find the pin IDs for source and target entities
                                const sourcePinned = board.pinned_entities.find(ew => 
                                  ew.entity.entity_name === conn.source_entity
                                );
                                const targetPinned = board.pinned_entities.find(ew => 
                                  ew.entity.entity_name === conn.target_entity
                                );
                                
                                if (sourcePinned && targetPinned) {
                                  try {
                                    await apiService.investigationBoard.createConnection({
                                      board_id: boardId,
                                      source_entity_id: sourcePinned.entity.id,
                                      target_entity_id: targetPinned.entity.id,
                                      connection_type: conn.suggested_type,
                                      notes: conn.reason
                                    });
                                    await loadBoard();
                                  } catch (err) {
                                    console.error('Failed to add connection:', err);
                                  }
                                }
                              }}
                              sx={{ minWidth: 80 }}
                            >
                              Add
                            </Button>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </List>
                </Box>
              )}

              {/* Empty State */}
              {entitySuggestions.length === 0 && entityConnections.length === 0 && (
                <Box textAlign="center" py={8}>
                  <AISuggestionsIcon sx={{ fontSize: 64, color: '#e0e0e0', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    No related entities found
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Try adding more entities or check the Knowledge Hub
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

