# Documentation Index

Quick navigation to all project documentation.

## 🚀 Getting Started

1. **[README_COMPLETE.md](README_COMPLETE.md)** - Start here! Complete overview
2. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
3. **[test_installation.py](test_installation.py)** - Verify your installation

## 📖 Main Documentation

### User Documentation
- **[README_RCNN.md](README_RCNN.md)** - Complete user guide
  - Installation instructions
  - Usage examples
  - Configuration options
  - Troubleshooting
  - Performance benchmarks

### Quick Reference
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup
  - Installation steps
  - Basic usage
  - Common issues
  - Tips for best results

### Visual Guide
- **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - Diagrams and flowcharts
  - UI layout
  - Application flow
  - Measurement calculations
  - Alignment checks
  - Training pipeline

## 🏗️ Technical Documentation

### Architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design
  - Module architecture
  - Data flow
  - Design patterns
  - Performance optimization
  - Extensibility

### Project Summary
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete overview
  - Feature checklist
  - Technical specifications
  - Usage examples
  - Performance benchmarks
  - Project status

### Comparison
- **[COMPARISON.md](COMPARISON.md)** - Implementation comparison
  - MediaPipe vs R-CNN
  - Feature comparison
  - Performance comparison
  - When to use each
  - Migration guide

## 💻 Code Files

### Main Application
- **[main.py](main.py)** - Main application
  - Real-time capture
  - Pose detection
  - Measurement calculation
  - UI rendering

### Model Architecture
- **[model_arch.py](model_arch.py)** - R-CNN implementation
  - KeypointRCNN class
  - ModelTrainer class
  - DepthEstimator class
  - CenteringChecker class

### Pose Utilities
- **[pose_utils.py](pose_utils.py)** - Pose analysis
  - PoseUtils class
  - AlignmentChecker class
  - MeasurementCalculator class
  - SkeletonDrawer class

### Dataset Handling
- **[dataset.py](dataset.py)** - Data loading
  - COCOKeypointDataset class
  - DataAugmentation class
  - SyntheticDataGenerator class
  - Dataset registration

### Training
- **[train.py](train.py)** - Model training
  - Training loop
  - Evaluation
  - Visualization
  - Checkpoint management

### Configuration
- **[config.py](config.py)** - Settings
  - Model parameters
  - Camera settings
  - Alignment thresholds
  - Privacy settings

## 🧪 Testing & Installation

### Installation Scripts
- **[install.bat](install.bat)** - Windows installation
- **[install.sh](install.sh)** - Linux/Mac installation

### Testing
- **[test_installation.py](test_installation.py)** - Verify setup
  - Package imports
  - Camera access
  - Model loading
  - Synthetic data test

### Dependencies
- **[requirements_rcnn.txt](requirements_rcnn.txt)** - Python packages

## 📚 Documentation by Use Case

### I want to...

#### ...get started quickly
1. [QUICKSTART.md](QUICKSTART.md)
2. Run `python test_installation.py`
3. Run `python main.py --demo`

#### ...understand the system
1. [README_COMPLETE.md](README_COMPLETE.md)
2. [VISUAL_GUIDE.md](VISUAL_GUIDE.md)
3. [ARCHITECTURE.md](ARCHITECTURE.md)

