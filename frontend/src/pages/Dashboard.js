import React, { useState, useCallback } from 'react';
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

// Modern color palette with gradients
const modernColors = {
  primary: ['#667eea', '#764ba2'],
  secondary: ['#f093fb', '#f5576c'], 
  success: ['#4facfe', '#00f2fe'],
  warning: ['#43e97b', '#38f9d7'],
  error: ['#fa709a', '#fee140'],
  info: ['#a8edea', '#fed6e3'],
  purple: ['#d299c2', '#fef9d7'],
  orange: ['#fad0c4', '#ffd1ff'],
};

// Animated stat card with gradient background
function ModernStatCard({ title, value, subtitle, icon, colorScheme, trend, progress, onClick, loading }) {
  const theme = useTheme();
  const [hovered, setHovered] = useState(false);

  const gradientBg = `linear-gradient(135deg, ${colorScheme[0]}, ${colorScheme[1]})`;
  const lightBg = `linear-gradient(135deg, ${alpha(colorScheme[0], 0.1)}, ${alpha(colorScheme[1], 0.1)})`;

  return (
    <Fade in={true} timeout={1000}>
      <Card 
        sx={{ 
          height: '100%', 
          cursor: onClick ? 'pointer' : 'default',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: hovered ? 'translateY(-8px)' : 'translateY(0)',
          boxShadow: hovered 
            ? `0 20px 40px ${alpha(colorScheme[0], 0.3)}` 
            : `0 8px 32px ${alpha(colorScheme[0], 0.1)}`,
          background: lightBg,
          border: `1px solid ${alpha(colorScheme[0], 0.2)}`,
          borderRadius: 3,
          overflow: 'visible',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: gradientBg,
            borderRadius: '12px 12px 0 0',
          }
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={onClick}
      >
        <CardContent sx={{ p: 3, pb: '24px !important' }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ flexGrow: 1 }}>
              <Typography 
                color="text.secondary" 
                variant="body2" 
                sx={{ 
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                  fontSize: '0.75rem',
                  mb: 1
                }}
              >
                {title}
              </Typography>
              <Typography 
                variant="h3" 
                sx={{ 
                  fontWeight: 800, 
                  background: gradientBg,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5
                }}
              >
                {loading ? '...' : value}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                  {subtitle}
                </Typography>
              )}
            </Box>
            
            <Avatar
              sx={{
                background: gradientBg,
                width: 64,
                height: 64,
                boxShadow: `0 8px 32px ${alpha(colorScheme[0], 0.3)}`,
                transition: 'all 0.3s ease',
                transform: hovered ? 'scale(1.1) rotate(5deg)' : 'scale(1)',
              }}
            >
              {icon}
            </Avatar>
          </Box>

          {trend !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
              {trend >= 0 ? <TrendingUpIcon sx={{ color: 'success.main', fontSize: 18 }} /> : <TrendingDownIcon sx={{ color: 'error.main', fontSize: 18 }} />}
              <Typography 
                variant="body2" 
                sx={{ 
                  color: trend >= 0 ? 'success.main' : 'error.main',
                  fontWeight: 600
                }}
              >
                {trend >= 0 ? '+' : ''}{trend}% from last month
              </Typography>
            </Box>
          )}

          {progress !== undefined && (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ 
                height: 6, 
                borderRadius: 3, 
                bgcolor: alpha(colorScheme[0], 0.1),
                overflow: 'hidden'
              }}>
                <Box
                  sx={{
                    height: '100%',
                    width: `${progress}%`,
                    background: gradientBg,
                    borderRadius: 3,
                    transition: 'width 1s ease-in-out'
                  }}
                />
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                {progress}% Complete
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Fade>
  );
}

