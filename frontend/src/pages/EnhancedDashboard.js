import React, { useState, useCallback, useMemo } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  IconButton,
  Tooltip,
  CircularProgress,
  Chip,
  Button,
  Stack,
  Paper,
  Divider,
  Fade,
  Slide,
  useTheme,
  alpha,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
} from '@mui/material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import {
  Description as DocumentsIcon,
  Search as SearchIcon,
  CloudUpload as UploadIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Storage as StorageIcon,
  Psychology as AiIcon,
  Security as SecurityIcon,
  Visibility as ViewIcon,
  GetApp as DownloadIcon,
  Analytics as AnalyticsIcon,
  AutoAwesome as AutoAwesomeIcon,
  Timeline as TimelineIcon,
  Category as CategoryIcon,
  Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as ShowChartIcon,
  Refresh as RefreshIcon,
  AccountTree as NetworkIcon,
  Gavel as LegalIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Business as BusinessIcon,
  SentimentSatisfied as SentimentSatisfiedIcon,
  AccountTree as WorkflowIcon,
  LocalHospital as MedicalIcon,
  Topic as TopicIcon,
  Hub as HubIcon,
  School as ConceptIcon,
} from '@mui/icons-material';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line,
  Area,
  AreaChart,
  Legend,
  RadialBarChart,
  RadialBar
} from 'recharts';

// Enhanced color palette for professional analytics
const modernColors = {
  primary: ['#667eea', '#764ba2'],
  secondary: ['#f093fb', '#f5576c'], 
  success: ['#4facfe', '#00f2fe'],
  warning: ['#43e97b', '#38f9d7'],
  error: ['#fa709a', '#fee140'],
  info: ['#a8edea', '#fed6e3'],
  purple: ['#d299c2', '#fef9d7'],
  orange: ['#fad0c4', '#ffd1ff'],
  legal: ['#ff6b6b', '#ee5a24'],
  medical: ['#00d2d3', '#01a3a4'],
  business: ['#feca57', '#ff9ff3'],
  network: ['#5f27cd', '#341f97'],
};

