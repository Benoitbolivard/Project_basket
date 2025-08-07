"""Basic tests for basketball vision components."""

import pytest
import numpy as np
import cv2
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from vision.detector import BasketballDetector
from vision.tracker import BasketballTracker
from vision.analytics import BasketballAnalytics
from vision.processor import BasketballVideoProcessor


@pytest.fixture
def sample_frame():
    """Create a sample frame for testing."""
    # Create a simple test frame (640x480, RGB)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return frame


@pytest.fixture
def detector():
    """Create a basketball detector instance."""
    return BasketballDetector(confidence_threshold=0.1)  # Lower threshold for tests


@pytest.fixture
def tracker():
    """Create a basketball tracker instance."""
    return BasketballTracker()


@pytest.fixture
def analytics():
    """Create a basketball analytics instance."""
    return BasketballAnalytics()


@pytest.fixture
def processor():
    """Create a video processor instance."""
    return BasketballVideoProcessor(confidence_threshold=0.1)


class TestBasketballDetector:
    """Test basketball detection functionality."""
    
    def test_detector_initialization(self, detector):
        """Test detector initialization."""
        assert detector.confidence_threshold == 0.1
        assert detector.frame_count == 0
        assert detector.model is not None
    
    def test_detect_frame_basic(self, detector, sample_frame):
        """Test basic frame detection."""
        timestamp = 1.0
        results = detector.detect_frame(sample_frame, timestamp)
        
        # Check result structure
        assert 'frame_id' in results
        assert 'timestamp' in results
        assert 'frame_shape' in results
        assert 'players' in results
        assert 'ball' in results
        assert 'court_zones' in results
        
        # Check values
        assert results['timestamp'] == timestamp
        assert results['frame_shape'] == sample_frame.shape
        assert isinstance(results['players'], list)
        assert isinstance(results['court_zones'], dict)
    
    def test_bbox_center_calculation(self, detector):
        """Test bounding box center calculation."""
        bbox = np.array([10, 20, 50, 80])
        center = detector._get_bbox_center(bbox)
        assert center == (30.0, 50.0)
    
    def test_bbox_area_calculation(self, detector):
        """Test bounding box area calculation."""
        bbox = np.array([10, 20, 50, 80])
        area = detector._get_bbox_area(bbox)
        assert area == 2400.0  # (50-10) * (80-20)
    
    def test_player_filtering(self, detector):
        """Test player detection filtering."""
        frame_shape = (480, 640, 3)
        
        # Valid player detection
        valid_detection = {
            'bbox': [100, 100, 150, 250],  # Reasonable size and aspect ratio
            'confidence': 0.8
        }
        assert detector._is_likely_player(valid_detection, frame_shape)
        
        # Invalid player detection (too small)
        invalid_detection = {
            'bbox': [100, 100, 110, 115],  # Too small
            'confidence': 0.8
        }
        assert not detector._is_likely_player(invalid_detection, frame_shape)
    
    def test_basketball_filtering(self, detector):
        """Test basketball detection filtering."""
        # Valid basketball
        valid_ball = {
            'confidence': 0.6,
            'area': 500
        }
        assert detector._is_likely_basketball(valid_ball)
        
        # Invalid basketball (low confidence)
        invalid_ball = {
            'confidence': 0.2,
            'area': 500
        }
        assert not detector._is_likely_basketball(invalid_ball)


class TestBasketballTracker:
    """Test basketball tracking functionality."""
    
    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.tracker is not None
        assert tracker.player_stats == {}
        assert tracker.ball_trajectory == []
        assert tracker.possession_history == []
    
    def test_track_update_empty(self, tracker, sample_frame):
        """Test track update with no detections."""
        empty_detections = {
            'frame_id': 1,
            'timestamp': 1.0,
            'players': [],
            'ball': None,
            'court_zones': {}
        }
        
        results = tracker.update_tracks(empty_detections, sample_frame)
        
        assert results['frame_id'] == 1
        assert results['timestamp'] == 1.0
        assert results['tracked_players'] == []
        assert results['ball_info'] is None
    
    def test_possession_determination(self, tracker):
        """Test possession determination logic."""
        ball_center = (100, 100)
        players = [
            {'track_id': 1, 'center': (95, 95)},   # Close player
            {'track_id': 2, 'center': (200, 200)}  # Far player
        ]
        
        possession_player = tracker._determine_possession(ball_center, players)
        assert possession_player == 1  # Should be the closer player
    
    def test_player_color_consistency(self, tracker):
        """Test that player colors are consistent."""
        color1_a = tracker._get_player_color(1)
        color1_b = tracker._get_player_color(1)
        assert color1_a == color1_b
        
        color2 = tracker._get_player_color(2)
        assert color1_a != color2  # Different players should have different colors


