"""CRUD operations for database models."""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid

from . import db_models
from .models import VideoAnalysisResult, ShotAttempt, PossessionEvent, PlayerStats


def create_video_analysis(db: Session, analysis_result: VideoAnalysisResult) -> db_models.VideoAnalysis:
    """Create a new video analysis record."""
    
    # Extract video metadata
    video_metadata = analysis_result.video_metadata
    processing_summary = analysis_result.processing_summary
    game_statistics = analysis_result.game_statistics
    
    # Create main analysis record
    db_analysis = db_models.VideoAnalysis(
        video_path=video_metadata.video_path,
        video_fps=video_metadata.fps,
        video_width=video_metadata.width,
        video_height=video_metadata.height,
        video_total_frames=video_metadata.total_frames,
        video_duration_seconds=video_metadata.duration_seconds,
        
        total_frames_processed=processing_summary.total_frames_processed,
        frames_with_ball_detected=processing_summary.frames_with_ball_detected,
        ball_detection_rate=processing_summary.ball_detection_rate,
        total_events_detected=processing_summary.total_events_detected,
        unique_players_tracked=processing_summary.unique_players_tracked,
        processing_time_seconds=processing_summary.processing_time_seconds,
        
        game_duration=game_statistics.game_duration,
        total_shots=game_statistics.total_shots,
        possession_changes=game_statistics.possession_changes,
        
        frame_by_frame_data=analysis_result.frame_by_frame_data,
        player_performance=analysis_result.player_performance,
        shot_chart_data=game_statistics.shot_chart.model_dump() if game_statistics.shot_chart else {},
        possession_summary=game_statistics.possession_summary,
    )
    
    db.add(db_analysis)
    db.flush()  # Get the ID without committing
    
    # Add shot attempts if present
    if analysis_result.shot_attempts:
        for shot in analysis_result.shot_attempts:
            db_shot = db_models.ShotAttempt(
                analysis_id=db_analysis.id,
                timestamp=shot.timestamp,
                frame_id=shot.frame_id,
                shooter_id=shot.shooter_id,
                shot_position_x=shot.shot_position[0],
                shot_position_y=shot.shot_position[1],
                trajectory=shot.trajectory,
                shot_zone=shot.shot_zone,
                confidence=shot.confidence,
                made=shot.made,
                shot_value=shot.shot_value,
            )
            db.add(db_shot)
    
    # Add possession events if present
    if analysis_result.possession_events:
        for possession in analysis_result.possession_events:
            db_possession = db_models.PossessionEvent(
                analysis_id=db_analysis.id,
                timestamp=possession.timestamp,
                frame_id=possession.frame_id,
                player_id=possession.player_id,
                previous_player_id=possession.previous_player_id,
                ball_position_x=possession.ball_position[0],
                ball_position_y=possession.ball_position[1],
                duration=possession.duration,
            )
            db.add(db_possession)
    
    # Add player statistics
    for track_id, stats in game_statistics.player_stats.items():
        # Convert track_id to int if it's a string
        track_id_int = int(track_id) if isinstance(track_id, str) else track_id
        
        # Create PlayerStats object if stats is a dict
        if isinstance(stats, dict):
            player_stats_obj = PlayerStats(**stats)
        else:
            player_stats_obj = stats
            
        db_player_stat = db_models.PlayerStat(
            analysis_id=db_analysis.id,
            track_id=track_id_int,
            shots_attempted=player_stats_obj.shots_attempted,
            shots_made=player_stats_obj.shots_made,
            field_goal_percentage=player_stats_obj.field_goal_percentage,
            three_point_attempts=player_stats_obj.three_point_attempts,
            three_point_made=player_stats_obj.three_point_made,
            three_point_percentage=player_stats_obj.three_point_percentage,
            possessions=player_stats_obj.possessions,
            total_possession_time=player_stats_obj.total_possession_time,
            avg_possession_time=player_stats_obj.avg_possession_time,
            distance_covered=player_stats_obj.distance_covered,
            time_in_zones=player_stats_obj.time_in_zones,
        )
        db.add(db_player_stat)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_video_analysis(db: Session, analysis_id: str) -> Optional[db_models.VideoAnalysis]:
    """Get a video analysis by ID."""
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        return db.query(db_models.VideoAnalysis).filter(
            db_models.VideoAnalysis.id == analysis_uuid
        ).first()
    except ValueError:
        return None


def get_video_analyses(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.VideoAnalysis]:
    """Get all video analyses with pagination."""
    return db.query(db_models.VideoAnalysis).offset(skip).limit(limit).all()


