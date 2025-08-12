
import React, { useState } from "react";
import {
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Card,
  CardContent,
  Box,
  Avatar,
  useTheme,
  CssBaseline,
  createTheme,
  ThemeProvider,
  LinearProgress,
  Fade,
  Slide,
  IconButton,
  Tooltip,
  Badge
} from "@mui/material";
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import DescriptionIcon from '@mui/icons-material/Description';
import TableViewIcon from '@mui/icons-material/TableView';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import VisibilityIcon from '@mui/icons-material/Visibility';
import GetAppIcon from '@mui/icons-material/GetApp';
import axios from "axios";


const theme = createTheme({
  palette: {
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
    },
    secondary: {
      main: '#ec4899',
      light: '#f472b6',
      dark: '#db2777',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    success: {
      main: '#10b981',
      light: '#34d399',
    },
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
    },
    error: {
      main: '#ef4444',
      light: '#f87171',
    },
    grey: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h3: {
      fontWeight: 800,
      fontSize: '2.5rem',
      letterSpacing: '-0.025em',
      lineHeight: 1.2,
    },
    h4: {
      fontWeight: 700,
      fontSize: '2rem',
      letterSpacing: '-0.025em',
      lineHeight: 1.3,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
      letterSpacing: '-0.025em',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.05)',
    '0px 4px 6px -1px rgba(0, 0, 0, 0.1)',
    '0px 10px 15px -3px rgba(0, 0, 0, 0.1)',
    '0px 20px 25px -5px rgba(0, 0, 0, 0.1)',
    '0px 25px 50px -12px rgba(0, 0, 0, 0.25)',
    ...Array(19).fill('0px 25px 50px -12px rgba(0, 0, 0, 0.25)'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          padding: '10px 20px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(99, 102, 241, 0.4)',
            transform: 'translateY(-1px)',
          },
          transition: 'all 0.2s ease-in-out',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: '1px solid #e5e7eb',
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.05)',
          '&:hover': {
            boxShadow: '0px 10px 25px rgba(0, 0, 0, 0.1)',
            transform: 'translateY(-2px)',
          },
          transition: 'all 0.3s ease-in-out',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#f8fafc',
          fontWeight: 600,
          fontSize: '0.875rem',
          color: '#374151',
          borderBottom: '2px solid #e5e7eb',
        },
        body: {
          fontSize: '0.875rem',
          color: '#4b5563',
          borderBottom: '1px solid #f3f4f6',
        },
      },
    },
  },
});