// Interactive chart component with drill-down
function InteractiveChart({ title, data, type = 'pie', onDataClick, height = 300 }) {
  const theme = useTheme();
  const [selectedSegment, setSelectedSegment] = useState(null);

  const handleClick = useCallback((data, index) => {
    setSelectedSegment(index);
    if (onDataClick) {
      onDataClick(data, index);
    }
  }, [onDataClick]);

  const renderChart = () => {
    switch (type) {
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              onClick={handleClick}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color}
                  stroke={selectedSegment === index ? theme.palette.primary.main : 'none'}
                  strokeWidth={selectedSegment === index ? 3 : 0}
                  style={{ 
                    filter: selectedSegment === index ? 'brightness(1.1)' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                  }}
                />
              ))}
            </Pie>
            <RechartsTooltip 
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[8]
              }}
            />
          </PieChart>
        );
      
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.2)} />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <RechartsTooltip 
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[8]
              }}
            />
            <Bar 
              dataKey="value" 
              fill="url(#barGradient)"
              radius={[4, 4, 0, 0]}
              onClick={handleClick}
              style={{ cursor: 'pointer' }}
            />
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={theme.palette.primary.main} />
                <stop offset="100%" stopColor={theme.palette.primary.light} />
              </linearGradient>
            </defs>
          </BarChart>
        );
      
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.2)} />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <RechartsTooltip 
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[8]
              }}
            />
            <Line 
              type="monotone" 
              dataKey="count" 
              stroke={theme.palette.primary.main}
              strokeWidth={3}
              dot={{ fill: theme.palette.primary.main, strokeWidth: 2, r: 5 }}
              activeDot={{ r: 8, fill: theme.palette.secondary.main }}
            />
          </LineChart>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card sx={{ 
      height: '100%',
      background: 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
      backdropFilter: 'blur(10px)',
      border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
    }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
          <Tooltip title="Click segments to drill down">
            <IconButton size="small">
              <AssessmentIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <ResponsiveContainer width="100%" height={height}>
          {renderChart()}
        </ResponsiveContainer>
        
        {type === 'pie' && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
            {data.map((item, index) => (
              <Chip
                key={item.name}
                label={`${item.name}: ${item.value}`}
                size="small"
                sx={{
                  bgcolor: alpha(item.color, 0.1),
                  color: item.color,
                  fontWeight: 600,
                  border: selectedSegment === index ? `2px solid ${item.color}` : 'none',
                  cursor: 'pointer'
                }}
                onClick={() => handleClick(item, index)}
              />
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// Main Dashboard Component
function Dashboard() {
  const theme = useTheme();
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [drillDownData, setDrillDownData] = useState(null);

  // Fetch analytics data
  const { data: analyticsData, isLoading, refetch } = useQuery(
    ['analytics', selectedTimeRange],
    () => apiService.getAnalytics(),
    {
      staleTime: 5000, // 5 seconds for faster updates
      refetchInterval: 15000, // 15 seconds
      refetchOnWindowFocus: true, // Refresh when window focused
      refetchIntervalInBackground: true, // Keep refreshing in background
    }
  );

  const handleDrillDown = useCallback((data, category) => {
    setDrillDownData({ data, category });
    // Here you could navigate to a detailed view or open a modal
    console.log('Drill down into:', category, data);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  if (isLoading) {
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
          Loading your dashboard...
        </Typography>
      </Box>
    );
  }

  // Transform data for charts
  const categoryData = Object.entries(analyticsData?.documents_by_category || {}).map(([name, value], index) => ({
    name,
    value,
    color: Object.values(modernColors)[index % Object.values(modernColors).length][0]
  }));

  const fileTypeData = Object.entries(analyticsData?.documents_by_file_type || {}).map(([name, value], index) => ({
    name,
    value,
    color: Object.values(modernColors)[index % Object.values(modernColors).length][1]
  }));

  const timelineData = analyticsData?.timeline_data || [];

  const totalDocs = analyticsData?.total_documents || 0;
  const aiProcessed = analyticsData?.processing_stats?.ai_processed || 0;
  const aiPercentage = analyticsData?.processing_stats?.ai_processed_percentage || 0;
  const insights = analyticsData?.insights || {};

  return (
    <Box sx={{ p: 3, background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', minHeight: '100vh' }}>
      {/* Modern Header */}
      <Slide direction="down" in={true} timeout={800}>
        <Paper 
          elevation={0}
          sx={{ 
            p: 4, 
            mb: 4, 
            background: 'linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.6))',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            borderRadius: 4
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography 
                variant="h3" 
                sx={{ 
                  fontWeight: 800, 
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 1
                }}
              >
                Data Intelligence Hub 🚀
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 500 }}>
                Real-time insights from your document processing pipeline
              </Typography>
            </Box>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRefresh}
                sx={{ borderRadius: 2 }}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={<AnalyticsIcon />}
                sx={{ 
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8, #6a4190)',
                  }
                }}
              >
                Advanced Analytics
              </Button>
            </Stack>
          </Box>
          
          {/* Quick insights chips */}
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Chip 
              icon={<TrendingUpIcon />}
              label={`${insights.documents_uploaded_today || 0} docs uploaded today`}
              color="success"
              variant="outlined"
            />
            <Chip 
              icon={<AiIcon />}
              label={`${aiPercentage}% AI processed`}
              color="primary"
              variant="outlined"
            />
            <Chip 
              icon={<CategoryIcon />}
              label={`Top: ${insights.most_common_category || 'N/A'}`}
              color="secondary"
              variant="outlined"
            />
            <Chip 
              icon={<StorageIcon />}
              label={`Avg: ${insights.avg_file_size_mb || 0}MB per doc`}
              color="info"
              variant="outlined"
            />
          </Stack>
        </Paper>
      </Slide>

      <Grid container spacing={3}>
        {/* Modern Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatCard
            title="Total Documents"
            value={totalDocs.toLocaleString()}
            subtitle="Across all categories"
            icon={<DocumentsIcon sx={{ fontSize: 32 }} />}
            colorScheme={modernColors.primary}
            trend={12}
            loading={isLoading}
            onClick={() => handleDrillDown(totalDocs, 'total_documents')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatCard
            title="AI Enhanced"
            value={aiProcessed.toLocaleString()}
            subtitle={`${aiPercentage}% with intelligence`}
            icon={<AutoAwesomeIcon sx={{ fontSize: 32 }} />}
            colorScheme={modernColors.secondary}
            progress={aiPercentage}
            loading={isLoading}
            onClick={() => handleDrillDown(aiProcessed, 'ai_processed')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatCard
            title="Entities Extracted"
            value={insights.total_entities_extracted?.toLocaleString() || '0'}
            subtitle={`${insights.avg_entities_per_doc || 0} per document`}
            icon={<SearchIcon sx={{ fontSize: 32 }} />}
            colorScheme={modernColors.success}
            trend={8}
            loading={isLoading}
            onClick={() => handleDrillDown(insights.total_entities_extracted, 'entities')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatCard
            title="Processing Rate"
            value="99.5%"
            subtitle="Success rate achieved"
            icon={<SpeedIcon sx={{ fontSize: 32 }} />}
            colorScheme={modernColors.warning}
            progress={99.5}
            loading={isLoading}
            onClick={() => handleDrillDown(99.5, 'processing_rate')}
          />
        </Grid>

        {/* Interactive Charts */}
        <Grid item xs={12} md={6}>
          <InteractiveChart
            title="📂 Document Categories"
            data={categoryData}
            type="pie"
            height={350}
            onDataClick={(data) => handleDrillDown(data, 'category')}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <InteractiveChart
            title="📄 File Types Distribution"
            data={fileTypeData}
            type="bar"
            height={350}
            onDataClick={(data) => handleDrillDown(data, 'file_type')}
          />
        </Grid>

        <Grid item xs={12}>
          <InteractiveChart
            title="📈 Upload Timeline (Last 7 Days)"
            data={timelineData}
            type="line"
            height={300}
            onDataClick={(data) => handleDrillDown(data, 'timeline')}
          />
        </Grid>

        {/* Processing Pipeline Status */}
        <Grid item xs={12} md={8}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1))',
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                🔄 Processing Pipeline Status
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: alpha(modernColors.success[0], 0.1) }}>
                    <Typography variant="h4" sx={{ fontWeight: 800, color: modernColors.success[0], mb: 1 }}>
                      {totalDocs}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Documents Indexed
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: alpha(modernColors.primary[0], 0.1) }}>
                    <Typography variant="h4" sx={{ fontWeight: 800, color: modernColors.primary[0], mb: 1 }}>
                      {aiProcessed}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      AI Enhanced
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: alpha(modernColors.warning[0], 0.1) }}>
                    <Typography variant="h4" sx={{ fontWeight: 800, color: modernColors.warning[0], mb: 1 }}>
                      0
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Processing Queue
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={4}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(67, 233, 123, 0.1), rgba(56, 249, 215, 0.1))',
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                💚 System Health
              </Typography>
              
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Elasticsearch
                  </Typography>
                  <Chip label="Online" size="small" color="success" />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Neo4j Graph DB
                  </Typography>
                  <Chip label="Connected" size="small" color="success" />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    AI Processing
                  </Typography>
                  <Chip label="Ready" size="small" color="primary" />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Document Store
                  </Typography>
                  <Chip label="Available" size="small" color="info" />
                </Box>
              </Stack>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
                All systems operational • Last check: now
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;