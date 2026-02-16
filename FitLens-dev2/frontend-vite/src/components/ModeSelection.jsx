import PropTypes from 'prop-types';
import './ModeSelection.css';

const ModeSelection = ({ onSelectMode }) => {
  return (
    <div className="mode-selection-overlay">
      <div className="mode-selection-container">
        <h2>Choose Detection Method</h2>
        <p className="subtitle">How would you like to measure your body?</p>

        <div className="mode-options">
          {/* Manual Mode */}
          <div className="mode-card" onClick={() => onSelectMode('manual')}>
            <div className="mode-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
            </div>
            <h3>Manual Landmark Marking</h3>
            <p className="mode-description">
              Click to mark specific body measurement points yourself. 
              Perfect for targeting specific measurements.
            </p>
            <ul className="mode-features">
              <li>✓ Click to place measurement points</li>
              <li>✓ Choose specific body parts</li>
              <li>✓ Edit and adjust markers</li>
              <li>✓ Quick and focused</li>
            </ul>
            <button className="select-button manual">
              Select Manual Mode
            </button>
          </div>

          {/* Automatic Mode */}
          <div className="mode-card featured" onClick={() => onSelectMode('automatic')}>
            <div className="recommended-badge">Recommended</div>
            <div className="mode-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3>Complete Body Detection (Automatic)</h3>
            <p className="mode-description">
              AI-powered full body analysis using YOLOv8 and MediaPipe. 
              Get comprehensive measurements automatically.
            </p>
            <ul className="mode-features">
              <li>✓ 33-point body landmark detection</li>
              <li>✓ AI-powered segmentation</li>
              <li>✓ Comprehensive measurements</li>
              <li>✓ Clinical-grade accuracy</li>
            </ul>
            <button className="select-button automatic">
              Select Automatic Mode
            </button>
          </div>
        </div>

        <div className="mode-info">
          <p>
            <strong>Note:</strong> Both methods use the same measurement calculation logic and your provided height for accurate scaling.
          </p>
        </div>
      </div>
    </div>
  );
};

ModeSelection.propTypes = {
  onSelectMode: PropTypes.func.isRequired
};

export default ModeSelection;
