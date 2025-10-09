import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  TextField,
  Button,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  IconButton,
  Tooltip,
  Badge,
  LinearProgress,
  Collapse
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Tune as TuneIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Bookmark as BookmarkIcon,
  Visibility as VisibilityIcon,
  Source as SourceIcon,
  CalendarToday as CalendarIcon,
  Science as ScienceIcon,
  LocalHospital as HospitalIcon,
  Biotech as BiotechIcon,
  Article as ArticleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useQuery, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import apiService from '../services/api';

// Source configuration
const SOURCE_CONFIG = {
  clinicaltrials: {
    name: 'ClinicalTrials.gov',
    icon: <HospitalIcon />,
    color: '#1976d2',
    description: 'Clinical trials worldwide',
    enabled: true
  },
  fda: {
    name: 'FDA OpenFDA',
    icon: <ScienceIcon />,
    color: '#d32f2f',
    description: 'Drug safety & adverse events',
    enabled: true
  },
  chembl: {
    name: 'ChEMBL',
    icon: <BiotechIcon />,
    color: '#388e3c',
    description: 'Chemical compounds & bioactivity',
    enabled: false, // Requires API key
    requiresApiKey: true
  },
  semanticscholar: {
    name: 'Semantic Scholar',
    icon: <ArticleIcon />,
    color: '#7b1fa2',
    description: 'AI-powered research papers',
    enabled: true
  },
  europepmc: {
    name: 'Europe PMC',
    icon: <ArticleIcon />,
    color: '#f57c00',
    description: 'European research papers',
    enabled: true
  }
};

const DOCUMENT_TYPE_CONFIG = {
  research_article: { label: 'Research Articles', icon: <ArticleIcon />, color: '#1976d2' },
  clinical_trial: { label: 'Clinical Trials', icon: <HospitalIcon />, color: '#d32f2f' },
  adverse_event: { label: 'Adverse Events', icon: <ScienceIcon />, color: '#f57c00' },
  drug_label: { label: 'Drug Labels', icon: <ScienceIcon />, color: '#388e3c' },
  chemical_compound: { label: 'Compounds', icon: <BiotechIcon />, color: '#7b1fa2' }
};