export default function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showTable, setShowTable] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return setError("Please select a PDF file to upload.");
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    
    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 200);
    
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("http://192.168.200.63:8000/extract-invoice", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadProgress(100);
      setTimeout(() => {
        setData(res.data.data);
        setShowTable(true);
        setLoading(false);
      }, 500);
    } catch (err) {
      clearInterval(progressInterval);
      setError("Upload failed. Please try again.");
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
          zIndex: 0,
        }
      }}>
        {/* Header */}
        <Slide direction="down" in={true} timeout={800}>
          <Box sx={{ 
            position: 'relative',
            zIndex: 1,
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            py: 4, 
            px: 4, 
            mb: 4, 
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar sx={{ 
                bgcolor: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', 
                width: 56, 
                height: 56, 
                mr: 3,
                boxShadow: '0 8px 25px rgba(99, 102, 241, 0.3)'
              }}>
                <DescriptionIcon sx={{ fontSize: 28 }} />
              </Avatar>
              <Box>
                <Typography variant="h3" sx={{ 
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5
                }}>
                  Invoice Extractor
                </Typography>
                <Typography variant="body2" sx={{ color: 'grey.600' }}>
                  AI-powered invoice data extraction with beautiful visualization
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="View Documentation">
                <IconButton sx={{ color: 'grey.600' }}>
                  <VisibilityIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Download Sample">
                <IconButton sx={{ color: 'grey.600' }}>
                  <GetAppIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Slide>

        {/* Upload Card */}
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Fade in={true} timeout={1000}>
            <Card sx={{ 
              p: 4, 
              mb: 6, 
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)'
            }}>
              <CardContent sx={{ p: 0 }}>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 1, color: 'grey.800' }}>
                    Upload Invoice Document
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'grey.600' }}>
                    Select a PDF invoice to extract and analyze data automatically
                  </Typography>
                </Box>
                
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 3,
                  flexWrap: 'wrap',
                  '@media (max-width: 600px)': {
                    flexDirection: 'column',
                    alignItems: 'stretch'
                  }
                }}>
                  <input
                    type="file"
                    accept="application/pdf"
                    style={{ display: 'none' }}
                    id="upload-pdf"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="upload-pdf">
                    <Button 
                      variant="outlined" 
                      component="span" 
                      startIcon={<CloudUploadIcon />}
                      sx={{ 
                        minWidth: 140,
                        height: 48,
                        borderColor: 'primary.main',
                        color: 'primary.main',
                        '&:hover': {
                          borderColor: 'primary.dark',
                          backgroundColor: 'primary.50'
                        }
                      }}
                    >
                      Choose PDF
                    </Button>
                  </label>
                  
                  <Box sx={{ 
                    flex: 1, 
                    minWidth: 200,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2
                  }}>
                    {file && (
                      <Chip
                        icon={<DescriptionIcon />}
                        label={file.name}
                        variant="outlined"
                        sx={{ 
                          maxWidth: 300,
                          '& .MuiChip-label': {
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }
                        }}
                      />
                    )}
                    {!file && (
                      <Typography variant="body2" sx={{ color: 'grey.500', fontStyle: 'italic' }}>
                        No file selected
                      </Typography>
                    )}
                  </Box>
                  
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleUpload}
                    disabled={loading || !file}
                    startIcon={loading ? <TrendingUpIcon /> : <TableViewIcon />}
                    sx={{ 
                      minWidth: 160,
                      height: 48,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                      },
                      '&:disabled': {
                        background: 'grey.300'
                      }
                    }}
                  >
                    {loading ? "Processing..." : "Extract Data"}
                  </Button>
                </Box>
                
                {loading && (
                  <Box sx={{ mt: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" sx={{ color: 'grey.600', mr: 2 }}>
                        Processing invoice...
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'primary.main', fontWeight: 600 }}>
                        {Math.round(uploadProgress)}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={uploadProgress} 
                      sx={{ 
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                          borderRadius: 3
                        }
                      }}
                    />
                  </Box>
                )}
                
                {error && (
                  <Fade in={!!error}>
                    <Box sx={{ 
                      mt: 3, 
                      p: 2, 
                      backgroundColor: 'error.50', 
                      border: '1px solid',
                      borderColor: 'error.200',
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }}>
                      <ErrorIcon sx={{ color: 'error.main', fontSize: 20 }} />
                      <Typography color="error.main" variant="body2">
                        {error}
                      </Typography>
                    </Box>
                  </Fade>
                )}
              </CardContent>
            </Card>
          </Fade>

          {/* Data Table */}
          {data.length > 0 && (
            <Slide direction="up" in={showTable} timeout={800}>
              <Card sx={{ 
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
                overflow: 'hidden'
              }}>
                <Box sx={{ 
                  p: 3, 
                  background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ 
                        bgcolor: 'success.main', 
                        width: 40, 
                        height: 40,
                        boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
                      }}>
                        <TableViewIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" sx={{ color: 'grey.800', mb: 0.5 }}>
                          Extracted Invoice Data
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'grey.600' }}>
                          {data.length} items found and processed
                        </Typography>
                      </Box>
                    </Box>
                    <Badge badgeContent={data.length} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: '0.75rem' } }}>
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="Extraction Complete"
                        color="success"
                        variant="outlined"
                      />
                    </Badge>
                  </Box>
                </Box>
                
                <TableContainer sx={{ maxHeight: 600 }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Title</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell align="center">HSN Code</TableCell>
                        <TableCell align="center">GST Rate (%)</TableCell>
                        <TableCell align="center">Quantity</TableCell>
                        <TableCell align="right">Rate</TableCell>
                        <TableCell align="right">MRP</TableCell>
                        <TableCell align="center">Page #</TableCell>
                        <TableCell align="center">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.map((row, idx) => (
                        <TableRow 
                          key={idx} 
                          sx={{ 
                            '&:nth-of-type(odd)': { 
                              backgroundColor: 'rgba(248, 250, 252, 0.5)' 
                            },
                            '&:hover': { 
                              backgroundColor: 'rgba(99, 102, 241, 0.05)',
                              transform: 'scale(1.001)',
                              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
                            },
                            transition: 'all 0.2s ease-in-out',
                            cursor: 'pointer'
                          }}
                        >
                          <TableCell sx={{ fontWeight: 500 }}>
                            {row.title || 'N/A'}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={row.type || 'Unknown'} 
                              size="small" 
                              variant="outlined"
                              sx={{ fontSize: '0.75rem' }}
                            />
                          </TableCell>
                          <TableCell align="center" sx={{ fontFamily: 'monospace' }}>
                            {row.section_2_transaction_hsn || '-'}
                          </TableCell>
                          <TableCell align="center" sx={{ fontWeight: 500 }}>
                            {row.section_2_transaction_gst ? `${row.section_2_transaction_gst}%` : '-'}
                          </TableCell>
                          <TableCell align="center">
                            {row.section_2_transaction_qty || '-'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 500 }}>
                            {row.section_2_transaction_rate ? `₹${row.section_2_transaction_rate}` : '-'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600, color: 'primary.main' }}>
                            {row.section_2_transaction_mrp ? `₹${row.section_2_transaction_mrp}` : '-'}
                          </TableCell>
                          <TableCell align="center">
                            <Chip 
                              label={row.page_number || '1'} 
                              size="small" 
                              color="primary" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              icon={
                                row.status === "approved" ? <CheckCircleIcon /> : 
                                row.status === "reviewing" ? <CloudUploadIcon /> : 
                                <ErrorIcon />
                              }
                              label={row.status || 'pending'}
                              color={
                                row.status === "reviewing" ? "warning" :
                                row.status === "approved" ? "success" :
                                "error"
                              }
                              size="small"
                              sx={{ 
                                fontWeight: 500,
                                '& .MuiChip-icon': { fontSize: '1rem' }
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Card>
            </Slide>
          )}
        </Container>

        {/* Footer */}
        <Box sx={{ 
          position: 'relative',
          zIndex: 1,
          textAlign: 'center', 
          py: 6, 
          mt: 6,
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderTop: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', mb: 1 }}>
            &copy; {new Date().getFullYear()} Invoice Extractor
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            Crafted with ❤️ using React, Material-UI & Figma-inspired design
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
