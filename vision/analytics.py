"""Basketball analytics for advanced game analysis."""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class ShotAttempt:
    """Data class for shot attempt information."""
    timestamp: float
    frame_id: int
    shooter_id: Optional[int]
    shot_position: Tuple[float, float]
    trajectory: List[Tuple[float, float]]
    shot_zone: str
    confidence: float
    made: Optional[bool] = None


@dataclass
class PossessionEvent:
    """Data class for possession change events."""
    timestamp: float
    frame_id: int
    player_id: Optional[int]
    previous_player_id: Optional[int]
    ball_position: Tuple[float, float]
    duration: float = 0.0


class BasketballAnalytics:
    """Advanced basketball analytics processor."""
    
    # Shot zones (normalized coordinates relative to one basket)
    SHOT_ZONES = {
        'restricted_area': {'coords': (0.45, 0.88, 0.55, 1.0), 'value': 2},
        'paint': {'coords': (0.35, 0.81, 0.65, 1.0), 'value': 2},
        'left_corner_three': {'coords': (0.0, 0.88, 0.22, 1.0), 'value': 3},
        'right_corner_three': {'coords': (0.78, 0.88, 1.0, 1.0), 'value': 3},
        'left_wing_three': {'coords': (0.15, 0.65, 0.35, 0.85), 'value': 3},
        'right_wing_three': {'coords': (0.65, 0.65, 0.85, 0.85), 'value': 3},
        'top_three': {'coords': (0.35, 0.5, 0.65, 0.75), 'value': 3},
        'mid_range': {'coords': (0.25, 0.75, 0.75, 0.9), 'value': 2},
    }
    
    def __init__(self):
        """Initialize basketball analytics."""
        self.shot_attempts = []
        self.possession_events = []
        self.player_analytics = defaultdict(lambda: {
            'shots_attempted': 0,
            'shots_made': 0,
            'field_goal_percentage': 0.0,
            'three_point_attempts': 0,
            'three_point_made': 0,
            'three_point_percentage': 0.0,
            'possessions': 0,
            'total_possession_time': 0.0,
            'avg_possession_time': 0.0,
            'distance_covered': 0.0,
            'time_in_zones': defaultdict(float),
            'heat_map': defaultdict(int)
        })
        
        self.game_state = {
            'current_possession': None,
            'possession_start_time': None,
            'last_ball_position': None,
            'game_duration': 0.0
        }
    
    def analyze_frame(self, tracking_results: Dict) -> Dict:
        """
        Analyze a single frame for basketball events.
        
        Args:
            tracking_results: Results from tracker
            
        Returns:
            Analytics results for the frame
        """
        frame_analytics = {
            'timestamp': tracking_results['timestamp'],
            'frame_id': tracking_results['frame_id'],
            'events': [],
            'player_positions': {},
            'ball_analysis': {},
            'possession_analysis': {}
        }
        
        # Analyze player positions and movements
        for player in tracking_results['tracked_players']:
            player_id = player['track_id']
            position = player['center']
            
            frame_analytics['player_positions'][player_id] = {
                'position': position,
                'zone': self._determine_court_zone(position, tracking_results['court_zones']),
                'bbox': player['bbox']
            }
            
            # Update player analytics
            self._update_player_position_analytics(player_id, position, tracking_results['timestamp'])
        
        # Analyze ball and possession
        if tracking_results.get('ball_info'):
            ball_analysis = self._analyze_ball_movement(tracking_results)
            frame_analytics['ball_analysis'] = ball_analysis
            
            # Check for shot attempts
            shot_attempt = self._detect_shot_attempt(tracking_results)
            if shot_attempt:
                frame_analytics['events'].append({
                    'type': 'shot_attempt',
                    'data': shot_attempt
                })
                self.shot_attempts.append(shot_attempt)
        
        # Analyze possession changes
        possession_analysis = self._analyze_possession(tracking_results)
        frame_analytics['possession_analysis'] = possession_analysis
        
        if possession_analysis.get('possession_change'):
            frame_analytics['events'].append({
                'type': 'possession_change',
                'data': possession_analysis['possession_change']
            })
        
        return frame_analytics
    
    def _determine_court_zone(self, position: Tuple[float, float], court_zones: Dict) -> str:
        """Determine which court zone a position is in."""
        x, y = position
        
        # Check against defined court zones
        for zone_name, zone_info in court_zones.items():
            if zone_info.get('active', False):
                x1, y1, x2, y2 = zone_info['pixel_coords']
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return zone_name
        
        return 'unknown'
    
    def _update_player_position_analytics(self, player_id: int, position: Tuple[float, float], 
                                        timestamp: float):
        """Update analytics for player position."""
        analytics = self.player_analytics[player_id]
        
        # Update heat map (discretize position for heat map)
        heat_x = int(position[0] // 50) * 50
        heat_y = int(position[1] // 50) * 50
        analytics['heat_map'][(heat_x, heat_y)] += 1
        
        # Calculate distance covered (if we have previous position)
        if hasattr(self, '_last_positions') and player_id in self._last_positions:
            last_pos = self._last_positions[player_id]
            distance = np.sqrt((position[0] - last_pos[0])**2 + (position[1] - last_pos[1])**2)
            analytics['distance_covered'] += distance
        
        # Store current position for next frame
        if not hasattr(self, '_last_positions'):
            self._last_positions = {}
        self._last_positions[player_id] = position
    
    def _analyze_ball_movement(self, tracking_results: Dict) -> Dict:
        """Analyze ball movement patterns."""
        ball = tracking_results['ball_info']
        ball_position = ball['center']
        timestamp = tracking_results['timestamp']
        
        analysis = {
            'position': ball_position,
            'speed': 0.0,
            'direction': None,
            'height_estimate': 0.0
        }
        
        if self.game_state['last_ball_position']:
            # Calculate speed (pixels per second)
            last_pos = self.game_state['last_ball_position']['position']
            last_time = self.game_state['last_ball_position']['timestamp']
            
            if timestamp > last_time:
                distance = np.sqrt((ball_position[0] - last_pos[0])**2 + 
                                 (ball_position[1] - last_pos[1])**2)
                time_diff = timestamp - last_time
                analysis['speed'] = distance / time_diff
                
                # Direction vector
                analysis['direction'] = (
                    (ball_position[0] - last_pos[0]) / distance if distance > 0 else 0,
                    (ball_position[1] - last_pos[1]) / distance if distance > 0 else 0
                )
        
        # Estimate height based on ball size (larger = closer/lower)
        ball_area = ball['area']
        analysis['height_estimate'] = max(0, 1.0 - (ball_area / 5000))  # Normalized height estimate
        
        self.game_state['last_ball_position'] = {
            'position': ball_position,
            'timestamp': timestamp
        }
        
        return analysis
    
    def _detect_shot_attempt(self, tracking_results: Dict) -> Optional[ShotAttempt]:
        """Detect shot attempts based on ball trajectory and game state."""
        if not tracking_results.get('ball_info'):
            return None
        
        ball_analysis = tracking_results.get('ball_analysis', {})
        
        # Simple shot detection: high upward speed + possession info
        if (ball_analysis.get('speed', 0) > 200 and  # Fast movement
            ball_analysis.get('direction', [0, 0])[1] < -0.5):  # Upward movement
            
            ball_position = tracking_results['ball_info']['center']
            shot_zone = self._classify_shot_zone(ball_position)
            
            # Try to determine shooter from possession
            shooter_id = None
            possession = tracking_results.get('possession', {})
            if possession.get('player_id'):
                shooter_id = possession['player_id']
            
            shot_attempt = ShotAttempt(
                timestamp=tracking_results['timestamp'],
                frame_id=tracking_results['frame_id'],
                shooter_id=shooter_id,
                shot_position=ball_position,
                trajectory=[ball_position],  # Would be enhanced with full trajectory
                shot_zone=shot_zone,
                confidence=0.7
            )
            
            # Update player shot statistics
            if shooter_id:
                analytics = self.player_analytics[shooter_id]
                analytics['shots_attempted'] += 1
                if shot_zone in ['left_corner_three', 'right_corner_three', 'left_wing_three', 
                               'right_wing_three', 'top_three']:
                    analytics['three_point_attempts'] += 1
            
            return shot_attempt
        
        return None
    
    def _classify_shot_zone(self, position: Tuple[float, float]) -> str:
        """Classify the shot zone based on position."""
        x, y = position
        
        # Convert to normalized coordinates (assuming standard court proportions)
        # This is simplified - in practice, would need court detection/calibration
        for zone_name, zone_info in self.SHOT_ZONES.items():
            x1, y1, x2, y2 = zone_info['coords']
            # Convert normalized to approximate pixel coordinates (would need actual court mapping)
            if 0.4 <= x/1000 <= 0.6 and 0.8 <= y/1000 <= 1.0:  # Simplified check
                return zone_name
        
        return 'mid_range'  # Default zone
    
    def _analyze_possession(self, tracking_results: Dict) -> Dict:
        """Analyze possession changes and duration."""
        possession_info = tracking_results.get('possession', {})
        current_player = possession_info.get('player_id')
        timestamp = tracking_results['timestamp']
        
        analysis = {
            'current_possession': current_player,
            'possession_duration': 0.0,
            'possession_change': None
        }
        
        # Check for possession change
        if current_player != self.game_state['current_possession']:
            # Possession change detected
            if self.game_state['current_possession'] is not None:
                # Calculate possession duration
                duration = timestamp - self.game_state['possession_start_time']
                
                # Update previous player's possession analytics
                prev_player = self.game_state['current_possession']
                if prev_player:
                    analytics = self.player_analytics[prev_player]
                    analytics['total_possession_time'] += duration
                    analytics['possessions'] += 1
                    analytics['avg_possession_time'] = (
                        analytics['total_possession_time'] / analytics['possessions']
                    )
                
                # Create possession change event
                possession_event = PossessionEvent(
                    timestamp=timestamp,
                    frame_id=tracking_results['frame_id'],
                    player_id=current_player,
                    previous_player_id=prev_player,
                    ball_position=possession_info.get('ball_position', (0, 0)),
                    duration=duration
                )
                
                self.possession_events.append(possession_event)
                analysis['possession_change'] = possession_event
            
            # Update game state
            self.game_state['current_possession'] = current_player
            self.game_state['possession_start_time'] = timestamp
        
        # Calculate current possession duration
        if self.game_state['possession_start_time']:
            analysis['possession_duration'] = timestamp - self.game_state['possession_start_time']
        
        return analysis
    
    def get_game_statistics(self) -> Dict:
        """Get comprehensive game statistics."""
        return {
            'game_duration': self.game_state.get('game_duration', 0.0),
            'total_shots': len(self.shot_attempts),
            'possession_changes': len(self.possession_events),
            'player_stats': dict(self.player_analytics),
            'shot_chart': self._generate_shot_chart(),
            'possession_summary': self._generate_possession_summary()
        }
    
    def _generate_shot_chart(self) -> Dict:
        """Generate shot chart data."""
        shot_chart = {
            'attempts_by_zone': defaultdict(int),
            'makes_by_zone': defaultdict(int),
            'shot_positions': []
        }
        
        for shot in self.shot_attempts:
            shot_chart['attempts_by_zone'][shot.shot_zone] += 1
            if shot.made:
                shot_chart['makes_by_zone'][shot.shot_zone] += 1
            
            shot_chart['shot_positions'].append({
                'position': shot.shot_position,
                'zone': shot.shot_zone,
                'made': shot.made,
                'shooter_id': shot.shooter_id
            })
        
        return shot_chart
    
    def _generate_possession_summary(self) -> Dict:
        """Generate possession summary statistics."""
        if not self.possession_events:
            return {}
        
        durations = [event.duration for event in self.possession_events if event.duration > 0]
        
        return {
            'total_possessions': len(self.possession_events),
            'average_possession_duration': np.mean(durations) if durations else 0.0,
            'longest_possession': max(durations) if durations else 0.0,
            'shortest_possession': min(durations) if durations else 0.0
        }
    
    def visualize_analytics(self, frame: np.ndarray, frame_analytics: Dict) -> np.ndarray:
        """
        Visualize analytics on the frame.
        
        Args:
            frame: Input frame
            frame_analytics: Analytics results for the frame
            
        Returns:
            Annotated frame with analytics
        """
        annotated_frame = frame.copy()
        
        # Draw possession info
        possession = frame_analytics.get('possession_analysis', {})
        if possession.get('current_possession'):
            cv2.putText(annotated_frame, 
                       f"Possession: Player {possession['current_possession']} "
                       f"({possession.get('possession_duration', 0):.1f}s)",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw shot zones
        self._draw_shot_zones(annotated_frame)
        
        # Highlight events
        for event in frame_analytics.get('events', []):
            if event['type'] == 'shot_attempt':
                shot = event['data']
                pos = shot.shot_position
                cv2.circle(annotated_frame, (int(pos[0]), int(pos[1])), 20, (0, 255, 0), 3)
                cv2.putText(annotated_frame, "SHOT!", (int(pos[0]), int(pos[1]-25)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return annotated_frame
    
    def _draw_shot_zones(self, frame: np.ndarray):
        """Draw shot zones on the frame (simplified visualization)."""
        h, w = frame.shape[:2]
        
        # Draw a simplified court representation
        # Paint area
        cv2.rectangle(frame, (int(w*0.35), int(h*0.8)), (int(w*0.65), h), (100, 100, 255), 2)
        
        # Three-point line (simplified arc)
        cv2.ellipse(frame, (int(w*0.5), h), (int(w*0.25), int(h*0.25)), 0, 180, 360, (255, 100, 100), 2)
        
        # Free throw line
        cv2.line(frame, (int(w*0.35), int(h*0.85)), (int(w*0.65), int(h*0.85)), (255, 255, 100), 2)