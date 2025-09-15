import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  AvatarGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Badge,
  Tooltip,
  IconButton,
  Tab,
  Tabs,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Security as SecurityIcon,
  People as PeopleIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Shield as ShieldIcon,
  Lock as LockIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Assessment as AssessmentIcon,
  Notifications as NotificationsIcon,
  VpnKey as VpnKeyIcon,
  AdminPanelSettings as AdminIcon,
  Gavel as ComplianceIcon,
  Timeline as AuditIcon,
  TwoFA as MfaIcon,
  ArrowBack as ArrowBackIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const SECURITY_CLASSIFICATIONS = [
  { value: 'public', label: 'Public', color: 'success', icon: '🌍' },
  { value: 'internal', label: 'Internal', color: 'info', icon: '🏢' },
  { value: 'confidential', label: 'Confidential', color: 'warning', icon: '🔒' },
  { value: 'restricted', label: 'Restricted', color: 'error', icon: '🚫' },
  { value: 'top_secret', label: 'Top Secret', color: 'error', icon: '🔐' }
];

const USER_ROLES = [
  { value: 'super_admin', label: 'Super Admin', level: 10 },
  { value: 'org_admin', label: 'Organization Admin', level: 9 },
  { value: 'project_owner', label: 'Project Owner', level: 8 },
  { value: 'project_admin', label: 'Project Admin', level: 7 },
  { value: 'project_manager', label: 'Project Manager', level: 6 },
  { value: 'senior_analyst', label: 'Senior Analyst', level: 5 },
  { value: 'analyst', label: 'Analyst', level: 4 },
  { value: 'reviewer', label: 'Reviewer', level: 3 },
  { value: 'viewer', label: 'Viewer', level: 2 },
  { value: 'guest', label: 'Guest', level: 1 }
];

const COMPLIANCE_FRAMEWORKS = [
  { value: 'sox', label: 'SOX (Sarbanes-Oxley)', description: 'Financial reporting compliance' },
  { value: 'gdpr', label: 'GDPR', description: 'EU data protection regulation' },
  { value: 'hipaa', label: 'HIPAA', description: 'Healthcare information privacy' },
  { value: 'iso27001', label: 'ISO 27001', description: 'Information security management' },
  { value: 'nist', label: 'NIST Framework', description: 'Cybersecurity framework' }
];

