import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Box, Typography, Alert, CircularProgress
} from '@mui/material';
import { Lock as LockIcon, Email as EmailIcon } from '@mui/icons-material';

const LoginDialog = ({ open, onClose, onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Store token in localStorage
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Call the onLogin callback
      onLogin(data);
      
      // Close dialog
      onClose();
      
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ 
        background: 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
        color: 'white',
        textAlign: 'center',
        py: 3
      }}>
        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
          <LockIcon />
          <Typography variant="h4" fontWeight={600}>
            Login Required
          </Typography>
        </Box>
        <Typography variant="subtitle1" sx={{ opacity: 0.9, mt: 1 }}>
          Please authenticate to access this feature
        </Typography>
      </DialogTitle>
      
      <DialogContent dividers sx={{ p: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyPress={handleKeyPress}
            InputProps={{
              startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            placeholder="Enter your email"
            disabled={loading}
          />
          
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={handleKeyPress}
            InputProps={{
              startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            placeholder="Enter your password"
            disabled={loading}
          />
        </Box>
        
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>For testing:</strong> Enter any email and password to login.
            The system will generate a valid JWT token for authentication.
          </Typography>
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 3, justifyContent: 'space-between' }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleLogin}
          variant="contained"
          disabled={loading || !email || !password}
          startIcon={loading ? <CircularProgress size={20} /> : <LockIcon />}
          sx={{ minWidth: 120 }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LoginDialog;
