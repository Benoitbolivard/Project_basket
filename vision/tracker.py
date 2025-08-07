"""DeepSORT tracking integration for basketball players."""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from deep_sort_realtime.deepsort_tracker import DeepSort


class BasketballTracker:
    """DeepSORT-based tracker for basketball players with unique IDs."""
    
    def __init__(self, max_age: int = 30, n_init: int = 3):
        """
        Initialize the basketball tracker.
        
        Args:
            max_age: Maximum frames to keep track alive without detection
            n_init: Number of consecutive detections before track is confirmed
        """
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            max_cosine_distance=0.2,
            nn_budget=100
        )
        
        self.player_stats = {}  # Store player statistics
        self.ball_trajectory = []  # Store ball trajectory history
        self.possession_history = []  # Store possession changes
        
    def update_tracks(self, detections: Dict, frame: np.ndarray) -> Dict:
        """
        Update tracks with new detections.
        
        Args:
            detections: Detection results from YOLO
            frame: Current video frame
            
        Returns:
            Updated tracking results with unique IDs
        """
        # Prepare detection data for DeepSORT
        detection_list = []
        
        # Convert player detections to DeepSORT format
        for player in detections['players']:
            bbox = player['bbox']
            confidence = player['confidence']
            
            # DeepSORT expects (x, y, w, h) format
            x1, y1, x2, y2 = bbox
            w = x2 - x1
            h = y2 - y1
            detection_list.append(([x1, y1, w, h], confidence, 'player'))
        
        # Update tracker
        tracks = self.tracker.update_tracks(detection_list, frame=frame)
        
        # Process tracking results
        tracking_results = {
            'frame_id': detections['frame_id'],
            'timestamp': detections['timestamp'],
            'tracked_players': [],
            'ball_info': detections['ball'],
            'court_zones': detections['court_zones']
        }
        
        # Process confirmed tracks
        for track in tracks:
            if not track.is_confirmed():
                continue
                
            track_id = track.track_id
            bbox = track.to_ltrb()  # Get bounding box in (left, top, right, bottom) format
            
            player_info = {
                'track_id': track_id,
                'bbox': bbox.tolist(),
                'center': self._get_bbox_center(bbox),
                'confidence': track.get_det_conf() if hasattr(track, 'get_det_conf') else 0.5,
                'time_since_update': track.time_since_update,
                'hit_streak': track.hit_streak
            }
            
            # Update player statistics
            self._update_player_stats(track_id, player_info, detections['timestamp'])
            
            tracking_results['tracked_players'].append(player_info)
        
        # Analyze ball and possession
        self._update_ball_analysis(detections, tracking_results)
        
        return tracking_results
    
    def _get_bbox_center(self, bbox: np.ndarray) -> Tuple[float, float]:
        """Calculate the center point of a bounding box."""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _update_player_stats(self, track_id: int, player_info: Dict, timestamp: float):
        """Update statistics for a tracked player."""
        if track_id not in self.player_stats:
            self.player_stats[track_id] = {
                'first_seen': timestamp,
                'positions': [],
                'court_zones_visited': set(),
                'total_distance': 0.0,
                'possession_time': 0.0,
                'shots_taken': 0
            }
        
        stats = self.player_stats[track_id]
        center = player_info['center']
        
        # Update position history
        if stats['positions']:
            last_pos = stats['positions'][-1]
            distance = np.sqrt((center[0] - last_pos[0])**2 + (center[1] - last_pos[1])**2)
            stats['total_distance'] += distance
        
        stats['positions'].append(center)
        stats['last_seen'] = timestamp
        
        # Limit position history to prevent memory issues
        if len(stats['positions']) > 100:
            stats['positions'] = stats['positions'][-50:]
    
    def _update_ball_analysis(self, detections: Dict, tracking_results: Dict):
        """Analyze ball movement and possession."""
        ball = detections['ball']
        
        if ball:
            ball_center = ball['center']
            self.ball_trajectory.append({
                'timestamp': detections['timestamp'],
                'position': ball_center,
                'frame_id': detections['frame_id']
            })
            
            # Limit trajectory history
            if len(self.ball_trajectory) > 50:
                self.ball_trajectory = self.ball_trajectory[-30:]
            
            # Determine possession
            possession_player = self._determine_possession(ball_center, tracking_results['tracked_players'])
            
            tracking_results['possession'] = {
                'player_id': possession_player,
                'ball_position': ball_center,
                'confidence': 0.8 if possession_player else 0.0
            }
            
            # Update possession history
            if self.possession_history and self.possession_history[-1]['player_id'] != possession_player:
                # Possession change
                self.possession_history.append({
                    'timestamp': detections['timestamp'],
                    'player_id': possession_player,
                    'frame_id': detections['frame_id'],
                    'ball_position': ball_center
                })
            elif not self.possession_history:
                # First possession record
                self.possession_history.append({
                    'timestamp': detections['timestamp'],
                    'player_id': possession_player,
                    'frame_id': detections['frame_id'],
                    'ball_position': ball_center
                })
        else:
            tracking_results['possession'] = {
                'player_id': None,
                'ball_position': None,
                'confidence': 0.0
            }
    
    def _determine_possession(self, ball_center: Tuple[float, float], players: List[Dict]) -> Optional[int]:
        """
        Determine which player has possession of the ball.
        
        Args:
            ball_center: Ball center coordinates
            players: List of tracked players
            
        Returns:
            Track ID of player with possession, or None
        """
        if not players:
            return None
        
        possession_threshold = 80  # pixels
        closest_player = None
        min_distance = float('inf')
        
        for player in players:
            player_center = player['center']
            distance = np.sqrt((ball_center[0] - player_center[0])**2 + 
                             (ball_center[1] - player_center[1])**2)
            
            if distance < min_distance and distance < possession_threshold:
                min_distance = distance
                closest_player = player['track_id']
        
        return closest_player
    
    def detect_shot_attempt(self, frame_window: int = 10) -> Optional[Dict]:
        """
        Detect potential shot attempts based on ball trajectory.
        
        Args:
            frame_window: Number of frames to analyze for shot detection
            
        Returns:
            Shot information if detected, None otherwise
        """
        if len(self.ball_trajectory) < frame_window:
            return None
        
        recent_trajectory = self.ball_trajectory[-frame_window:]
        
        # Analyze trajectory for upward movement (potential shot)
        y_positions = [pos['position'][1] for pos in recent_trajectory]
        
        # Check for significant upward movement followed by downward
        if len(y_positions) >= 5:
            first_half = y_positions[:len(y_positions)//2]
            second_half = y_positions[len(y_positions)//2:]
            
            # Ball going up then down (simplified shot detection)
            avg_first = np.mean(first_half)
            avg_second = np.mean(second_half)
            
            if avg_first > avg_second and (avg_first - avg_second) > 50:
                # Potential shot detected
                shot_info = {
                    'timestamp': recent_trajectory[0]['timestamp'],
                    'frame_id': recent_trajectory[0]['frame_id'],
                    'shooter_position': recent_trajectory[0]['position'],
                    'trajectory': [(pos['position'][0], pos['position'][1]) for pos in recent_trajectory],
                    'confidence': 0.7
                }
                
                # Try to identify shooter
                if self.possession_history:
                    last_possession = self.possession_history[-1]
                    shot_info['shooter_id'] = last_possession['player_id']
                
                return shot_info
        
        return None
    
    def get_player_stats(self, track_id: int) -> Optional[Dict]:
        """Get statistics for a specific player."""
        return self.player_stats.get(track_id)
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all tracked players."""
        return {
            'players': self.player_stats,
            'possession_history': self.possession_history[-10:],  # Last 10 possessions
            'ball_trajectory': self.ball_trajectory[-20:],  # Last 20 ball positions
            'total_players': len(self.player_stats)
        }
    
    def visualize_tracks(self, frame: np.ndarray, tracking_results: Dict) -> np.ndarray:
        """
        Draw tracking results on frame for visualization.
        
        Args:
            frame: Input frame
            tracking_results: Tracking results
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw tracked players
        for player in tracking_results['tracked_players']:
            bbox = player['bbox']
            track_id = player['track_id']
            x1, y1, x2, y2 = map(int, bbox)
            
            # Different colors for different players
            color = self._get_player_color(track_id)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw player ID and info
            label = f"Player {track_id}"
            cv2.putText(annotated_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw ball and possession
        if tracking_results['ball_info']:
            ball = tracking_results['ball_info']
            bbox = ball['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            
            # Show possession
            possession = tracking_results.get('possession', {})
            if possession.get('player_id'):
                cv2.putText(annotated_frame, f"Possession: Player {possession['player_id']}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw ball trajectory
        if len(self.ball_trajectory) > 1:
            points = [pos['position'] for pos in self.ball_trajectory[-10:]]
            for i in range(1, len(points)):
                pt1 = (int(points[i-1][0]), int(points[i-1][1]))
                pt2 = (int(points[i][0]), int(points[i][1]))
                cv2.line(annotated_frame, pt1, pt2, (255, 255, 0), 2)
        
        return annotated_frame
    
    def _get_player_color(self, track_id: int) -> Tuple[int, int, int]:
        """Get a consistent color for a player based on their track ID."""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
            (0, 128, 128), (128, 128, 0)
        ]
        return colors[track_id % len(colors)]