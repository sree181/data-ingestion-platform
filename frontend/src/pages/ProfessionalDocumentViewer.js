import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Button,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  FormControl,
  InputLabel,
  Fab,
  Drawer,
  AppBar,
  Toolbar,
  LinearProgress,
  Badge,
  ButtonGroup,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  LocalHospital as MedicalIcon,
  Science as ScienceIcon,
  Gavel as LegalIcon,
  CalendarToday as DateIcon,
  AttachMoney as MoneyIcon,
  Article as ClauseIcon,
  Description as DocumentIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Highlight as HighlightIcon,
  Note as NoteIcon,
  Share as ShareIcon,
  Print as PrintIcon,
  GetApp as DownloadIcon,
  Search as SearchIcon,
  NavigateNext as NavigateNextIcon,
  NavigateBefore as NavigateBeforeIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  List as TocIcon,
  MenuBook as MenuBookIcon,
  Assignment as AssignmentIcon,
  Comment as CommentIcon,
  Flag as FlagIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

// Professional annotation types for legal and medical professionals
const ANNOTATION_TYPES = {
  legal: {
    'key-precedent': { 
      label: 'Key Precedent', 
      color: '#ff6b6b', 
      icon: '⚖️',
      description: 'Important legal precedent or case law'
    },
    'supporting-evidence': { 
      label: 'Supporting Evidence', 
      color: '#4ecdc4', 
      icon: '📋',
      description: 'Evidence that supports the case'
    },
    'contradictory-evidence': { 
      label: 'Contradictory Evidence', 
      color: '#ffe66d', 
      icon: '⚠️',
      description: 'Evidence that contradicts the position'
    },
    'procedural-note': { 
      label: 'Procedural Note', 
      color: '#a8e6cf', 
      icon: '📝',
      description: 'Procedural or administrative note'
    },
    'follow-up-required': { 
      label: 'Follow-up Required', 
      color: '#ff8b94', 
      icon: '🔔',
      description: 'Requires further investigation or action'
    },
    'liability-concern': { 
      label: 'Liability Concern', 
      color: '#ffaaa5', 
      icon: '🚨',
      description: 'Potential liability issue'
    }
  },
  medical: {
    'adverse-event': { 
      label: 'Adverse Event', 
      color: '#ff6b6b', 
      icon: '⚕️',
      description: 'Reported adverse event or side effect'
    },
    'efficacy-data': { 
      label: 'Efficacy Data', 
      color: '#4ecdc4', 
      icon: '📊',
      description: 'Clinical efficacy or effectiveness data'
    },
    'dosage-info': { 
      label: 'Dosage Information', 
      color: '#ffe66d', 
      icon: '💊',
      description: 'Drug dosage or administration information'
    },
    'contraindication': { 
      label: 'Contraindication', 
      color: '#ff8b94', 
      icon: '🚫',
      description: 'Medical contraindication or warning'
    },
    'clinical-significance': { 
      label: 'Clinical Significance', 
      color: '#a8e6cf', 
      icon: '🔬',
      description: 'Clinically significant finding'
    },
    'safety-concern': { 
      label: 'Safety Concern', 
      color: '#ffaaa5', 
      icon: '⚠️',
      description: 'Patient safety concern'
    }
  }
};

// Smart section detection patterns
const SECTION_PATTERNS = {
  medical: [
    { pattern: /abstract/i, title: 'Abstract', type: 'abstract' },
    { pattern: /introduction/i, title: 'Introduction', type: 'introduction' },
    { pattern: /background/i, title: 'Background', type: 'background' },
    { pattern: /methods?/i, title: 'Methods', type: 'methods' },
    { pattern: /methodology/i, title: 'Methodology', type: 'methods' },
    { pattern: /results?/i, title: 'Results', type: 'results' },
    { pattern: /findings?/i, title: 'Findings', type: 'results' },
    { pattern: /discussion/i, title: 'Discussion', type: 'discussion' },
    { pattern: /conclusion/i, title: 'Conclusion', type: 'conclusion' },
    { pattern: /references?/i, title: 'References', type: 'references' },
    { pattern: /adverse events?/i, title: 'Adverse Events', type: 'adverse-events' },
    { pattern: /side effects?/i, title: 'Side Effects', type: 'side-effects' },
    { pattern: /clinical trial/i, title: 'Clinical Trial', type: 'clinical-trial' },
    { pattern: /safety/i, title: 'Safety', type: 'safety' },
    { pattern: /efficacy/i, title: 'Efficacy', type: 'efficacy' }
  ],
  legal: [
    { pattern: /parties/i, title: 'Parties', type: 'parties' },
    { pattern: /recitals/i, title: 'Recitals', type: 'recitals' },
    { pattern: /definitions?/i, title: 'Definitions', type: 'definitions' },
    { pattern: /terms and conditions/i, title: 'Terms and Conditions', type: 'terms' },
    { pattern: /obligations?/i, title: 'Obligations', type: 'obligations' },
    { pattern: /liability/i, title: 'Liability', type: 'liability' },
    { pattern: /indemnification/i, title: 'Indemnification', type: 'indemnification' },
    { pattern: /termination/i, title: 'Termination', type: 'termination' },
    { pattern: /confidentiality/i, title: 'Confidentiality', type: 'confidentiality' },
    { pattern: /intellectual property/i, title: 'Intellectual Property', type: 'ip' },
    { pattern: /governing law/i, title: 'Governing Law', type: 'governing-law' },
    { pattern: /dispute resolution/i, title: 'Dispute Resolution', type: 'disputes' },
    { pattern: /force majeure/i, title: 'Force Majeure', type: 'force-majeure' }
  ]
};

// Entity type icon mapping (enhanced)
const getEntityIcon = (entityType) => {
  const icons = {
    'PERSON': <PersonIcon />,
    'ORGANIZATION': <BusinessIcon />,
    'LOCATION': <LocationIcon />,
    'DRUG': <MedicalIcon />,
    'DISEASE': <MedicalIcon />,
    'TREATMENT': <MedicalIcon />,
    'REGULATION': <LegalIcon />,
    'DATE': <DateIcon />,
    'MONEY': <MoneyIcon />,
    'CONCEPT': <ScienceIcon />,
    'LEGAL_PARTY': <PersonIcon />,
    'LEGAL_DATE': <DateIcon />,
    'LEGAL_JURISDICTION': <LocationIcon />,
    'LEGAL_TERMINATION': <LegalIcon />,
    'LEGAL_NON_COMPETE': <LegalIcon />,
    'LEGAL_CONFIDENTIALITY': <DocumentIcon />,
    'LEGAL_IP': <ScienceIcon />,
    'LEGAL_LIABILITY': <LegalIcon />,
    'LEGAL_PAYMENT': <MoneyIcon />,
    'LEGAL_FORCE_MAJEURE': <LegalIcon />,
  };
  return icons[entityType] || <ScienceIcon />;
};

// Entity type color mapping (enhanced)
const getEntityColor = (entityType) => {
  const colors = {
    'PERSON': 'primary',
    'ORGANIZATION': 'secondary',
    'LOCATION': 'success',
    'DRUG': 'warning',
    'DISEASE': 'error',
    'TREATMENT': 'info',
    'REGULATION': 'default',
    'DATE': 'primary',
    'MONEY': 'secondary',
    'CONCEPT': 'default',
    'LEGAL_PARTY': 'primary',
    'LEGAL_DATE': 'primary',
    'LEGAL_JURISDICTION': 'success',
    'LEGAL_TERMINATION': 'error',
    'LEGAL_NON_COMPETE': 'warning',
    'LEGAL_CONFIDENTIALITY': 'info',
    'LEGAL_IP': 'secondary',
    'LEGAL_LIABILITY': 'error',
    'LEGAL_PAYMENT': 'secondary',
    'LEGAL_FORCE_MAJEURE': 'warning',
  };
  return colors[entityType] || 'default';
};

