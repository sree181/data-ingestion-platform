import React, { useRef, useEffect, useCallback, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import { Box, IconButton, Tooltip, Card, Typography, Fade, Zoom } from '@mui/material';
import { 
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  ViewInAr as View3DIcon,
  Refresh as RefreshIcon,
  Fullscreen as FullscreenIcon,
  Mouse as MouseIcon
} from '@mui/icons-material';

/**
 * Enterprise-Grade WebGL Knowledge Graph
 * 
 * Professional 3D visualization with:
 * - Physically-based rendering (PBR)
 * - Smooth 60fps animations
 * - Intuitive camera controls
 * - Enterprise-grade aesthetics
 * - Optimized for large datasets
 */
const WebGLKnowledgeGraph = ({
  graphData,
  onNodeClick,
  onNodeHover,
  highlightNodes,
  highlightLinks,
  selectedEntity,
  entityConfig,
  width = '100%',
  height = '800px'
}) => {
  const graphRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoverNode, setHoverNode] = useState(null);
  const [showGuide, setShowGuide] = useState(true);
  
  // Measure container dimensions
  useEffect(() => {
    if (containerRef.current) {
      const updateDimensions = () => {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: rect.height
        });
      };
      
      updateDimensions();
      const resizeObserver = new ResizeObserver(updateDimensions);
      resizeObserver.observe(containerRef.current);
      
      return () => resizeObserver.disconnect();
    }
  }, []);
  
  // Hide guide after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => setShowGuide(false), 5000);
    return () => clearTimeout(timer);
  }, []);
  
  // Professional color palette with proper contrast
  const getNodeColor = useCallback((node) => {
    const config = entityConfig[node.type] || entityConfig.Entity || {};
    const baseColor = config.color || '#6b7280';
    
    // Selected node - golden highlight
    if (selectedEntity === node.name) {
      return '#f59e0b';
    }
    
    // Highlighted nodes - full color
    if (highlightNodes.has(node.id)) {
      return baseColor;
    }
    
    // Non-highlighted when filtering - subtle gray
    if (highlightNodes.size > 0) {
      return '#e5e7eb';
    }
    
    return baseColor;
  }, [highlightNodes, selectedEntity, entityConfig]);
  
  // Professional link styling
  const getLinkColor = useCallback((link) => {
    const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(link);
    
    if (isHighlighted) {
      return 'rgba(99, 102, 241, 0.3)'; // Soft indigo
    }
    
    return 'rgba(203, 213, 225, 0.15)'; // Very subtle gray
  }, [highlightLinks]);
  
  const getLinkWidth = useCallback((link) => {
    const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(link);
    return isHighlighted ? 1.2 : 0.3;
  }, [highlightLinks]);
  
  // Enhanced node rendering with professional materials
  const nodeThreeObject = useCallback((node) => {
    const group = new THREE.Group();
    
    // Calculate node size based on importance
    const baseRadius = Math.sqrt((node.val || 5)) * 0.8;
    const isSelected = selectedEntity === node.name;
    const isHighlighted = highlightNodes.has(node.id);
    const radius = isSelected ? baseRadius * 1.3 : baseRadius;
    
    // Create sphere with professional material
    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const color = new THREE.Color(getNodeColor(node));
    
    // Use MeshStandardMaterial for PBR (Physically Based Rendering)
    const material = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color.clone().multiplyScalar(isSelected ? 0.4 : 0.1),
      metalness: 0.2,
      roughness: 0.4,
      transparent: true,
      opacity: (highlightNodes.size === 0 || isHighlighted) ? 0.95 : 0.3
    });
    
    const sphere = new THREE.Mesh(geometry, material);
    group.add(sphere);
    
    // Add selection ring for selected nodes
    if (isSelected) {
      const ringGeometry = new THREE.TorusGeometry(radius * 1.4, 0.15, 8, 32);
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: 0xf59e0b,
        transparent: true,
        opacity: 0.8
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.rotation.x = Math.PI / 2;
      group.add(ring);
      
      // Animate ring
      const animate = () => {
        ring.rotation.z += 0.01;
        requestAnimationFrame(animate);
      };
      animate();
    }
    
    // Add hover highlight
    if (hoverNode && hoverNode.id === node.id) {
      const glowGeometry = new THREE.SphereGeometry(radius * 1.2, 16, 16);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.2
      });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      group.add(glow);
    }
    
    return group;
  }, [highlightNodes, selectedEntity, getNodeColor, entityConfig, hoverNode]);
  
  // Camera controls
  const handleZoomIn = useCallback(() => {
    if (graphRef.current) {
      const camera = graphRef.current.camera();
      const currentDistance = camera.position.length();
      const newDistance = currentDistance * 0.7;
      camera.position.normalize().multiplyScalar(newDistance);
    }
  }, []);
  
  const handleZoomOut = useCallback(() => {
    if (graphRef.current) {
      const camera = graphRef.current.camera();
      const currentDistance = camera.position.length();
      const newDistance = currentDistance * 1.3;
      camera.position.normalize().multiplyScalar(newDistance);
    }
  }, []);
  
  const handleCenter = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(1000, 20);
    }
  }, []);
  
  const handleRefresh = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.d3ReheatSimulation();
    }
  }, []);
  
  const handleFullscreen = useCallback(() => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        containerRef.current.requestFullscreen();
      }
    }
  }, []);
  
  // Setup professional lighting
  useEffect(() => {
    if (graphRef.current) {
      const scene = graphRef.current.scene();
      
      // Clear existing lights
      scene.children.filter(child => 
        child.type === 'AmbientLight' || 
        child.type === 'DirectionalLight' ||
        child.type === 'PointLight'
      ).forEach(light => scene.remove(light));
      
      // Ambient light for base illumination
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
      scene.add(ambientLight);
      
      // Key light (main directional light)
      const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
      keyLight.position.set(5, 5, 5);
      scene.add(keyLight);
      
      // Fill light (softer, from opposite side)
      const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
      fillLight.position.set(-5, 0, -5);
      scene.add(fillLight);
      
      // Rim light (for depth)
      const rimLight = new THREE.DirectionalLight(0xffffff, 0.2);
      rimLight.position.set(0, -5, 0);
      scene.add(rimLight);
      
      // Professional gradient background
      scene.background = new THREE.Color(0xf8fafc);
      
      // Add subtle fog for depth perception
      scene.fog = new THREE.Fog(0xf8fafc, 500, 1500);
    }
  }, []);
  
  // Handle node hover
  const handleNodeHover = useCallback((node) => {
    setHoverNode(node);
    if (onNodeHover) {
      onNodeHover(node);
    }
    
    // Change cursor
    if (containerRef.current) {
      containerRef.current.style.cursor = node ? 'pointer' : 'default';
    }
  }, [onNodeHover]);
  
  return (
    <Box 
      ref={containerRef} 
      sx={{ 
        position: 'relative', 
        width, 
        height,
        borderRadius: 2,
        overflow: 'hidden',
        bgcolor: '#f8fafc',
        boxShadow: 'inset 0 0 20px rgba(0,0,0,0.05)'
      }}
    >
      {/* Interactive Guide Overlay */}
      <Fade in={showGuide} timeout={1000}>
        <Card
          sx={{
            position: 'absolute',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 15,
            px: 3,
            py: 2,
            bgcolor: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(10px)',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}
        >
          <MouseIcon sx={{ color: 'white', fontSize: 28 }} />
          <Box>
            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600, mb: 0.5 }}>
              Interactive 3D Controls
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
              🖱️ Drag to rotate • 🔍 Scroll to zoom • 👆 Click node to select
            </Typography>
          </Box>
        </Card>
      </Fade>
      
      {/* Professional Control Panel */}
      <Box
        sx={{
          position: 'absolute',
          top: 20,
          right: 20,
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          gap: 1
        }}
      >
        {[
          { icon: <ZoomInIcon />, tooltip: 'Zoom In', action: handleZoomIn },
          { icon: <ZoomOutIcon />, tooltip: 'Zoom Out', action: handleZoomOut },
          { icon: <CenterIcon />, tooltip: 'Center & Fit', action: handleCenter },
          { icon: <RefreshIcon />, tooltip: 'Restart Layout', action: handleRefresh },
          { icon: <FullscreenIcon />, tooltip: 'Toggle Fullscreen', action: handleFullscreen },
        ].map((control, idx) => (
          <Zoom in timeout={200 + idx * 100} key={idx}>
            <Tooltip title={control.tooltip} placement="left">
              <IconButton
                onClick={control.action}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    bgcolor: 'white',
                    transform: 'scale(1.1)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.15)'
                  },
                }}
              >
                {control.icon}
              </IconButton>
            </Tooltip>
          </Zoom>
        ))}
      </Box>
      
      {/* Professional Info Badge */}
      <Card
        sx={{
          position: 'absolute',
          bottom: 20,
          left: 20,
          zIndex: 10,
          px: 2.5,
          py: 1.5,
          bgcolor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 2,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <View3DIcon sx={{ color: '#6366f1', fontSize: 20 }} />
          <Box>
            <Typography variant="caption" sx={{ display: 'block', fontWeight: 700, color: '#1e293b', lineHeight: 1.2 }}>
              WebGL 3D Graph
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.7rem' }}>
              {graphData.nodes.length} entities • {graphData.links.length} relationships
            </Typography>
          </Box>
        </Box>
      </Card>
      
      {/* Entity Type Legend (Not Source Types) */}
      <Card
        sx={{
          position: 'absolute',
          bottom: 20,
          right: 20,
          zIndex: 10,
          px: 2.5,
          py: 2,
          maxWidth: 200,
          bgcolor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 2,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
        }}
      >
        <Typography variant="caption" sx={{ display: 'block', fontWeight: 700, color: '#1e293b', mb: 1.5 }}>
          Entity Types
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {Object.entries(entityConfig)
            .filter(([type]) => type !== 'Entity') // Exclude generic "Entity" type
            .map(([type, config]) => (
              <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: config.color,
                    boxShadow: `0 0 8px ${config.color}40`,
                    flexShrink: 0
                  }}
                />
                <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 500 }}>
                  {config.label || type}
                </Typography>
              </Box>
            ))}
        </Box>
      </Card>
      
      {/* 3D Force Graph with Professional Settings */}
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        nodeLabel={node => `
          <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95)); color: white; padding: 12px 16px; border-radius: 8px; font-family: 'Inter', -apple-system, sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-weight: 700; font-size: 13px; margin-bottom: 8px; color: ${getNodeColor(node)};">${node.name}</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-bottom: 4px;">
              <span style="color: rgba(255,255,255,0.5);">Type:</span> ${node.type}
            </div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.7);">
              <span style="color: rgba(255,255,255,0.5);">Sources:</span> ${node.source_count || 1} document${(node.source_count || 1) !== 1 ? 's' : ''}
            </div>
          </div>
        `}
        nodeThreeObject={nodeThreeObject}
        nodeVal={node => node.val || 5}
        nodeColor={getNodeColor}
        nodeOpacity={1}
        linkColor={getLinkColor}
        linkWidth={getLinkWidth}
        linkOpacity={0.6}
        linkDirectionalParticles={link => {
          const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(link);
          return isHighlighted ? 2 : 0;
        }}
        linkDirectionalParticleWidth={2.5}
        linkDirectionalParticleSpeed={0.004}
        linkDirectionalParticleColor={() => 'rgba(99, 102, 241, 0.8)'}
        onNodeClick={onNodeClick}
        onNodeHover={handleNodeHover}
        enableNodeDrag={true}
        enableNavigationControls={true}
        showNavInfo={false}
        // Physics configuration for smooth, natural movement
        d3AlphaDecay={0.015}
        d3VelocityDecay={0.25}
        d3Force={{
          charge: { strength: -180, distanceMax: 400 },
          link: { distance: 60, strength: 0.5 },
          center: { strength: 0.01 }
        }}
        warmupTicks={100}
        cooldownTicks={0}
        cooldownTime={15000}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="#f8fafc"
        // Camera configuration
        cameraPosition={{ x: 0, y: 0, z: 400 }}
      />
    </Box>
  );
};

export default WebGLKnowledgeGraph;
