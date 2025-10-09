import React, { useState, useEffect, useCallback } from 'react';
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
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Menu,
  MenuList,
  ListItemButton,
  Stack,
  Checkbox,
  OutlinedInput
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
  Close as CloseIcon,
  ContentCopy as DuplicateIcon,
  Settings as SettingsIcon,
  PersonAdd as PersonAddIcon,
  Info as InfoIcon,
  MoreVert as MoreVertIcon,
  Archive as ArchiveIcon,
  Star as StarIcon,
  Search as SearchIcon,
  StarBorder as StarBorderIcon,
  CheckBox,
  CheckBoxOutlineBlank,
  IndeterminateCheckBox,
  SelectAll as SelectAllIcon,
  Download as ExportIcon,
  PersonOutline as ChangeOwnerIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Tune as TuneIcon,
  DragIndicator as DragIcon,
  SwapVert as ReorderIcon,
  Description as DocumentsIcon,
  CloudUpload as UploadIcon,
  Api as ApiIcon,
  Folder as FolderIcon,
  SmartToy as SmartToyIcon,
  Science as ScienceIcon
} from '@mui/icons-material';
import apiService from '../services/api';
import ModelSelector from '../components/ModelSelector';
import LoginDialog from '../components/LoginDialog';
import { useAuth } from '../contexts/AuthContext';

// Source configuration for multi-source ingestion
const SOURCE_CONFIG = {
  clinicaltrials: {
    name: 'ClinicalTrials.gov',
    icon: <BusinessIcon />,
    color: '#1976d2',
    description: 'Clinical trials worldwide',
    enabled: true
  },
  fda: {
    name: 'FDA OpenFDA',
    icon: <SecurityIcon />,
    color: '#d32f2f',
    description: 'Drug safety & adverse events',
    enabled: true
  },
  chembl: {
    name: 'ChEMBL',
    icon: <ScienceIcon />,
    color: '#388e3c',
    description: 'Chemical compounds & bioactivity',
    enabled: false, // Requires API key
    requiresApiKey: true
  },
  semanticscholar: {
    name: 'Semantic Scholar',
    icon: <DocumentsIcon />,
    color: '#7b1fa2',
    description: 'AI-powered research papers',
    enabled: true
  },
  europepmc: {
    name: 'Europe PMC',
    icon: <DocumentsIcon />,
    color: '#f57c00',
    description: 'European research papers',
    enabled: true
  }
};

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

// Enhanced Create Dialog Constants
const PROJECT_COLORS = [
  { name: 'Blue', value: '#1976d2', category: 'primary' },
  { name: 'Green', value: '#388e3c', category: 'primary' },
  { name: 'Orange', value: '#f57c00', category: 'primary' },
  { name: 'Purple', value: '#7b1fa2', category: 'primary' },
  { name: 'Red', value: '#d32f2f', category: 'primary' },
  { name: 'Teal', value: '#00796b', category: 'primary' },
  { name: 'Indigo', value: '#303f9f', category: 'secondary' },
  { name: 'Pink', value: '#c2185b', category: 'secondary' },
  { name: 'Cyan', value: '#0097a7', category: 'secondary' },
  { name: 'Amber', value: '#ffa000', category: 'secondary' },
  { name: 'Deep Orange', value: '#e64a19', category: 'secondary' },
  { name: 'Brown', value: '#5d4037', category: 'secondary' }
];

const PROJECT_ICONS = [
  // Business & Work
  { name: 'Business', icon: 'business', category: 'business', component: BusinessIcon },
  { name: 'Assessment', icon: 'assessment', category: 'business', component: AssessmentIcon },
  { name: 'Gavel', icon: 'gavel', category: 'business', component: ComplianceIcon },
  { name: 'Security', icon: 'security', category: 'business', component: SecurityIcon },
  { name: 'People', icon: 'people', category: 'business', component: PeopleIcon },
  { name: 'Timeline', icon: 'timeline', category: 'business', component: AuditIcon },
  // General
  { name: 'Folder', icon: 'folder', category: 'general', component: BusinessIcon },
  { name: 'Schedule', icon: 'schedule', category: 'general', component: ScheduleIcon },
  { name: 'Location', icon: 'location', category: 'general', component: LocationIcon },
  { name: 'Notifications', icon: 'notifications', category: 'general', component: NotificationsIcon }
];

// CSS animations for bulk operations
const slideInKeyframes = `
  @keyframes slideIn {
    from {
      transform: translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
`;

