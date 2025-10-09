import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
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
  Fade,
  Zoom,
  Slide,
  Paper,
  Divider,
  Stack,
  Badge,
  LinearProgress,
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
  FilterList as FilterIcon,
  Sort as SortIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  Refresh as RefreshIcon,
  KeyboardArrowDown as ArrowDownIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

// Gothic Noir Color Palette - Professional & Sophisticated
const PROJECT_COLORS = [
  { 
    name: 'Midnight Black', 
    value: '#000000', 
    gradient: 'linear-gradient(135deg, #000000 0%, #434343 100%)',
    accent: '#FFFFFF'
  },
  { 
    name: 'Silver Mist', 
    value: '#D1D0D0', 
    gradient: 'linear-gradient(135deg, #E0E0E0 0%, #A8A8A8 100%)',
    accent: '#000000'
  },
  { 
    name: 'Dusty Rose', 
    value: '#988686', 
    gradient: 'linear-gradient(135deg, #B8A8A8 0%, #786868 100%)',
    accent: '#FFFFFF'
  },
  { 
    name: 'Charcoal Gray', 
    value: '#5C4E4E', 
    gradient: 'linear-gradient(135deg, #7C6E6E 0%, #3C2E2E 100%)',
    accent: '#FFFFFF'
  },
  { 
    name: 'Steel Blue', 
    value: '#4A5568', 
    gradient: 'linear-gradient(135deg, #5A6578 0%, #2A3548 100%)',
    accent: '#FFFFFF'
  },
  { 
    name: 'Slate Gray', 
    value: '#718096', 
    gradient: 'linear-gradient(135deg, #8190A6 0%, #516076 100%)',
    accent: '#FFFFFF'
  },
  { 
    name: 'Warm Gray', 
    value: '#A0AEC0', 
    gradient: 'linear-gradient(135deg, #B0BED0 0%, #808EA0 100%)',
    accent: '#000000'
  },
  { 
    name: 'Graphite', 
    value: '#2D3748', 
    gradient: 'linear-gradient(135deg, #3D4758 0%, #1D2738 100%)',
    accent: '#FFFFFF'
  },
];

// Skeleton Loading Component
const ProjectCardSkeleton = () => (
  <Card
    sx={{
      height: 280,
      borderRadius: 3,
      background: 'rgba(255, 255, 255, 0.02)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(10px)',
      position: 'relative',
      overflow: 'hidden',
    }}
  >
    <Skeleton variant="rectangular" height={120} />
    <CardContent sx={{ p: 3 }}>
      <Skeleton variant="text" height={32} width="80%" sx={{ mb: 1 }} />
      <Skeleton variant="text" height={20} width="60%" sx={{ mb: 2 }} />
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Skeleton variant="rounded" height={24} width={60} />
        <Skeleton variant="rounded" height={24} width={80} />
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Skeleton variant="circular" height={32} width={32} />
        <Skeleton variant="rounded" height={32} width={80} />
      </Box>
    </CardContent>
  </Card>
);

