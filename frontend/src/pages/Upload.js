import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  Grid,
  Divider,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/html': ['.html'],
};

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

function FileUploadItem({ file, onRemove, onRetry }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'uploading':
        return <PendingIcon color="primary" />;
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <FileIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'uploading':
        return 'primary';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <ListItem
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        mb: 1,
        bgcolor: 'background.paper',
      }}
    >
      <ListItemIcon>
        {getStatusIcon(file.status)}
      </ListItemIcon>
      
      <ListItemText
        primary={file.name}
        secondary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {formatFileSize(file.size)}
            </Typography>
            <Chip
              label={file.status}
              size="small"
              color={getStatusColor(file.status)}
              variant="outlined"
            />
            {file.progress !== undefined && (
              <Box sx={{ flex: 1, ml: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={file.progress}
                  sx={{ height: 4, borderRadius: 2 }}
                />
              </Box>
            )}
          </Box>
        }
      />
      
      <ListItemSecondaryAction>
        {file.status === 'error' && (
          <IconButton
            edge="end"
            onClick={() => onRetry(file)}
            size="small"
            sx={{ mr: 1 }}
          >
            <RefreshIcon />
          </IconButton>
        )}
        <IconButton
          edge="end"
          onClick={() => onRemove(file.id)}
          size="small"
        >
          <DeleteIcon />
        </IconButton>
      </ListItemSecondaryAction>
    </ListItem>
  );
}

function Upload() {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    rejectedFiles.forEach((file) => {
      const error = file.errors[0];
      if (error.code === 'file-too-large') {
        toast.error(`${file.file.name} is too large. Maximum size is 50MB.`);
      } else if (error.code === 'file-invalid-type') {
        toast.error(`${file.file.name} is not a supported file type.`);
      } else {
        toast.error(`Error with ${file.file.name}: ${error.message}`);
      }
    });

    // Handle accepted files
    const newFiles = acceptedFiles.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      file: file,
      status: 'pending',
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newFiles]);
    
    if (newFiles.length > 0) {
      toast.success(`${newFiles.length} file(s) added for upload`);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  const removeFile = (fileId) => {
    setFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  const retryUpload = (file) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === file.id ? { ...f, status: 'pending', progress: 0 } : f
      )
    );
  };

  const simulateUpload = async (file) => {
    return new Promise((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          // 90% success rate for demo
          const success = Math.random() > 0.1;
          resolve(success);
        }
        
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, progress, status: progress === 100 ? 'processing' : 'uploading' }
              : f
          )
        );
      }, 200);
    });
  };

  const startUpload = async () => {
    const pendingFiles = files.filter((file) => file.status === 'pending');
    
    if (pendingFiles.length === 0) {
      toast.error('No files to upload');
      return;
    }

    setIsUploading(true);
    toast.success(`Starting upload of ${pendingFiles.length} files...`);

    let successCount = 0;
    let errorCount = 0;

    // Upload files one by one to avoid overwhelming the system
    for (const file of pendingFiles) {
      try {
        setFiles((prev) =>
          prev.map((f) => (f.id === file.id ? { ...f, status: 'uploading' } : f))
        );

        toast(`Uploading ${file.name}...`, { icon: '⬆️' });

        // Real upload using API - one file at a time
        const actualFiles = [file.file]; // Extract the actual File object
        const response = await apiService.uploadDocuments(actualFiles, (progress) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === file.id ? { ...f, progress } : f
            )
          );
        });
        
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, status: 'success', progress: 100 }
              : f
          )
        );

        successCount++;
        toast.success(`✅ ${file.name} uploaded successfully!`);
        
        // Small delay between uploads to prevent overwhelming the backend
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        console.error('Upload error:', error);
        errorCount++;
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'error', progress: 0 } : f
          )
        );
        toast.error(`❌ ${file.name}: ${error.message}`);
      }
    }

    setIsUploading(false);
    
    if (successCount > 0) {
      toast.success(`🎉 Upload completed! ${successCount} files uploaded successfully${errorCount > 0 ? `, ${errorCount} failed` : ''}`);
    } else {
      toast.error('All uploads failed. Please try again.');
    }
  };

  const clearAll = () => {
    setFiles([]);
    toast.success('All files cleared');
  };

  const getUploadStats = () => {
    const total = files.length;
    const uploaded = files.filter((f) => f.status === 'success').length;
    const failed = files.filter((f) => f.status === 'error').length;
    const pending = files.filter((f) => f.status === 'pending').length;
    const uploading = files.filter((f) => f.status === 'uploading').length;

    return { total, uploaded, failed, pending, uploading };
  };

  const stats = getUploadStats();

  return (
    <Box>
      {/* Upload Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Upload Documents 📁
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Drag and drop your documents or click to browse. 
          Supported formats: PDF, DOC, DOCX, TXT, HTML
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Upload Area */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              {/* Drag & Drop Zone */}
              <Paper
                {...getRootProps()}
                sx={{
                  p: 4,
                  textAlign: 'center',
                  border: '2px dashed',
                  borderColor: isDragActive ? 'primary.main' : 'divider',
                  bgcolor: isDragActive ? 'primary.50' : 'background.default',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  mb: 3,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'primary.50',
                  },
                }}
              >
                <input {...getInputProps()} />
                <UploadIcon
                  sx={{
                    fontSize: 64,
                    color: isDragActive ? 'primary.main' : 'text.secondary',
                    mb: 2,
                  }}
                />
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {isDragActive
                    ? 'Drop your files here'
                    : 'Drag & drop files here, or click to select'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Maximum file size: 50MB per file
                </Typography>
                <Button
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  Browse Files
                </Button>
              </Paper>

              {/* Upload Actions */}
              {files.length > 0 && (
                <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                  <Button
                    variant="contained"
                    onClick={startUpload}
                    disabled={isUploading || stats.pending === 0}
                    sx={{ flex: 1 }}
                  >
                    {isUploading ? 'Uploading...' : `Upload ${stats.pending} Files`}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={clearAll}
                    disabled={isUploading}
                  >
                    Clear All
                  </Button>
                </Box>
              )}

              {/* File List */}
              {files.length > 0 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Files ({files.length})
                  </Typography>
                  <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                    {files.map((file) => (
                      <FileUploadItem
                        key={file.id}
                        file={file}
                        onRemove={removeFile}
                        onRetry={retryUpload}
                      />
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Upload Info & Stats */}
        <Grid item xs={12} md={4}>
          {/* Upload Statistics */}
          {files.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Upload Statistics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Total Files:</Typography>
                    <Chip label={stats.total} size="small" />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Uploaded:</Typography>
                    <Chip label={stats.uploaded} size="small" color="success" />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Failed:</Typography>
                    <Chip label={stats.failed} size="small" color="error" />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>Pending:</Typography>
                    <Chip label={stats.pending} size="small" color="warning" />
                  </Box>
                  {stats.uploading > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography>Uploading:</Typography>
                      <Chip label={stats.uploading} size="small" color="primary" />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Upload Guidelines */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Upload Guidelines
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                For best results, ensure your documents are:
              </Alert>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="High Quality"
                    secondary="Clear text, good resolution"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Properly Named"
                    secondary="Descriptive filenames help with organization"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Text-Searchable"
                    secondary="OCR will be applied to image-based documents"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Supported Formats */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Supported Formats
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.values(ACCEPTED_FILE_TYPES).flat().map((ext) => (
                  <Chip
                    key={ext}
                    label={ext.toUpperCase()}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Maximum file size: 50MB per file
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Upload;