class TestBasketballAnalytics:
    """Test basketball analytics functionality."""
    
    def test_analytics_initialization(self, analytics):
        """Test analytics initialization."""
        assert analytics.shot_attempts == []
        assert analytics.possession_events == []
        assert len(analytics.player_analytics) == 0
        assert analytics.game_state['current_possession'] is None
    
    def test_court_zone_determination(self, analytics):
        """Test court zone determination."""
        court_zones = {
            'paint': {
                'active': True,
                'pixel_coords': (100, 100, 200, 200)
            }
        }
        
        # Position inside paint
        zone = analytics._determine_court_zone((150, 150), court_zones)
        assert zone == 'paint'
        
        # Position outside paint
        zone = analytics._determine_court_zone((300, 300), court_zones)
        assert zone == 'unknown'
    
    def test_shot_zone_classification(self, analytics):
        """Test shot zone classification."""
        # This is a simplified test - actual implementation would need court calibration
        position = (100, 100)
        zone = analytics._classify_shot_zone(position)
        assert zone in analytics.SHOT_ZONES or zone == 'mid_range'
    
    def test_game_statistics_structure(self, analytics):
        """Test game statistics structure."""
        stats = analytics.get_game_statistics()
        
        assert 'game_duration' in stats
        assert 'total_shots' in stats
        assert 'possession_changes' in stats
        assert 'player_stats' in stats
        assert 'shot_chart' in stats
        assert 'possession_summary' in stats


class TestBasketballVideoProcessor:
    """Test video processor integration."""
    
    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor.detector is not None
        assert processor.tracker is not None
        assert processor.analytics is not None
        assert processor.processing_results == []
    
    def test_process_frame_integration(self, processor, sample_frame):
        """Test frame processing integration."""
        timestamp = 1.0
        results = processor.process_frame(sample_frame, timestamp)
        
        # Check structure
        assert 'timestamp' in results
        assert 'frame_id' in results
        assert 'detections' in results
        assert 'tracking' in results
        assert 'analytics' in results
        assert 'processing_metadata' in results
        
        # Check values
        assert results['timestamp'] == timestamp
        assert isinstance(results['processing_metadata']['detection_count'], int)
        assert isinstance(results['processing_metadata']['tracked_players'], int)
        assert isinstance(results['processing_metadata']['events_detected'], int)
    
    def test_current_stats(self, processor):
        """Test current statistics retrieval."""
        stats = processor.get_current_stats()
        assert 'status' in stats or 'frames_processed' in stats


class TestModelsIntegration:
    """Test Pydantic models work with actual data."""
    
    def test_detection_model(self):
        """Test Detection model with sample data."""
        from backend.app.models import Detection
        
        detection_data = {
            'bbox': [10, 20, 50, 80],
            'confidence': 0.8,
            'class_id': 0,
            'class_name': 'person',
            'center': (30.0, 50.0),
            'area': 2400.0
        }
        
        detection = Detection(**detection_data)
        assert detection.bbox == [10, 20, 50, 80]
        assert detection.confidence == 0.8
        assert detection.center == (30.0, 50.0)
    
    def test_frame_analysis_model(self):
        """Test FrameAnalysis model with sample data."""
        from backend.app.models import FrameAnalysis
        
        frame_data = {
            'timestamp': 1.0,
            'frame_id': 1,
            'frame_shape': (480, 640, 3)
        }
        
        frame_analysis = FrameAnalysis(**frame_data)
        assert frame_analysis.timestamp == 1.0
        assert frame_analysis.frame_id == 1
        assert frame_analysis.players == []
        assert frame_analysis.ball is None


if __name__ == "__main__":
    # Run basic functionality tests without pytest
    print("Running basic basketball vision tests...")
    
    # Test detector
    detector = BasketballDetector(confidence_threshold=0.1)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    detections = detector.detect_frame(frame, 1.0)
    print(f"✓ Detector test passed - detected {len(detections['players'])} players")
    
    # Test tracker
    tracker = BasketballTracker()
    tracking_results = tracker.update_tracks(detections, frame)
    print(f"✓ Tracker test passed - tracking {len(tracking_results['tracked_players'])} players")
    
    # Test analytics
    analytics = BasketballAnalytics()
    analytics_results = analytics.analyze_frame(tracking_results)
    print(f"✓ Analytics test passed - found {len(analytics_results['events'])} events")
    
    # Test processor
    processor = BasketballVideoProcessor(confidence_threshold=0.1)
    frame_results = processor.process_frame(frame, 1.0)
    print(f"✓ Processor test passed - processed frame {frame_results['frame_id']}")
    
    print("All basic tests passed! ✅")