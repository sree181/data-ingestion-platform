import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
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
  Error as ErrorIcon
} from '@mui/icons-material';
import { apiService } from '../services/api';





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
  
  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({ title: '', tags: '' });
  
  // Snackbar for notifications
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Fetch documents from API - CRITICAL MISSING FUNCTIONALITY
  const { data: documentsData, isLoading, error, refetch } = useQuery(
    ['documents', page, pageSize],
    () => {
      console.log('Fetching documents with page:', page, 'pageSize:', pageSize);
      return apiService.getDocuments(page, pageSize);
    },
    {
      staleTime: 0, // No caching to ensure fresh data on pagination
      refetchOnWindowFocus: false,
      keepPreviousData: true, // Keep previous data while loading new data
      enabled: activeTab === 0, // Only fetch when in browse mode
    }
  );

  // Extract documents and total count
  const documents = documentsData?.documents || [];
  const totalDocuments = documentsData?.total || 0;
  
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
                <Card key={result.id} sx={{ cursor: 'pointer' }} onClick={() => navigate(`/document/${result.id}`)}>
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

  // Define columns for DataGrid
  const columns = [
    {
      field: 'title',
      headerName: 'Title',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.light' }}>
            <DocumentIcon fontSize="small" />
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight={500}>
              {params.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.row.file_type}
            </Typography>
          </Box>
        </Box>
      ),
    },
    {
      field: 'extraction_method',
      headerName: 'Processing',
      width: 150,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value.includes('llava') || params.value.includes('llamaparse') ? 'primary' : 'default'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'entities',
      headerName: 'Entities',
      width: 100,
      align: 'center',
      headerAlign: 'center',
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 120,
      valueFormatter: (params) => {
        if (!params.value) return 'Unknown';
        return new Date(params.value).toLocaleDateString();
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => (
        <IconButton
          size="small"
          onClick={(event) => handleMenuClick(event, params.row)}
        >
          <MoreIcon />
        </IconButton>
      ),
    },
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
          Document Library
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Browse, search, and manage your documents with AI-powered insights
        </Typography>
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
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                AI-Powered Document Search
              </Typography>
              <TextField
                fullWidth
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                placeholder="Search documents, ask questions, or describe what you're looking for..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery && (
                    <InputAdornment position="end">
                      <IconButton onClick={clearSearch} size="small">
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                sx={{ mb: 2 }}
              />
              
              <Stack direction="row" spacing={2} alignItems="center">
                <Button
                  variant="contained"
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isSearching}
                  startIcon={<SearchIcon />}
                >
                  {isSearching ? 'Searching...' : 'Search'}
                </Button>
                
                {/* Quick Search Chips */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {['COVID-19 vaccine', 'FDA approval', 'clinical trial'].map((term) => (
                    <Chip
                      key={term}
                      label={term}
                      size="small"
                      onClick={() => {
                        setSearchQuery(term);
                        setTimeout(handleSearch, 100);
                      }}
                      sx={{ 
                        background: alpha(theme.palette.primary.main, 0.1),
                        '&:hover': { background: alpha(theme.palette.primary.main, 0.2) }
                      }}
                    />
                  ))}
                </Box>
              </Stack>
            </CardContent>
          </Card>
          
          {renderSearchResults()}
        </Box>
      </TabPanel>
      
      {/* Browse Tab Content */}
      <TabPanel value={activeTab} index={0}>
        <Card sx={{ flex: 1, m: 3, mt: 0 }}>
          <CardContent sx={{ height: '100%', p: 0 }}>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <CircularProgress />
              </Box>
            ) : error ? (
              <Alert severity="error" sx={{ m: 2 }}>
                Failed to load documents: {error.message}
              </Alert>
            ) : (
              <DataGrid
                rows={documents}
                columns={columns}
                rowCount={totalDocuments}
                loading={isLoading}
                pageSizeOptions={[25, 50, 100]}
                paginationModel={{ page, pageSize }}
                paginationMode="server"
                onPaginationModelChange={(model) => {
                  console.log('Pagination model change:', model);
                  setPage(model.page);
                  setPageSize(model.pageSize);
                }}
                checkboxSelection
                disableSelectionOnClick
                autoHeight
                sx={{
                  '& .MuiDataGrid-main': {
                    overflow: 'visible'
                  }
                }}
              />
            )}
          </CardContent>
        </Card>
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
          <ViewIcon sx={{ mr: 1 }} /> View
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