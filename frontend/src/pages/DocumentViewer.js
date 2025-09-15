import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  LocalHospital as MedicalIcon,
  Science as ScienceIcon,
  Gavel as LegalIcon,
  CalendarToday as DateIcon,
  AttachMoney as MoneyIcon,
  Article as ClauseIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useParams } from 'react-router-dom';
import { apiService } from '../services/api';
import ImageGallery from '../components/ImageGallery';

// Entity type icon mapping
const getEntityIcon = (entityType) => {
  const icons = {
    'PERSON': <PersonIcon />,
    'ORGANIZATION': <BusinessIcon />,
    'LOCATION': <LocationIcon />,
    'DRUG': <MedicalIcon />,
    'DISEASE': <MedicalIcon />,
    'TREATMENT': <MedicalIcon />,
    'REGULATION': <LegalIcon />,
    'DATE': <DateIcon />,
    'MONEY': <MoneyIcon />,
    'CONCEPT': <ScienceIcon />,
    // Legal clause types
    'LEGAL_PARTY': <PersonIcon />,
    'LEGAL_DATE': <DateIcon />,
    'LEGAL_JURISDICTION': <LocationIcon />,
    'LEGAL_TERMINATION': <LegalIcon />,
    'LEGAL_NON_COMPETE': <LegalIcon />,
    'LEGAL_CONFIDENTIALITY': <DocumentIcon />,
    'LEGAL_IP': <ScienceIcon />,
    'LEGAL_LIABILITY': <LegalIcon />,
    'LEGAL_PAYMENT': <MoneyIcon />,
    'LEGAL_FORCE_MAJEURE': <LegalIcon />,
  };
  return icons[entityType] || <ScienceIcon />;
};

// Entity type color mapping
const getEntityColor = (entityType) => {
  const colors = {
    'PERSON': 'primary',
    'ORGANIZATION': 'secondary',
    'LOCATION': 'success',
    'DRUG': 'warning',
    'DISEASE': 'error',
    'TREATMENT': 'info',
    'REGULATION': 'default',
    'DATE': 'primary',
    'MONEY': 'secondary',
    'CONCEPT': 'default',
    // Legal clause colors
    'LEGAL_PARTY': 'primary',
    'LEGAL_DATE': 'primary',
    'LEGAL_JURISDICTION': 'success',
    'LEGAL_TERMINATION': 'error',
    'LEGAL_NON_COMPETE': 'warning',
    'LEGAL_CONFIDENTIALITY': 'info',
    'LEGAL_IP': 'secondary',
    'LEGAL_LIABILITY': 'error',
    'LEGAL_PAYMENT': 'secondary',
    'LEGAL_FORCE_MAJEURE': 'warning',
  };
  return colors[entityType] || 'default';
};

