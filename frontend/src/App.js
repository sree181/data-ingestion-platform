import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Theme Context
import { ThemeContextProvider, useTheme } from './contexts/ThemeContext';

// Components
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';

// Pages
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import Upload from './pages/Upload';
import Analytics from './pages/Analytics';
import Knowledge from './pages/Knowledge';
import Documents from './pages/Documents';
import DocumentsWithSearch from './pages/DocumentsWithSearch';
import EnhancedDocuments from './pages/EnhancedDocuments';
import DocumentViewer from './pages/DocumentViewer';
import KnowledgeGraph from './pages/KnowledgeGraph';
import InvestigativeWorkspace from './pages/InvestigativeWorkspace';
import EnhancedInvestigativeWorkspace from './pages/EnhancedInvestigativeWorkspace';
import EntityEnrichment from './pages/EntityEnrichment';
import Chat from './pages/Chat';
import ProjectSpaces from './pages/ProjectSpaces';
import LeaseManagement from './pages/LeaseManagement';
import EnhancedProjectSpaces from './pages/EnhancedProjectSpaces';
import { SecurityProvider } from './contexts/SecurityContext';

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

// App Content Component
function AppContent() {
  const { theme, isDarkMode } = useTheme();

  return (
    <SecurityProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
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
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />

                <Route path="/upload" element={<Upload />} />
                <Route path="/documents" element={<EnhancedDocuments />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/document/:documentId" element={<DocumentViewer />} />

                <Route path="/knowledge" element={<KnowledgeGraph />} />
                <Route path="/investigation" element={<EnhancedInvestigativeWorkspace />} />
                <Route path="/entity-enrichment" element={<EntityEnrichment />} />
                <Route path="/spaces" element={<EnhancedProjectSpaces />} />
                <Route path="/lease-management" element={<LeaseManagement />} />
              </Routes>
            </Box>
          </Box>
        </Box>
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
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContextProvider>
        <AppContent />
      </ThemeContextProvider>
    </QueryClientProvider>
  );
}

export default App;