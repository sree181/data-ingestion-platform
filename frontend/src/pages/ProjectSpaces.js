import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
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
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Fab,
  Tooltip,
  Paper,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Folder as FolderIcon,
  Gavel as GavelIcon,
  Science as ScienceIcon,
  Business as BusinessIcon,
  School as SchoolIcon,
  Settings as SettingsIcon,
  People as PeopleIcon,
  Description as DocumentsIcon,
  Analytics as AnalyticsIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

// Icon mapping for display
const iconMap = {
  folder: FolderIcon,
  gavel: GavelIcon,
  science: ScienceIcon,
  business: BusinessIcon,
  school: SchoolIcon
};

const ProjectSpaces = () => {
  const { isDarkMode } = useTheme();
  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  
  // Form states
  const [newSpace, setNewSpace] = useState({
    name: '',
    description: '',
    color: '#1976d2',
    icon: 'folder'
  });

  // Load spaces on component mount
  useEffect(() => {
    loadSpaces();
  }, []);

  const loadSpaces = async () => {
    try {
      setLoading(true);
      const spacesData = await apiService.getProjectSpaces();
      setSpaces(spacesData);
    } catch (error) {
      console.error('Failed to load project spaces:', error);
      toast.error('Failed to load project spaces');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSpace = async () => {
    try {
      setLoading(true);
      
      const createdSpace = await apiService.createProjectSpace(newSpace);
      setSpaces([createdSpace, ...spaces]);
      setCreateDialogOpen(false);
      setNewSpace({ name: '', description: '', color: '#1976d2', icon: 'folder' });
      toast.success('Project space created successfully!');
      
    } catch (error) {
      console.error('Failed to create project space:', error);
      toast.error('Failed to create project space');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSpace = async (spaceId) => {
    if (window.confirm('Are you sure you want to delete this project space?')) {
      try {
        await apiService.deleteProjectSpace(spaceId);
        setSpaces(spaces.filter(space => space.id !== spaceId));
        toast.success('Project space deleted successfully!');
      } catch (error) {
        console.error('Failed to delete project space:', error);
        toast.error('Failed to delete project space');
      }
    }
  };

  const getSpaceIcon = (iconName) => {
    const IconComponent = iconMap[iconName] || FolderIcon;
    return <IconComponent />;
  };

  // Upload functions
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const handleUploadToSpace = async () => {
    if (!selectedSpace || selectedFiles.length === 0) return;

    try {
      setUploading(true);
      setUploadProgress(0);

      // Upload files with progress tracking
      const result = await apiService.uploadDocuments(
        selectedFiles,
        (progress) => setUploadProgress(progress),
        selectedSpace.id
      );

      // Update space document count
      const updatedSpaces = spaces.map(space => 
        space.id === selectedSpace.id 
          ? { ...space, document_count: space.document_count + selectedFiles.length }
          : space
      );
      setSpaces(updatedSpaces);

      setUploadDialogOpen(false);
      setSelectedFiles([]);
      setUploadProgress(0);
      toast.success(`Successfully uploaded ${selectedFiles.length} document(s) to ${selectedSpace.name}!`);
      
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload documents');
    } finally {
      setUploading(false);
    }
  };

  const openUploadDialog = (space) => {
    setSelectedSpace(space);
    setUploadDialogOpen(true);
    setSelectedFiles([]);
  };

  const SpaceCard = ({ space }) => (
    <Card 
      sx={{ 
        height: '100%', 
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: theme => theme.shadows[8]
        },
        border: `2px solid ${space.color}`,
        borderRadius: 3
      }}
      onClick={() => setSelectedSpace(space)}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar 
            sx={{ 
              bgcolor: space.color, 
              mr: 2,
              width: 48,
              height: 48
            }}
          >
            {getSpaceIcon(space.icon)}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, fontFamily: 'Inter' }}>
              {space.name}
            </Typography>
            <Chip 
              label={space.user_role} 
              size="small" 
              color={space.user_role === 'owner' ? 'primary' : 'default'}
              sx={{ mt: 0.5, fontFamily: 'Inter' }}
            />
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Upload Documents">
              <IconButton 
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  openUploadDialog(space);
                }}
                sx={{ color: space.color }}
              >
                <UploadIcon />
              </IconButton>
            </Tooltip>
            {space.user_role === 'owner' && (
              <Tooltip title="Space Settings">
                <IconButton 
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedSpace(space);
                    setEditDialogOpen(true);
                  }}
                >
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
        
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ mb: 2, fontFamily: 'Inter' }}
        >
          {space.description}
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <DocumentsIcon fontSize="small" color="action" />
              <Typography variant="body2" sx={{ fontFamily: 'Inter' }}>
                {space.document_count}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <PeopleIcon fontSize="small" color="action" />
              <Typography variant="body2" sx={{ fontFamily: 'Inter' }}>
                {space.member_count}
              </Typography>
            </Box>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
            {new Date(space.created_at).toLocaleDateString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, fontFamily: 'Inter' }}>
            Project Spaces
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
            Organize your documents into dedicated project workspaces
          </Typography>
        </Box>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ 
            borderRadius: 2,
            textTransform: 'none',
            fontFamily: 'Inter',
            fontWeight: 500
          }}
        >
          Create Space
        </Button>
      </Box>

      {/* Spaces Grid */}
      <Grid container spacing={3}>
        {spaces.map((space) => (
          <Grid item xs={12} sm={6} md={4} key={space.id}>
            <SpaceCard space={space} />
          </Grid>
        ))}
      </Grid>

      {/* Create Space Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontFamily: 'Inter', fontWeight: 600 }}>
          Create New Project Space
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Space Name"
              value={newSpace.name}
              onChange={(e) => setNewSpace({ ...newSpace, name: e.target.value })}
              sx={{ mb: 2 }}
              InputProps={{ sx: { fontFamily: 'Inter' } }}
              InputLabelProps={{ sx: { fontFamily: 'Inter' } }}
            />
            
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={newSpace.description}
              onChange={(e) => setNewSpace({ ...newSpace, description: e.target.value })}
              sx={{ mb: 2 }}
              InputProps={{ sx: { fontFamily: 'Inter' } }}
              InputLabelProps={{ sx: { fontFamily: 'Inter' } }}
            />
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel sx={{ fontFamily: 'Inter' }}>Icon</InputLabel>
                  <Select
                    value={newSpace.icon}
                    onChange={(e) => setNewSpace({ ...newSpace, icon: e.target.value })}
                    label="Icon"
                    sx={{ fontFamily: 'Inter' }}
                  >
                    <MenuItem value="folder">📁 Folder</MenuItem>
                    <MenuItem value="gavel">⚖️ Legal</MenuItem>
                    <MenuItem value="science">🔬 Research</MenuItem>
                    <MenuItem value="business">💼 Business</MenuItem>
                    <MenuItem value="school">🎓 Education</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Color"
                  type="color"
                  value={newSpace.color}
                  onChange={(e) => setNewSpace({ ...newSpace, color: e.target.value })}
                  InputProps={{ sx: { fontFamily: 'Inter' } }}
                  InputLabelProps={{ sx: { fontFamily: 'Inter' } }}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setCreateDialogOpen(false)}
            sx={{ fontFamily: 'Inter' }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleCreateSpace}
            variant="contained"
            disabled={!newSpace.name.trim() || loading}
            sx={{ fontFamily: 'Inter' }}
          >
            {loading ? <CircularProgress size={20} /> : 'Create Space'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Space Details Dialog */}
      <Dialog 
        open={selectedSpace && !editDialogOpen && !membersDialogOpen} 
        onClose={() => setSelectedSpace(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedSpace && (
          <>
            <DialogTitle sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2,
              fontFamily: 'Inter',
              fontWeight: 600
            }}>
              <Avatar sx={{ bgcolor: selectedSpace.color }}>
                {getSpaceIcon(selectedSpace.icon)}
              </Avatar>
              {selectedSpace.name}
              <Chip 
                label={selectedSpace.user_role} 
                size="small" 
                color={selectedSpace.user_role === 'owner' ? 'primary' : 'default'}
              />
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" sx={{ mb: 3, fontFamily: 'Inter' }}>
                {selectedSpace.description}
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <DocumentsIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                    <Typography variant="h4" sx={{ fontWeight: 600, fontFamily: 'Inter' }}>
                      {selectedSpace.document_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
                      Documents
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                    <Typography variant="h4" sx={{ fontWeight: 600, fontFamily: 'Inter' }}>
                      {selectedSpace.member_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
                      Members
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={4}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <AnalyticsIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                    <Typography variant="h4" sx={{ fontWeight: 600, fontFamily: 'Inter' }}>
                      85%
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
                      Processed
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button 
                startIcon={<PeopleIcon />}
                onClick={() => setMembersDialogOpen(true)}
                sx={{ fontFamily: 'Inter' }}
              >
                Manage Members
              </Button>
              {selectedSpace.user_role === 'owner' && (
                <>
                  <Button 
                    startIcon={<EditIcon />}
                    onClick={() => setEditDialogOpen(true)}
                    sx={{ fontFamily: 'Inter' }}
                  >
                    Edit Space
                  </Button>
                  <Button 
                    startIcon={<DeleteIcon />}
                    color="error"
                    onClick={() => {
                      handleDeleteSpace(selectedSpace.id);
                      setSelectedSpace(null);
                    }}
                    sx={{ fontFamily: 'Inter' }}
                  >
                    Delete Space
                  </Button>
                </>
              )}
              <Button 
                onClick={() => setSelectedSpace(null)}
                sx={{ fontFamily: 'Inter' }}
              >
                Close
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Upload Dialog */}
      <Dialog 
        open={uploadDialogOpen} 
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontFamily: 'Inter', fontWeight: 600 }}>
          Upload Documents to {selectedSpace?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <input
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif"
              style={{ display: 'none' }}
              id="file-upload"
              multiple
              type="file"
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<UploadIcon />}
                sx={{ 
                  mb: 2, 
                  fontFamily: 'Inter',
                  borderColor: selectedSpace?.color,
                  color: selectedSpace?.color,
                  '&:hover': {
                    borderColor: selectedSpace?.color,
                    backgroundColor: `${selectedSpace?.color}10`
                  }
                }}
              >
                Select Files
              </Button>
            </label>
            
            {selectedFiles.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ fontFamily: 'Inter', mb: 1 }}>
                  Selected Files ({selectedFiles.length}):
                </Typography>
                <List dense>
                  {selectedFiles.map((file, index) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: selectedSpace?.color, width: 32, height: 32 }}>
                          <DocumentsIcon fontSize="small" />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={file.name}
                        secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                        sx={{ fontFamily: 'Inter' }}
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          size="small"
                          onClick={() => {
                            const newFiles = selectedFiles.filter((_, i) => i !== index);
                            setSelectedFiles(newFiles);
                          }}
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ fontFamily: 'Inter', mb: 1 }}>
                  Uploading... {uploadProgress}%
                </Typography>
                <Box sx={{ width: '100%', bgcolor: 'grey.200', borderRadius: 1, overflow: 'hidden' }}>
                  <Box 
                    sx={{ 
                      width: `${uploadProgress}%`, 
                      height: 8, 
                      bgcolor: selectedSpace?.color,
                      transition: 'width 0.3s ease'
                    }} 
                  />
                </Box>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setUploadDialogOpen(false)}
            disabled={uploading}
            sx={{ fontFamily: 'Inter' }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleUploadToSpace}
            disabled={selectedFiles.length === 0 || uploading}
            variant="contained"
            sx={{ 
              fontFamily: 'Inter',
              backgroundColor: selectedSpace?.color,
              '&:hover': {
                backgroundColor: selectedSpace?.color,
                opacity: 0.9
              }
            }}
          >
            {uploading ? 'Uploading...' : `Upload ${selectedFiles.length} File(s)`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Alert */}
      {spaces.length > 0 && (
        <Alert 
          severity="info" 
          sx={{ 
            mt: 4, 
            fontFamily: 'Inter',
            '& .MuiAlert-message': { fontFamily: 'Inter' }
          }}
        >
          💡 <strong>Tip:</strong> Click on any project space to view details, manage documents, and collaborate with team members. 
          Use different colors and icons to easily identify your projects!
        </Alert>
      )}
    </Box>
  );
};

export default ProjectSpaces;