function EnhancedProjectSpacesOptimized() {
  console.log('🚀 EnhancedProjectSpacesOptimized component loaded');
  const { isAuthenticated, user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [securityMetrics, setSecurityMetrics] = useState({});
  const [auditLogs, setAuditLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [showLoginDialog, setShowLoginDialog] = useState(false);
  
  // Dialog states
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [inviteMemberOpen, setInviteMemberOpen] = useState(false);
  const [securityConfigOpen, setSecurityConfigOpen] = useState(false);
  const [mfaSetupOpen, setMfaSetupOpen] = useState(false);
  const [showPubMedDialog, setShowPubMedDialog] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  
  // Model selection states
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [availableModels, setAvailableModels] = useState([]);
  const [modelLoading, setModelLoading] = useState(false);
  
  // Multi-source ingestion state
  const [ingestionQuery, setIngestionQuery] = useState('');
  const [selectedIngestionSources, setSelectedIngestionSources] = useState(['clinicaltrials', 'fda', 'europepmc']);
  const [maxResultsPerSource, setMaxResultsPerSource] = useState(5);
  const [enableAIAnalysis, setEnableAIAnalysis] = useState(true);
  const [enableEntityExtraction, setEnableEntityExtraction] = useState(true);
  const [enableRelationshipExtraction, setEnableRelationshipExtraction] = useState(true);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestionJobId, setIngestionJobId] = useState(null);
  const [ingestionProgress, setIngestionProgress] = useState(0);
  const [ingestionStatus, setIngestionStatus] = useState('');
  const [ingestionStatusData, setIngestionStatusData] = useState(null);
  
  // Form states
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    color: '#1976d2', // Default blue
    icon: 'business', // Default business icon
    security_classification: 'internal',
    encryption_enabled: true,
    requires_mfa: false,
    compliance_frameworks: [],
    ip_whitelist: [],
    data_retention_days: 2555,
    allowed_domains: []
  });

  // Enhanced dialog states
  const [formErrors, setFormErrors] = useState({});
  const [previewMode, setPreviewMode] = useState(false);
  
  // Context menu states
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedProjectForMenu, setSelectedProjectForMenu] = useState(null);
  
  // Bulk operations states
  const [selectedProjects, setSelectedProjects] = useState(new Set());
  const [bulkMode, setBulkMode] = useState(false);
  const [lastSelectedIndex, setLastSelectedIndex] = useState(-1);
  
  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [colorFilter, setColorFilter] = useState('all');
  const [memberCountFilter, setMemberCountFilter] = useState({ min: 0, max: 100 });
  const [documentCountFilter, setDocumentCountFilter] = useState({ min: 0, max: 1000 });
  const [securityFilter, setSecurityFilter] = useState('all');
  
  // PubMed search state
  const [pubmedSearch, setPubMedSearch] = useState({
    query: '',
    maxResults: 100,
    dateRange: '',
    articleTypes: []
  });
  const [pubmedJobs, setPubMedJobs] = useState([]);
  const [pubmedLoading, setPubMedLoading] = useState(false);
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Drag & Drop states
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOverItem, setDragOverItem] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [customOrder, setCustomOrder] = useState([]);
  const [dragAndDropEnabled, setDragAndDropEnabled] = useState(false);

  // Document Ingestion states
  const [fileBrowserOpen, setFileBrowserOpen] = useState(false);
  const [localFiles, setLocalFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingIngestion, setLoadingIngestion] = useState(false);
  
  const [memberInvitation, setMemberInvitation] = useState({
    email: '',
    role: 'viewer',
    permissions: []
  });

  useEffect(() => {
    loadProjects();
    loadSecurityAlerts();
    
    // Inject CSS animations
    const styleElement = document.createElement('style');
    styleElement.textContent = slideInKeyframes;
    document.head.appendChild(styleElement);
    
    return () => {
      // Cleanup: remove the style element
      if (document.head.contains(styleElement)) {
        document.head.removeChild(styleElement);
      }
    };
  }, []);

  // Poll ingestion status function
  const pollIngestionStatus = useCallback(async () => {
    console.log('🚀 pollIngestionStatus called');
    
    if (!selectedProject) {
      console.log('❌ No selectedProject, returning early');
      return;
    }
    
    try {
      console.log('📡 Making API call to get ingestion status for project:', selectedProject.id);
      const statusResponse = await apiService.getIngestionStatus(selectedProject.id);
      console.log('📊 Polling ingestion status:', statusResponse);
      setIngestionStatusData(statusResponse);
      
      console.log('✅ Updated ingestion status');
      console.log('🔍 Current ingestionStatus state after update:', statusResponse);
      
    } catch (error) {
      console.error('Error polling ingestion status:', error);
    }
  }, [selectedProject]);

  // Set up polling interval
  useEffect(() => {
    if (!selectedProject) return;
    
    console.log('🔄 Setting up polling for project:', selectedProject.id);
    
    // Initial call
    pollIngestionStatus();
    
    // Set up interval for polling every 10 seconds
    const interval = setInterval(() => {
      console.log('⏰ Polling interval triggered');
      pollIngestionStatus();
    }, 10000);
    
    return () => {
      console.log('🧹 Cleaning up polling interval');
      clearInterval(interval);
    };
  }, [selectedProject?.id]); // Only depend on project ID, not the entire object


  // Transform backend data to frontend format
  const transformBackendData = (backendSpaces) => {
    // Handle both array and object with spaces property
    const spacesArray = Array.isArray(backendSpaces) ? backendSpaces : (backendSpaces.spaces || []);
    return spacesArray.map(space => ({
      id: space.id,
      name: space.name,
      project_code: `${space.name.substring(0, 4).toUpperCase()}-${space.id}`,
      description: space.description,
      security_classification: 'internal', // Default classification
      encryption_enabled: true,
      requires_mfa: false,
      compliance_frameworks: ['iso27001'],
      members: space.member_count || 1,
      mfa_adoption_rate: 85.0,
      recent_audit_events: space.document_count * 2 || 0,
      high_risk_events: 0,
      created_at: space.created_at,
      color: space.color,
      icon: space.icon,
      document_count: space.document_count || 0,
      user_role: space.user_role || 'member'
    }));
  };

  // PubMed search functions
  const handlePubMedSearch = async () => {
    if (!selectedProject) {
      alert('Please select a project space first');
      return;
    }

    if (!pubmedSearch.query.trim()) {
      alert('Please enter a search query');
      return;
    }

    try {
      setPubMedLoading(true);
      
      const searchRequest = {
        query: pubmedSearch.query.trim(),
        max_results: pubmedSearch.maxResults,
        date_range: pubmedSearch.dateRange || null,
        article_types: pubmedSearch.articleTypes.length > 0 ? pubmedSearch.articleTypes : null,
        space_id: selectedProject.id
      };

      const response = await fetch('http://localhost:8007/api/v1/pubmed/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchRequest)
      });

      if (response.ok) {
        const result = await response.json();
        alert(`PubMed search started! Job ID: ${result.job_id}\n\nThis will search for articles and ingest them into your project space.`);
        
        // Load PubMed jobs
        await loadPubMedJobs();
        
        // Close dialog
        setShowPubMedDialog(false);
      } else {
        const error = await response.json();
        alert(`PubMed search failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('PubMed search error:', error);
      alert(`PubMed search failed: ${error.message}`);
    } finally {
      setPubMedLoading(false);
    }
  };

  const loadPubMedJobs = async () => {
    try {
      const response = await fetch(`http://localhost:8007/api/v1/pubmed/jobs?space_id=${selectedProject?.id || ''}`);
      if (response.ok) {
        const data = await response.json();
        setPubMedJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to load PubMed jobs:', error);
    }
  };

  // Model selection functions
  const handleModelSelect = (modelName) => {
    setSelectedModel(modelName);
    console.log('Model selected:', modelName);
  };

  // Multi-source ingestion functions
  const handleStartIngestion = async () => {
    if (!ingestionQuery.trim()) {
      alert('Please enter a search query for ingestion');
      return;
    }
    
    if (selectedIngestionSources.length === 0) {
      alert('Please select at least one data source');
      return;
    }

    try {
      setIsIngesting(true);
      setIngestionStatus('Starting ingestion...');
      setIngestionProgress(0);

      const response = await apiService.startIngestion({
        query: ingestionQuery,
        sources: selectedIngestionSources,
        max_results_per_source: maxResultsPerSource,
        project_space_id: selectedProject.id,
        processing_options: {
          model_name: selectedModel,
          enable_ai_analysis: enableAIAnalysis,
          enable_entity_extraction: enableEntityExtraction,
          enable_relationship_extraction: enableRelationshipExtraction
        }
      });

      setIngestionJobId(response.job_id);
      setIngestionStatus('Ingestion started successfully');
      alert(`Ingestion job started: ${response.job_id}`);
      
      // Start monitoring the job
      monitorIngestionJob(response.job_id);
      
    } catch (error) {
      console.error('Ingestion error:', error);
      alert('Failed to start ingestion: ' + (error.message || 'Unknown error'));
      setIsIngesting(false);
      setIngestionStatus('Failed to start ingestion');
    }
  };

  // Monitor ingestion job progress
  const monitorIngestionJob = async (jobId) => {
    const checkStatus = async () => {
      try {
        const response = await apiService.getIngestionJobStatus(jobId);
        const { status, progress } = response;
        
        setIngestionStatus(status);
        setIngestionProgress(progress || 0);
        
        if (status === 'completed') {
          setIsIngesting(false);
          setIngestionStatus('Ingestion completed successfully');
          alert('Ingestion completed successfully!');
          // Refresh project data to show new documents
          loadProjects();
        } else if (status === 'failed') {
          setIsIngesting(false);
          setIngestionStatus('Ingestion failed');
          alert('Ingestion failed: ' + (response.error || 'Unknown error'));
        } else if (status === 'running') {
          // Continue monitoring
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Error monitoring ingestion job:', error);
        setIsIngesting(false);
        setIngestionStatus('Error monitoring job');
      }
    };
    
    checkStatus();
  };

  const handleAuthRequired = () => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return false;
    }
    return true;
  };

  const fetchAvailableModels = async () => {
    setModelLoading(true);
    try {
      const response = await fetch('/api/v1/models/available');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
      }
    } catch (error) {
      console.error('Error fetching available models:', error);
    } finally {
      setModelLoading(false);
    }
  };

  const testModel = async (modelName) => {
    try {
      const response = await fetch(`/api/v1/models/test/${encodeURIComponent(modelName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ space_id: selectedProject?.id || '' })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Model test result:', data);
        return data.success;
      }
      return false;
    } catch (error) {
      console.error('Error testing model:', error);
      return false;
    }
  };

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      // Real API call to backend
      const backendSpaces = await apiService.getProjectSpaces();
      const transformedProjects = transformBackendData(backendSpaces);
      setProjects(transformedProjects);
    } catch (error) {
      console.error('Error loading projects:', error);
      // Fallback to empty array on error
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSecurityAlerts = async () => {
    // Initialize with empty alerts - will be populated from backend
    setAlerts([]);
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

  // Enhanced form validation
  const validateForm = () => {
    const errors = {};
    
    // Name validation
    if (!newProject.name.trim()) {
      errors.name = 'Project name is required';
    } else if (newProject.name.length < 3) {
      errors.name = 'Project name must be at least 3 characters';
    } else if (newProject.name.length > 50) {
      errors.name = 'Project name must be less than 50 characters';
    }
    
    // Description validation
    if (newProject.description && newProject.description.length > 500) {
      errors.description = 'Description must be less than 500 characters';
    }
    
    // Check for duplicate names
    if (projects.some(p => p.name.toLowerCase() === newProject.name.toLowerCase().trim())) {
      errors.name = 'A project with this name already exists';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateProject = async () => {
    try {
      // Validate form
      if (!validateForm()) {
        return;
      }

      // Real API call to create project space
      const createData = {
        name: newProject.name.trim(),
        description: newProject.description.trim(),
        color: newProject.color,
        icon: newProject.icon
      };
      
      const createdSpace = await apiService.createProjectSpace(createData);
      
      // Transform the created space to match frontend format
      const transformedProject = transformBackendData([createdSpace])[0];
      
      setProjects([...projects, transformedProject]);
      setCreateProjectOpen(false);
      
      // Reset form
      setNewProject({
        name: '',
        description: '',
        color: '#1976d2',
        icon: 'business',
        security_classification: 'internal',
        encryption_enabled: true,
        requires_mfa: false,
        compliance_frameworks: [],
        ip_whitelist: [],
        data_retention_days: 2555,
        allowed_domains: []
      });
      setFormErrors({});
      setPreviewMode(false);
    } catch (error) {
      console.error('Error creating project:', error);
      setFormErrors({ submit: 'Failed to create project space. Please try again.' });
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

  // Context Menu Handlers
  const handleContextMenu = (event, project) => {
    event.preventDefault();
    setSelectedProjectForMenu(project);
    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
          }
        : null,
    );
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
    setSelectedProjectForMenu(null);
  };

  const handleContextMenuAction = (action) => {
    if (!selectedProjectForMenu) return;
    
    switch (action) {
      case 'view':
        handleViewProject(selectedProjectForMenu);
        break;
      case 'edit':
        handleEditProject(selectedProjectForMenu);
        break;
      case 'duplicate':
        handleDuplicateProject(selectedProjectForMenu);
        break;
      case 'members':
        handleManageMembers(selectedProjectForMenu);
        break;
      case 'settings':
        handleProjectSettings(selectedProjectForMenu);
        break;
      case 'archive':
        handleArchiveProject(selectedProjectForMenu);
        break;
      case 'delete':
        handleDeleteProject(selectedProjectForMenu);
        break;
      case 'favorite':
        handleToggleFavorite(selectedProjectForMenu);
        break;
      default:
        break;
    }
    handleCloseContextMenu();
  };

  // Quick Action Handlers
  const handleViewProject = (project) => {
    console.log('👁️ handleViewProject called with project:', project?.id, project?.name);
    setSelectedProject(project);
    setActiveTab(0);
    console.log('✅ selectedProject state updated');
  };

  const handleEditProject = (project) => {
    setNewProject({
      name: project.name,
      description: project.description || '',
      color: project.color || '#1976d2',
      icon: project.icon || 'business',
      security_classification: project.security_classification || 'internal',
      encryption_enabled: project.encryption_enabled || true,
      requires_mfa: project.requires_mfa || false,
      compliance_frameworks: project.compliance_frameworks || [],
      ip_whitelist: project.ip_whitelist || [],
      data_retention_days: project.data_retention_days || 2555,
      allowed_domains: project.allowed_domains || []
    });
    setCreateProjectOpen(true);
  };

  const handleDuplicateProject = async (project) => {
    try {
      const duplicateData = {
        name: `${project.name} (Copy)`,
        description: project.description || '',
        color: project.color || '#1976d2',
        icon: project.icon || 'business'
      };
      
      const createdSpace = await apiService.createProjectSpace(duplicateData);
      const transformedProject = transformBackendData([createdSpace])[0];
      setProjects([...projects, transformedProject]);
    } catch (error) {
      console.error('Error duplicating project:', error);
      alert('Failed to duplicate project space. Please try again.');
    }
  };

  const handleManageMembers = (project) => {
    setSelectedProject(project);
    setInviteMemberOpen(true);
  };

  const handleProjectSettings = (project) => {
    setSelectedProject(project);
    setSecurityConfigOpen(true);
  };

  const handleArchiveProject = (project) => {
    // TODO: Implement archive functionality
    console.log('Archive project:', project.name);
    alert(`Archive functionality for "${project.name}" will be implemented soon.`);
  };

  const handleDeleteProject = async (project) => {
    // Show authentication level selection dialog
    const authLevel = await showAuthLevelDialog(project);
    if (!authLevel) return; // User cancelled
    
    // Humanized confirmation dialog
    const currentHour = new Date().getUTCHours();
    const isBusinessHours = currentHour >= 9 && currentHour < 17;
    const isAdmin = authLevel === 'admin' || authLevel === 'owner';
    
    let warningMessage = `⚠️  This action cannot be undone\n\n`;
    
    // Show contextual warning based on time and role
    if (!isBusinessHours && !isAdmin) {
      warningMessage += `🌙 After Hours Notice:\nWorkspace deletions are restricted to business hours (9 AM - 5 PM UTC)\nfor non-admin users to prevent accidental loss.\n\n`;
      warningMessage += `Your options:\n`;
      warningMessage += `• Wait until business hours\n`;
      warningMessage += `• Request admin approval\n\n`;
      alert(warningMessage + `Deletion cannot proceed at this time.`);
      return;
    } else if (!isBusinessHours && isAdmin) {
      warningMessage += `🛡️ Admin Override Active:\nYou're deleting outside business hours. This action will be logged.\n\n`;
    }
    
    const confirmMessage = `Delete "${project.name}"?\n\n` +
      `This workspace contains:\n` +
      `• 📄 ${project.document_count || 0} documents\n` +
      `• 👥 ${project.member_count || 1} member(s)\n` +
      `• 🔒 Security: ${project.security_classification || 'Internal'}\n\n` +
      warningMessage +
      `🔐 Authentication Level: ${authLevel.toUpperCase()}\n\n` +
      `To confirm, type: DELETE ${project.name}`;
    
    const userConfirmation = prompt(confirmMessage);
    if (userConfirmation !== `DELETE ${project.name}`) {
      alert(`❌ Deletion cancelled\n\nYou must type exactly: DELETE ${project.name}`);
      return;
    }
    
    try {
      console.log(`🗑️ Deleting project "${project.name}" with auth level: ${authLevel}`);
      
      const response = await apiService.deleteProjectSpace(project.id, authLevel);
      
      console.log('✅ Project deleted successfully:', response);
      
      // Refresh the project list
      await loadProjects();
      
      // Humanized success message
      const timestamp = response.timestamp ? new Date(response.timestamp).toLocaleString() : 'Unknown time';
      const isAfterHours = !isBusinessHours && isAdmin;
      
      alert(`✅ Workspace Deleted Successfully!\n\n` +
        `"${project.name}" has been permanently removed.\n\n` +
        `📊 Details:\n` +
        `• Deleted at: ${timestamp}\n` +
        `• Auth level: ${response.auth_level_used}\n` +
        `• Audit logged: Yes\n` +
        `• Transaction safe: Yes\n\n` +
        (isAfterHours ? `🛡️ Admin override was used (after hours)\n` : '')
      );
      
    } catch (error) {
      console.error('❌ Failed to delete workspace:', error);
      
      // Humanized error messages
      const errorMsg = error.message || error.response?.data?.detail || 'Unknown error';
      let userFriendlyMessage = `❌ Unable to Delete Workspace\n\n`;
      
      if (errorMsg.includes('business hours')) {
        userFriendlyMessage += `🌙 After Hours Protection\n\n`;
        userFriendlyMessage += `Workspace deletions are restricted to business hours\n`;
        userFriendlyMessage += `(9 AM - 5 PM UTC) to prevent accidental data loss.\n\n`;
        userFriendlyMessage += `Your options:\n`;
        userFriendlyMessage += `• ⏰ Wait until 9 AM UTC\n`;
        userFriendlyMessage += `• 👔 Request admin approval\n`;
        userFriendlyMessage += `• 📅 Schedule deletion for tomorrow\n`;
      } else if (errorMsg.includes('Rate limit')) {
        const match = errorMsg.match(/(\d+)\/(\d+)/);
        if (match) {
          userFriendlyMessage += `⏱️ Rate Limit Reached\n\n`;
          userFriendlyMessage += `You've reached the maximum deletion limit\n`;
          userFriendlyMessage += `(${match[1]} of ${match[2]} per hour).\n\n`;
          userFriendlyMessage += `This protects against accidental bulk deletions.\n\n`;
          userFriendlyMessage += `💡 Please wait about an hour and try again.`;
        } else {
          userFriendlyMessage += `⏱️ ${errorMsg}`;
        }
      } else if (error.response?.status === 403) {
        userFriendlyMessage += `🚫 Access Denied\n\n`;
        userFriendlyMessage += `You don't have permission to delete this workspace.\n\n`;
        userFriendlyMessage += `Required: ${authLevel} level access\n`;
        userFriendlyMessage += `💡 Contact a workspace owner for assistance.`;
      } else if (error.response?.status === 404) {
        userFriendlyMessage += `Workspace not found or already deleted.`;
      } else {
        userFriendlyMessage += `Something went wrong:\n${errorMsg}\n\n`;
        userFriendlyMessage += `💡 Please try again or contact support.`;
      }
      
      alert(userFriendlyMessage);
    }
  };

  const handleBulkDelete = async (projectsToDelete) => {
    const count = projectsToDelete.length;
    
    // Show authentication level selection dialog for bulk delete
    const authLevel = await showBulkAuthLevelDialog(projectsToDelete);
    if (!authLevel) return; // User cancelled
    
    // Show detailed confirmation dialog
    const projectNames = projectsToDelete.map(p => p.name).join(', ');
    const confirmMessage = `
Are you sure you want to delete ${count} project space(s)?

🔒 Security Level: ${authLevel.toUpperCase()}
📋 Projects to delete: ${projectNames}
⚠️  This action cannot be undone
📋 All documents and data will be permanently removed
🔍 This action will be logged for security auditing

Type "DELETE ALL" to confirm:`;
    
    const userConfirmation = prompt(confirmMessage);
    if (userConfirmation !== "DELETE ALL") {
      alert("Bulk deletion cancelled. You must type 'DELETE ALL' to confirm.");
      return;
    }
    
    try {
      console.log(`🗑️ Bulk deleting ${count} projects with auth level: ${authLevel}`);
      
      // Delete projects one by one with individual error handling
      const results = [];
      const errors = [];
      
      for (const project of projectsToDelete) {
        try {
          const response = await apiService.deleteProjectSpace(project.id, authLevel);
          results.push({ project: project.name, success: true, response });
          console.log(`✅ Deleted project: ${project.name}`);
        } catch (error) {
          errors.push({ project: project.name, error: error.message });
          console.error(`❌ Failed to delete project: ${project.name}`, error);
        }
      }
      
      // Clear selection
      setSelectedProjects(new Set());
      
      // Refresh the project list
      await loadProjects();
      
      // Show detailed results
      let resultMessage = `Bulk deletion completed!\n\n`;
      resultMessage += `✅ Successfully deleted: ${results.length} projects\n`;
      resultMessage += `❌ Failed: ${errors.length} projects\n\n`;
      
      if (results.length > 0) {
        resultMessage += `Successfully deleted:\n`;
        results.forEach(r => resultMessage += `• ${r.project}\n`);
      }
      
      if (errors.length > 0) {
        resultMessage += `\nFailed to delete:\n`;
        errors.forEach(e => resultMessage += `• ${e.project}: ${e.error}\n`);
      }
      
      alert(resultMessage);
      
    } catch (error) {
      console.error('❌ Failed to bulk delete projects:', error);
      alert(`Bulk deletion failed: ${error.message}`);
    }
  };

  const showAuthLevelDialog = (project) => {
    return new Promise((resolve) => {
      const dialog = document.createElement('div');
      dialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 400px; width: 90%;">
            <h3 style="margin: 0 0 15px 0; color: #333;">Delete Project: ${project.name}</h3>
            <p style="margin: 0 0 15px 0; color: #666;">Select your authentication level:</p>
            <div style="margin-bottom: 20px;">
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="owner" checked style="margin-right: 8px;">
                <strong>Owner</strong> - Only space owners can delete (most secure)
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="admin" style="margin-right: 8px;">
                <strong>Admin</strong> - Space owners and admins can delete
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="member" style="margin-right: 8px;">
                <strong>Member</strong> - Space owners, admins, and members can delete
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="viewer" style="margin-right: 8px;">
                <strong>Viewer</strong> - Anyone with access can delete (least secure)
              </label>
            </div>
            <div style="text-align: right;">
              <button id="cancelBtn" style="margin-right: 10px; padding: 8px 16px; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer;">Cancel</button>
              <button id="deleteBtn" style="padding: 8px 16px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;">Delete</button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(dialog);
      
      const cancelBtn = dialog.querySelector('#cancelBtn');
      const deleteBtn = dialog.querySelector('#deleteBtn');
      
      cancelBtn.onclick = () => {
        document.body.removeChild(dialog);
        resolve(null);
      };
      
      deleteBtn.onclick = () => {
        const selectedLevel = dialog.querySelector('input[name="authLevel"]:checked').value;
        document.body.removeChild(dialog);
        resolve(selectedLevel);
      };
    });
  };

  const showBulkAuthLevelDialog = (projects) => {
    return new Promise((resolve) => {
      const projectNames = projects.map(p => p.name).join(', ');
      const dialog = document.createElement('div');
      dialog.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
          <div style="background: white; padding: 20px; border-radius: 8px; max-width: 500px; width: 90%;">
            <h3 style="margin: 0 0 15px 0; color: #333;">Bulk Delete ${projects.length} Projects</h3>
            <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Projects to delete:</p>
            <div style="background: #f5f5f5; padding: 10px; border-radius: 4px; margin-bottom: 15px; max-height: 100px; overflow-y: auto;">
              <p style="margin: 0; font-size: 12px; color: #555;">${projectNames}</p>
            </div>
            <p style="margin: 0 0 15px 0; color: #666;">Select your authentication level:</p>
            <div style="margin-bottom: 20px;">
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="owner" checked style="margin-right: 8px;">
                <strong>Owner</strong> - Only space owners can delete (most secure)
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="admin" style="margin-right: 8px;">
                <strong>Admin</strong> - Space owners and admins can delete
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="member" style="margin-right: 8px;">
                <strong>Member</strong> - Space owners, admins, and members can delete
              </label>
              <label style="display: block; margin-bottom: 10px;">
                <input type="radio" name="authLevel" value="viewer" style="margin-right: 8px;">
                <strong>Viewer</strong> - Anyone with access can delete (least secure)
              </label>
            </div>
            <div style="text-align: right;">
              <button id="cancelBtn" style="margin-right: 10px; padding: 8px 16px; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer;">Cancel</button>
              <button id="deleteBtn" style="padding: 8px 16px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;">Delete All</button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(dialog);
      
      const cancelBtn = dialog.querySelector('#cancelBtn');
      const deleteBtn = dialog.querySelector('#deleteBtn');
      
      cancelBtn.onclick = () => {
        document.body.removeChild(dialog);
        resolve(null);
      };
      
      deleteBtn.onclick = () => {
        const selectedLevel = dialog.querySelector('input[name="authLevel"]:checked').value;
        document.body.removeChild(dialog);
        resolve(selectedLevel);
      };
    });
  };

  const handleToggleFavorite = (project) => {
    // TODO: Implement favorite functionality
    console.log('Toggle favorite for project:', project.name);
    alert(`Favorite functionality for "${project.name}" will be implemented soon.`);
  };

  // Bulk Operations Handlers
  const handleToggleBulkMode = () => {
    setBulkMode(!bulkMode);
    if (bulkMode) {
      // Exit bulk mode - clear selections
      setSelectedProjects(new Set());
      setLastSelectedIndex(-1);
    }
  };

  const handleProjectSelection = (projectId, event) => {
    event.stopPropagation();
    
    const newSelected = new Set(selectedProjects);
    const projectIndex = projects.findIndex(p => p.id === projectId);
    
    if (event.shiftKey && lastSelectedIndex !== -1) {
      // Range selection
      const start = Math.min(lastSelectedIndex, projectIndex);
      const end = Math.max(lastSelectedIndex, projectIndex);
      
      for (let i = start; i <= end; i++) {
        if (projects[i]) {
          newSelected.add(projects[i].id);
        }
      }
    } else {
      // Individual selection
      if (newSelected.has(projectId)) {
        newSelected.delete(projectId);
      } else {
        newSelected.add(projectId);
      }
      setLastSelectedIndex(projectIndex);
    }
    
    setSelectedProjects(newSelected);
    
    // Auto-enter bulk mode if items are selected
    if (newSelected.size > 0 && !bulkMode) {
      setBulkMode(true);
    }
    // Auto-exit bulk mode if no items are selected
    if (newSelected.size === 0 && bulkMode) {
      setBulkMode(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedProjects.size === projects.length) {
      // Deselect all
      setSelectedProjects(new Set());
      setBulkMode(false);
    } else {
      // Select all
      const allIds = new Set(projects.map(p => p.id));
      setSelectedProjects(allIds);
      setBulkMode(true);
    }
    setLastSelectedIndex(-1);
  };

  const handleBulkAction = async (action) => {
    const selectedProjectsList = projects.filter(p => selectedProjects.has(p.id));
    const selectedCount = selectedProjectsList.length;
    
    switch (action) {
      case 'delete':
        handleBulkDelete(selectedProjectsList);
        break;
        
      case 'archive':
        if (window.confirm(`Archive ${selectedCount} project space(s)?`)) {
          console.log('Bulk archive:', selectedProjectsList.map(p => p.name));
          alert(`Bulk archive functionality for ${selectedCount} spaces will be implemented soon.`);
        }
        break;
        
      case 'duplicate':
        if (window.confirm(`Create copies of ${selectedCount} project space(s)?`)) {
          try {
            for (const project of selectedProjectsList) {
              const duplicateData = {
                name: `${project.name} (Copy)`,
                description: project.description || '',
                color: project.color || '#1976d2',
                icon: project.icon || 'business'
              };
              
              const createdSpace = await apiService.createProjectSpace(duplicateData);
              const transformedProject = transformBackendData([createdSpace])[0];
              setProjects(prev => [...prev, transformedProject]);
            }
            
            // Clear selections after successful duplication
            setSelectedProjects(new Set());
            setBulkMode(false);
          } catch (error) {
            console.error('Error in bulk duplicate:', error);
            alert('Failed to duplicate some project spaces. Please try again.');
          }
        }
        break;
        
      case 'export':
        console.log('Bulk export:', selectedProjectsList.map(p => p.name));
        alert(`Export functionality for ${selectedCount} spaces will be implemented soon.`);
        break;
        
      case 'changeOwner':
        console.log('Bulk change owner:', selectedProjectsList.map(p => p.name));
        alert(`Change owner functionality for ${selectedCount} spaces will be implemented soon.`);
        break;
        
      default:
        break;
    }
  };

  // Search and Filter Logic
  const getFilteredAndSortedProjects = () => {
    let filtered = [...projects];

    // Text search
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      filtered = filtered.filter(project => 
        project.name.toLowerCase().includes(term) ||
        project.description?.toLowerCase().includes(term) ||
        project.project_code?.toLowerCase().includes(term)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(project => {
        const status = getProjectStatus(project);
        return status.label.toLowerCase().replace(' ', '_') === statusFilter;
      });
    }

    // Color filter
    if (colorFilter !== 'all') {
      filtered = filtered.filter(project => project.color === colorFilter);
    }

    // Member count filter
    filtered = filtered.filter(project => {
      const members = project.members || 1;
      return members >= memberCountFilter.min && members <= memberCountFilter.max;
    });

    // Document count filter
    filtered = filtered.filter(project => {
      const docs = project.document_count || 0;
      return docs >= documentCountFilter.min && docs <= documentCountFilter.max;
    });

    // Security filter
    if (securityFilter !== 'all') {
      filtered = filtered.filter(project => 
        project.security_classification === securityFilter
      );
    }

    // Sorting
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'date':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        case 'members':
          aValue = a.members || 1;
          bValue = b.members || 1;
          break;
        case 'documents':
          aValue = a.document_count || 0;
          bValue = b.document_count || 0;
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }

      if (typeof aValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return sortOrder === 'asc' 
          ? aValue - bValue
          : bValue - aValue;
      }
    });

    return filtered;
  };

  const getProjectStatus = (project) => {
    if (project.recent_audit_events > 50) return { label: 'Active', color: 'success' };
    if (project.recent_audit_events > 10) return { label: 'Moderate', color: 'warning' };
    return { label: 'Low Activity', color: 'default' };
  };

  const clearAllFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setColorFilter('all');
    setMemberCountFilter({ min: 0, max: 100 });
    setDocumentCountFilter({ min: 0, max: 1000 });
    setSecurityFilter('all');
    setSortBy('name');
    setSortOrder('asc');
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (searchTerm.trim()) count++;
    if (statusFilter !== 'all') count++;
    if (colorFilter !== 'all') count++;
    if (memberCountFilter.min > 0 || memberCountFilter.max < 100) count++;
    if (documentCountFilter.min > 0 || documentCountFilter.max < 1000) count++;
    if (securityFilter !== 'all') count++;
    return count;
  };

  // Drag & Drop Logic
  const getOrderedProjects = () => {
    const filteredProjects = getFilteredAndSortedProjects();
    
    if (!dragAndDropEnabled || customOrder.length === 0) {
      return filteredProjects;
    }

    // Apply custom order only if no filters/search are active and sort is by custom
    const hasActiveFilters = getActiveFilterCount() > 0 || searchTerm.trim();
    if (hasActiveFilters || sortBy !== 'custom') {
      return filteredProjects;
    }

    // Sort by custom order
    const orderedProjects = [];
    const projectMap = new Map(filteredProjects.map(p => [p.id, p]));
    
    // Add projects in custom order
    customOrder.forEach(id => {
      if (projectMap.has(id)) {
        orderedProjects.push(projectMap.get(id));
        projectMap.delete(id);
      }
    });
    
    // Add any remaining projects (new ones not in custom order)
    projectMap.forEach(project => {
      orderedProjects.push(project);
    });
    
    return orderedProjects;
  };

  const handleDragStart = (e, project) => {
    if (!dragAndDropEnabled) return;
    
    setDraggedItem(project);
    setIsDragging(true);
    
    // Set drag data
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', project.id);
    
    // Add drag image styling
    e.target.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    if (!dragAndDropEnabled) return;
    
    e.target.style.opacity = '1';
    setDraggedItem(null);
    setDragOverItem(null);
    setIsDragging(false);
  };

  const handleDragOver = (e, project) => {
    if (!dragAndDropEnabled || !draggedItem) return;
    
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    if (project.id !== draggedItem.id) {
      setDragOverItem(project);
    }
  };

  const handleDragLeave = (e) => {
    if (!dragAndDropEnabled) return;
    
    // Only clear drag over if we're actually leaving the card
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setDragOverItem(null);
    }
  };

  const handleDrop = (e, dropTarget) => {
    if (!dragAndDropEnabled || !draggedItem || !dropTarget) return;
    
    e.preventDefault();
    
    if (draggedItem.id === dropTarget.id) return;
    
    const currentProjects = getFilteredAndSortedProjects();
    const newOrder = [...currentProjects.map(p => p.id)];
    
    // Remove dragged item from its current position
    const draggedIndex = newOrder.indexOf(draggedItem.id);
    const targetIndex = newOrder.indexOf(dropTarget.id);
    
    if (draggedIndex !== -1) {
      newOrder.splice(draggedIndex, 1);
    }
    
    // Insert at new position
    const finalTargetIndex = draggedIndex < targetIndex ? targetIndex : targetIndex + 1;
    newOrder.splice(finalTargetIndex, 0, draggedItem.id);
    
    // Update custom order and switch to custom sort
    setCustomOrder(newOrder);
    setSortBy('custom');
    
    // Save to localStorage for persistence
    try {
      localStorage.setItem('projectSpacesOrder', JSON.stringify(newOrder));
    } catch (error) {
      console.warn('Could not save project order to localStorage:', error);
    }
    
    setDragOverItem(null);
  };

  const toggleDragAndDrop = () => {
    const newEnabled = !dragAndDropEnabled;
    setDragAndDropEnabled(newEnabled);
    
    if (newEnabled) {
      // Initialize custom order from current filtered projects
      const currentProjects = getFilteredAndSortedProjects();
      const currentOrder = currentProjects.map(p => p.id);
      setCustomOrder(currentOrder);
      setSortBy('custom');
      
      // Try to load saved order from localStorage
      try {
        const savedOrder = localStorage.getItem('projectSpacesOrder');
        if (savedOrder) {
          const parsedOrder = JSON.parse(savedOrder);
          setCustomOrder(parsedOrder);
        }
      } catch (error) {
        console.warn('Could not load project order from localStorage:', error);
      }
    } else {
      // Reset to default sorting when disabling
      setSortBy('name');
      setSortOrder('asc');
    }
  };

  const resetCustomOrder = () => {
    const currentProjects = getFilteredAndSortedProjects();
    const defaultOrder = currentProjects.map(p => p.id);
    setCustomOrder(defaultOrder);

    try {
      localStorage.removeItem('projectSpacesOrder');
    } catch (error) {
      console.warn('Could not clear project order from localStorage:', error);
    }
  };

  // Document Ingestion Handlers
  const handleBrowseLocalFiles = async () => {
    if (!selectedProject) return;
    
    try {
      setLoadingFiles(true);
      setFileBrowserOpen(true);
      
      const filesResponse = await apiService.getLocalFiles(selectedProject.id);
      setLocalFiles(filesResponse.files);
      setSelectedFiles(new Set());
    } catch (error) {
      console.error('Error loading local files:', error);
      alert('Failed to load local files. Please try again.');
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleFileSelection = (filePath, isSelected) => {
    const newSelected = new Set(selectedFiles);
    if (isSelected) {
      newSelected.add(filePath);
    } else {
      newSelected.delete(filePath);
    }
    setSelectedFiles(newSelected);
  };

  const handleSelectAllFiles = () => {
    if (selectedFiles.size === localFiles.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(localFiles.map(f => f.path)));
    }
  };

  const handleStartLocalIngestion = async () => {
    if (!selectedProject || selectedFiles.size === 0) return;
    
    // Check authentication
    if (!handleAuthRequired()) return;
    
    try {
      setLoadingIngestion(true);
      
      const ingestionRequest = {
        file_paths: Array.from(selectedFiles),
        processing_options: {
          model: selectedModel,  // ✅ Pass the selected model
          extract_text: true,
          extract_metadata: true,
          generate_embeddings: true
        }
      };
      
      console.log('🚀 Starting batch ingestion with request:', ingestionRequest);
      console.log('📁 Selected files:', Array.from(selectedFiles));
      console.log('🤖 Selected model:', selectedModel);
      
      const result = await apiService.startBatchIngestion(selectedProject.id, ingestionRequest);
      
      alert(`Batch ingestion started with ${selectedModel}! Job ID: ${result.job_id}`);
      setFileBrowserOpen(false);
      setSelectedFiles(new Set());
      
      // Start polling for status updates
      pollIngestionStatus();
      
    } catch (error) {
      console.error('Error starting ingestion:', error);
      alert('Failed to start ingestion. Please try again.');
    } finally {
      setLoadingIngestion(false);
    }
  };


  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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

  const renderProjectCard = (project) => {
    // Calculate processing progress based on document count and audit events
    const processingProgress = project.document_count > 0 
      ? Math.min((project.recent_audit_events / (project.document_count * 2)) * 100, 100)
      : 0;
    
    // Get status based on activity
    const status = getProjectStatus(project);
    
    return (
      <Grid item xs={12} md={6} lg={4} key={project.id}>
        <Card 
          draggable={dragAndDropEnabled}
          onDragStart={(e) => handleDragStart(e, project)}
          onDragEnd={handleDragEnd}
          onDragOver={(e) => handleDragOver(e, project)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, project)}
          onContextMenu={(e) => handleContextMenu(e, project)}
          sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            border: dragOverItem?.id === project.id
              ? '3px solid #4caf50'
              : selectedProjects.has(project.id) 
                ? '3px solid #1976d2' 
                : project.high_risk_events > 0 
                  ? '2px solid #f44336' 
                  : '1px solid #e0e0e0',
            borderRadius: 3,
            background: dragOverItem?.id === project.id
              ? 'linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%)'
              : selectedProjects.has(project.id)
                ? 'linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%)'
                : 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)',
            cursor: dragAndDropEnabled 
              ? 'grab' 
              : bulkMode 
                ? 'pointer' 
                : 'context-menu',
            position: 'relative',
            transform: selectedProjects.has(project.id) ? 'scale(0.98)' : 'scale(1)',
            transition: 'all 0.3s ease-in-out',
            opacity: draggedItem?.id === project.id ? 0.5 : 1,
            '&:hover': { 
              boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
              transform: selectedProjects.has(project.id) ? 'scale(0.98) translateY(-2px)' : 'translateY(-2px)',
            },
            '&:active': {
              cursor: dragAndDropEnabled ? 'grabbing' : 'pointer'
            }
          }}
          onClick={(e) => {
            if (bulkMode && !dragAndDropEnabled) {
              handleProjectSelection(project.id, e);
            }
          }}
        >
          {/* Selection Checkbox */}
          {(bulkMode || selectedProjects.has(project.id)) && (
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                left: 8,
                zIndex: 2,
                backgroundColor: 'rgba(255,255,255,0.9)',
                borderRadius: '50%',
                p: 0.5,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <IconButton
                size="small"
                onClick={(e) => handleProjectSelection(project.id, e)}
                sx={{ 
                  color: selectedProjects.has(project.id) ? 'primary.main' : 'text.secondary',
                  p: 0.5
                }}
              >
                {selectedProjects.has(project.id) ? (
                  <CheckBox fontSize="small" />
                ) : (
                  <CheckBoxOutlineBlank fontSize="small" />
                )}
              </IconButton>
            </Box>
          )}
          {/* Header with Icon and Status */}
          <Box 
            sx={{ 
              background: `linear-gradient(135deg, ${project.color || '#1976d2'} 0%, ${project.color || '#1976d2'}CC 100%)`,
              color: 'white',
              p: 2,
              borderRadius: '12px 12px 0 0'
            }}
          >
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
              <Box display="flex" alignItems="center">
                <Box
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    borderRadius: '50%',
                    p: 1,
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {project.icon === 'science' ? <AssessmentIcon /> : 
                   project.icon === 'gavel' ? <ComplianceIcon /> : 
                   <BusinessIcon />}
                </Box>
                <Box>
                  <Typography variant="h6" component="h3" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {project.name}
                  </Typography>
                  <Chip 
                    label={status.label} 
                    size="small" 
                    color={status.color}
                    sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  />
                </Box>
              </Box>
              
              <Box display="flex" alignItems="center" gap={1}>
                {project.high_risk_events > 0 && (
                  <Tooltip title={`${project.high_risk_events} high-risk events`}>
                    <WarningIcon sx={{ color: '#ffeb3b' }} />
                  </Tooltip>
                )}
                
                {/* Drag Handle */}
                {dragAndDropEnabled && (
                  <Tooltip title="Drag to reorder">
                    <IconButton
                      size="small"
                      sx={{
                        color: 'rgba(255,255,255,0.8)',
                        cursor: 'grab',
                        '&:hover': {
                          backgroundColor: 'rgba(255,255,255,0.1)',
                          color: 'white'
                        },
                        '&:active': {
                          cursor: 'grabbing'
                        }
                      }}
                    >
                      <DragIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}

                {/* Quick Actions Button */}
                {!dragAndDropEnabled && (
                  <Tooltip title="Quick Actions">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleContextMenu(e, project);
                      }}
                      sx={{
                        color: 'rgba(255,255,255,0.8)',
                        '&:hover': {
                          backgroundColor: 'rgba(255,255,255,0.1)',
                          color: 'white'
                        }
                      }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Box>
          </Box>

          <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
            {/* Description only - project_code (ID) removed from card view */}
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.5, minHeight: '40px' }}>
              {project.description || 'No description available'}
            </Typography>

            {/* Real-time Ingestion Progress */}
            {project.ingestionProgress && (
              <Box sx={{ mb: 2, p: 2, backgroundColor: '#e8f5e8', borderRadius: 2, border: '1px solid #4caf50' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={16} thickness={4} sx={{ color: '#4caf50' }} />
                    <Typography variant="body2" fontWeight={600} color="#2e7d32">
                      Document Ingestion {project.ingestionProgress.status === 'completed' ? 'Completed' : 'In Progress'}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="#2e7d32" fontWeight={500}>
                    {project.ingestionProgress.processed}/{project.ingestionProgress.total} files
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={(project.ingestionProgress.processed / project.ingestionProgress.total) * 100}
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    backgroundColor: '#c8e6c9',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 3,
                      backgroundColor: '#4caf50'
                    }
                  }}
                />
                <Box display="flex" justifyContent="space-between" mt={0.5}>
                  <Typography variant="caption" color="#2e7d32">
                    ✅ {project.ingestionProgress.successful} successful
                  </Typography>
                  {project.ingestionProgress.failed > 0 && (
                    <Typography variant="caption" color="#d32f2f">
                      ❌ {project.ingestionProgress.failed} failed
                    </Typography>
                  )}
                </Box>
              </Box>
            )}

            {/* Progress Section */}
            <Box sx={{ mb: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2" fontWeight={500}>
                  Processing Progress
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {Math.round(processingProgress)}%
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={processingProgress}
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: '#e0e0e0',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    background: `linear-gradient(90deg, ${project.color || '#1976d2'}, ${project.color || '#1976d2'}CC)`
                  }
                }}
              />
            </Box>

            {/* Stats Grid */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <Box 
                  sx={{ 
                    textAlign: 'center', 
                    p: 1.5, 
                    backgroundColor: '#f8f9fa', 
                    borderRadius: 2,
                    border: '1px solid #e9ecef'
                  }}
                >
                  <Typography variant="h6" color="primary" fontWeight={600}>
                    {project.document_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Documents
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box 
                  sx={{ 
                    textAlign: 'center', 
                    p: 1.5, 
                    backgroundColor: '#f8f9fa', 
                    borderRadius: 2,
                    border: '1px solid #e9ecef'
                  }}
                >
                  <Typography variant="h6" color="primary" fontWeight={600}>
                    {project.members || 1}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Members
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            {/* Security & Features */}
            <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
              {getSecurityClassificationChip(project.security_classification)}
              {project.encryption_enabled && (
                <Chip 
                  icon={<LockIcon fontSize="small" />}
                  label="Encrypted" 
                  size="small" 
                  color="success"
                  variant="outlined"
                />
              )}
              {project.requires_mfa && (
                <Chip 
                  icon={<ShieldIcon fontSize="small" />}
                  label="MFA" 
                  size="small" 
                  color="warning"
                  variant="outlined"
                />
              )}
            </Box>

            {/* Recent Activity */}
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                Recent Activity: {project.recent_audit_events} events
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last updated: {new Date(project.created_at).toLocaleDateString()}
              </Typography>
            </Box>
          </CardContent>
          
          {/* Enhanced Action Bar */}
          <CardActions 
            sx={{ 
              justifyContent: 'space-between', 
              px: 2.5, 
              pb: 2.5,
              pt: 0,
              borderTop: '1px solid #f0f0f0'
            }}
          >
            <Box display="flex" gap={1}>
              <Button
                variant="contained"
                size="small"
                startIcon={<ViewIcon />}
                onClick={() => {
                  loadProjectDetails(project.id);
                  setActiveTab(0);
                }}
                sx={{ 
                  textTransform: 'none',
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${project.color || '#1976d2'} 0%, ${project.color || '#1976d2'}CC 100%)`
                }}
              >
                View
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<SecurityIcon />}
                onClick={() => {
                  setSelectedProject(project);
                  setSecurityConfigOpen(true);
                }}
                sx={{ textTransform: 'none', borderRadius: 2 }}
              >
                Manage
              </Button>
            </Box>
            
            <Box display="flex" alignItems="center" gap={1}>
              <Tooltip title={`Role: ${project.user_role}`}>
                <Chip 
                  label={project.user_role} 
                  size="small" 
                  color="primary"
                  variant="outlined"
                />
              </Tooltip>
            </Box>
          </CardActions>
        </Card>
      </Grid>
    );
  };

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
          <Tab icon={<DocumentsIcon />} label="Document Manager" />
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

        {/* Document Manager Tab */}
        {activeTab === 1 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DocumentsIcon />
                Document Ingestion Pipeline
              </Typography>
              
              <Grid container spacing={3}>
                {/* Local Documents Section */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <FolderIcon />
                      Local Documents
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Select documents from the Searchable/ folder for ingestion into this project space.
                    </Typography>
                    
                    <Button
                      variant="contained"
                      startIcon={<UploadIcon />}
                      fullWidth
                      sx={{ mb: 2 }}
                      onClick={handleBrowseLocalFiles}
                    >
                      Browse Local Files
                    </Button>
                    
                    <Typography variant="body2" color="text.secondary">
                      📁 Available: ~2,600 PDF documents
                    </Typography>
                  </Card>
                </Grid>

                {/* Multi-Source Ingestion Section */}
                <Grid item xs={12} md={6}>
                  <Card variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ApiIcon />
                      Multi-Source Ingestion
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Search and ingest documents from multiple external data sources.
                    </Typography>
                    
                    <Stack spacing={2}>
                      {/* Search Query */}
                      <TextField
                        fullWidth
                        label="Search Query"
                        placeholder="Enter search query (e.g., 'COVID-19 vaccine efficacy')"
                        value={ingestionQuery}
                        onChange={(e) => setIngestionQuery(e.target.value)}
                        size="small"
                      />
                      
                      {/* Data Sources Selection */}
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Select Data Sources
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {Object.entries(SOURCE_CONFIG).map(([sourceId, config]) => (
                            <Chip
                              key={sourceId}
                              label={config.name}
                              icon={config.icon}
                              color={selectedIngestionSources.includes(sourceId) ? 'primary' : 'default'}
                              variant={selectedIngestionSources.includes(sourceId) ? 'filled' : 'outlined'}
                              onClick={() => {
                                if (selectedIngestionSources.includes(sourceId)) {
                                  setSelectedIngestionSources(prev => prev.filter(s => s !== sourceId));
                                } else {
                                  setSelectedIngestionSources(prev => [...prev, sourceId]);
                                }
                              }}
                              disabled={!config.enabled}
                              size="small"
                              sx={{
                                '&.MuiChip-filled': {
                                  bgcolor: config.color,
                                  color: 'white'
                                }
                              }}
                            />
                          ))}
                        </Box>
                      </Box>
                      
                      {/* Advanced Options */}
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Advanced Options
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <TextField
                              fullWidth
                              label="Max Results per Source"
                              type="number"
                              value={maxResultsPerSource}
                              onChange={(e) => setMaxResultsPerSource(parseInt(e.target.value) || 5)}
                              inputProps={{ min: 1, max: 50 }}
                              size="small"
                            />
                          </Grid>
                          <Grid item xs={6}>
                            <FormControl fullWidth size="small">
                              <InputLabel>AI Model</InputLabel>
                              <Select
                                value={selectedModel}
                                onChange={(e) => setSelectedModel(e.target.value)}
                                label="AI Model"
                              >
                                <MenuItem value="phi3:mini">Phi3 Mini</MenuItem>
                                <MenuItem value="llama3.1:8b">Llama 3.1 8B</MenuItem>
                                <MenuItem value="gpt-4">GPT-4</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                        </Grid>
                        
                        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={enableAIAnalysis}
                                onChange={(e) => setEnableAIAnalysis(e.target.checked)}
                                size="small"
                              />
                            }
                            label="AI Analysis"
                          />
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={enableEntityExtraction}
                                onChange={(e) => setEnableEntityExtraction(e.target.checked)}
                                size="small"
                              />
                            }
                            label="Entity Extraction"
                          />
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={enableRelationshipExtraction}
                                onChange={(e) => setEnableRelationshipExtraction(e.target.checked)}
                                size="small"
                              />
                            }
                            label="Relationships"
                          />
                        </Box>
                      </Box>
                      
                      {/* Start Ingestion Button */}
                      <Button
                        variant="contained"
                        startIcon={isIngesting ? <CircularProgress size={16} /> : <UploadIcon />}
                        fullWidth
                        onClick={handleStartIngestion}
                        disabled={isIngesting || !ingestionQuery || selectedIngestionSources.length === 0}
                        sx={{ mt: 1 }}
                      >
                        {isIngesting ? 'Ingesting...' : 'Start Multi-Source Ingestion'}
                      </Button>
                    </Stack>
                  </Card>
                </Grid>

                {/* Ingestion Status Section */}
                <Grid item xs={12}>
                  <Card variant="outlined" sx={{ p: 2 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6">
                        📊 Ingestion Status
                      </Typography>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          console.log('🔄 Manual refresh triggered');
                          console.log('🔄 Current selectedProject:', selectedProject?.id);
                          console.log('🔄 pollIngestionStatus function:', typeof pollIngestionStatus);
                          if (pollIngestionStatus) {
                            pollIngestionStatus();
                          } else {
                            console.error('❌ pollIngestionStatus function is not available');
                          }
                        }}
                        sx={{ textTransform: 'none' }}
                      >
                        Refresh Status
                      </Button>
                    </Box>
                    
                    {/* Multi-Source Ingestion Progress */}
                    {isIngesting && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Multi-Source Ingestion Progress
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={ingestionProgress} 
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {ingestionStatus} ({ingestionProgress}%)
                        </Typography>
                        {ingestionJobId && (
                          <Typography variant="caption" color="text.secondary">
                            Job ID: {ingestionJobId}
                          </Typography>
                        )}
                      </Box>
                    )}
                    
                    {/* Debug information */}
                    <Box sx={{ mb: 2, p: 1, backgroundColor: '#f5f5f5', borderRadius: 1, fontSize: '12px' }}>
                      <Typography variant="caption" color="text.secondary" component="pre">
                        {`Debug: ingestionStatusData = ${JSON.stringify(ingestionStatusData, null, 2) || 'null'}`}
                      </Typography>
                    </Box>
                    
                    {ingestionStatusData ? (
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Box textAlign="center" p={2} sx={{ backgroundColor: 'success.light', borderRadius: 2 }}>
                            <Typography variant="h4" fontWeight={600} color="success.dark">
                              {ingestionStatusData.total_documents || 0}
                            </Typography>
                            <Typography variant="body2" color="success.dark">
                              Total Documents
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={3}>
                          <Box textAlign="center" p={2} sx={{ backgroundColor: 'info.light', borderRadius: 2 }}>
                            <Typography variant="h4" fontWeight={600} color="info.dark">
                              {ingestionStatusData.success_rate || 0}%
                            </Typography>
                            <Typography variant="body2" color="info.dark">
                              Success Rate
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={3}>
                          <Box textAlign="center" p={2} sx={{ backgroundColor: 'warning.light', borderRadius: 2 }}>
                            <Typography variant="h4" fontWeight={600} color="warning.dark">
                              {ingestionStatusData.active_jobs || 0}
                            </Typography>
                            <Typography variant="body2" color="warning.dark">
                              Active Jobs
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={3}>
                          <Box textAlign="center" p={2} sx={{ backgroundColor: 'primary.light', borderRadius: 2 }}>
                            <Typography variant="h4" fontWeight={600} color="primary.dark">
                              {ingestionStatus.jobs?.length || 0}
                            </Typography>
                            <Typography variant="body2" color="primary.dark">
                              Total Jobs
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    ) : (
                      <Box textAlign="center" py={4}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Loading ingestion status...
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {`Debug: ingestionStatus = ${JSON.stringify(ingestionStatus) || 'null'}`}
                        </Typography>
                      </Box>
                    )}

                    {ingestionStatusData?.jobs && ingestionStatusData.jobs.length > 0 ? (
                      <Box mt={3}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Recent Ingestion Jobs
                        </Typography>
                        {ingestionStatusData.jobs.slice(0, 3).map((job, index) => (
                          <Box key={job.job_id} sx={{ mb: 1, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2" fontWeight={500}>
                                Job {index + 1}: {job.status}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {job.created_at ? new Date(job.created_at).toLocaleString() : 'Unknown date'}
                              </Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              Files: {job.successful_files || 0}/{job.total_files || 0} successful
                              {job.failed_files > 0 && `, ${job.failed_files} failed`}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    ) : (
                      <Box mt={3}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Recent Ingestion Activity
                        </Typography>
                        <Alert severity="info" sx={{ mt: 1 }}>
                          No recent ingestion jobs found. Use the options above to start ingesting documents into this project space.
                        </Alert>
                      </Box>
                    )}
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Members & Roles Tab */}
        {activeTab === 2 && (
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
        {activeTab === 3 && (
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
                            {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'Unknown date'}
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

        {/* Compliance Tab */}
        {activeTab === 4 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Compliance Overview</Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        📋 Compliance Frameworks
                      </Typography>
                      <Stack spacing={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>ISO 27001</Typography>
                          <Chip label="Compliant" color="success" size="small" />
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>GDPR</Typography>
                          <Chip label="Compliant" color="success" size="small" />
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography>SOC 2</Typography>
                          <Chip label="In Progress" color="warning" size="small" />
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        🔍 Recent Assessments
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Last assessment: March 1, 2024
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Next assessment: June 1, 2024
                      </Typography>
                      <Button variant="outlined" size="small" sx={{ mt: 2 }}>
                        View Assessment Report
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Alerts Tab */}
        {activeTab === 5 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Security Alerts</Typography>
              <Stack spacing={2}>
                <Alert severity="warning">
                  <Typography variant="body2">
                    <strong>High Risk Document Access</strong><br />
                    Unusual access pattern detected for classified documents in the last 24 hours.
                  </Typography>
                </Alert>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>System Update Available</strong><br />
                    Security patches are available for the document processing system.
                  </Typography>
                </Alert>
                <Alert severity="success">
                  <Typography variant="body2">
                    <strong>Backup Completed</strong><br />
                    Daily backup completed successfully at 2:00 AM.
                  </Typography>
                </Alert>
              </Stack>
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
          {/* Enhanced Header */}
          <Box 
            sx={{
              background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
              borderRadius: 4,
              p: 4,
              mb: 4,
              color: 'white',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Background Pattern */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '40%',
                height: '100%',
                backgroundImage: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.1"%3E%3Ccircle cx="30" cy="30" r="4"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
                opacity: 0.3
              }}
            />
            
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
              <Box sx={{ zIndex: 1 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <Box
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      borderRadius: '50%',
                      p: 1.5,
                      mr: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <BusinessIcon sx={{ fontSize: 32 }} />
                  </Box>
                  <Box>
                    <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                      Project Spaces
                    </Typography>
                    <Typography variant="h6" sx={{ opacity: 0.9, fontWeight: 300 }}>
                      Organize, secure, and collaborate on your documents
                    </Typography>
                  </Box>
                </Box>
                
                {/* Quick Stats */}
                <Grid container spacing={3} sx={{ mt: 2 }}>
                  <Grid item>
                    <Box textAlign="center">
                      <Typography variant="h4" fontWeight={600}>
                        {projects.length}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.8 }}>
                        Active Spaces
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item>
                    <Box textAlign="center">
                      <Typography variant="h4" fontWeight={600}>
                        {projects.reduce((sum, p) => sum + (p.document_count || 0), 0)}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.8 }}>
                        Total Documents
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item>
                    <Box textAlign="center">
                      <Typography variant="h4" fontWeight={600}>
                        {projects.reduce((sum, p) => sum + (p.members || 0), 0)}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.8 }}>
                        Team Members
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
              
              {/* Action Buttons */}
              <Box display="flex" gap={2} sx={{ zIndex: 1 }}>
                <Button 
                  variant="contained"
                  size="large"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateProjectOpen(true)}
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    color: 'white',
                    textTransform: 'none',
                    borderRadius: 3,
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.3)',
                      transform: 'translateY(-1px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.2)'
                    }
                  }}
                >
                  Create New Space
                </Button>
              </Box>
            </Box>
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

          {/* Search and Filter Panel */}
          <Box sx={{ mb: 3 }}>
            {/* Search Bar */}
            <Box display="flex" gap={2} mb={2} alignItems="center">
              <TextField
                fullWidth
                placeholder="Search project spaces by name, description, or code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />,
                  endAdornment: searchTerm && (
                    <IconButton
                      size="small"
                      onClick={() => setSearchTerm('')}
                      sx={{ color: 'text.secondary' }}
                    >
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'background.paper'
                  }
                }}
              />

              {/* Sort Controls */}
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Sort by</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  label="Sort by"
                  startAdornment={<SortIcon fontSize="small" sx={{ mr: 1 }} />}
                >
                  <MenuItem value="name">Name</MenuItem>
                  <MenuItem value="date">Date Created</MenuItem>
                  <MenuItem value="members">Members</MenuItem>
                  <MenuItem value="documents">Documents</MenuItem>
                  {dragAndDropEnabled && <MenuItem value="custom">Custom Order</MenuItem>}
                </Select>
              </FormControl>

              <IconButton
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                sx={{ 
                  border: '1px solid',
                  borderColor: 'divider',
                  '&:hover': { backgroundColor: 'action.hover' }
                }}
              >
                {sortOrder === 'asc' ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>

              {/* Advanced Filters Toggle */}
              <Button
                variant="outlined"
                startIcon={<TuneIcon />}
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                sx={{
                  minWidth: 'auto',
                  borderColor: showAdvancedFilters ? 'primary.main' : 'divider',
                  backgroundColor: showAdvancedFilters ? 'primary.light' : 'transparent'
                }}
              >
                Filters {getActiveFilterCount() > 0 && `(${getActiveFilterCount()})`}
              </Button>

              {/* Drag & Drop Toggle */}
              <Button
                variant="outlined"
                startIcon={<ReorderIcon />}
                onClick={toggleDragAndDrop}
                sx={{
                  minWidth: 'auto',
                  borderColor: dragAndDropEnabled ? 'success.main' : 'divider',
                  backgroundColor: dragAndDropEnabled ? 'success.light' : 'transparent',
                  color: dragAndDropEnabled ? 'success.main' : 'text.primary',
                  '&:hover': {
                    backgroundColor: dragAndDropEnabled ? 'success.light' : 'action.hover'
                  }
                }}
              >
                {dragAndDropEnabled ? 'Reordering' : 'Reorder'}
              </Button>
            </Box>

            {/* Advanced Filters Panel */}
            {showAdvancedFilters && (
              <Box
                sx={{
                  backgroundColor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  p: 3,
                  mb: 2
                }}
              >
                <Grid container spacing={3}>
                  {/* Status Filter */}
                  <Grid item xs={12} md={6} lg={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Status</InputLabel>
                      <Select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        label="Status"
                      >
                        <MenuItem value="all">All Status</MenuItem>
                        <MenuItem value="active">Active</MenuItem>
                        <MenuItem value="moderate">Moderate</MenuItem>
                        <MenuItem value="low_activity">Low Activity</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {/* Color Filter */}
                  <Grid item xs={12} md={6} lg={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Color</InputLabel>
                      <Select
                        value={colorFilter}
                        onChange={(e) => setColorFilter(e.target.value)}
                        label="Color"
                      >
                        <MenuItem value="all">All Colors</MenuItem>
                        {PROJECT_COLORS.map((color) => (
                          <MenuItem key={color.value} value={color.value}>
                            <Box display="flex" alignItems="center">
                              <Box
                                sx={{
                                  width: 16,
                                  height: 16,
                                  borderRadius: '50%',
                                  backgroundColor: color.value,
                                  mr: 1
                                }}
                              />
                              {color.name}
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>

                  {/* Security Filter */}
                  <Grid item xs={12} md={6} lg={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Security</InputLabel>
                      <Select
                        value={securityFilter}
                        onChange={(e) => setSecurityFilter(e.target.value)}
                        label="Security"
                      >
                        <MenuItem value="all">All Levels</MenuItem>
                        {SECURITY_CLASSIFICATIONS.map((security) => (
                          <MenuItem key={security.value} value={security.value}>
                            {security.icon} {security.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>

                  {/* Clear Filters */}
                  <Grid item xs={12} md={6} lg={3}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<ClearIcon />}
                      onClick={clearAllFilters}
                      disabled={getActiveFilterCount() === 0}
                      sx={{ height: '40px' }}
                    >
                      Clear All
                    </Button>
                  </Grid>
                </Grid>

                {/* Range Filters */}
                <Grid container spacing={3} sx={{ mt: 1 }}>
                  {/* Member Count Range */}
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" gutterBottom>
                      Member Count: {memberCountFilter.min} - {memberCountFilter.max}
                    </Typography>
                    <Box sx={{ px: 1 }}>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={memberCountFilter.min}
                        onChange={(e) => setMemberCountFilter({
                          ...memberCountFilter,
                          min: parseInt(e.target.value)
                        })}
                        style={{ width: '45%', marginRight: '10%' }}
                      />
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={memberCountFilter.max}
                        onChange={(e) => setMemberCountFilter({
                          ...memberCountFilter,
                          max: parseInt(e.target.value)
                        })}
                        style={{ width: '45%' }}
                      />
                    </Box>
                  </Grid>

                  {/* Document Count Range */}
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" gutterBottom>
                      Document Count: {documentCountFilter.min} - {documentCountFilter.max}
                    </Typography>
                    <Box sx={{ px: 1 }}>
                      <input
                        type="range"
                        min="0"
                        max="1000"
                        value={documentCountFilter.min}
                        onChange={(e) => setDocumentCountFilter({
                          ...documentCountFilter,
                          min: parseInt(e.target.value)
                        })}
                        style={{ width: '45%', marginRight: '10%' }}
                      />
                      <input
                        type="range"
                        min="0"
                        max="1000"
                        value={documentCountFilter.max}
                        onChange={(e) => setDocumentCountFilter({
                          ...documentCountFilter,
                          max: parseInt(e.target.value)
                        })}
                        style={{ width: '45%' }}
                      />
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            )}

            {/* Drag & Drop Information Panel */}
            {dragAndDropEnabled && (
              <Box
                sx={{
                  backgroundColor: 'success.light',
                  border: '1px solid',
                  borderColor: 'success.main',
                  borderRadius: 2,
                  p: 2,
                  mb: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <Box display="flex" alignItems="center" gap={2}>
                  <DragIcon sx={{ color: 'success.dark' }} />
                  <Typography variant="body2" color="success.dark">
                    <strong>Drag & Drop Mode Active</strong> - Drag cards to reorder them. Your custom order will be saved automatically.
                  </Typography>
                </Box>
                
                <Box display="flex" alignItems="center" gap={1}>
                  {customOrder.length > 0 && (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<ClearIcon />}
                      onClick={resetCustomOrder}
                      sx={{
                        borderColor: 'success.main',
                        color: 'success.dark',
                        '&:hover': {
                          backgroundColor: 'success.main',
                          color: 'white'
                        }
                      }}
                    >
                      Reset Order
                    </Button>
                  )}
                  
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<CloseIcon />}
                    onClick={toggleDragAndDrop}
                    sx={{
                      borderColor: 'success.main',
                      color: 'success.dark',
                      '&:hover': {
                        backgroundColor: 'success.main',
                        color: 'white'
                      }
                    }}
                  >
                    Exit
                  </Button>
                </Box>
              </Box>
            )}

            {/* Active Filters Chips */}
            {getActiveFilterCount() > 0 && (
              <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                {searchTerm && (
                  <Chip
                    label={`Search: "${searchTerm}"`}
                    onDelete={() => setSearchTerm('')}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {statusFilter !== 'all' && (
                  <Chip
                    label={`Status: ${statusFilter.replace('_', ' ')}`}
                    onDelete={() => setStatusFilter('all')}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {colorFilter !== 'all' && (
                  <Chip
                    label={`Color: ${PROJECT_COLORS.find(c => c.value === colorFilter)?.name}`}
                    onDelete={() => setColorFilter('all')}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {securityFilter !== 'all' && (
                  <Chip
                    label={`Security: ${SECURITY_CLASSIFICATIONS.find(s => s.value === securityFilter)?.label}`}
                    onDelete={() => setSecurityFilter('all')}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
            )}

            {/* Results Summary */}
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {getOrderedProjects().length} of {projects.length} project spaces
              {getActiveFilterCount() > 0 && ` (${getActiveFilterCount()} filters active)`}
              {dragAndDropEnabled && sortBy === 'custom' && ' - Custom order active'}
            </Typography>
          </Box>

          {/* Selection Toolbar */}
          {(bulkMode || selectedProjects.size > 0) && (
            <Box 
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                borderRadius: 2,
                p: 2,
                mb: 3,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                animation: 'slideIn 0.3s ease-out'
              }}
            >
              <Box display="flex" alignItems="center" gap={2}>
                <IconButton
                  onClick={handleSelectAll}
                  sx={{ color: 'white' }}
                  size="small"
                >
                  {selectedProjects.size === projects.length ? (
                    <CheckBox />
                  ) : selectedProjects.size > 0 ? (
                    <IndeterminateCheckBox />
                  ) : (
                    <CheckBoxOutlineBlank />
                  )}
                </IconButton>
                
                <Typography variant="h6" fontWeight={600}>
                  {selectedProjects.size === 0 
                    ? 'Select items to perform bulk actions'
                    : `${selectedProjects.size} item${selectedProjects.size !== 1 ? 's' : ''} selected`
                  }
                </Typography>
              </Box>

              {selectedProjects.size > 0 && (
                <Box display="flex" alignItems="center" gap={1}>
                  {/* Bulk Duplicate */}
                  <Tooltip title="Duplicate Selected">
                    <IconButton
                      onClick={() => handleBulkAction('duplicate')}
                      sx={{ color: 'white' }}
                      size="small"
                    >
                      <DuplicateIcon />
                    </IconButton>
                  </Tooltip>

                  {/* Bulk Export */}
                  <Tooltip title="Export Selected">
                    <IconButton
                      onClick={() => handleBulkAction('export')}
                      sx={{ color: 'white' }}
                      size="small"
                    >
                      <ExportIcon />
                    </IconButton>
                  </Tooltip>

                  {/* Change Owner */}
                  <Tooltip title="Change Owner">
                    <IconButton
                      onClick={() => handleBulkAction('changeOwner')}
                      sx={{ color: 'white' }}
                      size="small"
                    >
                      <ChangeOwnerIcon />
                    </IconButton>
                  </Tooltip>

                  <Divider orientation="vertical" flexItem sx={{ bgcolor: 'rgba(255,255,255,0.3)', mx: 1 }} />

                  {/* Bulk Archive */}
                  <Tooltip title="Archive Selected">
                    <IconButton
                      onClick={() => handleBulkAction('archive')}
                      sx={{ color: 'rgba(255,255,255,0.8)' }}
                      size="small"
                    >
                      <ArchiveIcon />
                    </IconButton>
                  </Tooltip>

                  {/* Bulk Delete */}
                  <Tooltip title="Delete Selected">
                    <IconButton
                      onClick={() => handleBulkAction('delete')}
                      sx={{ color: '#ffcdd2' }}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>

                  <Divider orientation="vertical" flexItem sx={{ bgcolor: 'rgba(255,255,255,0.3)', mx: 1 }} />

                  {/* Exit Bulk Mode */}
                  <Tooltip title="Exit Bulk Mode">
                    <IconButton
                      onClick={handleToggleBulkMode}
                      sx={{ color: 'white' }}
                      size="small"
                    >
                      <CloseIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              )}
            </Box>
          )}

          {/* Bulk Mode Toggle Button */}
          {!bulkMode && selectedProjects.size === 0 && (
            <Box display="flex" justifyContent="flex-end" mb={2}>
              <Button
                variant="outlined"
                startIcon={<SelectAllIcon />}
                onClick={handleToggleBulkMode}
                sx={{
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'primary.main',
                    color: 'white'
                  }
                }}
              >
                Enable Bulk Selection
              </Button>
            </Box>
          )}

          {/* Projects Grid */}
          <Grid container spacing={3}>
            {getOrderedProjects().map(renderProjectCard)}
          </Grid>
          
          {/* No Results Message */}
          {getFilteredAndSortedProjects().length === 0 && projects.length > 0 && (
            <Box 
              display="flex" 
              flexDirection="column" 
              alignItems="center" 
              justifyContent="center" 
              sx={{ py: 8, textAlign: 'center' }}
            >
              <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" color="text.secondary" gutterBottom>
                No project spaces found
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Try adjusting your search terms or filters to find what you're looking for.
              </Typography>
              <Button
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={clearAllFilters}
              >
                Clear All Filters
              </Button>
            </Box>
          )}
        </Box>
      )}

      {/* Create Project Dialog */}
      {/* Enhanced Create Project Dialog */}
      <Dialog 
        open={createProjectOpen} 
        onClose={() => {
          setCreateProjectOpen(false);
          setFormErrors({});
          setPreviewMode(false);
        }}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            minHeight: '600px'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
          color: 'white',
          textAlign: 'center',
          py: 3
        }}>
          <Typography variant="h4" fontWeight={600}>
            ✨ Create New Project Space
          </Typography>
          <Typography variant="subtitle1" sx={{ opacity: 0.9, mt: 1 }}>
            Design your perfect workspace with custom colors and icons
          </Typography>
        </DialogTitle>
        
        <DialogContent sx={{ p: 4 }}>
          <Grid container spacing={4}>
            {/* Left Side - Form */}
            <Grid item xs={12} md={previewMode ? 6 : 12}>
              <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                    📝 Basic Information
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Project Space Name"
                    value={newProject.name}
                    onChange={(e) => {
                      setNewProject({...newProject, name: e.target.value});
                      if (formErrors.name) setFormErrors({...formErrors, name: null});
                    }}
                    error={!!formErrors.name}
                    helperText={formErrors.name || `${newProject.name.length}/50 characters`}
                    placeholder="e.g., Legal Research, Financial Analysis"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2
                      }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Description (Optional)"
                    value={newProject.description}
                    onChange={(e) => {
                      setNewProject({...newProject, description: e.target.value});
                      if (formErrors.description) setFormErrors({...formErrors, description: null});
                    }}
                    error={!!formErrors.description}
                    helperText={formErrors.description || `${newProject.description.length}/500 characters`}
                    placeholder="Describe the purpose and scope of this project space..."
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2
                      }
                    }}
                  />
                </Grid>

                {/* Appearance */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600, mt: 2 }}>
                    🎨 Appearance
                  </Typography>
                </Grid>

                {/* Color Picker */}
                <Grid item xs={12}>
                  <Typography variant="body2" fontWeight={500} gutterBottom>
                    Choose a Color
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1.5} mt={1}>
                    {PROJECT_COLORS.map((color) => (
                      <Tooltip key={color.value} title={color.name}>
                        <Box
                          onClick={() => setNewProject({...newProject, color: color.value})}
                          sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            backgroundColor: color.value,
                            cursor: 'pointer',
                            border: newProject.color === color.value ? '3px solid #333' : '2px solid transparent',
                            transform: newProject.color === color.value ? 'scale(1.1)' : 'scale(1)',
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              transform: 'scale(1.1)',
                              boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                            }
                          }}
                        />
                      </Tooltip>
                    ))}
                  </Box>
                </Grid>

                {/* Icon Picker */}
                <Grid item xs={12}>
                  <Typography variant="body2" fontWeight={500} gutterBottom>
                    Choose an Icon
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1.5} mt={1}>
                    {PROJECT_ICONS.map((iconData) => {
                      const IconComponent = iconData.component;
                      return (
                        <Tooltip key={iconData.icon} title={iconData.name}>
                          <Box
                            onClick={() => setNewProject({...newProject, icon: iconData.icon})}
                            sx={{
                              width: 48,
                              height: 48,
                              borderRadius: 2,
                              backgroundColor: newProject.icon === iconData.icon ? newProject.color : '#f5f5f5',
                              color: newProject.icon === iconData.icon ? 'white' : newProject.color,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: 'pointer',
                              border: newProject.icon === iconData.icon ? `2px solid ${newProject.color}` : '2px solid transparent',
                              transition: 'all 0.2s ease-in-out',
                              '&:hover': {
                                backgroundColor: newProject.color,
                                color: 'white',
                                transform: 'scale(1.05)'
                              }
                            }}
                          >
                            <IconComponent fontSize="small" />
                          </Box>
                        </Tooltip>
                      );
                    })}
                  </Box>
                </Grid>

                {/* Security Configuration */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600, mt: 2 }}>
                    🔒 Security Configuration
                  </Typography>
                </Grid>

                {/* Security Classification */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Security Classification</InputLabel>
                    <Select
                      value={newProject.security_classification}
                      onChange={(e) => setNewProject({...newProject, security_classification: e.target.value})}
                      label="Security Classification"
                    >
                      <MenuItem value="public">Public</MenuItem>
                      <MenuItem value="internal">Internal</MenuItem>
                      <MenuItem value="confidential">Confidential</MenuItem>
                      <MenuItem value="restricted">Restricted</MenuItem>
                      <MenuItem value="top_secret">Top Secret</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {/* Data Retention Days */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Data Retention (Days)"
                    value={newProject.data_retention_days}
                    onChange={(e) => setNewProject({...newProject, data_retention_days: parseInt(e.target.value) || 2555})}
                    inputProps={{ min: 1, max: 3650 }}
                    helperText="How long to keep data (1-3650 days)"
                    sx={{ mb: 2 }}
                  />
                </Grid>

                {/* Encryption and MFA Toggles */}
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={newProject.encryption_enabled}
                        onChange={(e) => setNewProject({...newProject, encryption_enabled: e.target.checked})}
                        color="primary"
                      />
                    }
                    label="Enable Encryption at Rest (AES-256)"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block">
                    All documents will be encrypted using AES-256 encryption
                  </Typography>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={newProject.requires_mfa}
                        onChange={(e) => setNewProject({...newProject, requires_mfa: e.target.checked})}
                        color="primary"
                      />
                    }
                    label="Require Multi-Factor Authentication"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block">
                    All members must use MFA to access this space
                  </Typography>
                </Grid>

                {/* Compliance Frameworks */}
                <Grid item xs={12}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Compliance Frameworks</InputLabel>
                    <Select
                      multiple
                      value={newProject.compliance_frameworks}
                      onChange={(e) => setNewProject({...newProject, compliance_frameworks: e.target.value})}
                      label="Compliance Frameworks"
                      renderValue={(selected) => (selected || []).join(', ')}
                    >
                      <MenuItem value="sox">SOX (Sarbanes-Oxley)</MenuItem>
                      <MenuItem value="gdpr">GDPR (General Data Protection Regulation)</MenuItem>
                      <MenuItem value="hipaa">HIPAA (Health Insurance Portability)</MenuItem>
                      <MenuItem value="iso27001">ISO 27001 (Information Security)</MenuItem>
                      <MenuItem value="nist">NIST (National Institute of Standards)</MenuItem>
                      <MenuItem value="pci_dss">PCI DSS (Payment Card Industry)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {/* IP Whitelist */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="IP Whitelist"
                    value={(newProject.ip_whitelist || []).join(', ')}
                    onChange={(e) => setNewProject({...newProject, ip_whitelist: e.target.value.split(',').map(ip => ip.trim()).filter(ip => ip)})}
                    placeholder="192.168.1.0/24, 10.0.0.0/8"
                    helperText="Comma-separated IP addresses or ranges"
                    sx={{ mb: 2 }}
                  />
                </Grid>

                {/* Allowed Domains */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Allowed Email Domains"
                    value={(newProject.allowed_domains || []).join(', ')}
                    onChange={(e) => setNewProject({...newProject, allowed_domains: e.target.value.split(',').map(domain => domain.trim()).filter(domain => domain)})}
                    placeholder="company.com, partner.org"
                    helperText="Comma-separated email domains for invitations"
                    sx={{ mb: 2 }}
                  />
                </Grid>

                {/* Toggle Preview */}
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    onClick={() => setPreviewMode(!previewMode)}
                    startIcon={<ViewIcon />}
                    sx={{ mt: 2 }}
                  >
                    {previewMode ? 'Hide Preview' : 'Show Preview'}
                  </Button>
                </Grid>
              </Grid>
            </Grid>

            {/* Right Side - Live Preview */}
            {previewMode && (
              <Grid item xs={12} md={6}>
                <Box sx={{ position: 'sticky', top: 20 }}>
                  <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                    👁️ Live Preview
                  </Typography>
                  
                  {/* Preview Card */}
                  <Card 
                    sx={{ 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column',
                      borderRadius: 3,
                      background: 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)',
                      boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                      transform: 'scale(0.9)',
                      transformOrigin: 'top'
                    }}
                  >
                    {/* Preview Header */}
                    <Box 
                      sx={{ 
                        background: `linear-gradient(135deg, ${newProject.color} 0%, ${newProject.color}CC 100%)`,
                        color: 'white',
                        p: 2,
                        borderRadius: '12px 12px 0 0'
                      }}
                    >
                      <Box display="flex" alignItems="center">
                        <Box
                          sx={{
                            backgroundColor: 'rgba(255,255,255,0.2)',
                            borderRadius: '50%',
                            p: 1,
                            mr: 2,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          {(() => {
                            const iconData = PROJECT_ICONS.find(i => i.icon === newProject.icon);
                            const IconComponent = iconData ? iconData.component : BusinessIcon;
                            return <IconComponent />;
                          })()}
                        </Box>
                        <Box>
                          <Typography variant="h6" fontWeight={600}>
                            {newProject.name || 'Your Project Space'}
                          </Typography>
                          <Chip 
                            label="Active" 
                            size="small" 
                            sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
                          />
                        </Box>
                      </Box>
                    </Box>

                    <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.5 }}>
                        {newProject.description || 'No description provided'}
                      </Typography>

                      {/* Stats Preview */}
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Box 
                            sx={{ 
                              textAlign: 'center', 
                              p: 1.5, 
                              backgroundColor: '#f8f9fa', 
                              borderRadius: 2,
                              border: '1px solid #e9ecef'
                            }}
                          >
                            <Typography variant="h6" color="primary" fontWeight={600}>0</Typography>
                            <Typography variant="caption" color="text.secondary">Documents</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box 
                            sx={{ 
                              textAlign: 'center', 
                              p: 1.5, 
                              backgroundColor: '#f8f9fa', 
                              borderRadius: 2,
                              border: '1px solid #e9ecef'
                            }}
                          >
                            <Typography variant="h6" color="primary" fontWeight={600}>1</Typography>
                            <Typography variant="caption" color="text.secondary">Members</Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Box>
              </Grid>
            )}
          </Grid>

          {/* Error Messages */}
          {formErrors.submit && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {formErrors.submit}
            </Alert>
          )}
        </DialogContent>
        
        <DialogActions sx={{ p: 3, borderTop: '1px solid #f0f0f0' }}>
          <Button 
            onClick={() => {
              setCreateProjectOpen(false);
              setFormErrors({});
              setPreviewMode(false);
            }}
            sx={{ mr: 2 }}
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleCreateProject}
            disabled={!newProject.name.trim()}
            sx={{
              background: `linear-gradient(135deg, ${newProject.color} 0%, ${newProject.color}CC 100%)`,
              color: '#FFFFFF', // Ensure white text for visibility
              px: 4,
              py: 1.5,
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              '&:hover': {
                background: `linear-gradient(135deg, ${newProject.color}DD 0%, ${newProject.color}AA 100%)`,
                color: '#FFFFFF', // Maintain white text on hover
              },
              '&:disabled': {
                background: 'rgba(0, 0, 0, 0.12)',
                color: 'rgba(0, 0, 0, 0.26)',
              }
            }}
            startIcon={<AddIcon />}
          >
            Create Project Space
          </Button>
        </DialogActions>
      </Dialog>

      {/* PubMed Search Dialog */}
      <Dialog 
        open={showPubMedDialog} 
        onClose={() => setShowPubMedDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            minHeight: '500px'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          textAlign: 'center',
          py: 3
        }}>
          <Typography variant="h4" fontWeight={600}>
            🧬 PubMed Research Integration
          </Typography>
          <Typography variant="subtitle1" sx={{ opacity: 0.9, mt: 1 }}>
            Search and ingest medical research articles from PubMed
          </Typography>
        </DialogTitle>
        
        <DialogContent sx={{ p: 4 }}>
          <Grid container spacing={3}>
            {/* Search Query */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                🔍 Search Query
              </Typography>
              <TextField
                fullWidth
                label="Enter your search terms"
                placeholder="e.g., 'diabetes treatment', 'cancer immunotherapy', 'COVID-19 vaccines'"
                value={pubmedSearch.query}
                onChange={(e) => setPubMedSearch(prev => ({ ...prev, query: e.target.value }))}
                multiline
                rows={2}
                variant="outlined"
                helperText="Use medical terms, disease names, drug names, or research topics"
              />
            </Grid>

            {/* Search Parameters */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                📊 Search Parameters
              </Typography>
              <TextField
                fullWidth
                label="Maximum Results"
                type="number"
                value={pubmedSearch.maxResults}
                onChange={(e) => setPubMedSearch(prev => ({ ...prev, maxResults: parseInt(e.target.value) || 100 }))}
                inputProps={{ min: 1, max: 1000 }}
                helperText="Number of articles to retrieve (1-1000)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Date Range (Optional)"
                placeholder="e.g., '2020:2024', '2023', '2022:2023'"
                value={pubmedSearch.dateRange}
                onChange={(e) => setPubMedSearch(prev => ({ ...prev, dateRange: e.target.value }))}
                helperText="Filter by publication date"
              />
            </Grid>

            {/* Article Types */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                📄 Article Types (Optional)
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Select article types to filter</InputLabel>
                <Select
                  multiple
                  value={pubmedSearch.articleTypes}
                  onChange={(e) => setPubMedSearch(prev => ({ ...prev, articleTypes: e.target.value }))}
                  input={<OutlinedInput label="Select article types to filter" />}
                  renderValue={(selected) => selected.join(', ')}
                >
                  {[
                    'Clinical Trial',
                    'Meta-Analysis',
                    'Randomized Controlled Trial',
                    'Review',
                    'Systematic Review',
                    'Case Reports',
                    'Comparative Study',
                    'Evaluation Study',
                    'Multicenter Study',
                    'Observational Study'
                  ].map((type) => (
                    <MenuItem key={type} value={type}>
                      <Checkbox checked={pubmedSearch.articleTypes.indexOf(type) > -1} />
                      <ListItemText primary={type} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Current Jobs */}
            {pubmedJobs.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', fontWeight: 600 }}>
                  📋 Recent Searches
                </Typography>
                <List>
                  {pubmedJobs.slice(0, 3).map((job) => (
                    <ListItem key={job.job_id}>
                      <ListItemText
                        primary={`Query: ${job.query}`}
                        secondary={`Status: ${job.status} | Articles: ${job.processed_articles}/${job.total_articles}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        
        <DialogActions sx={{ p: 3, gap: 2 }}>
          <Button 
            onClick={() => setShowPubMedDialog(false)}
            variant="outlined"
            size="large"
          >
            Cancel
          </Button>
          <Button 
            onClick={handlePubMedSearch}
            variant="contained"
            size="large"
            disabled={pubmedLoading || !pubmedSearch.query.trim()}
            startIcon={pubmedLoading ? <CircularProgress size={20} /> : <SearchIcon />}
          >
            {pubmedLoading ? 'Searching...' : 'Start Search & Ingestion'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Model Selector Dialog */}
      <ModelSelector
        open={showModelSelector}
        onClose={() => setShowModelSelector(false)}
        selectedModel={selectedModel}
        onModelSelect={handleModelSelect}
        spaceId={selectedProject?.id}
      />

      {/* Login Dialog */}
      <LoginDialog
        open={showLoginDialog}
        onClose={() => setShowLoginDialog(false)}
        onLogin={(authData) => {
          console.log('User logged in:', authData);
          setShowLoginDialog(false);
          // Reload projects after login
          loadProjects();
        }}
      />

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

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: 200,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            border: '1px solid #e0e0e0'
          }
        }}
      >
        <MenuList dense>
          {/* View Details */}
          <MenuItem onClick={() => handleContextMenuAction('view')}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>

          {/* Edit */}
          <MenuItem onClick={() => handleContextMenuAction('edit')}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit Space</ListItemText>
          </MenuItem>

          {/* Duplicate */}
          <MenuItem onClick={() => handleContextMenuAction('duplicate')}>
            <ListItemIcon>
              <DuplicateIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Duplicate</ListItemText>
          </MenuItem>

          <Divider />

          {/* Manage Members */}
          <MenuItem onClick={() => handleContextMenuAction('members')}>
            <ListItemIcon>
              <PersonAddIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Manage Members</ListItemText>
          </MenuItem>

          {/* Settings */}
          <MenuItem onClick={() => handleContextMenuAction('settings')}>
            <ListItemIcon>
              <SettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>

          <Divider />

          {/* Favorite */}
          <MenuItem onClick={() => handleContextMenuAction('favorite')}>
            <ListItemIcon>
              <StarBorderIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Add to Favorites</ListItemText>
          </MenuItem>

          {/* Archive */}
          <MenuItem onClick={() => handleContextMenuAction('archive')}>
            <ListItemIcon>
              <ArchiveIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Archive</ListItemText>
          </MenuItem>

          <Divider />

          {/* Delete */}
          <MenuItem 
            onClick={() => handleContextMenuAction('delete')}
            sx={{ color: 'error.main' }}
          >
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete Space</ListItemText>
          </MenuItem>
        </MenuList>
      </Menu>

      {/* File Browser Dialog */}
      <Dialog 
        open={fileBrowserOpen} 
        onClose={() => setFileBrowserOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            maxHeight: '80vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <FolderIcon />
          Browse Local Documents
          {selectedFiles.size > 0 && (
            <Chip 
              label={`${selectedFiles.size} selected`} 
              size="small" 
              sx={{ 
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                ml: 1
              }} 
            />
          )}
        </DialogTitle>
        
        <DialogContent sx={{ p: 0 }}>
          {loadingFiles ? (
            <Box display="flex" justifyContent="center" alignItems="center" p={4}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                Loading files...
              </Typography>
            </Box>
          ) : (
            <>
              {/* File Browser Header */}
              <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', backgroundColor: '#f5f5f5' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    📁 Available Documents ({localFiles.length} files)
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={handleSelectAllFiles}
                      startIcon={selectedFiles.size === localFiles.length ? <CheckBox /> : <CheckBoxOutlineBlank />}
                    >
                      {selectedFiles.size === localFiles.length ? 'Deselect All' : 'Select All'}
                    </Button>
                  </Box>
                </Box>
                
                {localFiles.length > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Total size: {formatFileSize(localFiles.reduce((sum, file) => sum + file.size, 0))}
                  </Typography>
                )}
              </Box>

              {/* Files List */}
              <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                {localFiles.length === 0 ? (
                  <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={4}>
                    <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      No documents found
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      The Searchable folder appears to be empty or inaccessible.
                    </Typography>
                  </Box>
                ) : (
                  <List>
                    {localFiles.map((file, index) => (
                      <ListItem
                        key={file.path}
                        sx={{
                          borderBottom: index < localFiles.length - 1 ? '1px solid #f0f0f0' : 'none',
                          '&:hover': {
                            backgroundColor: '#f9f9f9'
                          }
                        }}
                      >
                        <ListItemIcon>
                          <IconButton
                            size="small"
                            onClick={() => handleFileSelection(file.path, !selectedFiles.has(file.path))}
                            sx={{ 
                              color: selectedFiles.has(file.path) ? 'primary.main' : 'text.secondary'
                            }}
                          >
                            {selectedFiles.has(file.path) ? (
                              <CheckBox />
                            ) : (
                              <CheckBoxOutlineBlank />
                            )}
                          </IconButton>
                        </ListItemIcon>
                        
                        <ListItemText
                          primary={file.filename}
                          primaryTypographyProps={{ variant: "body1", fontWeight: 500 }}
                          secondary={`Size: ${formatFileSize(file.size)} • Modified: ${new Date(file.modified_date).toLocaleDateString()} • Type: ${file.file_type.toUpperCase()}`}
                          secondaryTypographyProps={{ variant: "body2", color: "text.secondary" }}
                        />
                        
                        <ListItemSecondaryAction>
                          <Chip
                            label={file.file_type.toUpperCase()}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              borderColor: file.file_type === 'pdf' ? 'error.main' : 'primary.main',
                              color: file.file_type === 'pdf' ? 'error.main' : 'primary.main'
                            }}
                          />
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            </>
          )}
        </DialogContent>
        
        <DialogActions sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
          <Button 
            onClick={() => setFileBrowserOpen(false)}
            disabled={loadingIngestion}
          >
            Cancel
          </Button>
          
          <Button
            variant="contained"
            onClick={handleStartLocalIngestion}
            disabled={selectedFiles.size === 0 || loadingIngestion}
            startIcon={loadingIngestion ? <CircularProgress size={16} /> : <UploadIcon />}
          >
            {loadingIngestion 
              ? 'Starting Ingestion...' 
              : `Ingest ${selectedFiles.size} Document${selectedFiles.size !== 1 ? 's' : ''}`
            }
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default EnhancedProjectSpacesOptimized;
