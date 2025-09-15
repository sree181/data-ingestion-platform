import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

// Mock data
const categoryData = [
  { name: 'Legal', value: 45 },
  { name: 'Medical', value: 35 },
  { name: 'Government', value: 15 },
  { name: 'Research', value: 5 },
];

const COLORS = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2'];

function Analytics() {
  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>
        Analytics Dashboard 📊
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Document Categories
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Processing Timeline
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={[]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#1976d2" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Analytics;