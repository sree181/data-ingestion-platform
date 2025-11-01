import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import WebGLKnowledgeGraph from '../components/WebGLKnowledgeGraph';
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
  Switch,
  FormControlLabel,
  ToggleButton,
  ToggleButtonGroup,
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
  ViewInAr as View3DIcon,
  ViewQuilt as View2DIcon,
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
  
  // NEW: Rendering mode (2D Canvas vs 3D WebGL)
  const [renderMode, setRenderMode] = useState('3d'); // '2d' or '3d'
  
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

  // PROGRESSIVE DISCLOSURE: State for visible nodes
  const [visibleNodeIds, setVisibleNodeIds] = useState(new Set());
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [showAllNodes, setShowAllNodes] = useState(false);
  
  // SMART FILTERING: State for advanced filters
  const [minConnections, setMinConnections] = useState(0);
  const [minConfidence, setMinConfidence] = useState(0);
  const [domainFilter, setDomainFilter] = useState('all');
  const [importanceFilter, setImportanceFilter] = useState('all');
  
  // COMMUNITY DETECTION: State for clustering
  const [communities, setCommunities] = useState({});
  const [showCommunities, setShowCommunities] = useState(false);
  const [communityColors, setCommunityColors] = useState({});
  
  // EDGE TYPES: State for relationship filtering
  const [relationshipTypes, setRelationshipTypes] = useState([]);
  const [selectedRelationshipTypes, setSelectedRelationshipTypes] = useState([]);
  const [showRelationshipLegend, setShowRelationshipLegend] = useState(true);
  
  // DOCUMENT NODES: State for progressive disclosure of documents
  const [showDocuments, setShowDocuments] = useState(false);

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
    Document: {
      color: '#f472b6', // Pink
      gradient: ['#f472b6', '#ec4899'],
      shadow: 'rgba(244, 114, 182, 0.4)',
      hover: '#f9a8d4',
      glow: 'rgba(244, 114, 182, 0.6)',
      label: 'Documents',
      icon: <EntityIcon /> // Could use a document icon if available
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

  // RELATIONSHIP TYPE CONFIGURATION
  const relationshipConfig = {
    // Treatment & Prevention
    TREATS: {
      category: 'treatment',
      color: '#10b981', // Green
      lineStyle: 'solid',
      lineWidth: 3,
      particleColor: '#10b981',
      label: 'Treats'
    },
    PREVENTS: {
      category: 'treatment',
      color: '#059669', // Dark green
      lineStyle: 'solid',
      lineWidth: 3,
      particleColor: '#059669',
      label: 'Prevents'
    },
    
    // Adverse Events & Causality
    CAUSES: {
      category: 'adverse',
      color: '#ef4444', // Red
      lineStyle: 'dashed',
      dash: [5, 5],
      lineWidth: 2.5,
      particleColor: '#ef4444',
      label: 'Causes'
    },
    ASSOCIATED_WITH: {
      category: 'adverse',
      color: '#f87171', // Light red
      lineStyle: 'dashed',
      dash: [3, 2],
      lineWidth: 2,
      particleColor: '#f87171',
      label: 'Associated With'
    },
    
    // Drug Interactions
    INTERACTS_WITH: {
      category: 'interaction',
      color: '#f59e0b', // Orange
      lineStyle: 'dashed',
      dash: [5, 3],
      lineWidth: 2.5,
      particleColor: '#f59e0b',
      label: 'Interacts With'
    },
    COMBINED_WITH: {
      category: 'interaction',
      color: '#fbbf24', // Yellow
      lineStyle: 'dotted',
      dash: [2, 2],
      lineWidth: 2,
      particleColor: '#fbbf24',
      label: 'Combined With'
    },
    CONTRAINDICATES: {
      category: 'interaction',
      color: '#dc2626', // Dark red
      lineStyle: 'dashed',
      dash: [8, 4],
      lineWidth: 3,
      particleColor: '#dc2626',
      label: 'Contraindicates'
    },
    
    // Research & Authorship
    STUDIED_BY: {
      category: 'research',
      color: '#3b82f6', // Blue
      lineStyle: 'dotted',
      dash: [2, 4],
      lineWidth: 2,
      particleColor: '#3b82f6',
      label: 'Studied By'
    },
    AUTHORED_BY: {
      category: 'research',
      color: '#60a5fa', // Light blue
      lineStyle: 'dotted',
      dash: [2, 3],
      lineWidth: 1.5,
      particleColor: '#60a5fa',
      label: 'Authored By'
    },
    REPORTED_BY: {
      category: 'research',
      color: '#2563eb', // Dark blue
      lineStyle: 'dotted',
      dash: [2, 3],
      lineWidth: 1.5,
      particleColor: '#2563eb',
      label: 'Reported By'
    },
    
    // Manufacturing & Approval
    MANUFACTURED_BY: {
      category: 'regulatory',
      color: '#8b5cf6', // Purple
      lineStyle: 'solid',
      lineWidth: 2,
      particleColor: '#8b5cf6',
      label: 'Manufactured By'
    },
    APPROVED_BY: {
      category: 'regulatory',
      color: '#a78bfa', // Light purple
      lineStyle: 'solid',
      lineWidth: 2,
      particleColor: '#a78bfa',
      label: 'Approved By'
    },
    INVESTIGATED_BY: {
      category: 'regulatory',
      color: '#7c3aed', // Dark purple
      lineStyle: 'dotted',
      dash: [3, 2],
      lineWidth: 2,
      particleColor: '#7c3aed',
      label: 'Investigated By'
    },
    
    // Disease Relationships
    COMORBID_WITH: {
      category: 'disease',
      color: '#ec4899', // Pink
      lineStyle: 'dashed',
      dash: [4, 3],
      lineWidth: 2,
      particleColor: '#ec4899',
      label: 'Comorbid With'
    },
    PROGRESSES_TO: {
      category: 'disease',
      color: '#db2777', // Dark pink
      lineStyle: 'solid',
      lineWidth: 2.5,
      particleColor: '#db2777',
      label: 'Progresses To'
    },
    
    // Medical Procedures
    DIAGNOSED_BY: {
      category: 'procedure',
      color: '#06b6d4', // Cyan
      lineStyle: 'dotted',
      dash: [2, 3],
      lineWidth: 2,
      particleColor: '#06b6d4',
      label: 'Diagnosed By'
    },
    TREATED_WITH: {
      category: 'procedure',
      color: '#0891b2', // Dark cyan
      lineStyle: 'solid',
      lineWidth: 2.5,
      particleColor: '#0891b2',
      label: 'Treated With'
    },
    MONITORED_BY: {
      category: 'procedure',
      color: '#22d3ee', // Light cyan
      lineStyle: 'dotted',
      dash: [2, 2],
      lineWidth: 1.5,
      particleColor: '#22d3ee',
      label: 'Monitored By'
    },
    
    // Generic/Unknown
    RELATED_TO: {
      category: 'generic',
      color: '#9ca3af', // Gray
      lineStyle: 'dashed',
      dash: [3, 2],
      lineWidth: 1.5,
      particleColor: '#9ca3af',
      label: 'Related To'
    },
    CO_OCCURS_WITH: {
      category: 'generic',
      color: '#d1d5db', // Light gray
      lineStyle: 'dotted',
      dash: [2, 2],
      lineWidth: 1,
      particleColor: '#d1d5db',
      label: 'Co-Occurs With'
    },
    MENTIONED_IN: {
      category: 'generic',
      color: '#6b7280', // Medium gray
      lineStyle: 'dotted',
      dash: [1, 2],
      lineWidth: 1,
      particleColor: '#6b7280',
      label: 'Mentioned In'
    },
    
    // Document relationships
    CONTAINS: {
      category: 'document',
      color: '#f472b6', // Pink (matching Document node color)
      lineStyle: 'solid',
      lineWidth: 2,
      particleColor: '#f472b6',
      label: 'Contains'
    },
    HAS_ENTITY: {
      category: 'document',
      color: '#f9a8d4', // Light pink
      lineStyle: 'dotted',
      dash: [3, 2],
      lineWidth: 1.5,
      particleColor: '#f9a8d4',
      label: 'Has Entity'
    }
  };

  // Helper function to get relationship configuration
  const getRelationshipConfig = (relationshipType) => {
    const normalizedType = (relationshipType || 'RELATED_TO').toUpperCase().replace(/\s+/g, '_');
    return relationshipConfig[normalizedType] || relationshipConfig.RELATED_TO;
  };

  // Helper function to get line style array
  const getLineStyle = (relationshipType) => {
    const config = getRelationshipConfig(relationshipType);
    if (config.lineStyle === 'solid') return [];
    if (config.lineStyle === 'dashed') return config.dash || [5, 3];
    if (config.lineStyle === 'dotted') return config.dash || [2, 2];
    return [];
  };

  // Helper function to categorize relationships
  const categorizeRelationship = (relationshipType) => {
    const config = getRelationshipConfig(relationshipType);
    return config.category;
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

  // Keyboard shortcuts for better UX
  useEffect(() => {
    const handleKeyPress = (e) => {
      // ESC to deselect node and close drawer
      if (e.key === 'Escape') {
        setSelectedEntity(null);
        setEntityDetails(null);
        setHighlightNodes(new Set());
        setHighlightLinks(new Set());
        setDrawerOpen(false);
        setSearchResults([]);
        setError(null);
      }
      
      // Ctrl+K or Cmd+K to focus search box
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="Search entities"]');
        if (searchInput) {
          searchInput.focus();
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Load source documents when entity is selected
  useEffect(() => {
    const loadSourceDocuments = async () => {
      if (!entityDetails || !entityDetails.id) {
        setSourceDocuments([]);
        return;
      }

      setLoadingSources(true);
      try {
        // Query for documents containing this entity
        const response = await apiService.getEntitySourceDocuments(entityDetails.id);
        
        if (response && response.documents) {
          setSourceDocuments(response.documents);
          console.log('📄 Source Documents Loaded:', {
            entityId: entityDetails.id,
            entityName: entityDetails.name,
            documentCount: response.documents.length
          });
        } else {
          setSourceDocuments([]);
        }
      } catch (err) {
        console.error('Failed to load source documents:', err);
        // Fallback: try to get documents from relationships
        try {
          const docs = await getDocumentsFromRelationships(entityDetails.id);
          setSourceDocuments(docs);
        } catch (fallbackErr) {
          console.error('Fallback also failed:', fallbackErr);
          setSourceDocuments([]);
        }
      } finally {
        setLoadingSources(false);
      }
    };

    loadSourceDocuments();
  }, [entityDetails]);

  // Fallback: Get documents from Neo4j relationships
  const getDocumentsFromRelationships = async (entityId) => {
    try {
      // This would query Neo4j for Document nodes connected to this entity
      // For now, return empty array as this requires backend API
      return [];
    } catch (err) {
      console.error('Failed to get documents from relationships:', err);
      return [];
    }
  };

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
      // Reset highlight if search is empty
      setHighlightNodes(new Set());
      setSearchResults([]);
      setError(null);
      return;
    }

    const query = searchQuery.toLowerCase();
    
    // DEBUG: Log search details
    console.log('🔍 Search Debug:', {
      query,
      totalGraphNodes: graphData.nodes.length,
      filteredGraphNodes: filteredGraphData.nodes.length,
      sourceFilter,
      sampleNodeNames: filteredGraphData.nodes.slice(0, 5).map(n => n.name)
    });
    
    // Search in FILTERED graph data
    const matchingNodes = filteredGraphData.nodes.filter(node => 
      (node.name || '').toLowerCase().includes(query) ||
      (node.description || '').toLowerCase().includes(query) ||
      (node.id || '').toLowerCase().includes(query)
    );

    console.log('🔍 Search Results:', {
      matchingCount: matchingNodes.length,
      matches: matchingNodes.slice(0, 3).map(n => ({ name: n.name, type: n.type }))
    });

    if (matchingNodes.length === 0) {
      setError(`No entities found matching "${searchQuery}" in current graph`);
      setSearchResults([]);
      setHighlightNodes(new Set());
      return;
    }

    // Highlight matching nodes
    const matchingIds = new Set(matchingNodes.map(n => n.id));
    setHighlightNodes(matchingIds);
    setSearchResults(matchingNodes);
    setError(null);

    // Zoom to first match
    if (matchingNodes.length > 0 && graphRef.current) {
      const firstMatch = matchingNodes[0];
      
      // Wait a bit for the graph to render highlights
      setTimeout(() => {
        if (graphRef.current && firstMatch.x !== undefined && firstMatch.y !== undefined) {
          graphRef.current.centerAt(firstMatch.x, firstMatch.y, 1000);
          graphRef.current.zoom(2, 1000);
        }
        
        // Auto-select if only one match
        if (matchingNodes.length === 1) {
          handleNodeClick(firstMatch);
        }
      }, 100);
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

  // Color by entity type (Drug, Disease, Person, etc.) - ENHANCED
  const getNodeColorBySource = (node) => {
    // Use entity type for color (matching our enhanced color palette)
    const config = entityConfig[node.type] || entityConfig.Entity;
    return config.color;
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
          // Use predicate as the primary type (contains semantic meaning like "TREATS", "CAUSES")
          // Fallback to type (which is usually just "RELATES_TO")
          type: edge.predicate || edge.type,
          label: edge.predicate || edge.type,
          confidence: edge.confidence
        }));

        setGraphData({
          nodes: formattedNodes,
          links: formattedEdges
        });

        // PROGRESSIVE DISCLOSURE: Initialize with top 50 most important nodes
        if (!showAllNodes && formattedNodes.length > 50) {
          // Calculate importance score for each node
          const nodesWithImportance = formattedNodes.map(node => {
            // Count connections
            const connections = formattedEdges.filter(
              edge => edge.source === node.id || edge.target === node.id
            ).length;
            
            // Importance = connections * confidence * source_count
            const importance = connections * (node.confidence || 0.5) * (node.source_count || 1);
            
            return { ...node, connections, importance };
          });
          
          // Sort by importance and take top 50
          const topNodes = nodesWithImportance
            .sort((a, b) => b.importance - a.importance)
            .slice(0, 50);
          
          const topNodeIds = new Set(topNodes.map(n => n.id));
          setVisibleNodeIds(topNodeIds);
          
          console.log('📊 Progressive Disclosure:', {
            totalNodes: formattedNodes.length,
            visibleNodes: topNodes.length,
            topNode: topNodes[0]?.name,
            topImportance: topNodes[0]?.importance?.toFixed(2)
          });
        } else {
          // Show all nodes
          setVisibleNodeIds(new Set(formattedNodes.map(n => n.id)));
        }

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

  // Filtered graph data based on source filter and other filters
  const filteredGraphData = useMemo(() => {
    console.log('🔄 filteredGraphData recalculating...', {
      totalNodes: graphData.nodes.length,
      showAllNodes,
      showDocuments,
      visibleNodeIds: visibleNodeIds.size,
      minConnections,
      minConfidence,
      sourceFilter
    });
    
    let filteredNodes = graphData.nodes;
    
    // 0. Filter out Document nodes unless showDocuments is true
    if (!showDocuments) {
      filteredNodes = filteredNodes.filter(node => node.type !== 'Document');
      console.log(`  → Document filter (hidden):`, filteredNodes.length, 'nodes');
    }
    
    // 1. Apply source filter
    if (sourceFilter !== 'all') {
      filteredNodes = filteredNodes.filter(node => {
        if (sourceFilter === 'pdf') return node.has_pdf;
        if (sourceFilter === 'external') return node.has_external;
        if (sourceFilter === 'cross-source') return node.has_pdf && node.has_external;
        return true;
      });
      console.log(`  → Source filter (${sourceFilter}):`, filteredNodes.length, 'nodes');
    }
    
    // 2. SMART FILTERING: Apply importance filters
    if (minConnections > 0 || minConfidence > 0) {
      filteredNodes = filteredNodes.filter(node => {
        // Calculate connections
        const connections = graphData.links.filter(
          link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return sourceId === node.id || targetId === node.id;
          }
        ).length;
        
        // Filter by minimum connections
        if (connections < minConnections) return false;
        
        // Filter by minimum confidence
        if ((node.confidence || 0) < minConfidence) return false;
        
        return true;
      });
      console.log(`  → Smart filters (conn: ${minConnections}, conf: ${minConfidence}):`, filteredNodes.length, 'nodes');
    }
    
    // 3. PROGRESSIVE DISCLOSURE: Apply visibility filter
    if (!showAllNodes && visibleNodeIds.size > 0) {
      filteredNodes = filteredNodes.filter(node => visibleNodeIds.has(node.id));
      console.log(`  → Progressive disclosure (top 50):`, filteredNodes.length, 'nodes');
    } else if (showAllNodes) {
      console.log(`  → Showing all nodes:`, filteredNodes.length, 'nodes');
    }
    
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    
    // Filter links to only include filtered nodes
    const filteredLinks = graphData.links.filter(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId);
    });
    
    console.log('✅ Final filtered graph:', {
      nodes: filteredNodes.length,
      links: filteredLinks.length
    });
    
    return {
      nodes: filteredNodes,
      links: filteredLinks
    };
  }, [graphData, sourceFilter, minConnections, minConfidence, showAllNodes, showDocuments, visibleNodeIds]);

  // PROGRESSIVE DISCLOSURE: Expand node to show neighbors
  const expandNode = useCallback((nodeId) => {
    // Find all neighbors of this node
    const neighbors = new Set();
    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      
      if (sourceId === nodeId) neighbors.add(targetId);
      if (targetId === nodeId) neighbors.add(sourceId);
    });
    
    // Add neighbors to visible nodes
    setVisibleNodeIds(prev => {
      const newSet = new Set(prev);
      neighbors.forEach(id => newSet.add(id));
      newSet.add(nodeId); // Ensure the node itself is visible
      return newSet;
    });
    
    // Mark this node as expanded
    setExpandedNodes(prev => new Set(prev).add(nodeId));
    
    console.log('🔍 Expanded node:', {
      nodeId,
      neighborsAdded: neighbors.size,
      totalVisible: visibleNodeIds.size + neighbors.size
    });
  }, [graphData.links, visibleNodeIds]);
  
  // PROGRESSIVE DISCLOSURE: Collapse node (hide its unique neighbors)
  const collapseNode = useCallback((nodeId) => {
    // Mark as not expanded
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      newSet.delete(nodeId);
      return newSet;
    });
    
    // Note: We don't remove neighbors as they might be connected to other expanded nodes
    // This is a simplified version - full implementation would track which nodes to hide
  }, []);
  
  // COMMUNITY DETECTION: Enhanced algorithm with edge-type weighting
  const detectCommunities = useCallback(() => {
    console.log('🔍 Starting enhanced community detection with edge weights...');
    
    // Edge weight mapping based on relationship importance
    const edgeWeights = {
      treatment: 1.0,     // TREATS, PREVENTS
      adverse: 0.9,       // CAUSES, ASSOCIATED_WITH
      interaction: 0.8,   // INTERACTS_WITH, COMBINED_WITH
      disease: 0.8,       // COMORBID_WITH, PROGRESSES_TO
      regulatory: 0.7,    // MANUFACTURED_BY, APPROVED_BY
      research: 0.6,      // STUDIED_BY, AUTHORED_BY
      procedure: 0.7,     // DIAGNOSED_BY, TREATED_WITH
      generic: 0.3        // RELATED_TO, CO_OCCURS_WITH
    };
    
    // Build WEIGHTED adjacency list
    const adjacency = {};
    const edgeWeightMap = {};
    
    graphData.nodes.forEach(node => {
      adjacency[node.id] = new Map(); // Map of neighbor -> weight
      edgeWeightMap[node.id] = {};
    });
    
    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      
      // Get relationship category and weight
      const relConfig = getRelationshipConfig(link.type || link.label);
      const weight = edgeWeights[relConfig.category] || 0.5;
      
      // Multiply by confidence if available
      const finalWeight = weight * (link.confidence || 0.8);
      
      if (adjacency[sourceId]) {
        adjacency[sourceId].set(targetId, finalWeight);
      }
      if (adjacency[targetId]) {
        adjacency[targetId].set(sourceId, finalWeight);
      }
      
      // Store for logging
      if (!edgeWeightMap[sourceId][relConfig.category]) {
        edgeWeightMap[sourceId][relConfig.category] = 0;
      }
      edgeWeightMap[sourceId][relConfig.category] += finalWeight;
    });
    
    console.log('  → Edge weights calculated:', {
      totalEdges: graphData.links.length,
      sampleWeights: Object.entries(edgeWeights).slice(0, 3)
    });
    
    // Phase 1: Initial clustering by SEMANTIC SIMILARITY
    // Group nodes by their dominant relationship category
    const semanticGroups = {
      treatment_focused: [],
      adverse_focused: [],
      research_focused: [],
      regulatory_focused: [],
      mixed: []
    };
    
    graphData.nodes.forEach(node => {
      const weights = edgeWeightMap[node.id] || {};
      const categories = Object.keys(weights);
      
      if (categories.length === 0) {
        semanticGroups.mixed.push(node.id);
        return;
      }
      
      // Find dominant category
      const dominant = categories.reduce((a, b) => 
        weights[a] > weights[b] ? a : b
      );
      
      // Classify based on dominant category
      if (dominant === 'treatment' || dominant === 'procedure') {
        semanticGroups.treatment_focused.push(node.id);
      } else if (dominant === 'adverse' || dominant === 'interaction') {
        semanticGroups.adverse_focused.push(node.id);
      } else if (dominant === 'research') {
        semanticGroups.research_focused.push(node.id);
      } else if (dominant === 'regulatory') {
        semanticGroups.regulatory_focused.push(node.id);
      } else {
        semanticGroups.mixed.push(node.id);
      }
    });
    
    console.log('  → Semantic groups:', {
      treatment: semanticGroups.treatment_focused.length,
      adverse: semanticGroups.adverse_focused.length,
      research: semanticGroups.research_focused.length,
      regulatory: semanticGroups.regulatory_focused.length,
      mixed: semanticGroups.mixed.length
    });
    
    // Phase 2: Refine by entity type and connectivity within semantic groups
    const nodeCommunities = {};
    const communityMap = {};
    let communityId = 0;
    
    Object.entries(semanticGroups).forEach(([groupName, nodeIds]) => {
      if (nodeIds.length === 0) return;
      
      // Sub-group by entity type
      const typeGroups = {};
      nodeIds.forEach(nodeId => {
        const node = graphData.nodes.find(n => n.id === nodeId);
        const type = node?.type || 'Unknown';
        if (!typeGroups[type]) {
          typeGroups[type] = [];
        }
        typeGroups[type].push(nodeId);
      });
      
      // For each type group, use weighted connected components
      Object.entries(typeGroups).forEach(([type, nodes]) => {
        if (nodes.length <= 15) {
          // Small group - assign to single community
          nodes.forEach(nodeId => {
            nodeCommunities[nodeId] = communityId;
          });
          communityMap[communityId] = { 
            type, 
            semantic: groupName,
            size: nodes.length 
          };
          communityId++;
        } else {
          // Large group - use weighted connected components
          const visited = new Set();
          
          nodes.forEach(nodeId => {
            if (!visited.has(nodeId)) {
              const component = [];
              const queue = [{ id: nodeId, weight: 1.0 }];
              
              while (queue.length > 0) {
                const { id: current, weight: currentWeight } = queue.shift();
                if (visited.has(current)) continue;
                
                visited.add(current);
                component.push(current);
                
                // Add neighbors with strong connections (weight > 0.5)
                const neighbors = adjacency[current] || new Map();
                neighbors.forEach((weight, neighborId) => {
                  const neighborNode = graphData.nodes.find(n => n.id === neighborId);
                  if (neighborNode && 
                      neighborNode.type === type && 
                      !visited.has(neighborId) &&
                      weight > 0.4) { // Threshold for strong connection
                    queue.push({ id: neighborId, weight });
                  }
                });
              }
              
              // Assign this component to a community
              component.forEach(id => {
                nodeCommunities[id] = communityId;
              });
              communityMap[communityId] = { 
                type, 
                semantic: groupName,
                size: component.length 
              };
              communityId++;
            }
          });
        }
      });
    });
    
    // Phase 3: Generate colors based on semantic groups
    const colors = {};
    const semanticColorPalettes = {
      treatment_focused: ['#10b981', '#14b8a6', '#059669', '#0d9488'],
      adverse_focused: ['#ef4444', '#f97316', '#dc2626', '#ea580c'],
      research_focused: ['#3b82f6', '#8b5cf6', '#2563eb', '#7c3aed'],
      regulatory_focused: ['#a78bfa', '#c084fc', '#8b5cf6', '#a855f7'],
      mixed: ['#6b7280', '#9ca3af', '#4b5563', '#6b7280']
    };
    
    Object.entries(communityMap).forEach(([cid, info]) => {
      const palette = semanticColorPalettes[info.semantic] || semanticColorPalettes.mixed;
      const colorIndex = parseInt(cid) % palette.length;
      colors[cid] = palette[colorIndex];
    });
    
    setCommunities(nodeCommunities);
    setCommunityColors(colors);
    
    console.log('✅ Enhanced community detection complete:', {
      totalCommunities: Object.keys(communityMap).length,
      communityBreakdown: communityMap,
      sampleAssignments: Object.entries(nodeCommunities).slice(0, 5)
    });
    
    return { nodeCommunities, communityMap, colors };
  }, [graphData]);

  const handleNodeClick = useCallback(async (node) => {
    const isDocument = node.type === 'Document';
    console.log('🖱️ Node clicked:', node.name, '| Type:', node.type, '| Connected nodes:', graphData.links.filter(link => 
      (link.source.id === node.id || link.source === node.id) ||
      (link.target.id === node.id || link.target === node.id)
    ).length);
    
    // If clicking the same node, deselect it
    if (selectedEntity && selectedEntity.id === node.id) {
      setSelectedEntity(null);
      setEntityDetails(null);
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
      setDrawerOpen(false);
      return;
    }
    
    // Highlight this node and its connections
    const connectedNodes = new Set();
    const connectedLinks = new Set();
    
    connectedNodes.add(node.id);
    
    // For both entity and document nodes, find all connected nodes
    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      
      if (sourceId === node.id) {
        connectedLinks.add(link);
        connectedNodes.add(targetId);
      }
      if (targetId === node.id) {
        connectedLinks.add(link);
        connectedNodes.add(sourceId);
      }
    });
    
    console.log(`  → Highlighting ${connectedNodes.size} nodes and ${connectedLinks.size} links`);
    console.log(`  → Node type: ${isDocument ? 'Document' : 'Entity'}`);
    
    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);
    setSelectedEntity(node.name);
    
    // PROGRESSIVE DISCLOSURE: Auto-expand node on click (if not showing all)
    if (!showAllNodes && !expandedNodes.has(node.id)) {
      console.log(`  → Expanding node: ${node.name}`);
      expandNode(node.id);
    }
    
    // CENTER CAMERA on clicked node for better visibility
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500);
      // Zoom in a bit to see connections better
      setTimeout(() => {
        if (graphRef.current) {
          const currentZoom = graphRef.current.zoom();
          if (currentZoom < 2) {
            graphRef.current.zoom(2, 500);
          }
        }
      }, 300);
    }
    
    // Clear chat when switching entities/documents
    setChatMessages([]);
    setChatInput('');
    
    // Load details for drawer - Different handling for documents vs entities
    if (isDocument) {
      // For Document nodes, show document metadata
      setEntityDetails({
        ...node,
        type: 'Document',
        name: node.name,
        description: node.description || 'Document in knowledge base',
        confidence: node.confidence || 1.0,
        // Document-specific metadata
        doc_metadata: node.doc_metadata || {},
        classification: node.classification || '',
        source_types: node.source_types || []
      });
      setDrawerOpen(true);
      
      // For documents, don't try to load entity details or source documents
      // Instead, we could load the entities that this document contains
      setLoadingSources(false);
      setSourceDocuments([]);
      
      console.log('  → Document node selected, showing metadata');
    } else {
      // For Entity nodes, load entity details and source documents
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
        console.log('  → Could not load extended entity details (using basic info)');
      }
      
      // Load source documents for entities
      setLoadingSources(true);
      setSourceDocuments([]);
      try {
        const sourcesResponse = await apiService.getEntitySourceDocuments(node.id);
        if (sourcesResponse.success) {
          setSourceDocuments(sourcesResponse.documents || []);
          console.log(`  → Loaded ${sourcesResponse.documents?.length || 0} source documents`);
        }
      } catch (err) {
        // Silently ignore - source documents are optional
        console.log('  → Could not load source documents');
      } finally {
        setLoadingSources(false);
      }
    }
  }, [graphData.links, showAllNodes, expandedNodes, expandNode, selectedEntity]);

  const handleNodeHover = useCallback((node) => {
    setHoverNode(node || null);
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedEntity(null);
    setEntityDetails(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
    setDrawerOpen(false);
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
    // Calculate stats dynamically from FILTERED graph data
    const typeCounts = filteredGraphData.nodes.reduce((acc, node) => {
      const type = node.type || 'Entity';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});
    
    const statsCards = [
      {
        icon: <HubIcon />,
        value: filteredGraphData.nodes.length,
        label: 'Total Entities',
        color: '#667eea',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      },
      {
        icon: <TreeIcon />,
        value: filteredGraphData.links.length,
        label: 'Relationships',
        color: '#10b981',
        gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
      },
      {
        icon: <DrugIcon />,
        value: typeCounts.Drug || 0,
        label: 'Drugs',
        color: '#10b981',
        gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
      },
      {
        icon: <DiseaseIcon />,
        value: typeCounts.Disease || 0,
        label: 'Diseases',
        color: '#ef4444',
        gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
      },
      {
        icon: <PersonIcon />,
        value: typeCounts.Person || 0,
        label: 'People',
        color: '#8b5cf6',
        gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
      },
      {
        icon: <OrgIcon />,
        value: typeCounts.Organization || 0,
        label: 'Organizations',
        color: '#f59e0b',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
      },
    ];

    return (
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {statsCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={index}>
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

        {/* Interactive Graph Instructions */}
        <Alert 
          severity="info" 
          icon={<InfoIcon />}
          sx={{ 
            mb: 3, 
            borderRadius: 2,
            background: 'linear-gradient(135deg, rgba(3, 169, 244, 0.08) 0%, rgba(33, 150, 243, 0.08) 100%)',
            border: '1px solid rgba(3, 169, 244, 0.3)',
            '& .MuiAlert-icon': {
              color: '#03a9f4'
            }
          }}
        >
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, color: '#0277bd' }}>
              🖱️ Interactive Graph Controls
            </Typography>
            <Box component="ul" sx={{ m: 0, pl: 2, '& li': { mb: 0.5, fontSize: '0.875rem' } }}>
              <li><strong>Click</strong> any node to expand and see its connections</li>
              <li><strong>Drag</strong> nodes to reposition them and organize the graph</li>
              <li><strong>Scroll</strong> to zoom in/out (zoom in to see relationship labels)</li>
              <li><strong>Pan</strong> by clicking and dragging the background</li>
              <li><strong>Double-click</strong> background to reset view</li>
            </Box>
          </Box>
        </Alert>

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

          {/* Rendering Mode Toggle */}
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ToggleButtonGroup
              value={renderMode}
              exclusive
              onChange={(e, newMode) => {
                if (newMode !== null) {
                  setRenderMode(newMode);
                }
              }}
              sx={{
                backgroundColor: 'white',
                boxShadow: 1,
                borderRadius: 2,
                '& .MuiToggleButton-root': {
                  py: 1,
                  px: 3,
                  border: 'none',
                  fontWeight: 600,
                  textTransform: 'none',
                  '&.Mui-selected': {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #6a4293 100%)',
                    }
                  }
                }
              }}
            >
              <ToggleButton value="2d">
                <View2DIcon sx={{ mr: 1 }} />
                2D Canvas
              </ToggleButton>
              <ToggleButton value="3d">
                <View3DIcon sx={{ mr: 1 }} />
                3D WebGL
                <Chip 
                  label="PRO" 
                  size="small" 
                  sx={{ 
                    ml: 1, 
                    height: 20, 
                    fontSize: '0.65rem',
                    backgroundColor: renderMode === '3d' ? 'rgba(255,255,255,0.3)' : '#667eea',
                    color: renderMode === '3d' ? 'white' : 'white',
                    fontWeight: 700
                  }} 
                />
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* SMART FILTERING & PROGRESSIVE DISCLOSURE Controls */}
          <Card 
            elevation={0}
            sx={{
              mt: 2,
              p: 2,
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: '#667eea' }}>
              🎯 Advanced Filters
            </Typography>
            <Grid container spacing={2}>
              {/* Progressive Disclosure Toggle */}
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showAllNodes}
                      onChange={(e) => {
                        const newShowAll = e.target.checked;
                        setShowAllNodes(newShowAll);
                        
                        if (newShowAll) {
                          // Show all nodes
                          console.log('🔓 Showing all nodes:', graphData.nodes.length);
                          setVisibleNodeIds(new Set(graphData.nodes.map(n => n.id)));
                        } else {
                          // Reset to top 50 - recalculate importance
                          console.log('🔒 Resetting to top 50 nodes...');
                          
                          const nodesWithImportance = graphData.nodes.map(node => {
                            // Count connections
                            const connections = graphData.links.filter(
                              link => {
                                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                                return sourceId === node.id || targetId === node.id;
                              }
                            ).length;
                            
                            // Importance = connections * confidence * source_count
                            const importance = connections * (node.confidence || 0.5) * (node.source_count || 1);
                            
                            return { ...node, connections, importance };
                          });
                          
                          // Sort by importance and take top 50
                          const topNodes = nodesWithImportance
                            .sort((a, b) => b.importance - a.importance)
                            .slice(0, 50);
                          
                          const topNodeIds = new Set(topNodes.map(n => n.id));
                          setVisibleNodeIds(topNodeIds);
                          
                          console.log('✅ Top 50 calculated:', {
                            totalNodes: graphData.nodes.length,
                            visibleNodes: topNodes.length,
                            topNode: topNodes[0]?.name
                          });
                        }
                      }}
                      color="primary"
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Show All Nodes
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {showAllNodes ? `Showing ${graphData.nodes.length} nodes` : `Showing top ${Math.min(50, visibleNodeIds.size)} nodes`}
                      </Typography>
                    </Box>
                  }
                />
              </Grid>

              {/* Community Detection Toggle */}
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showCommunities}
                      onChange={(e) => {
                        const enabled = e.target.checked;
                        setShowCommunities(enabled);
                        if (enabled && Object.keys(communities).length === 0) {
                          // Run community detection if not already done
                          detectCommunities();
                        }
                      }}
                      color="secondary"
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Show Communities
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {showCommunities ? `${Object.keys(communityColors).length} clusters` : 'Color by entity type'}
                      </Typography>
                    </Box>
                  }
                />
              </Grid>

              {/* Show Documents Toggle */}
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showDocuments}
                      onChange={(e) => setShowDocuments(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Show Documents
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {showDocuments ? `Documents visible` : 'Only entities'}
                      </Typography>
                    </Box>
                  }
                />
              </Grid>

              {/* Min Connections Slider */}
              <Grid item xs={12} md={4}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Min Connections: {minConnections}
                </Typography>
                <Slider
                  value={minConnections}
                  onChange={(e, newValue) => {
                    console.log('🔗 Min Connections changed:', newValue);
                    setMinConnections(newValue);
                  }}
                  min={0}
                  max={20}
                  step={1}
                  marks={[
                    { value: 0, label: '0' },
                    { value: 10, label: '10' },
                    { value: 20, label: '20' }
                  ]}
                  sx={{
                    color: '#667eea',
                    '& .MuiSlider-thumb': {
                      backgroundColor: '#667eea',
                    }
                  }}
                />
              </Grid>

              {/* Min Confidence Slider */}
              <Grid item xs={12} md={4}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Min Confidence: {(minConfidence * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={minConfidence}
                  onChange={(e, newValue) => {
                    console.log('✅ Min Confidence changed:', newValue);
                    setMinConfidence(newValue);
                  }}
                  min={0}
                  max={1}
                  step={0.1}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 0.5, label: '50%' },
                    { value: 1, label: '100%' }
                  ]}
                  sx={{
                    color: '#764ba2',
                    '& .MuiSlider-thumb': {
                      backgroundColor: '#764ba2',
                    }
                  }}
                />
              </Grid>

              {/* Reset Filters Button */}
              <Grid item xs={12} md={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => {
                    console.log('🔄 Resetting all filters...');
                    setMinConnections(0);
                    setMinConfidence(0);
                    setShowCommunities(false);
                    setSourceFilter('all');
                    setShowAllNodes(false);
                    
                    // Recalculate top 50 nodes
                    const nodesWithImportance = graphData.nodes.map(node => {
                      const connections = graphData.links.filter(
                        link => {
                          const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                          const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                          return sourceId === node.id || targetId === node.id;
                        }
                      ).length;
                      const importance = connections * (node.confidence || 0.5) * (node.source_count || 1);
                      return { ...node, connections, importance };
                    });
                    
                    const topNodes = nodesWithImportance
                      .sort((a, b) => b.importance - a.importance)
                      .slice(0, 50);
                    
                    setVisibleNodeIds(new Set(topNodes.map(n => n.id)));
                    console.log('✅ Filters reset, showing top 50 nodes');
                  }}
                  sx={{
                    mt: 2,
                    borderRadius: 2,
                    textTransform: 'none',
                    borderColor: '#667eea',
                    color: '#667eea',
                    '&:hover': {
                      borderColor: '#764ba2',
                      backgroundColor: 'rgba(102, 126, 234, 0.05)'
                    }
                  }}
                >
                  Reset All Filters
                </Button>
              </Grid>
            </Grid>

            {/* Filter Statistics */}
            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip 
                label={`Total: ${graphData.nodes.length} nodes`} 
                size="small"
                sx={{ backgroundColor: 'rgba(102, 126, 234, 0.1)', color: '#667eea' }}
              />
              <Chip 
                label={`Visible: ${filteredGraphData.nodes.length} nodes`} 
                size="small"
                sx={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}
              />
              <Chip 
                label={`Expanded: ${expandedNodes.size} nodes`} 
                size="small"
                sx={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}
              />
            </Box>
          </Card>

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
              {renderMode === '3d' ? (
                <WebGLKnowledgeGraph
                  graphData={filteredGraphData}
                  onNodeClick={handleNodeClick}
                  onNodeHover={(node) => setHoverNode(node)}
                  highlightNodes={highlightNodes}
                  highlightLinks={highlightLinks}
                  selectedEntity={selectedEntity}
                  entityConfig={entityConfig}
                  width="100%"
                  height="70vh"
                />
              ) : (
                <ForceGraph2D
                  ref={graphRef}
                  graphData={filteredGraphData}
                nodeLabel={node => `
                  <div style="background: rgba(0,0,0,0.85); color: white; padding: 12px; border-radius: 8px; font-family: Arial; max-width: 250px;">
                    <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px; color: ${node.color};">${node.name}</div>
                    <div style="font-size: 12px; margin-bottom: 4px;">Type: ${node.type}</div>
                    <div style="font-size: 12px; margin-bottom: 4px;">Confidence: ${(node.confidence * 100).toFixed(0)}%</div>
                    <div style="font-size: 12px;">Sources: ${node.source_count} document${node.source_count !== 1 ? 's' : ''}</div>
                    ${node.source_types && node.source_types.length > 0 ? `<div style="margin-top: 6px; font-size: 11px; color: #aaa;">${node.source_types.join(', ')}</div>` : ''}
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 11px; opacity: 0.8;">
                      💡 <strong>Click</strong> to expand connections<br/>
                      🖱️ <strong>Drag</strong> to reposition
                    </div>
                  </div>
                `}
                nodeVal={node => node.val}
                nodeColor={node => {
                  // COMMUNITY DETECTION: Color by community if enabled
                  if (showCommunities && communities[node.id] !== undefined) {
                    const communityId = communities[node.id];
                    const communityColor = communityColors[communityId] || node.color;
                    // Apply highlight logic
                    if (highlightNodes.size === 0) return communityColor;
                    return highlightNodes.has(node.id) ? communityColor : '#e5e7eb';
                  }
                  
                  // Default: Highlight logic
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
                    
                    // LABEL - Only show for selected or hovered nodes (prevents clutter)
                    const label = node.name;
                    const shouldShowLabel = isSelected || isHovered;
                    
                    if (shouldShowLabel && isHighlighted) {
                      const fontSize = Math.max(12, 14 / globalScale);
                      ctx.font = `600 ${fontSize}px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'middle';
                      
                      // Label background for readability
                      const textMetrics = ctx.measureText(label);
                      const textWidth = Math.min(textMetrics.width, 150 / globalScale);
                      const padding = 6 / globalScale;
                      const labelY = node.y + radius + fontSize + 4 / globalScale;
                      
                      // Background with rounded corners
                      ctx.fillStyle = 'rgba(255, 255, 255, 0.98)';
                      ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
                      ctx.shadowBlur = 6;
                      
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
                      
                      // Text with node type color
                      ctx.fillStyle = config.color;
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
                linkLabel={link => {
                  const config = getRelationshipConfig(link.type || link.label);
                  return config.label || link.label || link.type;
                }}
                linkCanvasObjectMode={() => 'after'}
                linkCanvasObject={(link, ctx, globalScale) => {
                  const start = link.source;
                  const end = link.target;
                  
                  if (typeof start !== 'object' || typeof end !== 'object') return;
                  
                  // Save context
                  ctx.save();
                  
                  try {
                    // Get relationship configuration
                    const relConfig = getRelationshipConfig(link.type || link.label);
                    
                    // Check if this link is highlighted
                    const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(link);
                    
                    // Check if this relationship type is selected (if filter is active)
                    const isFiltered = selectedRelationshipTypes.length > 0;
                    const isSelected = !isFiltered || selectedRelationshipTypes.includes(relConfig.category);
                    
                    if (!isSelected) return; // Skip rendering if filtered out
                    
                    // Calculate line metrics
                    const dx = end.x - start.x;
                    const dy = end.y - start.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    // Calculate opacity and width based on state - SOFTER, MORE AESTHETIC
                    const baseOpacity = isHighlighted ? 0.45 : 0.08; // Reduced from 0.85 to 0.45
                    const lineWidth = isHighlighted ? relConfig.lineWidth * 1.2 : relConfig.lineWidth * 0.5; // Reduced from 1.8 to 1.2
                    
                    // AESTHETIC: Subtle shadow for depth (not too harsh)
                    if (isHighlighted && globalScale > 1.5) {
                      ctx.shadowColor = 'rgba(0, 0, 0, 0.1)'; // Soft black shadow instead of colored
                      ctx.shadowBlur = 8 / globalScale; // Reduced from 15 to 8
                      ctx.shadowOffsetX = 1 / globalScale; // Reduced from 2 to 1
                      ctx.shadowOffsetY = 1 / globalScale;
                    }
                    
                    // AESTHETIC: Soft, muted gradient (relationship color only, no entity colors)
                    const sourceNode = typeof link.source === 'object' ? link.source : graphData.nodes.find(n => n.id === link.source);
                    const targetNode = typeof link.target === 'object' ? link.target : graphData.nodes.find(n => n.id === link.target);
                    
                    if (isHighlighted && sourceNode && targetNode) {
                      // Create subtle gradient using only relationship color (muted tones)
                      const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
                      
                      // Use relationship color with varying opacity for smooth gradient
                      const hexOpacity1 = Math.round(baseOpacity * 0.6 * 255).toString(16).padStart(2, '0'); // Lighter at start
                      const hexOpacity2 = Math.round(baseOpacity * 255).toString(16).padStart(2, '0'); // Full in middle
                      const hexOpacity3 = Math.round(baseOpacity * 0.6 * 255).toString(16).padStart(2, '0'); // Lighter at end
                      
                      gradient.addColorStop(0, `${relConfig.color}${hexOpacity1}`);
                      gradient.addColorStop(0.5, `${relConfig.color}${hexOpacity2}`);
                      gradient.addColorStop(1, `${relConfig.color}${hexOpacity3}`);
                      
                      ctx.strokeStyle = gradient;
                    } else {
                      // Use solid color for non-highlighted links
                      const hexOpacity = Math.round(baseOpacity * 255).toString(16).padStart(2, '0');
                      ctx.strokeStyle = `${relConfig.color}${hexOpacity}`;
                    }
                    
                    ctx.lineWidth = lineWidth;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    
                    // Set dash pattern based on relationship type
                    const dashPattern = getLineStyle(link.type || link.label);
                    if (dashPattern.length > 0) {
                      const scaledDash = dashPattern.map(d => d / globalScale);
                      ctx.setLineDash(scaledDash);
                    }
                    
                    // ENHANCED: Draw main line
                    ctx.beginPath();
                    ctx.moveTo(start.x, start.y);
                    ctx.lineTo(end.x, end.y);
                    ctx.stroke();
                    
                    // Reset shadow
                    ctx.shadowBlur = 0;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    
                    // AESTHETIC: Subtle directional arrow (smaller, softer)
                    if (isHighlighted && distance > 40 && globalScale > 1.2) {
                      ctx.setLineDash([]); // Reset dash for arrow
                      
                      const arrowLength = Math.min(10 / globalScale, distance * 0.1); // Smaller arrow (10 instead of 15)
                      
                      // Calculate arrow position (slightly before the target node)
                      const nodeRadius = (targetNode?.val || 5) / globalScale * 3;
                      const arrowOffset = nodeRadius + arrowLength * 0.5;
                      const arrowPos = {
                        x: end.x - (dx / distance) * arrowOffset,
                        y: end.y - (dy / distance) * arrowOffset
                      };
                      
                      // Calculate arrow angle
                      const angle = Math.atan2(dy, dx);
                      
                      // Draw subtle arrow with reduced opacity
                      const arrowOpacity = Math.round(baseOpacity * 0.8 * 255).toString(16).padStart(2, '0');
                      ctx.fillStyle = `${relConfig.color}${arrowOpacity}`;
                      ctx.beginPath();
                      ctx.moveTo(arrowPos.x, arrowPos.y);
                      ctx.lineTo(
                        arrowPos.x - arrowLength * Math.cos(angle - Math.PI / 7), // Narrower angle
                        arrowPos.y - arrowLength * Math.sin(angle - Math.PI / 7)
                      );
                      ctx.lineTo(
                        arrowPos.x - arrowLength * Math.cos(angle + Math.PI / 7), // Narrower angle
                        arrowPos.y - arrowLength * Math.sin(angle + Math.PI / 7)
                      );
                      ctx.closePath();
                      ctx.fill();
                    }
                    
                    // ENHANCED: Draw label with improved styling
                    if (globalScale > 1.8 && isHighlighted && distance > 40) {
                      const midX = (start.x + end.x) / 2;
                      const midY = (start.y + end.y) / 2;
                      
                      const label = relConfig.label;
                      const fontSize = Math.max(10, 12 / globalScale);
                      ctx.font = `600 ${fontSize}px "Inter", -apple-system, BlinkMacSystemFont, sans-serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'middle';
                      
                      const textMetrics = ctx.measureText(label);
                      const textWidth = textMetrics.width;
                      const padding = 6 / globalScale;
                      const cornerRadius = 4 / globalScale;
                      
                      // Calculate label rotation (align with link)
                      const labelAngle = Math.atan2(dy, dx);
                      const shouldFlip = Math.abs(labelAngle) > Math.PI / 2;
                      const finalAngle = shouldFlip ? labelAngle + Math.PI : labelAngle;
                      
                      // Save context for rotation
                      ctx.save();
                      ctx.translate(midX, midY);
                      ctx.rotate(finalAngle);
                      
                      // Draw rounded rectangle background
                      const rectX = -textWidth / 2 - padding;
                      const rectY = -fontSize / 2 - padding / 2;
                      const rectWidth = textWidth + padding * 2;
                      const rectHeight = fontSize + padding;
                      
                      // Background with shadow
                      ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
                      ctx.shadowBlur = 8;
                      ctx.fillStyle = 'rgba(255, 255, 255, 0.98)';
                      
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
                      
                      // Border
                      ctx.shadowBlur = 0;
                      ctx.strokeStyle = relConfig.color;
                      ctx.lineWidth = 1.5 / globalScale;
                      ctx.stroke();
                      
                      // Text
                      ctx.fillStyle = relConfig.color;
                      ctx.shadowBlur = 0;
                      ctx.fillText(label, 0, 0);
                      
                      ctx.restore(); // Restore rotation
                    }
                    
                  } catch (e) {
                    console.debug('Enhanced link rendering failed:', e);
                  }
                  
                  // Reset context
                  ctx.setLineDash([]);
                  ctx.restore();
                }}
                linkDirectionalParticles={link => (highlightLinks.size === 0 || highlightLinks.has(link)) ? 2 : 0}
                linkDirectionalParticleWidth={2.5}
                linkDirectionalParticleSpeed={0.006}
                linkDirectionalParticleColor={(link) => {
                  const relConfig = getRelationshipConfig(link.type || link.label);
                  return relConfig.particleColor;
                }}
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
                onBackgroundClick={handleBackgroundClick}
                backgroundColor="transparent"
                enableNodeDrag={true}
                enableZoomInteraction={true}
                enablePanInteraction={true}
                d3AlphaDecay={0.02}
                d3VelocityDecay={0.3}
                cooldownTicks={100}
                warmupTicks={50}
                d3Force={{
                  charge: { strength: -200, distanceMax: 300 },
                  link: { distance: 50, iterations: 2 },
                  center: null,
                  collide: { radius: 20, strength: 0.8, iterations: 2 }
                }}
                onEngineStop={() => {
                  if (graphRef.current) {
                    graphRef.current.zoomToFit(400);
                  }
                }}
              />
              )}

            {/* Floating Graph Controls - Only show for 2D mode */}
            {renderMode === '2d' && (
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
            )}

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
