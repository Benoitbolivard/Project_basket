# Project Basket - Basketball Analytics Platform

A comprehensive basketball video analysis platform using computer vision and machine learning to provide advanced analytics for basketball games.

## Phase 1 - Vision de base ✅

### Features Completed

#### 🎯 Basketball-Specific YOLO Detection
- Optimized YOLO detection for basketball scenarios
- Detects players, basketball, and court elements
- Configurable confidence thresholds
- Court zone mapping and analysis
- Real-time visualization capabilities

#### 🔄 DeepSORT Player Tracking  
- Unique player ID assignment and tracking
- Maintains tracking across frames even with occlusions
- Player statistics and movement analysis
- Consistent color coding for visualization
- Track quality metrics and hit streaks

#### 📊 Basketball Analytics
- **Shot Detection**: Automatic detection of shot attempts based on ball trajectory
- **Possession Analysis**: Real-time ball possession tracking with player assignments
- **Court Zones**: Predefined basketball court zones (paint, three-point areas, etc.)
- **Player Performance**: Individual player statistics and heat maps
- **Game Events**: Comprehensive event detection and logging

#### 📁 Enhanced JSON Export
- Timestamped frame-by-frame data
- Precise bounding box coordinates
- Player tracking IDs and statistics
- Shot chart data with zone classifications
- Possession history and analytics
- Complete game statistics

### Technical Implementation

#### Core Components

1. **BasketballDetector** (`vision/detector.py`)
   - YOLO-based object detection
   - Basketball-specific class filtering
   - Court zone analysis
   - Confidence-based filtering

2. **BasketballTracker** (`vision/tracker.py`)
   - DeepSORT integration for player tracking
   - Possession determination logic
   - Player statistics tracking
   - Shot attempt detection

3. **BasketballAnalytics** (`vision/analytics.py`)
   - Advanced game event analysis
   - Shot zone classification
   - Player performance metrics
   - Heat map generation

4. **BasketballVideoProcessor** (`vision/processor.py`)
   - Complete video processing pipeline
   - Integrated detection, tracking, and analytics
   - Video output with annotations
   - JSON export functionality

5. **FastAPI Backend** (`backend/app/main.py`)
   - RESTful API for video analysis
   - File upload and processing endpoints
   - Real-time analysis status
   - JSON result download

### API Endpoints

```
POST /analyze/video        - Analyze local video file
POST /analyze/upload       - Upload and analyze video
GET  /analyze/{id}         - Get analysis results by ID
GET  /analyze/{id}/download - Download JSON results
GET  /stats/current        - Get current processing statistics
POST /analyze/live         - Start live camera analysis
GET  /health              - API health check
```

### Data Models

All API interactions use comprehensive Pydantic models for type safety:
- `VideoAnalysisResult` - Complete analysis output
- `FrameAnalysis` - Frame-by-frame detection/tracking data
- `PlayerStats` - Individual player performance metrics
- `ShotAttempt` - Shot attempt information
- `PossessionEvent` - Possession change events

### Installation & Usage

```bash
# Install dependencies
poetry install

# Run tests
poetry run python tests/test_basketball_vision.py

# Run demo
poetry run python demo.py

# Start API server
poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Demo Output

The demo generates:
- Annotated video with detections and tracking
- Complete JSON analysis with timestamps
- Individual frame visualizations
- Processing statistics and performance metrics

### Performance Metrics

- Real-time processing capability (30+ FPS on modern hardware)
- High accuracy basketball detection
- Robust multi-player tracking
- Comprehensive analytics output

## Project Structure

```
Project_basket/
├── vision/                 # Computer vision modules
│   ├── detector.py        # YOLO basketball detection
│   ├── tracker.py         # DeepSORT player tracking
│   ├── analytics.py       # Basketball analytics
│   └── processor.py       # Complete video processor
├── backend/               # FastAPI backend
│   └── app/
│       ├── main.py       # API endpoints
│       └── models.py     # Pydantic data models
├── tests/                 # Test suite
│   └── test_basketball_vision.py
├── demo.py               # Comprehensive demo script
└── pyproject.toml        # Dependencies and configuration
```

## Next Phases

- **Phase 2**: Backend & Database (Postgres, REST API)
- **Phase 3**: Frontend (Interactive shot charts, live dashboard)

## Technology Stack

- **Computer Vision**: OpenCV, Ultralytics YOLO
- **Tracking**: DeepSORT
- **Backend**: FastAPI, Pydantic
- **Data Processing**: NumPy
- **Package Management**: Poetry
