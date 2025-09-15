import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardHeader,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Divider,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  ButtonGroup,
  Alert,
  LinearProgress,
  Tooltip,
  Fade,
  Slide,
  Avatar,
  Badge,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  Stack,
  useTheme,
  alpha,
  Drawer,
  AppBar,
  Toolbar,
  Menu,
  Popover
} from '@mui/material';
import {
  Search as SearchIcon,
  AccountTree as NetworkIcon,
  Timeline as TimelineIcon,
  Description as DocumentIcon,
  Analytics as AnalyticsIcon,
  Person as PersonIcon,
  Business as OrganizationIcon,
  Event as EventIcon,
  Policy as RegulationIcon,
  DateRange as DateIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ExploreIcon,
  Share as ShareIcon,
  Bookmark as BookmarkIcon,
  FilterList as FilterIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Speed as SpeedIcon,
  PushPin as PinIcon,
  Close as CloseIcon,
  OpenInNew as OpenInNewIcon,
  TrendingUp as TrendingUpIcon,
  Hub as HubIcon,
  Launch as LaunchIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Menu as MenuIcon,
  Layers as LayersIcon,
  ScatterPlot as NodesIcon,
  Timeline as ConnectionsIcon,
  Straighten as PathIcon,
  CropFree as FocusIcon,
  ColorLens as ThemeIcon,
  Tune as TuneIcon,
  Save as SaveIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import ForceGraph2D from 'react-force-graph-2d';
import { format, subMonths, parseISO, isValid } from 'date-fns';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import apiService from '../services/api';
import ImageGallery from '../components/ImageGallery';

// Tab Panel Component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`investigation-tabpanel-${index}`}
      aria-labelledby={`investigation-tab-${index}`}
      {...other}
      style={{ height: '100%', overflow: 'hidden' }}
    >
      {value === index && (
        <Box sx={{ height: '100%', overflow: 'hidden' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Enhanced Search Panel Component
function SearchPanel({ onSearch, onFilterChange, isSearching }) {
  const theme = useTheme();
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    entityTypes: [],
    confidenceThreshold: 70,
    relationshipDepth: 2,
    showConnections: true,
    minConnections: 1,
    maxNodes: 100
  });

  const entityTypes = [
    { value: 'PERSON', label: 'People', icon: PersonIcon, color: '#FF6B6B' },
    { value: 'ORGANIZATION', label: 'Organizations', icon: OrganizationIcon, color: '#4ECDC4' },
    { value: 'EVENT', label: 'Events', icon: EventIcon, color: '#45B7D1' },
    { value: 'REGULATION', label: 'Regulations', icon: RegulationIcon, color: '#96CEB4' },
    { value: 'DATE', label: 'Dates', icon: DateIcon, color: '#FFEAA7' },
    { value: 'CONCEPT', label: 'Concepts', icon: ExploreIcon, color: '#DDA0DD' },
    { value: 'LOCATION', label: 'Locations', icon: DateIcon, color: '#98D8C8' }
  ];

  const handleSearch = useCallback(() => {
    if (onSearch) {
      onSearch(query, filters);
    }
    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [query, filters, onSearch, onFilterChange]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Modern Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          p: 3,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Advanced Search Panel
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9 }}>
          Configure search parameters and filters
        </Typography>
      </Box>

      <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
        {/* Enhanced Search Input */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <TextField
              fullWidth
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search entities, documents, or concepts..."
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: query && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setQuery('')}>
                      <CloseIcon />
                    </IconButton>
                  </InputAdornment>
                )
              }}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ mb: 2 }}
            />
            
            {isSearching && (
              <Box>
                <LinearProgress sx={{ mb: 1 }} />
                <Typography variant="caption" color="primary">
                  Analyzing relationships...
                </Typography>
              </Box>
            )}

            {/* Quick Search Chips */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {['COVID-19', 'Vaccine', 'Clinical Trial'].map((term) => (
                <Chip
                  key={term}
                  label={term}
                  size="small"
                  onClick={() => setQuery(term)}
                  sx={{ 
                    background: alpha(theme.palette.primary.main, 0.1),
                    '&:hover': { background: alpha(theme.palette.primary.main, 0.2) }
                  }}
                />
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Entity Types Filter */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Badge badgeContent={filters.entityTypes.length} color="primary">
                <FilterIcon />
              </Badge>
              <Typography variant="subtitle2" fontWeight={600}>
                Entity Types
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {entityTypes.map((type) => {
                const isSelected = filters.entityTypes.includes(type.value);
                const IconComponent = type.icon;
                return (
                  <Chip
                    key={type.value}
                    icon={<IconComponent />}
                    label={type.label}
                    onClick={() => {
                      const newTypes = isSelected
                        ? filters.entityTypes.filter(t => t !== type.value)
                        : [...filters.entityTypes, type.value];
                      setFilters(prev => ({ ...prev, entityTypes: newTypes }));
                    }}
                    variant={isSelected ? "filled" : "outlined"}
                    sx={{
                      backgroundColor: isSelected ? type.color : 'transparent',
                      color: isSelected ? 'white' : type.color,
                      borderColor: type.color,
                      '&:hover': {
                        backgroundColor: alpha(type.color, 0.1)
                      }
                    }}
                  />
                );
              })}
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Confidence & Depth */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2" fontWeight={600}>
              Confidence & Depth
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={3}>
              <Box>
                <Typography variant="body2" gutterBottom>
                  Confidence Threshold: {filters.confidenceThreshold}%
                </Typography>
                <Slider
                  value={filters.confidenceThreshold}
                  onChange={(e, value) => setFilters(prev => ({ ...prev, confidenceThreshold: value }))}
                  min={0}
                  max={100}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 50, label: '50%' },
                    { value: 100, label: '100%' }
                  ]}
                />
              </Box>
              <Box>
                <Typography variant="body2" gutterBottom>
                  Relationship Depth: {filters.relationshipDepth} hops
                </Typography>
                <Slider
                  value={filters.relationshipDepth}
                  onChange={(e, value) => setFilters(prev => ({ ...prev, relationshipDepth: value }))}
                  min={1}
                  max={5}
                  marks
                />
              </Box>
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* Advanced Options */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle2" fontWeight={600}>
              Advanced Options
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={filters.showConnections}
                    onChange={(e) => setFilters(prev => ({ ...prev, showConnections: e.target.checked }))}
                  />
                }
                label="Show Connections"
              />
              <Box>
                <Typography variant="body2" gutterBottom>
                  Max Nodes: {filters.maxNodes}
                </Typography>
                <Slider
                  value={filters.maxNodes}
                  onChange={(e, value) => setFilters(prev => ({ ...prev, maxNodes: value }))}
                  min={50}
                  max={500}
                  step={50}
                  marks={[
                    { value: 50, label: '50' },
                    { value: 250, label: '250' },
                    { value: 500, label: '500' }
                  ]}
                />
              </Box>
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* Action Buttons */}
        <Stack spacing={2} sx={{ mt: 3 }}>
          <Button
            variant="contained"
            fullWidth
            onClick={handleSearch}
            disabled={isSearching}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              py: 1.5,
              fontWeight: 600
            }}
            startIcon={<SearchIcon />}
          >
            Run Investigation
          </Button>
          <Button
            variant="outlined"
            fullWidth
            onClick={() => {
              setQuery('');
              setFilters({
                entityTypes: [],
                confidenceThreshold: 70,
                relationshipDepth: 2,
                showConnections: true,
                minConnections: 1,
                maxNodes: 100
              });
            }}
            startIcon={<RefreshIcon />}
          >
            Clear Filters
          </Button>
        </Stack>

        {/* Quick Presets */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Quick Presets:
          </Typography>
          <ButtonGroup size="small" variant="outlined" fullWidth>
            <Button onClick={() => setFilters(prev => ({ ...prev, entityTypes: ['PERSON', 'ORGANIZATION'] }))}>
              People & Orgs
            </Button>
            <Button onClick={() => setFilters(prev => ({ ...prev, entityTypes: ['EVENT', 'DATE'] }))}>
              Timeline
            </Button>
            <Button onClick={() => setFilters(prev => ({ ...prev, confidenceThreshold: 90 }))}>
              High Confidence
            </Button>
          </ButtonGroup>
        </Box>
      </Box>
    </Box>
  );
}

