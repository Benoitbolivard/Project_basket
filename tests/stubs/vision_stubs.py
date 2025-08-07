"""Vision processing stubs for CI testing."""

import json
from typing import Dict, Any, List
import numpy as np


class VisionStub:
    """Stub for vision processing that returns fake data without heavy ML models."""
    
    def __init__(self):
        self.confidence_threshold = 0.25
    
    def process_video(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """Return fake video processing results."""
        return {
            "video_metadata": {
                "video_path": video_path,
                "fps": 30.0,
                "width": 1920,
                "height": 1080,
                "total_frames": 1800,  # 1 minute at 30fps
                "duration_seconds": 60.0
            },
            "processing_summary": {
                "total_frames_processed": 1800,
                "frames_with_ball_detected": 1650,
                "ball_detection_rate": 0.917,
                "total_events_detected": 15,
                "unique_players_tracked": 6,
                "processing_time_seconds": 45.2
            },
            "game_statistics": {
                "game_duration": 60.0,
                "total_shots": 8,
                "possession_changes": 12,
                "player_stats": self._generate_fake_player_stats(),
                "shot_chart": {
                    "attempts_by_zone": {"paint": 3, "mid_range": 2, "three_point": 3},
                    "makes_by_zone": {"paint": 2, "mid_range": 1, "three_point": 1},
                    "shot_positions": []
                },
                "possession_summary": {}
            },
            "frame_by_frame_data": self._generate_fake_frame_data(),
            "player_performance": {},
            "shot_attempts": self._generate_fake_shots(),
            "possession_events": self._generate_fake_possessions(),
            "enhanced_stats": self._generate_enhanced_stats()
        }
    
    def _generate_fake_player_stats(self) -> Dict[int, Dict[str, Any]]:
        """Generate fake player statistics."""
        return {
            1: {
                "track_id": 1,
                "shots_attempted": 4,
                "shots_made": 2,
                "field_goal_percentage": 50.0,
                "three_point_attempts": 2,
                "three_point_made": 1,
                "three_point_percentage": 50.0,
                "possessions": 8,
                "total_possession_time": 25.4,
                "avg_possession_time": 3.175,
                "distance_covered": 1850.5,
                "time_in_zones": {"paint": 8.2, "mid_range": 12.1, "three_point": 5.1}
            },
            2: {
                "track_id": 2,
                "shots_attempted": 2,
                "shots_made": 1,
                "field_goal_percentage": 50.0,
                "three_point_attempts": 1,
                "three_point_made": 0,
                "three_point_percentage": 0.0,
                "possessions": 6,
                "total_possession_time": 18.7,
                "avg_possession_time": 3.12,
                "distance_covered": 1645.2,
                "time_in_zones": {"paint": 12.3, "mid_range": 8.4, "three_point": 4.0}
            },
            3: {
                "track_id": 3,
                "shots_attempted": 2,
                "shots_made": 1,
                "field_goal_percentage": 50.0,
                "three_point_attempts": 0,
                "three_point_made": 0,
                "three_point_percentage": 0.0,
                "possessions": 4,
                "total_possession_time": 15.2,
                "avg_possession_time": 3.8,
                "distance_covered": 1520.8,
                "time_in_zones": {"paint": 9.1, "mid_range": 6.1, "three_point": 0.0}
            }
        }
    
    def _generate_fake_frame_data(self) -> List[Dict[str, Any]]:
        """Generate fake frame-by-frame data."""
        frames = []
        for i in range(0, 1800, 30):  # Sample every 30 frames
            frame = {
                "timestamp": i / 30.0,
                "frame_id": i,
                "tracked_players": [
                    {
                        "track_id": 1,
                        "center": [960 + np.random.randint(-200, 200), 540 + np.random.randint(-100, 100)],
                        "confidence": 0.85
                    },
                    {
                        "track_id": 2,
                        "center": [960 + np.random.randint(-200, 200), 540 + np.random.randint(-100, 100)],
                        "confidence": 0.82
                    },
                    {
                        "track_id": 3,
                        "center": [960 + np.random.randint(-200, 200), 540 + np.random.randint(-100, 100)],
                        "confidence": 0.78
                    }
                ],
                "ball_analysis": {
                    "position": [960 + np.random.randint(-300, 300), 540 + np.random.randint(-150, 150)],
                    "confidence": 0.75
                }
            }
            frames.append(frame)
        return frames
    
    def _generate_fake_shots(self) -> List[Dict[str, Any]]:
        """Generate fake shot attempts."""
        return [
            {
                "timestamp": 15.5,
                "frame_id": 465,
                "shooter_id": 1,
                "shot_position": [1200, 400],
                "trajectory": [[1200, 400], [1150, 350], [1100, 300]],
                "shot_zone": "three_point",
                "confidence": 0.85,
                "made": True,
                "shot_value": 3
            },
            {
                "timestamp": 28.2,
                "frame_id": 846,
                "shooter_id": 2,
                "shot_position": [950, 500],
                "trajectory": [[950, 500], [920, 480], [900, 460]],
                "shot_zone": "paint",
                "confidence": 0.92,
                "made": True,
                "shot_value": 2
            },
            {
                "timestamp": 42.8,
                "frame_id": 1284,
                "shooter_id": 1,
                "shot_position": [1300, 350],
                "trajectory": [[1300, 350], [1280, 330], [1260, 310]],
                "shot_zone": "three_point",
                "confidence": 0.78,
                "made": False,
                "shot_value": 3
            }
        ]
    
    def _generate_fake_possessions(self) -> List[Dict[str, Any]]:
        """Generate fake possession events."""
        return [
            {
                "timestamp": 5.0,
                "frame_id": 150,
                "player_id": 1,
                "previous_player_id": None,
                "ball_position": [960, 540],
                "duration": 0.0
            },
            {
                "timestamp": 12.5,
                "frame_id": 375,
                "player_id": 2,
                "previous_player_id": 1,
                "ball_position": [850, 480],
                "duration": 7.5
            },
            {
                "timestamp": 25.0,
                "frame_id": 750,
                "player_id": 3,
                "previous_player_id": 2,
                "ball_position": [1050, 600],
                "duration": 12.5
            }
        ]
    
    def _generate_enhanced_stats(self) -> Dict[str, Any]:
        """Generate enhanced statistics."""
        return {
            'player_metrics': {
                1: {
                    'distance_covered_m': 1850.5 * 0.02,  # Convert pixels to meters
                    'avg_speed_kmh': 12.8,
                    'max_speed_kmh': 24.5,
                    'ball_touches': 45,
                    'total_frames': 800,
                    'time_played_seconds': 55.0
                },
                2: {
                    'distance_covered_m': 1645.2 * 0.02,
                    'avg_speed_kmh': 11.2,
                    'max_speed_kmh': 22.1,
                    'ball_touches': 38,
                    'total_frames': 750,
                    'time_played_seconds': 52.0
                },
                3: {
                    'distance_covered_m': 1520.8 * 0.02,
                    'avg_speed_kmh': 10.8,
                    'max_speed_kmh': 21.3,
                    'ball_touches': 32,
                    'total_frames': 700,
                    'time_played_seconds': 48.0
                }
            },
            'ball_metrics': {},
            'court_metrics': {}
        }


def monkey_patch_vision_for_ci():
    """Monkey patch vision modules to use stubs in CI environment."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from vision import processor
        # Replace the actual processor with our stub
        processor.BasketballVideoProcessor = VisionStub
        print("✅ Vision processing stubbed for CI")
    except ImportError:
        print("⚠️ Could not import vision module - may not be available in CI")
    
    try:
        from workers import video_processor
        # Also patch the worker
        video_processor.BasketballVideoProcessor = VisionStub
        print("✅ Worker vision processing stubbed for CI")
    except ImportError:
        print("⚠️ Could not import worker module")


if __name__ == "__main__":
    # Test the stub
    stub = VisionStub()
    result = stub.process_video("test_video.mp4")
    print("Stub result keys:", list(result.keys()))
    print("Enhanced stats:", json.dumps(result["enhanced_stats"], indent=2))