def delete_video_analysis(db: Session, analysis_id: str) -> bool:
    """Delete a video analysis and all related data."""
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        analysis = db.query(db_models.VideoAnalysis).filter(
            db_models.VideoAnalysis.id == analysis_uuid
        ).first()
        
        if analysis:
            db.delete(analysis)
            db.commit()
            return True
        return False
    except ValueError:
        return False


def get_shot_attempts(db: Session, analysis_id: str) -> List[db_models.ShotAttempt]:
    """Get all shot attempts for an analysis."""
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        return db.query(db_models.ShotAttempt).filter(
            db_models.ShotAttempt.analysis_id == analysis_uuid
        ).all()
    except ValueError:
        return []


def get_possession_events(db: Session, analysis_id: str) -> List[db_models.PossessionEvent]:
    """Get all possession events for an analysis."""
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        return db.query(db_models.PossessionEvent).filter(
            db_models.PossessionEvent.analysis_id == analysis_uuid
        ).all()
    except ValueError:
        return []


def get_player_stats(db: Session, analysis_id: str) -> List[db_models.PlayerStat]:
    """Get all player statistics for an analysis."""
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        return db.query(db_models.PlayerStat).filter(
            db_models.PlayerStat.analysis_id == analysis_uuid
        ).all()
    except ValueError:
        return []


def db_analysis_to_dict(db_analysis: db_models.VideoAnalysis) -> Dict[str, Any]:
    """Convert database analysis record to dictionary format matching API response."""
    
    # Convert shot attempts
    shot_attempts = []
    for shot in db_analysis.shot_attempts:
        shot_attempts.append({
            "timestamp": shot.timestamp,
            "frame_id": shot.frame_id,
            "shooter_id": shot.shooter_id,
            "shot_position": (shot.shot_position_x, shot.shot_position_y),
            "trajectory": shot.trajectory,
            "shot_zone": shot.shot_zone,
            "confidence": shot.confidence,
            "made": shot.made,
            "shot_value": shot.shot_value,
        })
    
    # Convert possession events
    possession_events = []
    for possession in db_analysis.possession_events:
        possession_events.append({
            "timestamp": possession.timestamp,
            "frame_id": possession.frame_id,
            "player_id": possession.player_id,
            "previous_player_id": possession.previous_player_id,
            "ball_position": (possession.ball_position_x, possession.ball_position_y),
            "duration": possession.duration,
        })
    
    # Convert player stats
    player_stats = {}
    for stat in db_analysis.player_stats:
        player_stats[stat.track_id] = {
            "track_id": stat.track_id,
            "shots_attempted": stat.shots_attempted,
            "shots_made": stat.shots_made,
            "field_goal_percentage": stat.field_goal_percentage,
            "three_point_attempts": stat.three_point_attempts,
            "three_point_made": stat.three_point_made,
            "three_point_percentage": stat.three_point_percentage,
            "possessions": stat.possessions,
            "total_possession_time": stat.total_possession_time,
            "avg_possession_time": stat.avg_possession_time,
            "distance_covered": stat.distance_covered,
            "time_in_zones": stat.time_in_zones,
        }
    
    return {
        "video_metadata": {
            "video_path": db_analysis.video_path,
            "fps": db_analysis.video_fps,
            "width": db_analysis.video_width,
            "height": db_analysis.video_height,
            "total_frames": db_analysis.video_total_frames,
            "duration_seconds": db_analysis.video_duration_seconds,
        },
        "processing_summary": {
            "total_frames_processed": db_analysis.total_frames_processed,
            "frames_with_ball_detected": db_analysis.frames_with_ball_detected,
            "ball_detection_rate": db_analysis.ball_detection_rate,
            "total_events_detected": db_analysis.total_events_detected,
            "unique_players_tracked": db_analysis.unique_players_tracked,
            "processing_time_seconds": db_analysis.processing_time_seconds,
        },
        "game_statistics": {
            "game_duration": db_analysis.game_duration,
            "total_shots": db_analysis.total_shots,
            "possession_changes": db_analysis.possession_changes,
            "player_stats": player_stats,
            "shot_chart": db_analysis.shot_chart_data,
            "possession_summary": db_analysis.possession_summary,
        },
        "frame_by_frame_data": db_analysis.frame_by_frame_data,
        "player_performance": db_analysis.player_performance,
        "shot_attempts": shot_attempts,
        "possession_events": possession_events,
    }