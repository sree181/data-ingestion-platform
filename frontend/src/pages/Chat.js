import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Container,
  Paper,
  InputAdornment,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Chat as ChatIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import axios from 'axios';

function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const messagesEndRef = useRef(null);

  // Chat API configuration
  const chatApi = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
  });

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I\'m your document assistant. I can help you find information, summarize content, and answer questions about your documents. What would you like to know?',
        timestamp: new Date().toISOString(),
      }
    ]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatApi.post('/chat', {
        query: userMessage.content,
        conversation_id: conversationId,
        document_ids: [], // Chat with all documents
        user_id: 'user1'
      });

      const botMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        citations: response.data.citations || [],
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, botMessage]);

      if (response.data.conversation_id && !conversationId) {
        setConversationId(response.data.conversation_id);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again. Make sure all services are running properly.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setSnackbar({ 
        open: true, 
        message: 'Failed to send message. Please try again.', 
        severity: 'error' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome-new',
        role: 'assistant',
        content: 'Chat cleared! How can I help you with your documents today?',
        timestamp: new Date().toISOString(),
      }
    ]);
    setConversationId(null);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <ChatIcon />
          </Avatar>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              Document Chat 💬
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask questions about your documents and get intelligent responses
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton 
            onClick={clearChat} 
            color="primary" 
            title="Clear Chat"
            sx={{ 
              bgcolor: 'primary.light', 
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' }
            }}
          >
            <ClearIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Chat Container */}
      <Paper 
        elevation={3} 
        sx={{ 
          height: 'calc(100vh - 250px)', 
          display: 'flex', 
          flexDirection: 'column',
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        {/* Messages Area */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          bgcolor: '#f8f9fa'
        }}>
          <List sx={{ width: '100%', p: 0 }}>
            {messages.map((message) => (
              <ListItem 
                key={message.id} 
                sx={{ 
                  flexDirection: 'column', 
                  alignItems: 'stretch', 
                  px: 0, 
                  py: 1 
                }}
              >
                <Card 
                  sx={{ 
                    mb: 1, 
                    alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '80%',
                    bgcolor: message.role === 'user' ? 'primary.main' : 'white',
                    color: message.role === 'user' ? 'white' : 'inherit',
                    boxShadow: message.role === 'user' ? 3 : 1,
                  }}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                      {message.role === 'user' ? (
                        <PersonIcon sx={{ fontSize: 20, mt: 0.2 }} />
                      ) : (
                        <BotIcon sx={{ 
                          fontSize: 20, 
                          mt: 0.2, 
                          color: message.role === 'user' ? 'white' : 'primary.main' 
                        }} />
                      )}
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 0.5 }}>
                          {message.content}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            opacity: 0.7,
                            fontSize: '0.7rem'
                          }}
                        >
                          {formatTimestamp(message.timestamp)}
                        </Typography>
                      </Box>
                    </Box>

                    {message.citations && message.citations.length > 0 && (
                      <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                        <Typography 
                          variant="caption" 
                          color="text.secondary" 
                          display="block" 
                          sx={{ mb: 1 }}
                        >
                          📄 Sources:
                        </Typography>
                        {message.citations.map((citation, idx) => (
                          <Chip
                            key={idx}
                            label={citation.title}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              mr: 0.5, 
                              mb: 0.5,
                              cursor: 'pointer',
                              '&:hover': { bgcolor: 'primary.light', color: 'white' }
                            }}
                            onClick={() => navigate(`/document/${citation.document_id}`)}
                          />
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </ListItem>
            ))}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        {/* Input Area */}
        <Box sx={{ p: 2, bgcolor: 'white' }}>
          <TextField
            fullWidth
            placeholder="Ask me anything about your documents..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              }
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton 
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    color="primary"
                    sx={{
                      bgcolor: 'primary.main',
                      color: 'white',
                      '&:hover': { bgcolor: 'primary.dark' },
                      '&:disabled': { bgcolor: 'grey.300', color: 'grey.500' }
                    }}
                  >
                    {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            💡 Try asking: "Summarize the COVID-19 documents" or "What are the key findings about vaccination?"
          </Typography>
        </Box>
      </Paper>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default Chat;