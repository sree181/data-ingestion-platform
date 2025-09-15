import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  LocalHospital as MedicalIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import * as d3 from 'd3';

function KnowledgeGraph() {
  const svgRef = useRef();
  const [selectedEntityType, setSelectedEntityType] = useState('all');
  const [zoom, setZoom] = useState(1);
  
  // Fetch all documents to build knowledge graph
  const { data: documentsData, isLoading, error } = useQuery(
    'knowledge-graph-data',
    () => apiService.searchDocuments('', { size: 100 }),
    {
      staleTime: 300000, // 5 minutes
    }
  );

  // Process data for knowledge graph
  const processGraphData = () => {
    if (!documentsData?.results) return { nodes: [], links: [] };

    const entityMap = new Map();
    const relationshipMap = new Map();
    const nodes = [];
    const links = [];

    // Extract all entities and relationships from documents
    documentsData.results.forEach(doc => {
      const entities = doc._source.openai_entities || [];
      const relationships = doc._source.relationships || [];

      // Add entities as nodes
      entities.forEach(entity => {
        const key = `${entity.type}:${entity.text}`;
        if (!entityMap.has(key)) {
          entityMap.set(key, {
            id: key,
            text: entity.text,
            type: entity.type,
            description: entity.description || '',
            confidence: entity.confidence || 0,
            documents: [doc._source.title],
            count: 1,
          });
        } else {
          const existing = entityMap.get(key);
          existing.documents.push(doc._source.title);
          existing.count += 1;
        }
      });

      // Add relationships as links
      relationships.forEach(rel => {
        const sourceKey = entities.find(e => e.text === rel.source_entity);
        const targetKey = entities.find(e => e.text === rel.target_entity);
        
        if (sourceKey && targetKey) {
          const linkKey = `${sourceKey.type}:${sourceKey.text}->${targetKey.type}:${targetKey.text}`;
          if (!relationshipMap.has(linkKey)) {
            relationshipMap.set(linkKey, {
              source: `${sourceKey.type}:${sourceKey.text}`,
              target: `${targetKey.type}:${targetKey.text}`,
              type: rel.relationship_type,
              description: rel.description || '',
              confidence: rel.confidence || 0,
              count: 1,
            });
          } else {
            relationshipMap.get(linkKey).count += 1;
          }
        }
      });
    });

    // Convert maps to arrays
    entityMap.forEach(entity => nodes.push(entity));
    relationshipMap.forEach(link => links.push(link));

    // Filter by selected entity type
    if (selectedEntityType !== 'all') {
      const filteredNodes = nodes.filter(node => 
        node.type.toLowerCase() === selectedEntityType.toLowerCase()
      );
      const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
      const filteredLinks = links.filter(link => 
        filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target)
      );
      return { nodes: filteredNodes, links: filteredLinks };
    }

    return { nodes, links };
  };

  const graphData = processGraphData();
  const entityTypes = [...new Set(graphData.nodes.map(n => n.type))];

  // D3.js visualization
  useEffect(() => {
    if (!graphData.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800;
    const height = 600;

    svg.attr('width', width).attr('height', height);

    const g = svg.append('g');

    // Create zoom behavior
    const zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // Color scale for entity types
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(graphData.links)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.count) * 2);

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(graphData.nodes)
      .enter().append('circle')
      .attr('r', d => Math.sqrt(d.count) * 5 + 10)
      .attr('fill', d => colorScale(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add labels
    const label = g.append('g')
      .selectAll('text')
      .data(graphData.nodes)
      .enter().append('text')
      .text(d => d.text)
      .attr('font-size', '12px')
      .attr('font-family', 'Arial, sans-serif')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .style('pointer-events', 'none')
      .style('fill', '#333');

    // Add tooltips
    node.append('title')
      .text(d => `${d.type}: ${d.text}\nDocuments: ${d.count}\nConfidence: ${(d.confidence * 100).toFixed(0)}%`);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      label
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Center graph function
    window.centerGraph = () => {
      svg.transition().duration(750).call(
        zoomBehavior.transform,
        d3.zoomIdentity.translate(0, 0).scale(1)
      );
    };

  }, [graphData, selectedEntityType]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load knowledge graph data: {error.message}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Knowledge Graph
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Interactive visualization of entities and relationships extracted from your documents using AI.
      </Typography>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
              <FormControl size="small" sx={{ minWidth: 200 }}>
                <InputLabel>Filter by Entity Type</InputLabel>
                <Select
                  value={selectedEntityType}
                  label="Filter by Entity Type"
                  onChange={(e) => setSelectedEntityType(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  {entityTypes.map(type => (
                    <MenuItem key={type} value={type}>
                      {type} ({graphData.nodes.filter(n => n.type === type).length})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box display="flex" gap={1}>
                <Tooltip title="Zoom In">
                  <IconButton 
                    onClick={() => {
                      const svg = d3.select(svgRef.current);
                      svg.transition().duration(300).call(
                        d3.zoom().scaleBy,
                        1.5
                      );
                    }}
                  >
                    <ZoomInIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Zoom Out">
                  <IconButton 
                    onClick={() => {
                      const svg = d3.select(svgRef.current);
                      svg.transition().duration(300).call(
                        d3.zoom().scaleBy,
                        0.67
                      );
                    }}
                  >
                    <ZoomOutIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Center Graph">
                  <IconButton onClick={() => window.centerGraph && window.centerGraph()}>
                    <CenterIcon />
                  </IconButton>
                </Tooltip>
              </Box>

              <Typography variant="body2" color="text.secondary">
                Zoom: {(zoom * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Graph Visualization */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Entity Relationship Network
            </Typography>
            <Box sx={{ border: '1px solid #ddd', borderRadius: 1, overflow: 'hidden' }}>
              <svg ref={svgRef} style={{ background: '#fafafa' }}></svg>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Drag nodes to explore • Scroll to zoom • Click center to reset view
            </Typography>
          </Paper>
        </Grid>

        {/* Statistics and Legend */}
        <Grid item xs={12} md={4}>
          {/* Statistics */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Graph Statistics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Entities: {graphData.nodes.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Relationships: {graphData.links.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Documents Analyzed: {documentsData?.total || 0}
              </Typography>
            </CardContent>
          </Card>

          {/* Entity Types Legend */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Types
              </Typography>
              <List dense>
                {entityTypes.map(type => {
                  const count = graphData.nodes.filter(n => n.type === type).length;
                  const getIcon = (type) => {
                    const icons = {
                      'PERSON': <PersonIcon fontSize="small" />,
                      'ORGANIZATION': <BusinessIcon fontSize="small" />,
                      'LOCATION': <LocationIcon fontSize="small" />,
                      'DRUG': <MedicalIcon fontSize="small" />,
                      'DISEASE': <MedicalIcon fontSize="small" />,
                    };
                    return icons[type] || <BusinessIcon fontSize="small" />;
                  };

                  return (
                    <ListItem key={type} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {getIcon(type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={type}
                        secondary={`${count} entities`}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </CardContent>
          </Card>

          {/* Top Entities */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Connected Entities
              </Typography>
              <List dense>
                {graphData.nodes
                  .sort((a, b) => b.count - a.count)
                  .slice(0, 10)
                  .map((entity, index) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemText
                        primary={entity.text}
                        secondary={
                          <Box>
                            <Chip 
                              label={entity.type} 
                              size="small" 
                              sx={{ mr: 1, fontSize: '10px', height: '20px' }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {entity.count} documents
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default KnowledgeGraph;