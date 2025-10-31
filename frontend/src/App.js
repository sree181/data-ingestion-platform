import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Theme Context
import { ThemeContextProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';

// Components
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';

// Pages
import Dashboard from './pages/Dashboard';
import EnhancedDashboard from './pages/EnhancedDashboard';
import Search from './pages/Search';
import Upload from './pages/Upload';
import Analytics from './pages/Analytics';
import Knowledge from './pages/Knowledge';
import Documents from './pages/Documents';
import DocumentsWithSearch from './pages/DocumentsWithSearch';
import EnhancedDocuments from './pages/EnhancedDocuments';
import DocumentViewer from './pages/DocumentViewer';
import ProfessionalDocumentViewer from './pages/ProfessionalDocumentViewer';
import KnowledgeGraph from './pages/KnowledgeGraph';
import InvestigativeWorkspace from './pages/InvestigativeWorkspace';
import EnhancedInvestigativeWorkspace from './pages/EnhancedInvestigativeWorkspace';
import EntityEnrichment from './pages/EntityEnrichment';
import Chat from './pages/Chat';
import ProjectSpaces from './pages/ProjectSpaces';
import LeaseManagement from './pages/LeaseManagement';
import EnhancedProjectSpaces from './pages/EnhancedProjectSpaces';
import OptimizedProjectSpaces from './pages/OptimizedProjectSpaces';
import EnhancedProjectSpacesOptimized from './pages/EnhancedProjectSpacesOptimized';
import SecurityDashboard from './pages/SecurityDashboard';
import SecurityTesting from './pages/SecurityTesting';
import UnifiedSearch from './pages/UnifiedSearch';
import SourceConfiguration from './pages/SourceConfiguration';
import KnowledgeHub from './pages/KnowledgeHub';
import InvestigationBoards from './pages/InvestigationBoards';
import InvestigationBoardCanvas from './pages/InvestigationBoardCanvas';
import WorkflowBuilder from './pages/WorkflowBuilder';
import LiteratureAutomation from './pages/LiteratureAutomation';
import ICSRAutomation from './pages/ICSRAutomation';
import ICSRReviewer from './pages/ICSRReviewer';
import RLDashboard from './pages/RLDashboard';
import RLIntelligenceDashboard from './pages/RLIntelligenceDashboard';
import Login from './pages/Login';
import { SecurityProvider } from './contexts/SecurityContext';
import ProtectedRoute from './components/ProtectedRoute';

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Make queryClient globally available for cache invalidation
window.queryClient = queryClient;

// App Content Component
function AppContent() {
  const { theme, isDarkMode } = useTheme();

  return (
    <SecurityProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Routes>
            {/* Public route - Login */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected routes - all under ProtectedRoute wrapper */}
            <Route path="/*" element={
              <ProtectedRoute>
                <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                  <Sidebar />
                  <Box
                    component="main"
                    sx={{
                      flexGrow: 1,
                      bgcolor: 'background.default',
                      overflow: 'hidden',
                    }}
                  >
                    <TopBar />
                    <Box sx={{ p: 3, height: 'calc(100vh - 64px)', overflow: 'auto' }}>
                      <Routes>
                        <Route path="/" element={<EnhancedDashboard />} />
                        <Route path="dashboard" element={<EnhancedDashboard />} />
                        <Route path="dashboard-legacy" element={<Dashboard />} />

                        <Route path="upload" element={<Upload />} />
                        <Route path="documents" element={<EnhancedDocuments />} />
                        <Route path="chat" element={<Chat />} />
                        <Route path="document/:documentId" element={<DocumentViewer />} />
                        <Route path="professional-document/:documentId" element={<ProfessionalDocumentViewer />} />

                        <Route path="knowledge" element={<KnowledgeGraph />} />
                        <Route path="knowledge-hub" element={<KnowledgeHub />} />
                        <Route path="investigations" element={<InvestigationBoards />} />
                        <Route path="investigations/:boardId" element={<InvestigationBoardCanvas />} />
                        <Route path="investigation" element={<EnhancedInvestigativeWorkspace />} />
                        <Route path="workflow-builder" element={<WorkflowBuilder />} />
                        <Route path="entity-enrichment" element={<EntityEnrichment />} />
                        <Route path="spaces" element={<EnhancedProjectSpacesOptimized />} />
                        <Route path="lease-management" element={<LeaseManagement />} />
                        <Route path="unified-search" element={<UnifiedSearch />} />
                        <Route path="source-configuration" element={<SourceConfiguration />} />
                        <Route path="literature-automation" element={<LiteratureAutomation />} />
                        <Route path="icsr-automation" element={<ICSRAutomation />} />
                        <Route path="icsr-reviewer" element={<ICSRReviewer />} />
                        <Route path="rl-dashboard" element={<RLDashboard />} />
                        <Route path="rl-intelligence" element={<RLIntelligenceDashboard />} />
                        <Route path="security" element={<ProtectedRoute requiredLevel="admin"><SecurityDashboard /></ProtectedRoute>} />
                        <Route path="security-testing" element={<ProtectedRoute requiredLevel="admin"><SecurityTesting /></ProtectedRoute>} />
                      </Routes>
                    </Box>
                  </Box>
                </Box>
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
        
        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: isDarkMode ? '#1e293b' : '#333',
              color: isDarkMode ? '#f8fafc' : '#fff',
              fontFamily: 'Inter',
              border: isDarkMode ? '1px solid #334155' : 'none',
            },
            success: {
              style: {
                background: isDarkMode ? '#10b981' : '#2e7d32',
              },
            },
            error: {
              style: {
                background: isDarkMode ? '#ef4444' : '#d32f2f',
              },
            },
          }}
        />
      </ThemeProvider>
    </SecurityProvider>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContextProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeContextProvider>
    </QueryClientProvider>
  );
}

export default App;