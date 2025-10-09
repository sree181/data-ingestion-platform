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
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Menu,
  MenuItem,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Dashboard as BoardIcon,
  MoreVert as MoreIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Launch as OpenIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

export default function InvestigationBoards() {
  const navigate = useNavigate();
  
  // State
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedBoard, setSelectedBoard] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'active'
  });

  // Load boards
  useEffect(() => {
    loadBoards();
  }, []);

  const loadBoards = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.investigationBoard.getBoards();
      setBoards(response.boards || []);
    } catch (err) {
      console.error('Failed to load boards:', err);
      setError('Failed to load investigation boards. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBoard = async () => {
    try {
      await apiService.investigationBoard.createBoard(formData);
      setCreateDialogOpen(false);
      setFormData({ title: '', description: '', status: 'active' });
      loadBoards();
    } catch (err) {
      console.error('Failed to create board:', err);
      setError('Failed to create board. Please try again.');
    }
  };

  const handleDeleteBoard = async (boardId) => {
    if (!window.confirm('Are you sure you want to delete this board? This action cannot be undone.')) {
      return;
    }
    
    try {
      await apiService.investigationBoard.deleteBoard(boardId);
      loadBoards();
      handleCloseMenu();
    } catch (err) {
      console.error('Failed to delete board:', err);
      setError('Failed to delete board. Please try again.');
    }
  };

  const handleExportBoard = async (boardId) => {
    try {
      const data = await apiService.investigationBoard.exportBoard(boardId);
      
      // Download as JSON
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `investigation-board-${boardId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      handleCloseMenu();
    } catch (err) {
      console.error('Failed to export board:', err);
      setError('Failed to export board. Please try again.');
    }
  };

  const handleOpenMenu = (event, board) => {
    setMenuAnchor(event.currentTarget);
    setSelectedBoard(board);
  };

  const handleCloseMenu = () => {
    setMenuAnchor(null);
    setSelectedBoard(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'archived': return 'default';
      case 'completed': return 'primary';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Investigation Boards
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Organize and explore entity connections
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ borderRadius: 2, px: 3 }}
        >
          New Board
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!loading && boards.length === 0 && (
        <Card sx={{ p: 8, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <BoardIcon sx={{ fontSize: 80, color: 'white', mb: 2 }} />
          <Typography variant="h5" gutterBottom sx={{ color: 'white', fontWeight: 600 }}>
            No Investigation Boards Yet
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: 'rgba(255,255,255,0.9)' }}>
            Create your first board to start organizing entities and discoveries
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{ 
              bgcolor: 'white', 
              color: '#667eea',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' }
            }}
          >
            Create First Board
          </Button>
        </Card>
      )}

      {/* Boards Grid */}
      {!loading && boards.length > 0 && (
        <Grid container spacing={3}>
          {boards.map((board) => (
            <Grid item xs={12} sm={6} md={4} key={board.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Chip 
                      label={board.status || 'active'} 
                      size="small" 
                      color={getStatusColor(board.status)}
                    />
                    <IconButton 
                      size="small" 
                      onClick={(e) => handleOpenMenu(e, board)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </Box>
                  
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                    {board.title}
                  </Typography>
                  
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
                    {board.description || 'No description'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, mt: 'auto' }}>
                    <Chip 
                      label={`${board.entity_count || 0} entities`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                    Updated {formatDate(board.updated_at)}
                  </Typography>
                </CardContent>
                
                <CardActions sx={{ px: 2, pb: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<OpenIcon />}
                    onClick={() => navigate(`/investigations/${board.id}`)}
                  >
                    Open Board
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => {
          navigate(`/investigations/${selectedBoard?.id}`);
          handleCloseMenu();
        }}>
          <OpenIcon sx={{ mr: 1 }} fontSize="small" />
          Open Board
        </MenuItem>
        <MenuItem onClick={() => {
          // TODO: Implement edit
          handleCloseMenu();
        }}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit Details
        </MenuItem>
        <MenuItem onClick={() => handleExportBoard(selectedBoard?.id)}>
          <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
          Export as JSON
        </MenuItem>
        <MenuItem 
          onClick={() => handleDeleteBoard(selectedBoard?.id)}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete Board
        </MenuItem>
      </Menu>

      {/* Create Board Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Investigation Board</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Board Title"
            fullWidth
            variant="outlined"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setCreateDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateBoard} 
            variant="contained"
            disabled={!formData.title.trim()}
          >
            Create Board
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

