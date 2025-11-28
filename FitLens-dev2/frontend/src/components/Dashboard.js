import React from 'react';
import {
  Typography,
  Card,
  CardContent,
  CardActionArea,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import VideocamIcon from '@mui/icons-material/Videocam';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

function Dashboard({ onModeSelect }) {
  const features = [
    'Upload Mode: Process front, side, and reference images',
    'Live Mode: Real-time pose detection with auto-capture',
    'Reference object calibration for accurate measurements',
    'Color-coded feedback (Red/Amber/Green)',
    'Temporal stability checks with RNN/LSTM',
    'Instance segmentation with Mask R-CNN',
    'MediaPipe landmarks for precise measurements',
    'Confidence scores for each measurement',
  ];

  return (
    <div className="dashboard-container">
      <Typography variant="h2" component="h1" gutterBottom>
        Body Measurement System
      </Typography>
      
      <Typography variant="h6" color="text.secondary" paragraph>
        Choose a mode to begin accurate body measurements
      </Typography>

      <div className="mode-buttons">
        <Card className="mode-card" onClick={() => onModeSelect('upload')}>
          <CardActionArea sx={{ height: '100%' }}>
            <CardContent>
              <CloudUploadIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" component="div">
                Upload Images
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Process front, side, and reference photos
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>

        <Card className="mode-card" onClick={() => onModeSelect('live')}>
          <CardActionArea sx={{ height: '100%' }}>
            <CardContent>
              <VideocamIcon sx={{ fontSize: 80, color: 'secondary.main', mb: 2 }} />
              <Typography variant="h5" component="div">
                Live Camera
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Real-time capture with alignment guidance
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>
      </div>

      <Box className="features-list">
        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
          Features
        </Typography>
        <List>
          {features.map((feature, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                <CheckCircleIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary={feature} />
            </ListItem>
          ))}
        </List>
      </Box>
    </div>
  );
}

export default Dashboard;
