import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  CircularProgress,
  Alert,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
  DialogContentText,
  InputAdornment,
  Tabs,
  Tab,
  Paper,
  Divider,
  Stack,
  FormControl,
  InputLabel,
  Select,
  Grid,
  useTheme,
  alpha
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import {
  Description as DocumentIcon,
  MoreVert as MoreIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  CalendarToday as CalendarIcon,
  LocalOffer as TagIcon,
  Visibility as VisibilityIcon,
  Assignment as AssignmentIcon,
  Warning as WarningIcon,
  Science as ScienceIcon,
  Article as ArticleIcon,
  Block as BlockIcon,
  VerifiedUser as VerifiedIcon
} from '@mui/icons-material';
import apiService from '../services/api';





// Tab Panel Component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`documents-tabpanel-${index}`}
      aria-labelledby={`documents-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function EnhancedDocuments() {
  const theme = useTheme();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  
  // New states for search and view modes
  const [activeTab, setActiveTab] = useState(0); // 0: Browse, 1: Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // table or grid
  const [sortBy, setSortBy] = useState('relevance');
  const [classificationFilter, setClassificationFilter] = useState('all'); // Filter by PV classification
  
  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({ title: '', tags: '' });
  
  // Snackbar for notifications
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Fetch documents from API - CRITICAL MISSING FUNCTIONALITY
  const { data: documentsData, isLoading, error, refetch } = useQuery(
    ['documents', page, pageSize], // Simple query key based on page and pageSize
    () => {
      console.log('🔄 Fetching documents - Page:', page, 'PageSize:', pageSize, 'From:', page * pageSize);
      return apiService.getDocuments(page, pageSize);
    },
    {
      staleTime: 0, // No caching to ensure fresh data on pagination
      cacheTime: 0, // Don't cache at all
      refetchOnWindowFocus: false, // Don't refetch on focus to avoid confusion
      keepPreviousData: false, // Don't keep previous data - show loading instead
      enabled: activeTab === 0, // Only fetch when in browse mode
      refetchInterval: false, // Disable auto-refetch during pagination testing
      retry: 1, // Only retry once
    }
  );

  // Extract documents and total count (normalize PV classification fields)
  const allDocuments = (documentsData?.results || []).map(hit => {
    const src = hit._source || {};
    const icsr = src.icsr_classification || {};
    // Prefer already-transformed flat fields, but fallback to nested icsr_classification
    const classification = src.classification ?? icsr.classification ?? null;
    const classification_confidence =
      src.classification_confidence ?? icsr.confidence ?? null;
    const classification_entities =
      src.classification_entities ?? icsr.key_entities ?? [];
    const classification_reasoning =
      src.classification_reasoning ?? icsr.reasoning ?? null;
    const classification_cost = src.classification_cost ?? icsr.cost ?? 0;

    return {
      ...src,
      classification,
      classification_confidence,
      classification_entities,
      classification_reasoning,
      classification_cost,
      id: hit._id,
    };
  });
  const totalDocuments = documentsData?.total || 0;
  
  // Apply classification filter
  const documents = classificationFilter === 'all' 
    ? allDocuments 
    : allDocuments.filter(doc => doc.classification === classificationFilter);
  
  // Menu handling
  const handleMenuOpen = (event, doc) => {
    setAnchorEl(event.currentTarget);
    setSelectedDoc(doc);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDoc(null);
  };

  // Search functionality
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await apiService.searchDocuments(searchQuery, { size: 50, from: 0 });
      setSearchResults(results.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSnackbar({ open: true, message: 'Search failed', severity: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
  };

  // Tab handling
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Menu click handler (alias for handleMenuOpen to match the columns definition)
  const handleMenuClick = handleMenuOpen;

  // Edit and delete handlers - see implementation below





  // Action handlers
  const handleView = (doc) => {
    handleMenuClose();
    navigate(`/document/${doc.id}`);
  };

  const handleDownload = async (doc) => {
    handleMenuClose();
    try {
      const response = await apiService.downloadDocument(doc.id);
      
      // Create blob and download
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${doc.title || 'document'}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setSnackbar({ open: true, message: 'Document downloaded successfully!', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to download document', severity: 'error' });
    }
  };

  const handleEdit = (doc) => {
    setEditFormData({ 
      title: doc.title || '',
      tags: doc.tags ? doc.tags.join(', ') : ''
    });
    setEditDialogOpen(true);
    // Don't close menu yet - keep selectedDoc until after edit
  };

  const handleDelete = (doc) => {
    setDeleteDialogOpen(true);
    // Don't close menu yet - keep selectedDoc until after deletion
  };

  const confirmEdit = async () => {
    try {
      console.log('Edit button clicked for document:', selectedDoc);
      
      if (!selectedDoc || !selectedDoc.id) {
        throw new Error('No document selected for editing');
      }
      
      const updateData = {
        title: editFormData.title,
        tags: editFormData.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      };
      
      await apiService.updateDocument(selectedDoc.id, updateData);
      setEditDialogOpen(false);
      handleMenuClose(); // Close menu after successful edit
      setSnackbar({ open: true, message: 'Document updated successfully!', severity: 'success' });
      refetch(); // Refresh the documents list
    } catch (error) {
      console.error('Edit operation failed:', error);
      setEditDialogOpen(false);
      handleMenuClose(); // Close menu on error too
      setSnackbar({ open: true, message: error.message || 'Failed to update document', severity: 'error' });
    }
  };

  const confirmDelete = async () => {
    try {
      console.log('Delete button clicked for document:', selectedDoc);
      
      if (!selectedDoc || !selectedDoc.id) {
        throw new Error('No document selected for deletion');
      }
      
      await apiService.deleteDocument(selectedDoc.id);
      setDeleteDialogOpen(false);
      handleMenuClose(); // Close menu after successful deletion
      setSnackbar({ open: true, message: 'Document deleted successfully!', severity: 'success' });
      refetch(); // Refresh the documents list
    } catch (error) {
      console.error('Delete operation failed:', error);
      setDeleteDialogOpen(false);
      handleMenuClose(); // Close menu on error too
      setSnackbar({ open: true, message: error.message || 'Failed to delete document', severity: 'error' });
    }
  };

  // Render search results in card format
  const renderSearchResults = () => (
    <Box sx={{ p: 2 }}>
      {isSearching ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : searchResults.length > 0 ? (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {searchResults.length} results for "{searchQuery}"
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {searchResults.map((result) => {
              // result is already transformed by apiService.searchDocuments
              const content = result.content || '';
              const cleanContent = content
                .replace(/=== PAGE \d+ ===/g, '')
                .replace(/---END PAGE \d+---/g, '')
                .replace(/\n{2,}/g, '\n')
                .trim();
              const preview = cleanContent.substring(0, 300);
              
              return (
                <Card key={result.id} sx={{ cursor: 'pointer', position: 'relative' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="h6" color="primary" sx={{ fontWeight: 600 }}>
                        {result.title || 'Untitled Document'}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {result.file_type && (
                          <Chip label={result.file_type} size="small" variant="outlined" />
                        )}
                        {result.extraction_method && (
                          <Chip 
                            label={result.extraction_method} 
                            size="small" 
                            color={result.extraction_method.includes('llava') || result.extraction_method.includes('llamaparse') ? 'primary' : 'default'}
                          />
                        )}
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.6 }}>
                      {preview}{cleanContent.length > 300 ? '...' : ''}
                    </Typography>
                    
                    {result.metadata?.openai_entities && result.metadata.openai_entities.length > 0 && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                          Entities ({result.metadata.openai_entities.length}):
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {result.metadata.openai_entities.slice(0, 5).map((entity, idx) => (
                            <Chip 
                              key={idx}
                              label={entity.text}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          ))}
                          {result.metadata.openai_entities.length > 5 && (
                            <Typography variant="caption" color="text.secondary">
                              +{result.metadata.openai_entities.length - 5} more
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    )}
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        {result.created_at ? new Date(result.created_at).toLocaleDateString() : 'Unknown date'}
                      </Typography>
                      {result.score && (
                        <Typography variant="caption" color="primary">
                          Relevance: {Math.round(result.score * 10) / 10}
                        </Typography>
                      )}
                    </Box>
                    
                    {/* Professional Action Buttons */}
                    <Box sx={{ 
                      display: 'flex', 
                      gap: 1, 
                      mt: 2, 
                      pt: 2, 
                      borderTop: '1px solid rgba(0,0,0,0.08)',
                      '& .MuiButton-root': {
                        fontSize: '0.75rem',
                        py: 0.5,
                        px: 1.5
                      }
                    }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<VisibilityIcon />}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/document/${result.id}`);
                        }}
                        sx={{ flex: 1 }}
                      >
                        Standard View
                      </Button>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<AssignmentIcon />}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/professional-document/${result.id}`);
                        }}
                        sx={{ 
                          flex: 1,
                          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
                          '&:hover': {
                            background: 'linear-gradient(135deg, #6C757D 0%, #495057 100%)'
                          }
                        }}
                      >
                        Professional
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        </Box>
      ) : searchQuery ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No documents found for "{searchQuery}"
          </Typography>
          <Button onClick={clearSearch} sx={{ mt: 2 }}>
            Clear Search
          </Button>
        </Box>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Start your search
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Enter keywords, ask questions, or describe what you're looking for.
          </Typography>
        </Box>
      )}
    </Box>
  );

  // PV Classification Config
  const pvClassificationConfig = {
    'ICSR': { 
      icon: <WarningIcon />, 
      color: '#d32f2f', 
      bgColor: '#ffebee',
      label: 'ICSR',
      description: 'Individual Case Safety Report'
    },
    'Safety_Information': { 
      icon: <ScienceIcon />, 
      color: '#1976d2', 
      bgColor: '#e3f2fd',
      label: 'Safety Info',
      description: 'Safety Information'
    },
    'Non-ICSR': { 
      icon: <ArticleIcon />, 
      color: '#0288d1', 
      bgColor: '#e1f5fe',
      label: 'Non-ICSR',
      description: 'General Medical Literature'
    },
    'Rejected': { 
      icon: <BlockIcon />, 
      color: '#757575', 
      bgColor: '#f5f5f5',
      label: 'Rejected',
      description: 'Not Relevant for PV'
    }
  };

  const getPVClassificationConfig = (classification) => {
    return pvClassificationConfig[classification] || null;
  };

  // Balanced Theme - Gray backgrounds with vibrant content colors
  const documentTypeConfig = {
    pdf: { icon: '📄', color: '#e53e3e', bgColor: '#F8F9FA', lightColor: '#fed7d7' },
    docx: { icon: '📝', color: '#3182ce', bgColor: '#F8F9FA', lightColor: '#bee3f8' },
    txt: { icon: '📋', color: '#38a169', bgColor: '#F8F9FA', lightColor: '#c6f6d5' },
    default: { icon: '📄', color: '#718096', bgColor: '#F8F9FA', lightColor: '#edf2f7' }
  };

  const getDocumentTypeConfig = (fileType) => {
    return documentTypeConfig[fileType?.toLowerCase()] || documentTypeConfig.default;
  };

  const getProcessingBadgeColor = (method) => {
    if (method?.includes('llava') || method?.includes('llamaparse')) return 'primary';
    if (method?.includes('openai')) return 'secondary';
    return 'default';
  };

  // Enhanced Document Card Component
  const DocumentCard = ({ document, onClick, onMenuClick }) => {
    const typeConfig = getDocumentTypeConfig(document.file_type);
    const processingColor = getProcessingBadgeColor(document.extraction_method);
    const pvConfig = getPVClassificationConfig(document.classification);
    
    // Debug logging for classification data
    if (document.classification) {
      console.log('🔍 Document Classification Debug:', {
        title: document.title,
        classification: document.classification,
        confidence: document.classification_confidence,
        entities: document.classification_entities,
        pvConfig: pvConfig
      });
    }
    
    return (
      <Card
        sx={{
          height: pvConfig ? 420 : 360, // Taller for PV classified documents
          display: 'flex',
          flexDirection: 'column',
          cursor: 'pointer',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          overflow: 'hidden',
          border: pvConfig ? `2px solid ${pvConfig.color}40` : 'none',
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: pvConfig 
              ? `0 20px 40px ${pvConfig.color}30`
              : '0 20px 40px rgba(0,0,0,0.12)',
            '& .document-actions': {
              opacity: 1,
              transform: 'translateY(0)'
            }
          }
        }}
        onClick={() => onClick(document)}
      >
        {/* Document Header with Subtle Gray Identity */}
        <Box
          sx={{
            height: 120,
            background: `linear-gradient(135deg, ${typeConfig.bgColor} 0%, ${typeConfig.lightColor} 100%)`,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `2px solid ${typeConfig.lightColor}`,
            borderTop: `1px solid ${typeConfig.lightColor}`
          }}
        >
          {/* Document Type Icon */}
          <Typography
            sx={{
              fontSize: '3rem',
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
            }}
          >
            {typeConfig.icon}
            </Typography>
          
          {/* File Type Badge */}
          <Chip
            label={document.file_type?.toUpperCase()}
            size="small"
            sx={{
              position: 'absolute',
              top: 12,
              right: 12,
              backgroundColor: typeConfig.color,
              color: 'white',
              fontWeight: 600,
              fontSize: '0.7rem'
            }}
          />
          
          {/* Processing Status Badge - Hide technical extraction methods */}
          {document.extraction_method && 
           !document.extraction_method.includes('official_llava_text_only') && 
           !document.extraction_method.includes('pymupdf') && (
            <Chip
              label={
                document.extraction_method.includes('llava') ? 'AI Enhanced' :
                document.extraction_method.includes('llamaparse') ? 'AI Parsed' :
                document.extraction_method.includes('openai') ? 'AI Processed' :
                'Processed'
              }
              size="small"
              color={processingColor}
              variant="outlined"
              sx={{
                position: 'absolute',
                top: 12,
                left: 12,
                backgroundColor: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(4px)',
                fontSize: '0.65rem'
              }}
            />
          )}
        </Box>

        {/* Document Content */}
        <CardContent sx={{ flexGrow: 1, p: 2, pb: 1 }}>
          {/* Title */}
          <Typography
            variant="h6"
            sx={{
              mb: 1,
              fontWeight: 600,
              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
              lineHeight: 1.3,
              color: '#1a202c', // Restored original dark text color
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              minHeight: '2.6em',
              letterSpacing: '-0.01em'
            }}
          >
            {document.title || 'Untitled Document'}
            </Typography>

          {/* PV Classification Badge */}
          {pvConfig && (
            <Box sx={{ mb: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Tooltip title={`${pvConfig.description} • Confidence: ${Math.round((document.classification_confidence || 0) * 100)}%`}>
                  <Chip
                    icon={pvConfig.icon}
                    label={`${pvConfig.label} (${Math.round((document.classification_confidence || 0) * 100)}%)`}
                    sx={{
                      backgroundColor: pvConfig.bgColor,
                      color: pvConfig.color,
                      fontWeight: 700,
                      fontSize: '0.75rem',
                      border: `1.5px solid ${pvConfig.color}`,
                      '& .MuiChip-icon': {
                        color: pvConfig.color
                      }
                    }}
                  />
                </Tooltip>
                
                {/* Ensemble Metadata - NEW */}
                {document.ensemble_models_used && document.ensemble_models_used.length > 0 && (
                  <Tooltip title={`Models: ${document.ensemble_models_used.join(' → ')}`}>
                    <Chip
                      label={`⚡ ${document.ensemble_models_used.length} model${document.ensemble_models_used.length > 1 ? 's' : ''}`}
                      size="small"
                      sx={{
                        backgroundColor: '#f3e5f5',
                        color: '#7b1fa2',
                        fontSize: '0.7rem',
                        fontWeight: 600
                      }}
                    />
                  </Tooltip>
                )}
                
                {document.processing_time_ms && (
                  <Tooltip title={`Processing time: ${document.processing_time_ms}ms`}>
                    <Chip
                      label={`${(document.processing_time_ms / 1000).toFixed(1)}s`}
                      size="small"
                      sx={{
                        backgroundColor: '#e3f2fd',
                        color: '#1976d2',
                        fontSize: '0.7rem',
                        fontWeight: 600
                      }}
                    />
                  </Tooltip>
                )}
                
                {document.classification_cost !== undefined && (
                  <Tooltip title={`Classification cost: $${document.classification_cost.toFixed(4)}`}>
                    <Chip
                      label={document.classification_cost === 0 ? 'Free' : `$${document.classification_cost.toFixed(4)}`}
                      size="small"
                      sx={{
                        backgroundColor: document.classification_cost === 0 ? '#e8f5e9' : '#fff3e0',
                        color: document.classification_cost === 0 ? '#2e7d32' : '#e65100',
                        fontSize: '0.7rem',
                        fontWeight: 600
                      }}
                    />
                  </Tooltip>
                )}
              </Box>
          </Box>
          )}

          {/* Metadata Row */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
            <Chip
              icon={<CalendarIcon />}
              label={document.created_at ? new Date(document.created_at).toLocaleDateString() : 'Unknown'}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
            {document.entities && (
              <Chip
                icon={<TagIcon />}
                label={`${document.entities} entities`}
                size="small"
                variant="outlined"
                color="secondary"
                sx={{ fontSize: '0.7rem' }}
              />
            )}
        </Box>

          {/* Content Preview */}
          {document.content && (
            <Typography
              variant="body2"
              sx={{
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                lineHeight: 1.5,
                mb: 1,
                color: '#4a5568', // Restored original secondary text color
                fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                fontSize: '0.875rem'
              }}
            >
              {document.content.substring(0, 150)}...
            </Typography>
          )}

          {/* Classification Entities - Highlighted entities used by model */}
          {pvConfig && document.classification_entities && document.classification_entities.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
                🎯 Classification Evidence:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {document.classification_entities.slice(0, 3).map((entity, idx) => (
                  <Tooltip 
                    key={idx} 
                    title={`${entity.type} • ${Math.round(entity.confidence * 100)}% confidence • ${entity.relevance}`}
                    arrow
                  >
        <Chip
                      label={entity.entity}
          size="small"
                      icon={<VerifiedIcon sx={{ fontSize: '0.9rem !important' }} />}
                      sx={{
                        fontSize: '0.65rem',
                        height: 22,
                        backgroundColor: pvConfig.bgColor,
                        borderColor: pvConfig.color,
                        border: `1px solid ${pvConfig.color}`,
                        color: pvConfig.color,
                        fontWeight: 600,
                        '& .MuiChip-icon': {
                          color: pvConfig.color
                        }
                      }}
                    />
                  </Tooltip>
                ))}
                {document.classification_entities.length > 3 && (
                  <Typography variant="caption" color={pvConfig.color} sx={{ alignSelf: 'center', ml: 0.5, fontWeight: 600 }}>
                    +{document.classification_entities.length - 3}
                  </Typography>
                )}
              </Box>
            </Box>
          )}

          {/* Entity Tags - Regular extracted entities */}
          {!pvConfig && document.metadata?.openai_entities && document.metadata.openai_entities.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
              {document.metadata.openai_entities.slice(0, 3).map((entity, idx) => (
                <Chip
                  key={idx}
                  label={entity.text}
                  size="small"
          variant="outlined"
                  sx={{
                    fontSize: '0.65rem',
                    height: 20,
                    backgroundColor: `${typeConfig.color}08`,
                    borderColor: `${typeConfig.color}40`,
                    color: typeConfig.color,
                    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif'
                  }}
                />
              ))}
              {document.metadata.openai_entities.length > 3 && (
                <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center', ml: 0.5 }}>
                  +{document.metadata.openai_entities.length - 3} more
                </Typography>
              )}
            </Box>
          )}
        </CardContent>

        {/* Actions Footer */}
        <CardActions
          className="document-actions"
          sx={{
            justifyContent: 'space-between',
            px: 2,
            pb: 2,
            pt: 0,
            opacity: 0.7,
            transform: 'translateY(4px)',
            transition: 'all 0.3s ease'
          }}
        >
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Standard View">
        <IconButton
          size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/document/${document.id}`);
                }}
                sx={{
                  backgroundColor: 'rgba(0,0,0,0.04)',
                  '&:hover': { backgroundColor: 'rgba(0,0,0,0.08)' }
                }}
              >
                <ViewIcon fontSize="small" />
        </IconButton>
            </Tooltip>
            <Tooltip title="Professional View">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/professional-document/${document.id}`);
                }}
                sx={{
                  backgroundColor: '#495057',
                  color: 'white',
                  '&:hover': { backgroundColor: '#343A40' }
                }}
              >
                <AssignmentIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload(document);
                }}
                sx={{
                  backgroundColor: 'rgba(0,0,0,0.04)',
                  '&:hover': { backgroundColor: 'rgba(0,0,0,0.08)' }
                }}
              >
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onMenuClick(e, document);
            }}
            sx={{
              backgroundColor: 'rgba(0,0,0,0.04)',
              '&:hover': { backgroundColor: 'rgba(0,0,0,0.08)' }
            }}
          >
            <MoreIcon fontSize="small" />
          </IconButton>
        </CardActions>
      </Card>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Sophisticated Gray Header */}
      <Box 
        sx={{ 
          background: 'linear-gradient(135deg, #343A40 0%, #495057 100%)',
          color: 'white',
          p: 4,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Background Pattern */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 200,
            height: 200,
            background: 'radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            opacity: 0.3
          }}
        />
        
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography 
            variant="h3" 
            sx={{ 
              mb: 1, 
              fontWeight: 700,
              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
              background: 'linear-gradient(45deg, #fff 30%, rgba(255,255,255,0.8) 90%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              letterSpacing: '-0.02em'
            }}
          >
            📚 Document Library
        </Typography>
          <Typography 
            variant="h6" 
            sx={{ 
              opacity: 0.9,
              fontWeight: 400,
              mb: 2
            }}
          >
            Discover, explore, and analyze your documents with AI-powered intelligence
          </Typography>
          
          {/* Quick Stats */}
          <Stack direction="row" spacing={3} sx={{ mt: 2, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {totalDocuments}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Total Documents
        </Typography>
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {documents.filter(d => d.classification === 'ICSR').length}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                🚨 ICSRs
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {documents.filter(d => d.classification === 'Safety_Information').length}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                🔬 Safety Info
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {documents.filter(d => d.extraction_method?.includes('llava') || d.extraction_method?.includes('llamaparse')).length}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                AI Processed
              </Typography>
            </Box>
          </Stack>
        </Box>
      </Box>
      
      {/* Enhanced Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab 
            icon={<GridViewIcon />} 
            label="Browse Documents" 
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />
          <Tab 
            icon={<SearchIcon />} 
            label="Intelligent Search" 
            iconPosition="start"
            sx={{ textTransform: 'none', fontWeight: 500 }}
          />

        </Tabs>
      </Box>
      


      {/* Search Tab Content */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ p: 3 }}>
          <Paper 
            elevation={3} 
            sx={{ 
              mb: 4,
              p: 4,
              background: 'linear-gradient(135deg, #495057 0%, #6C757D 100%)',
              color: 'white',
              borderRadius: 3,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Background decoration */}
            <Box
              sx={{
                position: 'absolute',
                top: -50,
                right: -50,
                width: 150,
                height: 150,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)'
              }}
            />
            
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
                🤖 AI-Powered Search
              </Typography>
              <Typography variant="h6" sx={{ mb: 3, opacity: 0.9, fontWeight: 400 }}>
                Ask questions, find insights, discover connections in your documents
              </Typography>
              <TextField
                fullWidth
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                placeholder="Ask me anything about your documents... 💭"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: 'rgba(0,0,0,0.6)' }} />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery && (
                    <InputAdornment position="end">
                      <IconButton onClick={clearSearch} size="small">
                        <ClearIcon sx={{ color: 'rgba(0,0,0,0.6)' }} />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                sx={{ 
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    borderRadius: 3,
                    fontSize: '1.1rem',
                    backdropFilter: 'blur(10px)',
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,1)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(255,255,255,1)',
                      boxShadow: '0 0 0 3px rgba(255,255,255,0.3)'
                    }
                  },
                  '& .MuiOutlinedInput-input': {
                    py: 2
                  }
                }}
              />
              
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isSearching}
                  startIcon={<SearchIcon />}
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.3)',
                    },
                    '&:disabled': {
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      color: 'rgba(255,255,255,0.5)'
                    }
                  }}
                >
                  {isSearching ? 'Searching...' : 'Search Documents'}
                </Button>
              </Stack>
              
              {/* Quick Search Suggestions */}
              <Box>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.8 }}>
                  💡 Try these searches:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {['COVID-19 vaccine side effects', 'FDA approval documents', 'clinical trial results', 'medical research papers'].map((term) => (
                    <Chip
                      key={term}
                      label={term}
                      size="small"
                      onClick={() => {
                        setSearchQuery(term);
                        setTimeout(handleSearch, 100);
                      }}
                      sx={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        border: '1px solid rgba(255,255,255,0.3)',
                        backdropFilter: 'blur(10px)',
                        '&:hover': { 
                          backgroundColor: 'rgba(255,255,255,0.3)',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                        },
                        transition: 'all 0.2s ease'
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </Box>
          </Paper>
          
          {renderSearchResults()}
        </Box>
      </TabPanel>
      
      {/* Browse Tab Content */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ p: 3 }}>
          {/* Enhanced Header with Stats */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box>
                <Typography 
                  variant="h5" 
                  sx={{ 
                    fontWeight: 600, 
                    mb: 0.5,
                    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                    letterSpacing: '-0.01em'
                  }}
                >
                  📚 Document Collection
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary"
                  sx={{
                    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif'
                  }}
                >
                  {totalDocuments} documents • Updated {new Date().toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
            
            {/* PV Classification Filters */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block', fontWeight: 600 }}>
                📋 Filter by PV Classification:
              </Typography>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                <Chip
                  label={`All (${allDocuments.length})`}
                  onClick={() => setClassificationFilter('all')}
                  color={classificationFilter === 'all' ? 'primary' : 'default'}
                  variant={classificationFilter === 'all' ? 'filled' : 'outlined'}
                  sx={{ fontWeight: classificationFilter === 'all' ? 600 : 400 }}
                />
                <Chip
                  icon={<WarningIcon />}
                  label={`ICSR (${allDocuments.filter(d => d.classification === 'ICSR').length})`}
                  onClick={() => setClassificationFilter('ICSR')}
                  sx={{
                    backgroundColor: classificationFilter === 'ICSR' ? '#d32f2f' : 'transparent',
                    color: classificationFilter === 'ICSR' ? 'white' : '#d32f2f',
                    borderColor: '#d32f2f',
                    fontWeight: classificationFilter === 'ICSR' ? 600 : 400,
                    '& .MuiChip-icon': { color: classificationFilter === 'ICSR' ? 'white' : '#d32f2f' }
                  }}
                />
                <Chip
                  icon={<ScienceIcon />}
                  label={`Safety Info (${allDocuments.filter(d => d.classification === 'Safety_Information').length})`}
                  onClick={() => setClassificationFilter('Safety_Information')}
                  sx={{
                    backgroundColor: classificationFilter === 'Safety_Information' ? '#1976d2' : 'transparent',
                    color: classificationFilter === 'Safety_Information' ? 'white' : '#1976d2',
                    borderColor: '#1976d2',
                    fontWeight: classificationFilter === 'Safety_Information' ? 600 : 400,
                    '& .MuiChip-icon': { color: classificationFilter === 'Safety_Information' ? 'white' : '#1976d2' }
                  }}
                />
                <Chip
                  icon={<ArticleIcon />}
                  label={`Non-ICSR (${allDocuments.filter(d => d.classification === 'Non-ICSR').length})`}
                  onClick={() => setClassificationFilter('Non-ICSR')}
                  sx={{
                    backgroundColor: classificationFilter === 'Non-ICSR' ? '#0288d1' : 'transparent',
                    color: classificationFilter === 'Non-ICSR' ? 'white' : '#0288d1',
                    borderColor: '#0288d1',
                    fontWeight: classificationFilter === 'Non-ICSR' ? 600 : 400,
                    '& .MuiChip-icon': { color: classificationFilter === 'Non-ICSR' ? 'white' : '#0288d1' }
                  }}
                />
                <Chip
                  icon={<BlockIcon />}
                  label={`Rejected (${allDocuments.filter(d => d.classification === 'Rejected').length})`}
                  onClick={() => setClassificationFilter('Rejected')}
                  sx={{
                    backgroundColor: classificationFilter === 'Rejected' ? '#757575' : 'transparent',
                    color: classificationFilter === 'Rejected' ? 'white' : '#757575',
                    borderColor: '#757575',
                    fontWeight: classificationFilter === 'Rejected' ? 600 : 400,
                    '& .MuiChip-icon': { color: classificationFilter === 'Rejected' ? 'white' : '#757575' }
                  }}
                />
              </Stack>
            </Box>
          </Box>

          {/* Document Cards Grid */}
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Loading documents...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Fetching your document library
                </Typography>
              </Box>
              </Box>
            ) : error ? (
            <Alert 
              severity="error" 
                sx={{
                m: 2,
                '& .MuiAlert-message': {
                  fontSize: '1rem'
                }
              }}
            >
              <Typography variant="h6" sx={{ mb: 1 }}>
                Failed to load documents
              </Typography>
              {error.message}
            </Alert>
          ) : documents.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <DocumentIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" color="text.secondary" sx={{ mb: 1 }}>
                No documents found
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Start by uploading some documents to your library
              </Typography>
            </Box>
          ) : (
            <>
              <Grid container spacing={3}>
                {documents.map((document) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={document.id}>
                    <DocumentCard
                      document={document}
                      onClick={(doc) => navigate(`/document/${doc.id}`)}
                      onMenuClick={(e, doc) => handleMenuClick(e, doc)}
                    />
                  </Grid>
                ))}
              </Grid>

              {/* Enhanced Pagination */}
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <Button
                    variant="outlined"
                    disabled={page === 0}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Page {page + 1} of {Math.ceil(totalDocuments / pageSize)}
                    </Typography>
                    <Select
                      value={pageSize}
                      onChange={(e) => setPageSize(e.target.value)}
                      size="small"
                      sx={{ minWidth: 80 }}
                    >
                      <MenuItem value={25}>25</MenuItem>
                      <MenuItem value={50}>50</MenuItem>
                      <MenuItem value={100}>100</MenuItem>
                    </Select>
                    <Typography variant="body2" color="text.secondary">
                      per page
                    </Typography>
                  </Box>
                  
                  <Button
                    variant="outlined"
                    disabled={page >= Math.ceil(totalDocuments / pageSize) - 1}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </Stack>
              </Box>
            </>
          )}
        </Box>
      </TabPanel>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { minWidth: 150 }
        }}
      >
        <MenuItem onClick={() => handleView(selectedDoc)}>
          <ViewIcon sx={{ mr: 1 }} /> Standard View
        </MenuItem>
        <MenuItem onClick={() => {
          handleMenuClose();
          navigate(`/professional-document/${selectedDoc.id}`);
        }}>
          <AssignmentIcon sx={{ mr: 1 }} /> Professional View
        </MenuItem>
        <MenuItem onClick={() => handleDownload(selectedDoc)}>
          <DownloadIcon sx={{ mr: 1 }} /> Download
        </MenuItem>
        <MenuItem onClick={() => handleEdit(selectedDoc)}>
          <EditIcon sx={{ mr: 1 }} /> Edit
        </MenuItem>
        <MenuItem onClick={() => handleDelete(selectedDoc)} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => { setEditDialogOpen(false); handleMenuClose(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Document</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Document Title"
            fullWidth
            variant="outlined"
            value={editFormData.title}
            onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Tags (comma-separated)"
            fullWidth
            variant="outlined"
            value={editFormData.tags}
            onChange={(e) => setEditFormData({ ...editFormData, tags: e.target.value })}
            helperText="Enter tags separated by commas (e.g., medical, research, covid)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setEditDialogOpen(false); handleMenuClose(); }}>Cancel</Button>
          <Button onClick={confirmEdit} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => { setDeleteDialogOpen(false); handleMenuClose(); }}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{selectedDoc?.title}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDeleteDialogOpen(false); handleMenuClose(); }}>Cancel</Button>
          <Button onClick={confirmDelete} color="error" variant="contained">Delete</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default EnhancedDocuments;