// Empty State Component
const EmptyState = ({ onCreateProject }) => (
  <Fade in timeout={600}>
    <Box
      sx={{
        textAlign: 'center',
        py: 8,
        px: 4,
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: 4,
        border: '2px dashed rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
      }}
    >
      <Box
        sx={{
          width: 120,
          height: 120,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #5C4E4E 0%, #718096 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 24px',
          boxShadow: '0 8px 32px rgba(92, 78, 78, 0.3)',
        }}
      >
        <FolderOpenIcon sx={{ fontSize: 48, color: 'white' }} />
      </Box>
      <Typography
        variant="h4"
        sx={{
          color: 'white',
          fontWeight: 600,
          mb: 2,
          fontFamily: '"IBM Plex Sans", sans-serif',
        }}
      >
        No Projects Yet
      </Typography>
      <Typography
        variant="body1"
        sx={{
          color: 'rgba(255, 255, 255, 0.7)',
          mb: 4,
          maxWidth: 400,
          margin: '0 auto 32px',
          lineHeight: 1.6,
        }}
      >
        Create your first project space to start organizing your data and workflows
      </Typography>
      <Button
        variant="contained"
        size="large"
        startIcon={<AddIcon />}
        onClick={onCreateProject}
        sx={{
          background: 'linear-gradient(135deg, #5C4E4E 0%, #718096 100%)',
          color: 'white',
          px: 4,
          py: 1.5,
          borderRadius: 3,
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '1.1rem',
          boxShadow: '0 8px 32px rgba(92, 78, 78, 0.4)',
          '&:hover': {
            background: 'linear-gradient(135deg, #4A3E3E 0%, #5A6B7A 100%)',
            boxShadow: '0 12px 40px rgba(92, 78, 78, 0.6)',
            transform: 'translateY(-2px)',
          },
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        Create Your First Project
      </Button>
    </Box>
  </Fade>
);

// Enhanced Project Card Component
const ProjectCard = ({ project, onEdit, onDelete, onView, onDuplicate, onArchive, index }) => {
  const [hovered, setHovered] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [favorite, setFavorite] = useState(false);

  const handleMenuOpen = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#10B981';
      case 'pending': return '#F59E0B';
      case 'archived': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <ActiveIcon sx={{ fontSize: 16 }} />;
      case 'pending': return <PendingIcon sx={{ fontSize: 16 }} />;
      case 'archived': return <ArchiveIcon sx={{ fontSize: 16 }} />;
      default: return <ErrorIcon sx={{ fontSize: 16 }} />;
    }
  };

  return (
    <Zoom in timeout={300 + index * 100}>
      <Card
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={() => onView(project)}
        sx={{
          height: 320,
          borderRadius: 4,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          overflow: 'hidden',
          cursor: 'pointer',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: hovered ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)',
          boxShadow: hovered 
            ? '0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1)' 
            : '0 8px 32px rgba(0, 0, 0, 0.2)',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            background: project.gradient || PROJECT_COLORS[0].gradient,
            opacity: hovered ? 1 : 0.8,
            transition: 'opacity 0.3s ease',
          },
        }}
      >
        {/* Header with gradient background */}
        <Box
          sx={{
            height: 120,
            background: project.gradient || PROJECT_COLORS[0].gradient,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {/* Animated background pattern */}
          <Box
            sx={{
              position: 'absolute',
              top: -50,
              right: -50,
              width: 100,
              height: 100,
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.1)',
              animation: hovered ? 'float 3s ease-in-out infinite' : 'none',
              '@keyframes float': {
                '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                '50%': { transform: 'translateY(-10px) rotate(180deg)' }
              }
            }}
          />
          
          <FolderOpenIcon 
            sx={{ 
              fontSize: 48, 
              color: 'white',
              filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3))',
              transition: 'transform 0.3s ease',
              transform: hovered ? 'scale(1.1)' : 'scale(1)',
            }} 
          />
          
          {/* Favorite button */}
          <IconButton
            onClick={(e) => {
              e.stopPropagation();
              setFavorite(!favorite);
            }}
            sx={{
              position: 'absolute',
              top: 12,
              right: 12,
              background: 'rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)',
              color: favorite ? '#F59E0B' : 'rgba(255, 255, 255, 0.8)',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.3)',
                color: '#F59E0B',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {favorite ? <StarIcon sx={{ fontSize: 20 }} /> : <StarBorderIcon sx={{ fontSize: 20 }} />}
          </IconButton>
        </Box>

        <CardContent sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Project name and status */}
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="h6"
              sx={{
                color: 'white',
                fontWeight: 600,
                fontSize: '1.1rem',
                mb: 0.5,
                fontFamily: '"IBM Plex Sans", sans-serif',
                lineHeight: 1.3,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 1,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {project.name}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Chip
                icon={getStatusIcon(project.status || 'active')}
                label={project.status || 'Active'}
                size="small"
                sx={{
                  backgroundColor: alpha(getStatusColor(project.status || 'active'), 0.2),
                  color: getStatusColor(project.status || 'active'),
                  border: `1px solid ${alpha(getStatusColor(project.status || 'active'), 0.3)}`,
                  fontWeight: 500,
                  fontSize: '0.75rem',
                  height: 24,
                }}
              />
              {project.is_public && (
                <Chip
                  label="Public"
                  size="small"
                  sx={{
                    backgroundColor: alpha('#3B82F6', 0.2),
                    color: '#3B82F6',
                    border: `1px solid ${alpha('#3B82F6', 0.3)}`,
                    fontWeight: 500,
                    fontSize: '0.75rem',
                    height: 24,
                  }}
                />
              )}
            </Box>
          </Box>

          {/* Description */}
          <Typography
            variant="body2"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              mb: 2,
              lineHeight: 1.5,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              flexGrow: 1,
            }}
          >
            {project.description || 'No description provided'}
          </Typography>

          {/* Metadata */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <DocumentIcon sx={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.6)' }} />
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                {project.document_count || 0}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <PeopleIcon sx={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.6)' }} />
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                {project.member_count || 0}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <TimeIcon sx={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.6)' }} />
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                {new Date(project.updated_at).toLocaleDateString()}
              </Typography>
            </Box>
          </Box>

          {/* Footer with actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar
                sx={{
                  width: 28,
                  height: 28,
                  background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                }}
              >
                {project.owner_name?.charAt(0) || 'U'}
              </Avatar>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                {project.owner_name || 'Unknown'}
              </Typography>
            </Box>

            <IconButton
              onClick={handleMenuOpen}
              sx={{
                color: 'rgba(255, 255, 255, 0.6)',
                '&:hover': {
                  color: 'white',
                  background: 'rgba(255, 255, 255, 0.1)',
                },
                transition: 'all 0.2s ease',
              }}
            >
              <MoreIcon />
            </IconButton>
          </Box>
        </CardContent>

        {/* Context Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              background: 'rgba(30, 30, 30, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 2,
              minWidth: 160,
            }
          }}
        >
          <MenuItem onClick={() => { onView(project); handleMenuClose(); }}>
            <ViewIcon sx={{ mr: 1, fontSize: 18 }} />
            View Project
          </MenuItem>
          <MenuItem onClick={() => { onEdit(project); handleMenuClose(); }}>
            <EditIcon sx={{ mr: 1, fontSize: 18 }} />
            Edit
          </MenuItem>
          <MenuItem onClick={() => { onDuplicate(project); handleMenuClose(); }}>
            <DuplicateIcon sx={{ mr: 1, fontSize: 18 }} />
            Duplicate
          </MenuItem>
          <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
          <MenuItem onClick={() => { onArchive(project); handleMenuClose(); }}>
            <ArchiveIcon sx={{ mr: 1, fontSize: 18 }} />
            Archive
          </MenuItem>
          <MenuItem 
            onClick={() => { onDelete(project); handleMenuClose(); }}
            sx={{ color: '#EF4444' }}
          >
            <DeleteIcon sx={{ mr: 1, fontSize: 18 }} />
            Delete
          </MenuItem>
        </Menu>
      </Card>
    </Zoom>
  );
};

function UltraModernProjectSpaces() {
  const navigate = useNavigate();
  
  // State
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [sortBy, setSortBy] = useState('updated_at'); // updated_at, name, created_at
  
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
      
      console.log('UltraModernProjectSpaces - API response:', response);
      
      let projectsData = [];
      if (Array.isArray(response)) {
        projectsData = response;
      } else if (response?.spaces && Array.isArray(response.spaces)) {
        projectsData = response.spaces;
      } else if (response?.data && Array.isArray(response.data)) {
        projectsData = response.data;
      } else if (response?.project_spaces && Array.isArray(response.project_spaces)) {
        projectsData = response.project_spaces;
      }
      
      console.log('UltraModernProjectSpaces - Extracted projects:', projectsData);
      setProjects(projectsData);
    } catch (error) {
      console.error('Error loading projects:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load projects',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    try {
      const response = await apiService.createProjectSpace({
        name: newProject.name,
        description: newProject.description,
        color: newProject.color,
        gradient: newProject.gradient,
      });

      setSnackbar({
        open: true,
        message: 'Project created successfully!',
        severity: 'success'
      });

      setCreateDialogOpen(false);
      setNewProject({
        name: '',
        description: '',
        color: PROJECT_COLORS[0].value,
        gradient: PROJECT_COLORS[0].gradient,
      });

      loadProjects();
    } catch (error) {
      console.error('Error creating project:', error);
      setSnackbar({
        open: true,
        message: 'Failed to create project',
        severity: 'error'
      });
    }
  };

  const handleDeleteProject = async (project) => {
    try {
      await apiService.deleteProjectSpace(project.id);
      setSnackbar({
        open: true,
        message: 'Project deleted successfully!',
        severity: 'success'
      });
      loadProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete project',
        severity: 'error'
      });
    }
  };

  const handleViewProject = (project) => {
    navigate(`/spaces/${project.id}`);
  };

  const handleEditProject = (project) => {
    // TODO: Implement edit functionality
    console.log('Edit project:', project);
  };

  const handleDuplicateProject = (project) => {
    // TODO: Implement duplicate functionality
    console.log('Duplicate project:', project);
  };

  const handleArchiveProject = (project) => {
    // TODO: Implement archive functionality
    console.log('Archive project:', project);
  };

  // Filter and sort projects
  const filteredProjects = projects
    .filter(project => {
      const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           project.description?.toLowerCase().includes(searchTerm.toLowerCase());
      
      if (activeTab === 0) return matchesSearch; // All
      if (activeTab === 1) return matchesSearch && (project.status === 'active' || !project.status); // Active
      if (activeTab === 2) return matchesSearch && project.status === 'archived'; // Archived
      
      return matchesSearch;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created_at':
          return new Date(b.created_at) - new Date(a.created_at);
        case 'updated_at':
        default:
          return new Date(b.updated_at) - new Date(a.updated_at);
      }
    });

  const tabCounts = {
    all: projects.length,
    active: projects.filter(p => p.status === 'active' || !p.status).length,
    archived: projects.filter(p => p.status === 'archived').length,
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `
          radial-gradient(circle at 20% 50%, rgba(92, 78, 78, 0.15) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(113, 128, 150, 0.12) 0%, transparent 50%),
          radial-gradient(circle at 40% 80%, rgba(160, 174, 192, 0.08) 0%, transparent 50%),
          linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 25%, #1F1F1F 50%, #2A2A2A 75%, #1A1A1A 100%)
        `,
        py: 4,
        fontFamily: '"IBM Plex Sans", sans-serif',
      }}
    >
      <Container maxWidth="xl">
        {/* Header Section */}
        <Box sx={{ mb: 6 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
            <Box>
              <Typography
                variant="h3"
                sx={{
                  color: 'white',
                  fontWeight: 700,
                  mb: 1,
                  fontFamily: '"IBM Plex Sans", sans-serif',
                  background: 'linear-gradient(45deg, #5C4E4E, #718096, #4A5568)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Project Spaces
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontWeight: 400,
                  fontFamily: '"IBM Plex Sans", sans-serif',
                }}
              >
                Organize and manage your data workflows
              </Typography>
            </Box>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{
                background: 'linear-gradient(135deg, #5C4E4E 0%, #718096 100%)',
                color: 'white',
                px: 4,
                py: 1.5,
                borderRadius: 3,
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1rem',
                boxShadow: '0 8px 32px rgba(92, 78, 78, 0.4)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4A3E3E 0%, #5A6B7A 100%)',
                  boxShadow: '0 12px 40px rgba(92, 78, 78, 0.6)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            >
              Create Project
            </Button>
          </Box>

          {/* Search and Controls */}
          <Paper
            sx={{
              p: 3,
              background: 'rgba(255, 255, 255, 0.03)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 3,
            }}
          >
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              {/* Search Bar */}
              <TextField
                placeholder="Search projects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: 'rgba(255, 255, 255, 0.6)' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  flexGrow: 1,
                  minWidth: 300,
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 2,
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#5C4E4E',
                      boxShadow: '0 0 0 2px rgba(92, 78, 78, 0.2)',
                    },
                  },
                  '& .MuiInputBase-input': {
                    color: 'white',
                    '&::placeholder': {
                      color: 'rgba(255, 255, 255, 0.5)',
                      opacity: 1,
                    },
                  },
                }}
              />

              {/* View Mode Toggle */}
              <Box sx={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 2, p: 0.5 }}>
                <IconButton
                  onClick={() => setViewMode('grid')}
                  sx={{
                    color: viewMode === 'grid' ? '#5C4E4E' : 'rgba(255, 255, 255, 0.6)',
                    background: viewMode === 'grid' ? 'rgba(92, 78, 78, 0.2)' : 'transparent',
                  }}
                >
                  <GridViewIcon />
                </IconButton>
                <IconButton
                  onClick={() => setViewMode('list')}
                  sx={{
                    color: viewMode === 'list' ? '#5C4E4E' : 'rgba(255, 255, 255, 0.6)',
                    background: viewMode === 'list' ? 'rgba(92, 78, 78, 0.2)' : 'transparent',
                  }}
                >
                  <ListViewIcon />
                </IconButton>
              </Box>

              {/* Sort Dropdown */}
              <Button
                endIcon={<ArrowDownIcon />}
                onClick={() => {
                  const options = ['updated_at', 'name', 'created_at'];
                  const currentIndex = options.indexOf(sortBy);
                  setSortBy(options[(currentIndex + 1) % options.length]);
                }}
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  textTransform: 'none',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 2,
                  px: 2,
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                  },
                }}
              >
                Sort: {sortBy === 'updated_at' ? 'Last Updated' : sortBy === 'name' ? 'Name' : 'Created'}
              </Button>

              {/* Refresh Button */}
              <IconButton
                onClick={loadProjects}
                sx={{
                  color: 'rgba(255, 255, 255, 0.6)',
                  '&:hover': {
                    color: '#5C4E4E',
                    background: 'rgba(92, 78, 78, 0.1)',
                  },
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Box>

            {/* Tabs */}
            <Box sx={{ mt: 3 }}>
              <Tabs
                value={activeTab}
                onChange={(e, newValue) => setActiveTab(newValue)}
                sx={{
                  '& .MuiTab-root': {
                    color: 'rgba(255, 255, 255, 0.6)',
                    textTransform: 'none',
                    fontWeight: 500,
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      color: '#5C4E4E',
                    },
                  },
                  '& .MuiTabs-indicator': {
                    background: 'linear-gradient(135deg, #5C4E4E 0%, #718096 100%)',
                    height: 3,
                    borderRadius: '2px 2px 0 0',
                  },
                }}
              >
                <Tab 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      All Projects
                      <Badge 
                        badgeContent={tabCounts.all} 
                        sx={{ 
                          '& .MuiBadge-badge': { 
                            background: '#5C4E4E',
                            color: 'white',
                            fontSize: '0.75rem',
                            minWidth: 20,
                            height: 20,
                          }
                        }} 
                      />
                    </Box>
                  } 
                />
                <Tab 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      Active
                      <Badge 
                        badgeContent={tabCounts.active} 
                        sx={{ 
                          '& .MuiBadge-badge': { 
                            background: '#10B981',
                            color: 'white',
                            fontSize: '0.75rem',
                            minWidth: 20,
                            height: 20,
                          }
                        }} 
                      />
                    </Box>
                  } 
                />
                <Tab 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      Archived
                      <Badge 
                        badgeContent={tabCounts.archived} 
                        sx={{ 
                          '& .MuiBadge-badge': { 
                            background: '#6B7280',
                            color: 'white',
                            fontSize: '0.75rem',
                            minWidth: 20,
                            height: 20,
                          }
                        }} 
                      />
                    </Box>
                  } 
                />
              </Tabs>
            </Box>
          </Paper>
        </Box>

        {/* Projects Grid */}
        {loading ? (
          <Grid container spacing={3}>
            {[...Array(6)].map((_, index) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
                <ProjectCardSkeleton />
              </Grid>
            ))}
          </Grid>
        ) : filteredProjects.length === 0 ? (
          <EmptyState onCreateProject={() => setCreateDialogOpen(true)} />
        ) : (
          <Grid container spacing={3}>
            {filteredProjects.map((project, index) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={project.id}>
                <ProjectCard
                  project={project}
                  onEdit={handleEditProject}
                  onDelete={handleDeleteProject}
                  onView={handleViewProject}
                  onDuplicate={handleDuplicateProject}
                  onArchive={handleArchiveProject}
                  index={index}
                />
              </Grid>
            ))}
          </Grid>
        )}

        {/* Create Project Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              background: 'rgba(30, 30, 30, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 4,
            }
          }}
        >
          <DialogTitle
            sx={{
              color: 'white',
              fontFamily: '"IBM Plex Sans", sans-serif',
              fontWeight: 600,
              fontSize: '1.5rem',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            Create New Project
          </DialogTitle>
          <DialogContent sx={{ p: 3 }}>
            <Stack spacing={3}>
              <TextField
                label="Project Name"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                fullWidth
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#6366F1',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&.Mui-focused': {
                      color: '#6366F1',
                    },
                  },
                  '& .MuiInputBase-input': {
                    color: 'white',
                  },
                }}
              />
              
              <TextField
                label="Description"
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                fullWidth
                multiline
                rows={3}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#6366F1',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&.Mui-focused': {
                      color: '#6366F1',
                    },
                  },
                  '& .MuiInputBase-input': {
                    color: 'white',
                  },
                }}
              />

              <Box>
                <Typography variant="subtitle2" sx={{ color: 'white', mb: 2 }}>
                  Choose Color Theme
                </Typography>
                <Grid container spacing={1}>
                  {PROJECT_COLORS.map((color) => (
                    <Grid item key={color.value}>
                      <Box
                        onClick={() => setNewProject({ ...newProject, color: color.value, gradient: color.gradient })}
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: 2,
                          background: color.gradient,
                          cursor: 'pointer',
                          border: newProject.color === color.value ? '3px solid white' : '2px solid transparent',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            transform: 'scale(1.1)',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                          },
                        }}
                      />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 3, gap: 2 }}>
            <Button
              onClick={() => setCreateDialogOpen(false)}
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                textTransform: 'none',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={!newProject.name.trim()}
              variant="contained"
              sx={{
                background: 'linear-gradient(135deg, #5C4E4E 0%, #718096 100%)',
                color: 'white',
                textTransform: 'none',
                px: 3,
                '&:hover': {
                  background: 'linear-gradient(135deg, #4A3E3E 0%, #5A6B7A 100%)',
                },
                '&:disabled': {
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'rgba(255, 255, 255, 0.3)',
                },
              }}
            >
              Create Project
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{
              background: snackbar.severity === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${snackbar.severity === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: snackbar.severity === 'success' ? '#10B981' : '#EF4444',
              backdropFilter: 'blur(10px)',
            }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
}

export default UltraModernProjectSpaces;
