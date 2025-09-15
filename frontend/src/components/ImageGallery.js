import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Tooltip,
  Badge,
  Paper,
  Stack,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Close as CloseIcon,
  ZoomIn as ZoomInIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  ImageSearch as ImageSearchIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

const ImageGallery = ({ 
  images = [], 
  loading = false, 
  onImageClick, 
  onEntityClick,
  compact = false 
}) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [hoveredImage, setHoveredImage] = useState(null);

  const handleImageClick = (image) => {
    setSelectedImage(image);
    if (onImageClick) {
      onImageClick(image);
    }
  };

  const handleCloseDialog = () => {
    setSelectedImage(null);
  };

  const getImageTypeColor = (imageType) => {
    const typeColors = {
      'chart': '#2196F3',
      'diagram': '#4CAF50', 
      'signature': '#FF9800',
      'seal': '#9C27B0',
      'medical': '#F44336',
      'legal': '#795548',
      'table': '#607D8B',
      'photo': '#3F51B5',
      'other': '#9E9E9E'
    };
    return typeColors[imageType] || typeColors.other;
  };

  const getEntityTypeColor = (entityType) => {
    const colors = {
      'PERSON': '#e3f2fd',
      'ORGANIZATION': '#f3e5f5', 
      'LOCATION': '#e8f5e8',
      'DATE': '#fff3e0',
      'MEDICAL': '#ffebee',
      'LEGAL': '#f1f8e9',
      'OTHER': '#fafafa'
    };
    return colors[entityType] || colors.OTHER;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading images...
        </Typography>
      </Box>
    );
  }

  if (!images || images.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
        <ImageSearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No Images Found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This document doesn't contain any extracted images
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Grid container spacing={compact ? 1 : 2}>
        {images.map((image, index) => (
          <Grid item xs={compact ? 6 : 4} md={compact ? 4 : 3} key={image.image_id || index}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 4
                }
              }}
              onMouseEnter={() => setHoveredImage(image)}
              onMouseLeave={() => setHoveredImage(null)}
              onClick={() => handleImageClick(image)}
            >
              {/* Image Preview */}
              <Box position="relative">
                <CardMedia
                  component="img"
                  height={compact ? 120 : 160}
                  image={image.preview_url || image.storage_url || '/placeholder-image.png'}
                  alt={image.analysis || 'Extracted image'}
                  sx={{ 
                    objectFit: 'cover',
                    backgroundColor: '#f5f5f5'
                  }}
                />
                
                {/* Image Type Badge */}
                <Chip
                  label={image.image_type || 'Unknown'}
                  size="small"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    backgroundColor: getImageTypeColor(image.image_type),
                    color: 'white',
                    fontSize: '0.7rem'
                  }}
                />

                {/* Entity Count Badge */}
                {image.entities && image.entities.length > 0 && (
                  <Badge 
                    badgeContent={image.entities.length} 
                    color="primary"
                    sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      '& .MuiBadge-badge': {
                        fontSize: '0.7rem'
                      }
                    }}
                  >
                    <AnalyticsIcon sx={{ color: 'white', fontSize: 20 }} />
                  </Badge>
                )}

                {/* Hover Overlay */}
                {hoveredImage === image && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: 'rgba(0,0,0,0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <ZoomInIcon sx={{ color: 'white', fontSize: 32 }} />
                  </Box>
                )}
              </Box>

              {/* Content */}
              {!compact && (
                <CardContent sx={{ p: 1.5 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {image.page_number ? `Page ${image.page_number}` : 'Unknown page'}
                  </Typography>
                  
                  {image.analysis && (
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        mt: 0.5,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical'
                      }}
                    >
                      {image.analysis}
                    </Typography>
                  )}

                  {/* Entity Chips */}
                  {image.entities && image.entities.length > 0 && (
                    <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap' }}>
                      {image.entities.slice(0, 2).map((entity, idx) => (
                        <Chip
                          key={idx}
                          label={entity.text || entity.name}
                          size="small"
                          variant="outlined"
                          sx={{
                            fontSize: '0.7rem',
                            height: 20,
                            backgroundColor: getEntityTypeColor(entity.type),
                            '&:hover': {
                              backgroundColor: getEntityTypeColor(entity.type),
                              filter: 'brightness(0.9)'
                            },
                            cursor: 'pointer'
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onEntityClick) {
                              onEntityClick(entity);
                            }
                          }}
                        />
                      ))}
                      {image.entities.length > 2 && (
                        <Chip
                          label={`+${image.entities.length - 2}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Stack>
                  )}
                </CardContent>
              )}
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Image Detail Dialog */}
      <Dialog 
        open={!!selectedImage} 
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        {selectedImage && (
          <>
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6">
                  Image Analysis - Page {selectedImage.page_number || 'Unknown'}
                </Typography>
                <Chip 
                  label={selectedImage.image_type || 'Unknown Type'}
                  size="small"
                  sx={{
                    backgroundColor: getImageTypeColor(selectedImage.image_type),
                    color: 'white',
                    mt: 1
                  }}
                />
              </Box>
              <Box>
                <Tooltip title="Download">
                  <IconButton onClick={() => {/* Handle download */}}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <IconButton onClick={handleCloseDialog}>
                  <CloseIcon />
                </IconButton>
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Grid container spacing={3}>
                {/* Image */}
                <Grid item xs={12} md={6}>
                  <Box
                    component="img"
                    src={selectedImage.preview_url || selectedImage.storage_url || '/placeholder-image.png'}
                    alt="Selected image"
                    sx={{
                      width: '100%',
                      height: 'auto',
                      maxHeight: 400,
                      objectFit: 'contain',
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1
                    }}
                  />
                </Grid>

                {/* Analysis */}
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    AI Analysis
                  </Typography>
                  
                  {selectedImage.analysis && (
                    <Typography variant="body2" paragraph>
                      {selectedImage.analysis}
                    </Typography>
                  )}

                  {selectedImage.text_content && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Extracted Text:
                      </Typography>
                      <Paper elevation={1} sx={{ p: 2, backgroundColor: '#f8f9fa' }}>
                        <Typography variant="body2" fontFamily="monospace">
                          {selectedImage.text_content}
                        </Typography>
                      </Paper>
                    </Box>
                  )}

                  {selectedImage.entities && selectedImage.entities.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Extracted Entities:
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        {selectedImage.entities.map((entity, idx) => (
                          <Chip
                            key={idx}
                            label={`${entity.text || entity.name} (${entity.type})`}
                            size="small"
                            sx={{
                              backgroundColor: getEntityTypeColor(entity.type),
                              mb: 1,
                              cursor: 'pointer'
                            }}
                            onClick={() => {
                              if (onEntityClick) {
                                onEntityClick(entity);
                              }
                            }}
                          />
                        ))}
                      </Stack>
                    </Box>
                  )}

                  {selectedImage.key_elements && selectedImage.key_elements.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Key Elements:
                      </Typography>
                      <ul style={{ paddingLeft: 20 }}>
                        {selectedImage.key_elements.map((element, idx) => (
                          <li key={idx}>
                            <Typography variant="body2">
                              {element}
                            </Typography>
                          </li>
                        ))}
                      </ul>
                    </Box>
                  )}

                  {selectedImage.confidence && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Analysis Confidence: {Math.round(selectedImage.confidence * 100)}%
                      </Typography>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default ImageGallery;