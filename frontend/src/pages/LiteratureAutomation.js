import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Article as ArticleIcon,
  Science as ScienceIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(3),
  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.2)',
}));

const SearchCard = styled(Card)(({ theme }) => ({
  background: 'rgba(255,255,255,0.95)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.2)',
  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
}));

const ResultCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
  },
}));

const LiteratureAutomation = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSources, setSelectedSources] = useState(['pubmed']);
  const [maxResults, setMaxResults] = useState(10);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [classificationDialog, setClassificationDialog] = useState(false);
  const [classificationResult, setClassificationResult] = useState(null);
  const [classifying, setClassifying] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [availableSources, setAvailableSources] = useState([]);

  // Available literature sources
  const sources = [
    { id: 'pubmed', name: 'PubMed', description: 'NCBI PubMed database' },
    { id: 'embase', name: 'Embase', description: 'Elsevier Embase database' },
    { id: 'cochrane', name: 'Cochrane Library', description: 'Cochrane systematic reviews' }
  ];

  // Load available sources on component mount
  useEffect(() => {
    loadAvailableSources();
  }, []);

  const loadAvailableSources = async () => {
    try {
      const response = await fetch('/api/v1/literature/sources');
      if (response.ok) {
        const data = await response.json();
        setAvailableSources(data.sources || sources);
      } else {
        setAvailableSources(sources);
      }
    } catch (error) {
      console.error('Error loading sources:', error);
      setAvailableSources(sources);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      const response = await fetch('/api/v1/literature/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          sources: selectedSources,
          max_results: maxResults
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setSearchResults(data.results || []);
      } else {
        throw new Error(data.message || 'Search failed');
      }
    } catch (error) {
      console.error('Search error:', error);
      setError(`Search failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClassifyArticle = async (article) => {
    setClassifying(true);
    setSelectedArticle(article);
    setClassificationDialog(true);

    try {
      const response = await fetch('/api/v1/literature/classify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          article_id: article.id,
          title: article.title,
          abstract: article.abstract,
          content: article.content
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setClassificationResult(data);
      } else {
        throw new Error(data.message || 'Classification failed');
      }
    } catch (error) {
      console.error('Classification error:', error);
      setError(`Classification failed: ${error.message}`);
    } finally {
      setClassifying(false);
    }
  };

  const getClassificationColor = (classification) => {
    switch (classification?.toLowerCase()) {
      case 'icsr':
        return 'error';
      case 'safety information':
        return 'warning';
      case 'non-icsr':
        return 'info';
      case 'rejected':
        return 'default';
      default:
        return 'default';
    }
  };

  const getClassificationIcon = (classification) => {
    switch (classification?.toLowerCase()) {
      case 'icsr':
        return <ErrorIcon />;
      case 'safety information':
        return <WarningIcon />;
      case 'non-icsr':
        return <InfoIcon />;
      case 'rejected':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <StyledCard>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <ScienceIcon sx={{ fontSize: 40, mr: 2 }} />
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                Literature Automation
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9 }}>
                AI-powered literature search and classification for pharmacovigilance
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </StyledCard>

      {/* Search Interface */}
      <SearchCard>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Search Literature
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search Query"
                placeholder="e.g., adverse events, drug safety, pharmacovigilance"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Sources</InputLabel>
                <Select
                  multiple
                  value={selectedSources}
                  onChange={(e) => setSelectedSources(e.target.value)}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {availableSources.map((source) => (
                    <MenuItem key={source.id} value={source.id}>
                      {source.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Max Results"
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 10)}
                inputProps={{ min: 1, max: 100 }}
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={1}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                sx={{ height: '56px' }}
              >
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </SearchCard>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {searchResults.length > 0 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Search Results ({searchResults.length} articles found)
              </Typography>
              <Chip
                label={`${selectedSources.join(', ')}`}
                color="primary"
                variant="outlined"
              />
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <List>
              {searchResults.map((article, index) => (
                <ListItem key={article.id || index} divider>
                  <ListItemText
                    primary={
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {article.title}
                        </Typography>
                        <Box display="flex" gap={1} mb={1}>
                          <Chip
                            icon={<ArticleIcon />}
                            label={article.source}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                          {article.journal && (
                            <Chip
                              label={article.journal}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {article.publication_date && (
                            <Chip
                              label={formatDate(article.publication_date)}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {article.abstract || 'No abstract available'}
                        </Typography>
                        {article.authors && article.authors.length > 0 && (
                          <Typography variant="caption" color="text.secondary">
                            Authors: {article.authors.join(', ')}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title="Classify Article">
                      <IconButton
                        onClick={() => handleClassifyArticle(article)}
                        disabled={classifying}
                      >
                        <AssessmentIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="View Details">
                      <IconButton
                        onClick={() => {
                          setSelectedArticle(article);
                          setActiveTab(1);
                        }}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Classification Dialog */}
      <Dialog
        open={classificationDialog}
        onClose={() => setClassificationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <AssessmentIcon sx={{ mr: 1 }} />
            Article Classification
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedArticle && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedArticle.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedArticle.abstract}
              </Typography>
              
              {classifying ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                  <Typography variant="body2" sx={{ ml: 2 }}>
                    Classifying article...
                  </Typography>
                </Box>
              ) : classificationResult ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Classification Result
                  </Typography>
                  <Box display="flex" gap={2} mb={2}>
                    <Chip
                      icon={getClassificationIcon(classificationResult.classification)}
                      label={classificationResult.classification}
                      color={getClassificationColor(classificationResult.classification)}
                      size="large"
                    />
                    <Chip
                      label={`Confidence: ${(classificationResult.confidence * 100).toFixed(1)}%`}
                      variant="outlined"
                      size="large"
                    />
                  </Box>
                  {classificationResult.reasoning && (
                    <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="body2">
                        <strong>Reasoning:</strong> {classificationResult.reasoning}
                      </Typography>
                    </Paper>
                  )}
                </Box>
              ) : null}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClassificationDialog(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default LiteratureAutomation;
