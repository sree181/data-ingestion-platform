import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  Badge
} from '@mui/material';
import {
  Security as SecurityIcon,
  Shield as ShieldIcon,
  Lock as LockIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Key as KeyIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useSecurityContext } from '../contexts/SecurityContext';

const SecurityDashboard = () => {
  const {
    securityData,
    userSecurity,
    loadSecurityDashboard,
    loadSecurityAlerts,
    loadComplianceFrameworks,
    loadEncryptionKeys,
    loadAuditEvents,
    resolveSecurityAlert,
    refreshSecurityData
  } = useSecurityContext();

  const [activeTab, setActiveTab] = useState(0);
  const [mfaDialogOpen, setMfaDialogOpen] = useState(false);
  const [mfaCode, setMfaCode] = useState('');
  const [newUserDialogOpen, setNewUserDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    loadSecurityDashboard();
    loadSecurityAlerts();
    loadComplianceFrameworks();
    loadEncryptionKeys(null);
    loadAuditEvents();
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleMfaSetup = () => {
    setMfaDialogOpen(true);
  };

  const handleMfaVerify = () => {
    // Implement MFA verification
    console.log('MFA Code:', mfaCode);
    setMfaDialogOpen(false);
    setMfaCode('');
  };

  const getThreatLevelColor = (level) => {
    switch (level) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getComplianceStatusColor = (status) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'partial': return 'warning';
      case 'non_compliant': return 'error';
      default: return 'default';
    }
  };

  const SecurityOverviewCard = () => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <SecurityIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6">Security Overview</Typography>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                {securityData.dashboard?.security_health?.overall_score || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Security Score
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="error.main">
                {Array.isArray(securityData.alerts) ? securityData.alerts.filter(alert => alert.status === 'active').length : 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Alerts
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="info.main">
                {securityData.dashboard?.encryption?.encrypted_documents || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Encrypted Docs
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary.main">
                {securityData.dashboard?.compliance?.compliant_projects || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Compliant Projects
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  const SecurityAlertsCard = () => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Security Alerts</Typography>
          <IconButton onClick={() => loadSecurityAlerts()}>
            <RefreshIcon />
          </IconButton>
        </Box>
        
        {securityData.alerts?.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Alert</TableCell>
                  <TableCell>Threat Level</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {securityData.alerts.slice(0, 5).map((alert, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography variant="body2">{alert.message}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.threat_level}
                        color={getThreatLevelColor(alert.threat_level)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.status}
                        color={alert.status === 'active' ? 'error' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(alert.timestamp).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => resolveSecurityAlert(alert.id)}
                      >
                        <CheckCircleIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No active security alerts
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const ComplianceCard = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Compliance Status</Typography>
        
        {securityData.dashboard?.compliance?.frameworks?.map((framework, index) => (
          <Box key={index} mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body1">{framework.name}</Typography>
              <Chip
                label={framework.status}
                color={getComplianceStatusColor(framework.status)}
                size="small"
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={framework.compliance_percentage}
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              {framework.compliance_percentage}% compliant
            </Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  );

  const UserManagementCard = () => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">User Management</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewUserDialogOpen(true)}
          >
            Add User
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" mb={1}>
              <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="body2">Active Users</Typography>
            </Box>
            <Typography variant="h4" color="primary.main">
              {securityData.dashboard?.users?.active_count || 0}
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" mb={1}>
              <GroupIcon sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="body2">Total Roles</Typography>
            </Box>
            <Typography variant="h4" color="info.main">
              {securityData.dashboard?.users?.roles_count || 0}
            </Typography>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="subtitle2" gutterBottom>Recent Activity</Typography>
        <List dense>
          {securityData.auditEvents?.slice(0, 3).map((event, index) => (
            <ListItem key={index} dense>
              <ListItemIcon>
                <TimelineIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={event.action}
                secondary={`${event.user} - ${new Date(event.timestamp).toLocaleString()}`}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );

  const EncryptionCard = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Encryption Status</Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" mb={1}>
              <LockIcon sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="body2">Encrypted Documents</Typography>
            </Box>
            <Typography variant="h4" color="success.main">
              {securityData.dashboard?.encryption?.encrypted_documents || 0}
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" mb={1}>
              <KeyIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="body2">Active Keys</Typography>
            </Box>
            <Typography variant="h4" color="warning.main">
              {securityData.encryptionKeys?.length || 0}
            </Typography>
          </Grid>
        </Grid>
        
        <Box mt={2}>
          <Typography variant="subtitle2" gutterBottom>Encryption Keys</Typography>
          {securityData.encryptionKeys?.map((key, index) => (
            <Box key={index} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2">{key.name}</Typography>
              <Chip
                label={key.status}
                color={key.status === 'active' ? 'success' : 'default'}
                size="small"
              />
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );

  const MfaSetupDialog = () => (
    <Dialog open={mfaDialogOpen} onClose={() => setMfaDialogOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Setup Multi-Factor Authentication</DialogTitle>
      <DialogContent>
        <Typography variant="body2" paragraph>
          Scan this QR code with your authenticator app to set up MFA:
        </Typography>
        
        <Box textAlign="center" mb={2}>
          <div style={{ 
            width: 200, 
            height: 200, 
            backgroundColor: '#f5f5f5', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            margin: '0 auto',
            border: '1px solid #ddd'
          }}>
            <Typography variant="caption">QR Code Placeholder</Typography>
          </div>
        </Box>
        
        <TextField
          fullWidth
          label="Enter verification code"
          value={mfaCode}
          onChange={(e) => setMfaCode(e.target.value)}
          margin="normal"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setMfaDialogOpen(false)}>Cancel</Button>
        <Button variant="contained" onClick={handleMfaVerify}>
          Verify & Enable
        </Button>
      </DialogActions>
    </Dialog>
  );

  if (securityData.loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Security Dashboard</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={refreshSecurityData}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            onClick={handleMfaSetup}
          >
            Security Settings
          </Button>
        </Box>
      </Box>

      {securityData.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {securityData.error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Alerts" />
          <Tab label="Compliance" />
          <Tab label="Users" />
          <Tab label="Encryption" />
        </Tabs>
      </Box>

      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <SecurityOverviewCard />
          </Grid>
          <Grid item xs={12} md={6}>
            <SecurityAlertsCard />
          </Grid>
          <Grid item xs={12} md={6}>
            <ComplianceCard />
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <SecurityAlertsCard />
          </Grid>
        </Grid>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <ComplianceCard />
          </Grid>
        </Grid>
      )}

      {activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <UserManagementCard />
          </Grid>
        </Grid>
      )}

      {activeTab === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <EncryptionCard />
          </Grid>
        </Grid>
      )}

      <MfaSetupDialog />
    </Box>
  );
};

export default SecurityDashboard;