function UnifiedSearch() {
  const theme = useTheme();
  const queryClient = useQueryClient();
  
  // Search state
  const [query, setQuery] = useState('');
  const [selectedSources, setSelectedSources] = useState(['clinicaltrials', 'fda', 'semanticscholar', 'europepmc']);
  const [selectedDocumentTypes, setSelectedDocumentTypes] = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortBy, setSortBy] = useState('relevance');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // UI state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedDocuments, setSelectedDocuments] = useState(new Set());
  const [searchHistory, setSearchHistory] = useState([]);
  
  // Search query
  const { data: searchResults, isLoading, error, refetch } = useQuery(
    ['unified-search', query, selectedSources, selectedDocumentTypes, dateFrom, dateTo, page, pageSize, sortBy, sortOrder],
    () => apiService.unifiedSearch({
      q: query,
      sources: selectedSources,
      document_types: selectedDocumentTypes,
      date_from: dateFrom,
      date_to: dateTo,
      page,
      size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder
    }),
    {
      enabled: !!query && query.length >= 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false
    }
  );

  // Handle search
  const handleSearch = useCallback(() => {
    if (query.trim().length < 2) {
      toast.error('Please enter at least 2 characters to search');
      return;
    }
    
    setPage(0);
    setSearchHistory(prev => [query, ...prev.filter(q => q !== query)].slice(0, 10));
    refetch();
  }, [query, refetch]);

  // Handle key press
  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  // Handle source toggle
  const handleSourceToggle = (sourceId) => {
    setSelectedSources(prev => 
      prev.includes(sourceId) 
        ? prev.filter(s => s !== sourceId)
        : [...prev, sourceId]
    );
  };

  // Handle document type toggle
  const handleDocumentTypeToggle = (docType) => {
    setSelectedDocumentTypes(prev => 
      prev.includes(docType) 
        ? prev.filter(t => t !== docType)
        : [...prev, docType]
    );
  };

  // Handle pagination
  const handlePageChange = (newPage) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle document selection
  const handleDocumentSelect = (docId) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(docId)) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      return newSet;
    });
  };

  // Handle select all
  const handleSelectAll = () => {
    if (selectedDocuments.size === searchResults?.results?.length) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(searchResults?.results?.map(doc => doc.id) || []));
    }
  };

  // Export selected documents
  const handleExport = () => {
    if (selectedDocuments.size === 0) {
      toast.error('Please select documents to export');
      return;
    }
    
    const selectedDocs = searchResults?.results?.filter(doc => selectedDocuments.has(doc.id)) || [];
    const exportData = {
      query,
      sources: selectedSources,
      documents: selectedDocs,
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success(`Exported ${selectedDocuments.size} documents`);
  };

  // Get source info
  const getSourceInfo = (sourceId) => SOURCE_CONFIG[sourceId] || { name: sourceId, icon: <SourceIcon />, color: '#666' };

  // Get document type info
  const getDocumentTypeInfo = (docType) => DOCUMENT_TYPE_CONFIG[docType] || { label: docType, icon: <ArticleIcon />, color: '#666' };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'text.primary' }}>
            🔍 Unified Search
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Search across all data sources with a single query
          </Typography>
          
          {/* Search Bar */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Search across all sources... (e.g., 'cancer immunotherapy', 'aspirin safety')"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              InputProps={{
                startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />,
                endAdornment: (
                  <IconButton onClick={handleSearch} disabled={!query || query.length < 2}>
                    <SearchIcon />
                  </IconButton>
                )
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  fontSize: '1.1rem'
                }
              }}
            />
            <Button
              variant="outlined"
              startIcon={<TuneIcon />}
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              sx={{ minWidth: 120 }}
            >
              Filters
            </Button>
          </Box>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Recent searches:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {searchHistory.slice(0, 5).map((search, index) => (
                  <Chip
                    key={index}
                    label={search}
                    size="small"
                    onClick={() => setQuery(search)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Advanced Filters */}
          <Collapse in={showAdvancedFilters}>
            <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 2 }}>
              <Grid container spacing={3}>
                {/* Sources */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Data Sources
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {Object.entries(SOURCE_CONFIG).map(([sourceId, config]) => (
                      <Chip
                        key={sourceId}
                        label={config.name}
                        icon={config.icon}
                        color={selectedSources.includes(sourceId) ? 'primary' : 'default'}
                        variant={selectedSources.includes(sourceId) ? 'filled' : 'outlined'}
                        onClick={() => handleSourceToggle(sourceId)}
                        disabled={!config.enabled}
                        sx={{
                          '&.MuiChip-filled': {
                            bgcolor: config.color,
                            color: 'white'
                          }
                        }}
                      />
                    ))}
                  </Box>
                </Grid>

                {/* Document Types */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Document Types
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {Object.entries(DOCUMENT_TYPE_CONFIG).map(([docType, config]) => (
                      <Chip
                        key={docType}
                        label={config.label}
                        icon={config.icon}
                        color={selectedDocumentTypes.includes(docType) ? 'primary' : 'default'}
                        variant={selectedDocumentTypes.includes(docType) ? 'filled' : 'outlined'}
                        onClick={() => handleDocumentTypeToggle(docType)}
                        sx={{
                          '&.MuiChip-filled': {
                            bgcolor: config.color,
                            color: 'white'
                          }
                        }}
                      />
                    ))}
                  </Box>
                </Grid>

                {/* Date Range */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Date Range
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField
                      type="date"
                      label="From"
                      value={dateFrom}
                      onChange={(e) => setDateFrom(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                      size="small"
                    />
                    <TextField
                      type="date"
                      label="To"
                      value={dateTo}
                      onChange={(e) => setDateTo(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                      size="small"
                    />
                  </Box>
                </Grid>

                {/* Sort Options */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Sort By
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel>Sort by</InputLabel>
                      <Select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        label="Sort by"
                      >
                        <MenuItem value="relevance">Relevance</MenuItem>
                        <MenuItem value="date">Date</MenuItem>
                        <MenuItem value="quality">Quality</MenuItem>
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ minWidth: 100 }}>
                      <InputLabel>Order</InputLabel>
                      <Select
                        value={sortOrder}
                        onChange={(e) => setSortOrder(e.target.value)}
                        label="Order"
                      >
                        <MenuItem value="desc">Desc</MenuItem>
                        <MenuItem value="asc">Asc</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Collapse>
        </Container>
      </Paper>

      {/* Results */}
      <Container maxWidth="lg">
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Search failed: {error.message}
          </Alert>
        )}

        {searchResults && (
          <>
            {/* Results Header */}
            <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  {searchResults.total.toLocaleString()} results found
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    startIcon={<DownloadIcon />}
                    onClick={handleExport}
                    disabled={selectedDocuments.size === 0}
                    size="small"
                  >
                    Export ({selectedDocuments.size})
                  </Button>
                  <Button
                    startIcon={<RefreshIcon />}
                    onClick={() => refetch()}
                    size="small"
                  >
                    Refresh
                  </Button>
                </Box>
              </Box>

              {/* Search Stats */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Typography variant="body2" color="text.secondary">
                  Search time: {searchResults.search_time_ms}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sources: {searchResults.sources_searched.join(', ')}
                </Typography>
                {searchResults.errors.length > 0 && (
                  <Typography variant="body2" color="error">
                    {searchResults.errors.length} source(s) had errors
                  </Typography>
                )}
              </Box>

              {/* Source Breakdown */}
              {searchResults.source_breakdown && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Results by source:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(searchResults.source_breakdown).map(([source, count]) => {
                      const sourceInfo = getSourceInfo(source);
                      return (
                        <Chip
                          key={source}
                          label={`${sourceInfo.name}: ${count}`}
                          icon={sourceInfo.icon}
                          size="small"
                          sx={{ bgcolor: sourceInfo.color, color: 'white' }}
                        />
                      );
                    })}
                  </Box>
                </Box>
              )}
            </Paper>

            {/* Results List */}
            <Grid container spacing={3}>
              {searchResults.results.map((doc) => (
                <Grid item xs={12} key={doc.id}>
                  <Card 
                    elevation={2} 
                    sx={{ 
                      cursor: 'pointer',
                      border: selectedDocuments.has(doc.id) ? `2px solid ${theme.palette.primary.main}` : 'none',
                      '&:hover': { elevation: 4 }
                    }}
                    onClick={() => handleDocumentSelect(doc.id)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                            {doc.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {doc.abstract || doc.summary || 'No abstract available'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1, ml: 2 }}>
                          <Chip
                            label={getSourceInfo(doc.source).name}
                            icon={getSourceInfo(doc.source).icon}
                            size="small"
                            sx={{ bgcolor: getSourceInfo(doc.source).color, color: 'white' }}
                          />
                          <Chip
                            label={getDocumentTypeInfo(doc.document_type).label}
                            icon={getDocumentTypeInfo(doc.document_type).icon}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>

                      {/* Document Metadata */}
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                        {doc.publication_date && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <CalendarIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {new Date(doc.publication_date).toLocaleDateString()}
                            </Typography>
                          </Box>
                        )}
                        {doc.authors && doc.authors.length > 0 && (
                          <Typography variant="body2" color="text.secondary">
                            {doc.authors.slice(0, 3).map(a => a.name).join(', ')}
                            {doc.authors.length > 3 && ` +${doc.authors.length - 3} more`}
                          </Typography>
                        )}
                        {doc.quality_score && (
                          <Typography variant="body2" color="text.secondary">
                            Quality: {doc.quality_score.toFixed(1)}/100
                          </Typography>
                        )}
                      </Box>

                      {/* Key Concepts */}
                      {doc.key_concepts && doc.key_concepts.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Key concepts:
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {doc.key_concepts.slice(0, 5).map((concept, index) => (
                              <Chip
                                key={index}
                                label={concept}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                            {doc.key_concepts.length > 5 && (
                              <Chip
                                label={`+${doc.key_concepts.length - 5} more`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                      )}

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Tooltip title="View full document">
                          <IconButton size="small">
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Bookmark">
                          <IconButton size="small">
                            <BookmarkIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Share">
                          <IconButton size="small">
                            <ShareIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {/* Pagination */}
            {searchResults.total > pageSize && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 4 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    disabled={page === 0}
                    onClick={() => handlePageChange(page - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    disabled={page >= Math.ceil(searchResults.total / pageSize) - 1}
                    onClick={() => handlePageChange(page + 1)}
                  >
                    Next
                  </Button>
                </Box>
              </Box>
            )}
          </>
        )}

        {/* Empty State */}
        {!isLoading && !error && (!searchResults || searchResults.results.length === 0) && query && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No results found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Try adjusting your search terms or filters
            </Typography>
          </Box>
        )}
      </Container>
    </Box>
  );
}

export default UnifiedSearch;
