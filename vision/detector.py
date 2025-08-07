"""Basketball-specific YOLO detection module."""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import time


class BasketballDetector:
    """YOLO-based detector optimized for basketball scenarios."""
    
    # Basketball-specific class mapping
    BASKETBALL_CLASSES = {
        0: 'person',        # Players, referees, coaches
        32: 'sports ball',  # Basketball
    }
    
    # Court zones mapping (normalized coordinates)
    COURT_ZONES = {
        'three_point_left': (0.0, 0.3, 0.25, 0.7),
        'three_point_right': (0.75, 0.3, 1.0, 0.7),
        'paint_left': (0.0, 0.35, 0.15, 0.65),
        'paint_right': (0.85, 0.35, 1.0, 0.65),
        'mid_court': (0.25, 0.2, 0.75, 0.8),
        'free_throw_left': (0.0, 0.4, 0.19, 0.6),
        'free_throw_right': (0.81, 0.4, 1.0, 0.6),
    }
    
    def __init__(self, model_path: str = 'yolov8n.pt', confidence_threshold: float = 0.25):
        """
        Initialize the basketball detector.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.frame_count = 0
        
    def detect_frame(self, frame: np.ndarray, timestamp: float = None) -> Dict:
        """
        Detect basketball-relevant objects in a single frame.
        
        Args:
            frame: Input video frame
            timestamp: Frame timestamp
            
        Returns:
            Detection results with bounding boxes and classifications
        """
        if timestamp is None:
            timestamp = time.time()
            
        self.frame_count += 1
        
        # Run YOLO detection
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        detections = {
            'frame_id': self.frame_count,
            'timestamp': timestamp,
            'frame_shape': frame.shape,
            'players': [],
            'ball': None,
            'court_objects': [],
            'court_zones': self._analyze_court_zones(frame)
        }
        
        # Process detections
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in self.BASKETBALL_CLASSES:
                        bbox = box.xyxy[0].cpu().numpy()
                        detection_info = {
                            'bbox': bbox.tolist(),
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': self.BASKETBALL_CLASSES[class_id],
                            'center': self._get_bbox_center(bbox),
                            'area': self._get_bbox_area(bbox)
                        }
                        
                        # Classify as player or ball
                        if class_id == 0:  # person
                            if self._is_likely_player(detection_info, frame.shape):
                                detections['players'].append(detection_info)
                        elif class_id == 32:  # sports ball
                            if self._is_likely_basketball(detection_info):
                                detections['ball'] = detection_info
        
        return detections
    
    def _get_bbox_center(self, bbox: np.ndarray) -> Tuple[float, float]:
        """Calculate the center point of a bounding box."""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _get_bbox_area(self, bbox: np.ndarray) -> float:
        """Calculate the area of a bounding box."""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def _is_likely_player(self, detection: Dict, frame_shape: Tuple) -> bool:
        """
        Determine if a person detection is likely a basketball player.
        
        Args:
            detection: Detection information
            frame_shape: Shape of the input frame
            
        Returns:
            True if likely a player
        """
        # Filter by size (players should be reasonably sized)
        bbox = detection['bbox']
        height = bbox[3] - bbox[1]
        width = bbox[2] - bbox[0]
        
        # Players should have a certain aspect ratio (taller than wide)
        aspect_ratio = height / width if width > 0 else 0
        
        # Filter criteria
        min_height = frame_shape[0] * 0.1  # At least 10% of frame height
        max_height = frame_shape[0] * 0.8  # At most 80% of frame height
        min_aspect_ratio = 1.2  # Players are typically taller than wide
        max_aspect_ratio = 4.0  # Not too thin
        
        return (min_height <= height <= max_height and 
                min_aspect_ratio <= aspect_ratio <= max_aspect_ratio and
                detection['confidence'] > 0.3)
    
    def _is_likely_basketball(self, detection: Dict) -> bool:
        """
        Determine if a sports ball detection is likely a basketball.
        
        Args:
            detection: Detection information
            
        Returns:
            True if likely a basketball
        """
        # Basketball should have high confidence and reasonable size
        return (detection['confidence'] > 0.4 and 
                detection['area'] > 100 and  # Minimum size
                detection['area'] < 10000)   # Maximum size
    
    def _analyze_court_zones(self, frame: np.ndarray) -> Dict:
        """
        Analyze court zones based on frame content.
        
        Args:
            frame: Input video frame
            
        Returns:
            Court zone information
        """
        h, w = frame.shape[:2]
        zones = {}
        
        for zone_name, (x1, y1, x2, y2) in self.COURT_ZONES.items():
            # Convert normalized coordinates to pixel coordinates
            pixel_coords = (
                int(x1 * w), int(y1 * h),
                int(x2 * w), int(y2 * h)
            )
            zones[zone_name] = {
                'normalized_coords': (x1, y1, x2, y2),
                'pixel_coords': pixel_coords,
                'active': True  # Could be enhanced with court detection
            }
        
        return zones
    
    def visualize_detections(self, frame: np.ndarray, detections: Dict) -> np.ndarray:
        """
        Draw detection results on frame for visualization.
        
        Args:
            frame: Input frame
            detections: Detection results
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw players
        for player in detections['players']:
            bbox = player['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Player {player['confidence']:.2f}", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw ball
        if detections['ball']:
            ball = detections['ball']
            bbox = ball['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(annotated_frame, f"Ball {ball['confidence']:.2f}", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Draw court zones (optional)
        for zone_name, zone_info in detections['court_zones'].items():
            if zone_info['active']:
                x1, y1, x2, y2 = zone_info['pixel_coords']
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
                cv2.putText(annotated_frame, zone_name, (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        return annotated_frame