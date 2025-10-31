import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DocumentsIcon,
  Psychology as EntityIcon,
  Psychology as PsychologyIcon,
  Chat as ChatIcon,
  Folder as SpacesIcon,
  Security as SecurityIcon,
  Dashboard as BoardIcon,
  Public as UnifiedSearchIcon,
  Settings as SourceConfigIcon,
  Hub as HubIcon,
  AccountTree as WorkflowIcon,
  Science as LiteratureIcon,
  Email as ICSRIcon,
  RateReview as ICSRReviewIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

const menuItems = [
  {
    path: '/spaces',
    label: 'Project Spaces',
    icon: <SpacesIcon />,
    description: 'Organize by projects',
  },
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    description: 'Overview & insights',
  },
  // {
  //   path: '/unified-search',
  //   label: 'Unified Search',
  //   icon: <UnifiedSearchIcon />,
  //   description: 'Search across all sources',
  // },
  {
    path: '/documents',
    label: 'Document Library',
    icon: <DocumentsIcon />,
    description: 'Browse & search documents',
  },
  {
    path: '/chat',
    label: 'Document Chat',
    icon: <ChatIcon />,
    description: 'Chat with documents',
  },
  {
    path: '/knowledge-hub',
    label: 'Knowledge Hub',
    icon: <HubIcon />,
    description: 'Explore knowledge graph',
  },
  {
    path: '/investigations',
    label: 'Investigation Boards',
    icon: <BoardIcon />,
    description: 'Build & analyze entity networks',
  },
  {
    path: '/workflow-builder',
    label: 'Workflow Builder',
    icon: <WorkflowIcon />,
    description: 'Visual pipeline automation',
  },
  {
    path: '/entity-enrichment',
    label: 'Entity Enrichment',
    icon: <EntityIcon />,
    description: 'Web scraping & enrichment',
  },
  {
    path: '/source-configuration',
    label: 'Source Configuration',
    icon: <SourceConfigIcon />,
    description: 'Manage data sources',
  },
  {
    path: '/icsr-automation',
    label: 'ICSR Automation',
    icon: <ICSRIcon />,
    description: 'Email processing & ICSR validation',
  },
  {
    path: '/icsr-reviewer',
    label: 'ICSR Reviewer',
    icon: <ICSRReviewIcon />,
    description: 'Review & approve extracted ICSRs',
  },
  // {
  //   path: '/rl-dashboard',
  //   label: 'RL Dashboard',
  //   icon: <PsychologyIcon />,
  //   description: 'Reinforcement Learning Intelligence',
  // },
  {
    path: '/rl-intelligence',
    label: 'RL Intelligence',
    icon: <PsychologyIcon />,
    description: 'AI-Powered Adaptive Classification',
    badge: 'NEW',
  },
  {
    path: '/security',
    label: 'Security Dashboard',
    icon: <SecurityIcon />,
    description: 'Security & compliance',
  },
  {
    path: '/security-testing',
    label: 'Security Testing',
    icon: <SecurityIcon />,
    description: 'Test security features',
  },
];

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          bgcolor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: '16px',
            background: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
            padding: 1,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <img 
            src="/Nuvelogo.png" 
            alt="Nuve Logo" 
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'contain',
              borderRadius: '12px'
            }} 
          />
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5, fontFamily: 'Inter' }}>
          Nuve Platform
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'Inter' }}>
          Enterprise Document Intelligence
        </Typography>
        <Chip
          label="v1.0"
          size="small"
          color="primary"
          sx={{ mt: 1, fontSize: '0.75rem', fontFamily: 'Inter' }}
        />
      </Box>

      <Divider />

      {/* Navigation */}
      <List sx={{ px: 2, py: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  px: 2,
                  '&:hover': {
                    bgcolor: 'primary.50',
                  },
                  ...(isActive && {
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                    '& .MuiListItemText-secondary': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                  }),
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: isActive ? 'inherit' : 'text.secondary',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  secondary={item.description}
                  primaryTypographyProps={{
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.95rem',
                  }}
                  secondaryTypographyProps={{
                    fontSize: '0.8rem',
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      {/* User Profile */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              width: 40,
              height: 40,
              bgcolor: 'primary.main',
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            U
          </Avatar>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Demo User
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block' }}
            >
              Administrator
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Status Indicator */}
      <Box sx={{ p: 2, pt: 0 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1.5,
            borderRadius: 2,
            bgcolor: 'success.50',
            border: '1px solid',
            borderColor: 'success.200',
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: 'success.main',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%': {
                  opacity: 1,
                },
                '50%': {
                  opacity: 0.5,
                },
                '100%': {
                  opacity: 1,
                },
              },
            }}
          />
          <Typography variant="caption" color="success.dark" sx={{ fontWeight: 500 }}>
            All Systems Operational
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
}

export default Sidebar;