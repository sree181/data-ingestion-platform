import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Compare as CompareIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

const RiskChip = styled(Chip)(({ theme, risklevel }) => {
  const getColor = (level) => {
    switch (level) {
      case 'CRITICAL': return theme.palette.error.main;
      case 'HIGH': return theme.palette.warning.main;
      case 'MEDIUM': return theme.palette.info.main;
      case 'LOW': return theme.palette.success.main;
      default: return theme.palette.grey[500];
    }
  };
  
  return {
    backgroundColor: getColor(risklevel),
    color: theme.palette.getContrastText(getColor(risklevel)),
    fontWeight: 'bold',
  };
});

const LeverageChip = styled(Chip)(({ theme, leveragelevel }) => {
  const getColor = (level) => {
    switch (level) {
      case 'LEVERAGE_HIGH': return theme.palette.success.main;
      case 'LEVERAGE_MEDIUM': return theme.palette.info.main;
      case 'LEVERAGE_LOW': return theme.palette.warning.main;
      case 'LEVERAGE_NEGATIVE': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };
  
  return {
    backgroundColor: getColor(leveragelevel),
    color: theme.palette.getContrastText(getColor(leveragelevel)),
    fontWeight: 'bold',
  };
});

const LeaseManagement = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Extraction Configuration State
  const [extractionRules, setExtractionRules] = useState({
    obligationTypes: [],
    riskCategories: [],
    negotiationFactors: [],
    marketStandards: {}
  });
  
  // Comparison Configuration State
  const [comparisonConfig, setComparisonConfig] = useState({
    riskTolerance: 'MEDIUM',
    focusAreas: [],
    enableRiskAnalysis: true,
    enableNegotiationAnalysis: true,
    enableMarketBenchmarking: true
  });
  
  // Document Selection State
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [availableDocuments, setAvailableDocuments] = useState([]);
  
  // Analysis Results State
  const [extractionResults, setExtractionResults] = useState([]);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [negotiationAnalysis, setNegotiationAnalysis] = useState(null);
  
  // Clause Selection State
  const [selectedClause, setSelectedClause] = useState(null);
  const [clauseComparison, setClauseComparison] = useState(null);
  const [clauseComparisonLoading, setClauseComparisonLoading] = useState(false);
  
  // All Clauses Comparison State
  const [allClausesComparison, setAllClausesComparison] = useState(null);
  const [allClausesLoading, setAllClausesLoading] = useState(false);
  
  // Dialog States
  const [extractionDialogOpen, setExtractionDialogOpen] = useState(false);
  const [comparisonDialogOpen, setComparisonDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [clauseComparisonDialogOpen, setClauseComparisonDialogOpen] = useState(false);
  
  // New Extraction State
  const [newExtraction, setNewExtraction] = useState({
    documentId: '',
    focusAreas: [],
    customRules: {}
  });

  useEffect(() => {
    console.log('🚀 LeaseManagement component mounted, loading documents...');
    loadConfiguration();
    loadAvailableDocuments();
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      
      // Load extraction rules
      const rulesResponse = await fetch('http://localhost:8005/api/v1/lease/config/rules');
      if (rulesResponse.ok) {
        const rules = await rulesResponse.json();
        setExtractionRules(rules);
      }
      
      // Load focus areas
      const focusResponse = await fetch('http://localhost:8006/api/v1/config/focus-areas');
      if (focusResponse.ok) {
        const focus = await focusResponse.json();
        setComparisonConfig(prev => ({
          ...prev,
          focusAreas: focus.focus_areas
        }));
      }
      
    } catch (err) {
      setError('Failed to load configuration: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableDocuments = async () => {
    console.log('🔄 Loading available documents...');
    try {
      // Fetch documents from the search service
      const response = await fetch('http://localhost:8000/api/v1/search?query=*&page=0&size=100');
      console.log('📡 API Response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('📄 API Response data:', data);
        const documents = data.results?.map(doc => ({
          id: doc._id,
          name: doc._source?.title || doc._source?.filename || doc._id,
          type: 'lease',
          uploaded: doc._source?.uploaded_at || doc._source?.created_at || new Date().toISOString()
        })) || [];
        console.log('📋 Mapped documents:', documents);
        setAvailableDocuments(documents);
      } else {
        console.log('⚠️ API failed, using sample data');
        // Fallback to sample data if API fails
        const sampleDocuments = [
          { id: 'sample_lease_1', name: 'Sample Office Lease Agreement - Building A', type: 'lease', uploaded: '2024-01-15' },
          { id: 'sample_lease_2', name: 'Sample Retail Space Lease - Mall Location', type: 'lease', uploaded: '2024-01-20' },
          { id: 'sample_lease_3', name: 'Sample Warehouse Lease - Industrial Park', type: 'lease', uploaded: '2024-01-25' }
        ];
        console.log('📋 Setting sample documents:', sampleDocuments);
        setAvailableDocuments(sampleDocuments);
        console.info('Using sample documents for demonstration. Upload real documents to see them here.');
      }
    } catch (err) {
      console.warn('❌ Failed to load documents from API, using sample data:', err.message);
      // Fallback to sample data
      const sampleDocuments = [
        { id: 'sample_lease_1', name: 'Sample Office Lease Agreement - Building A', type: 'lease', uploaded: '2024-01-15' },
        { id: 'sample_lease_2', name: 'Sample Retail Space Lease - Mall Location', type: 'lease', uploaded: '2024-01-20' },
        { id: 'sample_lease_3', name: 'Sample Warehouse Lease - Industrial Park', type: 'lease', uploaded: '2024-01-25' }
      ];
      console.log('📋 Setting sample documents in catch:', sampleDocuments);
      setAvailableDocuments(sampleDocuments);
      console.info('Using sample documents for demonstration. Upload real documents to see them here.');
    }
  };

  const handleExtractObligations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First, try to get the actual document content
      let documentContent = `Sample lease content for ${newExtraction.documentId}. This is a placeholder for the actual document content.`;
      
      try {
        const docResponse = await fetch(`http://localhost:8000/api/documents/${newExtraction.documentId}`);
        if (docResponse.ok) {
          const docData = await docResponse.json();
          documentContent = docData.content || docData.text || documentContent;
        }
      } catch (docErr) {
        console.warn('Could not fetch document content, using placeholder:', docErr.message);
      }
      
      const response = await fetch('http://localhost:8005/api/v1/lease/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: newExtraction.documentId,
          document_content: documentContent,
          focus_areas: newExtraction.focusAreas,
          extraction_rules: newExtraction.customRules
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setExtractionResults(prev => [...prev, result]);
        setSuccess('Obligations extracted successfully!');
        setExtractionDialogOpen(false);
      } else {
        throw new Error('Extraction failed');
      }
    } catch (err) {
      setError('Failed to extract obligations: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompareDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8006/api/v1/lease/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_ids: selectedDocuments,
          comparison_config: comparisonConfig,
          focus_areas: comparisonConfig.focusAreas,
          risk_tolerance: comparisonConfig.riskTolerance
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setComparisonResults(result);
        setRiskAnalysis(result.risk_analysis);
        setNegotiationAnalysis(result.negotiation_analysis);
        setSuccess('Document comparison completed successfully!');
        setComparisonDialogOpen(false);
      } else {
        throw new Error('Comparison failed');
      }
    } catch (err) {
      setError('Failed to compare documents: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateConfiguration = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Update extraction rules
      await fetch('http://localhost:8005/api/v1/lease/config/rules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(extractionRules)
      });
      
      setSuccess('Configuration updated successfully!');
      setConfigDialogOpen(false);
    } catch (err) {
      setError('Failed to update configuration: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClauseSelection = (clause, documentId) => {
    setSelectedClause({
      ...clause,
      sourceDocumentId: documentId
    });
    setClauseComparisonDialogOpen(true);
  };

  const handleCompareSpecificClause = async () => {
    if (!selectedClause || selectedDocuments.length < 2) {
      setError('Please select a clause and at least 2 documents for comparison');
      return;
    }

    try {
      setClauseComparisonLoading(true);
      setError(null);

      // Prepare documents for comparison
      const documentsForComparison = await Promise.all(selectedDocuments.map(async (doc) => {
        let content = `Sample content for ${doc.name}`;
        
        try {
          const docResponse = await fetch(`http://localhost:8000/api/documents/${doc.id}`);
          if (docResponse.ok) {
            const docData = await docResponse.json();
            content = docData.content || docData.text || content;
          }
        } catch (docErr) {
          console.warn('Could not fetch document content for specific clause comparison:', docErr.message);
        }
        
        return {
          document_id: doc.id,
          content: content,
          metadata: {
            title: doc.name,
            type: doc.type,
            uploaded: doc.uploaded
          }
        };
      }));

      const response = await fetch('http://localhost:8005/api/v1/lease/compare-specific-clause', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clause_text: selectedClause.clause_text,
          clause_category: selectedClause.obligation_type,
          documents: documentsForComparison
        })
      });

      if (!response.ok) {
        throw new Error('Failed to compare specific clause');
      }

      const result = await response.json();
      setClauseComparison(result);
      setSuccess('Clause comparison completed successfully');

    } catch (err) {
      setError('Failed to compare specific clause: ' + err.message);
    } finally {
      setClauseComparisonLoading(false);
    }
  };

  const handleCompareAllClauses = async () => {
    if (extractionResults.length < 2) {
      setError('Please extract clauses from at least 2 documents first');
      return;
    }

    try {
      setAllClausesLoading(true);
      setError(null);

      // Prepare documents for comparison using extraction results
      const documentsForComparison = await Promise.all(extractionResults.map(async (result) => {
        let content = `Sample content for ${result.document_id}`;
        
        try {
          const docResponse = await fetch(`http://localhost:8000/api/documents/${result.document_id}`);
          if (docResponse.ok) {
            const docData = await docResponse.json();
            content = docData.content || docData.text || content;
          }
        } catch (docErr) {
          console.warn('Could not fetch document content for comparison:', docErr.message);
        }
        
        return {
          document_id: result.document_id,
          content: content,
          metadata: {
            title: result.document_id,
            type: 'lease',
            uploaded: new Date().toISOString()
          }
        };
      }));

      const response = await fetch('http://localhost:8005/api/v1/lease/compare-clauses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documents: documentsForComparison,
          focus_categories: ['MAINTENANCE', 'RENEWAL', 'TERMINATION', 'RENT', 'SECURITY', 'INSURANCE', 'ASSIGNMENT', 'IMPROVEMENTS', 'COMPLIANCE', 'FORCE_MAJEURE']
        })
      });

      if (!response.ok) {
        throw new Error('Failed to compare all clauses');
      }

      const result = await response.json();
      setAllClausesComparison(result);
      setSuccess('All clauses comparison completed successfully');

    } catch (err) {
      setError('Failed to compare all clauses: ' + err.message);
    } finally {
      setAllClausesLoading(false);
    }
  };

  const renderExtractionTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Lease Obligation Extraction</Typography>
        <Box display="flex" gap={2}>
          {extractionResults.length >= 2 && (
            <Button
              variant="outlined"
              startIcon={<CompareIcon />}
              onClick={handleCompareAllClauses}
              disabled={allClausesLoading}
            >
              {allClausesLoading ? 'Comparing...' : 'Compare All Clauses'}
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setExtractionDialogOpen(true)}
          >
            Extract Obligations
          </Button>
        </Box>
      </Box>

      {extractionResults.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="textSecondary" align="center">
              No extractions performed yet
            </Typography>
            <Typography variant="body2" color="textSecondary" align="center">
              Click "Extract Obligations" to start analyzing lease documents
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {extractionResults.map((result, index) => (
            <Grid item xs={12} md={6} key={index}>
              <StyledCard>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {result.document_id}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    {result.obligations.length} obligations extracted
                  </Typography>
                  
                  <Box mt={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Risk Distribution:
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {Object.entries(result.summary.risk_distribution).map(([level, count]) => (
                        <RiskChip
                          key={level}
                          label={`${level}: ${count}`}
                          size="small"
                          risklevel={level}
                        />
                      ))}
                    </Box>
                  </Box>
                  
                  <Box mt={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Market Compliance: {result.summary.market_standard_percentage.toFixed(1)}%
                    </Typography>
                  </Box>

                  {/* Extracted Clauses - Clickable for Comparison */}
                  <Box mt={3}>
                    <Typography variant="subtitle2" gutterBottom>
                      Extracted Clauses:
                    </Typography>
                    <Box maxHeight="300px" overflow="auto">
                      {result.obligations.slice(0, 5).map((obligation, clauseIndex) => (
                        <Card 
                          key={clauseIndex} 
                          sx={{ 
                            mb: 1, 
                            cursor: 'pointer',
                            '&:hover': { 
                              backgroundColor: 'action.hover',
                              boxShadow: 2
                            }
                          }}
                          onClick={() => handleClauseSelection(obligation, result.document_id)}
                        >
                          <CardContent sx={{ p: 2 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                              <Typography variant="subtitle2" color="primary">
                                {obligation.obligation_type}
                              </Typography>
                              <Box display="flex" gap={1}>
                                <RiskChip
                                  label={obligation.risk_level}
                                  size="small"
                                  risklevel={obligation.risk_level}
                                />
                                <LeverageChip
                                  label={obligation.negotiation_leverage.replace('LEVERAGE_', '')}
                                  size="small"
                                  leveragelevel={obligation.negotiation_leverage}
                                />
                              </Box>
                            </Box>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                              }}
                            >
                              {obligation.clause_text}
                            </Typography>
                            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                              Click to compare across documents
                            </Typography>
                          </CardContent>
                        </Card>
                      ))}
                      {result.obligations.length > 5 && (
                        <Typography variant="caption" color="textSecondary">
                          ... and {result.obligations.length - 5} more clauses
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </CardContent>
              </StyledCard>
            </Grid>
          ))}
        </Grid>
      )}

      {/* All Clauses Side-by-Side Comparison */}
      {allClausesComparison && (
        <Box mt={4}>
          <Typography variant="h5" gutterBottom>
            Side-by-Side Clause Comparison
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Compare all extracted clauses across documents
          </Typography>
          
          {/* Summary Statistics */}
          <Card sx={{ mb: 3, p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Comparison Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">
                  Total Documents
                </Typography>
                <Typography variant="h6">
                  {allClausesComparison.summary?.total_documents || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">
                  Categories Found
                </Typography>
                <Typography variant="h6">
                  {allClausesComparison.summary?.total_categories || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">
                  Common Clauses
                </Typography>
                <Typography variant="h6">
                  {allClausesComparison.summary?.common_clauses_count || 0}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">
                  Unique Clauses
                </Typography>
                <Typography variant="h6">
                  {allClausesComparison.summary?.unique_clauses_count || 0}
                </Typography>
              </Grid>
            </Grid>
          </Card>

          {/* Category-wise Comparison */}
          {Object.entries(allClausesComparison.comparison_matrix || {}).map(([category, matrix]) => (
            <Card key={category} sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  {category.replace('_', ' ')} Clauses
                </Typography>
                
                {/* Common Clauses */}
                {matrix.common_clauses && matrix.common_clauses.length > 0 && (
                  <Box mb={3}>
                    <Typography variant="subtitle2" gutterBottom>
                      Common Clauses ({matrix.common_clauses.length})
                    </Typography>
                    {matrix.common_clauses.map((clause, index) => (
                      <Card key={index} sx={{ p: 2, mb: 2, backgroundColor: 'success.light', color: 'success.contrastText' }}>
                        <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                          "{clause.text}"
                        </Typography>
                        <Typography variant="caption">
                          Found in: {clause.documents?.join(', ')}
                        </Typography>
                      </Card>
                    ))}
                  </Box>
                )}

                {/* Side-by-Side Unique Clauses */}
                <Typography variant="subtitle2" gutterBottom>
                  Document-Specific Clauses
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(matrix.unique_clauses || {}).map(([docId, clauses]) => (
                    <Grid item xs={12} md={6} key={docId}>
                      <Card sx={{ p: 2, height: '100%' }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                          {docId}
                        </Typography>
                        <Typography variant="caption" color="textSecondary" gutterBottom>
                          {clauses.length} unique clauses
                        </Typography>
                        
                        {clauses.map((clause, clauseIndex) => (
                          <Card key={clauseIndex} sx={{ p: 2, mb: 2, backgroundColor: 'grey.50' }}>
                            <Typography variant="body2" sx={{ mb: 1, fontStyle: 'italic' }}>
                              "{clause.text}"
                            </Typography>
                            <Box display="flex" gap={1} flexWrap="wrap">
                              <RiskChip
                                label={clause.risk_level}
                                size="small"
                                risklevel={clause.risk_level}
                              />
                              <LeverageChip
                                label={clause.negotiation_leverage?.replace('LEVERAGE_', '') || 'N/A'}
                                size="small"
                                leveragelevel={clause.negotiation_leverage}
                              />
                              <Chip
                                label={clause.market_standard ? 'Standard' : 'Non-Standard'}
                                size="small"
                                color={clause.market_standard ? 'success' : 'warning'}
                              />
                            </Box>
                            
                            {/* Extracted Fields */}
                            {clause.extracted_fields && Object.keys(clause.extracted_fields).length > 0 && (
                              <Box mt={1}>
                                <Typography variant="caption" color="textSecondary" gutterBottom>
                                  Extracted Details:
                                </Typography>
                                {Object.entries(clause.extracted_fields).map(([field, value]) => (
                                  <Box key={field} display="flex" justifyContent="space-between" mb={0.5}>
                                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                                      {field.replace('_', ' ')}:
                                    </Typography>
                                    <Typography variant="caption" fontWeight="bold">
                                      {value}
                                    </Typography>
                                  </Box>
                                ))}
                              </Box>
                            )}
                          </Card>
                        ))}
                      </Card>
                    </Grid>
                  ))}
                </Grid>

                {/* Differences */}
                {matrix.differences && matrix.differences.length > 0 && (
                  <Box mt={3}>
                    <Typography variant="subtitle2" gutterBottom>
                      Key Differences
                    </Typography>
                    {matrix.differences.map((diff, index) => (
                      <Card key={index} sx={{ p: 2, mb: 2, backgroundColor: 'warning.light' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Clause: "{diff.clause_text}"
                        </Typography>
                        <Typography variant="body2" gutterBottom>
                          Documents: {diff.documents?.join(' vs ')}
                        </Typography>
                        {diff.differences?.map((fieldDiff, fieldIndex) => (
                          <Box key={fieldIndex} display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                              {fieldDiff.field?.replace('_', ' ')}:
                            </Typography>
                            <Box display="flex" gap={2}>
                              <Typography variant="body2" color="error">
                                {fieldDiff.document1_value}
                              </Typography>
                              <Typography variant="body2">vs</Typography>
                              <Typography variant="body2" color="success.main">
                                {fieldDiff.document2_value}
                              </Typography>
                            </Box>
                          </Box>
                        ))}
                      </Card>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );

  const renderComparisonTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Document Comparison</Typography>
        <Box>
          <Button
            variant="outlined"
            onClick={() => setConfigDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Configure
          </Button>
          <Button
            variant="contained"
            startIcon={<CompareIcon />}
            onClick={() => setComparisonDialogOpen(true)}
            disabled={selectedDocuments.length < 2}
          >
            Compare Documents
          </Button>
        </Box>
      </Box>

      {!comparisonResults ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="textSecondary" align="center">
              No comparison performed yet
            </Typography>
            <Typography variant="body2" color="textSecondary" align="center">
              Select 2 or more documents and click "Compare Documents"
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {/* Risk Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <WarningIcon sx={{ mr: 1 }} />
                  Risk Analysis
                </Typography>
                <Typography variant="h4" color="error" gutterBottom>
                  {riskAnalysis?.overall_risk_score.toFixed(1)}/100
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Overall Risk Score
                </Typography>
                
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Risk Distribution:
                  </Typography>
                  {Object.entries(riskAnalysis?.risk_distribution || {}).map(([level, count]) => (
                    <Box key={level} display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">{level}:</Typography>
                      <Typography variant="body2" fontWeight="bold">{count}</Typography>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Negotiation Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrendingUpIcon sx={{ mr: 1 }} />
                  Negotiation Analysis
                </Typography>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {negotiationAnalysis?.overall_leverage_score.toFixed(1)}/100
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Overall Leverage Score
                </Typography>
                
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Market Position: {negotiationAnalysis?.market_position}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Detailed Results */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detailed Comparison Results
                </Typography>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Obligation Type</TableCell>
                        <TableCell>Risk Assessment</TableCell>
                        <TableCell>Negotiation Opportunities</TableCell>
                        <TableCell>Market Benchmark</TableCell>
                        <TableCell>Similarity Score</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {comparisonResults.results.map((result, index) => (
                        <TableRow key={index}>
                          <TableCell>{result.obligation_type}</TableCell>
                          <TableCell>
                            <RiskChip
                              label={result.risk_assessment}
                              size="small"
                              risklevel={result.risk_assessment.split(' ')[0]}
                            />
                          </TableCell>
                          <TableCell>
                            <Box>
                              {result.negotiation_opportunities.slice(0, 2).map((opp, i) => (
                                <Chip
                                  key={i}
                                  label={opp}
                                  size="small"
                                  color="primary"
                                  sx={{ mr: 1, mb: 1 }}
                                />
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {result.market_benchmark.compliance_status}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {(result.similarity_score * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );

  const renderConfigurationTab = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        Configuration Settings
      </Typography>
      
      <Grid container spacing={3}>
        {/* Extraction Rules */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extraction Rules
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Configure how lease obligations are extracted and analyzed
              </Typography>
              
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Extracted Clauses from Documents:
                </Typography>
                {extractionResults.length === 0 ? (
                  <Typography variant="body2" color="textSecondary">
                    No clauses extracted yet. Extract obligations from documents first.
                  </Typography>
                ) : (
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {Array.from(new Set(
                      extractionResults.flatMap(result => 
                        result.obligations.map(obligation => obligation.obligation_type)
                      )
                    )).map((clauseType) => (
                      <Chip key={clauseType} label={clauseType} size="small" color="primary" />
                    ))}
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Extracted Clauses Details */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extracted Clauses Details
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                View detailed information about extracted clauses from documents
              </Typography>
              
              {extractionResults.length === 0 ? (
                <Typography variant="body2" color="textSecondary">
                  No clauses extracted yet. Extract obligations from documents first.
                </Typography>
              ) : (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Clause Summary by Document:
                  </Typography>
                  <Box maxHeight="400px" overflow="auto">
                    {extractionResults.map((result, index) => (
                      <Box key={index} mb={2} p={2} border="1px solid #e0e0e0" borderRadius={1}>
                        <Typography variant="subtitle2" gutterBottom>
                          {result.document_id}
                        </Typography>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          {result.obligations.length} clauses extracted
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={0.5}>
                          {result.obligations.slice(0, 10).map((obligation, clauseIndex) => (
                            <Chip 
                              key={clauseIndex} 
                              label={obligation.obligation_type} 
                              size="small" 
                              variant="outlined"
                            />
                          ))}
                          {result.obligations.length > 10 && (
                            <Chip 
                              label={`+${result.obligations.length - 10} more`} 
                              size="small" 
                              variant="outlined"
                              color="secondary"
                            />
                          )}
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Lease Management
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Extract lease obligations, compare documents, and analyze negotiation leverage
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Extraction" />
          <Tab label="Comparison" />
          <Tab label="Configuration" />
        </Tabs>
      </Box>

      {loading && (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      )}

      {!loading && (
        <>
          {activeTab === 0 && renderExtractionTab()}
          {activeTab === 1 && renderComparisonTab()}
          {activeTab === 2 && renderConfigurationTab()}
        </>
      )}

      {/* Extraction Dialog */}
      <Dialog open={extractionDialogOpen} onClose={() => setExtractionDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Extract Lease Obligations</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Select Document</InputLabel>
            <Select
              value={newExtraction.documentId}
              onChange={(e) => setNewExtraction(prev => ({
                ...prev,
                documentId: e.target.value
              }))}
            >
              {availableDocuments.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>
                  {doc.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Focus Areas</InputLabel>
            <Select
              multiple
              value={newExtraction.focusAreas}
              onChange={(e) => setNewExtraction(prev => ({
                ...prev,
                focusAreas: e.target.value
              }))}
            >
              {comparisonConfig.focusAreas.map((area) => (
                <MenuItem key={area} value={area}>
                  {area}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExtractionDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleExtractObligations} variant="contained">
            Extract
          </Button>
        </DialogActions>
      </Dialog>

      {/* Comparison Dialog */}
      <Dialog open={comparisonDialogOpen} onClose={() => setComparisonDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Compare Documents</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Select documents to compare (minimum 2 required)
          </Typography>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Select Documents</InputLabel>
            <Select
              multiple
              value={selectedDocuments}
              onChange={(e) => setSelectedDocuments(e.target.value)}
            >
              {availableDocuments.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>
                  {doc.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Selected Documents: {selectedDocuments.length}
            </Typography>
            {selectedDocuments.map((docId) => {
              const doc = availableDocuments.find(d => d.id === docId);
              return (
                <Chip
                  key={docId}
                  label={doc?.name || docId}
                  onDelete={() => setSelectedDocuments(prev => prev.filter(id => id !== docId))}
                  sx={{ mr: 1, mb: 1 }}
                />
              );
            })}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComparisonDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCompareDocuments} 
            variant="contained"
            disabled={selectedDocuments.length < 2}
          >
            Compare
          </Button>
        </DialogActions>
      </Dialog>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Update Configuration</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Configuration changes will be applied to future extractions and comparisons
          </Typography>
          
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Risk Tolerance
            </Typography>
            <FormControl fullWidth>
              <Select
                value={comparisonConfig.riskTolerance}
                onChange={(e) => setComparisonConfig(prev => ({
                  ...prev,
                  riskTolerance: e.target.value
                }))}
              >
                <MenuItem value="LOW">Low - Conservative approach</MenuItem>
                <MenuItem value="MEDIUM">Medium - Balanced approach</MenuItem>
                <MenuItem value="HIGH">High - Aggressive approach</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box mt={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={comparisonConfig.enableRiskAnalysis}
                  onChange={(e) => setComparisonConfig(prev => ({
                    ...prev,
                    enableRiskAnalysis: e.target.checked
                  }))}
                />
              }
              label="Enable Risk Analysis"
            />
          </Box>
          
          <Box mt={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={comparisonConfig.enableNegotiationAnalysis}
                  onChange={(e) => setComparisonConfig(prev => ({
                    ...prev,
                    enableNegotiationAnalysis: e.target.checked
                  }))}
                />
              }
              label="Enable Negotiation Analysis"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateConfiguration} variant="contained">
            Update Configuration
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clause Comparison Dialog */}
      <Dialog open={clauseComparisonDialogOpen} onClose={() => setClauseComparisonDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6">
              Compare Clause: {selectedClause?.obligation_type}
            </Typography>
            <Button
              variant="contained"
              startIcon={<CompareIcon />}
              onClick={handleCompareSpecificClause}
              disabled={clauseComparisonLoading || selectedDocuments.length < 2}
            >
              {clauseComparisonLoading ? 'Comparing...' : 'Compare Across Documents'}
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedClause && (
            <Box mb={3}>
              <Typography variant="subtitle2" gutterBottom>
                Selected Clause:
              </Typography>
              <Card sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="body2">
                  {selectedClause.clause_text}
                </Typography>
                <Box display="flex" gap={1} mt={1}>
                  <RiskChip
                    label={selectedClause.risk_level}
                    size="small"
                    risklevel={selectedClause.risk_level}
                  />
                  <LeverageChip
                    label={selectedClause.negotiation_leverage.replace('LEVERAGE_', '')}
                    size="small"
                    leveragelevel={selectedClause.negotiation_leverage}
                  />
                </Box>
              </Card>
            </Box>
          )}

          {clauseComparison && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Comparison Results
              </Typography>
              
              {/* Summary */}
              <Card sx={{ mb: 3, p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="textSecondary">
                      Total Matches
                    </Typography>
                    <Typography variant="h6">
                      {clauseComparison.comparison_summary.total_matches}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="textSecondary">
                      Documents with Matches
                    </Typography>
                    <Typography variant="h6">
                      {clauseComparison.comparison_summary.documents_with_matches}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="textSecondary">
                      Risk Distribution
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {Object.entries(clauseComparison.comparison_summary.risk_distribution).map(([level, count]) => (
                        <Chip key={level} label={`${level}: ${count}`} size="small" />
                      ))}
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="textSecondary">
                      Leverage Distribution
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {Object.entries(clauseComparison.comparison_summary.leverage_distribution).map(([level, count]) => (
                        <Chip key={level} label={`${level.replace('LEVERAGE_', '')}: ${count}`} size="small" />
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </Card>

              {/* Side-by-side Comparison */}
              <Typography variant="h6" gutterBottom>
                Side-by-Side Comparison
              </Typography>
              <Grid container spacing={2}>
                {clauseComparison.similar_clauses.map((clause, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle2" color="primary" gutterBottom>
                        {clause.document_metadata.title || clause.document_id}
                      </Typography>
                      
                      <Typography variant="body2" sx={{ mb: 2, fontStyle: 'italic' }}>
                        "{clause.clause_text}"
                      </Typography>
                      
                      <Box display="flex" gap={1} mb={2}>
                        <RiskChip
                          label={clause.risk_level}
                          size="small"
                          risklevel={clause.risk_level}
                        />
                        <LeverageChip
                          label={clause.negotiation_leverage.replace('LEVERAGE_', '')}
                          size="small"
                          leveragelevel={clause.negotiation_leverage}
                        />
                        <Chip
                          label={clause.market_standard ? 'Standard' : 'Non-Standard'}
                          size="small"
                          color={clause.market_standard ? 'success' : 'warning'}
                        />
                      </Box>

                      {/* Extracted Fields Comparison */}
                      {Object.keys(clause.extracted_fields).length > 0 && (
                        <Box>
                          <Typography variant="caption" color="textSecondary" gutterBottom>
                            Extracted Fields:
                          </Typography>
                          {Object.entries(clause.extracted_fields).map(([field, value]) => (
                            <Box key={field} display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                                {field.replace('_', ' ')}:
                              </Typography>
                              <Typography variant="caption" fontWeight="bold">
                                {value}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Card>
                  </Grid>
                ))}
              </Grid>

              {/* Field Differences */}
              {clauseComparison.comparison_summary.field_differences.length > 0 && (
                <Box mt={3}>
                  <Typography variant="h6" gutterBottom>
                    Key Differences
                  </Typography>
                  {clauseComparison.comparison_summary.field_differences.map((diff, index) => (
                    <Card key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Documents: {diff.documents.join(' vs ')}
                      </Typography>
                      {diff.differences.map((fieldDiff, fieldIndex) => (
                        <Box key={fieldIndex} display="flex" justifyContent="space-between" mb={1}>
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                            {fieldDiff.field.replace('_', ' ')}:
                          </Typography>
                          <Box display="flex" gap={2}>
                            <Typography variant="body2" color="error">
                              {fieldDiff.document1_value}
                            </Typography>
                            <Typography variant="body2">vs</Typography>
                            <Typography variant="body2" color="success.main">
                              {fieldDiff.document2_value}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          )}

          {!clauseComparison && !clauseComparisonLoading && (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="textSecondary">
                Click "Compare Across Documents" to see side-by-side comparison
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClauseComparisonDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LeaseManagement;
