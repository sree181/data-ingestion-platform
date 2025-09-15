import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const SecurityContext = createContext();

export const useSecurityContext = () => {
  const context = useContext(SecurityContext);
  if (!context) {
    throw new Error('useSecurityContext must be used within a SecurityProvider');
  }
  return context;
};

export const SecurityProvider = ({ children }) => {
  const [securityData, setSecurityData] = useState({
    dashboard: null,
    alerts: [],
    complianceFrameworks: [],
    encryptionKeys: [],
    auditEvents: [],
    securityHealth: null,
    loading: true,
    error: null
  });

  const [userSecurity, setUserSecurity] = useState({
    mfaEnabled: false,
    securityClearance: 'internal',
    permissions: [],
    currentProject: null
  });

  // Load security dashboard data
  const loadSecurityDashboard = async (projectId = null) => {
    try {
      setSecurityData(prev => ({ ...prev, loading: true, error: null }));
      
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/api/v1/security/dashboard${params}`);
      
      setSecurityData(prev => ({
        ...prev,
        dashboard: response.data,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to load security dashboard:', error);
      setSecurityData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load security dashboard'
      }));
    }
  };

  // Load security alerts
  const loadSecurityAlerts = async (projectId = null, filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId);
      if (filters.status) params.append('status', filters.status);
      if (filters.threat_level) params.append('threat_level', filters.threat_level);
      if (filters.limit) params.append('limit', filters.limit);
      
      const response = await api.get(`/api/v1/security/monitoring/alerts?${params}`);
      
      setSecurityData(prev => ({
        ...prev,
        alerts: response.data
      }));
    } catch (error) {
      console.error('Failed to load security alerts:', error);
    }
  };

  // Load compliance frameworks
  const loadComplianceFrameworks = async () => {
    try {
      const response = await api.get('/api/v1/security/compliance/frameworks');
      
      setSecurityData(prev => ({
        ...prev,
        complianceFrameworks: response.data
      }));
    } catch (error) {
      console.error('Failed to load compliance frameworks:', error);
    }
  };

  // Assess project compliance
  const assessCompliance = async (projectId, framework) => {
    try {
      const response = await api.post('/api/v1/security/compliance/assess', {
        project_id: projectId,
        framework: framework
      });
      
      return response.data;
    } catch (error) {
      console.error('Failed to assess compliance:', error);
      throw error;
    }
  };

  // Generate compliance report
  const generateComplianceReport = async (projectId, framework, reportType = 'assessment') => {
    try {
      const response = await api.post('/api/v1/security/compliance/report', {
        project_id: projectId,
        framework: framework,
        report_type: reportType
      });
      
      return response.data;
    } catch (error) {
      console.error('Failed to generate compliance report:', error);
      throw error;
    }
  };

  // Load encryption keys
  const loadEncryptionKeys = async (projectId) => {
    try {
      const response = await api.get(`/api/v1/security/encryption/keys?project_id=${projectId}`);
      
      setSecurityData(prev => ({
        ...prev,
        encryptionKeys: response.data
      }));
    } catch (error) {
      console.error('Failed to load encryption keys:', error);
    }
  };

  // Create encryption key
  const createEncryptionKey = async (projectId) => {
    try {
      const response = await api.post('/api/v1/security/encryption/keys', {
        project_id: projectId
      });
      
      // Reload keys
      await loadEncryptionKeys(projectId);
      
      return response.data;
    } catch (error) {
      console.error('Failed to create encryption key:', error);
      throw error;
    }
  };

  // Rotate encryption key
  const rotateEncryptionKey = async (keyId) => {
    try {
      const response = await api.post(`/api/v1/security/encryption/keys/${keyId}/rotate`);
      
      return response.data;
    } catch (error) {
      console.error('Failed to rotate encryption key:', error);
      throw error;
    }
  };

  // Load audit events
  const loadAuditEvents = async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (filters.project_id) params.append('project_id', filters.project_id);
      if (filters.user_id) params.append('user_id', filters.user_id);
      if (filters.event_type) params.append('event_type', filters.event_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.limit) params.append('limit', filters.limit);
      
      const response = await api.get(`/api/v1/security/audit/events?${params}`);
      
      setSecurityData(prev => ({
        ...prev,
        auditEvents: response.data
      }));
    } catch (error) {
      console.error('Failed to load audit events:', error);
    }
  };

  // Log security event
  const logSecurityEvent = async (eventData) => {
    try {
      const response = await api.post('/api/v1/security/monitoring/events', eventData);
      
      return response.data;
    } catch (error) {
      console.error('Failed to log security event:', error);
      throw error;
    }
  };

  // Resolve security alert
  const resolveSecurityAlert = async (alertId, resolutionData = {}) => {
    try {
      const response = await api.post(`/api/v1/security/monitoring/alerts/${alertId}/resolve`, resolutionData);
      
      // Reload alerts
      await loadSecurityAlerts();
      
      return response.data;
    } catch (error) {
      console.error('Failed to resolve security alert:', error);
      throw error;
    }
  };

  // Load security health
  const loadSecurityHealth = async (projectId = null) => {
    try {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/api/v1/security/health${params}`);
      
      setSecurityData(prev => ({
        ...prev,
        securityHealth: response.data
      }));
    } catch (error) {
      console.error('Failed to load security health:', error);
    }
  };

  // Get executive security summary
  const getExecutiveSummary = async (projectId = null) => {
    try {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/api/v1/security/reports/executive-summary${params}`);
      
      return response.data;
    } catch (error) {
      console.error('Failed to get executive summary:', error);
      throw error;
    }
  };

  // Initialize security context
  useEffect(() => {
    const initializeSecurity = async () => {
      try {
        await Promise.all([
          loadSecurityDashboard(),
          loadSecurityAlerts(),
          loadComplianceFrameworks(),
          loadSecurityHealth()
        ]);
      } catch (error) {
        console.error('Failed to initialize security context:', error);
      }
    };

    initializeSecurity();
  }, []);

  // Auto-refresh security data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadSecurityAlerts();
      loadSecurityHealth();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const contextValue = {
    // State
    securityData,
    userSecurity,
    
    // Dashboard functions
    loadSecurityDashboard,
    loadSecurityHealth,
    getExecutiveSummary,
    
    // Alert functions
    loadSecurityAlerts,
    resolveSecurityAlert,
    logSecurityEvent,
    
    // Compliance functions
    loadComplianceFrameworks,
    assessCompliance,
    generateComplianceReport,
    
    // Encryption functions
    loadEncryptionKeys,
    createEncryptionKey,
    rotateEncryptionKey,
    
    // Audit functions
    loadAuditEvents,
    
    // Utility functions
    setUserSecurity,
    refreshSecurityData: () => {
      loadSecurityDashboard();
      loadSecurityAlerts();
      loadSecurityHealth();
    }
  };

  return (
    <SecurityContext.Provider value={contextValue}>
      {children}
    </SecurityContext.Provider>
  );
};
