import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, CircularProgress, Typography } from '@mui/material';

const ProtectedRoute = ({ children, requiredLevel = 'user' }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading while checking authentication
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}
      >
        <CircularProgress size={60} sx={{ color: 'white', mb: 2 }} />
        <Typography variant="h6" color="white">
          Verifying Access...
        </Typography>
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check access level if required
  const accessLevels = {
    'restricted': 1,
    'user': 2,
    'admin': 3
  };

  const userLevel = accessLevels[user?.organization_level] || 1;
  const requiredLevelValue = accessLevels[requiredLevel] || 1;

  if (userLevel < requiredLevelValue) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          p: 4
        }}
      >
        <Typography variant="h4" color="white" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="h6" color="white" textAlign="center" sx={{ mb: 3 }}>
          You don't have sufficient permissions to access this resource.
        </Typography>
        <Typography variant="body1" color="white" textAlign="center">
          Required Level: {requiredLevel} | Your Level: {user?.organization_level}
        </Typography>
      </Box>
    );
  }

  return children;
};

export default ProtectedRoute;
