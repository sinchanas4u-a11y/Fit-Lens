import React, { useState, useRef } from 'react';

const ZoomableImage = ({ src, alt, style, className }) => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const imgRef = useRef(null);

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale(prev => Math.min(Math.max(prev * delta, 0.5), 5));
  };

  const handleMouseDown = (e) => {
    if (scale === 1) return;
    setIsDragging(true);
    dragStart.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y
    };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleDoubleClick = () => {
    if (scale !== 1) {
      setScale(1);
      setPosition({ x: 0, y: 0 });
    } else {
      setScale(2);
    }
  };

  const resetZoom = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  // Touch support for mobile web:
  const lastTouchDist = useRef(null);
  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      lastTouchDist.current = Math.sqrt(dx * dx + dy * dy);
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (lastTouchDist.current) {
        const delta = dist / lastTouchDist.current;
        setScale(prev => Math.min(Math.max(prev * delta, 0.5), 5));
      }
      lastTouchDist.current = dist;
    }
  };

  return (
    <>
      <div style={{ position: 'relative', overflow: 'hidden',
        cursor: scale > 1 ? 'grab' : 'zoom-in', ...style }}
        className={className}>
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onDoubleClick={handleDoubleClick}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          style={{
            transform: `scale(${scale}) translate(${position.x / scale}px, ${position.y / scale}px)`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.1s ease',
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            userSelect: 'none',
            cursor: isDragging ? 'grabbing' : scale > 1 ? 'grab' : 'zoom-in',
          }}
          draggable={false}
        />
        {/* Zoom controls */}
        <div style={{
          position: 'absolute', bottom: 8, right: 8,
          display: 'flex', gap: 4, zIndex: 10
        }}>
          <button onClick={() => setScale(s => Math.min(s * 1.3, 5))}
            style={zoomBtnStyle} title="Zoom In">+</button>
          <button onClick={() => setScale(s => Math.max(s * 0.77, 0.5))}
            style={zoomBtnStyle} title="Zoom Out">−</button>
          <button onClick={resetZoom}
            style={zoomBtnStyle} title="Reset">⊙</button>
          <button onClick={() => setIsFullscreen(true)}
            style={zoomBtnStyle} title="Fullscreen">⛶</button>
        </div>
        {/* Scale indicator */}
        {scale !== 1 && (
          <div style={{
            position: 'absolute', top: 8, left: 8,
            background: 'rgba(0,0,0,0.6)', color: '#00d4aa',
            padding: '2px 8px', borderRadius: 6,
            fontSize: 12, fontWeight: 700
          }}>
            {Math.round(scale * 100)}%
          </div>
        )}
      </div>

      {/* Fullscreen modal */}
      {isFullscreen && (
        <div style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.95)',
          zIndex: 9999, display: 'flex',
          flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center'
        }}
          onClick={() => setIsFullscreen(false)}>
          <button onClick={() => setIsFullscreen(false)}
            style={{
              position: 'absolute', top: 16, right: 16,
              background: 'rgba(255,255,255,0.2)',
              border: 'none', color: '#fff',
              borderRadius: '50%', width: 40, height: 40,
              fontSize: 20, cursor: 'pointer'
            }}>✕</button>
          <img src={src} alt={alt}
            style={{ maxWidth: '95vw', maxHeight: '95vh',
              objectFit: 'contain', borderRadius: 8 }} />
          <p style={{ color: '#a0aec0', marginTop: 12, fontSize: 12 }}>
            Scroll to zoom • Click anywhere to close
          </p>
        </div>
      )}
    </>
  );
};

const zoomBtnStyle = {
  background: 'rgba(0,0,0,0.7)', color: '#00d4aa',
  border: '1px solid #00d4aa', borderRadius: 6,
  width: 28, height: 28, cursor: 'pointer',
  fontSize: 16, fontWeight: 700, display: 'flex',
  alignItems: 'center', justifyContent: 'center',
};

export default ZoomableImage;