function EnhancedProjectSpaces() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [securityMetrics, setSecurityMetrics] = useState({});
  const [auditLogs, setAuditLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
  // Dialog states
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [inviteMemberOpen, setInviteMemberOpen] = useState(false);
  const [securityConfigOpen, setSecurityConfigOpen] = useState(false);
  const [mfaSetupOpen, setMfaSetupOpen] = useState(false);
  
  // Form states
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    security_classification: 'internal',
    encryption_enabled: true,
    requires_mfa: false,
    compliance_frameworks: [],
    ip_whitelist: [],
    data_retention_days: 2555
  });
  
  const [memberInvitation, setMemberInvitation] = useState({
    email: '',
    role: 'viewer',
    permissions: []
  });

  useEffect(() => {
    loadProjects();
    loadSecurityAlerts();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      // Mock API call - replace with actual API
      const mockProjects = [
        {
          id: 1,
          name: 'Financial Audit 2024',
          project_code: 'FINA-A1B2',
          security_classification: 'confidential',
          encryption_enabled: true,
          requires_mfa: true,
          compliance_frameworks: ['sox', 'iso27001'],
          members: 8,
          mfa_adoption_rate: 87.5,
          recent_audit_events: 156,
          high_risk_events: 2,
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 2,
          name: 'Legal Case Discovery',
          project_code: 'LEGA-C3D4',
          security_classification: 'restricted',
          encryption_enabled: true,
          requires_mfa: true,
          compliance_frameworks: ['gdpr', 'hipaa'],
          members: 5,
          mfa_adoption_rate: 100,
          recent_audit_events: 89,
          high_risk_events: 0,
          created_at: '2024-02-01T14:30:00Z'
        }
      ];
      setProjects(mockProjects);
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSecurityAlerts = async () => {
    // Mock security alerts
    const mockAlerts = [
      {
        id: 1,
        type: 'warning',
        message: 'MFA adoption rate below 90% in Financial Audit project',
        timestamp: new Date(),
        project_id: 1
      },
      {
        id: 2,
        type: 'info',
        message: '2 failed login attempts detected for user@company.com',
        timestamp: new Date(Date.now() - 3600000),
        project_id: null
      }
    ];
    setAlerts(mockAlerts);
  };

  const loadProjectDetails = async (projectId) => {
    try {
      // Mock API call for detailed project data
      const mockDetails = {
        ...projects.find(p => p.id === projectId),
        members: [
          {
            user_id: 1,
            email: 'admin@company.com',
            full_name: 'System Administrator',
            role: 'project_owner',
            joined_at: '2024-01-15T10:00:00Z',
            last_access: '2024-03-15T09:30:00Z',
            mfa_enabled: true,
            security_clearance: 'confidential'
          },
          {
            user_id: 2,
            email: 'analyst@company.com',
            full_name: 'Senior Analyst',
            role: 'senior_analyst',
            joined_at: '2024-01-16T14:20:00Z',
            last_access: '2024-03-14T16:45:00Z',
            mfa_enabled: true,
            security_clearance: 'internal'
          }
        ]
      };
      setSelectedProject(mockDetails);
      
      // Load security metrics
      const mockMetrics = {
        total_members: 8,
        mfa_adoption_rate: 87.5,
        recent_audit_events: 156,
        high_risk_events: 2,
        compliance_score: 94.2,
        encryption_status: 'active',
        last_security_scan: '2024-03-14T10:00:00Z'
      };
      setSecurityMetrics(mockMetrics);
      
      // Load audit logs
      const mockAuditLogs = [
        {
          id: 1,
          action: 'document_download',
          user_email: 'analyst@company.com',
          resource_type: 'document',
          ip_address: '192.168.1.100',
          risk_score: 10,
          timestamp: '2024-03-15T09:30:00Z',
          details: { document_name: 'Financial_Report_Q1.pdf' }
        },
        {
          id: 2,
          action: 'role_change',
          user_email: 'admin@company.com',
          resource_type: 'user',
          ip_address: '192.168.1.50',
          risk_score: 30,
          timestamp: '2024-03-14T16:20:00Z',
          details: { target_user: 'newuser@company.com', old_role: 'viewer', new_role: 'analyst' }
        }
      ];
      setAuditLogs(mockAuditLogs);
      
    } catch (error) {
      console.error('Error loading project details:', error);
    }
  };

  const handleCreateProject = async () => {
    try {
      // Mock API call
      const newProjectData = {
        ...newProject,
        id: projects.length + 1,
        project_code: `PROJ-${Math.random().toString(36).substr(2, 4).toUpperCase()}`,
        created_at: new Date().toISOString()
      };
      
      setProjects([...projects, newProjectData]);
      setCreateProjectOpen(false);
      setNewProject({
        name: '',
        description: '',
        security_classification: 'internal',
        encryption_enabled: true,
        requires_mfa: false,
        compliance_frameworks: [],
        ip_whitelist: [],
        data_retention_days: 2555
      });
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const handleInviteMember = async () => {
    try {
      // Mock API call
      console.log('Inviting member:', memberInvitation);
      setInviteMemberOpen(false);
      setMemberInvitation({
        email: '',
        role: 'viewer',
        permissions: []
      });
    } catch (error) {
      console.error('Error inviting member:', error);
    }
  };

  const getSecurityClassificationChip = (classification) => {
    const config = SECURITY_CLASSIFICATIONS.find(s => s.value === classification) || SECURITY_CLASSIFICATIONS[1];
    return (
      <Chip
        icon={<span>{config.icon}</span>}
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
      />
    );
  };

  const getRoleChip = (role) => {
    const roleConfig = USER_ROLES.find(r => r.value === role) || USER_ROLES[8];
    const getColor = (level) => {
      if (level >= 8) return 'error';
      if (level >= 6) return 'warning';
      if (level >= 4) return 'info';
      return 'default';
    };
    
    return (
      <Chip
        label={roleConfig.label}
        color={getColor(roleConfig.level)}
        size="small"
      />
    );
  };

  const renderProjectCard = (project) => (
    <Grid item xs={12} md={6} lg={4} key={project.id}>
      <Card 
        sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          border: project.high_risk_events > 0 ? '2px solid #f44336' : '1px solid #e0e0e0',
          '&:hover': { boxShadow: 6 }
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Typography variant="h6" component="h3" noWrap>
              {project.name}
            </Typography>
            {project.high_risk_events > 0 && (
              <Tooltip title={`${project.high_risk_events} high-risk events`}>
                <WarningIcon color="error" />
              </Tooltip>
            )}
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Code: {project.project_code}
          </Typography>
          
          <Box mb={2}>
            {getSecurityClassificationChip(project.security_classification)}
          </Box>
          
          <Grid container spacing={1} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center">
                <PeopleIcon fontSize="small" sx={{ mr: 1 }} />
                <Typography variant="body2">{project.members} members</Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center">
                <MfaIcon fontSize="small" sx={{ mr: 1 }} />
                <Typography variant="body2">{project.mfa_adoption_rate}% MFA</Typography>
              </Box>
            </Grid>
          </Grid>
          
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Security Features:
            </Typography>
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {project.encryption_enabled && (
                <Chip icon={<LockIcon />} label="Encrypted" size="small" color="success" />
              )}
              {project.requires_mfa && (
                <Chip icon={<ShieldIcon />} label="MFA Required" size="small" color="info" />
              )}
              {project.compliance_frameworks.map(framework => (
                <Chip 
                  key={framework} 
                  label={framework.toUpperCase()} 
                  size="small" 
                  variant="outlined" 
                />
              ))}
            </Box>
          </Box>
          
          {project.recent_audit_events > 0 && (
            <Alert severity="info" sx={{ mb: 1 }}>
              {project.recent_audit_events} audit events (30 days)
            </Alert>
          )}
        </CardContent>
        
        <CardActions>
          <Button 
            size="small" 
            startIcon={<ViewIcon />}
            onClick={() => {
              loadProjectDetails(project.id);
              setActiveTab(0);
            }}
          >
            View Details
          </Button>
          <Button 
            size="small" 
            startIcon={<SecurityIcon />}
            onClick={() => {
              setSelectedProject(project);
              setSecurityConfigOpen(true);
            }}
          >
            Security
          </Button>
        </CardActions>
      </Card>
    </Grid>
  );

  const renderProjectDetails = () => {
    if (!selectedProject) return null;

    return (
      <Container maxWidth="xl">
        <Box mb={3}>
          <Typography variant="h4" gutterBottom>
            {selectedProject.name}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Project Code: {selectedProject.project_code}
          </Typography>
        </Box>

        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab icon={<SecurityIcon />} label="Security Overview" />
          <Tab icon={<PeopleIcon />} label="Members & Roles" />
          <Tab icon={<AuditIcon />} label="Audit Logs" />
          <Tab icon={<ComplianceIcon />} label="Compliance" />
          <Tab icon={<NotificationsIcon />} label="Alerts" />
        </Tabs>

        {/* Security Overview Tab */}
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <SecurityIcon sx={{ mr: 1 }} />
                    Security Metrics
                  </Typography>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      MFA Adoption Rate
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={securityMetrics.mfa_adoption_rate || 0}
                      sx={{ mt: 1, mb: 1 }}
                    />
                    <Typography variant="body2">
                      {securityMetrics.mfa_adoption_rate || 0}%
                    </Typography>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Compliance Score
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={securityMetrics.compliance_score || 0}
                      color="success"
                      sx={{ mt: 1, mb: 1 }}
                    />
                    <Typography variant="body2">
                      {securityMetrics.compliance_score || 0}%
                    </Typography>
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="primary">
                          {securityMetrics.total_members || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Members
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="error">
                          {securityMetrics.high_risk_events || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          High Risk Events
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <LockIcon sx={{ mr: 1 }} />
                    Security Configuration
                  </Typography>
                  
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Encryption at Rest" 
                        secondary="AES-256 encryption enabled"
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        {selectedProject.requires_mfa ? (
                          <CheckCircleIcon color="success" />
                        ) : (
                          <WarningIcon color="warning" />
                        )}
                      </ListItemIcon>
                      <ListItemText 
                        primary="Multi-Factor Authentication" 
                        secondary={selectedProject.requires_mfa ? "Required for all members" : "Optional"}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <LocationIcon color="info" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="IP Restrictions" 
                        secondary={`${selectedProject.ip_whitelist?.length || 0} allowed IP ranges`}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <ScheduleIcon color="info" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Data Retention" 
                        secondary={`${selectedProject.data_retention_days || 2555} days`}
                      />
                    </ListItem>
                  </List>
                  
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    sx={{ mt: 2 }}
                    onClick={() => setSecurityConfigOpen(true)}
                  >
                    Configure Security Settings
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Members & Roles Tab */}
        {activeTab === 1 && (
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Project Members</Typography>
                <Button 
                  variant="contained" 
                  startIcon={<AddIcon />}
                  onClick={() => setInviteMemberOpen(true)}
                >
                  Invite Member
                </Button>
              </Box>
              
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Member</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Security Clearance</TableCell>
                      <TableCell>MFA Status</TableCell>
                      <TableCell>Last Access</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedProject.members?.map((member) => (
                      <TableRow key={member.user_id}>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                              {member.full_name.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {member.full_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {member.email}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          {getRoleChip(member.role)}
                        </TableCell>
                        <TableCell>
                          {getSecurityClassificationChip(member.security_clearance)}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            icon={member.mfa_enabled ? <CheckCircleIcon /> : <WarningIcon />}
                            label={member.mfa_enabled ? 'Enabled' : 'Disabled'}
                            color={member.mfa_enabled ? 'success' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(member.last_access).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <EditIcon />
                          </IconButton>
                          <IconButton size="small" color="error">
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {/* Audit Logs Tab */}
        {activeTab === 2 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Audit Events</Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>IP Address</TableCell>
                      <TableCell>Risk Score</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(log.timestamp).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={log.action.replace('_', ' ')} 
                            size="small"
                            color={log.risk_score > 50 ? 'error' : 'default'}
                          />
                        </TableCell>
                        <TableCell>{log.user_email}</TableCell>
                        <TableCell>{log.ip_address}</TableCell>
                        <TableCell>
                          <Chip 
                            label={log.risk_score}
                            color={
                              log.risk_score > 70 ? 'error' : 
                              log.risk_score > 30 ? 'warning' : 'success'
                            }
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {JSON.stringify(log.details)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}
      </Container>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>Loading secure project spaces...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {selectedProject ? (
        <Box>
          <Button 
            onClick={() => setSelectedProject(null)}
            startIcon={<ArrowBackIcon />}
            sx={{ mb: 2 }}
          >
            Back to Projects
          </Button>
          {renderProjectDetails()}
        </Box>
      ) : (
        <Box>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Box>
              <Typography variant="h4" gutterBottom>
                <SecurityIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
                Secure Project Spaces
              </Typography>
              <Typography variant="subtitle1" color="text.secondary">
                Enterprise-grade project isolation with comprehensive security controls
              </Typography>
            </Box>
            <Button 
              variant="contained" 
              size="large"
              startIcon={<AddIcon />}
              onClick={() => setCreateProjectOpen(true)}
            >
              Create Secure Project
            </Button>
          </Box>

          {/* Security Alerts */}
          {alerts.length > 0 && (
            <Box mb={3}>
              {alerts.map((alert) => (
                <Alert 
                  key={alert.id}
                  severity={alert.type}
                  sx={{ mb: 1 }}
                  action={
                    <IconButton color="inherit" size="small">
                      <CloseIcon />
                    </IconButton>
                  }
                >
                  {alert.message}
                </Alert>
              ))}
            </Box>
          )}

          {/* Projects Grid */}
          <Grid container spacing={3}>
            {projects.map(renderProjectCard)}
          </Grid>
        </Box>
      )}

      {/* Create Project Dialog */}
      <Dialog 
        open={createProjectOpen} 
        onClose={() => setCreateProjectOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Secure Project</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Project Name"
                value={newProject.name}
                onChange={(e) => setNewProject({...newProject, name: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={newProject.description}
                onChange={(e) => setNewProject({...newProject, description: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Security Classification</InputLabel>
                <Select
                  value={newProject.security_classification}
                  onChange={(e) => setNewProject({...newProject, security_classification: e.target.value})}
                >
                  {SECURITY_CLASSIFICATIONS.map(sc => (
                    <MenuItem key={sc.value} value={sc.value}>
                      <Box display="flex" alignItems="center">
                        <span style={{ marginRight: 8 }}>{sc.icon}</span>
                        {sc.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Data Retention (days)"
                value={newProject.data_retention_days}
                onChange={(e) => setNewProject({...newProject, data_retention_days: parseInt(e.target.value)})}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newProject.encryption_enabled}
                    onChange={(e) => setNewProject({...newProject, encryption_enabled: e.target.checked})}
                  />
                }
                label="Enable Encryption at Rest"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newProject.requires_mfa}
                    onChange={(e) => setNewProject({...newProject, requires_mfa: e.target.checked})}
                  />
                }
                label="Require Multi-Factor Authentication"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateProjectOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateProject}>
            Create Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invite Member Dialog */}
      <Dialog 
        open={inviteMemberOpen} 
        onClose={() => setInviteMemberOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Invite Project Member</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={memberInvitation.email}
                onChange={(e) => setMemberInvitation({...memberInvitation, email: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={memberInvitation.role}
                  onChange={(e) => setMemberInvitation({...memberInvitation, role: e.target.value})}
                >
                  {USER_ROLES.map(role => (
                    <MenuItem key={role.value} value={role.value}>
                      {role.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteMemberOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleInviteMember}>
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default EnhancedProjectSpaces;
