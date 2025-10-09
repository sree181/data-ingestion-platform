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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Menu,
  MenuItem,
  InputAdornment,
  Skeleton,
  Snackbar,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  alpha,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  MoreVert as MoreIcon,
  FolderOpen as FolderOpenIcon,
  Description as DocumentIcon,
  People as PeopleIcon,
  AccessTime as TimeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Archive as ArchiveIcon,
  ContentCopy as DuplicateIcon,
  Settings as SettingsIcon,
  Business as BusinessIcon,
  CheckCircle as ActiveIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
  Visibility as ViewIcon,
  Share as ShareIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  TrendingUp as TrendingIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

// Gothic Noir color palette - Professional & Sophisticated
const PROJECT_COLORS = [
  { name: 'Midnight Black', value: '#000000', gradient: 'linear-gradient(135deg, #000000 0%, #434343 100%)' },
  { name: 'Silver Mist', value: '#D1D0D0', gradient: 'linear-gradient(135deg, #E0E0E0 0%, #A8A8A8 100%)' },
  { name: 'Dusty Rose', value: '#988686', gradient: 'linear-gradient(135deg, #B8A8A8 0%, #786868 100%)' },
  { name: 'Charcoal Gray', value: '#5C4E4E', gradient: 'linear-gradient(135deg, #7C6E6E 0%, #3C2E2E 100%)' },
  { name: 'Steel Blue', value: '#4A5568', gradient: 'linear-gradient(135deg, #5A6578 0%, #2A3548 100%)' },
  { name: 'Slate Gray', value: '#718096', gradient: 'linear-gradient(135deg, #8190A6 0%, #516076 100%)' },
  { name: 'Warm Gray', value: '#A0AEC0', gradient: 'linear-gradient(135deg, #B0BED0 0%, #808EA0 100%)' },
  { name: 'Graphite', value: '#2D3748', gradient: 'linear-gradient(135deg, #3D4758 0%, #1D2738 100%)' },
];