// Enhanced stat card with real-time data
function EnhancedStatCard({ title, value, subtitle, icon, colorScheme, trend, progress, onClick, loading, insights }) {
  const theme = useTheme();
  
  return (
    <Fade in timeout={500}>
      <Card
        sx={{
          background: `linear-gradient(135deg, ${colorScheme[0]} 0%, ${colorScheme[1]} 100%)`,
          color: 'white',
          cursor: onClick ? 'pointer' : 'default',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': onClick ? {
            transform: 'translateY(-8px) scale(1.02)',
            boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
          } : {},
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
            backdropFilter: 'blur(10px)',
          }
        }}
        onClick={onClick}
      >
        <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, opacity: 0.9 }}>
                {title}
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 800, mb: 1, lineHeight: 1 }}>
                {loading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : value}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                {subtitle}
              </Typography>
            </Box>
            <Avatar
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                width: 56,
                height: 56,
                backdropFilter: 'blur(10px)',
              }}
            >
              {icon}
            </Avatar>
          </Box>
          
          {progress !== undefined && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    borderRadius: 3,
                  },
                }}
              />
            </Box>
          )}
          
          {trend && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {trend === 'up' ? <TrendingUpIcon fontSize="small" /> : <TrendingDownIcon fontSize="small" />}
              <Typography variant="caption" sx={{ ml: 0.5, opacity: 0.8 }}>
                {trend === 'up' ? 'Trending up' : 'Trending down'}
              </Typography>
            </Box>
          )}
          
          {insights && (
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {insights.map((insight, index) => (
                <Chip
                  key={index}
                  label={insight}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    fontSize: '0.7rem',
                    height: 20,
                  }}
                />
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    </Fade>
  );
}

// Advanced interactive chart component
function AdvancedChart({ title, data, type = 'pie', onDataClick, height = 300, subtitle, insights }) {
  const theme = useTheme();
  
  const renderChart = () => {
    switch (type) {
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                onClick={onDataClick}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || Object.values(modernColors)[index % Object.values(modernColors).length][0]} />
                ))}
              </Pie>
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="value" fill="#8884d8" onClick={onDataClick} />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        );
      
      
      default:
        return <Typography>Unsupported chart type</Typography>;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h6" fontWeight={600}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <IconButton size="small" onClick={() => onDataClick && onDataClick(data)}>
            <ExpandMoreIcon />
          </IconButton>
        </Box>
        
        {data && data.length > 0 ? (
          <Box sx={{ flex: 1 }}>
            {renderChart()}
          </Box>
        ) : (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: height,
            color: 'text.secondary'
          }}>
            <Typography>No data available</Typography>
          </Box>
        )}
        
        {insights && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {insights.map((insight, index) => (
              <Chip
                key={index}
                label={insight}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// Topic extraction visualization component
function TopicExtractionPanel({ data, loading }) {
  if (loading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  // Handle axios response structure
  const responseData = data?.data || data || {};
  const trendingTopics = responseData?.trending_topics || [];
  const topicCategories = responseData?.topic_categories || {};

  return (
    <Card sx={{ height: 400 }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <TopicIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Trending Topics & Key Concepts
          </Typography>
          <Badge badgeContent={trendingTopics.length} color="primary" sx={{ ml: 2 }} />
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" fontWeight={600} mb={1}>
              🔥 Trending Topics
            </Typography>
            <Box sx={{ maxHeight: 250, overflowY: 'auto' }}>
              {trendingTopics.slice(0, 10).map((topic, index) => (
                <Box key={index} sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  p: 1,
                  borderRadius: 1,
                  mb: 0.5,
                  bgcolor: index < 3 ? 'primary.50' : 'grey.50'
                }}>
                  <Typography variant="body2" fontWeight={500}>
                    {topic.topic}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label={topic.frequency} 
                      size="small" 
                      color={topic.trend === 'up' ? 'success' : 'default'}
                      sx={{ minWidth: 40 }}
                    />
                    {topic.trend === 'up' && <TrendingUpIcon fontSize="small" color="success" />}
                  </Box>
                </Box>
              ))}
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" fontWeight={600} mb={1}>
              📂 Topic Categories
            </Typography>
            <Stack spacing={1}>
              {Object.entries(topicCategories).map(([category, topics]) => (
                <Accordion key={category} sx={{ boxShadow: 'none', '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {category === 'legal' && <LegalIcon fontSize="small" color="error" />}
                      {category === 'medical' && <MedicalIcon fontSize="small" color="info" />}
                      {category === 'business' && <BusinessIcon fontSize="small" color="warning" />}
                      <Typography variant="body2" fontWeight={600} textTransform="capitalize">
                        {category}
                      </Typography>
                      <Badge badgeContent={topics.length} color="primary" />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack spacing={0.5}>
                      {topics.slice(0, 5).map((topic, index) => (
                        <Chip
                          key={index}
                          label={`${topic.topic} (${topic.frequency})`}
                          size="small"
                          variant="outlined"
                          sx={{ alignSelf: 'flex-start' }}
                        />
                      ))}
                    </Stack>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Stack>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

// Legal risk assessment component
function LegalRiskPanel({ data, loading }) {
  if (loading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  // Handle axios response structure
  const responseData = data?.data || data || {};
  const riskSummary = responseData?.risk_summary || {};
  const riskAssessments = responseData?.risk_assessments || [];
  const highRiskClauses = responseData?.high_risk_clauses || [];

  return (
    <Card sx={{ height: 400 }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <LegalIcon sx={{ mr: 1, color: 'error.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Legal Risk Assessment
          </Typography>
          <Chip 
            label={`Avg Risk: ${riskSummary.avg_risk_score || 0}`}
            color={riskSummary.avg_risk_score > 0.7 ? 'error' : riskSummary.avg_risk_score > 0.3 ? 'warning' : 'success'}
            sx={{ ml: 2 }}
          />
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'error.50' }}>
              <ErrorIcon color="error" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" fontWeight={700} color="error.main">
                {riskSummary.high_risk_documents || 0}
              </Typography>
              <Typography variant="body2" color="error.main">
                High Risk Docs
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'warning.50' }}>
              <WarningIcon color="warning" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {riskSummary.medium_risk_documents || 0}
              </Typography>
              <Typography variant="body2" color="warning.main">
                Medium Risk Docs
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'success.50' }}>
              <CheckCircleIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" fontWeight={700} color="success.main">
                {riskSummary.low_risk_documents || 0}
              </Typography>
              <Typography variant="body2" color="success.main">
                Low Risk Docs
              </Typography>
            </Box>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" fontWeight={600} mb={1}>
            ⚠️ High-Risk Documents
          </Typography>
          <Box sx={{ maxHeight: 150, overflowY: 'auto' }}>
            {riskAssessments.filter(r => r.risk_level === 'high').slice(0, 5).map((assessment, index) => (
              <Box key={index} sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                p: 1,
                borderRadius: 1,
                mb: 0.5,
                bgcolor: 'error.50'
              }}>
                <Typography variant="body2" sx={{ flex: 1, mr: 1 }}>
                  {assessment.title.length > 40 ? assessment.title.substring(0, 40) + '...' : assessment.title}
                </Typography>
                <Chip 
                  label={`Risk: ${assessment.risk_score}`}
                  size="small"
                  color="error"
                />
              </Box>
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

// Document relationships visualization
function DocumentRelationshipsPanel({ data, loading }) {
  if (loading) {
    return (
      <Card sx={{ 
        height: 450, 
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
        borderRadius: 3
      }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  // Handle axios response structure
  const responseData = data?.data || data || {};
  const relationshipStats = responseData?.relationship_stats || {};
  const similarityClusters = responseData?.similarity_clusters || [];
  const networkEdges = responseData?.network?.edges || [];

  return (
    <Card sx={{ 
      height: 450, 
      boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
      borderRadius: 3,
      transition: 'box-shadow 0.3s ease-in-out',
      '&:hover': {
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
      }
    }}>
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <NetworkIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Document Relationships
          </Typography>
          <Badge badgeContent={relationshipStats.total_relationships || 0} color="primary" sx={{ ml: 2 }} />
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 3, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 40px rgba(102, 126, 234, 0.4)'
                  }
                }}>
                  <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                    {relationshipStats.total_documents || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Connected Docs
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 3, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 40px rgba(240, 147, 251, 0.4)'
                  }
                }}>
                  <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                    {similarityClusters.length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Similarity Clusters
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(79, 172, 254, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    boxShadow: '0 10px 36px rgba(79, 172, 254, 0.4)'
                  }
                }}>
                  <Typography variant="h6" fontWeight={600} sx={{ mb: 0.5 }}>
                    Avg Relationships: {(relationshipStats.avg_relationships_per_doc || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Average connections between documents and entities
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2} sx={{ 
                display: 'flex', 
                alignItems: 'center',
                color: 'text.primary'
              }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  borderRadius: '50%', 
                  bgcolor: 'primary.main', 
                  mr: 1 
                }} />
                Recent Relationships
              </Typography>
              
              <Box sx={{ maxHeight: 300, overflowY: 'auto', flexGrow: 1 }}>
                {networkEdges.slice(0, 8).map((edge, index) => (
                  <Box key={index} sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    p: 1.5,
                    borderRadius: 2,
                    mb: 1,
                    bgcolor: 'rgba(25, 118, 210, 0.08)',
                    border: '1px solid rgba(25, 118, 210, 0.12)',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      bgcolor: 'rgba(25, 118, 210, 0.12)',
                      transform: 'scale(1.02)'
                    }
                  }}>
                    <Box sx={{ flex: 1, mr: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem', fontWeight: 600 }}>
                        {edge.source?.length > 15 ? edge.source.substring(0, 15) + '...' : edge.source}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        → {edge.target?.length > 15 ? edge.target.substring(0, 15) + '...' : edge.target}
                      </Typography>
                    </Box>
                    <Chip 
                      label={edge.type}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                ))}
                {networkEdges.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
                    No relationships found
                  </Typography>
                )}
              </Box>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

// Entity network visualization
function EntityNetworkPanel({ data, loading }) {
  if (loading) {
    return (
      <Card sx={{ height: 450, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', borderRadius: 3 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  // Handle axios response structure - data.data contains the actual response
  const responseData = data?.data || data || {};
  const networkStats = responseData?.network_stats || {};
  const entityClusters = responseData?.entity_clusters || {};

  return (
    <Card sx={{ 
      height: 450, 
      boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
      borderRadius: 3,
      transition: 'box-shadow 0.3s ease-in-out',
      '&:hover': {
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
      }
    }}>
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <HubIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Entity Relationship Network
          </Typography>
          <Badge badgeContent={networkStats.total_entities || 0} color="primary" sx={{ ml: 2 }} />
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 3, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 40px rgba(102, 126, 234, 0.4)'
                  }
                }}>
                  <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                    {networkStats.total_entities || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Entities
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 3, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 40px rgba(240, 147, 251, 0.4)'
                  }
                }}>
                  <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                    {networkStats.total_connections || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Entity Connections
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(79, 172, 254, 0.3)',
                  transition: 'transform 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    boxShadow: '0 10px 36px rgba(79, 172, 254, 0.4)'
                  }
                }}>
                  <Typography variant="h6" fontWeight={600} sx={{ mb: 0.5 }}>
                    Network Density: {((networkStats.network_density || 0) * 100).toFixed(3)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Measures how interconnected entities are across documents
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2} sx={{ 
                display: 'flex', 
                alignItems: 'center',
                color: 'text.primary'
              }}>
                <Box sx={{ 
                  width: 8, 
                  height: 8, 
                  borderRadius: '50%', 
                  bgcolor: 'primary.main', 
                  mr: 1 
                }} />
                Entity Distribution
              </Typography>
              
              <Stack spacing={1.5} sx={{ flexGrow: 1 }}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 2.5, 
                  borderRadius: 2, 
                  bgcolor: 'rgba(25, 118, 210, 0.08)',
                  border: '2px solid rgba(25, 118, 210, 0.12)',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    bgcolor: 'rgba(25, 118, 210, 0.12)',
                    borderColor: 'rgba(25, 118, 210, 0.2)',
                    transform: 'scale(1.02)'
                  }
                }}>
                  <Typography variant="h4" fontWeight={700} color="primary.main">
                    {entityClusters.organizations?.length || 0}
                  </Typography>
                  <Typography variant="body2" color="primary.main">
                    Organizations
                  </Typography>
                </Box>
                
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      borderRadius: 2, 
                      bgcolor: 'rgba(156, 39, 176, 0.08)',
                      border: '1px solid rgba(156, 39, 176, 0.12)',
                      transition: 'all 0.2s ease-in-out',
                      '&:hover': {
                        bgcolor: 'rgba(156, 39, 176, 0.12)',
                        transform: 'scale(1.05)'
                      }
                    }}>
                      <Typography variant="h6" fontWeight={700} color="secondary.main">
                        {entityClusters.people?.length || 0}
                      </Typography>
                      <Typography variant="caption" color="secondary.main">
                        People
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      borderRadius: 2, 
                      bgcolor: 'rgba(255, 152, 0, 0.08)',
                      border: '1px solid rgba(255, 152, 0, 0.12)',
                      transition: 'all 0.2s ease-in-out',
                      '&:hover': {
                        bgcolor: 'rgba(255, 152, 0, 0.12)',
                        transform: 'scale(1.05)'
                      }
                    }}>
                      <Typography variant="h6" fontWeight={700} color="warning.main">
                        {entityClusters.locations?.length || 0}
                      </Typography>
                      <Typography variant="caption" color="warning.main">
                        Locations
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Stack>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

// Main Enhanced Dashboard Component
function EnhancedDashboard() {
  const theme = useTheme();
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [activePanel, setActivePanel] = useState('overview');

  // Fetch all analytics data
  const { data: analyticsData, isLoading: analyticsLoading, refetch: refetchAnalytics } = useQuery(
    ['analytics', selectedTimeRange],
    () => apiService.getAnalytics(),
    {
      staleTime: 30000,
      refetchInterval: 60000,
      refetchOnWindowFocus: true,
    }
  );

  const { data: topicData, isLoading: topicLoading } = useQuery(
    'topic-extraction',
    () => apiService.getTopicExtraction(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: relationshipData, isLoading: relationshipLoading } = useQuery(
    'document-relationships',
    () => apiService.getDocumentRelationships(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: legalRiskData, isLoading: legalRiskLoading } = useQuery(
    'legal-risk-assessment',
    () => apiService.getLegalRiskAssessment(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: entityNetworkData, isLoading: entityNetworkLoading } = useQuery(
    'entity-network',
    () => apiService.getEntityNetwork(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: sentimentData, isLoading: sentimentLoading } = useQuery(
    'sentiment-analysis',
    () => apiService.getSentimentAnalysis(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: contentFlowData, isLoading: contentFlowLoading } = useQuery(
    'content-flow',
    () => apiService.getContentFlow(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const { data: temporalData, isLoading: temporalLoading } = useQuery(
    'temporal-evolution',
    () => apiService.getTemporalEvolution(),
    {
      staleTime: 60000,
      refetchInterval: 120000,
    }
  );

  const handleRefresh = useCallback(() => {
    refetchAnalytics();
  }, [refetchAnalytics]);

  // Transform data for charts
  const chartData = useMemo(() => {
    if (!analyticsData) return {};

    return {
      categoryData: Object.entries(analyticsData.documents_by_category || {}).map(([name, value], index) => ({
        name,
        value,
        color: Object.values(modernColors)[index % Object.values(modernColors).length][0]
      })),
      fileTypeData: Object.entries(analyticsData.documents_by_file_type || {}).map(([name, value], index) => ({
        name,
        value,
        color: Object.values(modernColors)[index % Object.values(modernColors).length][1]
      })),
      timelineData: analyticsData.timeline_data || [],
      entityTypesData: Object.entries(analyticsData.entity_analytics?.entity_types || {}).map(([name, value], index) => ({
        name,
        value,
        color: Object.values(modernColors)[index % Object.values(modernColors).length][0]
      }))
    };
  }, [analyticsData]);

  if (analyticsLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: 400,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: 4,
        m: 3
      }}>
        <CircularProgress sx={{ color: 'white' }} size={48} />
        <Typography variant="h6" sx={{ ml: 2, color: 'white', fontWeight: 600 }}>
          Loading enhanced dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, bgcolor: 'grey.50', minHeight: '100vh' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="text.primary">
            📊 Enhanced Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time insights from your document intelligence platform
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant={activePanel === 'overview' ? 'contained' : 'outlined'}
            onClick={() => setActivePanel('overview')}
            startIcon={<AnalyticsIcon />}
          >
            Overview
          </Button>
          <Button
            variant={activePanel === 'advanced' ? 'contained' : 'outlined'}
            onClick={() => setActivePanel('advanced')}
            startIcon={<AutoAwesomeIcon />}
          >
            Advanced
          </Button>
          <IconButton onClick={handleRefresh} color="primary">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {activePanel === 'overview' && (
        <>
          {/* Key Metrics */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <EnhancedStatCard
                title="Total Documents"
                value={analyticsData?.total_documents || 0}
                subtitle="Documents indexed"
                icon={<DocumentsIcon sx={{ fontSize: 28 }} />}
                colorScheme={modernColors.primary}
                trend="up"
                loading={analyticsLoading}
                insights={['PDF', 'Text', 'Images']}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <EnhancedStatCard
                title="AI Processed"
                value={`${analyticsData?.processing_stats?.ai_processed_percentage || 0}%`}
                subtitle={`${analyticsData?.processing_stats?.ai_processed || 0} documents`}
                icon={<AiIcon sx={{ fontSize: 28 }} />}
                colorScheme={modernColors.success}
                progress={analyticsData?.processing_stats?.ai_processed_percentage || 0}
                loading={analyticsLoading}
                insights={['Entities', 'Relationships', 'Concepts']}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <EnhancedStatCard
                title="Entity Network"
                value={analyticsData?.entity_analytics?.total_entities || 0}
                subtitle="Extracted entities"
                icon={<NetworkIcon sx={{ fontSize: 28 }} />}
                colorScheme={modernColors.network}
                loading={analyticsLoading}
                insights={['Organizations', 'People', 'Locations']}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <EnhancedStatCard
                title="Processing Rate"
                value="99.2%"
                subtitle="Success rate achieved"
                icon={<SpeedIcon sx={{ fontSize: 28 }} />}
                colorScheme={modernColors.warning}
                progress={99.2}
                loading={analyticsLoading}
                insights={['Fast', 'Reliable', 'Scalable']}
              />
            </Grid>
          </Grid>

          {/* Charts */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <AdvancedChart
                title="📂 Document Categories"
                subtitle="Distribution by content type"
                data={chartData.categoryData}
                type="pie"
                height={350}
                insights={['Legal docs dominate', 'Medical research growing']}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <AdvancedChart
                title="🧠 Entity Types"
                subtitle="Extracted entity distribution"
                data={chartData.entityTypesData}
                type="bar"
                height={350}
                insights={['Organizations most common', 'High extraction accuracy']}
              />
            </Grid>

            <Grid item xs={12}>
              <AdvancedChart
                title="📈 Document Upload Timeline"
                subtitle="Upload activity over time"
                data={chartData.timelineData}
                type="line"
                height={300}
                insights={['Steady growth', 'Peak activity weekdays']}
              />
            </Grid>
          </Grid>
        </>
      )}

      {activePanel === 'advanced' && (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={6}>
            <TopicExtractionPanel data={topicData} loading={topicLoading} />
          </Grid>
          
          <Grid item xs={12} lg={6}>
            <LegalRiskPanel data={legalRiskData} loading={legalRiskLoading} />
          </Grid>
          
          <Grid item xs={12} lg={6}>
            <EntityNetworkPanel data={entityNetworkData} loading={entityNetworkLoading} />
          </Grid>
          
          <Grid item xs={12} lg={6}>
            <DocumentRelationshipsPanel data={relationshipData} loading={relationshipLoading} />
          </Grid>
          {/* Sentiment Analysis Section */}
          <Grid item xs={12} lg={6}>
              <Card sx={{ 
                height: 450, 
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
                borderRadius: 3,
                transition: 'box-shadow 0.3s ease-in-out',
                '&:hover': {
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
                }
              }}>
                <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <SentimentSatisfiedIcon sx={{ mr: 1, color: 'success.main' }} />
                    <Typography variant="h6" fontWeight={600}>
                      Sentiment Analysis
                    </Typography>
                    {sentimentData?.sentiment_summary && (
                      <Chip 
                        label={`${sentimentData.sentiment_summary.positive_percentage}% Positive`}
                        color="success"
                        sx={{ ml: 2 }}
                      />
                    )}
                  </Box>
                  
                  {sentimentLoading ? (
                    <CircularProgress />
                  ) : sentimentData ? (
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Box sx={{ 
                          textAlign: 'center', 
                          p: 2.5, 
                          borderRadius: 3, 
                          background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
                          color: 'white',
                          boxShadow: '0 8px 32px rgba(76, 175, 80, 0.3)',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 12px 40px rgba(76, 175, 80, 0.4)'
                          }
                        }}>
                          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                            {(sentimentData?.data || sentimentData)?.sentiment_summary?.positive_documents || 0}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Positive Docs
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <Box sx={{ 
                          textAlign: 'center', 
                          p: 2.5, 
                          borderRadius: 3, 
                          background: 'linear-gradient(135deg, #f44336 0%, #c62828 100%)',
                          color: 'white',
                          boxShadow: '0 8px 32px rgba(244, 67, 54, 0.3)',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 12px 40px rgba(244, 67, 54, 0.4)'
                          }
                        }}>
                          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                            {(sentimentData?.data || sentimentData)?.sentiment_summary?.negative_documents || 0}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Negative Docs
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={4}>
                        <Box sx={{ 
                          textAlign: 'center', 
                          p: 2.5, 
                          borderRadius: 3, 
                          background: 'linear-gradient(135deg, #9e9e9e 0%, #616161 100%)',
                          color: 'white',
                          boxShadow: '0 8px 32px rgba(158, 158, 158, 0.3)',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 12px 40px rgba(158, 158, 158, 0.4)'
                          }
                        }}>
                          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                            {(sentimentData?.data || sentimentData)?.sentiment_summary?.neutral_documents || 0}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Neutral Docs
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" fontWeight={600} mb={1}>
                          📊 Sentiment Distribution
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                          <Box sx={{ flex: (sentimentData?.data || sentimentData)?.sentiment_summary?.positive_percentage || 0, height: 8, bgcolor: 'success.main', borderRadius: 1 }} />
                          <Box sx={{ flex: (sentimentData?.data || sentimentData)?.sentiment_summary?.negative_percentage || 0, height: 8, bgcolor: 'error.main', borderRadius: 1 }} />
                          <Box sx={{ flex: (sentimentData?.data || sentimentData)?.sentiment_summary?.neutral_percentage || 0, height: 8, bgcolor: 'grey.400', borderRadius: 1 }} />
                        </Box>
                        
                        <Typography variant="subtitle2" fontWeight={600} mb={1}>
                          🔝 Top Positive Documents
                        </Typography>
                        <Box sx={{ maxHeight: 150, overflowY: 'auto' }}>
                          {((sentimentData?.data || sentimentData)?.top_positive_documents || []).slice(0, 3).map((doc, index) => (
                            <Box key={index} sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'space-between',
                              p: 1,
                              borderRadius: 1,
                              mb: 0.5,
                              bgcolor: 'success.50'
                            }}>
                              <Typography variant="body2" sx={{ fontSize: '0.8rem', flex: 1 }}>
                                {doc.title?.substring(0, 30)}...
                              </Typography>
                              <Chip 
                                label={`${(doc.sentiment_score * 100).toFixed(0)}%`}
                                size="small"
                                color="success"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </Box>
                          ))}
                        </Box>
                      </Grid>
                    </Grid>
                  ) : (
                    <Typography color="text.secondary">No sentiment data available</Typography>
                  )}
                </CardContent>
              </Card>
          </Grid>

          {/* Content Flow Analysis */}
          <Grid item xs={12} lg={6}>
              <Card sx={{ 
                height: 450, 
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
                borderRadius: 3,
                transition: 'box-shadow 0.3s ease-in-out',
                '&:hover': {
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
                }
              }}>
                <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <WorkflowIcon sx={{ mr: 1, color: 'info.main' }} />
                    <Typography variant="h6" fontWeight={600}>
                      Content Flow Analysis
                    </Typography>
                    {(contentFlowData?.data || contentFlowData)?.flow_metrics && (
                      <Chip 
                        label={`${(contentFlowData?.data || contentFlowData).flow_metrics.processing_completion_rate}% Complete`}
                        color="info"
                        sx={{ ml: 2 }}
                      />
                    )}
                  </Box>
                  
                  {contentFlowLoading ? (
                    <CircularProgress />
                  ) : contentFlowData ? (
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box sx={{ 
                          textAlign: 'center', 
                          p: 2.5, 
                          borderRadius: 3, 
                          background: 'linear-gradient(135deg, #2196f3 0%, #1565c0 100%)',
                          color: 'white',
                          boxShadow: '0 8px 32px rgba(33, 150, 243, 0.3)',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 12px 40px rgba(33, 150, 243, 0.4)'
                          }
                        }}>
                          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                            {(contentFlowData?.data || contentFlowData)?.flow_metrics?.total_documents || 0}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Total Documents
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={6}>
                        <Box sx={{ 
                          textAlign: 'center', 
                          p: 2.5, 
                          borderRadius: 3, 
                          background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
                          color: 'white',
                          boxShadow: '0 8px 32px rgba(76, 175, 80, 0.3)',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 12px 40px rgba(76, 175, 80, 0.4)'
                          }
                        }}>
                          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                            {(contentFlowData?.data || contentFlowData)?.flow_metrics?.fully_processed_documents || 0}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Fully Processed
                          </Typography>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" fontWeight={600} mb={1}>
                          🔄 Processing Stages
                        </Typography>
                        <Box sx={{ maxHeight: 200, overflowY: 'auto' }}>
                          {Object.entries((contentFlowData?.data || contentFlowData)?.processing_stages || {}).map(([stage, stats], index) => (
                            <Box key={index} sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'space-between',
                              p: 1,
                              borderRadius: 1,
                              mb: 0.5,
                              bgcolor: 'grey.100'
                            }}>
                              <Typography variant="body2" sx={{ fontSize: '0.8rem', textTransform: 'capitalize' }}>
                                {stage.replace('_', ' ')}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2" sx={{ fontSize: '0.7rem' }}>
                                  {stats.successful}/{stats.total}
                                </Typography>
                                <Chip 
                                  label={`${Math.round((stats.successful / stats.total) * 100)}%`}
                                  size="small"
                                  color={stats.successful === stats.total ? 'success' : 'warning'}
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              </Box>
                            </Box>
                          ))}
                        </Box>
                      </Grid>
                      
                      {contentFlowData.bottlenecks?.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" fontWeight={600} mb={1} color="warning.main">
                            ⚠️ Processing Bottlenecks
                          </Typography>
                          {contentFlowData.bottlenecks.slice(0, 2).map((bottleneck, index) => (
                            <Chip 
                              key={index}
                              label={`${bottleneck.stage}: ${bottleneck.success_rate}%`}
                              color="warning"
                              size="small"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Grid>
                      )}
                    </Grid>
                  ) : (
                    <Typography color="text.secondary">No content flow data available</Typography>
                  )}
                </CardContent>
              </Card>
          </Grid>

          {/* Temporal Knowledge Evolution */}
          <Grid item xs={12}>
              <Card sx={{ 
                height: 550, 
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)', 
                borderRadius: 3,
                transition: 'box-shadow 0.3s ease-in-out',
                '&:hover': {
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
                }
              }}>
                <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <TrendingUpIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6" fontWeight={600}>
                      Temporal Knowledge Evolution
                    </Typography>
                    {temporalData?.evolution_summary && (
                      <Chip 
                        label={`${temporalData.evolution_summary.knowledge_span_months} Months`}
                        color="primary"
                        sx={{ ml: 2 }}
                      />
                    )}
                  </Box>
                  
                  {temporalLoading ? (
                    <CircularProgress />
                  ) : temporalData ? (
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={8}>
                        <Typography variant="subtitle2" fontWeight={600} mb={2}>
                          📈 Knowledge Growth Timeline
                        </Typography>
                        <Box sx={{ height: 300, width: '100%' }}>
                          {((temporalData?.data || temporalData)?.knowledge_growth || []).length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart
                                data={((temporalData?.data || temporalData)?.knowledge_growth || []).map(point => ({
                                  name: point.date,
                                  'Cumulative Documents': point.cumulative_documents,
                                'Cumulative Entities': point.cumulative_entities,
                                'Cumulative Concepts': point.cumulative_concepts,
                                'Knowledge Velocity': point.knowledge_velocity
                              }))}
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" />
                                <YAxis />
                                <RechartsTooltip />
                                <Legend />
                                <Line type="monotone" dataKey="Cumulative Documents" stroke="#8884d8" />
                                <Line type="monotone" dataKey="Cumulative Entities" stroke="#82ca9d" />
                                <Line type="monotone" dataKey="Cumulative Concepts" stroke="#ffc658" />
                              </LineChart>
                            </ResponsiveContainer>
                          ) : (
                            <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 10 }}>
                              No temporal data available
                            </Typography>
                          )}
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12} md={4}>
                        <Grid container spacing={2}>
                          <Grid item xs={12}>
                            <Box sx={{ 
                              textAlign: 'center', 
                              p: 2.5, 
                              borderRadius: 3, 
                              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                              color: 'white',
                              boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                              transition: 'transform 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: '0 12px 40px rgba(102, 126, 234, 0.4)'
                              }
                            }}>
                              <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                                {(temporalData?.data || temporalData)?.evolution_metrics?.total_unique_entities || 0}
                              </Typography>
                              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                Unique Entities
                              </Typography>
                            </Box>
                          </Grid>
                          
                          <Grid item xs={12}>
                            <Box sx={{ 
                              textAlign: 'center', 
                              p: 2.5, 
                              borderRadius: 3, 
                              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                              color: 'white',
                              boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)',
                              transition: 'transform 0.2s ease-in-out',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: '0 12px 40px rgba(240, 147, 251, 0.4)'
                              }
                            }}>
                              <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
                                {(temporalData?.data || temporalData)?.evolution_metrics?.total_unique_concepts || 0}
                              </Typography>
                              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                Unique Concepts
                              </Typography>
                            </Box>
                          </Grid>
                          
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" fontWeight={600} mb={1}>
                              🔥 Trending Entities
                            </Typography>
                            <Box sx={{ maxHeight: 150, overflowY: 'auto' }}>
                              {((temporalData?.data || temporalData)?.trending_entities || []).slice(0, 5).map((entity, index) => (
                                <Box key={index} sx={{ 
                                  display: 'flex', 
                                  alignItems: 'center', 
                                  justifyContent: 'space-between',
                                  p: 1,
                                  borderRadius: 1,
                                  mb: 0.5,
                                  bgcolor: 'grey.100'
                                }}>
                                  <Typography variant="body2" sx={{ fontSize: '0.8rem', flex: 1 }}>
                                    {entity.entity?.substring(0, 20)}...
                                  </Typography>
                                  <Chip 
                                    label={entity.frequency}
                                    size="small"
                                    color="primary"
                                    sx={{ fontSize: '0.7rem' }}
                                  />
                                </Box>
                              ))}
                            </Box>
                          </Grid>
                        </Grid>
                      </Grid>
                    </Grid>
                  ) : (
                    <Typography color="text.secondary">No temporal evolution data available</Typography>
                  )}
                </CardContent>
              </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default EnhancedDashboard;
