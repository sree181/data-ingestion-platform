import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
        console.log('✅ Restored session from localStorage');
      } catch (error) {
        console.error('❌ Error parsing user data:', error);
        // Clear invalid data
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  const login = (authData) => {
    setUser(authData.user);
    setIsAuthenticated(true);
    // Store in localStorage for persistence
    localStorage.setItem('access_token', authData.access_token);
    localStorage.setItem('user', JSON.stringify(authData.user));
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  const hasPermission = (requiredLevel) => {
    if (!user) return false;
    
    const accessLevels = {
      'restricted': 1,
      'user': 2,
      'admin': 3
    };
    
    const userLevel = accessLevels[user.organization_level] || 1;
    const requiredLevelValue = accessLevels[requiredLevel] || 1;
    
    return userLevel >= requiredLevelValue;
  };

  const canAccessProject = (projectId, action = 'read') => {
    if (!user) return false;
    
    // For now, implement basic project access logic
    // In a real system, this would check against project-specific permissions
    const userLevel = user.organization_level;
    
    switch (action) {
      case 'read':
        return ['user', 'admin'].includes(userLevel);
      case 'write':
        return ['admin'].includes(userLevel);
      case 'delete':
        return ['admin'].includes(userLevel);
      case 'admin':
        return ['admin'].includes(userLevel);
      default:
        return false;
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    hasPermission,
    canAccessProject
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