function ModernProjectSpaces() {
  const navigate = useNavigate();
  
  // State
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState(0); // 0: All, 1: Active, 2: Archived
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  
  // New project form
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    color: PROJECT_COLORS[0].value,
    gradient: PROJECT_COLORS[0].gradient,
  });

  // Load projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await apiService.getProjectSpaces();
      
      console.log('ModernProjectSpaces - API response:', response);
      console.log('ModernProjectSpaces - response type:', typeof response);
      console.log('ModernProjectSpaces - is array?', Array.isArray(response));
      
      // Handle different response formats
      let projectsArray = [];
      if (Array.isArray(response)) {
        projectsArray = response;
      } else if (response && Array.isArray(response.spaces)) {
        projectsArray = response.spaces;
      } else if (response && Array.isArray(response.data)) {
        projectsArray = response.data;
      } else if (response && response.success && Array.isArray(response.project_spaces)) {
        projectsArray = response.project_spaces;
      } else if (response && typeof response === 'object') {
        // Try to find any array property
        const keys = Object.keys(response);
        for (const key of keys) {
          if (Array.isArray(response[key])) {
            console.log(`Found array at key: ${key}`);
            projectsArray = response[key];
            break;
          }
        }
      }
      
      console.log('ModernProjectSpaces - projectsArray:', projectsArray);
      console.log('ModernProjectSpaces - projectsArray length:', projectsArray.length);
      
      if (!Array.isArray(projectsArray)) {
        console.error('Could not find projects array in response:', response);
        projectsArray = [];
      }
      
      const transformedProjects = projectsArray.map(p => ({
        id: p.id,
        name: p.name,
        description: p.description || '',
        color: p.color || '#1976d2',
        documentsCount: p.documents_count || 0,
        membersCount: p.members_count || 1,
        lastActivity: p.last_activity || p.created_at,
        status: p.status || 'active',
        owner: p.owner || 'You',
      }));
      
      console.log('ModernProjectSpaces - transformedProjects:', transformedProjects);
      setProjects(transformedProjects);
    } catch (error) {
      console.error('Error loading projects:', error);
      console.error('Error details:', error.message, error.response);
      showSnackbar('Failed to load projects', 'error');
      setProjects([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCreateProject = async () => {
    if (!newProject.name.trim()) return;
    
    try {
      const created = await apiService.createProjectSpace({
        name: newProject.name,
        description: newProject.description,
        color: newProject.color,
      });
      
      setProjects(prev => [...prev, {
        id: created.id,
        name: created.name,
        description: created.description || '',
        color: created.color || '#1976d2',
        documentsCount: 0,
        membersCount: 1,
        lastActivity: new Date().toISOString(),
        status: 'active',
        owner: 'You',
      }]);
      
      setCreateDialogOpen(false);
      setNewProject({ name: '', description: '', color: '#1976d2' });
      showSnackbar('Project created successfully!');
    } catch (error) {
      console.error('Error creating project:', error);
      showSnackbar('Failed to create project', 'error');
    }
  };

  const handleMenuOpen = (event, project) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedProject(project);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedProject(null);
  };

  const handleDeleteProject = async () => {
    if (!selectedProject) return;
    
    if (window.confirm(`Delete "${selectedProject.name}"?`)) {
      try {
        await apiService.deleteProjectSpace(selectedProject.id);
        setProjects(prev => prev.filter(p => p.id !== selectedProject.id));
        showSnackbar('Project deleted successfully');
      } catch (error) {
        console.error('Error deleting project:', error);
        showSnackbar('Failed to delete project', 'error');
      }
    }
    handleMenuClose();
  };

  const handleViewProject = (projectId) => {
    navigate(`/spaces/${projectId}`);
  };

  // Filter projects
  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTab = activeTab === 0 ? true : 
                      activeTab === 1 ? project.status === 'active' :
                      project.status === 'archived';
    return matchesSearch && matchesTab;
  });

  // Get status config
  const getStatusConfig = (status) => {
    const configs = {
      active: { color: 'success', icon: <ActiveIcon fontSize="small" />, label: 'Active' },
      pending: { color: 'warning', icon: <PendingIcon fontSize="small" />, label: 'Pending' },
      archived: { color: 'default', icon: <ArchiveIcon fontSize="small" />, label: 'Archived' },
    };
    return configs[status] || configs.active;
  };

  // Format time ago
  const formatTimeAgo = (date) => {
    const now = new Date();
    const past = new Date(date);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 30) return `${diffDays}d ago`;
    return past.toLocaleDateString();
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', pb: 4 }}>
      {/* Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #2D3748 0%, #1A202C 100%)',
          color: 'white',
          py: 6,
          mb: 4,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
            Project Spaces
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, fontWeight: 400 }}>
            Organize and manage your document projects
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg">
        {/* Search and Actions Bar */}
        <Box sx={{ mb: 4 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search projects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
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
            </Grid>
            <Grid item xs={12} md={6} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
                sx={{
                  borderRadius: 3,
                  px: 4,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #2D3748 0%, #1A202C 100%)',
                  boxShadow: '0 4px 12px rgba(45, 55, 72, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #3D4758 0%, #2A303C 100%)',
                    boxShadow: '0 6px 16px rgba(45, 55, 72, 0.5)',
                  },
                }}
              >
                Create Project
              </Button>
            </Grid>
          </Grid>
        </Box>

        {/* Filter Tabs */}
        <Box sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1rem',
              },
            }}
          >
            <Tab label={`All (${projects.length})`} />
            <Tab label={`Active (${projects.filter(p => p.status === 'active').length})`} />
            <Tab label={`Archived (${projects.filter(p => p.status === 'archived').length})`} />
          </Tabs>
        </Box>

        {/* Loading State */}
        {loading && (
          <Grid container spacing={3}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Card sx={{ borderRadius: 3 }}>
                  <CardContent>
                    <Skeleton variant="text" width="60%" height={32} />
                    <Skeleton variant="text" width="100%" />
                    <Skeleton variant="text" width="80%" />
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      <Skeleton variant="circular" width={24} height={24} />
                      <Skeleton variant="text" width="40%" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Empty State */}
        {!loading && filteredProjects.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <FolderOpenIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              {searchTerm ? 'No projects found' : 'No projects yet'}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Create your first project to get started'}
            </Typography>
            {!searchTerm && (
              <Button
                variant="contained"
                size="large"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
                sx={{
                  borderRadius: 3,
                  px: 4,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                Create Project
              </Button>
            )}
          </Box>
        )}

        {/* Project Cards */}
        {!loading && filteredProjects.length > 0 && (
          <Grid container spacing={3}>
            {filteredProjects.map((project) => {
              const statusConfig = getStatusConfig(project.status);
              
              return (
                <Grid item xs={12} sm={6} md={4} key={project.id}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 3,
                      border: '1px solid',
                      borderColor: 'divider',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      cursor: 'pointer',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 6,
                        borderColor: project.color,
                        '& .card-actions': {
                          opacity: 1,
                        },
                      },
                    }}
                    onClick={() => handleViewProject(project.id)}
                  >
                    {/* Card Header with Color Bar */}
                    <Box
                      sx={{
                        height: 6,
                        bgcolor: project.color,
                        borderRadius: '12px 12px 0 0',
                      }}
                    />
                    
                    <CardContent sx={{ flexGrow: 1, p: 3 }}>
                      {/* Title and Menu */}
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              mb: 0.5,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {project.name}
                          </Typography>
                          <Chip
                            icon={statusConfig.icon}
                            label={statusConfig.label}
                            color={statusConfig.color}
                            size="small"
                            sx={{ height: 24 }}
                          />
                        </Box>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, project)}
                          sx={{
                            ml: 1,
                            opacity: 0.6,
                            '&:hover': { opacity: 1 },
                          }}
                        >
                          <MoreIcon />
                        </IconButton>
                      </Box>

                      {/* Description */}
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mb: 3,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          minHeight: 40,
                        }}
                      >
                        {project.description || 'No description'}
                      </Typography>

                      {/* Metadata */}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                        <Tooltip title="Documents">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <DocumentIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {project.documentsCount}
                            </Typography>
                          </Box>
                        </Tooltip>
                        <Tooltip title="Members">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <PeopleIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {project.membersCount}
                            </Typography>
                          </Box>
                        </Tooltip>
                        <Tooltip title="Last activity">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <TimeIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {formatTimeAgo(project.lastActivity)}
                            </Typography>
                          </Box>
                        </Tooltip>
                      </Box>
                    </CardContent>

                    {/* Card Actions */}
                    <CardActions
                      className="card-actions"
                      sx={{
                        p: 2,
                        pt: 0,
                        opacity: { xs: 1, md: 0 },
                        transition: 'opacity 0.2s',
                      }}
                    >
                      <Button
                        fullWidth
                        variant="contained"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewProject(project.id);
                        }}
                        sx={{
                          borderRadius: 2,
                          textTransform: 'none',
                          fontWeight: 600,
                          bgcolor: project.color,
                          '&:hover': {
                            bgcolor: alpha(project.color, 0.8),
                          },
                        }}
                      >
                        View Project
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}
      </Container>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { borderRadius: 2, minWidth: 180 },
        }}
      >
        <MenuItem onClick={() => { handleViewProject(selectedProject?.id); handleMenuClose(); }}>
          <FolderOpenIcon fontSize="small" sx={{ mr: 1.5 }} />
          Open
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <EditIcon fontSize="small" sx={{ mr: 1.5 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <SettingsIcon fontSize="small" sx={{ mr: 1.5 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <DuplicateIcon fontSize="small" sx={{ mr: 1.5 }} />
          Duplicate
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ArchiveIcon fontSize="small" sx={{ mr: 1.5 }} />
          Archive
        </MenuItem>
        <MenuItem onClick={handleDeleteProject} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1.5 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Project Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Create New Project
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            autoFocus
            fullWidth
            label="Project Name"
            value={newProject.name}
            onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
            sx={{ mb: 3 }}
          />
          <TextField
            fullWidth
            label="Description (optional)"
            multiline
            rows={3}
            value={newProject.description}
            onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
            sx={{ mb: 3 }}
          />
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, fontWeight: 600 }}>
              Choose Project Color
            </Typography>
            <Grid container spacing={1.5}>
              {PROJECT_COLORS.map((colorOption) => (
                <Grid item xs={3} key={colorOption.value}>
                  <Tooltip title={colorOption.name} arrow>
                    <Box
                      onClick={() => setNewProject({ 
                        ...newProject, 
                        color: colorOption.value,
                        gradient: colorOption.gradient 
                      })}
                      sx={{
                        width: '100%',
                        height: 56,
                        borderRadius: 2,
                        background: colorOption.gradient,
                        cursor: 'pointer',
                        border: newProject.color === colorOption.value ? '3px solid' : '2px solid',
                        borderColor: newProject.color === colorOption.value ? '#2D3436' : 'rgba(0,0,0,0.1)',
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: 4,
                        },
                        '&::after': newProject.color === colorOption.value ? {
                          content: '"✓"',
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          color: 'white',
                          fontSize: '1.5rem',
                          fontWeight: 'bold',
                          textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        } : {},
                      }}
                    />
                  </Tooltip>
                </Grid>
              ))}
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button onClick={() => setCreateDialogOpen(false)} sx={{ textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateProject}
            disabled={!newProject.name.trim()}
            sx={{
              textTransform: 'none',
              fontWeight: 600,
              px: 3,
            }}
          >
            Create Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
          sx={{ borderRadius: 2 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ModernProjectSpaces;
