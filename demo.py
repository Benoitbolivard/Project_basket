#!/usr/bin/env python3
"""
Basketball Analytics Demo Script
Demonstrates the complete Phase 1 functionality.
"""

import cv2
import json
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from vision.analytics import BasketballAnalytics
from vision.detector import BasketballDetector
from vision.processor import BasketballVideoProcessor
from vision.tracker import BasketballTracker


def create_demo_video(output_path: str = "demo_basketball.mp4", duration: int = 10):
    """
    Create a simple demo video for testing basketball analytics.
    
    Args:
        output_path: Path for output video
        duration: Video duration in seconds
    """
    print(f"Creating demo video: {output_path}")
    
    width, height = 640, 480
    fps = 30
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # Create a simple basketball court background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (34, 139, 34)  # Green court background
        
        # Draw court lines
        cv2.rectangle(frame, (50, 50), (width-50, height-50), (255, 255, 255), 2)  # Court boundary
        cv2.circle(frame, (width//2, height//2), 50, (255, 255, 255), 2)  # Center circle
        cv2.line(frame, (width//2, 50), (width//2, height-50), (255, 255, 255), 2)  # Half court line
        
        # Add some moving "players" (simple rectangles)
        t = frame_num / fps
        
        # Player 1
        p1_x = int(100 + 50 * np.sin(t))
        p1_y = int(150 + 30 * np.cos(t))
        cv2.rectangle(frame, (p1_x, p1_y), (p1_x+30, p1_y+60), (255, 0, 0), -1)
        
        # Player 2
        p2_x = int(200 + 40 * np.sin(t * 1.5))
        p2_y = int(250 + 25 * np.cos(t * 1.5))
        cv2.rectangle(frame, (p2_x, p2_y), (p2_x+30, p2_y+60), (0, 255, 0), -1)
        
        # Moving "ball"
        ball_x = int(width//2 + 100 * np.sin(t * 2))
        ball_y = int(height//2 + 50 * np.cos(t * 3))
        cv2.circle(frame, (ball_x, ball_y), 8, (255, 165, 0), -1)
        
        out.write(frame)
    
    out.release()
    print(f"Demo video created: {output_path}")


def demo_detection():
    """Demonstrate basketball detection capabilities."""
    print("\n=== Basketball Detection Demo ===")
    
    detector = BasketballDetector(confidence_threshold=0.3)
    
    # Create a test frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Add some visual elements that might be detected
    cv2.rectangle(frame, (100, 100), (150, 200), (255, 0, 0), -1)  # Person-like rectangle
    cv2.circle(frame, (300, 300), 15, (255, 165, 0), -1)  # Ball-like circle
    
    # Run detection
    start_time = time.time()
    results = detector.detect_frame(frame, 1.0)
    detection_time = time.time() - start_time
    
    print(f"Detection completed in {detection_time:.3f}s")
    print(f"Frame ID: {results['frame_id']}")
    print(f"Players detected: {len(results['players'])}")
    print(f"Ball detected: {'Yes' if results['ball'] else 'No'}")
    print(f"Court zones defined: {len(results['court_zones'])}")
    
    # Create visualization
    vis_frame = detector.visualize_detections(frame, results)
    cv2.imwrite("demo_detection.jpg", vis_frame)
    print("Detection visualization saved: demo_detection.jpg")


def demo_tracking():
    """Demonstrate basketball tracking capabilities."""
    print("\n=== Basketball Tracking Demo ===")
    
    detector = BasketballDetector(confidence_threshold=0.3)
    tracker = BasketballTracker()
    
    # Simulate multiple frames
    for frame_id in range(5):
        # Create frame with moving elements
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add moving player-like rectangle
        x = 100 + frame_id * 20
        y = 150
        cv2.rectangle(frame, (x, y), (x+30, y+60), (255, 0, 0), -1)
        
        # Add moving ball
        ball_x = 300 + frame_id * 10
        ball_y = 200
        cv2.circle(frame, (ball_x, ball_y), 12, (255, 165, 0), -1)
        
        # Detect and track
        detections = detector.detect_frame(frame, frame_id * 0.033)  # 30 FPS
        tracking_results = tracker.update_tracks(detections, frame)
        
        print(f"Frame {frame_id + 1}:")
        print(f"  Tracked players: {len(tracking_results['tracked_players'])}")
        print(f"  Ball detected: {'Yes' if tracking_results['ball_info'] else 'No'}")
        
        possession = tracking_results.get('possession', {})
        if possession.get('player_id'):
            print(f"  Possession: Player {possession['player_id']}")
        
        # Create visualization for last frame
        if frame_id == 4:
            vis_frame = tracker.visualize_tracks(frame, tracking_results)
            cv2.imwrite("demo_tracking.jpg", vis_frame)
            print("Tracking visualization saved: demo_tracking.jpg")


def demo_analytics():
    """Demonstrate basketball analytics capabilities."""
    print("\n=== Basketball Analytics Demo ===")
    
    detector = BasketballDetector(confidence_threshold=0.3)
    tracker = BasketballTracker()
    analytics = BasketballAnalytics()
    
    # Simulate game scenario
    for frame_id in range(10):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Simulate player movement and ball interaction
        timestamp = frame_id * 0.1
        
        # Player 1
        p1_x = 100 + frame_id * 5
        p1_y = 150
        cv2.rectangle(frame, (p1_x, p1_y), (p1_x+30, p1_y+60), (255, 0, 0), -1)
        
        # Ball movement (simulate shot)
        if frame_id < 5:
            ball_x = p1_x + 15  # Near player
            ball_y = p1_y + 30
        else:
            ball_x = p1_x + 15 + (frame_id - 5) * 20  # Moving away (shot)
            ball_y = p1_y + 30 - (frame_id - 5) * 15  # Upward trajectory
        
        cv2.circle(frame, (ball_x, ball_y), 12, (255, 165, 0), -1)
        
        # Process through pipeline
        detections = detector.detect_frame(frame, timestamp)
        tracking_results = tracker.update_tracks(detections, frame)
        analytics_results = analytics.analyze_frame(tracking_results)
        
        # Check for events
        events = analytics_results.get('events', [])
        if events:
            for event in events:
                print(f"Frame {frame_id + 1}: {event['type']} detected!")
    
    # Get final statistics
    game_stats = analytics.get_game_statistics()
    print("\nGame Statistics:")
    print(f"  Total shots: {game_stats['total_shots']}")
    print(f"  Possession changes: {game_stats['possession_changes']}")
    print(f"  Players tracked: {len(game_stats['player_stats'])}")


def demo_full_processor():
    """Demonstrate the complete video processor."""
    print("\n=== Complete Video Processor Demo ===")
    
    # Create demo video first
    demo_video_path = "demo_basketball.mp4"
    create_demo_video(demo_video_path, duration=3)  # Short demo
    
    # Process the video
    processor = BasketballVideoProcessor(
        confidence_threshold=0.2,
        output_dir="demo_output"
    )
    
    print("Processing demo video...")
    start_time = time.time()
    
    results = processor.process_video(
        video_path=demo_video_path,
        output_video_path="demo_output/analyzed_basketball.mp4",
        output_json_path="demo_output/analysis_results.json",
        visualize=True,
        save_frames=False
    )
    
    processing_time = time.time() - start_time
    
    print(f"Video processing completed in {processing_time:.1f}s")
    print(f"Processed {results['processing_summary']['total_frames_processed']} frames")
    print(f"Ball detection rate: {results['processing_summary']['ball_detection_rate']:.1%}")
    print(f"Unique players tracked: {results['processing_summary']['unique_players_tracked']}")
    
    # Display some analytics
    game_stats = results['game_statistics']
    print(f"Total events detected: {results['processing_summary']['total_events_detected']}")
    
    print("\nOutput files created:")
    print("  - demo_output/analyzed_basketball.mp4 (annotated video)")
    print("  - demo_output/analysis_results.json (complete analysis)")


def demo_api_usage():
    """Demonstrate API usage patterns."""
    print("\n=== API Usage Demo ===")
    
    # This would typically be done with HTTP requests
    from backend.app.models import AnalysisRequest
    
    # Create a sample request
    request = AnalysisRequest(
        video_path="demo_basketball.mp4",
        output_video_path="api_output.mp4",
        confidence_threshold=0.25,
        visualize=True
    )
    
    print("Sample API request structure:")
    print(json.dumps(request.dict(), indent=2))
    
    # Show what the response would look like
    print("\nAPI endpoints available:")
    print("  POST /analyze/video - Analyze video file")
    print("  POST /analyze/upload - Upload and analyze video")
    print("  GET  /analyze/{id} - Get analysis results")
    print("  GET  /analyze/{id}/download - Download JSON results")
    print("  GET  /stats/current - Get current processing stats")
    print("  POST /analyze/live - Start live camera analysis")


def main():
    """Run all demos."""
    print("🏀 Basketball Analytics Phase 1 - Complete Demo")
    print("=" * 50)
    
    try:
        # Create output directory
        Path("demo_output").mkdir(exist_ok=True)
        
        # Run individual component demos
        demo_detection()
        demo_tracking()
        demo_analytics()
        demo_full_processor()
        demo_api_usage()
        
        print("\n✅ All demos completed successfully!")
        print("\nPhase 1 Features Implemented:")
        print("  ✓ Basketball-specific YOLO detection (players, ball, court)")
        print("  ✓ DeepSORT tracking with unique player IDs")
        print("  ✓ Basketball analytics (shots, possession, zones)")
        print("  ✓ JSON export with timestamps and coordinates")
        print("  ✓ FastAPI backend with comprehensive endpoints")
        print("  ✓ Integrated video processing pipeline")
        
        print("\nFiles created:")
        print("  - demo_detection.jpg")
        print("  - demo_tracking.jpg")
        print("  - demo_basketball.mp4")
        print("  - demo_output/ (directory with analysis results)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()