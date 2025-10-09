import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
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
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
} from '@mui/material';
import {
  Email as EmailIcon,
  Assessment as AssessmentIcon,
  FileDownload as DownloadIcon,
  Visibility as ViewIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  PlayArrow as ProcessIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  color: 'white',
  marginBottom: theme.spacing(3),
  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.2)',
}));

const ProcessCard = styled(Card)(({ theme }) => ({
  background: 'rgba(255,255,255,0.95)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.2)',
  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
}));

const StatCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  textAlign: 'center',
  padding: theme.spacing(2),
}));

const ICSRAutomation = () => {
  const [statistics, setStatistics] = useState({
    total_processed: 0,
    valid_icsrs: 0,
    invalid_icsrs: 0,
    xml_generated: 0,
    average_processing_time: 0.0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [processingEmails, setProcessingEmails] = useState(false);
  const [emailQueue, setEmailQueue] = useState([]);
  const [processedEmails, setProcessedEmails] = useState([]);

  // Mock email data for demonstration
  const mockEmails = [
    {
      id: 'email_001',
      subject: 'Adverse Event Report - Patient ID 12345',
      sender: 'doctor@hospital.com',
      received_date: '2024-01-15T10:30:00Z',
      status: 'pending',
      classification: null,
      confidence: null
    },
    {
      id: 'email_002',
      subject: 'Safety Concern - Drug X Side Effects',
      sender: 'pharmacist@clinic.com',
      received_date: '2024-01-15T11:15:00Z',
      status: 'pending',
      classification: null,
      confidence: null
    },
    {
      id: 'email_003',
      subject: 'General Inquiry about Medication',
      sender: 'patient@email.com',
      received_date: '2024-01-15T12:00:00Z',
      status: 'pending',
      classification: null,
      confidence: null
    }
  ];

  useEffect(() => {
    loadStatistics();
    setEmailQueue(mockEmails);
  }, []);

  const loadStatistics = async () => {
    try {
      const response = await fetch('/api/v1/icsr/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  const handleProcessEmails = async () => {
    setProcessingEmails(true);
    setError(null);

    try {
      // Simulate email processing
      const processingPromises = emailQueue.map(async (email, index) => {
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 1000 + index * 500));
        
        // Mock classification result
        const classifications = ['Valid ICSR', 'Invalid ICSR', 'Rejection', 'Irrelevant'];
        const classification = classifications[Math.floor(Math.random() * classifications.length)];
        const confidence = Math.random() * 0.4 + 0.6; // 0.6 to 1.0

        return {
          ...email,
          status: 'processed',
          classification,
          confidence,
          processed_date: new Date().toISOString()
        };
      });

      const results = await Promise.all(processingPromises);
      setProcessedEmails(results);
      setEmailQueue([]);
      
      // Update statistics
      const validCount = results.filter(r => r.classification === 'Valid ICSR').length;
      const invalidCount = results.filter(r => r.classification === 'Invalid ICSR').length;
      const rejectionCount = results.filter(r => r.classification === 'Rejection').length;
      const irrelevantCount = results.filter(r => r.classification === 'Irrelevant').length;

      setStatistics(prev => ({
        ...prev,
        total_processed: prev.total_processed + results.length,
        valid_icsrs: prev.valid_icsrs + validCount,
        invalid_icsrs: prev.invalid_icsrs + invalidCount + rejectionCount + irrelevantCount,
        xml_generated: prev.xml_generated + validCount
      }));

    } catch (error) {
      console.error('Error processing emails:', error);
      setError(`Email processing failed: ${error.message}`);
    } finally {
      setProcessingEmails(false);
    }
  };

  const getClassificationColor = (classification) => {
    switch (classification) {
      case 'Valid ICSR':
        return 'success';
      case 'Invalid ICSR':
        return 'error';
      case 'Rejection':
        return 'warning';
      case 'Irrelevant':
        return 'default';
      default:
        return 'default';
    }
  };

  const getClassificationIcon = (classification) => {
    switch (classification) {
      case 'Valid ICSR':
        return <CheckCircleIcon />;
      case 'Invalid ICSR':
        return <ErrorIcon />;
      case 'Rejection':
        return <WarningIcon />;
      case 'Irrelevant':
        return <InfoIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
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
            <EmailIcon sx={{ fontSize: 40, mr: 2 }} />
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                ICSR Automation
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9 }}>
                AI-powered email processing and ICSR validation for pharmacovigilance
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </StyledCard>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard>
            <Typography variant="h4" component="div">
              {statistics.total_processed}
            </Typography>
            <Typography variant="body2">
              Total Processed
            </Typography>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard>
            <Typography variant="h4" component="div" color="success.main">
              {statistics.valid_icsrs}
            </Typography>
            <Typography variant="body2">
              Valid ICSRs
            </Typography>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard>
            <Typography variant="h4" component="div" color="error.main">
              {statistics.invalid_icsrs}
            </Typography>
            <Typography variant="body2">
              Invalid ICSRs
            </Typography>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard>
            <Typography variant="h4" component="div" color="info.main">
              {statistics.xml_generated}
            </Typography>
            <Typography variant="body2">
              XML Generated
            </Typography>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard>
            <Typography variant="h4" component="div" color="warning.main">
              {statistics.average_processing_time.toFixed(1)}s
            </Typography>
            <Typography variant="body2">
              Avg. Processing Time
            </Typography>
          </StatCard>
        </Grid>
      </Grid>

      {/* Main Content */}
      <ProcessCard>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6">
              Email Processing Queue
            </Typography>
            <Box>
              <Button
                variant="contained"
                startIcon={processingEmails ? <StopIcon /> : <ProcessIcon />}
                onClick={handleProcessEmails}
                disabled={processingEmails || emailQueue.length === 0}
                color={processingEmails ? 'error' : 'primary'}
                sx={{ mr: 1 }}
              >
                {processingEmails ? 'Processing...' : 'Process Emails'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadStatistics}
              >
                Refresh
              </Button>
            </Box>
          </Box>

          {processingEmails && (
            <Box mb={3}>
              <Typography variant="body2" gutterBottom>
                Processing emails...
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Email Queue */}
          {emailQueue.length > 0 && (
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Pending Emails ({emailQueue.length})
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Subject</TableCell>
                      <TableCell>Sender</TableCell>
                      <TableCell>Received</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {emailQueue.map((email) => (
                      <TableRow key={email.id}>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {email.subject}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {email.sender}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(email.received_date)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={email.status}
                            color="warning"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton size="small">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Processed Emails */}
          {processedEmails.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Processed Emails ({processedEmails.length})
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Subject</TableCell>
                      <TableCell>Sender</TableCell>
                      <TableCell>Classification</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Processed</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {processedEmails.map((email) => (
                      <TableRow key={email.id}>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {email.subject}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {email.sender}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getClassificationIcon(email.classification)}
                            label={email.classification}
                            color={getClassificationColor(email.classification)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {(email.confidence * 100).toFixed(1)}%
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(email.processed_date)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton size="small">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          {email.classification === 'Valid ICSR' && (
                            <Tooltip title="Download XML">
                              <IconButton size="small">
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Empty State */}
          {emailQueue.length === 0 && processedEmails.length === 0 && (
            <Box textAlign="center" py={4}>
              <EmailIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No emails in queue
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload emails or connect to your email system to start processing
              </Typography>
            </Box>
          )}
        </CardContent>
      </ProcessCard>
    </Container>
  );
};

export default ICSRAutomation;

