import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Typography,
  Chip,
  Avatar,
  IconButton,
  Button,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Collapse,
  Tooltip,
  Paper,
  Badge,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Description as DocumentIcon,
  CalendarToday as DateIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingIcon,
  Highlight as HighlightIcon,
  OpenInNew as OpenIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';

const popularSearches = [
  'COVID-19 vaccine',
  'FDA approval',
  'clinical trial',
  'emergency authorization',
  'public health policy',
  'vaccine efficacy',
  'legal framework',
  'regulatory guidance',
];

const filters = {
  categories: ['Medical', 'Legal', 'Regulatory', 'Research'],
  fileTypes: ['PDF', 'DOC', 'TXT'],
  dateRanges: ['Last 7 days', 'Last 30 days', 'Last 6 months', 'Last year'],
};

function SearchResult({ result }) {
  const [expanded, setExpanded] = useState(false);

  const getCategoryColor = (category) => {
    const colors = {
      Medical: 'success',
      Legal: 'primary',
      Regulatory: 'warning',
      Research: 'secondary',
    };
    return colors[category] || 'default';
  };

  return (
    <Card sx={{ mb: 2, '&:hover': { boxShadow: 4 } }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, cursor: 'pointer' }}>
              {result.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip
                label={result.category}
                size="small"
                color={getCategoryColor(result.category)}
                variant="outlined"
              />
              <Chip
                label={result.fileType}
                size="small"
                variant="outlined"
                icon={<DocumentIcon />}
              />
              <Chip
                label={result.size}
                size="small"
                variant="outlined"
              />
              <Chip
                label={result.date}
                size="small"
                variant="outlined"
                icon={<DateIcon />}
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Open Document">
              <IconButton size="small">
                <OpenIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={expanded ? "Show Less" : "Show More"}>
              <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {(() => {
            // Smart content preview - skip page markers and show meaningful content
            const content = result.content || '';
            const cleanContent = content
              .replace(/=== PAGE \d+ ===/g, '') // Remove page markers
              .replace(/---END PAGE \d+---/g, '') // Remove end page markers
              .replace(/\n{2,}/g, '\n') // Collapse multiple newlines
              .trim();
            
            const previewLength = expanded ? cleanContent.length : 600; // Increased from 200 to 600
            const preview = cleanContent.substring(0, previewLength);
            return preview + (!expanded && cleanContent.length > previewLength ? '...' : '');
          })()}
        </Typography>

        <Collapse in={expanded}>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Key Highlights:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {result.highlights.map((highlight, index) => (
                <Chip
                  key={index}
                  label={highlight}
                  size="small"
                  icon={<HighlightIcon />}
                  sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}
                />
              ))}
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

function Search() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  // Real search function
  const performSearch = async (query) => {
    const filters = {};
    
    // Extract filters from activeFilters
    activeFilters.forEach(filter => {
      if (['Medical', 'Legal', 'Regulatory', 'Research'].includes(filter)) {
        filters.category = filter;
      } else if (['PDF', 'DOC', 'TXT'].includes(filter)) {
        filters.fileType = filter;
      } else if (filter.includes('days') || filter.includes('months') || filter.includes('year')) {
        filters.dateRange = filter;
      }
    });
    
    return await apiService.searchDocuments(query, filters);
  };

  const { data: searchResults, isLoading, refetch } = useQuery(
    ['search', searchQuery],
    () => performSearch(searchQuery),
    {
      enabled: !!searchQuery,
      staleTime: 0,
    }
  );

  const handleSearch = (query = searchQuery) => {
    if (query.trim()) {
      setSearchQuery(query);
      refetch();
    }
  };

  const handleFilterToggle = (filter) => {
    setActiveFilters(prev => 
      prev.includes(filter) 
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  const clearFilters = () => {
    setActiveFilters([]);
  };

  return (
    <Box>
      {/* Search Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
            Intelligent Document Search
          </Typography>
          
          {/* Search Input */}
          <TextField
            fullWidth
            placeholder="Search documents, ask questions, or describe what you're looking for..."
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
                  <Button
                    variant="contained"
                    onClick={() => handleSearch()}
                    disabled={!searchQuery.trim()}
                    sx={{ mr: -1 }}
                  >
                    Search
                  </Button>
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: 'background.paper',
              },
            }}
          />

          {/* Search Actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
                variant={showFilters ? 'contained' : 'outlined'}
                size="small"
              >
                Filters
                {activeFilters.length > 0 && (
                  <Badge badgeContent={activeFilters.length} color="secondary" sx={{ ml: 1 }} />
                )}
              </Button>
              <Button startIcon={<SortIcon />} variant="outlined" size="small">
                Sort: Relevance
              </Button>
              {activeFilters.length > 0 && (
                <Button onClick={clearFilters} size="small" color="error">
                  Clear Filters
                </Button>
              )}
            </Box>
            
            {searchResults && (
              <Typography variant="body2" color="text.secondary">
                {searchResults.total.toLocaleString()} results found
              </Typography>
            )}
          </Box>

          {/* Active Filters */}
          {activeFilters.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {activeFilters.map((filter) => (
                <Chip
                  key={filter}
                  label={filter}
                  onDelete={() => handleFilterToggle(filter)}
                  color="primary"
                  variant="filled"
                  size="small"
                />
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Filters Sidebar */}
        <Grid item xs={12} md={3}>
          <Collapse in={showFilters}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Filters
                </Typography>

                {/* Categories */}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Categories
                </Typography>
                <Box sx={{ mb: 3 }}>
                  {filters.categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onClick={() => handleFilterToggle(category)}
                      variant={activeFilters.includes(category) ? 'filled' : 'outlined'}
                      color={activeFilters.includes(category) ? 'primary' : 'default'}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* File Types */}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  File Types
                </Typography>
                <Box sx={{ mb: 3 }}>
                  {filters.fileTypes.map((type) => (
                    <Chip
                      key={type}
                      label={type}
                      onClick={() => handleFilterToggle(type)}
                      variant={activeFilters.includes(type) ? 'filled' : 'outlined'}
                      color={activeFilters.includes(type) ? 'primary' : 'default'}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Date Range */}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  Date Range
                </Typography>
                <Box>
                  {filters.dateRanges.map((range) => (
                    <Chip
                      key={range}
                      label={range}
                      onClick={() => handleFilterToggle(range)}
                      variant={activeFilters.includes(range) ? 'filled' : 'outlined'}
                      color={activeFilters.includes(range) ? 'primary' : 'default'}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Collapse>

          {/* Popular Searches */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                <TrendingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Popular Searches
              </Typography>
              <Box>
                {popularSearches.map((search, index) => (
                  <Chip
                    key={index}
                    label={search}
                    onClick={() => handleSearch(search)}
                    variant="outlined"
                    size="small"
                    sx={{ m: 0.5, cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Search Results */}
        <Grid item xs={12} md={9}>
          {!searchQuery && !isLoading && (
            <Paper sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.50' }}>
              <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                Start your search
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enter keywords, ask questions, or describe what you're looking for.
                Our AI-powered search will find the most relevant documents.
              </Typography>
            </Paper>
          )}

          {isLoading && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary">
                Searching...
              </Typography>
            </Box>
          )}

          {searchResults && !isLoading && (
            <Box>
              {searchResults.results.map((result) => (
                <SearchResult key={result.id} result={result} />
              ))}
              
              {searchResults.results.length === 0 && (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                    No results found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Try different keywords or remove some filters
                  </Typography>
                </Paper>
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

export default Search;