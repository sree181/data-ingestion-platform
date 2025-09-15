import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
} from '@mui/material';
import {
  AccountTree as GraphIcon,
} from '@mui/icons-material';

function Knowledge() {
  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>
        Knowledge Graph 🕸️
      </Typography>

      <Card>
        <CardContent sx={{ textAlign: 'center', py: 8 }}>
          <GraphIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 2 }}>
            Knowledge Graph Coming Soon
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Interactive knowledge graph visualization will show relationships
            between entities, documents, and concepts.
          </Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            This feature requires Neo4j integration and will display entity relationships
            extracted from your documents.
          </Alert>
          <Button variant="contained" disabled>
            Explore Graph
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Knowledge;