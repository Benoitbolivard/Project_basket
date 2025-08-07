"""Database models for basketball analysis."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# New models for the basketball stats platform
class Club(Base):
    """Club/team entity."""
    __tablename__ = "clubs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)  # Short code like "LAL", "GSW"
    city = Column(String, nullable=True)
    founded_year = Column(Integer, nullable=True)
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    players = relationship("ClubPlayer", back_populates="club")
    home_matches = relationship("Match", foreign_keys="Match.home_club_id", back_populates="home_club")
    away_matches = relationship("Match", foreign_keys="Match.away_club_id", back_populates="away_club")


class ClubPlayer(Base):
    """Player entity for a club."""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    name = Column(String, nullable=False)
    jersey_number = Column(Integer, nullable=True)
    position = Column(String, nullable=True)  # PG, SG, SF, PF, C
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    birthdate = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="players")
    stats = relationship("StatPublic", back_populates="player")


class Match(Base):
    """Basketball match/game entity."""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    home_club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    away_club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    played_date = Column(DateTime, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, playing, finished, cancelled
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    video_url = Column(String, nullable=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    home_club = relationship("Club", foreign_keys=[home_club_id])
    away_club = relationship("Club", foreign_keys=[away_club_id])
    analysis = relationship("Analysis")
    stats = relationship("StatPublic", back_populates="match")


class StatPublic(Base):
    """Public statistics for players in matches."""
    __tablename__ = "stats_public"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Basic stats
    minutes_played = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    three_points_made = Column(Integer, default=0)
    three_points_attempted = Column(Integer, default=0)
    free_throws_made = Column(Integer, default=0)
    free_throws_attempted = Column(Integer, default=0)
    rebounds = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    steals = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)
    
    # Advanced stats from vision processing
    distance_covered_m = Column(Float, default=0.0)  # Distance in meters
    avg_speed_kmh = Column(Float, default=0.0)       # Average speed in km/h
    max_speed_kmh = Column(Float, default=0.0)       # Peak speed in km/h
    ball_touches = Column(Integer, default=0)         # Number of ball touches
    time_with_ball = Column(Float, default=0.0)      # Time with ball in seconds
    
    # Zone-based data
    time_in_paint = Column(Float, default=0.0)       # Seconds in paint area
    time_in_three_zone = Column(Float, default=0.0)  # Seconds in 3-point area
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="stats")
    player = relationship("ClubPlayer", back_populates="stats")


class User(Base):
    """User entity for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="public")  # public, club
    is_active = Column(Boolean, default=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    club = relationship("Club")


class JobStatus(Base):
    """RQ job status tracking."""
    __tablename__ = "job_status"
    
    id = Column(String, primary_key=True, index=True)  # RQ job ID
    status = Column(String, nullable=False)  # queued, started, finished, failed
    job_type = Column(String, nullable=False)  # video_processing, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    metadata = Column(JSON, nullable=True)  # Additional job metadata


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