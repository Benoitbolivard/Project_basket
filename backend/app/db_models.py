"""SQLAlchemy database models."""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .database import Base


class VideoAnalysis(Base):
    """Main video analysis record."""
    __tablename__ = "video_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Video metadata
    video_path = Column(String, nullable=False)
    video_fps = Column(Float, nullable=False)
    video_width = Column(Integer, nullable=False)
    video_height = Column(Integer, nullable=False)
    video_total_frames = Column(Integer, nullable=False)
    video_duration_seconds = Column(Float, nullable=False)
    
    # Processing summary
    total_frames_processed = Column(Integer, nullable=False)
    frames_with_ball_detected = Column(Integer, default=0)
    ball_detection_rate = Column(Float, default=0.0)
    total_events_detected = Column(Integer, default=0)
    unique_players_tracked = Column(Integer, default=0)
    processing_time_seconds = Column(Float)
    
    # Game statistics
    game_duration = Column(Float, default=0.0)
    total_shots = Column(Integer, default=0)
    possession_changes = Column(Integer, default=0)
    
    # JSON fields for complex data
    frame_by_frame_data = Column(JSON, default=list)
    player_performance = Column(JSON, default=dict)
    shot_chart_data = Column(JSON, default=dict)
    possession_summary = Column(JSON, default=dict)
    
    # Relationships
    shot_attempts = relationship("ShotAttempt", back_populates="analysis", cascade="all, delete-orphan")
    possession_events = relationship("PossessionEvent", back_populates="analysis", cascade="all, delete-orphan")
    player_stats = relationship("PlayerStat", back_populates="analysis", cascade="all, delete-orphan")


class ShotAttempt(Base):
    """Individual shot attempt record."""
    __tablename__ = "shot_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("video_analyses.id"), nullable=False)
    
    timestamp = Column(Float, nullable=False)
    frame_id = Column(Integer, nullable=False)
    shooter_id = Column(Integer)
    shot_position_x = Column(Float, nullable=False)
    shot_position_y = Column(Float, nullable=False)
    trajectory = Column(JSON, default=list)  # List of trajectory points
    shot_zone = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    made = Column(Boolean)
    shot_value = Column(Integer)
    
    # Relationship
    analysis = relationship("VideoAnalysis", back_populates="shot_attempts")


class PossessionEvent(Base):
    """Ball possession change event."""
    __tablename__ = "possession_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("video_analyses.id"), nullable=False)
    
    timestamp = Column(Float, nullable=False)
    frame_id = Column(Integer, nullable=False)
    player_id = Column(Integer)
    previous_player_id = Column(Integer)
    ball_position_x = Column(Float, nullable=False)
    ball_position_y = Column(Float, nullable=False)
    duration = Column(Float, default=0.0)
    
    # Relationship
    analysis = relationship("VideoAnalysis", back_populates="possession_events")


class PlayerStat(Base):
    """Player performance statistics."""
    __tablename__ = "player_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("video_analyses.id"), nullable=False)
    
    track_id = Column(Integer, nullable=False)
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
    time_in_zones = Column(JSON, default=dict)
    
    # Relationship
    analysis = relationship("VideoAnalysis", back_populates="player_stats")