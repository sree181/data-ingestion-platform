import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Tooltip,
  Menu,
  MenuItem,
  Chip,
  Avatar,
  Divider,
  ListItemIcon,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  Refresh as RefreshIcon,
  AccountCircle as AccountIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';

const pageInfo = {
  '/dashboard': {
    title: 'Dashboard',
    subtitle: 'Monitor your data ingestion platform performance',
  },
  '/search': {
    title: 'Intelligent Search',
    subtitle: 'Find documents using advanced AI-powered search',
  },
  '/upload': {
    title: 'Upload Documents',
    subtitle: 'Add new documents to your knowledge base',
  },
  '/documents': {
    title: 'Document Library',
    subtitle: 'Browse and manage your document collection',
  },
  '/analytics': {
    title: 'Analytics',
    subtitle: 'Discover insights and trends in your data',
  },
  '/knowledge': {
    title: 'Knowledge Graph',
    subtitle: 'Explore relationships and connections',
  },
};

function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationCount] = useState(3); // Mock notification count
  const { isDarkMode, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const currentPage = pageInfo[location.pathname] || {
    title: 'Data Platform',
    subtitle: 'Enterprise Document Intelligence',
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleMenuClose();
  };

  const getUserInitials = () => {
    if (user?.full_name) {
      return user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return 'U';
  };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
        color: 'text.primary',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: 3 }}>
        {/* Page Info */}
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.25 }}>
            {currentPage.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {currentPage.subtitle}
          </Typography>
        </Box>

        {/* Actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* System Status */}
          <Chip
            label="Online"
            size="small"
            color="success"
            variant="outlined"
            sx={{ mr: 2 }}
          />

          {/* Theme Toggle */}
          <Tooltip title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
            <IconButton
              onClick={toggleTheme}
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              {isDarkMode ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Refresh Button */}
          <Tooltip title="Refresh Data">
            <IconButton
              onClick={handleRefresh}
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <Badge badgeContent={notificationCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* Help */}
          <Tooltip title="Help & Documentation">
            <IconButton
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <HelpIcon />
            </IconButton>
          </Tooltip>

          {/* Settings */}
          <Tooltip title="Settings">
            <IconButton
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>

          {/* User Menu */}
          <Tooltip title={user?.email || 'User Menu'}>
            <IconButton
              onClick={handleMenuOpen}
              sx={{
                bgcolor: 'action.hover',
                '&:hover': {
                  bgcolor: 'action.selected',
                },
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: 'primary.main',
                  fontSize: '0.875rem',
                }}
              >
                {getUserInitials()}
              </Avatar>
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            PaperProps={{
              sx: {
                mt: 1,
                minWidth: 240,
                borderRadius: 2,
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
              },
            }}
          >
            {/* User Info Header */}
            <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle2" fontWeight={600}>
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user?.email || 'user@example.com'}
              </Typography>
              {user?.organization && (
                <Chip
                  label={user.organization}
                  size="small"
                  sx={{ 
                    mt: 0.5, 
                    height: 20, 
                    fontSize: '0.7rem',
                    backgroundColor: 'rgba(56, 178, 172, 0.1)',
                    color: 'primary.main'
                  }}
                />
              )}
            </Box>

            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <PersonIcon fontSize="small" />
              </ListItemIcon>
              Profile
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              Account Settings
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <HelpIcon fontSize="small" />
              </ListItemIcon>
              Help & Support
            </MenuItem>
            
            <Divider sx={{ my: 1 }} />
            
            <MenuItem 
              onClick={handleLogout}
              sx={{
                color: 'error.main',
                '&:hover': {
                  backgroundColor: 'error.lighter',
                }
              }}
            >
              <ListItemIcon>
                <LogoutIcon fontSize="small" sx={{ color: 'error.main' }} />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;