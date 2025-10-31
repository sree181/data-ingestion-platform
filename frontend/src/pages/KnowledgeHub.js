import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Paper,
  InputAdornment,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  ListItemButton,
  Badge,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Hub as HubIcon,
  Science as DrugIcon,
  LocalHospital as DiseaseIcon,
  Person as PersonIcon,
  Business as OrgIcon,
  Category as EntityIcon,
  AccountTree as TreeIcon,
  Send as SendIcon,
  Chat as ChatIcon,
  PushPin as PinIcon,
  Dashboard as BoardIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

const KnowledgeHub = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const graphRef = useRef();

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entityDetails, setEntityDetails] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [statistics, setStatistics] = useState({});
  const [entityTypes, setEntityTypes] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [graphDepth, setGraphDepth] = useState(2);
  const [activeTab, setActiveTab] = useState(0);
  
  // NEW: Source filter state
  const [sourceFilter, setSourceFilter] = useState('all');
  
  // NEW: Highlight state
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState(null);
  
  // NEW: Source documents state
  const [sourceDocuments, setSourceDocuments] = useState([]);
  const [loadingSources, setLoadingSources] = useState(false);
  
  // NEW: Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);
  
  // NEW: Investigation Board integration state
  const [pinToBoardDialogOpen, setPinToBoardDialogOpen] = useState(false);
  const [availableBoards, setAvailableBoards] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState('');
  const [loadingBoards, setLoadingBoards] = useState(false);
  const [pinning, setPinning] = useState(false);

  // Enhanced Entity type configuration with gradients and depth
  const entityConfig = {
    Drug: { 
      color: '#10b981', 
      gradient: ['#10b981', '#059669'],
      shadow: 'rgba(16, 185, 129, 0.4)',
      hover: '#34d399',
      glow: 'rgba(16, 185, 129, 0.6)',
      label: 'Drugs', 
      icon: <DrugIcon /> 
    },
    Disease: { 
      color: '#ef4444', 
      gradient: ['#ef4444', '#dc2626'],
      shadow: 'rgba(239, 68, 68, 0.4)',
      hover: '#f87171',
      glow: 'rgba(239, 68, 68, 0.6)',
      label: 'Diseases', 
      icon: <DiseaseIcon /> 
    },
    Person: { 
      color: '#8b5cf6', 
      gradient: ['#8b5cf6', '#7c3aed'],
      shadow: 'rgba(139, 92, 246, 0.4)',
      hover: '#a78bfa',
      glow: 'rgba(139, 92, 246, 0.6)',
      label: 'People', 
      icon: <PersonIcon /> 
    },
    Organization: { 
      color: '#f59e0b', 
      gradient: ['#f59e0b', '#d97706'],
      shadow: 'rgba(245, 158, 11, 0.4)',
      hover: '#fbbf24',
      glow: 'rgba(245, 158, 11, 0.6)',
      label: 'Organizations', 
      icon: <OrgIcon /> 
    },
    Procedure: { 
      color: '#06b6d4', 
      gradient: ['#06b6d4', '#0891b2'],
      shadow: 'rgba(6, 182, 212, 0.4)',
      hover: '#22d3ee',
      glow: 'rgba(6, 182, 212, 0.6)',
      label: 'Procedures', 
      icon: <EntityIcon /> 
    },
    Entity: { 
      color: '#6b7280', 
      gradient: ['#6b7280', '#4b5563'],
      shadow: 'rgba(107, 114, 128, 0.4)',
      hover: '#9ca3af',
      glow: 'rgba(107, 114, 128, 0.6)',
      label: 'Other Entities', 
      icon: <EntityIcon /> 
    },
  };

  // Load initial statistics and FULL GRAPH on mount
  useEffect(() => {
    loadStatistics();
    loadEntityTypes();
    loadFullGraph(); // Load entire graph by default
  }, []);

  // Handle navigation from Investigation Board
  useEffect(() => {
    if (location.state?.searchEntity) {
      const entityName = location.state.searchEntity;
      setSearchQuery(entityName);
      // Trigger search after a short delay to let state update
      setTimeout(() => {
        handleSearchFromNavigation(entityName);
      }, 300);
      // Clear the state to prevent re-searching on re-render
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleSearchFromNavigation = async (entityName) => {
    setLoading(true);
    setError(null);
    
    try {
      const searchResponse = await apiService.searchKnowledgeHubEntities(entityName, null, 20);
      
      if (searchResponse.success && searchResponse.entities && searchResponse.entities.length > 0) {
        setSearchResults(searchResponse.entities);
        // Auto-select first result to show entity details
        const firstEntity = searchResponse.entities[0];
        // Simulate node click to show entity details
        const nodeData = {
          id: firstEntity.id || firstEntity.name,
          name: firstEntity.name,
          type: firstEntity.type,
          ...firstEntity
        };
        setTimeout(() => handleNodeClick(nodeData), 100);
      } else {
        setError(`Entity "${entityName}" not found in Knowledge Hub`);
      }
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search for entity');
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await apiService.getKnowledgeHubStatistics();
      if (response.success) {
        setStatistics(response.statistics);
      }
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  };

  const loadEntityTypes = async () => {
    try {
      const response = await apiService.getKnowledgeHubEntityTypes();
      if (response.success) {
        setEntityTypes(response.entity_types || []);
      }
    } catch (err) {
      console.error('Failed to load entity types:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      // Search for entities
      const searchResponse = await apiService.searchKnowledgeHubEntities(
        searchQuery,
        selectedTypes.length > 0 ? selectedTypes : null,
        20
      );

      if (searchResponse.success && searchResponse.entities && searchResponse.entities.length > 0) {
        setSearchResults(searchResponse.entities);
        
        // Auto-select first result if only one
        if (searchResponse.entities.length === 1) {
          await loadEntityGraph(searchResponse.entities[0].name);
        }
      } else {
        setError('No entities found matching your search.');
        setSearchResults([]);
      }
    } catch (err) {
      setError(`Search failed: ${err.message}`);
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEntityGraph = async (entityName) => {
    setLoading(true);
    setError(null);
    setSelectedEntity(entityName);

    try {
      const response = await apiService.getKnowledgeHubEntity(entityName, graphDepth);

      if (response.success && response.graph) {
        const { nodes, edges } = response.graph;
        
        // Transform data for react-force-graph
        const formattedNodes = nodes.map(node => ({
          id: node.id,
          name: node.name,
          type: node.type,
          val: node.is_center ? 15 : 8,
          color: getNodeColorBySource(node),
          confidence: node.confidence,
          description: node.description,
          isCenter: node.is_center,
          source_types: node.source_types || [],
          source_count: node.source_count || 1,
          has_pdf: node.has_pdf,
          has_external: node.has_external
        }));

        const formattedEdges = edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          type: edge.type,
          label: edge.predicate,
          confidence: edge.confidence
        }));

        setGraphData({
          nodes: formattedNodes,
          links: formattedEdges
        });

        // Center the graph
        setTimeout(() => {
          if (graphRef.current) {
            graphRef.current.zoomToFit(400);
          }
        }, 100);
      } else {
        setError('Failed to load entity graph.');
      }
    } catch (err) {
      setError(`Failed to load graph: ${err.message}`);
      console.error('Entity graph loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (type) => {
    return entityConfig[type]?.color || entityConfig.Entity.color;
  };

  // Color by source mix (PDF, external, or both)
  const getNodeColorBySource = (node) => {
    const hasPdf = node.has_pdf || (node.source_types && node.source_types.includes('pdf'));
    const hasExternal = node.has_external || (node.source_types && node.source_types.some(st => st !== 'pdf'));
    
    if (hasPdf && hasExternal) {
      // Cross-source (mentioned in both PDFs and external sources)
      return '#9333ea'; // Purple
    } else if (hasExternal) {
      // External source only (Clinical Trials, FDA, etc.)
      return '#f97316'; // Orange
    } else {
      // PDF only
      return '#3b82f6'; // Blue
    }
  };

  const loadFullGraph = async () => {
    setLoading(true);
    setError(null);
    setSelectedEntity(null);
    
    try {
      // Get all entities and relationships from Neo4j
      const response = await apiService.getKnowledgeHubFullGraph();
      
      // API returns {nodes: [...], edges: [...]} directly
      if (response && response.nodes && response.nodes.length > 0) {
        const { nodes, edges } = response;
        
        // Apply source filter
        let filteredNodes = nodes;
        if (sourceFilter !== 'all') {
          filteredNodes = nodes.filter(node => {
            if (sourceFilter === 'pdf') {
              return node.has_pdf && !node.has_external;
            } else if (sourceFilter === 'external') {
              return node.has_external && !node.has_pdf;
            } else if (sourceFilter === 'cross-source') {
              return node.has_pdf && node.has_external;
            }
            return true;
          });
        }
        
        // Get IDs of filtered nodes
        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
        
        // Filter edges to only include those between filtered nodes
        const filteredEdges = edges.filter(edge => 
          filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
        );
        
        // Transform data for react-force-graph
        const formattedNodes = filteredNodes.map(node => ({
          id: node.id,
          name: node.name,
          type: node.type,
          val: 10, // All nodes same size for full graph
          color: getNodeColorBySource(node), // Color by source instead of type
          confidence: node.confidence,
          description: node.description,
          source_types: node.source_types || [],
          source_count: node.source_count || 1,
          has_pdf: node.has_pdf,
          has_external: node.has_external
        }));

        const formattedEdges = filteredEdges.map(edge => ({
          source: edge.source,
          target: edge.target,
          type: edge.type,
          label: edge.predicate,
          confidence: edge.confidence
        }));

        setGraphData({
          nodes: formattedNodes,
          links: formattedEdges
        });

        // Center the graph
        setTimeout(() => {
          if (graphRef.current) {
            graphRef.current.zoomToFit(400);
          }
        }, 100);
      } else {
        setError('No graph data available.');
      }
    } catch (err) {
      setError(`Failed to load graph: ${err.message}`);
      console.error('Full graph loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Reload graph when source filter changes
  useEffect(() => {
    if (graphData.nodes.length > 0) {
      loadFullGraph();
    }
  }, [sourceFilter]);

  const handleNodeClick = useCallback(async (node) => {
    // Highlight this node and its connections
    const connectedNodes = new Set();
    const connectedLinks = new Set();
    
    connectedNodes.add(node.id);
    
    graphData.links.forEach(link => {
      if (link.source.id === node.id || link.source === node.id) {
        connectedLinks.add(link);
        connectedNodes.add(typeof link.target === 'object' ? link.target.id : link.target);
      }
      if (link.target.id === node.id || link.target === node.id) {
        connectedLinks.add(link);
        connectedNodes.add(typeof link.source === 'object' ? link.source.id : link.source);
      }
    });
    
    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);
    setSelectedEntity(node.name);
    
    // Clear chat when switching entities
    setChatMessages([]);
    setChatInput('');
    
    // Load entity details for drawer
    setEntityDetails(node);
    setDrawerOpen(true);

    try {
      const detailsResponse = await apiService.getKnowledgeHubEntityDetails(node.id);
      if (detailsResponse.success) {
        setEntityDetails({
          ...node,
          ...detailsResponse.entity
        });
      }
    } catch (err) {
      // Silently ignore - entity details are optional, basic node info is already displayed
      // This is expected for entities that don't have extended metadata
    }
    
    // NEW: Load source documents
    setLoadingSources(true);
    setSourceDocuments([]);
    try {
      const sourcesResponse = await apiService.getEntitySources(node.name);
      if (sourcesResponse.success) {
        setSourceDocuments(sourcesResponse.documents || []);
      }
    } catch (err) {
      // Silently ignore - source documents are optional
    } finally {
      setLoadingSources(false);
    }
  }, [graphData.links]);

  const handleNodeHover = useCallback((node) => {
    setHoverNode(node || null);
  }, []);

  const handleRefresh = () => {
    // Clear highlights
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
    setHoverNode(null);
    
    // Reload full graph
    if (!selectedEntity) {
      loadFullGraph();
    } else {
      setSelectedEntity(null);
      loadFullGraph();
    }
  };

  // NEW: Investigation Board integration functions
  const handleOpenPinDialog = async () => {
    setPinToBoardDialogOpen(true);
    setLoadingBoards(true);
    try {
      const response = await apiService.investigationBoard.getBoards();
      // Backend returns {success: true, boards: [...]}
      setAvailableBoards(response.boards || []);
    } catch (err) {
      console.error('Failed to load boards:', err);
      setAvailableBoards([]);
    } finally {
      setLoadingBoards(false);
    }
  };
  
  const handlePinToBoard = async () => {
    if (!selectedBoard || !entityDetails) return;
    
    setPinning(true);
    try {
      await apiService.investigationBoard.pinEntity({
        board_id: selectedBoard,
        entity_name: entityDetails.name,
        entity_type: entityDetails.type,
        pin_reason: `Pinned from Knowledge Hub - Confidence: ${(entityDetails.confidence * 100).toFixed(0)}%`,
        // Store the entity ID for later retrieval
        knowledge_hub_entity_id: entityDetails.id || entityDetails.name
      });
      
      setPinToBoardDialogOpen(false);
      setSelectedBoard('');
      // Show success message
      setError(null);
      alert('✅ Entity pinned to Investigation Board successfully!');
    } catch (err) {
      console.error('Failed to pin entity:', err);
      alert('❌ Failed to pin entity. Please try again.');
    } finally {
      setPinning(false);
    }
  };
  
  // NEW: Chat functions
  const handleSendMessage = async () => {
    if (!chatInput.trim() || !selectedEntity || chatLoading) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    
    // Add user message to chat
    const newMessages = [...chatMessages, { role: 'user', content: userMessage }];
    setChatMessages(newMessages);
    setChatLoading(true);
    
    try {
      const response = await apiService.chatWithEntity(
        selectedEntity,
        userMessage,
        newMessages.map(msg => ({ role: msg.role, content: msg.content }))
      );
      
      if (response.success) {
        setChatMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: response.response,
            sources: response.sources || []
          }
        ]);
      } else {
        setChatMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${response.error}`,
            sources: []
          }
        ]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your question.',
          sources: []
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.5, 400);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.5, 400);
    }
  };

  const handleCenter = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  // Render statistics cards
  const renderStatisticsCards = () => {
    const statsCards = [
      {
        icon: <HubIcon />,
        value: statistics.total_entities || 0,
        label: 'Total Entities',
        color: '#667eea',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      },
      {
        icon: <TreeIcon />,
        value: statistics.total_relationships || 0,
        label: 'Relationships',
        color: '#10b981',
        gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
      },
      {
        icon: <DrugIcon />,
        value: statistics.node_counts?.Drug || 0,
        label: 'Drugs',
        color: '#f59e0b',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
      },
      {
        icon: <DiseaseIcon />,
        value: statistics.node_counts?.Disease || 0,
        label: 'Diseases',
        color: '#ef4444',
        gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
      },
    ];

    return (
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statsCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              elevation={0}
              sx={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: 3,
                overflow: 'hidden',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.15)'
                }
              }}
            >
              <CardContent sx={{ position: 'relative', overflow: 'hidden' }}>
                <Box 
                  sx={{
                    position: 'absolute',
                    top: -20,
                    right: -20,
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    background: stat.gradient,
                    opacity: 0.1,
                  }}
                />
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: 2,
                      background: stat.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      mb: 2,
                      boxShadow: `0 8px 24px ${stat.color}40`,
                      transition: 'transform 0.3s ease',
                      '&:hover': {
                        transform: 'scale(1.1) rotate(5deg)'
                      }
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Typography 
                    variant="h3" 
                    sx={{ 
                      fontWeight: 700,
                      mb: 0.5,
                      background: stat.gradient,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text'
                    }}
                  >
                    {stat.value.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                    {stat.label}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 4
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 800,
              color: 'white',
              mb: 1,
              textShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
          >
            🌐 Knowledge Hub
          </Typography>
          <Typography 
            variant="h6" 
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              fontWeight: 400
            }}
          >
            Explore your multi-source knowledge graph
          </Typography>
        </Box>

        {/* Statistics Cards */}
        {renderStatisticsCards()}

        {/* Search and Filters */}
        <Card 
          elevation={0}
          sx={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: 3,
            mb: 3,
            p: 3
          }}
        >
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search entities (e.g., COVID-19, vaccine, Naproxen)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: '#667eea' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'white',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: '0 4px 20px rgba(102, 126, 234, 0.15)',
                    },
                    '&.Mui-focused': {
                      boxShadow: '0 4px 20px rgba(102, 126, 234, 0.25)',
                    }
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Filter by Source</InputLabel>
                <Select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  label="Filter by Source"
                  sx={{
                    borderRadius: 2,
                    backgroundColor: 'white',
                  }}
                >
                  <MenuItem value="all">All Sources</MenuItem>
                  <MenuItem value="pdf">📄 PDF Only</MenuItem>
                  <MenuItem value="external">🌐 External Only</MenuItem>
                  <MenuItem value="cross-source">🔗 Cross-Source</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                sx={{
                  py: 1.75,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  fontWeight: 600,
                  textTransform: 'none',
                  fontSize: '1rem',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    boxShadow: '0 12px 32px rgba(102, 126, 234, 0.6)',
                    transform: 'translateY(-2px)'
                  }
                }}
              >
                Search
              </Button>
            </Grid>
          </Grid>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, color: '#333' }}>
                Search Results ({searchResults.length})
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {searchResults.map((entity, idx) => (
                  <Chip
                    key={idx}
                    label={entity.name}
                    onClick={() => loadEntityGraph(entity.name)}
                    sx={{
                      fontWeight: 500,
                      backgroundColor: getNodeColorBySource(entity),
                      color: 'white',
                      '&:hover': {
                        transform: 'scale(1.05)',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                      }
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Card>

        {/* Error Message */}
        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        {/* Graph Container */}
        <Card 
          elevation={0}
          sx={{
            background: `
              radial-gradient(at 0% 0%, rgba(56, 178, 172, 0.08) 0px, transparent 50%),
              radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.08) 0px, transparent 50%),
              radial-gradient(at 100% 100%, rgba(239, 68, 68, 0.08) 0px, transparent 50%),
              radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
              linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%)
            `,
            backdropFilter: 'blur(10px)',
            borderRadius: 3,
            overflow: 'hidden',
            height: '70vh',
            position: 'relative',
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: '0 20px 60px rgba(0,0,0,0.08)'
          }}
        >
          {loading ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2
              }}
            >
              <CircularProgress size={60} sx={{ color: '#667eea' }} />
              <Typography variant="h6" sx={{ color: '#667eea', fontWeight: 600 }}>
                Loading Knowledge Graph...
              </Typography>
            </Box>
          ) : graphData.nodes.length > 0 ? (
            <>
              <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                nodeLabel={node => `
                  <div style="background: rgba(0,0,0,0.85); color: white; padding: 12px; border-radius: 8px; font-family: Arial; max-width: 250px;">
                    <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px; color: ${node.color};">${node.name}</div>
                    <div style="font-size: 12px; margin-bottom: 4px;">Type: ${node.type}</div>
                    <div style="font-size: 12px; margin-bottom: 4px;">Confidence: ${(node.confidence * 100).toFixed(0)}%</div>
                    <div style="font-size: 12px;">Sources: ${node.source_count} document${node.source_count !== 1 ? 's' : ''}</div>
                    ${node.source_types && node.source_types.length > 0 ? `<div style="margin-top: 6px; font-size: 11px; color: #aaa;">${node.source_types.join(', ')}</div>` : ''}
                  </div>
                `}
                nodeVal={node => node.val}
                nodeColor={node => {
                  // Highlight logic
                  if (highlightNodes.size === 0) return node.color;
                  return highlightNodes.has(node.id) ? node.color : '#e5e7eb';
                }}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  // Safety check: skip if node position is invalid
                  if (!node || typeof node.x !== 'number' || typeof node.y !== 'number' || 
                      !isFinite(node.x) || !isFinite(node.y)) {
                    return;
                  }
                  
                  const config = entityConfig[node.type] || entityConfig.Entity;
                  const radius = Math.max(4, (node.val || 5) / globalScale * 3);
                  const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);
                  const isHovered = hoverNode && hoverNode.id === node.id;
                  const isSelected = selectedEntity && selectedEntity.id === node.id;
                  
                  // Save context
                  ctx.save();
                  
                  try {
                    // OUTER GLOW for selected/important nodes
                    if (isSelected || isHovered) {
                      ctx.shadowColor = config.glow;
                      ctx.shadowBlur = isSelected ? 20 : 15;
                    }
                    
                    // GRADIENT FILL (radial gradient for depth)
                    const gradient = ctx.createRadialGradient(
                      node.x - radius * 0.3, 
                      node.y - radius * 0.3, 
                      radius * 0.1,
                      node.x, 
                      node.y, 
                      radius
                    );
                    gradient.addColorStop(0, config.gradient[0]);
                    gradient.addColorStop(1, config.gradient[1]);
                    
                    // Main circle
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                    ctx.fillStyle = isHighlighted ? gradient : '#e5e7eb';
                    ctx.fill();
                    
                    // INNER HIGHLIGHT (3D effect)
                    if (isHighlighted) {
                      const highlightGradient = ctx.createRadialGradient(
                        node.x - radius * 0.4,
                        node.y - radius * 0.4,
                        0,
                        node.x - radius * 0.3,
                        node.y - radius * 0.3,
                        radius * 0.6
                      );
                      highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
                      highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                      
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
                      ctx.fillStyle = highlightGradient;
                      ctx.fill();
                    }
                    
                    // Reset shadow
                    ctx.shadowBlur = 0;
                    
                    // BORDER with state-based styling
                    ctx.strokeStyle = isSelected ? '#ffffff' : 
                                      isHovered ? config.hover : 
                                      isHighlighted ? 'rgba(255, 255, 255, 0.5)' : 
                                      '#d1d5db';
                    ctx.lineWidth = isSelected ? 4/globalScale : 
                                    isHovered ? 3/globalScale : 
                                    2/globalScale;
                    ctx.stroke();
                    
                    // LABEL - Visible for important or hovered nodes
                    const label = node.name;
                    const shouldShowLabel = isSelected || isHovered || 
                                           (node.val > 8 && globalScale >= 1.2);
                    
                    if (shouldShowLabel && isHighlighted) {
                      const fontSize = Math.max(10, 13 / globalScale);
                      ctx.font = `600 ${fontSize}px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'middle';
                      
                      // Label background for readability
                      const textMetrics = ctx.measureText(label);
                      const textWidth = Math.min(textMetrics.width, 150 / globalScale);
                      const padding = 6 / globalScale;
                      const labelY = node.y + radius + fontSize + 4 / globalScale;
                      
                      // Background with rounded corners
                      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
                      ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
                      ctx.shadowBlur = 4;
                      
                      // Rounded rectangle for label background
                      const rectX = node.x - textWidth/2 - padding;
                      const rectY = labelY - fontSize/2 - padding/2;
                      const rectWidth = textWidth + padding * 2;
                      const rectHeight = fontSize + padding;
                      const cornerRadius = padding;
                      
                      ctx.beginPath();
                      ctx.moveTo(rectX + cornerRadius, rectY);
                      ctx.lineTo(rectX + rectWidth - cornerRadius, rectY);
                      ctx.quadraticCurveTo(rectX + rectWidth, rectY, rectX + rectWidth, rectY + cornerRadius);
                      ctx.lineTo(rectX + rectWidth, rectY + rectHeight - cornerRadius);
                      ctx.quadraticCurveTo(rectX + rectWidth, rectY + rectHeight, rectX + rectWidth - cornerRadius, rectY + rectHeight);
                      ctx.lineTo(rectX + cornerRadius, rectY + rectHeight);
                      ctx.quadraticCurveTo(rectX, rectY + rectHeight, rectX, rectY + rectHeight - cornerRadius);
                      ctx.lineTo(rectX, rectY + cornerRadius);
                      ctx.quadraticCurveTo(rectX, rectY, rectX + cornerRadius, rectY);
                      ctx.closePath();
                      ctx.fill();
                      
                      ctx.shadowBlur = 0;
                      
                      // Text
                      ctx.fillStyle = '#1f2937';
                      // Truncate label if too long
                      const truncatedLabel = label.length > 20 ? label.substring(0, 18) + '...' : label;
                      ctx.fillText(truncatedLabel, node.x, labelY);
                    }
                  } catch (e) {
                    // Fallback to simple rendering
                    console.debug('Enhanced rendering failed for node:', node.id, e);
                    ctx.fillStyle = config.color;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
                    ctx.fill();
                  }
                  
                  // Restore context
                  ctx.restore();
                }}
                linkLabel={link => link.label || link.type}
                linkCanvasObjectMode={() => 'after'}
                linkCanvasObject={(link, ctx, globalScale) => {
                  const start = link.source;
                  const end = link.target;
                  
                  if (typeof start !== 'object' || typeof end !== 'object') return;
                  
                  const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(link);
                  const opacity = isHighlighted ? 0.6 : 0.2;
                  
                  // Get source and target node configs
                  const sourceConfig = entityConfig[start.type] || entityConfig.Entity;
                  const targetConfig = entityConfig[end.type] || entityConfig.Entity;
                  
                  // GRADIENT LINK (from source color to target color)
                  const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
                  gradient.addColorStop(0, `${sourceConfig.color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`);
                  gradient.addColorStop(1, `${targetConfig.color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`);
                  
                  ctx.strokeStyle = gradient;
                  ctx.lineWidth = isHighlighted ? 2.5 : 1;
                  ctx.lineCap = 'round';
                  
                  // DASHED for certain relationship types
                  const linkType = (link.label || link.type || '').toUpperCase();
                  if (linkType.includes('RELATED') || linkType.includes('ASSOCIATED')) {
                    ctx.setLineDash([5, 3]);
                  } else {
                    ctx.setLineDash([]);
                  }
                  
                  ctx.beginPath();
                  ctx.moveTo(start.x, start.y);
                  ctx.lineTo(end.x, end.y);
                  ctx.stroke();
                  ctx.setLineDash([]);
                }}
                linkDirectionalParticles={link => (highlightLinks.size === 0 || highlightLinks.has(link)) ? 4 : 0}
                linkDirectionalParticleWidth={4}
                linkDirectionalParticleSpeed={0.008}
                linkDirectionalParticleColor={(link) => {
                  const sourceConfig = entityConfig[link.source?.type] || entityConfig.Entity;
                  return sourceConfig.color;
                }}
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
                backgroundColor="transparent"
                d3VelocityDecay={0.3}
                cooldownTicks={200}
                onEngineStop={() => {
                  if (graphRef.current) {
                    graphRef.current.zoomToFit(400);
                  }
                }}
              />

            {/* Floating Graph Controls */}
            <Box
              sx={{
                position: 'absolute',
                top: 20,
                right: 20,
                display: 'flex',
                flexDirection: 'column',
                gap: 1
              }}
            >
              <IconButton
                onClick={handleRefresh}
                sx={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  '&:hover': {
                    background: 'white',
                    transform: 'scale(1.1)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.15)'
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                <RefreshIcon />
              </IconButton>
              <IconButton
                onClick={handleZoomIn}
                sx={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  '&:hover': {
                    background: 'white',
                    transform: 'scale(1.1)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.15)'
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                <ZoomInIcon />
              </IconButton>
              <IconButton
                onClick={handleZoomOut}
                sx={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  '&:hover': {
                    background: 'white',
                    transform: 'scale(1.1)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.15)'
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                <ZoomOutIcon />
              </IconButton>
              <IconButton
                onClick={handleCenter}
                sx={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  '&:hover': {
                    background: 'white',
                    transform: 'scale(1.1)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.15)'
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                <CenterIcon />
              </IconButton>
            </Box>

            {/* Legend - Source-based Colors */}
            <Paper
              elevation={0}
              sx={{
                position: 'absolute',
                bottom: 20,
                left: 20,
                p: 2.5,
                maxWidth: 280,
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: 2,
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                border: '1px solid rgba(255, 255, 255, 0.3)'
              }}
            >
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, color: '#333' }}>
                Source Types
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Box
                    sx={{
                      width: 18,
                      height: 18,
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)'
                    }}
                  />
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#555' }}>
                    PDF Documents
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Box
                    sx={{
                      width: 18,
                      height: 18,
                      borderRadius: '50%',
                      backgroundColor: '#f97316',
                      boxShadow: '0 2px 8px rgba(249, 115, 22, 0.4)'
                    }}
                  />
                  <Box display="flex" flexDirection="column">
                    <Typography variant="body2" sx={{ fontWeight: 500, color: '#555' }}>
                      External Sources
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#888', fontSize: '0.7rem' }}>
                      (Clinical Trials, FDA)
                    </Typography>
                  </Box>
                </Box>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Box
                    sx={{
                      width: 18,
                      height: 18,
                      borderRadius: '50%',
                      backgroundColor: '#9333ea',
                      boxShadow: '0 2px 8px rgba(147, 51, 234, 0.4)'
                    }}
                  />
                  <Box display="flex" flexDirection="column">
                    <Typography variant="body2" sx={{ fontWeight: 500, color: '#555' }}>
                      Cross-Source
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#888', fontSize: '0.7rem' }}>
                      (Both)
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Paper>
          </>
        ) : !loading && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              flexDirection: 'column',
              gap: 2
            }}
          >
            <HubIcon sx={{ fontSize: 80, color: '#cbd5e1' }} />
            <Typography variant="h6" sx={{ color: '#64748b' }}>
              No Graph Data
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8' }}>
              Search for an entity or load the full graph to get started
            </Typography>
          </Box>
        )}
      </Card>

      {/* Entity Details Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 400, p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Entity Details</Typography>
            <IconButton onClick={() => setDrawerOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>

          {entityDetails && (
            <>
              <Box mb={3}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Name
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {entityDetails.name}
                </Typography>
              </Box>

              <Box mb={3}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Type
                </Typography>
                <Chip
                  label={entityDetails.type}
                  sx={{
                    backgroundColor: getNodeColorBySource(entityDetails),
                    color: 'white',
                    fontWeight: 600
                  }}
                  icon={entityConfig[entityDetails.type]?.icon}
                />
              </Box>

              {entityDetails.description && (
                <Box mb={3}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body2">
                    {entityDetails.description}
                  </Typography>
                </Box>
              )}

              <Box mb={3}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Confidence Score
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <Slider
                    value={entityDetails.confidence * 100}
                    disabled
                    sx={{ flex: 1 }}
                  />
                  <Typography variant="body2">
                    {(entityDetails.confidence * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Box>

              {entityDetails.source_count !== undefined && (
                <Box mb={3}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Source Documents
                  </Typography>
                  <Typography variant="h6" gutterBottom>
                    {entityDetails.source_count} document{entityDetails.source_count !== 1 ? 's' : ''}
                  </Typography>
                  {entityDetails.source_types && entityDetails.source_types.length > 0 && (
                    <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
                      {entityDetails.source_types.map((sourceType, idx) => (
                        <Chip
                          key={idx}
                          label={sourceType === 'pdf' ? 'PDF' : sourceType === 'clinicaltrials' ? 'Clinical Trial' : sourceType === 'fda' ? 'FDA' : sourceType}
                          size="small"
                          sx={{
                            backgroundColor: sourceType === 'pdf' ? '#3b82f6' : '#f97316',
                            color: 'white',
                            fontWeight: 500
                          }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {entityDetails.connection_count !== undefined && (
                <Box mb={3}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Connections
                  </Typography>
                  <Typography variant="h6">
                    {entityDetails.connection_count}
                  </Typography>
                </Box>
              )}

              {/* Pin to Investigation Board */}
              <Box mb={3}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<PinIcon />}
                  onClick={handleOpenPinDialog}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    fontWeight: 600,
                    py: 1.5,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #6a4293 100%)',
                    }
                  }}
                >
                  Pin to Investigation Board
                </Button>
              </Box>

              {/* Source Documents Section */}
              <Box mb={3}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
                  📄 Source Documents ({sourceDocuments.length})
                </Typography>
                
                {loadingSources ? (
                  <Box display="flex" justifyContent="center" p={2}>
                    <CircularProgress size={24} />
                  </Box>
                ) : sourceDocuments.length > 0 ? (
                  <>
                    {sourceDocuments.slice(0, 5).map((doc, idx) => (
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
                        onClick={() => navigate(`/viewer/${doc.doc_id}`)}
                      >
                        <CardContent>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                            <Typography variant="body1" fontWeight={600} sx={{ flex: 1 }}>
                              {doc.title || 'Untitled'}
                            </Typography>
                            <IconButton size="small">
                              <InfoIcon fontSize="small" />
                            </IconButton>
                          </Box>
                          
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
                            <Chip 
                              label={`${(doc.entity_confidence * 100).toFixed(0)}% confidence`}
                              size="small"
                              sx={{
                                fontSize: '0.7rem',
                                height: 20,
                                backgroundColor: doc.entity_confidence > 0.8 ? '#10b981' : '#f59e0b',
                                color: 'white'
                              }}
                            />
                          </Box>
                          
                          {doc.snippets && doc.snippets.length > 0 && (
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{
                                display: 'block',
                                mt: 1,
                                '& mark': {
                                  backgroundColor: '#fef08a',
                                  fontWeight: 600,
                                  padding: '0 2px'
                                }
                              }}
                              dangerouslySetInnerHTML={{ __html: doc.snippets[0] }}
                            />
                          )}
                        </CardContent>
                      </Card>
                    ))}
                    
                    {sourceDocuments.length > 5 && (
                      <Button 
                        variant="outlined" 
                        fullWidth
                        onClick={() => {
                          // TODO: Open modal with all sources
                          console.log('Show all sources:', sourceDocuments);
                        }}
                      >
                        View All {sourceDocuments.length} Documents
                      </Button>
                    )}
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    No source documents found
                  </Typography>
                )}
              </Box>

              {/* NEW: Entity Chat Section */}
              <Box mb={3}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ChatIcon sx={{ fontSize: '1.2rem' }} />
                  Ask Questions About This Entity
                </Typography>
                
                {/* Chat Messages */}
                <Paper 
                  sx={{ 
                    height: 300, 
                    mb: 2, 
                    p: 2, 
                    overflowY: 'auto',
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb'
                  }}
                >
                  {chatMessages.length === 0 ? (
                    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="100%" color="text.secondary">
                      <ChatIcon sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
                      <Typography variant="body2" align="center">
                        Ask questions about {selectedEntity}
                      </Typography>
                      <Typography variant="caption" align="center" sx={{ mt: 1 }}>
                        Example: "What are the side effects?" or "Tell me more about this entity"
                      </Typography>
                    </Box>
                  ) : (
                    <>
                      {chatMessages.map((msg, idx) => (
                        <Box 
                          key={idx}
                          sx={{
                            mb: 2,
                            display: 'flex',
                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                          }}
                        >
                          <Paper
                            elevation={1}
                            sx={{
                              p: 1.5,
                              maxWidth: '80%',
                              backgroundColor: msg.role === 'user' ? '#667eea' : 'white',
                              color: msg.role === 'user' ? 'white' : 'text.primary',
                              borderRadius: 2
                            }}
                          >
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                              {msg.content}
                            </Typography>
                            
                            {/* Show sources for assistant messages */}
                            {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                              <Box mt={1.5} pt={1.5} borderTop="1px solid #e5e7eb">
                                <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" mb={0.5}>
                                  Sources:
                                </Typography>
                                <Box display="flex" flexWrap="wrap" gap={0.5}>
                                  {msg.sources.map((source, sidx) => (
                                    <Chip
                                      key={sidx}
                                      label={`[${source.citation_number}] ${source.title.substring(0, 30)}...`}
                                      size="small"
                                      onClick={() => navigate(`/viewer/${source.doc_id}`)}
                                      sx={{
                                        fontSize: '0.65rem',
                                        height: 20,
                                        cursor: 'pointer',
                                        '&:hover': {
                                          backgroundColor: '#e5e7eb'
                                        }
                                      }}
                                    />
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Paper>
                        </Box>
                      ))}
                      <div ref={chatEndRef} />
                    </>
                  )}
                </Paper>

                {/* Chat Input */}
                <Box display="flex" gap={1}>
                  <TextField
                    fullWidth
                    size="small"
                    placeholder="Type your question..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    disabled={chatLoading}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'white'
                      }
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={!chatInput.trim() || chatLoading}
                    sx={{
                      minWidth: 48,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5568d3 0%, #6a4293 100%)',
                      }
                    }}
                  >
                    {chatLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                  </Button>
                </Box>
              </Box>
            </>
          )}
        </Box>
      </Drawer>

      {/* Pin to Board Dialog */}
      <Dialog open={pinToBoardDialogOpen} onClose={() => setPinToBoardDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <BoardIcon color="primary" />
            <Typography variant="h6">Pin to Investigation Board</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {loadingBoards ? (
            <Box display="flex" justifyContent="center" py={3}>
              <CircularProgress />
            </Box>
          ) : availableBoards.length === 0 ? (
            <Box textAlign="center" py={3}>
              <Typography color="text.secondary" gutterBottom>
                No investigation boards found
              </Typography>
              <Button
                variant="contained"
                startIcon={<BoardIcon />}
                onClick={() => {
                  setPinToBoardDialogOpen(false);
                  navigate('/investigations');
                }}
                sx={{ mt: 2 }}
              >
                Create New Board
              </Button>
            </Box>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Select a board to pin <strong>{entityDetails?.name}</strong>
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Investigation Board</InputLabel>
                <Select
                  value={selectedBoard}
                  onChange={(e) => setSelectedBoard(e.target.value)}
                  label="Investigation Board"
                >
                  {availableBoards.map((board) => (
                    <MenuItem key={board.id} value={board.id}>
                      <Box display="flex" justifyContent="space-between" width="100%">
                        <span>{board.title}</span>
                        <Chip
                          label={`${board.entity_count || 0} entities`}
                          size="small"
                          sx={{ ml: 2 }}
                        />
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setPinToBoardDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handlePinToBoard}
            disabled={!selectedBoard || pinning || loadingBoards}
            startIcon={pinning ? <CircularProgress size={16} /> : <PinIcon />}
          >
            {pinning ? 'Pinning...' : 'Pin Entity'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  </Box>
  );
};

export default KnowledgeHub;
