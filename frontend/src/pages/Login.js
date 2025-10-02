import React, { useState, useEffect } from 'react';
// Cache bust: 2025-10-01-12:50 - Minimalistic design with subtle colors
import {
  Box, Container, Paper, TextField, Button, Typography, Alert,
  CircularProgress, Card, CardContent, CardActions, Divider,
  FormControl, InputLabel, Select, MenuItem, Chip, Stack
} from '@mui/material';
import {
  Lock as LockIcon, Email as EmailIcon, Security as SecurityIcon,
  Business as BusinessIcon, VpnKey as VpnKeyIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    organization: 'default'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [organizations] = useState([
    { id: 'default', name: 'Default Organization', level: 'admin' },
    { id: 'enterprise', name: 'Enterprise Corp', level: 'user' },
    { id: 'government', name: 'Government Agency', level: 'restricted' }
  ]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Store authentication data with organization info
      const authData = {
        ...data,
        user: {
          ...data.user,
          organization: formData.organization,
          organization_level: organizations.find(org => org.id === formData.organization)?.level || 'user'
        }
      };
      
      login(authData);
      navigate('/dashboard');
      
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getOrganizationColor = (level) => {
    switch (level) {
      case 'admin': return 'success';
      case 'user': return 'primary';
      case 'restricted': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f7fafc 0%, #e2e8f0 50%, #cbd5e0 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif'
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={0}
          sx={{
            borderRadius: 4,
            overflow: 'hidden',
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            border: '1px solid rgba(0,0,0,0.06)',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)'
          }}
        >
          {/* Header */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #4a5568 0%, #2d3748 100%)',
              color: 'white',
              p: 4,
              textAlign: 'center'
            }}
          >
            <Box
              sx={{
                width: 60,
                height: 60,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #38b2ac 0%, #319795 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                boxShadow: '0 4px 12px rgba(56, 178, 172, 0.3)'
              }}
            >
              <SecurityIcon sx={{ fontSize: 28, color: 'white' }} />
            </Box>
            <Typography 
              variant="h4" 
              component="h1" 
              fontWeight="300" 
              gutterBottom
              sx={{ 
                fontSize: '2rem',
                letterSpacing: '-0.02em',
                fontFamily: '"Inter", sans-serif'
              }}
            >
              Welcome Back
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                opacity: 0.8,
                fontSize: '0.95rem',
                fontWeight: 400
              }}
            >
              Sign in to continue to your workspace
            </Typography>
          </Box>

          {/* Login Form */}
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={handleLogin}>
              <Stack spacing={3}>
                {/* Error Alert */}
                {error && (
                  <Alert 
                    severity="error" 
                    sx={{ 
                      borderRadius: 2,
                      backgroundColor: '#fef2f2',
                      border: '1px solid #fecaca',
                      '& .MuiAlert-icon': {
                        color: '#dc2626'
                      }
                    }}
                  >
                    {error}
                  </Alert>
                )}

                {/* Email Field */}
                <TextField
                  fullWidth
                  label="Email Address"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  placeholder="Enter your email"
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ color: '#718096', mr: 1.5, fontSize: 20 }} />
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 3,
                      backgroundColor: '#f8fafc',
                      '&:hover fieldset': {
                        borderColor: '#38b2ac',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: '#38b2ac',
                        borderWidth: 2,
                      },
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: '#38b2ac',
                    }
                  }}
                />

                {/* Password Field */}
                <TextField
                  fullWidth
                  label="Password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  placeholder="Enter your password"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ color: '#718096', mr: 1.5, fontSize: 20 }} />
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 3,
                      backgroundColor: '#f8fafc',
                      '&:hover fieldset': {
                        borderColor: '#38b2ac',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: '#38b2ac',
                        borderWidth: 2,
                      },
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: '#38b2ac',
                    }
                  }}
                />

                {/* Organization Field */}
                <FormControl fullWidth required>
                  <InputLabel>Organization</InputLabel>
                  <Select
                    name="organization"
                    value={formData.organization}
                    onChange={handleInputChange}
                    startAdornment={<BusinessIcon sx={{ color: '#718096', mr: 1.5, fontSize: 20 }} />}
                    sx={{
                      borderRadius: 3,
                      backgroundColor: '#f8fafc',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#38b2ac',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#38b2ac',
                        borderWidth: 2,
                      },
                    }}
                  >
                    {organizations.map((org) => (
                      <MenuItem key={org.id} value={org.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          <Typography variant="body1" sx={{ flexGrow: 1, fontWeight: 400 }}>
                            {org.name}
                          </Typography>
                          <Chip
                            label={org.level}
                            size="small"
                            sx={{
                              backgroundColor: org.level === 'admin' ? '#e6fffa' : org.level === 'user' ? '#ebf8ff' : '#f7fafc',
                              color: org.level === 'admin' ? '#234e52' : org.level === 'user' ? '#2c5282' : '#4a5568',
                              border: '1px solid',
                              borderColor: org.level === 'admin' ? '#38b2ac' : org.level === 'user' ? '#3182ce' : '#e2e8f0',
                              fontWeight: 500,
                              fontSize: '0.75rem'
                            }}
                          />
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Login Button */}
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <VpnKeyIcon />}
                  sx={{
                    py: 1.8,
                    background: 'linear-gradient(135deg, #38b2ac 0%, #319795 100%)',
                    color: 'white',
                    fontWeight: 500,
                    fontSize: '1rem',
                    textTransform: 'none',
                    letterSpacing: '0.01em',
                    borderRadius: 3,
                    boxShadow: '0 4px 14px rgba(56, 178, 172, 0.25)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #319795 0%, #2c7a7b 100%)',
                      boxShadow: '0 6px 20px rgba(56, 178, 172, 0.35)',
                      transform: 'translateY(-1px)',
                    },
                    '&:disabled': {
                      background: '#e2e8f0',
                      color: '#a0aec0',
                      boxShadow: 'none',
                      transform: 'none',
                    },
                    fontFamily: '"Inter", sans-serif'
                  }}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </Stack>
            </form>
          </CardContent>

          {/* Footer */}
          <CardActions sx={{ p: 3, justifyContent: 'center', backgroundColor: '#f8fafc' }}>
            <Typography 
              variant="body2" 
              color="text.secondary" 
              textAlign="center"
              sx={{ 
                fontSize: '0.875rem',
                lineHeight: 1.6,
                fontFamily: '"Inter", sans-serif'
              }}
            >
              <strong>For Testing:</strong> Use any email and password combination.<br />
              <strong>Examples:</strong> admin@test.com / password123<br />
              Select your organization to determine access level.
            </Typography>
          </CardActions>
        </Paper>

        {/* Enterprise Security Features */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography 
            variant="h6" 
            color="#4a5568" 
            gutterBottom 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              mb: 2,
              fontWeight: 500,
              fontSize: '1rem',
              fontFamily: '"Inter", sans-serif'
            }}
          >
            <SecurityIcon sx={{ mr: 1, fontSize: 18, color: '#38b2ac' }} />
            Enterprise Security Features
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
            {['JWT Authentication', 'Role-Based Access', 'Audit Logging', 'Project-Level Permissions', 'Data Encryption', 'Session Management'].map((feature) => (
              <Chip
                key={feature}
                label={feature}
                size="small"
                sx={{
                  backgroundColor: 'rgba(56, 178, 172, 0.08)',
                  color: '#2d3748',
                  border: '1px solid rgba(56, 178, 172, 0.2)',
                  fontWeight: 400,
                  fontSize: '0.75rem',
                  '&:hover': {
                    backgroundColor: 'rgba(56, 178, 172, 0.12)',
                  }
                }}
              />
            ))}
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Login;