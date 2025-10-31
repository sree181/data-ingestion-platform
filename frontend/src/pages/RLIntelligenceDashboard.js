import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  Chip,
  LinearProgress,
  Grid,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  AttachMoney as AttachMoneyIcon,
  School as SchoolIcon,
  CheckCircle as CheckCircleIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from '../services/api';

const RLIntelligenceDashboard = () => {
  const [rlEnabled, setRLEnabled] = useState(false);
  const [rlStatus, setRLStatus] = useState(null);
  const [rlMetrics, setRLMetrics] = useState(null);
  const [trainingHistory, setTrainingHistory] = useState(null);
  const [modelWeights, setModelWeights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch RL data on component mount
  useEffect(() => {
    fetchRLData();
  }, []);

  const fetchRLData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all RL data
      const [statusRes, metricsRes, historyRes, weightsRes] = await Promise.all([
        fetch('http://localhost:8013/api/v1/rl/status'),
        fetch('http://localhost:8013/api/v1/rl/metrics'),
        fetch('http://localhost:8013/api/v1/rl/training-history'),
        fetch('http://localhost:8013/api/v1/rl/model-weights')
      ]);

      if (statusRes.ok) setRLStatus(await statusRes.json());
      if (metricsRes.ok) setRLMetrics(await metricsRes.json());
      if (historyRes.ok) setTrainingHistory(await historyRes.json());
      if (weightsRes.ok) setModelWeights(await weightsRes.json());

      setLoading(false);
    } catch (err) {
      console.error('Error fetching RL data:', err);
      setError('Unable to connect to RL Intelligence Service. Please ensure the service is running on port 8013.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="h6">RL Intelligence Service Unavailable</Typography>
          <Typography variant="body2">{error}</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            To start the service: <code>docker-compose up rl-intelligence-service</code>
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <PsychologyIcon sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
          RL Intelligence Layer
        </Typography>
        <Typography variant="body1" color="text.secondary">
          AI-Powered Adaptive Classification Intelligence
        </Typography>
      </Box>

      {/* Info Alert */}
      <Alert severity="info" sx={{ mb: 3 }} icon={<SchoolIcon />}>
        <Typography variant="body2">
          <strong>What is RL Intelligence?</strong><br />
          Our Reinforcement Learning system continuously learns and optimizes classification performance,
          reducing costs and improving accuracy. Trained on 1,000 episodes with 97 real PubMed documents,
          it achieved a <strong>570% reward improvement</strong> and <strong>90% peak accuracy</strong>.
        </Typography>
      </Alert>

      {/* Status Card */}
      {rlStatus && (
        <Card sx={{ mb: 3, bgcolor: rlStatus.model_loaded ? 'success.light' : 'warning.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ mr: 2, fontSize: 40, color: rlStatus.model_loaded ? 'success.dark' : 'warning.dark' }} />
                <Box>
                  <Typography variant="h6">
                    RL System Status: {rlStatus.status.toUpperCase()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Model Loaded: {rlStatus.model_loaded ? 'Yes ✅' : 'No ⚠️'} | 
                    Training Episodes: {rlStatus.training_episodes} | 
                    Last Updated: {new Date(rlStatus.last_updated).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
              <Switch
                checked={rlEnabled}
                onChange={(e) => setRLEnabled(e.target.checked)}
                color="primary"
                disabled={!rlStatus.model_loaded}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics */}
      {rlStatus && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'primary.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'primary.dark' }} />
                  <Typography variant="h6">Accuracy</Typography>
                </Box>
                <Typography variant="h3" color="primary.dark">
                  {(rlStatus.peak_accuracy * 100).toFixed(0)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Peak RL-optimized accuracy
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'success.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AttachMoneyIcon sx={{ mr: 1, color: 'success.dark' }} />
                  <Typography variant="h6">Cost Savings</Typography>
                </Box>
                <Typography variant="h3" color="success.dark">
                  {rlStatus.cost_savings_percent.toFixed(0)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Intelligent model routing
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'warning.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <SpeedIcon sx={{ mr: 1, color: 'warning.dark' }} />
                  <Typography variant="h6">Speed Boost</Typography>
                </Box>
                <Typography variant="h3" color="warning.dark">
                  {rlStatus.speed_improvement.toFixed(1)}x
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Optimized decision paths
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'info.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <SchoolIcon sx={{ mr: 1, color: 'info.dark' }} />
                  <Typography variant="h6">Learning</Typography>
                </Box>
                <Typography variant="h3" color="info.dark">570%</Typography>
                <Typography variant="body2" color="text.secondary">
                  Reward improvement
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Training History Chart */}
      {trainingHistory && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TimelineIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Training History - Learning Curve</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Reward progression over {trainingHistory.total_episodes} training episodes. 
              The agent learned to optimize classification strategy, achieving a {trainingHistory.improvement_percent.toFixed(1)}% improvement.
            </Typography>
            
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trainingHistory.key_episodes}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="episode" label={{ value: 'Episode', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Reward', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="reward" stroke="#8884d8" strokeWidth={2} dot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap' }}>
              <Chip label={`Start: ${trainingHistory.start_reward.toFixed(2)}`} color="default" />
              <Chip label={`Peak: ${trainingHistory.peak_reward.toFixed(2)} (Episode ${trainingHistory.peak_episode})`} color="success" />
              <Chip label={`Final: ${trainingHistory.final_reward.toFixed(2)}`} color="primary" />
              <Chip label={`Improvement: ${trainingHistory.improvement_percent.toFixed(1)}%`} color="secondary" />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Model Weights */}
      {modelWeights && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🎯 Learned Model Weights & Thresholds
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The RL agent learned optimal weights and thresholds for each classification model through 1,000 training episodes.
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
                  <Typography variant="subtitle2" fontWeight="bold">Rule-Based Weight</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={95}
                      sx={{ flexGrow: 1, mr: 2, height: 10, borderRadius: 5 }}
                      color="success"
                    />
                    <Typography variant="body2" fontWeight="bold">0.95</Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    ↑ from 0.48 ({modelWeights.learned_weights.rule_based.improvement})
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="caption">
                    {modelWeights.learned_weights.rule_based.insight}
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'error.light' }}>
                  <Typography variant="subtitle2" fontWeight="bold">BERT Weight</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={0}
                      sx={{ flexGrow: 1, mr: 2, height: 10, borderRadius: 5 }}
                      color="error"
                    />
                    <Typography variant="body2" fontWeight="bold">-2.99</Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    ↓ from 0.30 ({modelWeights.learned_weights.bert.improvement})
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="caption">
                    {modelWeights.learned_weights.bert.insight}
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'info.light' }}>
                  <Typography variant="subtitle2" fontWeight="bold">LLM Weight</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={100}
                      sx={{ flexGrow: 1, mr: 2, height: 10, borderRadius: 5 }}
                      color="info"
                    />
                    <Typography variant="body2" fontWeight="bold">1.12</Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    ↑ from 0.27 ({modelWeights.learned_weights.llm.improvement})
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="caption">
                    {modelWeights.learned_weights.llm.insight}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>Key Insights:</Typography>
              <Box component="ul" sx={{ pl: 2 }}>
                {modelWeights.key_insights.map((insight, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{insight}</Typography>
                  </li>
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Domain Specialization */}
      {rlStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🏥 Domain Specialization
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              RL agent is trained on real medical literature across multiple domains
            </Typography>

            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {rlStatus.domains_trained.map((domain, idx) => (
                <Chip
                  key={idx}
                  label={domain}
                  color={idx === 0 ? 'primary' : idx === 1 ? 'secondary' : idx === 2 ? 'info' : 'default'}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Real-time Metrics */}
      {rlMetrics && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Current Performance Metrics
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Best performance achieved during training (Episode {rlMetrics.episode})
            </Typography>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Metric</strong></TableCell>
                    <TableCell align="right"><strong>Value</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Accuracy</TableCell>
                    <TableCell align="right">{(rlMetrics.accuracy * 100).toFixed(1)}%</TableCell>
                    <TableCell>Classification correctness</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Cost Efficiency</TableCell>
                    <TableCell align="right">{rlMetrics.cost_efficiency.toFixed(2)}</TableCell>
                    <TableCell>Minimize API costs</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Processing Speed</TableCell>
                    <TableCell align="right">{rlMetrics.processing_speed.toFixed(2)}s</TableCell>
                    <TableCell>Faster response times</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Domain Specialization</TableCell>
                    <TableCell align="right">{rlMetrics.domain_specialization.toFixed(2)}</TableCell>
                    <TableCell>Domain-aware decisions</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Total Reward</strong></TableCell>
                    <TableCell align="right"><strong>{rlMetrics.total_reward.toFixed(2)}</strong></TableCell>
                    <TableCell><strong>Multi-objective score</strong></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Feature Description */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            💡 What RL Intelligence Provides
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            When enabled, RL enhancement adds intelligent optimization to every classification:
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🎯 Intelligent Strategy Selection
                </Typography>
                <Typography variant="body2">
                  Analyzes document characteristics and recommends the optimal classification path
                  (Rule-only, Rule+BERT, or Full Ensemble) to maximize accuracy while minimizing cost.
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🏥 Domain-Aware Optimization
                </Typography>
                <Typography variant="body2">
                  Detects medical domain (hepatology, cardiology, etc.) and applies domain-specific
                  strategies learned from real medical literature.
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🔮 Performance Prediction
                </Typography>
                <Typography variant="body2">
                  Predicts classification accuracy, cost, and processing time before running,
                  providing transparency into AI decision-making.
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  📈 Continuous Learning
                </Typography>
                <Typography variant="body2">
                  Learns from every classification in production, updating the RL model with
                  real-world feedback and adapting to changing data patterns.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default RLIntelligenceDashboard;