#### ...use the application
1. [README_RCNN.md](README_RCNN.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. Run `python main.py --height YOUR_HEIGHT`

#### ...train a model
1. [README_RCNN.md](README_RCNN.md) - Training section
2. [train.py](train.py) - Training script
3. [dataset.py](dataset.py) - Dataset handling

#### ...customize the system
1. [config.py](config.py) - Configuration
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Extensibility
3. [pose_utils.py](pose_utils.py) - Add measurements

#### ...troubleshoot issues
1. Run `python test_installation.py`
2. [README_RCNN.md](README_RCNN.md) - Troubleshooting
3. [QUICKSTART.md](QUICKSTART.md) - Common issues

#### ...understand the code
1. [ARCHITECTURE.md](ARCHITECTURE.md)
2. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
3. Read code files with comments

#### ...compare implementations
1. [COMPARISON.md](COMPARISON.md)
2. [README_RCNN.md](README_RCNN.md)
3. [README.md](README.md) - MediaPipe version

## 🎯 Documentation by Role

### End User
1. [QUICKSTART.md](QUICKSTART.md)
2. [README_RCNN.md](README_RCNN.md)
3. [VISUAL_GUIDE.md](VISUAL_GUIDE.md)

### Developer
1. [ARCHITECTURE.md](ARCHITECTURE.md)
2. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
3. Code files with docstrings

### Researcher
1. [README_RCNN.md](README_RCNN.md) - Technical details
2. [ARCHITECTURE.md](ARCHITECTURE.md)
3. [train.py](train.py) - Training pipeline

### System Administrator
1. [install.bat](install.bat) / [install.sh](install.sh)
2. [test_installation.py](test_installation.py)
3. [requirements_rcnn.txt](requirements_rcnn.txt)

## 📊 Documentation Statistics

- **Total Documentation Files:** 8
- **Total Code Files:** 7
- **Total Lines of Code:** ~3,500+
- **Total Lines of Documentation:** ~2,500+
- **Code Comments:** Comprehensive
- **Docstrings:** All functions

## 🔍 Search Guide

### Find information about...

- **Installation:** QUICKSTART.md, README_RCNN.md, install scripts
- **Usage:** README_RCNN.md, QUICKSTART.md, main.py
- **Configuration:** config.py, README_RCNN.md
- **Training:** train.py, README_RCNN.md, dataset.py
- **Measurements:** pose_utils.py, ARCHITECTURE.md
- **Alignment:** pose_utils.py, VISUAL_GUIDE.md
- **Privacy:** config.py, README_RCNN.md, PROJECT_SUMMARY.md
- **Performance:** COMPARISON.md, PROJECT_SUMMARY.md
- **Troubleshooting:** README_RCNN.md, QUICKSTART.md
- **Architecture:** ARCHITECTURE.md, VISUAL_GUIDE.md

## 📝 File Descriptions

### Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| README_COMPLETE.md | Complete overview | Everyone |
| README_RCNN.md | Full documentation | Users |
| QUICKSTART.md | Fast setup | New users |
| ARCHITECTURE.md | Technical design | Developers |
| PROJECT_SUMMARY.md | Feature checklist | Everyone |
| COMPARISON.md | Implementation comparison | Decision makers |
| VISUAL_GUIDE.md | Diagrams | Visual learners |
| INDEX.md | This file | Everyone |

### Code Files

| File | Purpose | Lines |
|------|---------|-------|
| main.py | Main application | ~400 |
| model_arch.py | R-CNN model | ~350 |
| pose_utils.py | Pose utilities | ~500 |
| dataset.py | Data loading | ~300 |
| train.py | Training script | ~250 |
| config.py | Configuration | ~150 |
| test_installation.py | Testing | ~200 |

## 🎓 Learning Path

### Beginner
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `python main.py --demo`
3. Read [VISUAL_GUIDE.md](VISUAL_GUIDE.md)
4. Try `python main.py --height YOUR_HEIGHT`

### Intermediate
1. Read [README_RCNN.md](README_RCNN.md)
2. Explore [config.py](config.py)
3. Read [COMPARISON.md](COMPARISON.md)
4. Customize settings

### Advanced
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Study code files
3. Read [train.py](train.py)
4. Train custom model

## 🔗 Quick Links

### Most Important Files
- 🚀 [QUICKSTART.md](QUICKSTART.md) - Start here
- 📖 [README_RCNN.md](README_RCNN.md) - Complete guide
- 💻 [main.py](main.py) - Run this
- ⚙️ [config.py](config.py) - Configure this

### Most Useful Commands
```bash
python test_installation.py  # Test setup
python main.py --demo        # Demo mode
python main.py --height 175  # Run with calibration
python train.py --mode train # Train model
```

---

**Start with [README_COMPLETE.md](README_COMPLETE.md) or [QUICKSTART.md](QUICKSTART.md)!**