function ProfessionalDocumentViewer() {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const contentRef = useRef(null);
  
  // State management
  const [annotations, setAnnotations] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [selectedText, setSelectedText] = useState('');
  const [selectionRange, setSelectionRange] = useState(null);
  const [annotationDialog, setAnnotationDialog] = useState(false);
  const [currentAnnotationType, setCurrentAnnotationType] = useState('');
  const [annotationNote, setAnnotationNote] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState('');
  const [readingProgress, setReadingProgress] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  const [userType, setUserType] = useState('medical'); // 'legal' or 'medical'
  
  // Fetch document details
  const { data: document, isLoading, error } = useQuery(
    ['document', documentId],
    () => apiService.getDocument(documentId),
    {
      enabled: !!documentId,
      staleTime: 300000, // 5 minutes
    }
  );

  // Get pre-analyzed document structure from the document data (no separate API call needed!)
  const documentStructure = useMemo(() => {
    if (!document) return null;
    
    // Check if document already has pre-analyzed structure from ingestion
    if (document.document_structure) {
      return document.document_structure;
    }
    
    // Fallback: create basic structure from existing document data
    const pageCount = document.metadata?.page_count || 1;
    const wordCount = document.metadata?.word_count || 0;
    
    // Create basic page-based sections for legacy documents
    const basicSections = [];
    for (let i = 1; i <= Math.min(pageCount, 10); i++) { // Limit to 10 pages for performance
      basicSections.push({
        id: `page-${i}`,
        title: `Page ${i}`,
        section_type: 'page',
        start_position: ((i - 1) * Math.floor(wordCount / pageCount)),
        end_position: (i * Math.floor(wordCount / pageCount)),
        confidence: 0.9,
        word_count: Math.floor(wordCount / pageCount),
        key_points: [`Content from page ${i}`],
        page_number: i,
        color: '#f0f0f0'
      });
    }
    
    return {
      document_type: document.file_type === 'pdf' ? 'research_paper' : 'general_document',
      confidence: 0.85, // Fixed confidence value
      analysis_timestamp: new Date().toISOString(),
      total_pages: pageCount,
      total_words: wordCount,
      sections: basicSections,
      fallback_navigation: {
        type: 'page_based',
        total_pages: pageCount,
        sections: basicSections
      }
    };
  }, [document]);
  
  const structureLoading = false; // No loading since we use document data directly

  // Helper function to extract title from content lines
  const extractTitleFromLines = (lines) => {
    for (const line of lines) {
      const cleanLine = line.trim();
      if (cleanLine && cleanLine.length > 5 && cleanLine.length < 100) {
        // Check if it looks like a title
        if (!cleanLine.match(/^[A-Z\s]+$/) && cleanLine.match(/[A-Z]/)) {
          return cleanLine;
        }
      }
    }
    return null;
  };

  // Smart table of contents from LLM analysis
  const tableOfContents = useMemo(() => {
    if (documentStructure?.sections) {
      return documentStructure.sections.map(section => ({
        id: section.id,
        title: section.title,
        type: section.section_type,
        page: section.page_number || 1,
        wordCount: section.word_count,
        confidence: section.confidence,
        keyPoints: section.key_points || [],
        startPosition: section.start_position,
        endPosition: section.end_position,
        color: section.color || '#fafafa'
      }));
    }
    
    // Fallback to basic pattern matching if LLM analysis fails
    if (!document?.content) return [];
    
    const content = document.content;
    const sections = [];
    
    // Look for page breaks first (most reliable)
    const pageMatches = content.match(/=== PAGE (\d+) ===/g);
    if (pageMatches && pageMatches.length > 1) {
      const pages = content.split(/=== PAGE \d+ ===/);
      pages.forEach((pageContent, index) => {
        if (index > 0 && pageContent.trim()) { // Skip first empty split
          const lines = pageContent.trim().split('\n').slice(0, 5);
          const title = extractTitleFromLines(lines) || ('Page ' + index);
          
          sections.push({
            id: 'page-' + index,
            title: title,
            type: 'page',
            page: index,
            wordCount: pageContent.split(' ').length,
            confidence: 0.8,
            keyPoints: [],
            startPosition: 0, // Will be calculated when needed
            endPosition: pageContent.length,
            color: '#fafafa'
          });
        }
      });
    } else {
      // Pattern-based fallback
      const patterns = SECTION_PATTERNS[userType] || SECTION_PATTERNS.medical;
      const paragraphs = content.split('\n').filter(p => p.trim().length > 0);
      
      patterns.forEach(({ pattern, title, type }) => {
        paragraphs.forEach((paragraph, index) => {
          if (pattern.test(paragraph)) {
            sections.push({
              id: 'section-' + sections.length,
              title: title,
              type: type,
              page: Math.floor(index / 20) + 1, // Rough page estimation
              wordCount: Math.floor(Math.random() * 500) + 100,
              confidence: 0.6,
              keyPoints: [],
              startPosition: 0,
              endPosition: 0,
              color: '#fafafa'
            });
          }
        });
      });
    }
    
    return sections;
  }, [documentStructure, document?.content, userType]);

  // Enhanced content with section anchors
  const enhancedContent = useMemo(() => {
    if (!document?.content) return '';
    
    let content = document.highlighted_content || document.content;
    
    // Inject section anchors based on LLM analysis
    if (documentStructure?.sections) {
      // Sort sections by start position
      const sortedSections = [...documentStructure.sections].sort((a, b) => a.start_position - b.start_position);
      
      // Inject anchors from end to beginning to maintain positions
      for (let i = sortedSections.length - 1; i >= 0; i--) {
        const section = sortedSections[i];
        const sectionId = section.id;
        const sectionType = section.section_type;
        const sectionTitle = section.title;
        const confidencePercent = Math.round(section.confidence * 100);
        
        const anchor = '<div id="' + sectionId + '" class="section-anchor" style="position: relative; top: -80px; visibility: hidden;"></div>' +
        '<div class="section-header" style="' +
          'background: linear-gradient(135deg, #495057 0%, #343A40 100%);' +
          'color: white;' +
          'padding: 8px 16px;' +
          'margin: 20px 0 10px 0;' +
          'border-radius: 8px;' +
          'font-weight: 600;' +
          'font-size: 1.1rem;' +
          'display: flex;' +
          'align-items: center;' +
          'gap: 8px;' +
        '">' +
          '<span style="' +
            'background: rgba(255,255,255,0.2);' +
            'padding: 2px 8px;' +
            'border-radius: 12px;' +
            'font-size: 0.8rem;' +
            'font-weight: 500;' +
          '">' + sectionType + '</span>' +
          sectionTitle +
          '<span style="' +
            'margin-left: auto;' +
            'font-size: 0.8rem;' +
            'opacity: 0.8;' +
          '">' + confidencePercent + '% confidence</span>' +
        '</div>';
        
        // Insert anchor at the section start position
        const insertPosition = Math.max(0, section.start_position);
        content = content.slice(0, insertPosition) + anchor + content.slice(insertPosition);
      }
    } else {
      // Fallback: inject anchors at page breaks
      content = content.replace(/=== PAGE (\d+) ===/g, (match, pageNum) => {
        return '<div id="page-' + pageNum + '" class="section-anchor" style="position: relative; top: -80px; visibility: hidden;"></div>' +
        '<div class="section-header" style="' +
          'background: linear-gradient(135deg, #6C757D 0%, #495057 100%);' +
          'color: white;' +
          'padding: 8px 16px;' +
          'margin: 20px 0 10px 0;' +
          'border-radius: 8px;' +
          'font-weight: 600;' +
          'font-size: 1.1rem;' +
        '">📄 Page ' + pageNum + '</div>';
      });
    }
    
    // Apply legal risk redlining if available
    if (documentStructure?.fallback_navigation?.risk_analysis?.risk_highlights) {
      const riskHighlights = documentStructure.fallback_navigation.risk_analysis.risk_highlights;
      
      // Sort highlights by position (descending) to avoid position shifts during replacement
      const sortedHighlights = [...riskHighlights].sort((a, b) => b.start - a.start);
      
      sortedHighlights.forEach(highlight => {
        const before = content.substring(0, highlight.start);
        const highlightedText = content.substring(highlight.start, highlight.end);
        const after = content.substring(highlight.end);
        
        const riskLevelLabel = highlight.risk_level.replace('_', ' ').toUpperCase();
        const riskColor = highlight.risk_level === 'high_risk' ? '#ffcdd2' : 
                         highlight.risk_level === 'medium_risk' ? '#fff3e0' : '#e8f5e8';
        
        const highlightHtml = 
          '<span class="risk-highlight risk-' + highlight.risk_level + '" style="' +
            'background-color: ' + riskColor + ';' +
            'padding: 2px 6px;' +
            'border-radius: 4px;' +
            'border-left: 3px solid ' + (highlight.risk_level === 'high_risk' ? '#d32f2f' : 
                                       highlight.risk_level === 'medium_risk' ? '#f57c00' : '#2e7d32') + ';' +
            'position: relative;' +
            'font-weight: 500;' +
          '" title="' + riskLevelLabel + ' RISK: ' + highlight.text + '">' +
            highlightedText +
            ' <sup style="' +
              'font-size: 9px;' +
              'color: ' + (highlight.risk_level === 'high_risk' ? '#d32f2f' : 
                          highlight.risk_level === 'medium_risk' ? '#f57c00' : '#2e7d32') + ';' +
              'font-weight: bold;' +
              'background: white;' +
              'padding: 1px 3px;' +
              'border-radius: 2px;' +
              'margin-left: 2px;' +
            '">' + riskLevelLabel.charAt(0) + '</sup>' +
          '</span>';
        
        content = before + highlightHtml + after;
      });
    }
    
    return content;
  }, [document?.content, document?.highlighted_content, documentStructure]);

  // Handle text selection for annotations
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection.rangeCount > 0 && selection.toString().trim().length > 0) {
      const range = selection.getRangeAt(0);
      const selectedText = selection.toString().trim();
      
      if (selectedText.length > 5) { // Minimum selection length
        setSelectedText(selectedText);
        setSelectionRange(range.cloneRange());
      }
    }
  };

  // Add annotation
  const addAnnotation = () => {
    if (!selectedText || !currentAnnotationType) return;
    
    const newAnnotation = {
      id: 'annotation-' + Date.now(),
      text: selectedText,
      type: currentAnnotationType,
      note: annotationNote,
      timestamp: new Date().toISOString(),
      range: selectionRange,
      userType: userType
    };
    
    setAnnotations(prev => [...prev, newAnnotation]);
    setAnnotationDialog(false);
    setSelectedText('');
    setAnnotationNote('');
    setCurrentAnnotationType('');
    
    // Clear selection
    window.getSelection().removeAllRanges();
  };

  // Add bookmark
  const addBookmark = (section) => {
    const newBookmark = {
      id: 'bookmark-' + Date.now(),
      sectionId: section.id,
      title: section.title,
      timestamp: new Date().toISOString()
    };
    
    setBookmarks(prev => [...prev, newBookmark]);
  };

  // Navigate to section using real positions
  const navigateToSection = (sectionId) => {
    const section = tableOfContents.find(s => s.id === sectionId);
    if (!section) return;

    // Try to find the actual anchor element first
    try {
      const anchorElement = window.document.getElementById(sectionId);
      if (anchorElement) {
        anchorElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setActiveSection(sectionId);
        return;
      }
    } catch (error) {
      console.warn('Error finding anchor element:', error);
    }

    // Fallback: scroll to approximate position based on content
    if (section.startPosition && contentRef.current) {
      const contentElement = contentRef.current;
      const totalContentHeight = contentElement.scrollHeight;
      const documentLength = document?.content?.length || 1;
      const relativePosition = section.startPosition / documentLength;
      const targetScrollPosition = totalContentHeight * relativePosition;
      
      contentElement.scrollTo({
        top: targetScrollPosition,
        behavior: 'smooth'
      });
      
      setActiveSection(sectionId);
    }
  };

  // Handle scroll for reading progress
  useEffect(() => {
    const handleScroll = () => {
      if (contentRef.current) {
        const element = contentRef.current;
        const scrollTop = element.scrollTop;
        const scrollHeight = element.scrollHeight - element.clientHeight;
        const progress = (scrollTop / scrollHeight) * 100;
        setReadingProgress(Math.min(100, Math.max(0, progress)));
      }
    };

    const contentElement = contentRef.current;
    if (contentElement) {
      contentElement.addEventListener('scroll', handleScroll);
      return () => contentElement.removeEventListener('scroll', handleScroll);
    }
  }, []);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load document: {error.message}
      </Alert>
    );
  }

  if (!document) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        Document not found
      </Alert>
    );
  }

  const entities = document.openai_entities || [];
  const relationships = document.relationships || [];
  const legalClauses = document.legal_clauses || [];
  const insights = document.document_insights || {};
  const highlightedContent = document.highlighted_content || document.content;
  const availableAnnotationTypes = ANNOTATION_TYPES[userType] || ANNOTATION_TYPES.medical;

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }} data-version="aesthetic-v3.0" data-cache-bust="20250926">
      {/* Enhanced Professional Header */}
      <AppBar position="fixed" sx={{ 
        zIndex: 1300,
        background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        height: '56px' // Reduced height for better space utilization
      }}>
        <Toolbar variant="dense" sx={{ justifyContent: 'space-between', minHeight: '56px' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <IconButton 
              color="inherit" 
              onClick={() => navigate('/documents')}
              size="small"
              sx={{ 
                mr: 0.5,
                '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
              }}
            >
              <NavigateBeforeIcon fontSize="small" />
            </IconButton>
            
            <Button
              variant="text"
              onClick={() => navigate('/document/' + documentId)}
              sx={{ 
                mr: 1,
                color: 'rgba(255,255,255,0.8)',
                fontSize: '0.75rem',
                minWidth: 'auto',
                px: 1,
                py: 0.5,
                '&:hover': { 
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  color: 'white'
                }
              }}
              startIcon={<VisibilityIcon fontSize="small" />}
              size="small"
            >
              Standard
            </Button>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MenuBookIcon sx={{ fontSize: '1.1rem', color: 'rgba(255,255,255,0.9)' }} />
              <Typography variant="subtitle1" sx={{ 
                fontWeight: 600, 
                fontSize: '1rem',
                maxWidth: '300px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {document?.title || 'Loading...'}
              </Typography>
            </Box>
            
            <Chip 
              label={userType === 'legal' ? 'Legal' : 'Medical'} 
              size="small"
              sx={{ 
                backgroundColor: userType === 'legal' ? 'rgba(244, 67, 54, 0.2)' : 'rgba(76, 175, 80, 0.2)',
                color: 'white',
                fontWeight: 500,
                fontSize: '0.7rem',
                height: '24px'
              }}
            />
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* User Type Toggle */}
            <ButtonGroup size="small" variant="contained" sx={{ mr: 2 }}>
              <Button 
                onClick={() => setUserType('medical')}
                variant={userType === 'medical' ? 'contained' : 'outlined'}
                sx={{ 
                  backgroundColor: userType === 'medical' ? 'rgba(255,255,255,0.2)' : 'transparent',
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white',
                  '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
                }}
              >
                Medical
              </Button>
              <Button 
                onClick={() => setUserType('legal')}
                variant={userType === 'legal' ? 'contained' : 'outlined'}
                sx={{ 
                  backgroundColor: userType === 'legal' ? 'rgba(255,255,255,0.2)' : 'transparent',
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white',
                  '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
                }}
              >
                Legal
              </Button>
            </ButtonGroup>
            
            {/* Action Buttons */}
            <Tooltip title="Print Document">
              <IconButton color="inherit" size="small">
                <PrintIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download PDF">
              <IconButton color="inherit" size="small">
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share">
              <IconButton color="inherit" size="small">
                <ShareIcon />
              </IconButton>
            </Tooltip>
            
            {/* Reading Progress */}
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 2, minWidth: 100 }}>
              <Typography variant="caption" sx={{ mr: 1, color: 'rgba(255,255,255,0.8)' }}>
                {Math.round(readingProgress)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={readingProgress} 
                sx={{ 
                  width: 60,
                  height: 4,
                  borderRadius: 2,
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#4caf50',
                    borderRadius: 2
                  }
                }}
              />
            </Box>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Navigation Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: sidebarOpen ? 320 : 60,
          flexShrink: 0,
          transition: 'width 0.3s',
          '& .MuiDrawer-paper': {
            width: sidebarOpen ? 320 : 60,
            boxSizing: 'border-box',
            mt: '64px',
            height: 'calc(100vh - 64px)',
            background: 'linear-gradient(180deg, #F8F9FA 0%, #E9ECEF 100%)',
            borderRight: '1px solid #DEE2E6',
            transition: 'width 0.3s',
            overflow: 'hidden'
          },
        }}
      >
        {/* Sidebar Toggle */}
        <Box sx={{ p: 1, borderBottom: '1px solid #DEE2E6' }}>
          <IconButton 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            sx={{ width: '100%', justifyContent: sidebarOpen ? 'flex-end' : 'center' }}
          >
            {sidebarOpen ? <VisibilityOffIcon /> : <VisibilityIcon />}
          </IconButton>
        </Box>

        {sidebarOpen && (
          <Box sx={{ overflow: 'auto', height: '100%' }}>
            {/* Ultra-Modern Smart Table of Contents */}
            <Box sx={{ mb: 3 }}>
              {/* Optimized Compact Header */}
              <Box sx={{ 
                p: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: '16px 16px 0 0',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
                  <Box sx={{ 
                    p: 1.5, 
                    borderRadius: '12px', 
                    bgcolor: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)'
                  }}>
                    <TocIcon sx={{ fontSize: '1.2rem' }} />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" sx={{ 
                      fontWeight: 700,
                      fontSize: '1rem',
                      letterSpacing: '-0.01em',
                      mb: 0.5
                    }}>
                      Document Structure
                    </Typography>
                    <Typography variant="caption" sx={{ 
                      opacity: 0.85,
                      fontSize: '0.75rem',
                      fontWeight: 400
                    }}>
                      AI-powered navigation
                    </Typography>
                  </Box>
                </Box>
                
                {/* Compact Insights Grid */}
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1 }}>
                  <Box sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.15)', 
                    borderRadius: '8px', 
                    p: 1,
                    textAlign: 'center'
                  }}>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.65rem', display: 'block' }}>
                      Sections
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
                      {tableOfContents.length}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.15)', 
                    borderRadius: '8px', 
                    p: 1,
                    textAlign: 'center'
                  }}>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.65rem', display: 'block' }}>
                      Read Time
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
                      {Math.ceil((documentStructure?.total_words || 0) / 250)}m
                    </Typography>
                  </Box>
                  
                  <Box sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.15)', 
                    borderRadius: '8px', 
                    p: 1,
                    textAlign: 'center'
                  }}>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.65rem', display: 'block' }}>
                      AI Score
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
                      {Math.round((documentStructure?.analysis_confidence || 0) * 100)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.15)', 
                    borderRadius: '8px', 
                    p: 1,
                    textAlign: 'center'
                  }}>
                    <Typography variant="caption" sx={{ opacity: 0.8, fontSize: '0.65rem', display: 'block' }}>
                      Level
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
                      {documentStructure?.document_type === 'research_paper' ? 'High' : 
                       documentStructure?.document_type === 'legal_document' ? 'Expert' : 'Medium'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              
              {/* Ultra-Modern Section List */}
              <Box sx={{ 
                maxHeight: '500px',
                overflowY: 'auto',
                bgcolor: 'white',
                borderRadius: '0 0 20px 20px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                border: '1px solid #e2e8f0',
                borderTop: 'none',
                '&::-webkit-scrollbar': {
                  width: '6px',
                },
                '&::-webkit-scrollbar-track': {
                  background: '#f8fafc',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  borderRadius: '3px',
                },
              }}>
                {tableOfContents.map((section, index) => (
                  <Box 
                    key={section.id}
                    onClick={() => navigateToSection(section.id)}
                    sx={{ 
                      p: 2,
                      borderBottom: index < tableOfContents.length - 1 ? '1px solid #f1f5f9' : 'none',
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                      backgroundColor: activeSection === section.id ? '#f0f9ff' : 'transparent',
                      '&:hover': {
                        bgcolor: '#f8fafc',
                        transform: 'translateX(4px)',
                        boxShadow: '4px 0 12px rgba(59, 130, 246, 0.1)'
                      },
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        bottom: 0,
                        width: activeSection === section.id ? '4px' : '2px',
                        background: section.color && section.color.replace ? 
                          section.color : '#3b82f6',
                        transition: 'width 0.2s ease'
                      },
                      '&:hover:before': {
                        width: '4px'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      {/* Compact Section Number Badge */}
                      <Box sx={{ 
                        minWidth: '32px',
                        height: '32px',
                        borderRadius: '10px',
                        background: section.color && section.color.replace ? 
                          'linear-gradient(135deg, ' + section.color + ' 0%, ' + section.color.replace('f', 'c') + ' 100%)' : 
                          'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '0.8rem',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
                      }}>
                        {index + 1}
                      </Box>
                      
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        {/* Compact Section Title */}
                        <Typography variant="subtitle2" sx={{ 
                          fontWeight: 600,
                          color: '#1e293b',
                          fontSize: '0.9rem',
                          lineHeight: 1.3,
                          mb: 0.5,
                          letterSpacing: '-0.01em'
                        }}>
                          {section.title}
                        </Typography>
                        
                        {/* Compact Smart Badges */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip 
                            label={(section.section_type || 'section').replace('_', ' ')} 
                            size="small" 
                            sx={{ 
                              height: '20px',
                              fontSize: '0.65rem',
                              fontWeight: 600,
                              bgcolor: section.color && section.color.replace ? section.color.replace('#', '#').slice(0, 7) + '20' : '#e0f2fe',
                              color: section.color && section.color.replace ? section.color.replace('f', '8') : '#0277bd',
                              textTransform: 'capitalize',
                              borderRadius: '10px'
                            }} 
                          />
                          {section.confidence && section.confidence > 0.8 && (
                            <Chip 
                              label={Math.round(section.confidence * 100) + '% AI'} 
                              size="small" 
                              sx={{ 
                                height: '20px',
                                fontSize: '0.65rem',
                                fontWeight: 600,
                                bgcolor: section.confidence > 0.9 ? '#dcfce7' : '#fef3c7',
                                color: section.confidence > 0.9 ? '#16a34a' : '#d97706',
                                borderRadius: '10px'
                              }} 
                            />
                          )}
                          <Chip 
                            label={Math.ceil((section.word_count || 0) / 250) + 'm'} 
                            size="small" 
                            sx={{ 
                              height: '20px',
                              fontSize: '0.65rem',
                              fontWeight: 600,
                              bgcolor: '#f1f5f9',
                              color: '#64748b',
                              borderRadius: '10px'
                            }} 
                          />
                        </Box>
                        
                        {/* Compact Key Insights */}
                        {section.key_points && section.key_points.length > 0 && (
                          <Typography variant="caption" sx={{ 
                            color: '#64748b',
                            fontSize: '0.7rem',
                            fontWeight: 400,
                            display: 'block',
                            mt: 0.5,
                            lineHeight: 1.3,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            💡 {section.key_points[0]}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>

            {/* Bookmarks */}
            {bookmarks.length > 0 && (
              <Accordion sx={{ boxShadow: 'none', '&:before': { display: 'none' } }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BookmarkIcon />
                    <Typography variant="subtitle1" fontWeight={600}>
                      Bookmarks
                    </Typography>
                    <Badge badgeContent={bookmarks.length} color="secondary" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 0 }}>
                  <List dense>
                    {bookmarks.map((bookmark) => (
                      <ListItem key={bookmark.id} disablePadding>
                        <ListItemButton onClick={() => navigateToSection(bookmark.sectionId)}>
                          <ListItemIcon>
                            <StarIcon color="secondary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={bookmark.title}
                            secondary={new Date(bookmark.timestamp).toLocaleString()}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Annotations */}
            <Accordion sx={{ boxShadow: 'none', '&:before': { display: 'none' } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <NoteIcon />
                  <Typography variant="subtitle1" fontWeight={600}>
                    My Annotations
                  </Typography>
                  <Badge badgeContent={annotations.length} color="warning" />
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <List dense>
                  {annotations.map((annotation) => (
                    <ListItem key={annotation.id} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                      <Box sx={{ width: '100%', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                          <Typography variant="caption" sx={{ 
                            backgroundColor: availableAnnotationTypes[annotation.type]?.color || '#ccc',
                            color: 'white',
                            px: 1,
                            py: 0.25,
                            borderRadius: 1,
                            fontSize: '0.7rem',
                            fontWeight: 500
                          }}>
                            {availableAnnotationTypes[annotation.type]?.icon} {availableAnnotationTypes[annotation.type]?.label}
                          </Typography>
                        </Box>
                        <Typography variant="body2" sx={{ 
                          fontStyle: 'italic', 
                          backgroundColor: 'rgba(0,0,0,0.02)', 
                          p: 1, 
                          borderRadius: 1,
                          fontSize: '0.8rem',
                          lineHeight: 1.4
                        }}>
                          "{annotation.text.substring(0, 100)}..."
                        </Typography>
                        {annotation.note && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                            Note: {annotation.note}
                          </Typography>
                        )}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          </Box>
        )}
      </Drawer>

      {/* Enhanced Main Content Area */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          mt: '64px',
          height: 'calc(100vh - 64px)',
          overflow: 'auto',
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
          position: 'relative'
        }}
        ref={contentRef}
        data-version="compact-optimized-v4.0"
        data-cache-bust="20250926-3"
      >
        {/* Enhanced Floating Quick Actions */}
        <Fab
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000,
            background: selectedText ? 
              'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 
              'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
            '&:hover': {
              background: selectedText ? 
                'linear-gradient(135deg, #34d399 0%, #10b981 100%)' : 
                'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)',
              transform: 'scale(1.05)'
            },
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.15)',
            width: 60,
            height: 60
          }}
          onClick={() => setAnnotationDialog(true)}
          disabled={!selectedText}
        >
          {selectedText ? <HighlightIcon sx={{ color: 'white', fontSize: '1.5rem' }} /> : <NoteIcon sx={{ color: 'white', fontSize: '1.5rem' }} />}
        </Fab>
        
        <Grid container spacing={0} sx={{ height: '100%' }}>
          {/* Optimized Document Content */}
          <Grid item xs={12} md={8} sx={{ height: '100%', overflow: 'auto' }}>
            <Paper sx={{ 
              m: 1.5, // Reduced margin for better space utilization
              p: 3,    // Reduced padding
              minHeight: 'calc(100vh - 80px)', // Optimized height
              backgroundColor: 'white',
              borderRadius: 2, // Reduced border radius for cleaner look
              boxShadow: '0 2px 12px rgba(0,0,0,0.06)', // Subtler shadow
              position: 'relative'
            }}>
              {/* Compact Professional Header */}
              <Box sx={{ mb: 3, pb: 2, borderBottom: '1px solid #E9ECEF' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h5" sx={{ 
                    fontWeight: 600, 
                    color: '#343A40',
                    fontSize: '1.5rem',
                    lineHeight: 1.3,
                    flex: 1,
                    mr: 2
                  }}>
                    {document?.title || 'Loading...'}
                  </Typography>
                  
                  {/* Professional Status Indicators */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {document?.file_type && (
                      <Chip 
                        label={document.file_type.toUpperCase()}
                        size="small"
                        sx={{ 
                          backgroundColor: '#495057',
                          color: 'white',
                          fontWeight: 600,
                          fontSize: '0.7rem',
                          height: '24px'
                        }}
                      />
                    )}
                    {documentStructure?.document_type && (
                      <Chip 
                        label={documentStructure.document_type.replace('_', ' ').toUpperCase()}
                        size="small"
                        sx={{ 
                          backgroundColor: documentStructure.document_type === 'legal_document' ? '#dc3545' : 
                                         documentStructure.document_type === 'medical_report' ? '#28a745' : '#007bff',
                          color: 'white',
                          fontWeight: 600,
                          fontSize: '0.7rem',
                          height: '24px'
                        }}
                      />
                    )}
                  </Box>
                </Box>
                
                {/* Compact Metadata & Quick Stats */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {document?.metadata?.page_count && (
                      <Typography variant="caption" sx={{ color: '#6c757d', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <DocumentIcon sx={{ fontSize: '0.9rem' }} />
                        {document.metadata.page_count} pages
                      </Typography>
                    )}
                    {document?.metadata?.word_count && (
                      <Typography variant="caption" sx={{ color: '#6c757d', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <MenuBookIcon sx={{ fontSize: '0.9rem' }} />
                        {document.metadata.word_count.toLocaleString()} words
                      </Typography>
                    )}
                    {documentStructure?.analysis_confidence && (
                      <Typography variant="caption" sx={{ color: '#6c757d', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <ScienceIcon sx={{ fontSize: '0.9rem' }} />
                        AI: {Math.round(documentStructure.analysis_confidence * 100)}%
                      </Typography>
                    )}
                  </Box>
                  
                  {/* Quick Action Buttons */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Tooltip title="Add Bookmark">
                      <IconButton size="small" sx={{ color: '#495057' }}>
                        <BookmarkBorderIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Add Annotation">
                      <IconButton 
                        size="small" 
                        sx={{ color: selectedText ? '#007bff' : '#6c757d' }}
                        disabled={!selectedText}
                        onClick={() => setAnnotationDialog(true)}
                      >
                        <HighlightIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                
                {document.ai_summary && (
                  <Alert severity="info" sx={{ mb: 3, borderRadius: 2 }}>
                    <Typography variant="subtitle1" fontWeight="bold">AI Summary:</Typography>
                    <Typography variant="body2">{document.ai_summary}</Typography>
                  </Alert>
                )}

                {/* Professional Metadata */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {document.categories?.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  ))}
                  {insights.document_type && (
                    <Chip
                      label={'Type: ' + insights.document_type}
                      color="secondary"
                      size="small"
                    />
                  )}
                  {insights.sentiment && (
                    <Chip
                      label={'Sentiment: ' + insights.sentiment}
                      color={insights.sentiment === 'positive' ? 'success' : 
                             insights.sentiment === 'negative' ? 'error' : 'default'}
                      size="small"
                    />
                  )}
                </Box>
              </Box>

              {/* LLM Analysis Status */}
              {/* Document structure is now pre-analyzed during ingestion - no loading needed! */}

              {documentStructure && (
                <Alert severity={document.document_structure ? "success" : "info"} sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    {document.document_structure ? (
                      <>
                        <strong>AI Analysis Complete:</strong> Identified {documentStructure.sections?.length || 0} sections 
                        in this {documentStructure.document_type.replace('_', ' ')} 
                        ({Math.round(documentStructure.confidence * 100)}% confidence)
                      </>
                    ) : (
                      <>
                        <strong>Legacy Document:</strong> Using page-based navigation with {documentStructure.sections?.length || 0} pages 
                        for this {documentStructure.document_type.replace('_', ' ')}.
                        <em> New documents will have full AI analysis.</em>
                      </>
                    )}
                  </Typography>
                </Alert>
              )}

              {/* Enhanced Document Content with Section Anchors */}
              <Box
                onMouseUp={handleTextSelection}
                sx={{
                  '& .entity': {
                    padding: '2px 4px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      transform: 'scale(1.02)',
                      boxShadow: 1,
                    },
                  },
                  // Enhanced entity styling
                  '& .entity-person': { backgroundColor: '#e3f2fd', border: '1px solid #2196f3' },
                  '& .entity-organization': { backgroundColor: '#f3e5f5', border: '1px solid #9c27b0' },
                  '& .entity-location': { backgroundColor: '#e8f5e8', border: '1px solid #4caf50' },
                  '& .entity-drug': { backgroundColor: '#fff3e0', border: '1px solid #ff9800' },
                  '& .entity-disease': { backgroundColor: '#ffebee', border: '1px solid #f44336' },
                  '& .entity-treatment': { backgroundColor: '#e1f5fe', border: '1px solid #03a9f4' },
                  '& .entity-regulation': { backgroundColor: '#f5f5f5', border: '1px solid #757575' },
                  '& .entity-date': { backgroundColor: '#e8eaf6', border: '1px solid #3f51b5' },
                  '& .entity-money': { backgroundColor: '#f1f8e9', border: '1px solid #8bc34a' },
                  '& .entity-concept': { backgroundColor: '#fafafa', border: '1px solid #9e9e9e' },
                  // Legal clause highlighting
                  '& .entity-legal-party': { backgroundColor: '#e3f2fd', border: '2px solid #2196f3', fontWeight: 'bold' },
                  '& .entity-legal-date': { backgroundColor: '#e8eaf6', border: '2px solid #3f51b5', fontWeight: 'bold' },
                  '& .entity-legal-jurisdiction': { backgroundColor: '#e8f5e8', border: '2px solid #4caf50', fontWeight: 'bold' },
                  '& .entity-legal-termination': { backgroundColor: '#ffebee', border: '2px solid #f44336', fontWeight: 'bold' },
                  '& .entity-legal-non-compete': { backgroundColor: '#fff3e0', border: '2px solid #ff9800', fontWeight: 'bold' },
                  '& .entity-legal-confidentiality': { backgroundColor: '#e1f5fe', border: '2px solid #03a9f4', fontWeight: 'bold' },
                  '& .entity-legal-ip': { backgroundColor: '#f3e5f5', border: '2px solid #9c27b0', fontWeight: 'bold' },
                  '& .entity-legal-liability': { backgroundColor: '#ffebee', border: '2px solid #f44336', fontWeight: 'bold' },
                  '& .entity-legal-payment': { backgroundColor: '#f1f8e9', border: '2px solid #8bc34a', fontWeight: 'bold' },
                  '& .entity-legal-force-majeure': { backgroundColor: '#fff3e0', border: '2px solid #ff9800', fontWeight: 'bold' },
                  lineHeight: 1.8,
                  fontSize: '16px',
                  fontFamily: '"Inter", "Roboto", sans-serif',
                  color: '#2C3E50',
                  '& p': { marginBottom: '1.5rem' },
                  '& h1, & h2, & h3, & h4, & h5, & h6': { 
                    fontWeight: 600, 
                    marginTop: '2rem', 
                    marginBottom: '1rem',
                    color: '#34495E'
                  }
                }}
                dangerouslySetInnerHTML={{ __html: enhancedContent }}
              />
            </Paper>
          </Grid>

          {/* Ultra-Modern Professional Sidebar */}
          <Grid item xs={12} md={4} sx={{ height: '100%', overflow: 'auto' }}>
            <Box sx={{ p: 2, height: '100%' }}>
              {/* Compact Professional Tools */}
              <Box sx={{ 
                mb: 2,
                p: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: 3,
                color: 'white',
                boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
              }}>
                <Typography variant="h6" sx={{ 
                  fontWeight: 600,
                  mb: 1.5,
                  fontSize: '0.95rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <AssignmentIcon sx={{ fontSize: '1.1rem' }} />
                  Professional Tools
                </Typography>
                
                {/* Compact Grid Layout */}
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                  <Button 
                    startIcon={<HighlightIcon sx={{ fontSize: '0.9rem' }} />}
                    disabled={!selectedText}
                    onClick={() => setAnnotationDialog(true)}
                    variant="contained"
                    size="small"
                    sx={{ 
                      py: 1,
                      fontSize: '0.75rem',
                      background: selectedText ? 
                        'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderRadius: 2,
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.3)',
                        transform: 'translateY(-1px)'
                      },
                      '&:disabled': {
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'rgba(255, 255, 255, 0.5)'
                      }
                    }}
                  >
                    Annotate
                  </Button>
                  <Button 
                    startIcon={<BookmarkIcon sx={{ fontSize: '0.9rem' }} />} 
                    variant="contained"
                    size="small"
                    sx={{ 
                      py: 1,
                      fontSize: '0.75rem',
                      background: 'rgba(255, 255, 255, 0.15)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderRadius: 2,
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.3)',
                        transform: 'translateY(-1px)'
                      }
                    }}
                  >
                    Bookmark
                  </Button>
                  <Button 
                    startIcon={<SearchIcon sx={{ fontSize: '0.9rem' }} />} 
                    variant="contained"
                    size="small"
                    sx={{ 
                      py: 1,
                      fontSize: '0.75rem',
                      background: 'rgba(255, 255, 255, 0.15)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderRadius: 2,
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.3)',
                        transform: 'translateY(-1px)'
                      }
                    }}
                  >
                    Search
                  </Button>
                  <Button 
                    startIcon={<FlagIcon sx={{ fontSize: '0.9rem' }} />} 
                    variant="contained"
                    size="small"
                    sx={{ 
                      py: 1,
                      fontSize: '0.75rem',
                      background: 'rgba(255, 255, 255, 0.15)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      fontWeight: 600,
                      textTransform: 'none',
                      borderRadius: 2,
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.3)',
                        transform: 'translateY(-1px)'
                      }
                    }}
                  >
                    Flag Issue
                  </Button>
                </Box>
                
                {/* Compact Selected Text Indicator */}
                {selectedText && (
                  <Box sx={{ 
                    mt: 1.5,
                    p: 1.5, 
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 2,
                    border: '1px solid rgba(255, 255, 255, 0.2)'
                  }}>
                    <Typography variant="caption" sx={{ 
                      color: 'rgba(255, 255, 255, 0.8)', 
                      fontWeight: 500,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      fontSize: '0.65rem',
                      display: 'block',
                      mb: 0.5
                    }}>
                      Selected Text
                    </Typography>
                    <Typography variant="body2" sx={{ 
                      color: 'white', 
                      fontWeight: 400,
                      fontSize: '0.8rem',
                      lineHeight: 1.3
                    }}>
                      "{selectedText.substring(0, 50)}{selectedText.length > 50 ? '...' : ''}"
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {/* Compact Document Analytics */}
              <Box sx={{ 
                mb: 2,
                p: 2,
                background: 'white',
                borderRadius: 3,
                boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
                border: '1px solid #f1f5f9'
              }}>
                <Typography variant="h6" sx={{ 
                  fontWeight: 600,
                  mb: 1.5,
                  fontSize: '0.95rem',
                  color: '#1e293b',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  📊 Document Intelligence
                </Typography>
                
                {/* Compact Metrics */}
                <Box sx={{ display: 'grid', gap: 1.5 }}>
                  {/* Compact Reading Progress */}
                  <Box sx={{ 
                    p: 2,
                    background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
                    borderRadius: 2,
                    border: '1px solid #e2e8f0'
                  }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ 
                        color: '#374151', 
                        fontWeight: 600,
                        fontSize: '0.8rem'
                      }}>
                        📖 Reading Progress
                      </Typography>
                      <Typography variant="h6" sx={{ 
                        fontWeight: 700, 
                        color: '#059669',
                        fontSize: '1rem'
                      }}>
                        {Math.round(readingProgress)}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={readingProgress}
                      sx={{ 
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: '#e5e7eb',
                        '& .MuiLinearProgress-bar': {
                          background: 'linear-gradient(90deg, #10b981 0%, #059669 100%)',
                          borderRadius: 3
                        }
                      }}
                    />
                  </Box>
                  
                  {/* Compact Intelligence Metrics */}
                  {documentStructure && (
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Box sx={{ 
                        p: 1.5,
                        background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
                        borderRadius: 2,
                        border: '1px solid #93c5fd',
                        textAlign: 'center'
                      }}>
                        <Typography variant="caption" sx={{ 
                          color: '#1e40af', 
                          fontWeight: 600,
                          fontSize: '0.65rem',
                          display: 'block',
                          mb: 0.5
                        }}>
                          SECTIONS
                        </Typography>
                        <Typography variant="h6" sx={{ 
                          fontWeight: 700,
                          color: '#1e40af',
                          fontSize: '1.1rem',
                          lineHeight: 1
                        }}>
                          {documentStructure.sections?.length || 0}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ 
                        p: 1.5,
                        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                        borderRadius: 2,
                        border: '1px solid #fcd34d',
                        textAlign: 'center'
                      }}>
                        <Typography variant="caption" sx={{ 
                          color: '#92400e', 
                          fontWeight: 600,
                          fontSize: '0.65rem',
                          display: 'block',
                          mb: 0.5
                        }}>
                          READ TIME
                        </Typography>
                        <Typography variant="h6" sx={{ 
                          fontWeight: 700,
                          color: '#92400e',
                          fontSize: '1.1rem',
                          lineHeight: 1
                        }}>
                          {Math.ceil((documentStructure.total_words || 0) / 250)}m
                        </Typography>
                      </Box>
                    </Box>
                  )}
                  
                  {/* Compact Document Type */}
                  {documentStructure && (
                    <Box sx={{ 
                      p: 1.5,
                      background: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
                      borderRadius: 2,
                      border: '1px solid #a5b4fc',
                      textAlign: 'center'
                    }}>
                      <Typography variant="caption" sx={{ 
                        color: '#3730a3', 
                        fontWeight: 600,
                        fontSize: '0.65rem',
                        display: 'block',
                        mb: 0.5
                      }}>
                        DOCUMENT TYPE
                      </Typography>
                      <Typography variant="subtitle2" sx={{ 
                        fontWeight: 600,
                        color: '#3730a3',
                        fontSize: '0.85rem',
                        textTransform: 'capitalize',
                        lineHeight: 1
                      }}>
                        {documentStructure.document_type?.replace('_', ' ') || 'Unknown'}
                      </Typography>
                    </Box>
                  )}
                  
                  {/* Compact AI Confidence */}
                  {documentStructure && (
                    <Box sx={{ 
                      p: 2,
                      background: documentStructure.analysis_confidence > 0.8 ? 
                        'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)' : 
                        documentStructure.analysis_confidence > 0.6 ? 
                        'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)' : 
                        'linear-gradient(135deg, #fecaca 0%, #fca5a5 100%)',
                      borderRadius: 2,
                      border: documentStructure.analysis_confidence > 0.8 ? 
                        '1px solid #86efac' : 
                        documentStructure.analysis_confidence > 0.6 ? 
                        '1px solid #fcd34d' : 
                        '1px solid #f87171'
                    }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ 
                          color: documentStructure.analysis_confidence > 0.8 ? '#15803d' : 
                                 documentStructure.analysis_confidence > 0.6 ? '#92400e' : '#dc2626',
                          fontWeight: 600,
                          fontSize: '0.8rem'
                        }}>
                          🤖 AI Confidence
                        </Typography>
                        <Typography variant="h6" sx={{ 
                          fontWeight: 700,
                          color: documentStructure.analysis_confidence > 0.8 ? '#15803d' : 
                                 documentStructure.analysis_confidence > 0.6 ? '#92400e' : '#dc2626',
                          fontSize: '1rem'
                        }}>
                          {Math.round((documentStructure.analysis_confidence || 0) * 100)}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(documentStructure.analysis_confidence || 0) * 100}
                        sx={{ 
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255, 255, 255, 0.5)',
                          '& .MuiLinearProgress-bar': {
                            background: documentStructure.analysis_confidence > 0.8 ? 
                              'linear-gradient(90deg, #10b981 0%, #059669 100%)' : 
                              documentStructure.analysis_confidence > 0.6 ? 
                              'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)' : 
                              'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)',
                            borderRadius: 3
                          }
                        }}
                      />
                    </Box>
                  )}
                </Box>
              </Box>

              {/* Legal Risk Analysis */}
              {documentStructure?.fallback_navigation?.risk_analysis && (
                <Accordion defaultExpanded sx={{ mb: 2, borderRadius: 3, '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      ⚖️ Legal Risk Analysis
                      <Chip 
                        label={`Risk Score: ${Math.round(documentStructure.fallback_navigation.risk_analysis.overall_risk_score * 10) / 10}`}
                        color={documentStructure.fallback_navigation.risk_analysis.overall_risk_score >= 3 ? 'error' : 
                               documentStructure.fallback_navigation.risk_analysis.overall_risk_score >= 1.5 ? 'warning' : 'success'}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {/* High Risk Sections */}
                    {documentStructure.fallback_navigation.risk_analysis.high_risk_sections.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#d32f2f', fontWeight: 600, mb: 1 }}>
                          🔴 High Risk Sections ({documentStructure.fallback_navigation.risk_analysis.high_risk_sections.length})
                        </Typography>
                        {documentStructure.fallback_navigation.risk_analysis.high_risk_sections.map((section, index) => (
                          <Card key={index} sx={{ mb: 1, border: '1px solid #ffcdd2', backgroundColor: '#ffebee' }}>
                            <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                              <Typography variant="body2" fontWeight={600}>{section.section_title}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                Risk Score: {section.risk_score.toFixed(1)} | {section.risk_factors.length} risk factors
                              </Typography>
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    )}

                    {/* Medium Risk Sections */}
                    {documentStructure.fallback_navigation.risk_analysis.medium_risk_sections.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#f57c00', fontWeight: 600, mb: 1 }}>
                          🟡 Medium Risk Sections ({documentStructure.fallback_navigation.risk_analysis.medium_risk_sections.length})
                        </Typography>
                        {documentStructure.fallback_navigation.risk_analysis.medium_risk_sections.slice(0, 3).map((section, index) => (
                          <Card key={index} sx={{ mb: 1, border: '1px solid #fff3e0', backgroundColor: '#fffbf2' }}>
                            <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                              <Typography variant="body2" fontWeight={600}>{section.section_title}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                Risk Score: {section.risk_score.toFixed(1)}
                              </Typography>
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    )}

                    {/* Risk Highlights Summary */}
                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>📊 Risk Highlights</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {documentStructure.fallback_navigation.risk_analysis.risk_highlights.length} risk patterns identified in document
                      </Typography>
                      <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip label={`H: ${documentStructure.fallback_navigation.risk_analysis.high_risk_sections.length}`} color="error" size="small" />
                        <Chip label={`M: ${documentStructure.fallback_navigation.risk_analysis.medium_risk_sections.length}`} color="warning" size="small" />
                        <Chip label={`L: ${documentStructure.fallback_navigation.risk_analysis.low_risk_sections.length}`} color="success" size="small" />
                      </Box>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* AI-Extracted Entities */}
              <Accordion defaultExpanded sx={{ mb: 2, borderRadius: 3, '&:before': { display: 'none' } }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    AI-Extracted Entities ({entities.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {entities.slice(0, 10).map((entity, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {getEntityIcon(entity.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={entity.text}
                          secondary={
                            <Box>
                              <Chip
                                label={entity.type}
                                color={getEntityColor(entity.type)}
                                size="small"
                                sx={{ mr: 1, mb: 0.5 }}
                              />
                              {entity.confidence && (
                                <Typography variant="caption" color="text.secondary">
                                  {(entity.confidence * 100).toFixed(0)}% confidence
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                    {entities.length > 10 && (
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body2" color="text.secondary" align="center">
                              +{entities.length - 10} more entities
                            </Typography>
                          }
                        />
                      </ListItem>
                    )}
                  </List>
                </AccordionDetails>
              </Accordion>

              {/* Legal Clauses (if available) */}
              {legalClauses.length > 0 && (
                <Accordion sx={{ mb: 2, borderRadius: 3, '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Legal Clauses ({legalClauses.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {legalClauses.slice(0, 5).map((clause, index) => (
                        <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', px: 0 }}>
                          <Box sx={{ width: '100%', mb: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <ClauseIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                              <Typography variant="subtitle2" fontWeight="bold">
                                {clause.clause_name}
                              </Typography>
                              <Chip
                                label={clause.type}
                                color={getEntityColor(clause.type)}
                                size="small"
                                sx={{ ml: 1 }}
                              />
                            </Box>
                            <Typography variant="body2" sx={{ 
                              fontStyle: 'italic', 
                              backgroundColor: 'grey.50', 
                              p: 1, 
                              borderRadius: 1,
                              border: '1px solid',
                              borderColor: 'grey.200',
                              fontSize: '0.8rem'
                            }}>
                              "{clause.text.substring(0, 150)}..."
                            </Typography>
                          </Box>
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Document Insights */}
              {Object.keys(insights).length > 0 && (
                <Accordion sx={{ borderRadius: 3, '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Professional Insights</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      {insights.key_findings && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Key Findings:</Typography>
                          {insights.key_findings.slice(0, 3).map((finding, index) => (
                            <Typography key={index} variant="body2" sx={{ mb: 1, fontSize: '0.85rem' }}>
                              • {finding}
                            </Typography>
                          ))}
                        </Box>
                      )}

                      {insights.risk_factors && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Risk Factors:</Typography>
                          {insights.risk_factors.slice(0, 3).map((risk, index) => (
                            <Typography key={index} variant="body2" sx={{ mb: 1, fontSize: '0.85rem' }}>
                              • {risk}
                            </Typography>
                          ))}
                        </Box>
                      )}

                      {insights.main_themes && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>Main Themes:</Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {insights.main_themes.slice(0, 5).map((theme, index) => (
                              <Chip
                                key={index}
                                label={theme}
                                color="secondary"
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        </Box>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Floating Action Button for Quick Annotation */}
      {selectedText && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000 }}
          onClick={() => setAnnotationDialog(true)}
        >
          <HighlightIcon />
        </Fab>
      )}

      {/* Professional Annotation Dialog */}
      <Dialog 
        open={annotationDialog} 
        onClose={() => setAnnotationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, #495057 0%, #343A40 100%)',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <HighlightIcon />
          Add Professional Annotation
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>Selected Text:</Typography>
          <Paper sx={{ p: 2, mb: 3, backgroundColor: 'grey.50', fontStyle: 'italic' }}>
            "{selectedText}"
          </Paper>
          
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Annotation Type</InputLabel>
            <Select
              value={currentAnnotationType}
              onChange={(e) => setCurrentAnnotationType(e.target.value)}
              label="Annotation Type"
            >
              {Object.entries(availableAnnotationTypes).map(([key, type]) => (
                <MenuItem key={key} value={key}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span style={{ fontSize: '1.2rem' }}>{type.icon}</span>
                    <Box>
                      <Typography variant="body2" fontWeight={500}>{type.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Additional Notes (Optional)"
            value={annotationNote}
            onChange={(e) => setAnnotationNote(e.target.value)}
            placeholder="Add your professional notes or observations..."
          />
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setAnnotationDialog(false)}>Cancel</Button>
          <Button 
            onClick={addAnnotation}
            variant="contained"
            disabled={!currentAnnotationType}
            startIcon={<AddIcon />}
          >
            Add Annotation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ProfessionalDocumentViewer;
