"""Database CRUD operations for basketball analysis."""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from . import db_models
from .models import VideoAnalysisResult, ShotAttempt, PossessionEvent, PlayerStats


# Analysis CRUD operations (existing)


def create_analysis(db: Session, analysis_id: str, video_path: str, 
                   confidence_threshold: float = 0.25, visualize: bool = True, 
                   save_frames: bool = False) -> db_models.Analysis:
    """Create a new analysis record."""
    db_analysis = db_models.Analysis(
        id=analysis_id,
        video_path=video_path,
        confidence_threshold=confidence_threshold,
        visualize=visualize,
        save_frames=save_frames,
        status="processing"
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis(db: Session, analysis_id: str) -> Optional[db_models.Analysis]:
    """Get analysis by ID."""
    return db.query(db_models.Analysis).filter(db_models.Analysis.id == analysis_id).first()


def get_analyses(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.Analysis]:
    """Get all analyses with pagination."""
    return db.query(db_models.Analysis).offset(skip).limit(limit).all()


def update_analysis_results(db: Session, analysis_id: str, results: VideoAnalysisResult) -> Optional[db_models.Analysis]:
    """Update analysis with complete results."""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
    
    # Update video metadata
    video_metadata = results.video_metadata
    db_analysis.fps = video_metadata.fps
    db_analysis.width = video_metadata.width
    db_analysis.height = video_metadata.height
    db_analysis.total_frames = video_metadata.total_frames
    db_analysis.duration_seconds = video_metadata.duration_seconds
    
    # Update processing summary
    processing_summary = results.processing_summary
    db_analysis.frames_processed = processing_summary.total_frames_processed
    db_analysis.frames_with_ball = processing_summary.frames_with_ball_detected
    db_analysis.unique_players = processing_summary.unique_players_tracked
    db_analysis.total_events = processing_summary.total_events_detected
    db_analysis.processing_time = processing_summary.processing_time_seconds
    
    # Store JSON data
    db_analysis.game_statistics = results.game_statistics.dict() if results.game_statistics else None
    db_analysis.processing_summary = processing_summary.dict()
    
    # Update status
    db_analysis.status = "completed"
    db_analysis.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Store detailed data
    _store_player_stats(db, analysis_id, results.game_statistics.player_stats if results.game_statistics else {})
    _store_shots(db, analysis_id, results.shot_attempts or [])
    _store_possessions(db, analysis_id, results.possession_events or [])
    _store_frame_data(db, analysis_id, results.frame_by_frame_data)
    
    db.refresh(db_analysis)
    return db_analysis


def update_analysis_error(db: Session, analysis_id: str, error_message: str) -> Optional[db_models.Analysis]:
    """Update analysis with error status."""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
    
    db_analysis.status = "failed"
    db_analysis.error_message = error_message
    db_analysis.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def delete_analysis(db: Session, analysis_id: str) -> bool:
    """Delete an analysis and all related data."""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return False
    
    db.delete(db_analysis)
    db.commit()
    return True


def get_analysis_shots(db: Session, analysis_id: str) -> List[db_models.Shot]:
    """Get all shots for an analysis."""
    return db.query(db_models.Shot).filter(db_models.Shot.analysis_id == analysis_id).all()


def get_analysis_players(db: Session, analysis_id: str) -> List[db_models.Player]:
    """Get all players for an analysis."""
    return db.query(db_models.Player).filter(db_models.Player.analysis_id == analysis_id).all()


def _store_player_stats(db: Session, analysis_id: str, player_stats: Dict[int, PlayerStats]):
    """Store player statistics."""
    for track_id, stats in player_stats.items():
        db_player = db_models.Player(
            analysis_id=analysis_id,
            track_id=track_id,
            shots_attempted=stats.shots_attempted,
            shots_made=stats.shots_made,
            field_goal_percentage=stats.field_goal_percentage,
            three_point_attempts=stats.three_point_attempts,
            three_point_made=stats.three_point_made,
            three_point_percentage=stats.three_point_percentage,
            possessions=stats.possessions,
            total_possession_time=stats.total_possession_time,
            avg_possession_time=stats.avg_possession_time,
            distance_covered=stats.distance_covered,
            time_in_zones=stats.time_in_zones
        )
        db.add(db_player)
    db.commit()


def _store_shots(db: Session, analysis_id: str, shots: List[ShotAttempt]):
    """Store shot attempts."""
    for shot in shots:
        db_shot = db_models.Shot(
            analysis_id=analysis_id,
            timestamp=shot.timestamp,
            frame_id=shot.frame_id,
            shooter_id=shot.shooter_id,
            shot_position_x=shot.shot_position[0],
            shot_position_y=shot.shot_position[1],
            shot_zone=shot.shot_zone,
            confidence=shot.confidence,
            made=shot.made,
            shot_value=shot.shot_value,
            trajectory=shot.trajectory
        )
        db.add(db_shot)
    db.commit()


def _store_possessions(db: Session, analysis_id: str, possessions: List[PossessionEvent]):
    """Store possession events."""
    for possession in possessions:
        db_possession = db_models.Possession(
            analysis_id=analysis_id,
            timestamp=possession.timestamp,
            frame_id=possession.frame_id,
            player_id=possession.player_id,
            previous_player_id=possession.previous_player_id,
            ball_position_x=possession.ball_position[0],
            ball_position_y=possession.ball_position[1],
            duration=possession.duration
        )
        db.add(db_possession)
    db.commit()


def _store_frame_data(db: Session, analysis_id: str, frame_data: List[Dict[str, Any]]):
    """Store frame-by-frame data."""
    for frame in frame_data:
        db_frame = db_models.FrameData(
            analysis_id=analysis_id,
            frame_id=frame.get('frame_id', 0),
            timestamp=frame.get('timestamp', 0.0),
            detections=frame.get('detections'),
            tracking_data=frame.get('tracking_data'),
            events=frame.get('events'),
            ball_analysis=frame.get('ball_analysis')
        )
        db.add(db_frame)
    db.commit()


def update_analysis_status(db: Session, analysis_id: str, status: str) -> Optional[db_models.Analysis]:
    """Update analysis status."""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
    
    db_analysis.status = status
    if status == "completed":
        db_analysis.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


# New CRUD operations for basketball stats platform

# Club operations
def create_club(db: Session, name: str, code: str, city: str = None) -> db_models.Club:
    """Create a new club."""
    db_club = db_models.Club(name=name, code=code, city=city)
    db.add(db_club)
    db.commit()
    db.refresh(db_club)
    return db_club


def get_club(db: Session, club_id: int) -> Optional[db_models.Club]:
    """Get club by ID."""
    return db.query(db_models.Club).filter(db_models.Club.id == club_id).first()


def get_clubs(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.Club]:
    """Get all clubs."""
    return db.query(db_models.Club).offset(skip).limit(limit).all()


# Player operations
def create_player(db: Session, club_id: int, name: str, jersey_number: int = None, 
                 position: str = None) -> db_models.ClubPlayer:
    """Create a new player."""
    db_player = db_models.ClubPlayer(
        club_id=club_id, 
        name=name, 
        jersey_number=jersey_number,
        position=position
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def get_player(db: Session, player_id: int) -> Optional[db_models.ClubPlayer]:
    """Get player by ID."""
    return db.query(db_models.ClubPlayer).filter(db_models.ClubPlayer.id == player_id).first()


def get_players_by_club(db: Session, club_id: int) -> List[db_models.ClubPlayer]:
    """Get all players for a club."""
    return db.query(db_models.ClubPlayer).filter(db_models.ClubPlayer.club_id == club_id).all()


# Match operations
def create_match(db: Session, home_club_id: int, away_club_id: int, 
                scheduled_date: datetime) -> db_models.Match:
    """Create a new match."""
    db_match = db_models.Match(
        home_club_id=home_club_id,
        away_club_id=away_club_id,
        scheduled_date=scheduled_date
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def get_match(db: Session, match_id: int) -> Optional[db_models.Match]:
    """Get match by ID."""
    return db.query(db_models.Match).filter(db_models.Match.id == match_id).first()


def get_matches(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.Match]:
    """Get all matches."""
    return db.query(db_models.Match).offset(skip).limit(limit).all()


def update_match_result(db: Session, match_id: int, home_score: int, away_score: int,
                       duration_minutes: int = None) -> Optional[db_models.Match]:
    """Update match with final result."""
    db_match = get_match(db, match_id)
    if not db_match:
        return None
    
    db_match.home_score = home_score
    db_match.away_score = away_score
    db_match.duration_minutes = duration_minutes
    db_match.status = "finished"
    db_match.played_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_match)
    return db_match


# Stats operations
def create_or_update_player_stats(db: Session, match_id: int, player_id: int, 
                                stats_data: Dict[str, Any]) -> db_models.StatPublic:
    """Create or update player stats for a match."""
    # Check if stats already exist
    existing_stats = db.query(db_models.StatPublic).filter(
        db_models.StatPublic.match_id == match_id,
        db_models.StatPublic.player_id == player_id
    ).first()
    
    if existing_stats:
        # Update existing stats
        for key, value in stats_data.items():
            if hasattr(existing_stats, key):
                setattr(existing_stats, key, value)
        existing_stats.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_stats)
        return existing_stats
    else:
        # Create new stats
        db_stats = db_models.StatPublic(
            match_id=match_id,
            player_id=player_id,
            **stats_data
        )
        db.add(db_stats)
        db.commit()
        db.refresh(db_stats)
        return db_stats


def get_player_match_stats(db: Session, player_id: int, match_id: int) -> Optional[db_models.StatPublic]:
    """Get player stats for a specific match."""
    return db.query(db_models.StatPublic).filter(
        db_models.StatPublic.player_id == player_id,
        db_models.StatPublic.match_id == match_id
    ).first()


def get_player_all_stats(db: Session, player_id: int) -> List[db_models.StatPublic]:
    """Get all stats for a player across all matches."""
    return db.query(db_models.StatPublic).filter(
        db_models.StatPublic.player_id == player_id
    ).all()


def get_match_all_stats(db: Session, match_id: int) -> List[db_models.StatPublic]:
    """Get all player stats for a match."""
    return db.query(db_models.StatPublic).filter(
        db_models.StatPublic.match_id == match_id
    ).all()


# User operations
def create_user(db: Session, email: str, username: str, hashed_password: str, 
               role: str = "public", club_id: int = None) -> db_models.User:
    """Create a new user."""
    db_user = db_models.User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
        club_id=club_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[db_models.User]:
    """Get user by email."""
    return db.query(db_models.User).filter(db_models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[db_models.User]:
    """Get user by username."""
    return db.query(db_models.User).filter(db_models.User.username == username).first()


# Job status operations
def create_job_status(db: Session, job_id: str, job_type: str, status: str = "queued",
                     metadata: Dict[str, Any] = None) -> db_models.JobStatus:
    """Create a new job status record."""
    db_job = db_models.JobStatus(
        id=job_id,
        job_type=job_type,
        status=status,
        metadata=metadata
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job_status(db: Session, job_id: str, status: str, progress: float = None,
                     result: Dict[str, Any] = None, error_message: str = None) -> Optional[db_models.JobStatus]:
    """Update job status."""
    db_job = db.query(db_models.JobStatus).filter(db_models.JobStatus.id == job_id).first()
    if not db_job:
        return None
    
    db_job.status = status
    if progress is not None:
        db_job.progress = progress
    if result is not None:
        db_job.result = result
    if error_message is not None:
        db_job.error_message = error_message
    
    if status == "started" and not db_job.started_at:
        db_job.started_at = datetime.utcnow()
    elif status in ["finished", "failed"]:
        db_job.finished_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_job)
    return db_job