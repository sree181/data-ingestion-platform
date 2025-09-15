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
    >
      {value === index && (
        <Box sx={{ height: '100%', p: 1 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Enhanced Search Panel Component
function SearchPanel({ onSearch, searchQuery, setSearchQuery, onFilterChange, isSearching }) {
  const theme = useTheme();
  const [filters, setFilters] = useState({
    entityTypes: [],
    confidenceThreshold: 70,
    relationshipDepth: 2,
    dateRange: {
      start: subMonths(new Date(), 6),
      end: new Date()
    },
    documentTypes: [],
    showConnections: true,
    minConnections: 1,
    maxNodes: 100
  });

  const entityTypes = [
    { value: 'PERSON', label: 'People', icon: '👤', color: '#FF6B6B' },
    { value: 'ORGANIZATION', label: 'Organizations', icon: '🏢', color: '#4ECDC4' },
    { value: 'EVENT', label: 'Events', icon: '📅', color: '#45B7D1' },
    { value: 'REGULATION', label: 'Regulations', icon: '⚖️', color: '#96CEB4' },
    { value: 'DATE', label: 'Dates', icon: '📆', color: '#FFEAA7' },
    { value: 'CONCEPT', label: 'Concepts', icon: '💡', color: '#DDA0DD' },
    { value: 'LOCATION', label: 'Locations', icon: '📍', color: '#98D8C8' }
  ];

  const handleSearch = useCallback(() => {
    const searchFilters = { ...filters, confidenceThreshold: filters.confidenceThreshold / 100 };
    if (onFilterChange) onFilterChange(searchFilters);
    onSearch(searchQuery, searchFilters);
  }, [searchQuery, filters, onSearch, onFilterChange]);

  const modernColors = {
    primary: '#667eea',
    secondary: '#f093fb',
    success: '#4facfe',
    warning: '#43e97b'
  };

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      {/* Modern Header */}
      <Box sx={{ 
        p: 2, 
        background: `linear-gradient(135deg, ${modernColors.primary} 0%, #764ba2 100%)`,
        color: 'white',
        borderRadius: '8px 8px 0 0'
      }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <SearchIcon sx={{ mr: 1 }} />
          Investigation Hub
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9 }}>
          Advanced cross-analysis tools
        </Typography>
      </Box>
      
      {/* Enhanced Search */}
      <Box sx={{ p: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search entities, documents, relationships..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Tooltip title="Search">
                  <IconButton onClick={handleSearch} size="small" disabled={isSearching}>
                    {isSearching ? <LinearProgress size={20} /> : <SearchIcon />}
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            )
          }}
          sx={{ 
            mb: 2,
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              background: alpha(theme.palette.primary.main, 0.02)
            }
          }}
        />

        {/* Quick Search Chips */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
          {['COVID-19', 'Vaccine', 'Adverse Events', 'Clinical Trial'].map((term) => (
            <Chip
              key={term}
              label={term}
              size="small"
              clickable
              onClick={() => setSearchQuery(term)}
              sx={{ 
                background: alpha(modernColors.primary, 0.1),
                '&:hover': { background: alpha(modernColors.primary, 0.2) }
              }}
            />
          ))}
        </Box>
      </Box>

      {/* Enhanced Filters */}
      <Box sx={{ px: 2 }}>
        {/* Entity Types Filter */}
        <Accordion sx={{ mb: 1, '&:before': { display: 'none' } }}>
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ 
              background: alpha(theme.palette.primary.main, 0.05),
              borderRadius: 1,
              '&:hover': { background: alpha(theme.palette.primary.main, 0.1) }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Badge badgeContent={filters.entityTypes.length} color="primary">
                <FilterIcon sx={{ mr: 1 }} />
              </Badge>
              <Typography variant="body2">Entity Types</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {entityTypes.map(type => (
                <Chip
                  key={type.value}
                  label={`${type.icon} ${type.label}`}
                  clickable
                  size="small"
                  variant={filters.entityTypes.includes(type.value) ? "filled" : "outlined"}
                  onClick={() => {
                    setFilters(prev => ({
                      ...prev,
                      entityTypes: prev.entityTypes.includes(type.value)
                        ? prev.entityTypes.filter(t => t !== type.value)
                        : [...prev.entityTypes, type.value]
                    }));
                  }}
                  sx={{ 
                    background: filters.entityTypes.includes(type.value) 
                      ? alpha(type.color, 0.2) 
                      : 'transparent',
                    color: type.color,
                    border: `1px solid ${type.color}`,
                    '&:hover': { background: alpha(type.color, 0.1) }
                  }}
                />
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Confidence & Depth */}
        <Accordion sx={{ mb: 1, '&:before': { display: 'none' } }}>
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ 
              background: alpha(theme.palette.success.main, 0.05),
              borderRadius: 1,
              '&:hover': { background: alpha(theme.palette.success.main, 0.1) }
            }}
          >
            <Typography variant="body2">
              🎯 Confidence: {filters.confidenceThreshold}% | 🔗 Depth: {filters.relationshipDepth}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" gutterBottom>Confidence Threshold</Typography>
            <Slider
              value={filters.confidenceThreshold}
              onChange={(_, value) => setFilters(prev => ({...prev, confidenceThreshold: value}))}
              min={0}
              max={100}
              step={5}
              marks={[
                { value: 0, label: '0%' },
                { value: 50, label: '50%' },
                { value: 100, label: '100%' }
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              sx={{ mb: 2 }}
            />
            
            <Typography variant="body2" gutterBottom>Relationship Depth</Typography>
            <Slider
              value={filters.relationshipDepth}
              onChange={(_, value) => setFilters(prev => ({...prev, relationshipDepth: value}))}
              min={1}
              max={5}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 3, label: '3' },
                { value: 5, label: '5' }
              ]}
              valueLabelDisplay="auto"
            />
          </AccordionDetails>
        </Accordion>

        {/* Advanced Options */}
        <Accordion sx={{ mb: 1, '&:before': { display: 'none' } }}>
          <AccordionSummary 
            expandIcon={<ExpandMoreIcon />}
            sx={{ 
              background: alpha(theme.palette.warning.main, 0.05),
              borderRadius: 1,
              '&:hover': { background: alpha(theme.palette.warning.main, 0.1) }
            }}
          >
            <Typography variant="body2">⚙️ Advanced Options</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormControlLabel
              control={
                <Switch
                  checked={filters.showConnections}
                  onChange={(e) => setFilters(prev => ({...prev, showConnections: e.target.checked}))}
                  color="primary"
                />
              }
              label="Show entity connections"
              sx={{ mb: 1 }}
            />
            
            <Typography variant="body2" gutterBottom>Max Nodes to Display</Typography>
            <Slider
              value={filters.maxNodes}
              onChange={(_, value) => setFilters(prev => ({...prev, maxNodes: value}))}
              min={20}
              max={500}
              step={20}
              valueLabelDisplay="auto"
            />
          </AccordionDetails>
        </Accordion>
      </Box>

      {/* Enhanced Action Buttons */}
      <Box sx={{ p: 2 }}>
        <Stack spacing={1}>
          <Button
            variant="contained"
            fullWidth
            onClick={handleSearch}
            disabled={isSearching}
            startIcon={isSearching ? <LinearProgress size={20} /> : <SearchIcon />}
            sx={{ 
              background: `linear-gradient(135deg, ${modernColors.primary} 0%, #764ba2 100%)`,
              '&:hover': { background: `linear-gradient(135deg, ${modernColors.secondary} 0%, #f5576c 100%)` }
            }}
          >
            {isSearching ? 'Analyzing...' : 'Run Investigation'}
          </Button>
          
          <Button
            variant="outlined"
            fullWidth
            onClick={() => setFilters({
              entityTypes: [],
              confidenceThreshold: 70,
              relationshipDepth: 2,
              dateRange: { start: subMonths(new Date(), 6), end: new Date() },
              documentTypes: [],
              showConnections: true,
              minConnections: 1,
              maxNodes: 100
            })}
            startIcon={<RefreshIcon />}
            size="small"
          >
            Clear Filters
          </Button>
        </Stack>

        {/* Quick Preset Actions */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>Quick Presets</Typography>
          <ButtonGroup orientation="vertical" size="small" fullWidth variant="outlined">
            <Button 
              startIcon={<PersonIcon />} 
              onClick={() => setFilters(prev => ({...prev, entityTypes: ['PERSON', 'ORGANIZATION']}))}
            >
              People & Organizations
            </Button>
            <Button 
              startIcon={<EventIcon />} 
              onClick={() => setFilters(prev => ({...prev, entityTypes: ['EVENT', 'DATE']}))}
            >
              Events & Timeline
            </Button>
            <Button 
              startIcon={<DocumentIcon />} 
              onClick={() => setFilters(prev => ({...prev, documentTypes: ['multimodal']}))}
            >
              Multimodal Documents
            </Button>
          </ButtonGroup>
        </Box>
      </Box>
    </Box>
  );
}

// Entity Details Panel Component
function EntityDetailsPanel({ selectedEntity, relatedEntities, onEntityClick }) {
  if (!selectedEntity) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Select an entity to view details
        </Typography>
      </Box>
    );
  }

  const getEntityIcon = (type) => {
    switch (type) {
      case 'PERSON': return <PersonIcon />;
      case 'ORGANIZATION': return <OrganizationIcon />;
      case 'EVENT': return <EventIcon />;
      case 'REGULATION': return <RegulationIcon />;
      case 'DATE': return <DateIcon />;
      default: return <NetworkIcon />;
    }
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {getEntityIcon(selectedEntity.type)} Entity Details
      </Typography>
      
      {/* Entity Info */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">{selectedEntity.label}</Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {selectedEntity.type}
          </Typography>
          
          {selectedEntity.confidence && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2">Confidence Score</Typography>
              <LinearProgress 
                variant="determinate" 
                value={selectedEntity.confidence * 100} 
                sx={{ mt: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {Math.round(selectedEntity.confidence * 100)}%
              </Typography>
            </Box>
          )}

          {selectedEntity.description && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {selectedEntity.description}
            </Typography>
          )}

          {/* Action Buttons */}
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button size="small" startIcon={<ExploreIcon />}>
              Explore
            </Button>
            <Button size="small" startIcon={<ShareIcon />}>
              Share
            </Button>
            <Button size="small" startIcon={<BookmarkIcon />}>
              Save
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Related Entities */}
      {relatedEntities && relatedEntities.length > 0 && (
        <Card>
          <CardHeader title="Related Entities" />
          <CardContent sx={{ maxHeight: 300, overflow: 'auto' }}>
            <List dense>
              {relatedEntities.map((entity, index) => (
                <ListItem 
                  key={entity.id} 
                  button 
                  onClick={() => onEntityClick(entity)}
                >
                  <ListItemIcon>
                    {getEntityIcon(entity.type)}
                  </ListItemIcon>
                  <ListItemText 
                    primary={entity.label}
                    secondary={`${entity.type} • Confidence: ${Math.round(entity.confidence * 100)}%`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

// Timeline View Component
function TimelineView({ investigationData }) {
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const generateTimelineFromData = () => {
      if (!investigationData.nodes) return;

      // Extract documents and create timeline events
      const documentNodes = investigationData.nodes.filter(node => node.type === 'DOCUMENT');
      const events = documentNodes.map((doc, index) => ({
        id: doc.id,
        title: doc.label,
        timestamp: new Date(Date.now() - (index * 24 * 60 * 60 * 1000)).toISOString(),
        type: 'document_processed',
        description: `Document processed with AI analysis`,
        entities: investigationData.nodes.filter(node => 
          investigationData.links.some(link => 
            (link.source === doc.id && link.target === node.id) ||
            (link.target === doc.id && link.source === node.id)
          )
        ).slice(0, 3)
      }));

      setTimelineData(events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
    };

    generateTimelineFromData();
  }, [investigationData]);

  return (
    <Box sx={{ p: 2, height: '500px', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
        <TimelineIcon sx={{ mr: 1 }} />
        Investigation Timeline
      </Typography>
      
      {timelineData.length === 0 ? (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            No timeline data available. Apply filters to see events.
          </Typography>
        </Box>
      ) : (
        <Box>
          {timelineData.map((event, index) => (
            <Box key={event.id} sx={{ mb: 3, display: 'flex' }}>
              <Box sx={{ width: '4px', bgcolor: '#1976d2', mr: 2 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                  {event.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {new Date(event.timestamp).toLocaleDateString()} - {event.type.replace('_', ' ')}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {event.description}
                </Typography>
                {event.entities.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {event.entities.map((entity, idx) => (
                      <Chip
                        key={idx}
                        label={entity.label}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}

// Documents View Component
function DocumentsView({ investigationData, onDocumentClick }) {
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    if (investigationData.nodes) {
      const documentNodes = investigationData.nodes.filter(node => node.type === 'DOCUMENT');
      const enrichedDocs = documentNodes.map(doc => {
        // Use original entity data if available, otherwise fall back to connected nodes
        const originalEntities = doc.openai_entities || [];
        const relatedEntities = investigationData.nodes.filter(node => 
          node.type !== 'DOCUMENT' && investigationData.links.some(link => 
            (link.source === doc.id && link.target === node.id) ||
            (link.target === doc.id && link.source === node.id)
          )
        );

        // Calculate entity count from original data
        const entityCount = originalEntities.length > 0 ? originalEntities.length : relatedEntities.length;
        
        // Helper function for entity type colors (inline)
        const getEntityTypeColor = (type) => {
          const colors = {
            'PERSON': '#FF6B6B',
            'ORGANIZATION': '#4ECDC4', 
            'EVENT': '#45B7D1',
            'REGULATION': '#96CEB4',
            'DATE': '#FFEAA7',
            'CONCEPT': '#DDA0DD',
            'LOCATION': '#98D8C8'
          };
          return colors[type] || '#B0B0B0';
        };

        // Create entity objects for display
        const displayEntities = originalEntities.length > 0 
          ? originalEntities.slice(0, 5).map(entity => ({
              label: entity.text,
              type: entity.type,
              color: getEntityTypeColor(entity.type),
              confidence: entity.confidence
            }))
          : relatedEntities.slice(0, 5);

        return {
          ...doc,
          entityCount: entityCount,
          entities: displayEntities,
          relevanceScore: Math.min(entityCount * 10, 100),
          fullTitle: doc.originalDoc?.title || doc.label,
          // Add image data if available
          hasImages: doc.originalDoc?.stored_images?.length > 0 || false,
          imageCount: doc.originalDoc?.stored_images?.length || 0,
          images: doc.originalDoc?.stored_images || []
        };
      }).sort((a, b) => b.relevanceScore - a.relevanceScore);

      setDocuments(enrichedDocs);
    }
  }, [investigationData]);

  return (
    <Box sx={{ p: 2, height: '500px', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
        <DocumentIcon sx={{ mr: 1 }} />
        Related Documents ({documents.length})
      </Typography>
      
      {documents.length === 0 ? (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            No documents found. Apply filters to see related documents.
          </Typography>
        </Box>
      ) : (
        <Box>
          {documents.map((doc) => (
            <Card key={doc.id} sx={{ mb: 2, cursor: 'pointer' }} onClick={() => onDocumentClick(doc)}>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', flexGrow: 1 }}>
                    {doc.fullTitle || doc.label}
                  </Typography>
                  <Chip 
                    label={`${doc.relevanceScore}%`} 
                    size="small" 
                    color={doc.relevanceScore > 70 ? 'success' : doc.relevanceScore > 40 ? 'warning' : 'default'}
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {doc.entityCount} entities identified
                </Typography>
                
                {doc.entities.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                    {doc.entities.map((entity, idx) => (
                      <Chip
                        key={idx}
                        label={entity.label}
                        size="small"
                        sx={{ 
                          fontSize: '0.7rem',
                          bgcolor: entity.color + '20',
                          border: `1px solid ${entity.color}`,
                          color: entity.color
                        }}
                      />
                    ))}
                  </Box>
                )}

                {/* Image Gallery for documents with images */}
                {doc.hasImages && doc.images.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      📷 {doc.imageCount} image{doc.imageCount > 1 ? 's' : ''} extracted
                    </Typography>
                    <ImageGallery 
                      images={doc.images.slice(0, 3).map(img => ({
                        ...img,
                        preview_url: img.storage_url || `/api/v1/documents/${doc.id}/images/${img.image_id}`,
                        entities: doc.originalDoc?.image_entities?.filter(e => 
                          e.image_id === img.image_id || 
                          e.page_number === img.page_number
                        ) || [],
                        analysis: img.analysis || 'AI analysis pending',
                        image_type: img.image_type || 'unknown'
                      }))}
                      compact={true}
                      onImageClick={(image) => console.log('Document image clicked:', image)}
                      onEntityClick={(entity) => console.log('Image entity clicked:', entity)}
                    />
                    {doc.imageCount > 3 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        +{doc.imageCount - 3} more images...
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}

// Analytics View Component  
function AnalyticsView({ investigationData }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (investigationData.nodes && investigationData.links) {
      const nodes = investigationData.nodes;
      const links = investigationData.links;
      
      // Calculate analytics
      const entityNodes = nodes.filter(n => n.type !== 'DOCUMENT');
      const documentNodes = nodes.filter(n => n.type === 'DOCUMENT');
      
      const entityTypes = {};
      entityNodes.forEach(entity => {
        entityTypes[entity.type] = (entityTypes[entity.type] || 0) + 1;
      });

      const topEntities = entityNodes
        .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
        .slice(0, 10);

      const connectionCounts = {};
      links.forEach(link => {
        connectionCounts[link.source] = (connectionCounts[link.source] || 0) + 1;
        connectionCounts[link.target] = (connectionCounts[link.target] || 0) + 1;
      });

      const mostConnected = Object.entries(connectionCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .map(([nodeId, count]) => ({
          node: nodes.find(n => n.id === nodeId),
          connections: count
        }));

      setAnalytics({
        totalEntities: entityNodes.length,
        totalDocuments: documentNodes.length,
        totalConnections: links.length,
        entityTypes: Object.entries(entityTypes).map(([type, count]) => ({ type, count })),
        topEntities,
        mostConnected,
        avgConfidence: entityNodes.reduce((sum, e) => sum + (e.confidence || 0), 0) / entityNodes.length || 0
      });
    }
  }, [investigationData]);

  if (!analytics) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No analytics data available. Apply filters to see statistics.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, height: '500px', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
        <AnalyticsIcon sx={{ mr: 1 }} />
        Investigation Analytics
      </Typography>
      
      {/* Key Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="primary">{analytics.totalEntities}</Typography>
              <Typography variant="body2">Entities</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="secondary">{analytics.totalDocuments}</Typography>
              <Typography variant="body2">Documents</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="success.main">{analytics.totalConnections}</Typography>
              <Typography variant="body2">Connections</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h4" color="warning.main">{(analytics.avgConfidence * 100).toFixed(1)}%</Typography>
              <Typography variant="body2">Avg Confidence</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Entity Types Distribution */}
      <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Entity Types</Typography>
      <Box sx={{ mb: 3 }}>
        {analytics.entityTypes.map(({ type, count }) => (
          <Box key={type} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" sx={{ minWidth: 120 }}>{type}</Typography>
            <Box sx={{ flexGrow: 1, mx: 2, height: 8, bgcolor: 'grey.200', borderRadius: 1 }}>
              <Box 
                sx={{ 
                  height: '100%', 
                  bgcolor: 'primary.main', 
                  borderRadius: 1,
                  width: `${(count / analytics.totalEntities) * 100}%`
                }} 
              />
            </Box>
            <Typography variant="body2" sx={{ minWidth: 30 }}>{count}</Typography>
          </Box>
        ))}
      </Box>

      {/* Most Connected Entities */}
      <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Most Connected</Typography>
      <Box>
        {analytics.mostConnected.map(({ node, connections }, idx) => (
          <Box key={node?.id || idx} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" sx={{ flexGrow: 1 }}>
              {node?.label || 'Unknown'} ({node?.type || 'Unknown'})
            </Typography>
            <Chip label={`${connections} connections`} size="small" />
          </Box>
        ))}
      </Box>
    </Box>
  );
}

// Enhanced Network View Component
function NetworkView({ graphData, onNodeClick, selectedEntity, filters }) {
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isPaused, setIsPaused] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [graphRef, setGraphRef] = useState(null);
  const theme = useTheme();

  const getEntityColor = (type) => {
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
  };

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const label = node.label;
    const fontSize = Math.max(8, 12 / globalScale);
    ctx.font = `${fontSize}px Inter, sans-serif`;
    
    // Enhanced node styling
    const baseSize = node.size || 5;
    const size = selectedEntity && selectedEntity.id === node.id ? baseSize * 1.5 : baseSize;
    
    // Node glow effect for important nodes
    if (node.confidence && node.confidence > 0.8) {
      ctx.shadowColor = getEntityColor(node.type);
      ctx.shadowBlur = 10;
    }
    
    // Main node circle
    ctx.fillStyle = getEntityColor(node.type);
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fill();
    
    // Inner highlight
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.beginPath();
    ctx.arc(node.x - size * 0.3, node.y - size * 0.3, size * 0.4, 0, 2 * Math.PI);
    ctx.fill();
    
    // Reset shadow
    ctx.shadowBlur = 0;

    // Selected node highlight with animation
    if (selectedEntity && selectedEntity.id === node.id) {
      const time = Date.now() * 0.005;
      const pulse = 0.5 + 0.5 * Math.sin(time);
      ctx.strokeStyle = `rgba(255, 107, 53, ${0.5 + pulse * 0.5})`;
      ctx.lineWidth = 3 / globalScale;
      ctx.setLineDash([5 / globalScale, 5 / globalScale]);
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 2, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Hovered node effect
    if (hoveredNode && hoveredNode.id === node.id) {
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 2 / globalScale;
      ctx.stroke();
    }

    // Enhanced labels with better visibility
    if (showLabels && (globalScale > 1.2 || node.type === 'DOCUMENT' || (selectedEntity && selectedEntity.id === node.id))) {
      const maxLabelLength = Math.floor(20 / Math.max(1, globalScale - 1));
      const displayLabel = label.length > maxLabelLength ? label.substring(0, maxLabelLength) + '...' : label;
      
      const textWidth = ctx.measureText(displayLabel).width;
      const bckgDimensions = [textWidth + 6, fontSize + 4];
      
      // Label background with rounded corners effect
      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.fillRect(
        node.x - bckgDimensions[0] / 2, 
        node.y + size + 2, 
        bckgDimensions[0], 
        bckgDimensions[1]
      );
      
      // Label border
      ctx.strokeStyle = getEntityColor(node.type);
      ctx.lineWidth = 1 / globalScale;
      ctx.strokeRect(
        node.x - bckgDimensions[0] / 2, 
        node.y + size + 2, 
        bckgDimensions[0], 
        bckgDimensions[1]
      );
      
      // Label text
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#333';
      ctx.fillText(displayLabel, node.x, node.y + size + 2 + bckgDimensions[1] / 2);
    }
  }, [selectedEntity, hoveredNode, showLabels]);

  const linkCanvasObject = useCallback((link, ctx) => {
    // Enhanced link styling
    const start = link.source;
    const end = link.target;
    
    if (typeof start !== 'object' || typeof end !== 'object') return;
    
    // Link opacity based on confidence
    const opacity = link.weight ? Math.max(0.3, link.weight) : 0.5;
    
    // Gradient links for better visual appeal
    const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
    gradient.addColorStop(0, `rgba(150, 150, 150, ${opacity})`);
    gradient.addColorStop(1, `rgba(100, 100, 100, ${opacity})`);
    
    ctx.strokeStyle = gradient;
    ctx.lineWidth = Math.max(1, (link.weight || 0.5) * 3);
    
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();
  }, []);

  const handleZoomIn = () => {
    if (graphRef) {
      graphRef.zoom(zoomLevel * 1.5, 400);
      setZoomLevel(prev => prev * 1.5);
    }
  };

  const handleZoomOut = () => {
    if (graphRef) {
      graphRef.zoom(zoomLevel * 0.75, 400);
      setZoomLevel(prev => prev * 0.75);
    }
  };

  const handleCenter = () => {
    if (graphRef) {
      graphRef.zoomToFit(400);
      setZoomLevel(1);
    }
  };

  const filteredGraphData = useMemo(() => {
    if (!graphData || !graphData.nodes) return { nodes: [], links: [] };
    
    let filteredNodes = graphData.nodes;
    let filteredLinks = graphData.links;
    
    // Apply filters
    if (filters?.entityTypes?.length > 0) {
      filteredNodes = filteredNodes.filter(node => 
        node.type === 'DOCUMENT' || filters.entityTypes.includes(node.type)
      );
    }
    
    if (filters?.confidenceThreshold) {
      filteredNodes = filteredNodes.filter(node => 
        node.type === 'DOCUMENT' || !node.confidence || node.confidence >= filters.confidenceThreshold
      );
    }
    
    // Filter links to only include nodes that passed the filter
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    filteredLinks = filteredLinks.filter(link => 
      nodeIds.has(link.source) && nodeIds.has(link.target)
    );
    
    // Limit nodes if specified
    if (filters?.maxNodes && filteredNodes.length > filters.maxNodes) {
      // Keep documents and highest confidence entities
      const documents = filteredNodes.filter(n => n.type === 'DOCUMENT');
      const entities = filteredNodes
        .filter(n => n.type !== 'DOCUMENT')
        .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
        .slice(0, filters.maxNodes - documents.length);
      
      filteredNodes = [...documents, ...entities];
      const nodeIds = new Set(filteredNodes.map(n => n.id));
      filteredLinks = filteredLinks.filter(link => 
        nodeIds.has(link.source) && nodeIds.has(link.target)
      );
    }
    
    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, filters]);

  return (
    <Box sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* Enhanced Controls */}
      <Box sx={{ 
        position: 'absolute', 
        top: 10, 
        right: 10, 
        zIndex: 1000,
        background: alpha(theme.palette.background.paper, 0.95),
        borderRadius: 2,
        p: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        backdropFilter: 'blur(10px)'
      }}>
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Center View">
          <IconButton size="small" onClick={handleCenter}>
            <CenterIcon />
          </IconButton>
        </Tooltip>
        <Divider />
        <Tooltip title={isPaused ? "Resume" : "Pause"}>
          <IconButton size="small" onClick={() => setIsPaused(!isPaused)}>
            {isPaused ? <PlayIcon /> : <PauseIcon />}
          </IconButton>
        </Tooltip>
        <Tooltip title={showLabels ? "Hide Labels" : "Show Labels"}>
          <IconButton size="small" onClick={() => setShowLabels(!showLabels)}>
            <Typography sx={{ fontSize: '0.7rem' }}>
              {showLabels ? 'ABC' : '•••'}
            </Typography>
          </IconButton>
        </Tooltip>
      </Box>

      {/* Network Statistics */}
      <Box sx={{ 
        position: 'absolute', 
        top: 10, 
        left: 10, 
        zIndex: 1000,
        background: alpha(theme.palette.background.paper, 0.95),
        borderRadius: 2,
        p: 1.5,
        backdropFilter: 'blur(10px)'
      }}>
        <Typography variant="caption" display="block">
          <strong>Nodes:</strong> {filteredGraphData.nodes.length}
        </Typography>
        <Typography variant="caption" display="block">
          <strong>Links:</strong> {filteredGraphData.links.length}
        </Typography>
        <Typography variant="caption" display="block">
          <strong>Zoom:</strong> {Math.round(zoomLevel * 100)}%
        </Typography>
      </Box>

      {/* Enhanced hover tooltip */}
      {hoveredNode && (
        <Fade in={Boolean(hoveredNode)}>
          <Box
            sx={{
              position: 'absolute',
              top: 60,
              left: 10,
              background: alpha(theme.palette.background.paper, 0.98),
              color: theme.palette.text.primary,
              p: 2,
              borderRadius: 2,
              minWidth: 200,
              zIndex: 1001,
              border: `2px solid ${getEntityColor(hoveredNode.type)}`,
              backdropFilter: 'blur(10px)'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Avatar sx={{ 
                bgcolor: getEntityColor(hoveredNode.type),
                mr: 1,
                width: 32,
                height: 32
              }}>
                {hoveredNode.type === 'PERSON' ? '👤' : 
                 hoveredNode.type === 'ORGANIZATION' ? '🏢' : 
                 hoveredNode.type === 'DOCUMENT' ? '📄' : '🔗'}
              </Avatar>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                  {hoveredNode.label}
                </Typography>
                <Chip 
                  label={hoveredNode.type} 
                  size="small"
                  sx={{ 
                    background: getEntityColor(hoveredNode.type),
                    color: 'white',
                    fontSize: '0.7rem'
                  }}
                />
              </Box>
            </Box>
            
            {hoveredNode.confidence && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" display="block">
                  Confidence: {Math.round(hoveredNode.confidence * 100)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={hoveredNode.confidence * 100}
                  sx={{ 
                    height: 4,
                    background: alpha(getEntityColor(hoveredNode.type), 0.2),
                    '& .MuiLinearProgress-bar': {
                      background: getEntityColor(hoveredNode.type)
                    }
                  }}
                />
              </Box>
            )}
            
            {hoveredNode.description && (
              <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                {hoveredNode.description.length > 100 
                  ? hoveredNode.description.substring(0, 100) + '...'
                  : hoveredNode.description
                }
              </Typography>
            )}
          </Box>
        </Fade>
      )}

      {/* Main Force Graph */}
      <Box sx={{ 
        width: '100%', 
        height: '100%',
        '& canvas': {
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.02)} 0%, ${alpha(theme.palette.secondary.main, 0.02)} 100%)`
        }
      }}>
        <ForceGraph2D
          ref={setGraphRef}
          graphData={filteredGraphData}
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={onNodeClick}
          onNodeHover={setHoveredNode}
          nodeColor={(node) => getEntityColor(node.type)}
          nodeVal={(node) => node.size || 5}
          nodeLabel={(node) => node.label}
          linkDirectionalParticles={filters?.showConnections ? 2 : 0}
          linkDirectionalParticleSpeed={0.004}
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
        />
      </Box>
    </Box>
  );
}

// Main Investigation Workspace Component
function InvestigativeWorkspace() {
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
  const [graphMode, setGraphMode] = useState('force'); // force, circular, hierarchical
  const [showNodeLabels, setShowNodeLabels] = useState(true);
  const [highlightMode, setHighlightMode] = useState('hover'); // hover, select, path
  const [fullscreen, setFullscreen] = useState(false);
  const [nodeDetails, setNodeDetails] = useState(null);
  const [detailsAnchor, setDetailsAnchor] = useState(null);
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
        // Multi-select
        return isSelected ? prev.filter(n => n.id !== node.id) : [...prev, node];
      } else {
        // Single select
        return [node];
      }
    });
    setNodeDetails(node);
    setDetailsAnchor(event.target);
  }, []);

  const handleNodeHover = useCallback((node) => {
    if (highlightMode === 'hover' && node) {
      // Highlight connected nodes
      const connectedNodes = investigationData.links
        .filter(link => link.source === node.id || link.target === node.id)
        .map(link => link.source === node.id ? link.target : link.source);
      
      // Visual feedback for connected nodes
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
      // Use advanced search API with filters
      const entityTypesStr = searchFilters.entityTypes.length > 0 ? searchFilters.entityTypes.join(',') : null;
      
      const searchResults = await apiService.advancedSearch(
        query,
        entityTypesStr,
        searchFilters.confidenceThreshold, // Already in decimal format
        Math.min(searchFilters.maxNodes || 100, 200), // size with limit
        0   // from
      );
      
      if (searchResults && searchResults.results) {
        // Create filtered network data from search results
        const filteredNodes = new Map();
        const filteredLinks = [];
        
        // Process search results to build network
        searchResults.results.forEach((hit, index) => {
          const doc = hit._source;
          const docId = hit._id;
          
          // Add document node with original data
          filteredNodes.set(docId, {
            id: docId,
            label: (doc.title || 'Untitled').substring(0, 30) + '...',
            type: 'DOCUMENT',
            size: 8,
            color: '#4CAF50',
            originalDoc: doc,  // Preserve original document data
            openai_entities: doc.openai_entities || []
          });
          
          // Add entity nodes and links
          (doc.openai_entities || []).forEach(entity => {
            if (entity.confidence >= (filters.confidenceThreshold / 100)) {
              const entityId = `entity_${entity.text.replace(/\s+/g, '_')}`;
              
              // Check if entity type matches filter
              if (filters.entityTypes.length === 0 || filters.entityTypes.includes(entity.type)) {
                if (!filteredNodes.has(entityId)) {
                  filteredNodes.set(entityId, {
                    id: entityId,
                    label: entity.text,
                    type: entity.type,
                    size: Math.min(6 + Math.round(entity.confidence * 4), 12),
                    color: getEntityTypeColor(entity.type),
                    confidence: entity.confidence
                  });
                }
                
                // Link document to entity
                filteredLinks.push({
                  source: docId,
                  target: entityId,
                  relationship: 'CONTAINS',
                  weight: entity.confidence
                });
              }
            }
          });
        });
        
        // Create entity-to-entity co-occurrence links
        const nodeArray = Array.from(filteredNodes.values());
        const entityNodes = nodeArray.filter(n => n.type !== 'DOCUMENT');
        
        for (let i = 0; i < entityNodes.length; i++) {
          for (let j = i + 1; j < entityNodes.length && j < i + 5; j++) {
            filteredLinks.push({
              source: entityNodes[i].id,
              target: entityNodes[j].id,
              relationship: 'CO_OCCURS',
              weight: 0.5
            });
          }
        }
        
        // Update investigation data with filtered results
        setInvestigationData({
          nodes: nodeArray,
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

  // Helper function for entity type colors
  const getEntityTypeColor = (type) => {
    const colors = {
      'PERSON': '#FF6B6B',
      'ORGANIZATION': '#4ECDC4', 
      'EVENT': '#45B7D1',
      'REGULATION': '#96CEB4',
      'DATE': '#FFEAA7',
      'CONCEPT': '#DDA0DD',
      'LOCATION': '#98D8C8'
    };
    return colors[type] || '#B0B0B0';
  };

  const handleEntityClick = (entity) => {
    setSelectedEntity(entity);
    // Could trigger additional API calls to get entity details
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
        .slice(0, 10) // Limit to 10 related entities
    : [];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, borderRadius: 0 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          🕵️ Investigative Workspace
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Palantir-style investigation and analysis platform
        </Typography>
      </Paper>

      {/* Main Workspace */}
      <Grid container sx={{ flexGrow: 1 }}>
        {/* Left Panel - Enhanced Search & Filters */}
        <Grid item xs={3} sx={{ borderRight: '1px solid #e0e0e0' }}>
          <Paper sx={{ height: '100%', borderRadius: 0, overflow: 'hidden' }}>
            <SearchPanel 
              onSearch={handleSearch}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              onFilterChange={setFilters}
              isSearching={isSearching}
            />
          </Paper>
        </Grid>

        {/* Center Panel - Main Workspace */}
        <Grid item xs={6}>
          <Paper sx={{ height: '100%', borderRadius: 0 }}>
            {/* Tab System */}
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange}
              sx={{ borderBottom: '1px solid #e0e0e0' }}
            >
              <Tab icon={<NetworkIcon />} label="Network" />
              <Tab icon={<TimelineIcon />} label="Timeline" />
              <Tab icon={<DocumentIcon />} label="Documents" />
              <Tab icon={<AnalyticsIcon />} label="Analytics" />
            </Tabs>

            {loading && <LinearProgress />}

            {/* Tab Panels */}
            <TabPanel value={activeTab} index={0}>
              <NetworkView 
                graphData={investigationData}
                onNodeClick={handleEntityClick}
                selectedEntity={selectedEntity}
                filters={filters}
              />
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <TimelineView investigationData={investigationData} />
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <DocumentsView investigationData={investigationData} onDocumentClick={handleEntityClick} />
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <AnalyticsView investigationData={investigationData} />
            </TabPanel>
          </Paper>
        </Grid>

        {/* Right Panel - Entity Details */}
        <Grid item xs={3} sx={{ borderLeft: '1px solid #e0e0e0' }}>
          <Paper sx={{ height: '100%', p: 2, borderRadius: 0 }}>
            <EntityDetailsPanel 
              selectedEntity={selectedEntity}
              relatedEntities={relatedEntities}
              onEntityClick={handleEntityClick}
            />
          </Paper>
        </Grid>
      </Grid>

      {/* Status Bar */}
      <Paper sx={{ p: 1, borderRadius: 0, borderTop: '1px solid #e0e0e0' }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <Typography variant="caption" color="text.secondary">
              Entities: {investigationData.nodes.length}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="caption" color="text.secondary">
              Relationships: {investigationData.links.length}
            </Typography>
          </Grid>
          <Grid item>
            <Typography variant="caption" color="text.secondary">
              {selectedEntity ? `Selected: ${selectedEntity.label}` : 'No selection'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

export default InvestigativeWorkspace;