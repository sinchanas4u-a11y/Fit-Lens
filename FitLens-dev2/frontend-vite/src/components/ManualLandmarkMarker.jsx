import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import './ManualLandmarkMarker.css';

const ManualLandmarkMarker = ({ imageData, imageType, onComplete, onCancel, imageHeight, imageWidth }) => {
  const [landmarks, setLandmarks] = useState([]);
  const [currentLine, setCurrentLine] = useState(null);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  // Landmark types with colors
  const landmarkTypes = [
    { id: 'shoulder', label: 'Shoulder Width', color: '#FF6B6B', description: 'Mark left & right shoulder edges' },
    { id: 'chest', label: 'Chest Width', color: '#4ECDC4', description: 'Mark left & right chest edges' },
    { id: 'waist', label: 'Waist Width', color: '#45B7D1', description: 'Mark left & right waist edges' },
    { id: 'hip', label: 'Hip Width', color: '#FFA07A', description: 'Mark left & right hip edges' },
    { id: 'arm', label: 'Arm Length', color: '#98D8C8', description: 'Mark shoulder to wrist' },
    { id: 'leg', label: 'Leg Length', color: '#F7DC6F', description: 'Mark hip to ankle' },
    { id: 'custom', label: 'Custom Measurement', color: '#BB8FCE', description: 'Mark any two points' }
  ];

  const [selectedType, setSelectedType] = useState(landmarkTypes[0].id);

  useEffect(() => {
    if (imageRef.current && canvasRef.current) {
      const image = imageRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      // Calculate scale to fit image in canvas
      const maxWidth = canvas.width;
      const maxHeight = canvas.height;
      const scaleX = maxWidth / image.naturalWidth;
      const scaleY = maxHeight / image.naturalHeight;
      const newScale = Math.min(scaleX, scaleY, 1);
      
      setScale(newScale);
      setOffset({
        x: (maxWidth - image.naturalWidth * newScale) / 2,
        y: (maxHeight - image.naturalHeight * newScale) / 2
      });

      redrawCanvas();
    }
  }, [imageData, landmarks, currentLine, hoveredPoint]);

  const redrawCanvas = () => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw image
    ctx.drawImage(
      image,
      offset.x,
      offset.y,
      image.naturalWidth * scale,
      image.naturalHeight * scale
    );

    // Draw existing landmarks and lines
    landmarks.forEach((landmark, idx) => {
      const color = landmarkTypes.find(t => t.id === landmark.type)?.color || '#888';
      
      // Draw line if landmark has pair
      if (landmark.points.length === 2) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(
          landmark.points[0].x * scale + offset.x,
          landmark.points[0].y * scale + offset.y
        );
        ctx.lineTo(
          landmark.points[1].x * scale + offset.x,
          landmark.points[1].y * scale + offset.y
        );
        ctx.stroke();

        // Draw distance label
        const midX = (landmark.points[0].x + landmark.points[1].x) / 2 * scale + offset.x;
        const midY = (landmark.points[0].y + landmark.points[1].y) / 2 * scale + offset.y;
        const distance = Math.sqrt(
          Math.pow(landmark.points[1].x - landmark.points[0].x, 2) +
          Math.pow(landmark.points[1].y - landmark.points[0].y, 2)
        );
        
        ctx.fillStyle = color;
        ctx.font = 'bold 14px Arial';
        ctx.fillText(`${Math.round(distance)}px`, midX + 5, midY - 5);
      }

      // Draw points
      landmark.points.forEach((point, pointIdx) => {
        ctx.fillStyle = color;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        
        const isHovered = hoveredPoint === `${idx}-${pointIdx}`;
        const radius = isHovered ? 8 : 6;
        
        ctx.beginPath();
        ctx.arc(
          point.x * scale + offset.x,
          point.y * scale + offset.y,
          radius,
          0,
          Math.PI * 2
        );
        ctx.fill();
        ctx.stroke();

        // Draw point number
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(
          pointIdx + 1,
          point.x * scale + offset.x,
          point.y * scale + offset.y
        );
      });
    });

    // Draw current line being drawn
    if (currentLine) {
      const color = landmarkTypes.find(t => t.id === selectedType)?.color || '#888';
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(
        currentLine.start.x * scale + offset.x,
        currentLine.start.y * scale + offset.y
      );
      ctx.lineTo(
        currentLine.end.x * scale + offset.x,
        currentLine.end.y * scale + offset.y
      );
      ctx.stroke();
      ctx.setLineDash([]);
    }
  };

  // Helper to get exact canvas coordinates accounting for CSS scaling
  const getCanvasCoordinates = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    
    // Calculate scale between displayed size (CSS) and internal resolution (width/height attributes)
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    // Get position relative to canvas element
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    return { x, y };
  };

  const handleCanvasClick = (e) => {
    // Get canvas-internal coordinates
    const { x: canvasX, y: canvasY } = getCanvasCoordinates(e);

    // Map to image coordinates using image scale and offset
    const x = (canvasX - offset.x) / scale;
    const y = (canvasY - offset.y) / scale;

    // Check if clicking on existing point to start line
    const clickedPointIndex = findClickedPoint(x, y);
    
    if (clickedPointIndex !== null) {
      const [landmarkIdx, pointIdx] = clickedPointIndex.split('-').map(Number);
      setSelectedPoint(clickedPointIndex);
      return;
    }

    // Add new point
    if (!currentLine) {
      // Start new landmark
      setCurrentLine({
        start: { x, y },
        end: { x, y }
      });
    } else {
      // Complete landmark with second point
      const newLandmark = {
        type: selectedType,
        points: [
          currentLine.start,
          { x, y }
        ],
        label: landmarkTypes.find(t => t.id === selectedType)?.label || 'Custom'
      };
      
      setLandmarks([...landmarks, newLandmark]);
      setCurrentLine(null);
    }
  };

  const handleCanvasMouseMove = (e) => {
    const { x: canvasX, y: canvasY } = getCanvasCoordinates(e);

    const x = (canvasX - offset.x) / scale;
    const y = (canvasY - offset.y) / scale;

    // Update hover state
    const hoveredIdx = findClickedPoint(x, y);
    setHoveredPoint(hoveredIdx);

    // Update current line endpoint
    if (currentLine) {
      setCurrentLine({
        ...currentLine,
        end: { x, y }
      });
    }
  };

  const findClickedPoint = (x, y) => {
    // Adjust threshold for better touch/click targets
    const threshold = 15 / scale;
    for (let i = 0; i < landmarks.length; i++) {
      for (let j = 0; j < landmarks[i].points.length; j++) {
        const point = landmarks[i].points[j];
        const dist = Math.sqrt(Math.pow(point.x - x, 2) + Math.pow(point.y - y, 2));
        if (dist < threshold) {
          return `${i}-${j}`;
        }
      }
    }
    return null;
  };

  const handleDeleteLandmark = (index) => {
    setLandmarks(landmarks.filter((_, idx) => idx !== index));
  };

  const handleCancelCurrentLine = () => {
    setCurrentLine(null);
  };

  const handleSubmit = () => {
    if (landmarks.length === 0) {
      alert('Please mark at least one measurement point');
      return;
    }

    // Convert landmarks to API format
    const formattedLandmarks = landmarks.map(landmark => ({
      type: landmark.type,
      label: landmark.label,
      points: landmark.points.map(p => ({
        x: p.x,
        y: p.y,
        // Normalized coordinates (0-1 range)
        x_norm: p.x / imageRef.current.naturalWidth,
        y_norm: p.y / imageRef.current.naturalHeight
      }))
    }));

    onComplete({
      landmarks: formattedLandmarks,
      imageType,
      imageWidth: imageRef.current.naturalWidth,
      imageHeight: imageRef.current.naturalHeight
    });
  };

  return (
    <div className="manual-landmark-marker">
      <div className="marker-header">
        <h3>Manual Landmark Marking - {imageType === 'front' ? 'Front View' : 'Side View'}</h3>
        <p>Click on the image to mark measurement points. Click two points to create a measurement line.</p>
      </div>

      <div className="marker-content">
        {/* Canvas for marking */}
        <div className="canvas-container">
          <canvas
            ref={canvasRef}
            width={900}
            height={700}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            style={{ cursor: currentLine ? 'crosshair' : 'pointer' }}
          />
          <img
            ref={imageRef}
            src={imageData}
            alt="Marking target"
            style={{ display: 'none' }}
            onLoad={redrawCanvas}
          />
          
          {currentLine && (
            <div className="cancel-line-button">
              <button onClick={handleCancelCurrentLine}>Cancel Current Line (ESC)</button>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="marker-controls">
          <div className="landmark-type-selector">
            <h4>Select Measurement Type:</h4>
            {landmarkTypes.map(type => (
              <button
                key={type.id}
                className={`type-button ${selectedType === type.id ? 'active' : ''}`}
                onClick={() => setSelectedType(type.id)}
                style={{
                  borderColor: type.color,
                  backgroundColor: selectedType === type.id ? type.color : 'transparent',
                  color: selectedType === type.id ? '#fff' : type.color
                }}
              >
                <span className="type-dot" style={{ backgroundColor: type.color }}></span>
                <span className="type-label">{type.label}</span>
              </button>
            ))}
          </div>

          <div className="marked-landmarks">
            <h4>Marked Measurements ({landmarks.length}):</h4>
            {landmarks.length === 0 ? (
              <p className="no-landmarks">No measurements marked yet</p>
            ) : (
              <ul>
                {landmarks.map((landmark, idx) => {
                  const distance = Math.sqrt(
                    Math.pow(landmark.points[1].x - landmark.points[0].x, 2) +
                    Math.pow(landmark.points[1].y - landmark.points[0].y, 2)
                  );
                  const color = landmarkTypes.find(t => t.id === landmark.type)?.color;
                  
                  return (
                    <li key={idx} style={{ borderLeftColor: color }}>
                      <span className="landmark-info">
                        <span className="landmark-label">{landmark.label}</span>
                        <span className="landmark-distance">{Math.round(distance)} px</span>
                      </span>
                      <button
                        className="delete-button"
                        onClick={() => handleDeleteLandmark(idx)}
                        title="Delete this measurement"
                      >
                        ✕
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="action-buttons">
            <button className="cancel-button" onClick={onCancel}>
              Cancel
            </button>
            <button
              className="submit-button"
              onClick={handleSubmit}
              disabled={landmarks.length === 0}
            >
              Complete Marking ({landmarks.length} measurements)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

ManualLandmarkMarker.propTypes = {
  imageData: PropTypes.string.isRequired,
  imageType: PropTypes.string.isRequired,
  onComplete: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  imageHeight: PropTypes.number,
  imageWidth: PropTypes.number
};

export default ManualLandmarkMarker;