// Enhanced Network View Component
function NetworkView({ 
  data, 
  onEntityClick, 
  onEntityHover, 
  filters, 
  graphMode, 
  showNodeLabels, 
  selectedNodes, 
  highlightMode,
  graphRef,
  fullscreen 
}) {
  const theme = useTheme();
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isPaused, setIsPaused] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [setGraphRef] = useState(null);

  const getEntityColor = useCallback((type) => {
    const colors = {
      'PERSON': '#FF6B6B',
      'ORGANIZATION': '#4ECDC4',
      'EVENT': '#45B7D1',
      'REGULATION': '#96CEB4',
      'DATE': '#FFEAA7',
      'CONCEPT': '#DDA0DD',
      'LOCATION': '#98D8C8',
      'DOCUMENT': '#4CAF50'
    };
    return colors[type] || '#B0B0B0';
  }, []);

  // Enhanced node canvas rendering
  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;
    const size = node.size || 6;
    
    // Determine if node is selected or hovered
    const isSelected = selectedNodes.some(n => n.id === node.id);
    const isHovered = hoveredNode === node;
    
    // Dynamic size based on selection state
    const nodeRadius = isSelected ? size * 1.5 : isHovered ? size * 1.2 : size;
    
    // Node color
    const baseColor = getEntityColor(node.type);
    const nodeColor = isSelected ? '#ff6b6b' : isHovered ? '#4ecdc4' : baseColor;
    
    // Draw glow effect for high confidence nodes
    if (node.confidence && node.confidence > 0.8) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeRadius + 3, 0, 2 * Math.PI);
      ctx.fillStyle = alpha(nodeColor, 0.3);
      ctx.fill();
    }
    
    // Draw main node
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColor;
    ctx.fill();
    
    // Add inner highlight for selection
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeRadius - 2, 0, 2 * Math.PI);
      ctx.fillStyle = alpha('#fff', 0.6);
      ctx.fill();
      
      // Animated selection pulse
      const pulseRadius = nodeRadius + Math.sin(Date.now() * 0.005) * 2;
      ctx.beginPath();
      ctx.arc(node.x, node.y, pulseRadius, 0, 2 * Math.PI);
      ctx.strokeStyle = alpha('#ff6b6b', 0.5);
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    
    // Draw labels if enabled
    if (showNodeLabels && globalScale > 0.5) {
      const maxLabelLength = 15;
      const displayLabel = label.length > maxLabelLength ? 
        label.substring(0, maxLabelLength) + '...' : label;
      
      ctx.font = `${fontSize}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Label background
      const textMetrics = ctx.measureText(displayLabel);
      const bgWidth = textMetrics.width + 6;
      const bgHeight = fontSize + 4;
      
      ctx.fillStyle = alpha('#fff', 0.9);
      ctx.fillRect(
        node.x - bgWidth / 2, 
        node.y + nodeRadius + 5, 
        bgWidth, 
        bgHeight
      );
      
      // Label border
      ctx.strokeStyle = alpha('#000', 0.2);
      ctx.lineWidth = 1;
      ctx.strokeRect(
        node.x - bgWidth / 2, 
        node.y + nodeRadius + 5, 
        bgWidth, 
        bgHeight
      );
      
      // Label text
      ctx.fillStyle = '#333';
      ctx.fillText(displayLabel, node.x, node.y + nodeRadius + 5 + bgHeight / 2);
    }
  }, [getEntityColor, showNodeLabels, selectedNodes, hoveredNode]);

  // Enhanced link canvas rendering
  const linkCanvasObject = useCallback((link, ctx) => {
    const start = link.source;
    const end = link.target;
    
    if (typeof start !== 'object' || typeof end !== 'object') return;
    
    // Link styling based on weight and filters
    const opacity = link.weight ? link.weight * 0.8 + 0.2 : 0.6;
    const lineWidth = link.weight ? link.weight * 3 + 1 : 2;
    
    // Gradient color
    const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
    gradient.addColorStop(0, alpha(getEntityColor(start.type), opacity));
    gradient.addColorStop(1, alpha(getEntityColor(end.type), opacity));
    
    // Draw link
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
    
    // Draw arrowhead for directed links
    if (link.directed) {
      const headlen = 8;
      const angle = Math.atan2(end.y - start.y, end.x - start.x);
      
      ctx.beginPath();
      ctx.moveTo(end.x, end.y);
      ctx.lineTo(end.x - headlen * Math.cos(angle - Math.PI / 6), end.y - headlen * Math.sin(angle - Math.PI / 6));
      ctx.moveTo(end.x, end.y);
      ctx.lineTo(end.x - headlen * Math.cos(angle + Math.PI / 6), end.y - headlen * Math.sin(angle + Math.PI / 6));
      ctx.strokeStyle = alpha('#333', opacity);
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [getEntityColor]);

  // Filter graph data based on current filters
  const filteredGraphData = useMemo(() => {
    if (!data || !data.nodes) return { nodes: [], links: [] };
    
    let filteredNodes = data.nodes;
    let filteredLinks = data.links || [];
    
    // Apply entity type filter
    if (filters.entityTypes && filters.entityTypes.length > 0) {
      filteredNodes = filteredNodes.filter(node => 
        filters.entityTypes.includes(node.type)
      );
    }
    
    // Apply confidence threshold
    if (filters.confidenceThreshold) {
      const threshold = filters.confidenceThreshold / 100;
      filteredNodes = filteredNodes.filter(node => 
        !node.confidence || node.confidence >= threshold
      );
    }
    
    // Apply max nodes limit
    if (filters.maxNodes && filteredNodes.length > filters.maxNodes) {
      // Sort by confidence and take top N
      filteredNodes = filteredNodes
        .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
        .slice(0, filters.maxNodes);
    }
    
    // Filter links to only include nodes that made it through filtering
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    filteredLinks = filteredLinks.filter(link => 
      nodeIds.has(link.source) && nodeIds.has(link.target)
    );
    
    return { nodes: filteredNodes, links: filteredLinks };
  }, [data, filters]);

  return (
    <Box sx={{ 
      position: 'relative', 
      height: '100%', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      overflow: 'hidden'
    }}>
      {/* Graph Controls */}
      <Box sx={{ 
        position: 'absolute', 
        top: 16, 
        right: 16, 
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: 1
      }}>
        <Tooltip title="Zoom In">
          <IconButton 
            sx={{ background: alpha('#fff', 0.9) }}
            onClick={() => graphRef.current?.zoom(zoomLevel * 1.2)}
          >
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton 
            sx={{ background: alpha('#fff', 0.9) }}
            onClick={() => graphRef.current?.zoom(zoomLevel * 0.8)}
          >
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Center Graph">
          <IconButton 
            sx={{ background: alpha('#fff', 0.9) }}
            onClick={() => graphRef.current?.zoomToFit(400)}
          >
            <CenterIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title={isPaused ? "Resume" : "Pause"}>
          <IconButton 
            sx={{ background: alpha('#fff', 0.9) }}
            onClick={() => setIsPaused(!isPaused)}
          >
            {isPaused ? <PlayIcon /> : <PauseIcon />}
          </IconButton>
        </Tooltip>
        <Tooltip title={showNodeLabels ? "Hide Labels" : "Show Labels"}>
          <IconButton sx={{ background: alpha('#fff', 0.9) }}>
            {showNodeLabels ? 'ABC' : '•••'}
          </IconButton>
        </Tooltip>
      </Box>

      {/* Graph Statistics */}
      <Box sx={{ 
        position: 'absolute', 
        top: 16, 
        left: 16, 
        zIndex: 1000,
        background: alpha('#fff', 0.9),
        borderRadius: 1,
        p: 1
      }}>
        <Typography variant="caption" display="block">
          Nodes: {filteredGraphData.nodes.length}
        </Typography>
        <Typography variant="caption" display="block">
          Links: {filteredGraphData.links.length}
        </Typography>
        <Typography variant="caption" display="block">
          Zoom: {Math.round(zoomLevel * 100)}%
        </Typography>
      </Box>

      {/* Hover Tooltip */}
      {hoveredNode && (
        <Fade in={true}>
          <Card sx={{ 
            position: 'absolute', 
            bottom: 16, 
            right: 16, 
            zIndex: 1000,
            maxWidth: 300,
            background: alpha('#fff', 0.95)
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ 
                  width: 32, 
                  height: 32, 
                  mr: 1,
                  background: getEntityColor(hoveredNode.type)
                }}>
                  {hoveredNode.label?.charAt(0) || '?'}
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {hoveredNode.label || hoveredNode.id}
                  </Typography>
                  <Chip 
                    label={hoveredNode.type || 'Unknown'} 
                    size="small"
                    sx={{ background: alpha(getEntityColor(hoveredNode.type), 0.2) }}
                  />
                </Box>
              </Box>
              {hoveredNode.confidence && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Confidence: {Math.round(hoveredNode.confidence * 100)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={hoveredNode.confidence * 100}
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>
              )}
              {hoveredNode.description && (
                <Typography variant="body2" color="text.secondary">
                  {hoveredNode.description.length > 100 ? 
                    hoveredNode.description.substring(0, 100) + '...' : 
                    hoveredNode.description}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Fade>
      )}

      {/* Force Graph */}
      <ForceGraph2D
        ref={setGraphRef}
        graphData={filteredGraphData}
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        onNodeClick={onEntityClick}
        onNodeHover={setHoveredNode}
        nodeRelSize={8}
        linkDirectionalParticles={filters.showConnections ? 2 : 0}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        backgroundColor="transparent"
        width={undefined}
        height={500}
        cooldownTicks={isPaused ? 0 : 100}
        d3AlphaDecay={isPaused ? 1 : 0.0228}
        d3VelocityDecay={isPaused ? 1 : 0.4}
        onEngineStop={() => {}}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        onZoom={(zoom) => setZoomLevel(zoom.k)}
      />
    </Box>
  );
}

// Enhanced Investigation Workspace Main Component
function EnhancedInvestigativeWorkspace() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [investigationData, setInvestigationData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    entityTypes: [],
    confidenceThreshold: 0.7,
    relationshipDepth: 2,
    showConnections: true,
    maxNodes: 100
  });
  const [isSearching, setIsSearching] = useState(false);
  
  // Enhanced UI state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [graphMode, setGraphMode] = useState('force');
  const [showNodeLabels, setShowNodeLabels] = useState(true);
  const [highlightMode, setHighlightMode] = useState('hover');
  const [fullscreen, setFullscreen] = useState(false);
  const [nodeDetails, setNodeDetails] = useState(null);
  const graphRef = useRef();

  // Fetch knowledge graph data
  const { data: graphData, isLoading: graphLoading } = useQuery(
    'knowledge-graph',
    () => apiService.getKnowledgeGraphData(),
    {
      staleTime: 300000, // 5 minutes
      refetchOnWindowFocus: false,
    }
  );

  // Enhanced graph interactions
  const handleNodeClick = useCallback((node, event) => {
    setSelectedNodes(prev => {
      const isSelected = prev.find(n => n.id === node.id);
      if (event.ctrlKey || event.metaKey) {
        return isSelected ? prev.filter(n => n.id !== node.id) : [...prev, node];
      } else {
        return [node];
      }
    });
    setNodeDetails(node);
  }, []);

  const handleNodeHover = useCallback((node) => {
    if (highlightMode === 'hover' && node) {
      const connectedNodes = investigationData.links
        .filter(link => link.source === node.id || link.target === node.id)
        .map(link => link.source === node.id ? link.target : link.source);
      
      if (graphRef.current) {
        graphRef.current.nodeColor(n => 
          n.id === node.id ? '#ff6b6b' :
          connectedNodes.includes(n.id) ? '#4ecdc4' :
          alpha('#69b7ff', 0.3)
        );
      }
    }
  }, [highlightMode, investigationData.links]);

  const centerGraph = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  }, []);

  const saveGraphState = useCallback(() => {
    const state = {
      nodes: investigationData.nodes,
      links: investigationData.links,
      filters,
      searchQuery,
      timestamp: Date.now()
    };
    localStorage.setItem('investigation-state', JSON.stringify(state));
  }, [investigationData, filters, searchQuery]);

  const exportGraph = useCallback(() => {
    const dataStr = JSON.stringify(investigationData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `investigation-graph-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [investigationData]);

  useEffect(() => {
    if (graphData && graphData.nodes) {
      setInvestigationData(graphData);
    }
  }, [graphData]);

  // Auto-save graph state
  useEffect(() => {
    const saveTimer = setTimeout(saveGraphState, 2000);
    return () => clearTimeout(saveTimer);
  }, [saveGraphState]);

  // Load saved state on mount
  useEffect(() => {
    const savedState = localStorage.getItem('investigation-state');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        if (state.filters) setFilters(state.filters);
        if (state.searchQuery) setSearchQuery(state.searchQuery);
      } catch (e) {
        console.warn('Failed to load saved investigation state:', e);
      }
    }
  }, []);

  const handleSearch = async (query, searchFilters) => {
    setIsSearching(true);
    setLoading(true);
    try {
      const entityTypesStr = searchFilters.entityTypes.length > 0 ? searchFilters.entityTypes.join(',') : null;
      
      const searchResults = await apiService.advancedSearch(
        query,
        entityTypesStr,
        searchFilters.confidenceThreshold / 100, // Convert to decimal
        Math.min(searchFilters.maxNodes || 100, 200),
        0
      );
      
      if (searchResults && searchResults.results) {
        const filteredNodes = new Map();
        const filteredLinks = [];
        
        searchResults.results.forEach((hit, index) => {
          const doc = hit._source;
          const docId = hit._id;
          
          filteredNodes.set(docId, {
            id: docId,
            label: (doc.title || 'Untitled').substring(0, 30) + '...',
            type: 'DOCUMENT',
            size: 8,
            color: '#4CAF50',
            originalDoc: doc,
            confidence: 1.0
          });
          
          if (doc.openai_entities) {
            doc.openai_entities.forEach(entity => {
              const entityId = `entity_${entity.text.replace(/\s+/g, '_')}_${entity.type}`;
              filteredNodes.set(entityId, {
                id: entityId,
                label: entity.text,
                type: entity.type,
                size: 6,
                color: '#69b7ff',
                confidence: entity.confidence,
                description: entity.description
              });
              
              filteredLinks.push({
                source: docId,
                target: entityId,
                type: 'CONTAINS',
                weight: entity.confidence
              });
            });
          }
          
          if (doc.openai_relationships) {
            doc.openai_relationships.forEach(rel => {
              const sourceId = `entity_${rel.source_entity.replace(/\s+/g, '_')}_ENTITY`;
              const targetId = `entity_${rel.target_entity.replace(/\s+/g, '_')}_ENTITY`;
              
              filteredLinks.push({
                source: sourceId,
                target: targetId,
                type: rel.relationship_type,
                weight: rel.confidence,
                description: rel.description
              });
            });
          }
        });
        
        setInvestigationData({
          nodes: Array.from(filteredNodes.values()),
          links: filteredLinks
        });
      }
      
      console.log('Advanced search results:', searchResults);
    } catch (error) {
      console.error('Advanced search failed:', error);
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Find related entities for selected entity
  const relatedEntities = selectedEntity 
    ? investigationData.links
        .filter(link => link.source === selectedEntity.id || link.target === selectedEntity.id)
        .map(link => {
          const relatedId = link.source === selectedEntity.id ? link.target : link.source;
          return investigationData.nodes.find(node => node.id === relatedId);
        })
        .filter(Boolean)
        .slice(0, 10)
    : [];

  // Enhanced Layout Components
  const EnhancedToolbar = () => (
    <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', boxShadow: 3 }}>
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton color="inherit" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            🕵️ Investigation Workspace
          </Typography>
          <Chip 
            label={`${investigationData.nodes.length} Entities`}
            size="small"
            sx={{ background: alpha('#fff', 0.2), color: 'white' }}
          />
          <Chip 
            label={`${investigationData.links.length} Connections`}
            size="small"
            sx={{ background: alpha('#fff', 0.2), color: 'white' }}
          />
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Save State">
            <IconButton color="inherit" onClick={saveGraphState}>
              <SaveIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Export Graph">
            <IconButton color="inherit" onClick={exportGraph}>
              <ExportIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Center Graph">
            <IconButton color="inherit" onClick={centerGraph}>
              <CenterIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            <IconButton color="inherit" onClick={() => setFullscreen(!fullscreen)}>
              {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );

  const GraphControlPanel = () => (
    <Box sx={{ 
      position: 'absolute', 
      top: 16, 
      right: 16, 
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      gap: 1
    }}>
      {/* Compact Control Buttons */}
      <Card sx={{ p: 1, minWidth: 'auto' }}>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Zoom In">
            <IconButton size="small" onClick={() => graphRef.current?.zoom(1.2)}>
              <ZoomInIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out">
            <IconButton size="small" onClick={() => graphRef.current?.zoom(0.8)}>
              <ZoomOutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Center Graph">
            <IconButton size="small" onClick={centerGraph}>
              <CenterIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={showNodeLabels ? "Hide Labels" : "Show Labels"}>
            <IconButton 
              size="small" 
              onClick={() => setShowNodeLabels(!showNodeLabels)}
              color={showNodeLabels ? "primary" : "default"}
            >
              <Typography variant="caption" fontWeight="bold">
                {showNodeLabels ? 'ABC' : '•••'}
              </Typography>
            </IconButton>
          </Tooltip>
        </Stack>
      </Card>

      {/* Selected Nodes Info (if any) */}
      {selectedNodes.length > 0 && (
        <Card sx={{ p: 1, maxWidth: 200 }}>
          <Typography variant="caption" color="primary" fontWeight={600}>
            {selectedNodes.length} selected
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
            {selectedNodes.slice(0, 2).map(node => (
              <Chip 
                key={node.id}
                label={node.label.substring(0, 8) + '...'}
                size="small"
                variant="outlined"
                onDelete={() => setSelectedNodes(prev => prev.filter(n => n.id !== node.id))}
                sx={{ fontSize: '0.6rem', height: 20 }}
              />
            ))}
            {selectedNodes.length > 2 && (
              <Typography variant="caption" color="text.secondary">
                +{selectedNodes.length - 2} more
              </Typography>
            )}
          </Box>
        </Card>
      )}
    </Box>
  );

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <EnhancedToolbar />
      
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Collapsible Sidebar */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          sx={{
            width: sidebarOpen ? 380 : 0,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 380,
              position: 'relative',
              border: 'none',
              borderRight: `1px solid ${theme.palette.divider}`,
              background: alpha(theme.palette.background.paper, 0.98)
            },
          }}
        >
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <SearchPanel 
              onSearch={handleSearch} 
              onFilterChange={setFilters}
              isSearching={isSearching}
            />
            
            {selectedNodes.length > 0 && (
              <Card sx={{ m: 2, mt: 1 }}>
                <CardHeader 
                  title="Entity Inspector" 
                  titleTypographyProps={{ variant: 'h6', fontSize: '1rem' }}
                  sx={{ pb: 1 }}
                />
                <CardContent sx={{ pt: 0, maxHeight: 300, overflowY: 'auto' }}>
                  {selectedNodes.map(node => (
                    <Box key={node.id} sx={{ mb: 2, p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {node.label}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Type: {node.type || 'Unknown'}
                      </Typography>
                      {node.confidence && (
                        <Typography variant="body2" color="text.secondary">
                          Confidence: {(node.confidence * 100).toFixed(1)}%
                        </Typography>
                      )}
                      {relatedEntities.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" display="block">
                            Connected to {relatedEntities.length} entities
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                            {relatedEntities.slice(0, 3).map(entity => (
                              <Chip 
                                key={entity.id}
                                label={entity.label}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            ))}
                          </Box>
                        </Box>
                      )}
                    </Box>
                  ))}
                </CardContent>
              </Card>
            )}
          </Box>
        </Drawer>

        {/* Main Graph Area */}
        <Box 
          sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            overflow: 'hidden',
            position: 'relative',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
          }}
        >
          <Box sx={{ background: 'white', borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange}
              variant="fullWidth"
              sx={{ 
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 500,
                  minHeight: 64,
                  fontSize: '0.95rem'
                },
                '& .Mui-selected': {
                  background: alpha(theme.palette.primary.main, 0.1)
                }
              }}
            >
              <Tab 
                icon={<NetworkIcon sx={{ fontSize: 24 }} />} 
                label={
                  <Box>
                    <Typography variant="body2" fontWeight={600}>Network View</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Interactive knowledge graph
                    </Typography>
                  </Box>
                }
                iconPosition="start"
              />
              <Tab 
                icon={<TimelineIcon sx={{ fontSize: 24 }} />} 
                label={
                  <Box>
                    <Typography variant="body2" fontWeight={600}>Timeline</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Chronological events
                    </Typography>
                  </Box>
                }
                iconPosition="start"
              />
              <Tab 
                icon={<DocumentIcon sx={{ fontSize: 24 }} />} 
                label={
                  <Box>
                    <Typography variant="body2" fontWeight={600}>Documents</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Source materials
                    </Typography>
                  </Box>
                }
                iconPosition="start"
              />

            </Tabs>
          </Box>

          {activeTab === 0 && <GraphControlPanel />}

          <TabPanel value={activeTab} index={0}>
            <Box sx={{ position: 'relative', height: '100%', overflow: 'hidden' }}>
              <NetworkView 
                data={investigationData} 
                onEntityClick={handleNodeClick}
                onEntityHover={handleNodeHover}
                filters={filters}
                graphMode={graphMode}
                showNodeLabels={showNodeLabels}
                selectedNodes={selectedNodes}
                highlightMode={highlightMode}
                graphRef={graphRef}
                fullscreen={fullscreen}
              />
              
              <Card 
                sx={{ 
                  position: 'absolute', 
                  bottom: 16, 
                  left: 16, 
                  zIndex: 1000,
                  background: alpha('#fff', 0.95),
                  backdropFilter: 'blur(10px)'
                }}
              >
                <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
                  <Stack direction="row" spacing={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="primary" fontWeight={600}>
                        {investigationData.nodes.length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Entities
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="primary" fontWeight={600}>
                        {investigationData.links.length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Relations
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="primary" fontWeight={600}>
                        {selectedNodes.length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Selected
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
              
              {(loading || isSearching) && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: alpha('#fff', 0.8),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 2000
                  }}
                >
                  <Card sx={{ p: 3, textAlign: 'center' }}>
                    <LinearProgress sx={{ mb: 2, width: 200 }} />
                    <Typography variant="h6" color="primary">
                      {isSearching ? 'Searching...' : 'Loading...'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Building knowledge graph
                    </Typography>
                  </Card>
                </Box>
              )}
            </Box>
          </TabPanel>
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Timeline View - Coming Soon
              </Typography>
            </Box>
          </TabPanel>
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Documents View - Coming Soon
              </Typography>
            </Box>
          </TabPanel>

        </Box>
      </Box>
    </Box>
  );
}

export default EnhancedInvestigativeWorkspace;