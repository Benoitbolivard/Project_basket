"""Pydantic models for basketball analysis API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime


class BoundingBox(BaseModel):
    """Bounding box coordinates."""
    x1: float = Field(..., description="Left coordinate")
    y1: float = Field(..., description="Top coordinate") 
    x2: float = Field(..., description="Right coordinate")
    y2: float = Field(..., description="Bottom coordinate")


class Detection(BaseModel):
    """Object detection result."""
    bbox: List[float] = Field(..., description="Bounding box coordinates [x1, y1, x2, y2]")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    class_id: int = Field(..., description="Class ID")
    class_name: str = Field(..., description="Class name")
    center: Tuple[float, float] = Field(..., description="Center coordinates (x, y)")
    area: float = Field(..., description="Bounding box area")


class PlayerTracking(BaseModel):
    """Tracked player information."""
    track_id: int = Field(..., description="Unique tracking ID")
    bbox: List[float] = Field(..., description="Bounding box coordinates")
    center: Tuple[float, float] = Field(..., description="Center coordinates")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    time_since_update: int = Field(..., description="Frames since last update")
    hit_streak: int = Field(..., description="Consecutive detection streak")


class BallInfo(BaseModel):
    """Basketball information."""
    position: Tuple[float, float] = Field(..., description="Ball center position")
    bbox: List[float] = Field(..., description="Ball bounding box")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    speed: Optional[float] = Field(None, description="Ball speed (pixels/second)")
    direction: Optional[Tuple[float, float]] = Field(None, description="Movement direction vector")
    height_estimate: Optional[float] = Field(None, ge=0, le=1, description="Estimated height (normalized)")


class CourtZone(BaseModel):
    """Basketball court zone information."""
    normalized_coords: Tuple[float, float, float, float] = Field(..., description="Normalized coordinates (x1, y1, x2, y2)")
    pixel_coords: Tuple[int, int, int, int] = Field(..., description="Pixel coordinates (x1, y1, x2, y2)")
    active: bool = Field(True, description="Whether zone is active/detected")


class PossessionInfo(BaseModel):
    """Ball possession information."""
    player_id: Optional[int] = Field(None, description="Player ID with possession")
    ball_position: Optional[Tuple[float, float]] = Field(None, description="Ball position")
    confidence: float = Field(..., ge=0, le=1, description="Possession confidence")
    duration: Optional[float] = Field(None, description="Current possession duration (seconds)")


class ShotAttempt(BaseModel):
    """Shot attempt information."""
    timestamp: float = Field(..., description="Shot timestamp")
    frame_id: int = Field(..., description="Frame ID")
    shooter_id: Optional[int] = Field(None, description="Shooter player ID")
    shot_position: Tuple[float, float] = Field(..., description="Shot origin position")
    trajectory: List[Tuple[float, float]] = Field(..., description="Ball trajectory points")
    shot_zone: str = Field(..., description="Shot zone classification")
    confidence: float = Field(..., ge=0, le=1, description="Shot detection confidence")
    made: Optional[bool] = Field(None, description="Whether shot was made")
    shot_value: Optional[int] = Field(None, description="Point value (2 or 3)")


class PossessionEvent(BaseModel):
    """Possession change event."""
    timestamp: float = Field(..., description="Event timestamp")
    frame_id: int = Field(..., description="Frame ID")
    player_id: Optional[int] = Field(None, description="New possession player ID")
    previous_player_id: Optional[int] = Field(None, description="Previous possession player ID")
    ball_position: Tuple[float, float] = Field(..., description="Ball position at change")
    duration: float = Field(0.0, description="Previous possession duration")


class PlayerStats(BaseModel):
    """Player performance statistics."""
    track_id: int = Field(..., description="Player tracking ID")
    shots_attempted: int = Field(0, description="Total shots attempted")
    shots_made: int = Field(0, description="Total shots made")
    field_goal_percentage: float = Field(0.0, ge=0, le=100, description="Field goal percentage")
    three_point_attempts: int = Field(0, description="Three-point attempts")
    three_point_made: int = Field(0, description="Three-point shots made")
    three_point_percentage: float = Field(0.0, ge=0, le=100, description="Three-point percentage")
    possessions: int = Field(0, description="Number of possessions")
    total_possession_time: float = Field(0.0, description="Total possession time (seconds)")
    avg_possession_time: float = Field(0.0, description="Average possession duration")
    distance_covered: float = Field(0.0, description="Total distance covered (pixels)")
    time_in_zones: Dict[str, float] = Field(default_factory=dict, description="Time spent in court zones")


class GameEvent(BaseModel):
    """Game event information."""
    type: str = Field(..., description="Event type (shot_attempt, possession_change, etc.)")
    timestamp: float = Field(..., description="Event timestamp")
    frame_id: int = Field(..., description="Frame ID")
    data: Dict[str, Any] = Field(..., description="Event-specific data")


class FrameAnalysis(BaseModel):
    """Complete frame analysis result."""
    timestamp: float = Field(..., description="Frame timestamp")
    frame_id: int = Field(..., description="Frame ID")
    frame_shape: Tuple[int, int, int] = Field(..., description="Frame dimensions (height, width, channels)")
    
    # Detection results
    players: List[Detection] = Field(default_factory=list, description="Detected players")
    ball: Optional[Detection] = Field(None, description="Detected basketball")
    court_zones: Dict[str, CourtZone] = Field(default_factory=dict, description="Court zone information")
    
    # Tracking results
    tracked_players: List[PlayerTracking] = Field(default_factory=list, description="Tracked players")
    possession: Optional[PossessionInfo] = Field(None, description="Ball possession info")
    
    # Analytics results
    events: List[GameEvent] = Field(default_factory=list, description="Detected events")
    player_positions: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Player position data")
    ball_analysis: Optional[BallInfo] = Field(None, description="Ball movement analysis")


class VideoMetadata(BaseModel):
    """Video file metadata."""
    video_path: str = Field(..., description="Path to video file")
    fps: float = Field(..., description="Frames per second")
    width: int = Field(..., description="Video width")
    height: int = Field(..., description="Video height")
    total_frames: int = Field(..., description="Total number of frames")
    duration_seconds: float = Field(..., description="Video duration in seconds")


class ProcessingSummary(BaseModel):
    """Processing summary statistics."""
    total_frames_processed: int = Field(..., description="Total frames processed")
    frames_with_ball_detected: int = Field(..., description="Frames with ball detection")
    ball_detection_rate: float = Field(..., ge=0, le=1, description="Ball detection rate")
    total_events_detected: int = Field(..., description="Total events detected")
    unique_players_tracked: int = Field(..., description="Number of unique players tracked")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")


class ShotChart(BaseModel):
    """Shot chart data."""
    attempts_by_zone: Dict[str, int] = Field(default_factory=dict, description="Shot attempts by zone")
    makes_by_zone: Dict[str, int] = Field(default_factory=dict, description="Made shots by zone")
    shot_positions: List[Dict[str, Any]] = Field(default_factory=list, description="Individual shot positions")


class GameStatistics(BaseModel):
    """Complete game statistics."""
    game_duration: float = Field(0.0, description="Game duration in seconds")
    total_shots: int = Field(0, description="Total shot attempts")
    possession_changes: int = Field(0, description="Number of possession changes")
    player_stats: Dict[int, PlayerStats] = Field(default_factory=dict, description="Player statistics")
    shot_chart: ShotChart = Field(default_factory=ShotChart, description="Shot chart data")
    possession_summary: Dict[str, Any] = Field(default_factory=dict, description="Possession summary")


class VideoAnalysisResult(BaseModel):
    """Complete video analysis result."""
    video_metadata: VideoMetadata = Field(..., description="Video metadata")
    processing_summary: ProcessingSummary = Field(..., description="Processing summary")
    game_statistics: GameStatistics = Field(..., description="Game statistics")
    frame_by_frame_data: List[Dict[str, Any]] = Field(default_factory=list, description="Frame-by-frame data")
    player_performance: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Player performance metrics")
    
    # Optional detailed data
    shot_attempts: Optional[List[ShotAttempt]] = Field(None, description="All shot attempts")
    possession_events: Optional[List[PossessionEvent]] = Field(None, description="All possession events")


class AnalysisRequest(BaseModel):
    """Request for video analysis."""
    video_path: str = Field(..., description="Path to video file")
    output_video_path: Optional[str] = Field(None, description="Output video path")
    output_json_path: Optional[str] = Field(None, description="Output JSON path")
    visualize: bool = Field(True, description="Create visualized output")
    save_frames: bool = Field(False, description="Save individual frames")
    confidence_threshold: float = Field(0.25, ge=0, le=1, description="Detection confidence threshold")


class AnalysisResponse(BaseModel):
    """Response for video analysis."""
    success: bool = Field(..., description="Whether analysis succeeded")
    message: str = Field(..., description="Status message")
    analysis_id: Optional[str] = Field(None, description="Analysis ID")
    results: Optional[VideoAnalysisResult] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")


class LiveAnalysisConfig(BaseModel):
    """Configuration for live analysis."""
    camera_index: int = Field(0, description="Camera device index")
    display: bool = Field(True, description="Display live analysis")
    confidence_threshold: float = Field(0.25, ge=0, le=1, description="Detection confidence threshold")
    save_output: bool = Field(False, description="Save analysis output")


class CurrentStats(BaseModel):
    """Current processing statistics."""
    status: str = Field(..., description="Current status")
    frames_processed: int = Field(0, description="Frames processed so far")
    current_game_stats: Optional[GameStatistics] = Field(None, description="Current game statistics")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")