"""Main video processor that integrates detection, tracking, and analytics."""

import cv2
import numpy as np
import json
import time
from typing import Dict, List, Optional, Union
from pathlib import Path

from .detector import BasketballDetector
from .tracker import BasketballTracker
from .analytics import BasketballAnalytics


class BasketballVideoProcessor:
    """
    Main processor for basketball video analysis.
    Integrates YOLO detection, DeepSORT tracking, and basketball analytics.
    """
    
    def __init__(self, 
                 model_path: str = 'yolov8n.pt',
                 confidence_threshold: float = 0.25,
                 output_dir: str = 'output'):
        """
        Initialize the basketball video processor.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Detection confidence threshold
            output_dir: Directory for output files
        """
        self.detector = BasketballDetector(model_path, confidence_threshold)
        self.tracker = BasketballTracker()
        self.analytics = BasketballAnalytics()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.processing_results = []
        self.video_metadata = {}
    
    def process_video(self, 
                     video_path: str,
                     output_video_path: Optional[str] = None,
                     output_json_path: Optional[str] = None,
                     visualize: bool = True,
                     save_frames: bool = False) -> Dict:
        """
        Process a basketball video with complete analysis pipeline.
        
        Args:
            video_path: Path to input video
            output_video_path: Path for output video (optional)
            output_json_path: Path for JSON output (optional)
            visualize: Whether to create visualized output video
            save_frames: Whether to save individual analyzed frames
            
        Returns:
            Complete processing results
        """
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.video_metadata = {
            'video_path': video_path,
            'fps': fps,
            'width': width,
            'height': height,
            'total_frames': total_frames,
            'duration_seconds': total_frames / fps if fps > 0 else 0
        }
        
        # Setup output video if requested
        writer = None
        if output_video_path and visualize:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        print(f"Processing video: {video_path}")
        print(f"Resolution: {width}x{height}, FPS: {fps}, Total frames: {total_frames}")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate timestamp
            timestamp = frame_count / fps if fps > 0 else frame_count
            
            # Process frame through pipeline
            frame_results = self.process_frame(frame, timestamp)
            self.processing_results.append(frame_results)
            
            # Visualization and output
            if visualize:
                annotated_frame = self.visualize_frame(frame, frame_results)
                
                if writer:
                    writer.write(annotated_frame)
                
                if save_frames:
                    frame_path = self.output_dir / f"frame_{frame_count:06d}.jpg"
                    cv2.imwrite(str(frame_path), annotated_frame)
            
            frame_count += 1
            
            # Progress update
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / frame_count) * (total_frames - frame_count)
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames}), "
                      f"ETA: {eta:.1f}s")
        
        # Cleanup
        cap.release()
        if writer:
            writer.release()
        
        processing_time = time.time() - start_time
        print(f"Processing completed in {processing_time:.1f}s")
        
        # Generate final results
        final_results = self.generate_final_results()
        
        # Save JSON output
        if output_json_path:
            self.save_json_results(final_results, output_json_path)
        else:
            # Auto-generate JSON filename
            json_path = self.output_dir / f"analysis_{int(time.time())}.json"
            self.save_json_results(final_results, str(json_path))
        
        return final_results
    
    def process_frame(self, frame: np.ndarray, timestamp: float) -> Dict:
        """
        Process a single frame through the complete pipeline.
        
        Args:
            frame: Input video frame
            timestamp: Frame timestamp in seconds
            
        Returns:
            Complete frame analysis results
        """
        # 1. Detection
        detections = self.detector.detect_frame(frame, timestamp)
        
        # 2. Tracking
        tracking_results = self.tracker.update_tracks(detections, frame)
        
        # 3. Analytics
        analytics_results = self.analytics.analyze_frame(tracking_results)
        
        # Combine all results
        frame_results = {
            'timestamp': timestamp,
            'frame_id': detections['frame_id'],
            'detections': detections,
            'tracking': tracking_results,
            'analytics': analytics_results,
            'processing_metadata': {
                'detection_count': len(detections['players']) + (1 if detections['ball'] else 0),
                'tracked_players': len(tracking_results['tracked_players']),
                'events_detected': len(analytics_results.get('events', []))
            }
        }
        
        return frame_results
    
    def visualize_frame(self, frame: np.ndarray, frame_results: Dict) -> np.ndarray:
        """
        Create a comprehensive visualization of frame analysis.
        
        Args:
            frame: Original frame
            frame_results: Complete frame analysis
            
        Returns:
            Annotated frame with all visualizations
        """
        # Start with detector visualization
        annotated_frame = self.detector.visualize_detections(
            frame, frame_results['detections']
        )
        
        # Add tracking visualization
        annotated_frame = self.tracker.visualize_tracks(
            annotated_frame, frame_results['tracking']
        )
        
        # Add analytics visualization
        annotated_frame = self.analytics.visualize_analytics(
            annotated_frame, frame_results['analytics']
        )
        
        # Add general info overlay
        info_text = [
            f"Frame: {frame_results['frame_id']}",
            f"Time: {frame_results['timestamp']:.1f}s",
            f"Players: {frame_results['processing_metadata']['tracked_players']}",
            f"Events: {frame_results['processing_metadata']['events_detected']}"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(annotated_frame, text, (10, frame.shape[0] - 100 + i*20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated_frame
    
    def generate_final_results(self) -> Dict:
        """
        Generate comprehensive final results from all processed frames.
        
        Returns:
            Complete analysis results
        """
        # Get game statistics from analytics
        game_stats = self.analytics.get_game_statistics()
        
        # Get tracking statistics
        tracking_stats = self.tracker.get_all_stats()
        
        # Compile frame-by-frame data
        frame_data = []
        for frame_result in self.processing_results:
            frame_summary = {
                'timestamp': frame_result['timestamp'],
                'frame_id': frame_result['frame_id'],
                'players_detected': len(frame_result['detections']['players']),
                'ball_detected': frame_result['detections']['ball'] is not None,
                'tracked_players': [
                    {
                        'track_id': p['track_id'],
                        'position': p['center'],
                        'bbox': p['bbox']
                    }
                    for p in frame_result['tracking']['tracked_players']
                ],
                'events': frame_result['analytics'].get('events', []),
                'possession': frame_result['tracking'].get('possession', {}),
                'ball_position': (
                    frame_result['detections']['ball']['center'] 
                    if frame_result['detections']['ball'] else None
                )
            }
            frame_data.append(frame_summary)
        
        # Summary statistics
        total_frames = len(self.processing_results)
        frames_with_ball = sum(1 for f in frame_data if f['ball_detected'])
        total_events = sum(len(f['events']) for f in frame_data)
        
        final_results = {
            'video_metadata': self.video_metadata,
            'processing_summary': {
                'total_frames_processed': total_frames,
                'frames_with_ball_detected': frames_with_ball,
                'ball_detection_rate': frames_with_ball / total_frames if total_frames > 0 else 0,
                'total_events_detected': total_events,
                'unique_players_tracked': len(tracking_stats['players'])
            },
            'game_statistics': game_stats,
            'tracking_statistics': tracking_stats,
            'frame_by_frame_data': frame_data,
            'shot_chart': game_stats.get('shot_chart', {}),
            'possession_analysis': game_stats.get('possession_summary', {}),
            'player_performance': {
                player_id: {
                    'shots_attempted': stats['shots_attempted'],
                    'shots_made': stats['shots_made'],
                    'field_goal_percentage': stats['field_goal_percentage'],
                    'three_point_percentage': stats['three_point_percentage'],
                    'total_distance': stats['distance_covered'],
                    'possession_time': stats['total_possession_time'],
                    'avg_possession_duration': stats['avg_possession_time']
                }
                for player_id, stats in game_stats.get('player_stats', {}).items()
            }
        }
        
        return final_results
    
    def save_json_results(self, results: Dict, output_path: str):
        """
        Save analysis results to JSON file with proper formatting.
        
        Args:
            results: Analysis results to save
            output_path: Output JSON file path
        """
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        # Convert and save
        json_safe_results = convert_numpy(results)
        
        with open(output_path, 'w') as f:
            json.dump(json_safe_results, f, indent=2, default=str)
        
        print(f"Analysis results saved to: {output_path}")
    
    def process_live_stream(self, camera_index: int = 0, display: bool = True) -> None:
        """
        Process live video stream from camera.
        
        Args:
            camera_index: Camera device index
            display: Whether to display live analysis
        """
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise ValueError(f"Could not open camera: {camera_index}")
        
        print("Starting live analysis. Press 'q' to quit.")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate timestamp
            timestamp = time.time() - start_time
            
            # Process frame
            frame_results = self.process_frame(frame, timestamp)
            
            if display:
                # Visualize and display
                annotated_frame = self.visualize_frame(frame, frame_results)
                cv2.imshow('Basketball Analysis', annotated_frame)
                
                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_count += 1
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"Live analysis completed. Processed {frame_count} frames.")
    
    def get_current_stats(self) -> Dict:
        """Get current processing statistics."""
        if not self.processing_results:
            return {"status": "No frames processed yet"}
        
        return {
            "frames_processed": len(self.processing_results),
            "current_game_stats": self.analytics.get_game_statistics(),
            "current_tracking_stats": self.tracker.get_all_stats()
        }