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
  Collapse,
  Stack,
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
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import apiService from '../services/api';

function Documents() {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [expandedCard, setExpandedCard] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'table'
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Fetch documents
  const { data: documentsData, isLoading, error, refetch } = useQuery(
    'documents', 
    apiService.getDocuments,
    {
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const documents = documentsData?.documents || [];

  // Search functionality
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearchLoading(true);
    try {
      const results = await apiService.searchDocuments(searchQuery);
      setSearchResults(results.results || []);
      setIsSearchMode(true);
      setSnackbar({ open: true, message: `Found ${results.total || (results.results?.length || 0)} results`, severity: 'success' });
    } catch (error) {
      console.error('Search error:', error);
      setSnackbar({ open: true, message: 'Search failed', severity: 'error' });
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearchMode(false);
    setSearchResults([]);
  };

  const displayDocuments = isSearchMode ? searchResults : documents;
  const totalDocuments = isSearchMode ? searchResults.length : documents.length;

  // Handlers
  const handleMenuClick = (event, doc) => {
    setAnchorEl(event.currentTarget);
    setSelectedDoc(doc);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDoc(null);
  };

  const handleEdit = () => {
    setEditDialogOpen(true);
    handleMenuClose();
  };

  const handleDelete = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleView = () => {
    if (selectedDoc) {
      navigate(`/document/${selectedDoc.id}`);
    }
    handleMenuClose();
  };

  const handleDownload = () => {
    if (selectedDoc) {
      window.open(`/api/documents/${selectedDoc.id}/download`, '_blank');
    }
    handleMenuClose();
  };

  const handleCardClick = (doc) => {
    setSelectedDoc(doc);
    setDetailDialogOpen(true);
  };

  const handleExpandCard = (docId, event) => {
    event.stopPropagation();
    setExpandedCard(expandedCard === docId ? null : docId);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Health': '#4caf50',
      'Finance': '#2196f3',
      'Legal': '#ff9800',
      'Research': '#9c27b0',
      'General': '#607d8b'
    };
    return colors[category] || colors['General'];
  };

  // DataGrid columns
  const columns = [
    {
      field: 'title',
      headerName: 'Document Title',
      flex: 1,
      minWidth: 300,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
          <DocumentIcon color="primary" />
          <Typography
            variant="body2"
            sx={{
              fontWeight: 500,
              cursor: 'pointer',
              '&:hover': { color: 'primary.main' }
            }}
            onClick={() => handleCardClick(params.row)}
          >
            {params.value}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          sx={{
            backgroundColor: getCategoryColor(params.value),
            color: 'white',
            fontWeight: 500
          }}
        />
      ),
    },
    {
      field: 'fileType',
      headerName: 'Type',
      width: 80,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ textTransform: 'uppercase', fontWeight: 500 }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'size',
      headerName: 'Size',
      width: 100,
    },
    {
      field: 'date',
      headerName: 'Upload Date',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2">
          {formatDate(params.value)}
        </Typography>
      ),
    },
    {
      field: 'processingStatus',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value === 'completed' ? 'Completed' : 'Processing'}
          size="small"
          color={params.value === 'completed' ? 'success' : 'warning'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <IconButton
          onClick={(e) => handleMenuClick(e, params.row)}
          size="small"
        >
          <MoreIcon />
        </IconButton>
      ),
    },
  ];

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={refetch}>
            Retry
          </Button>
        }>
          Failed to load documents: {error.message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
            Document Library 📚
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Browse and manage your document collection
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Total documents: {totalDocuments}
          </Typography>
          <Button
            variant="outlined"
            onClick={refetch}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Search Bar */}
      <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleSearchKeyPress}
              disabled={searchLoading}
              fullWidth
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchQuery && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={clearSearch}>
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={!searchQuery.trim() || searchLoading}
              startIcon={searchLoading ? <CircularProgress size={20} /> : <SearchIcon />}
            >
              Search
            </Button>
          </Box>
          {isSearchMode && (
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Showing {searchResults.length} search results for "{searchQuery}"
              </Typography>
              <Button size="small" onClick={clearSearch}>
                Clear Search
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Documents DataGrid */}
      <Card>
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={displayDocuments}
            columns={columns}
            pageSize={pageSize}
            onPageSizeChange={setPageSize}
            rowsPerPageOptions={[25, 50, 100]}
            pagination
            disableSelectionOnClick
            sx={{
              border: 'none',
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'grey.50',
              },
            }}
          />
        </Box>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleView}>
          <ViewIcon sx={{ mr: 1 }} />
          View
        </MenuItem>
        <MenuItem onClick={handleDownload}>
          <DownloadIcon sx={{ mr: 1 }} />
          Download
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <EditIcon sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DocumentIcon color="primary" />
            Document Details
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedDoc && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="h6" gutterBottom>
                {selectedDoc.title}
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Category
                  </Typography>
                  <Chip
                    label={selectedDoc.category}
                    size="small"
                    sx={{
                      backgroundColor: getCategoryColor(selectedDoc.category),
                      color: 'white'
                    }}
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    File Type
                  </Typography>
                  <Typography variant="body1">
                    {selectedDoc.fileType?.toUpperCase()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Size
                  </Typography>
                  <Typography variant="body1">
                    {selectedDoc.size}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Upload Date
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(selectedDoc.date)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Processing Status
                  </Typography>
                  <Chip
                    label={selectedDoc.processingStatus === 'completed' ? 'Completed' : 'Processing'}
                    size="small"
                    color={selectedDoc.processingStatus === 'completed' ? 'success' : 'warning'}
                    variant="outlined"
                  />
                </Box>
              </Stack>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>
            Close
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              if (selectedDoc) {
                navigate(`/document/${selectedDoc.id}`);
              }
            }}
            startIcon={<ViewIcon />}
          >
            View Document
          </Button>
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

export default Documents;