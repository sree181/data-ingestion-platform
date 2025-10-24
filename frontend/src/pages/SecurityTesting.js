import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Snackbar,
  IconButton,
  Tooltip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Security as SecurityIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  VpnKey as KeyIcon,
  Shield as ShieldIcon,
  Assessment as AssessmentIcon,
  Gavel as GavelIcon,
  Lock as LockIcon,
  Visibility as VisibilityIcon,
  Storage as StorageIcon,
  Fingerprint as FingerprintIcon,
  Business as BusinessIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';
import apiService from '../services/api';

const SecurityTesting = () => {
  const [authToken, setAuthToken] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [expandedSections, setExpandedSections] = useState({});

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const updateTestResult = (testId, result) => {
    setTestResults(prev => ({
      ...prev,
      [testId]: result
    }));
  };

  const setTestLoading = (testId, isLoading) => {
    setLoading(prev => ({
      ...prev,
      [testId]: isLoading
    }));
  };

  const makeRequest = async (endpoint, method = 'GET', data = null) => {
    try {
      const config = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        }
      };

      if (data) {
        config.body = JSON.stringify(data);
      }

      const response = await fetch(`/api/v1${endpoint}`, config);
      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${responseData.detail || responseData.message || 'Unknown error'}`);
      }

      return responseData;
    } catch (error) {
      throw error;
    }
  };

  // Authentication Tests
  const testJWTToken = async () => {
    setTestLoading('jwt', true);
    try {
      const result = await makeRequest('/auth/login', 'POST', {
        email: 'admin@test.com',
        password: 'password123',
        organization: 'Default Organization'
      });
      
      setAuthToken(result.access_token);
      updateTestResult('jwt', { success: true, data: result });
      showSnackbar('JWT token generated successfully', 'success');
    } catch (error) {
      updateTestResult('jwt', { success: false, error: error.message });
      showSnackbar(`JWT token test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('jwt', false);
    }
  };

  const testUserAuth = async () => {
    setTestLoading('auth', true);
    try {
      if (!authToken) {
        throw new Error('Please test JWT token first');
      }
      
      const result = await makeRequest('/auth/me');
      updateTestResult('auth', { success: true, data: result });
      showSnackbar('User authentication successful', 'success');
    } catch (error) {
      updateTestResult('auth', { success: false, error: error.message });
      showSnackbar(`Authentication test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('auth', false);
    }
  };

  const testSpacePermissions = async () => {
    setTestLoading('permissions', true);
    try {
      if (!authToken) {
        throw new Error('Please test JWT token first');
      }
      
      const result = await makeRequest('/project-spaces');
      updateTestResult('permissions', { success: true, data: result });
      showSnackbar('Space permissions test successful', 'success');
    } catch (error) {
      updateTestResult('permissions', { success: false, error: error.message });
      showSnackbar(`Permissions test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('permissions', false);
    }
  };

  // Security Monitoring Tests
  const testSecurityHealth = async () => {
    setTestLoading('health', true);
    try {
      const result = await makeRequest('/security/health');
      updateTestResult('health', { success: true, data: result });
      showSnackbar('Security health check successful', 'success');
    } catch (error) {
      updateTestResult('health', { success: false, error: error.message });
      showSnackbar(`Health check failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('health', false);
    }
  };

  const testSecurityAlerts = async () => {
    setTestLoading('alerts', true);
    try {
      const result = await makeRequest('/security/alerts');
      updateTestResult('alerts', { success: true, data: result });
      showSnackbar('Security alerts retrieved successfully', 'success');
    } catch (error) {
      updateTestResult('alerts', { success: false, error: error.message });
      showSnackbar(`Alerts test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('alerts', false);
    }
  };

  const testSecurityDashboard = async () => {
    setTestLoading('dashboard', true);
    try {
      const result = await makeRequest('/security/dashboard');
      updateTestResult('dashboard', { success: true, data: result });
      showSnackbar('Security dashboard data retrieved successfully', 'success');
    } catch (error) {
      updateTestResult('dashboard', { success: false, error: error.message });
      showSnackbar(`Dashboard test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('dashboard', false);
    }
  };

  // Compliance Framework Tests
  const testComplianceFrameworks = async () => {
    setTestLoading('frameworks', true);
    try {
      const result = await makeRequest('/security/compliance/frameworks');
      updateTestResult('frameworks', { success: true, data: result });
      showSnackbar('Compliance frameworks retrieved successfully', 'success');
    } catch (error) {
      updateTestResult('frameworks', { success: false, error: error.message });
      showSnackbar(`Frameworks test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('frameworks', false);
    }
  };

  const testComplianceValidation = async () => {
    setTestLoading('validation', true);
    try {
      if (!authToken) {
        throw new Error('Please test JWT token first');
      }
      
      const result = await makeRequest('/compliance/validate', 'POST', {
        space_id: 'test-space',
        framework: 'gdpr',
        data_types: ['personal_data']
      });
      updateTestResult('validation', { success: true, data: result });
      showSnackbar('Compliance validation successful', 'success');
    } catch (error) {
      updateTestResult('validation', { success: false, error: error.message });
      showSnackbar(`Validation test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('validation', false);
    }
  };

  // Access Control Tests
  const testIPWhitelist = async () => {
    setTestLoading('ip', true);
    try {
      if (!authToken) {
        throw new Error('Please test JWT token first');
      }
      
      const result = await makeRequest('/access-control/policies', 'POST', {
        space_id: 'test-space',
        policy_type: 'ip_whitelist',
        ip_ranges: ['192.168.1.0/24', '10.0.0.0/8']
      });
      updateTestResult('ip', { success: true, data: result });
      showSnackbar('IP whitelist policy created successfully', 'success');
    } catch (error) {
      updateTestResult('ip', { success: false, error: error.message });
      showSnackbar(`IP whitelist test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('ip', false);
    }
  };

  // Audit Logging Tests
  const testAuditLogging = async () => {
    setTestLoading('audit', true);
    try {
      if (!authToken) {
        throw new Error('Please test JWT token first');
      }
      
      const result = await makeRequest('/audit/log', 'POST', {
        event_type: 'user_login',
        category: 'authentication',
        severity: 'info',
        user_id: 'test-user',
        event_description: 'User logged in successfully',
        event_data: { ip_address: '192.168.1.100', user_agent: 'Mozilla/5.0...' }
      });
      updateTestResult('audit', { success: true, data: result });
      showSnackbar('Audit event logged successfully', 'success');
    } catch (error) {
      updateTestResult('audit', { success: false, error: error.message });
      showSnackbar(`Audit logging test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('audit', false);
    }
  };

  // Data Classification Tests
  const testClassificationLevels = async () => {
    setTestLoading('levels', true);
    try {
      const result = await makeRequest('/data-classification/levels');
      updateTestResult('levels', { success: true, data: result });
      showSnackbar('Classification levels retrieved successfully', 'success');
    } catch (error) {
      updateTestResult('levels', { success: false, error: error.message });
      showSnackbar(`Classification levels test failed: ${error.message}`, 'error');
    } finally {
      setTestLoading('levels', false);
    }
  };

  const TestSection = ({ title, icon, children, sectionId }) => (
    <Accordion 
      expanded={expandedSections[sectionId]} 
      onChange={() => toggleSection(sectionId)}
      sx={{ mb: 2 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 2, flexGrow: 1 }}>
            {title}
          </Typography>
          <Badge 
            badgeContent={Object.keys(testResults).filter(key => key.startsWith(sectionId)).length} 
            color="primary"
          >
            <Chip 
              label={Object.keys(testResults).filter(key => key.startsWith(sectionId)).length > 0 ? 'Tested' : 'Not Tested'}
              color={Object.keys(testResults).filter(key => key.startsWith(sectionId)).length > 0 ? 'success' : 'default'}
              size="small"
            />
          </Badge>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          {children}
        </Grid>
      </AccordionDetails>
    </Accordion>
  );

  const TestCard = ({ title, description, testId, onTest, icon }) => (
    <Grid item xs={12} md={6} lg={4}>
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            {icon}
            <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
              {title}
            </Typography>
            {testResults[testId] && (
              testResults[testId].success ? (
                <CheckCircleIcon color="success" />
              ) : (
                <ErrorIcon color="error" />
              )
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {description}
          </Typography>
          <Button
            variant="contained"
            onClick={onTest}
            disabled={loading[testId]}
            startIcon={loading[testId] ? <CircularProgress size={20} /> : <PlayIcon />}
            fullWidth
          >
            {loading[testId] ? 'Testing...' : 'Test'}
          </Button>
          {testResults[testId] && (
            <Box sx={{ mt: 2 }}>
              <Alert 
                severity={testResults[testId].success ? 'success' : 'error'}
                sx={{ mb: 1 }}
              >
                {testResults[testId].success ? 'Test Passed' : 'Test Failed'}
              </Alert>
              <Paper sx={{ p: 1, maxHeight: 200, overflow: 'auto' }}>
                <Typography variant="caption" component="pre" sx={{ fontSize: '0.75rem' }}>
                  {JSON.stringify(testResults[testId], null, 2)}
                </Typography>
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <SecurityIcon sx={{ mr: 2, color: 'primary.main' }} />
          Security Features Testing
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Comprehensive testing suite for all security endpoints and features
        </Typography>
      </Box>

      {authToken && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Authentication Token:</strong> {authToken.substring(0, 20)}...
          </Typography>
        </Alert>
      )}

      <TestSection 
        title="Authentication & Authorization" 
        icon={<KeyIcon color="primary" />}
        sectionId="auth"
      >
        <TestCard
          title="JWT Token Generation"
          description="Test JWT token creation and validation"
          testId="jwt"
          onTest={testJWTToken}
          icon={<KeyIcon />}
        />
        <TestCard
          title="User Authentication"
          description="Test user login and authentication flow"
          testId="auth"
          onTest={testUserAuth}
          icon={<FingerprintIcon />}
        />
        <TestCard
          title="Space Permissions"
          description="Test project space permission checking"
          testId="permissions"
          onTest={testSpacePermissions}
          icon={<BusinessIcon />}
        />
      </TestSection>

      <TestSection 
        title="Security Monitoring" 
        icon={<ShieldIcon color="primary" />}
        sectionId="monitoring"
      >
        <TestCard
          title="Security Health"
          description="Check overall security system health"
          testId="health"
          onTest={testSecurityHealth}
          icon={<CheckCircleIcon />}
        />
        <TestCard
          title="Security Alerts"
          description="Test security alert system"
          testId="alerts"
          onTest={testSecurityAlerts}
          icon={<WarningIcon />}
        />
        <TestCard
          title="Security Dashboard"
          description="Test security monitoring dashboard"
          testId="dashboard"
          onTest={testSecurityDashboard}
          icon={<AssessmentIcon />}
        />
      </TestSection>

      <TestSection 
        title="Compliance Framework" 
        icon={<GavelIcon color="primary" />}
        sectionId="compliance"
      >
        <TestCard
          title="Compliance Frameworks"
          description="Test compliance framework management"
          testId="frameworks"
          onTest={testComplianceFrameworks}
          icon={<GavelIcon />}
        />
        <TestCard
          title="Compliance Validation"
          description="Test compliance validation processes"
          testId="validation"
          onTest={testComplianceValidation}
          icon={<CheckCircleIcon />}
        />
      </TestSection>

      <TestSection 
        title="Access Control" 
        icon={<LockIcon color="primary" />}
        sectionId="access"
      >
        <TestCard
          title="IP Whitelist"
          description="Test IP address whitelisting"
          testId="ip"
          onTest={testIPWhitelist}
          icon={<LockIcon />}
        />
      </TestSection>

      <TestSection 
        title="Audit Logging" 
        icon={<VisibilityIcon color="primary" />}
        sectionId="audit"
      >
        <TestCard
          title="Audit Event Logging"
          description="Test audit event logging"
          testId="audit"
          onTest={testAuditLogging}
          icon={<VisibilityIcon />}
        />
      </TestSection>

      <TestSection 
        title="Data Classification" 
        icon={<StorageIcon color="primary" />}
        sectionId="classification"
      >
        <TestCard
          title="Classification Levels"
          description="Test data classification levels"
          testId="levels"
          onTest={testClassificationLevels}
          icon={<StorageIcon />}
        />
      </TestSection>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Box>
  );
};

export default SecurityTesting;
