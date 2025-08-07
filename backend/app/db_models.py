"""Database models for basketball analysis."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Analysis(Base):
    """Analysis session record."""
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, index=True)
    video_path = Column(String, nullable=False)
    status = Column(String, default="processing")  # processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Video metadata
    fps = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    total_frames = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Processing summary
    frames_processed = Column(Integer, default=0)
    frames_with_ball = Column(Integer, default=0)
    unique_players = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    processing_time = Column(Float, nullable=True)
    
    # Configuration
    confidence_threshold = Column(Float, default=0.25)
    visualize = Column(Boolean, default=True)
    save_frames = Column(Boolean, default=False)
    
    # JSON results
    game_statistics = Column(JSON, nullable=True)
    processing_summary = Column(JSON, nullable=True)
    
    # Relationships
    players = relationship("Player", back_populates="analysis", cascade="all, delete-orphan")
    shots = relationship("Shot", back_populates="analysis", cascade="all, delete-orphan")
    possessions = relationship("Possession", back_populates="analysis", cascade="all, delete-orphan")
    frames = relationship("FrameData", back_populates="analysis", cascade="all, delete-orphan")


class Player(Base):
    """Player statistics for an analysis."""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    
    # Statistics
    shots_attempted = Column(Integer, default=0)
    shots_made = Column(Integer, default=0)
    field_goal_percentage = Column(Float, default=0.0)
    three_point_attempts = Column(Integer, default=0)
    three_point_made = Column(Integer, default=0)
    three_point_percentage = Column(Float, default=0.0)
    possessions = Column(Integer, default=0)
    total_possession_time = Column(Float, default=0.0)
    avg_possession_time = Column(Float, default=0.0)
    distance_covered = Column(Float, default=0.0)
    
    # Zone time data
    time_in_zones = Column(JSON, nullable=True)
    
    analysis = relationship("Analysis", back_populates="players")


class Shot(Base):
    """Shot attempt record."""
    __tablename__ = "shots"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    
    # Shot details
    timestamp = Column(Float, nullable=False)
    frame_id = Column(Integer, nullable=False)
    shooter_id = Column(Integer, nullable=True)
    shot_position_x = Column(Float, nullable=False)
    shot_position_y = Column(Float, nullable=False)
    shot_zone = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    made = Column(Boolean, nullable=True)
    shot_value = Column(Integer, nullable=True)  # 2 or 3 points
    
    # Trajectory data
    trajectory = Column(JSON, nullable=True)
    
    analysis = relationship("Analysis", back_populates="shots")


class Possession(Base):
    """Ball possession change event."""
    __tablename__ = "possessions"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    
    # Event details
    timestamp = Column(Float, nullable=False)
    frame_id = Column(Integer, nullable=False)
    player_id = Column(Integer, nullable=True)
    previous_player_id = Column(Integer, nullable=True)
    ball_position_x = Column(Float, nullable=False)
    ball_position_y = Column(Float, nullable=False)
    duration = Column(Float, default=0.0)
    
    analysis = relationship("Analysis", back_populates="possessions")


class FrameData(Base):
    """Frame-by-frame analysis data."""
    __tablename__ = "frame_data"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    
    # Frame details
    frame_id = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    
    # Detection and tracking data (stored as JSON for flexibility)
    detections = Column(JSON, nullable=True)
    tracking_data = Column(JSON, nullable=True)
    events = Column(JSON, nullable=True)
    ball_analysis = Column(JSON, nullable=True)
    
    analysis = relationship("Analysis", back_populates="frames")