"""RQ Worker for video processing jobs."""

import os
import sys
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from vision.processor import BasketballVideoProcessor
from backend.app.database import SessionLocal
from backend.app import crud, db_models


def process_video_job(analysis_id: str, video_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video in background job and update database with enhanced stats.
    
    Args:
        analysis_id: Analysis ID
        video_path: Path to video file
        config: Processing configuration
        
    Returns:
        Processing results
    """
    db = SessionLocal()
    
    try:
        # Update job status to started
        crud.update_analysis_status(db, analysis_id, "processing")
        
        # Get processor
        processor = BasketballVideoProcessor(
            confidence_threshold=config.get('confidence_threshold', 0.25)
        )
        
        # Process video
        results = processor.process_video(
            video_path=video_path,
            output_video_path=config.get('output_video_path'),
            output_json_path=config.get('output_json_path'),
            visualize=config.get('visualize', True),
            save_frames=config.get('save_frames', False)
        )
        
        # Calculate enhanced stats
        enhanced_stats = calculate_enhanced_stats(results)
        
        # Update analysis with results and enhanced stats
        results['enhanced_stats'] = enhanced_stats
        crud.update_analysis_results(db, analysis_id, results)
        crud.update_analysis_status(db, analysis_id, "completed")
        
        return {
            'status': 'completed',
            'analysis_id': analysis_id,
            'enhanced_stats': enhanced_stats
        }
        
    except Exception as e:
        # Update database with error
        crud.update_analysis_error(db, analysis_id, str(e))
        crud.update_analysis_status(db, analysis_id, "failed")
        raise
    finally:
        db.close()


def calculate_enhanced_stats(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate enhanced statistics from vision processing results.
    
    This includes:
    - Distance covered (meters) and speed (km/h) per player
    - Ball touches based on proximity detection
    - Time spent in different court zones
    
    Args:
        results: Raw vision processing results
        
    Returns:
        Enhanced statistics
    """
    enhanced_stats = {
        'player_metrics': {},
        'ball_metrics': {},
        'court_metrics': {}
    }
    
    try:
        video_metadata = results.get('video_metadata', {})
        fps = video_metadata.get('fps', 30)
        frame_data = results.get('frame_by_frame_data', [])
        
        if not frame_data:
            return enhanced_stats
            
        # Player tracking data
        player_positions = {}  # {player_id: [(x, y, timestamp), ...]}
        ball_touches = {}      # {player_id: count}
        zone_times = {}        # {player_id: {zone: seconds}}
        
        # Process frame-by-frame data
        for frame in frame_data:
            timestamp = frame.get('timestamp', 0)
            tracked_players = frame.get('tracked_players', [])
            ball_analysis = frame.get('ball_analysis')
            
            # Track player positions
            for player in tracked_players:
                player_id = player.get('track_id')
                if player_id is not None:
                    center = player.get('center', [0, 0])
                    if player_id not in player_positions:
                        player_positions[player_id] = []
                    player_positions[player_id].append((center[0], center[1], timestamp))
            
            # Detect ball touches (ball within 1m/~50 pixels of player)
            if ball_analysis:
                ball_pos = ball_analysis.get('position', [0, 0])
                for player in tracked_players:
                    player_id = player.get('track_id')
                    player_center = player.get('center', [0, 0])
                    
                    # Calculate distance (approximate 1m = 50 pixels)
                    distance = ((ball_pos[0] - player_center[0])**2 + (ball_pos[1] - player_center[1])**2)**0.5
                    if distance < 50:  # Within ~1 meter
                        if player_id not in ball_touches:
                            ball_touches[player_id] = 0
                        ball_touches[player_id] += 1
        
        # Calculate distance and speed for each player
        for player_id, positions in player_positions.items():
            if len(positions) < 2:
                continue
                
            total_distance_pixels = 0
            speeds = []
            
            for i in range(1, len(positions)):
                prev_x, prev_y, prev_t = positions[i-1]
                curr_x, curr_y, curr_t = positions[i]
                
                # Distance in pixels
                distance_pixels = ((curr_x - prev_x)**2 + (curr_y - prev_y)**2)**0.5
                total_distance_pixels += distance_pixels
                
                # Speed calculation (pixels per second)
                time_diff = curr_t - prev_t
                if time_diff > 0:
                    speed_pixels_per_sec = distance_pixels / time_diff
                    speeds.append(speed_pixels_per_sec)
            
            # Convert to real world units (approximate: 1 pixel ≈ 0.02m on basketball court)
            pixels_to_meters = 0.02
            distance_meters = total_distance_pixels * pixels_to_meters
            
            # Convert speed to km/h
            avg_speed_pixels_per_sec = sum(speeds) / len(speeds) if speeds else 0
            avg_speed_kmh = avg_speed_pixels_per_sec * pixels_to_meters * 3.6  # m/s to km/h
            max_speed_kmh = max(speeds) * pixels_to_meters * 3.6 if speeds else 0
            
            enhanced_stats['player_metrics'][player_id] = {
                'distance_covered_m': round(distance_meters, 2),
                'avg_speed_kmh': round(avg_speed_kmh, 2),
                'max_speed_kmh': round(max_speed_kmh, 2),
                'ball_touches': ball_touches.get(player_id, 0),
                'total_frames': len(positions),
                'time_played_seconds': positions[-1][2] - positions[0][2] if positions else 0
            }
    
    except Exception as e:
        print(f"Error calculating enhanced stats: {e}")
        enhanced_stats['error'] = str(e)
    
    return enhanced_stats


if __name__ == "__main__":
    # This can be run as a standalone worker
    from rq import Worker, Queue, Connection
    import redis
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_conn = redis.from_url(redis_url)
    
    with Connection(redis_conn):
        worker = Worker(['video_processing'])
        worker.work()