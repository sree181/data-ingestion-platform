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
  TextField,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Avatar,
  AvatarGroup,
  Tooltip,
  Stack,
  Divider,
  Badge
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Description as DocumentsIcon,
  Security as SecurityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Clear as ClearIcon,
  Visibility as ViewIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/api';

const OptimizedProjectSpaces = () => {
  const { isAuthenticated, user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  
  // Form state
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    color: '#1976d2'
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await apiService.getProjectSpaces();
      console.log('Projects loaded:', response);
      
      // Transform backend data
      const spacesArray = Array.isArray(response) ? response : (response.spaces || []);
      const transformedProjects = spacesArray.map(space => ({
        id: space.id,
        name: space.name,
        description: space.description || 'No description provided',
        document_count: space.document_count || 0,
        member_count: space.member_count || 1,
        created_at: space.created_at,
        color: space.color || '#1976d2',
        icon: space.icon || 'business'
      }));
      
      setProjects(transformedProjects);
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    try {
      const response = await apiService.createProjectSpace({
        name: newProject.name,
        description: newProject.description,
        color: newProject.color
      });
      
      console.log('Project created:', response);
      setCreateDialogOpen(false);
      setNewProject({ name: '', description: '', color: '#1976d2' });
      loadProjects();
    } catch (error) {
      console.error('Error creating project:', error);
      alert('Failed to create project. Please try again.');
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return;
    }
    
    try {
      await apiService.deleteProjectSpace(projectId, 'owner');
      loadProjects();
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('Failed to delete project. Please try again.');
    }
  };

  const handleContextMenu = (event, project) => {
    event.preventDefault();
    setContextMenu({
      mouseX: event.clientX + 2,
      mouseY: event.clientY - 6,
    });
    setSelectedProject(project);
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
    setSelectedProject(null);
  };

  // Filter and sort projects
  const filteredProjects = projects
    .filter(project => 
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.description.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
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
        case 'documents':
          aValue = a.document_count;
          bValue = b.document_count;
          break;
        case 'members':
          aValue = a.member_count;
          bValue = b.member_count;
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const getProjectIcon = (iconName) => {
    const iconMap = {
      business: <BusinessIcon />,
      security: <SecurityIcon />,
      documents: <DocumentsIcon />,
      people: <PeopleIcon />
    };
    return iconMap[iconName] || <BusinessIcon />;
  };

  const getStatusColor = (project) => {
    if (project.document_count === 0) return 'default';
    if (project.document_count < 5) return 'warning';
    return 'success';
  };

  const getStatusText = (project) => {
    if (project.document_count === 0) return 'Empty';
    if (project.document_count < 5) return 'Low Activity';
    return 'Active';
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography>Loading projects...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Compact Header */}
      <Box sx={{ mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h4" fontWeight={600} gutterBottom>
              Project Spaces
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {projects.length} spaces • {projects.reduce((sum, p) => sum + p.document_count, 0)} documents
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{ borderRadius: 2 }}
          >
            New Space
          </Button>
        </Box>

        {/* Compact Search and Controls */}
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="Search spaces..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            InputProps={{
              startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />,
              endAdornment: searchTerm && (
                <IconButton size="small" onClick={() => setSearchTerm('')}>
                  <ClearIcon fontSize="small" />
                </IconButton>
              )
            }}
            sx={{ flexGrow: 1, maxWidth: 400 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort by</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort by"
            >
              <MenuItem value="name">Name</MenuItem>
              <MenuItem value="date">Date</MenuItem>
              <MenuItem value="documents">Documents</MenuItem>
              <MenuItem value="members">Members</MenuItem>
            </Select>
          </FormControl>

          <IconButton
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            size="small"
          >
            <SortIcon sx={{ transform: sortOrder === 'desc' ? 'rotate(180deg)' : 'none' }} />
          </IconButton>
        </Box>
      </Box>

      {/* Compact Project Grid */}
      <Grid container spacing={2}>
        {filteredProjects.map((project) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={project.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 3
                }
              }}
              onContextMenu={(e) => handleContextMenu(e, project)}
            >
              <CardContent sx={{ flexGrow: 1, p: 2 }}>
                {/* Header */}
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Avatar
                      sx={{
                        bgcolor: project.color,
                        width: 32,
                        height: 32,
                        fontSize: 16
                      }}
                    >
                      {getProjectIcon(project.icon)}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600} noWrap>
                        {project.name}
                      </Typography>
                      <Chip
                        label={getStatusText(project)}
                        size="small"
                        color={getStatusColor(project)}
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                  <IconButton size="small" onClick={(e) => handleContextMenu(e, project)}>
                    <MoreVertIcon fontSize="small" />
                  </IconButton>
                </Box>

                {/* Description */}
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mb: 2,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}
                >
                  {project.description}
                </Typography>

                {/* Stats */}
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box display="flex" gap={2}>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <DocumentsIcon fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        {project.document_count}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <PeopleIcon fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        {project.member_count}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Empty State */}
      {filteredProjects.length === 0 && (
        <Box textAlign="center" py={8}>
          <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {searchTerm ? 'No projects found' : 'No project spaces yet'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm 
              ? 'Try adjusting your search terms' 
              : 'Create your first project space to get started'
            }
          </Typography>
          {!searchTerm && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Create Project Space
            </Button>
          )}
        </Box>
      )}

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
      >
        <MenuItem onClick={() => { handleCloseContextMenu(); /* Navigate to project */ }}>
          <ViewIcon sx={{ mr: 1 }} fontSize="small" />
          View Details
        </MenuItem>
        <MenuItem onClick={() => { handleCloseContextMenu(); /* Edit project */ }}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit
        </MenuItem>
        <MenuItem onClick={() => { handleCloseContextMenu(); /* Settings */ }}>
          <SettingsIcon sx={{ mr: 1 }} fontSize="small" />
          Settings
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => {
            if (selectedProject) {
              handleDeleteProject(selectedProject.id);
            }
            handleCloseContextMenu();
          }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Project Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project Space</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Project Name"
              value={newProject.name}
              onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth>
              <InputLabel>Color Theme</InputLabel>
              <Select
                value={newProject.color}
                onChange={(e) => setNewProject({ ...newProject, color: e.target.value })}
                label="Color Theme"
              >
                <MenuItem value="#1976d2">Blue</MenuItem>
                <MenuItem value="#388e3c">Green</MenuItem>
                <MenuItem value="#f57c00">Orange</MenuItem>
                <MenuItem value="#d32f2f">Red</MenuItem>
                <MenuItem value="#7b1fa2">Purple</MenuItem>
                <MenuItem value="#00796b">Teal</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained"
            disabled={!newProject.name.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OptimizedProjectSpaces;