function DocumentViewer() {
  const { documentId } = useParams();
  
  // Fetch document details
  const { data: document, isLoading, error } = useQuery(
    ['document', documentId],
    () => apiService.getDocument(documentId),
    {
      enabled: !!documentId,
      staleTime: 300000, // 5 minutes
    }
  );

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
        Failed to load document: {error.message}
      </Alert>
    );
  }

  if (!document) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        Document not found
      </Alert>
    );
  }

  const entities = document.openai_entities || [];
  const relationships = document.relationships || [];
  const legalClauses = document.legal_clauses || [];
  const clauseContexts = document.clause_contexts || [];
  const insights = document.document_insights || {};
  const highlightedContent = document.highlighted_content || document.content;

  return (
    <Box sx={{ p: 3 }}>
      {/* Document Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {document.title}
        </Typography>
        
        {document.ai_summary && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold">AI Summary:</Typography>
            <Typography variant="body2">{document.ai_summary}</Typography>
          </Alert>
        )}

        {/* Categories and Tags */}
        <Box sx={{ mb: 2 }}>
          {document.categories?.map((category) => (
            <Chip
              key={category}
              label={category}
              color="primary"
              variant="outlined"
              size="small"
              sx={{ mr: 1, mb: 1 }}
            />
          ))}
        </Box>

        {/* Document Insights */}
        {insights.main_themes && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Main Themes:</Typography>
            {insights.main_themes.map((theme, index) => (
              <Chip
                key={index}
                label={theme}
                color="secondary"
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>
        )}
      </Paper>

      <Grid container spacing={3}>
        {/* Document Content with Highlighted Entities */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Document Content
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box
              sx={{
                '& .entity': {
                  padding: '2px 4px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    transform: 'scale(1.05)',
                    boxShadow: 1,
                  },
                },
                '& .entity-person': { backgroundColor: '#e3f2fd', border: '1px solid #2196f3' },
                '& .entity-organization': { backgroundColor: '#f3e5f5', border: '1px solid #9c27b0' },
                '& .entity-location': { backgroundColor: '#e8f5e8', border: '1px solid #4caf50' },
                '& .entity-drug': { backgroundColor: '#fff3e0', border: '1px solid #ff9800' },
                '& .entity-disease': { backgroundColor: '#ffebee', border: '1px solid #f44336' },
                '& .entity-treatment': { backgroundColor: '#e1f5fe', border: '1px solid #03a9f4' },
                '& .entity-regulation': { backgroundColor: '#f5f5f5', border: '1px solid #757575' },
                '& .entity-date': { backgroundColor: '#e8eaf6', border: '1px solid #3f51b5' },
                '& .entity-money': { backgroundColor: '#f1f8e9', border: '1px solid #8bc34a' },
                '& .entity-concept': { backgroundColor: '#fafafa', border: '1px solid #9e9e9e' },
                // Legal clause highlighting
                '& .entity-legal-party': { backgroundColor: '#e3f2fd', border: '2px solid #2196f3', fontWeight: 'bold' },
                '& .entity-legal-date': { backgroundColor: '#e8eaf6', border: '2px solid #3f51b5', fontWeight: 'bold' },
                '& .entity-legal-jurisdiction': { backgroundColor: '#e8f5e8', border: '2px solid #4caf50', fontWeight: 'bold' },
                '& .entity-legal-termination': { backgroundColor: '#ffebee', border: '2px solid #f44336', fontWeight: 'bold' },
                '& .entity-legal-non-compete': { backgroundColor: '#fff3e0', border: '2px solid #ff9800', fontWeight: 'bold' },
                '& .entity-legal-confidentiality': { backgroundColor: '#e1f5fe', border: '2px solid #03a9f4', fontWeight: 'bold' },
                '& .entity-legal-ip': { backgroundColor: '#f3e5f5', border: '2px solid #9c27b0', fontWeight: 'bold' },
                '& .entity-legal-liability': { backgroundColor: '#ffebee', border: '2px solid #f44336', fontWeight: 'bold' },
                '& .entity-legal-payment': { backgroundColor: '#f1f8e9', border: '2px solid #8bc34a', fontWeight: 'bold' },
                '& .entity-legal-force-majeure': { backgroundColor: '#fff3e0', border: '2px solid #ff9800', fontWeight: 'bold' },
                lineHeight: 1.6,
                fontSize: '16px',
              }}
              dangerouslySetInnerHTML={{ __html: highlightedContent }}
            />
          </Paper>
        </Grid>

        {/* Entities and Relationships Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Extracted Entities */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                AI-Extracted Entities ({entities.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {entities.map((entity, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {getEntityIcon(entity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={entity.text}
                      secondary={
                        <Box>
                          <Chip
                            label={entity.type}
                            color={getEntityColor(entity.type)}
                            size="small"
                            sx={{ mr: 1 }}
                          />
                          {entity.confidence && (
                            <Typography variant="caption" color="text.secondary">
                              Confidence: {(entity.confidence * 100).toFixed(0)}%
                            </Typography>
                          )}
                          {entity.description && (
                            <Typography variant="body2" color="text.secondary">
                              {entity.description}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>

          {/* Relationships */}
          {relationships.length > 0 && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">
                  Entity Relationships ({relationships.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {relationships.map((rel, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={`${rel.source_entity} → ${rel.target_entity}`}
                        secondary={
                          <Box>
                            <Chip
                              label={rel.relationship_type}
                              size="small"
                              variant="outlined"
                              sx={{ mb: 1 }}
                            />
                            {rel.description && (
                              <Typography variant="body2" color="text.secondary">
                                {rel.description}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Legal Clauses */}
          {legalClauses.length > 0 && (
            <Accordion sx={{ mt: 2 }} defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">
                  Legal Clauses ({legalClauses.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {legalClauses.map((clause, index) => (
                    <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                      <Box sx={{ width: '100%', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <ListItemIcon sx={{ minWidth: 'auto', mr: 1 }}>
                            <ClauseIcon />
                          </ListItemIcon>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {clause.clause_name}
                          </Typography>
                          <Chip
                            label={clause.type}
                            color={getEntityColor(clause.type)}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                          {clause.confidence && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              {(clause.confidence * 100).toFixed(0)}%
                            </Typography>
                          )}
                        </Box>
                        <Typography variant="body2" sx={{ 
                          fontStyle: 'italic', 
                          backgroundColor: 'grey.50', 
                          p: 1, 
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'grey.200',
                          mb: 1
                        }}>
                          "{clause.text}"
                        </Typography>
                        {clause.paragraph_context && (
                          <Typography variant="caption" color="text.secondary">
                            Context: {clause.paragraph_context.substring(0, 200)}...
                          </Typography>
                        )}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Document Insights */}
          {Object.keys(insights).length > 0 && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Document Insights</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  {insights.document_type && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Document Type:</Typography>
                      <Chip label={insights.document_type} size="small" />
                    </Box>
                  )}

                  {insights.sentiment && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Sentiment:</Typography>
                      <Chip 
                        label={insights.sentiment} 
                        size="small"
                        color={insights.sentiment === 'positive' ? 'success' : 
                               insights.sentiment === 'negative' ? 'error' : 'default'}
                      />
                    </Box>
                  )}

                  {insights.key_findings && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Key Findings:</Typography>
                      {insights.key_findings.map((finding, index) => (
                        <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                          • {finding}
                        </Typography>
                      ))}
                    </Box>
                  )}

                  {insights.risk_factors && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Risk Factors:</Typography>
                      {insights.risk_factors.map((risk, index) => (
                        <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                          • {risk}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </Grid>

        {/* Images Section - Full Width */}
        {document.stored_images && document.stored_images.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Extracted Images ({document.stored_images.length})
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <ImageGallery 
                images={document.stored_images.map(img => ({
                  ...img,
                  // Map the stored image format to gallery format
                  preview_url: img.storage_url || `/api/v1/documents/${documentId}/images/${img.image_id}`,
                  entities: document.image_entities?.filter(e => 
                    e.image_id === img.image_id || 
                    e.page_number === img.page_number
                  ) || [],
                  analysis: img.analysis || 'AI analysis not available',
                  image_type: img.image_type || 'unknown'
                }))}
                onImageClick={(image) => console.log('Image clicked:', image)}
                onEntityClick={(entity) => console.log('Entity clicked:', entity)}
              />
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

export default DocumentViewer;