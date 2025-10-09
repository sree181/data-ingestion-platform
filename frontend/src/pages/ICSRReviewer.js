/**
 * ICSR Reviewer Interface
 * 
 * Allows reviewers to:
 * 1. View all ICSR-classified documents pending review
 * 2. Trigger automated ICSR data extraction (Appendix-01 fields)
 * 3. Review and edit extracted ICSR data
 * 4. Approve/Reject ICSRs
 * 5. Generate and download ICH E2B R3 XML files
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Snackbar
} from '@mui/material';
import {
  Download as DownloadIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  PlayArrow as ExtractIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  CheckCircle
} from '@mui/icons-material';
import apiService from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`icsr-tabpanel-${index}`}
      aria-labelledby={`icsr-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ICSRReviewer() {
  const [tabValue, setTabValue] = useState(0);
  const [pendingICSRs, setPendingICSRs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [icsrData, setIcsrData] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    loadPendingICSRs();
  }, []);

  const loadPendingICSRs = async () => {
    setLoading(true);
    try {
      const response = await apiService.icsr.listPending();
      setPendingICSRs(response.documents || []);
    } catch (error) {
      console.error('Failed to load pending ICSRs:', error);
      showSnackbar('Failed to load pending ICSRs', 'error');
    } finally {
      setLoading(false);
    }
  };

  const extractICSRData = async (documentId) => {
    setExtracting(true);
    try {
      const response = await apiService.icsr.extract(documentId);
      
      if (response.success) {
        showSnackbar(
          response.already_extracted 
            ? 'ICSR data already extracted'
            : 'ICSR extraction completed successfully',
          'success'
        );
        
        // Reload pending list
        await loadPendingICSRs();
        
        // Open review dialog
        setIcsrData(response.icsr_data);
        setSelectedDocument({ document_id: documentId, title: 'Document' });
        setReviewDialogOpen(true);
      }
    } catch (error) {
      console.error('ICSR extraction failed:', error);
      showSnackbar(
        error.response?.data?.detail || 'ICSR extraction failed',
        'error'
      );
    } finally {
      setExtracting(false);
    }
  };

  const viewICSRData = async (documentId) => {
    setLoading(true);
    try {
      const response = await apiService.icsr.get(documentId);
      
      if (response.success) {
        setIcsrData(response.icsr_data);
        setSelectedDocument({
          document_id: documentId,
          title: response.title
        });
        setReviewerNotes(response.reviewer_notes || '');
        setReviewDialogOpen(true);
      }
    } catch (error) {
      console.error('Failed to load ICSR data:', error);
      showSnackbar('Failed to load ICSR data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveICSRChanges = async () => {
    if (!selectedDocument) return;
    
    try {
      await apiService.icsr.update(selectedDocument.document_id, {
        document_id: selectedDocument.document_id,
        icsr_data: icsrData,
        reviewer_notes: reviewerNotes,
        status: 'pending_review'
      });
      
      showSnackbar('Changes saved successfully', 'success');
      setEditMode(false);
    } catch (error) {
      console.error('Failed to save changes:', error);
      showSnackbar('Failed to save changes', 'error');
    }
  };

  const approveICSR = async () => {
    if (!selectedDocument) return;
    
    try {
      const response = await apiService.icsr.approve({
        document_id: selectedDocument.document_id,
        reviewer_name: 'Current User', // TODO: Get from auth context
        reviewer_comments: reviewerNotes
      });
      
      if (response.success) {
        showSnackbar('ICSR approved successfully', 'success');
        setReviewDialogOpen(false);
        await loadPendingICSRs();
        
        // Offer to download XML
        if (response.xml) {
          downloadXML(selectedDocument.document_id);
        }
      }
    } catch (error) {
      console.error('Failed to approve ICSR:', error);
      showSnackbar('Failed to approve ICSR', 'error');
    }
  };

  const downloadXML = async (documentId) => {
    try {
      const response = await fetch(`/api/v1/icsr/${documentId}/xml`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `icsr_${documentId}.xml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showSnackbar('XML downloaded successfully', 'success');
    } catch (error) {
      console.error('Failed to download XML:', error);
      showSnackbar('Failed to download XML', 'error');
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const renderICSRField = (label, value, path, editable = true) => {
    if (!value) return null;
    
    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="caption" color="text.secondary" display="block">
          {label}
        </Typography>
        {editMode && editable ? (
          <TextField
            fullWidth
            size="small"
            value={value}
            onChange={(e) => {
              // Update nested field in icsrData
              const updatedData = { ...icsrData };
              const keys = path.split('.');
              let current = updatedData;
              for (let i = 0; i < keys.length - 1; i++) {
                current = current[keys[i]];
              }
              current[keys[keys.length - 1]] = e.target.value;
              setIcsrData(updatedData);
            }}
            sx={{ mt: 0.5 }}
          />
        ) : (
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {value}
          </Typography>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📋 ICSR Reviewer Interface
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Review, validate, and approve Individual Case Safety Reports extracted from literature
      </Typography>

      <Paper sx={{ mt: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Pending Review" />
          <Tab label="ICSR Classified Documents" />
        </Tabs>

        {/* Pending Review Tab */}
        <TabPanel value={tabValue} index={0}>
          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : pendingICSRs.length === 0 ? (
            <Alert severity="info">
              No ICSRs pending review. Documents must first be classified as ICSR and extracted.
            </Alert>
          ) : (
            <List>
              {pendingICSRs.map((doc, index) => (
                <React.Fragment key={doc.document_id}>
                  <ListItem
                    secondaryAction={
                      <Box>
                        <Tooltip title="View & Review">
                          <IconButton
                            edge="end"
                            onClick={() => viewICSRData(doc.document_id)}
                            sx={{ mr: 1 }}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download XML">
                          <IconButton
                            edge="end"
                            onClick={() => downloadXML(doc.document_id)}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1">{doc.title}</Typography>
                          <Chip
                            label={`${Math.round(doc.confidence * 100)}% confidence`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          PMID: {doc.pmid || 'N/A'} • Extracted: {new Date(doc.extraction_date).toLocaleString()}
                        </>
                      }
                    />
                  </ListItem>
                  {index < pendingICSRs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </TabPanel>

        {/* ICSR Classified Documents Tab */}
        <TabPanel value={tabValue} index={1}>
          <ICSRDocumentList
            onExtract={extractICSRData}
            extracting={extracting}
          />
        </TabPanel>
      </Paper>

      {/* ICSR Review Dialog */}
      <Dialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Review ICSR: {selectedDocument?.title}
            </Typography>
            <Box>
              {!editMode ? (
                <Button
                  startIcon={<EditIcon />}
                  onClick={() => setEditMode(true)}
                  sx={{ mr: 1 }}
                >
                  Edit
                </Button>
              ) : (
                <Button
                  startIcon={<SaveIcon />}
                  onClick={saveICSRChanges}
                  variant="contained"
                  sx={{ mr: 1 }}
                >
                  Save Changes
                </Button>
              )}
              <IconButton onClick={() => setReviewDialogOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {icsrData ? (
            <Box>
              {/* General Information */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">General Information</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      {renderICSRField('Report Type', icsrData.report_type, 'report_type')}
                    </Grid>
                    <Grid item xs={6}>
                      {renderICSRField('Country', icsrData.country_of_incidence, 'country_of_incidence')}
                    </Grid>
                    <Grid item xs={6}>
                      {renderICSRField('Initial Receipt Date', icsrData.initial_receipt_date, 'initial_receipt_date')}
                    </Grid>
                    <Grid item xs={6}>
                      {renderICSRField('Medically Confirmed', icsrData.medically_confirm, 'medically_confirm')}
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Patient Information */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Patient Information</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      {renderICSRField('Gender', icsrData.patient_gender, 'patient_gender')}
                    </Grid>
                    <Grid item xs={6}>
                      {renderICSRField('Age', `${icsrData.patient_age} ${icsrData.patient_age_unit}`, 'patient_age')}
                    </Grid>
                    <Grid item xs={12}>
                      {renderICSRField('Medical History', icsrData.patient_other_relevant_history, 'patient_other_relevant_history')}
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* AI-Generated Narrative */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">📝 AI-Generated ICSR Narrative</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                    <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                      {icsrData.case_narrative || 'No narrative generated'}
                    </Typography>
                  </Paper>
                </AccordionDetails>
              </Accordion>

              {/* Reviewer Notes */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Reviewer Notes
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  placeholder="Add your review comments here..."
                  variant="outlined"
                />
              </Box>
            </Box>
          ) : (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => downloadXML(selectedDocument?.document_id)}
            variant="outlined"
          >
            Download XML
          </Button>
          <Button
            startIcon={<ApproveIcon />}
            onClick={approveICSR}
            variant="contained"
            color="success"
          >
            Approve & Generate XML
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
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

/**
 * Component to display ICSR-classified documents with Extract button
 */
function ICSRDocumentList({ onExtract, extracting }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadICSRDocuments();
  }, []);

  const loadICSRDocuments = async () => {
    setLoading(true);
    try {
      // Fetch all documents with ICSR classification
      const response = await apiService.getDocuments(0, 100, {});
      console.log('📋 Total documents received:', response.results?.length);
      
      const mappedDocs = (response.results || [])
        .map(hit => ({ ...hit._source, id: hit._id }));
      
      console.log('📋 Sample doc classification:', mappedDocs[0]?.classification);
      console.log('📋 Sample doc title:', mappedDocs[0]?.title);
      
      const icsrDocs = mappedDocs.filter(doc => doc.classification === 'ICSR');
      console.log('📋 ICSR documents found:', icsrDocs.length);
      
      setDocuments(icsrDocs);
    } catch (error) {
      console.error('Failed to load ICSR documents:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (documents.length === 0) {
    return (
      <Alert severity="info">
        No ICSR-classified documents found. Please run PV Classification on your documents first.
      </Alert>
    );
  }

  return (
    <List>
      {documents.map((doc, index) => (
        <React.Fragment key={doc.id}>
          <ListItem
            secondaryAction={
              <Button
                startIcon={extracting ? <CircularProgress size={16} /> : <ExtractIcon />}
                onClick={() => onExtract(doc.id)}
                variant="contained"
                disabled={extracting || doc.icsr_data}
              >
                {doc.icsr_data ? 'Extracted' : 'Extract ICSR Data'}
              </Button>
            }
          >
            <ListItemText
              primary={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body1">{doc.title}</Typography>
                  <Chip
                    label={`ICSR (${Math.round((doc.classification_confidence || 0) * 100)}%)`}
                    size="small"
                    color="error"
                  />
                  {doc.icsr_data && (
                    <Chip
                      label="Data Extracted"
                      size="small"
                      color="success"
                      icon={<CheckCircle />}
                    />
                  )}
                </Box>
              }
              secondary={`PMID: ${doc.pmid || 'N/A'} • Classification: ${doc.classification_reasoning || 'N/A'}`}
            />
          </ListItem>
          {index < documents.length - 1 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  );
}

