from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import uuid
import os
import sys
from typing import Dict, Any, List
import redis
from rq import Queue
from rq.job import Job
from datetime import timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from vision.processor import BasketballVideoProcessor
from .models import (
    AnalysisRequest, 
    AnalysisResponse, 
    VideoAnalysisResult,
    LiveAnalysisConfig,
    CurrentStats
)
from .database import get_db, init_db
from . import crud
from .auth import (
    authenticate_user,
    create_access_token,
    hash_password,
    get_current_user,
    require_club_access
)

app = FastAPI(title="Basketball Analytics API", version="1.0.0")

# Environment variables with defaults
import os
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(frontend_path), html=True), name="dashboard")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Initialize Redis connection for job queue
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
try:
    redis_conn = redis.from_url(redis_url)
    job_queue = Queue('video_processing', connection=redis_conn)
except Exception as e:
    print(f"Redis connection failed: {e}. Job queue disabled.")
    redis_conn = None
    job_queue = None

# Global processor instance
processor = None

def get_processor():
    """Get or create basketball processor instance."""
    global processor
    if processor is None:
        processor = BasketballVideoProcessor()
    return processor

@app.get("/")
async def read_root():
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "processor_ready": processor is not None}

@app.post("/analyze/video", response_model=AnalysisResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a basketball video file.
    
    Args:
        request: Analysis request parameters
        db: Database session
        
    Returns:
        Analysis response with results or status
    """
    try:
        # Validate video file exists
        if not Path(request.video_path).exists():
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.video_path}")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create analysis record in database
        db_analysis = crud.create_analysis(
            db, 
            analysis_id, 
            request.video_path,
            request.confidence_threshold,
            request.visualize,
            request.save_frames
        )
        
        # Schedule background processing
        background_tasks.add_task(
            process_video_background, 
            analysis_id, 
            request,
            db
        )
        
        return AnalysisResponse(
            success=True,
            message="Video analysis started",
            analysis_id=analysis_id
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Failed to start video analysis",
            error=str(e)
        )

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get RQ job status and results.
    
    Args:
        job_id: RQ job ID
        
    Returns:
        Job status and results
    """
    if not redis_conn:
        raise HTTPException(status_code=503, detail="Job queue not available")
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        result = {
            "job_id": job_id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
            "exc_info": job.exc_info,
            "progress": getattr(job.meta, 'progress', 0) if hasattr(job, 'meta') else 0
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")


@app.post("/upload")
async def upload_video_with_queue(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.25,
    visualize: bool = True,
    save_frames: bool = False
):
    """
    Upload video and queue for processing with enhanced validation.
    
    Args:
        file: Uploaded video file
        confidence_threshold: Detection confidence threshold
        visualize: Create visualized output video
        save_frames: Save individual analyzed frames
        
    Returns:
        Job ID for tracking processing status
    """
    # Validate file size
    max_size_mb = int(os.getenv('MAX_UPLOAD_SIZE_MB', '100'))
    if hasattr(file, 'size') and file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {max_size_mb}MB")
    
    # Validate MIME type
    allowed_types = os.getenv('ALLOWED_VIDEO_TYPES', 'video/mp4,video/avi,video/mov').split(',')
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_video_path = temp_file.name
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create analysis record in database
        db = next(get_db())
        crud.create_analysis(
            db, 
            analysis_id, 
            temp_video_path,
            confidence_threshold,
            visualize,
            save_frames
        )
        
        # Queue job for processing if Redis available
        if job_queue:
            from workers.video_processor import process_video_job
            
            job_config = {
                'confidence_threshold': confidence_threshold,
                'visualize': visualize,
                'save_frames': save_frames,
                'output_video_path': None,
                'output_json_path': None
            }
            
            job = job_queue.enqueue(
                process_video_job,
                analysis_id,
                temp_video_path,
                job_config,
                timeout=int(os.getenv('REDIS_JOB_TIMEOUT', '3600'))
            )
            
            return {
                "success": True,
                "message": "Video uploaded and queued for processing",
                "analysis_id": analysis_id,
                "job_id": job.id
            }
        else:
            # Fallback to background task if Redis not available
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            background_tasks.add_task(
                process_video_background, 
                analysis_id, 
                AnalysisRequest(
                    video_path=temp_video_path,
                    confidence_threshold=confidence_threshold,
                    visualize=visualize,
                    save_frames=save_frames
                ),
                db
            )
            
            return {
                "success": True,
                "message": "Video uploaded and processing started",
                "analysis_id": analysis_id,
                "job_id": None
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/analyze/{analysis_id}")
async def get_analysis_results(analysis_id: str, db: Session = Depends(get_db)):
    """
    Get analysis results by ID.
    
    Args:
        analysis_id: Analysis ID
        db: Database session
        
    Returns:
        Analysis results
    """
    db_analysis = crud.get_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Build response from database
    result = {
        "id": db_analysis.id,
        "video_path": db_analysis.video_path,
        "status": db_analysis.status,
        "created_at": db_analysis.created_at,
        "completed_at": db_analysis.completed_at,
        "error_message": db_analysis.error_message,
        "video_metadata": {
            "video_path": db_analysis.video_path,
            "fps": db_analysis.fps,
            "width": db_analysis.width,
            "height": db_analysis.height,
            "total_frames": db_analysis.total_frames,
            "duration_seconds": db_analysis.duration_seconds
        },
        "processing_summary": db_analysis.processing_summary,
        "game_statistics": db_analysis.game_statistics
    }
    
    return result

@app.get("/analyze/{analysis_id}/download")
async def download_analysis_json(analysis_id: str, db: Session = Depends(get_db)):
    """
    Download analysis results as JSON file.
    
    Args:
        analysis_id: Analysis ID
        db: Database session
        
    Returns:
        JSON file download
    """
    db_analysis = crud.get_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Build complete analysis data
    analysis_data = {
        "analysis_id": db_analysis.id,
        "video_path": db_analysis.video_path,
        "status": db_analysis.status,
        "created_at": str(db_analysis.created_at),
        "completed_at": str(db_analysis.completed_at) if db_analysis.completed_at else None,
        "video_metadata": {
            "video_path": db_analysis.video_path,
            "fps": db_analysis.fps,
            "width": db_analysis.width,
            "height": db_analysis.height,
            "total_frames": db_analysis.total_frames,
            "duration_seconds": db_analysis.duration_seconds
        },
        "processing_summary": db_analysis.processing_summary,
        "game_statistics": db_analysis.game_statistics,
        "players": [
            {
                "track_id": player.track_id,
                "shots_attempted": player.shots_attempted,
                "shots_made": player.shots_made,
                "field_goal_percentage": player.field_goal_percentage,
                "three_point_attempts": player.three_point_attempts,
                "three_point_made": player.three_point_made,
                "three_point_percentage": player.three_point_percentage,
                "possessions": player.possessions,
                "total_possession_time": player.total_possession_time,
                "avg_possession_time": player.avg_possession_time,
                "distance_covered": player.distance_covered,
                "time_in_zones": player.time_in_zones
            }
            for player in db_analysis.players
        ],
        "shots": [
            {
                "timestamp": shot.timestamp,
                "frame_id": shot.frame_id,
                "shooter_id": shot.shooter_id,
                "shot_position": [shot.shot_position_x, shot.shot_position_y],
                "shot_zone": shot.shot_zone,
                "confidence": shot.confidence,
                "made": shot.made,
                "shot_value": shot.shot_value,
                "trajectory": shot.trajectory
            }
            for shot in db_analysis.shots
        ],
        "possessions": [
            {
                "timestamp": poss.timestamp,
                "frame_id": poss.frame_id,
                "player_id": poss.player_id,
                "previous_player_id": poss.previous_player_id,
                "ball_position": [poss.ball_position_x, poss.ball_position_y],
                "duration": poss.duration
            }
            for poss in db_analysis.possessions
        ]
    }
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        import json
        json.dump(analysis_data, temp_file, indent=2, default=str)
        temp_json_path = temp_file.name
    
    return FileResponse(
        temp_json_path,
        media_type='application/json',
        filename=f"basketball_analysis_{analysis_id}.json"
    )

@app.post("/analyze/live")
async def start_live_analysis(config: LiveAnalysisConfig):
    """
    Start live video analysis from camera.
    
    Args:
        config: Live analysis configuration
        
    Returns:
        Status response
    """
    try:
        video_processor = get_processor()
        
        # Set confidence threshold
        video_processor.detector.confidence_threshold = config.confidence_threshold
        
        # Start live analysis (this will block, so in real use you'd want to run this in background)
        video_processor.process_live_stream(
            camera_index=config.camera_index,
            display=config.display
        )
        
        return {"message": "Live analysis completed", "success": True}
        
    except Exception as e:
        return {"message": f"Live analysis failed: {str(e)}", "success": False}

@app.get("/stats/current", response_model=CurrentStats)
async def get_current_stats():
    """
    Get current processing statistics.
    
    Returns:
        Current statistics
    """
    if processor is None:
        return CurrentStats(status="Processor not initialized")
    
    stats = processor.get_current_stats()
    return CurrentStats(**stats)

@app.delete("/analyze/{analysis_id}")
async def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Delete analysis results from database.
    
    Args:
        analysis_id: Analysis ID
        db: Database session
        
    Returns:
        Success status
    """
    if crud.delete_analysis(db, analysis_id):
        return {"message": "Analysis deleted", "success": True}
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")


@app.get("/analyze")
async def list_analyses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all analyses.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of analyses and basic info
    """
    analyses = crud.get_analyses(db, skip=skip, limit=limit)
    
    result = []
    for analysis in analyses:
        summary = {
            "analysis_id": analysis.id,
            "video_path": analysis.video_path,
            "status": analysis.status,
            "created_at": analysis.created_at,
            "completed_at": analysis.completed_at,
            "duration": analysis.duration_seconds,
            "total_frames": analysis.total_frames,
            "players_tracked": analysis.unique_players,
            "error_message": analysis.error_message
        }
        result.append(summary)
    
    return {"analyses": result, "total_count": len(result)}

def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        os.unlink(file_path)
    except OSError:
        pass  # File already deleted or doesn't exist


async def process_video_background(analysis_id: str, request: AnalysisRequest, db_session_maker):
    """Process video in background and update database."""
    # Create new database session for background task
    from .database import SessionLocal
    db = SessionLocal()
    
    try:
        # Get processor
        video_processor = get_processor()
        
        # Set confidence threshold if different
        if request.confidence_threshold != video_processor.detector.confidence_threshold:
            video_processor.detector.confidence_threshold = request.confidence_threshold
        
        # Process video
        results = video_processor.process_video(
            video_path=request.video_path,
            output_video_path=request.output_video_path,
            output_json_path=request.output_json_path,
            visualize=request.visualize,
            save_frames=request.save_frames
        )
        
        # Convert to response model
        video_analysis = VideoAnalysisResult(**results)
        
        # Update database with results
        crud.update_analysis_results(db, analysis_id, video_analysis)
        
    except Exception as e:
        # Update database with error
        crud.update_analysis_error(db, analysis_id, str(e))
    finally:
        db.close()


# Add new endpoint for shot chart data
@app.get("/analyze/{analysis_id}/shot-chart")
async def get_shot_chart_data(analysis_id: str, db: Session = Depends(get_db)):
    """Get shot chart data for visualization."""
    db_analysis = crud.get_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    shots = crud.get_analysis_shots(db, analysis_id)
    
    shot_chart_data = {
        "analysis_id": analysis_id,
        "video_metadata": {
            "width": db_analysis.width,
            "height": db_analysis.height,
            "duration": db_analysis.duration_seconds
        },
        "shots": [
            {
                "x": shot.shot_position_x,
                "y": shot.shot_position_y,
                "made": shot.made,
                "zone": shot.shot_zone,
                "value": shot.shot_value,
                "timestamp": shot.timestamp,
                "player_id": shot.shooter_id
            }
            for shot in shots
        ],
        "zones": {
            "paint": {"attempts": 0, "makes": 0},
            "mid_range": {"attempts": 0, "makes": 0},
            "three_point": {"attempts": 0, "makes": 0}
        }
    }
    
    # Calculate zone statistics
    for shot in shots:
        zone = "three_point" if shot.shot_value == 3 else ("paint" if "paint" in shot.shot_zone.lower() else "mid_range")
        shot_chart_data["zones"][zone]["attempts"] += 1
        if shot.made:
            shot_chart_data["zones"][zone]["makes"] += 1
    
    return shot_chart_data


# New stats endpoints
@app.get("/players/{player_id}/stats")
async def get_player_stats(
    player_id: int, 
    match_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get player statistics, optionally filtered by match.
    
    Args:
        player_id: Player ID
        match_id: Optional match ID to filter stats
        db: Database session
        
    Returns:
        Player statistics
    """
    try:
        # Get player info
        player = crud.get_player(db, player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get stats
        if match_id:
            stats = crud.get_player_match_stats(db, player_id, match_id)
            if not stats:
                raise HTTPException(status_code=404, detail="Stats not found for this player and match")
            stats_list = [stats]
        else:
            stats_list = crud.get_player_all_stats(db, player_id)
        
        # Calculate aggregated stats
        total_stats = {
            "player_id": player_id,
            "player_name": player.name,
            "club_name": player.club.name if player.club else None,
            "jersey_number": player.jersey_number,
            "position": player.position,
            "games_played": len(stats_list),
            "total_minutes": sum(s.minutes_played for s in stats_list),
            "total_points": sum(s.points for s in stats_list),
            "total_field_goals_made": sum(s.field_goals_made for s in stats_list),
            "total_field_goals_attempted": sum(s.field_goals_attempted for s in stats_list),
            "field_goal_percentage": 0,
            "total_three_points_made": sum(s.three_points_made for s in stats_list),
            "total_three_points_attempted": sum(s.three_points_attempted for s in stats_list),
            "three_point_percentage": 0,
            "total_distance_covered_m": sum(s.distance_covered_m for s in stats_list),
            "avg_speed_kmh": sum(s.avg_speed_kmh for s in stats_list) / len(stats_list) if stats_list else 0,
            "max_speed_kmh": max((s.max_speed_kmh for s in stats_list), default=0),
            "total_ball_touches": sum(s.ball_touches for s in stats_list),
            "avg_ball_touches_per_game": sum(s.ball_touches for s in stats_list) / len(stats_list) if stats_list else 0
        }
        
        # Calculate percentages
        if total_stats["total_field_goals_attempted"] > 0:
            total_stats["field_goal_percentage"] = round(
                (total_stats["total_field_goals_made"] / total_stats["total_field_goals_attempted"]) * 100, 1
            )
        
        if total_stats["total_three_points_attempted"] > 0:
            total_stats["three_point_percentage"] = round(
                (total_stats["total_three_points_made"] / total_stats["total_three_points_attempted"]) * 100, 1
            )
        
        # Include individual game stats if requested
        if match_id:
            total_stats["match_stats"] = {
                "match_id": match_id,
                "minutes_played": stats_list[0].minutes_played,
                "points": stats_list[0].points,
                "field_goals": f"{stats_list[0].field_goals_made}/{stats_list[0].field_goals_attempted}",
                "three_points": f"{stats_list[0].three_points_made}/{stats_list[0].three_points_attempted}",
                "distance_covered_m": stats_list[0].distance_covered_m,
                "avg_speed_kmh": stats_list[0].avg_speed_kmh,
                "max_speed_kmh": stats_list[0].max_speed_kmh,
                "ball_touches": stats_list[0].ball_touches,
                "time_with_ball": stats_list[0].time_with_ball
            }
        
        return total_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving player stats: {str(e)}")


@app.get("/matches/{match_id}/stats")
async def get_match_stats(match_id: int, db: Session = Depends(get_db)):
    """
    Get aggregated statistics for a match.
    
    Args:
        match_id: Match ID
        db: Database session
        
    Returns:
        Aggregated match statistics
    """
    try:
        # Get match info
        match = crud.get_match(db, match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get all player stats for this match
        match_stats = crud.get_match_all_stats(db, match_id)
        
        # Separate home and away team stats
        home_team_stats = [s for s in match_stats if s.player.club_id == match.home_club_id]
        away_team_stats = [s for s in match_stats if s.player.club_id == match.away_club_id]
        
        def aggregate_team_stats(team_stats, team_name):
            if not team_stats:
                return {"team_name": team_name, "players": []}
                
            return {
                "team_name": team_name,
                "total_points": sum(s.points for s in team_stats),
                "field_goals": f"{sum(s.field_goals_made for s in team_stats)}/{sum(s.field_goals_attempted for s in team_stats)}",
                "field_goal_percentage": round(
                    (sum(s.field_goals_made for s in team_stats) / sum(s.field_goals_attempted for s in team_stats) * 100) 
                    if sum(s.field_goals_attempted for s in team_stats) > 0 else 0, 1
                ),
                "three_points": f"{sum(s.three_points_made for s in team_stats)}/{sum(s.three_points_attempted for s in team_stats)}",
                "three_point_percentage": round(
                    (sum(s.three_points_made for s in team_stats) / sum(s.three_points_attempted for s in team_stats) * 100) 
                    if sum(s.three_points_attempted for s in team_stats) > 0 else 0, 1
                ),
                "total_distance_covered_m": round(sum(s.distance_covered_m for s in team_stats), 1),
                "avg_team_speed_kmh": round(sum(s.avg_speed_kmh for s in team_stats) / len(team_stats), 1) if team_stats else 0,
                "max_team_speed_kmh": round(max((s.max_speed_kmh for s in team_stats), default=0), 1),
                "total_ball_touches": sum(s.ball_touches for s in team_stats),
                "players": [
                    {
                        "player_id": s.player_id,
                        "name": s.player.name,
                        "jersey_number": s.player.jersey_number,
                        "minutes_played": s.minutes_played,
                        "points": s.points,
                        "field_goals": f"{s.field_goals_made}/{s.field_goals_attempted}",
                        "three_points": f"{s.three_points_made}/{s.three_points_attempted}",
                        "distance_covered_m": s.distance_covered_m,
                        "avg_speed_kmh": s.avg_speed_kmh,
                        "ball_touches": s.ball_touches
                    }
                    for s in team_stats
                ]
            }
        
        result = {
            "match_id": match_id,
            "match_date": match.played_date.isoformat() if match.played_date else match.scheduled_date.isoformat(),
            "home_team": aggregate_team_stats(home_team_stats, match.home_club.name),
            "away_team": aggregate_team_stats(away_team_stats, match.away_club.name),
            "final_score": {
                "home": match.home_score,
                "away": match.away_score
            } if match.home_score is not None else None,
            "duration_minutes": match.duration_minutes,
            "status": match.status
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving match stats: {str(e)}")


# Authentication endpoints
@app.post("/auth/register")
async def register_user(
    username: str,
    email: str,
    password: str,
    role: str = "public",
    club_id: int = None,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if user already exists
        if crud.get_user_by_username(db, username):
            raise HTTPException(status_code=400, detail="Username already taken")
        
        if crud.get_user_by_email(db, email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate role
        if role not in ["public", "club"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'public' or 'club'")
        
        # Hash password and create user
        hashed_password = hash_password(password)
        user = crud.create_user(
            db, 
            email=email, 
            username=username, 
            hashed_password=hashed_password,
            role=role,
            club_id=club_id
        )
        
        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login")
async def login_user(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    try:
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role, "user_id": user.id}
        )
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "club_id": user.club_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "club_id": current_user.club_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


# Protected club endpoints
@app.get("/club/dashboard-data")
async def get_club_dashboard_data(
    current_user = Depends(require_club_access()),
    db: Session = Depends(get_db)
):
    """Get dashboard data for club users."""
    try:
        if not current_user.club_id:
            raise HTTPException(status_code=400, detail="User not associated with a club")
        
        # Get club info
        club = crud.get_club(db, current_user.club_id)
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        # Get club players and their stats
        players = crud.get_players_by_club(db, current_user.club_id)
        
        player_stats = []
        for player in players:
            stats = crud.get_player_all_stats(db, player.id)
            
            # Calculate aggregated stats
            total_minutes = sum(s.minutes_played for s in stats)
            total_distance = sum(s.distance_covered_m for s in stats)
            total_touches = sum(s.ball_touches for s in stats)
            avg_speed = sum(s.avg_speed_kmh for s in stats) / len(stats) if stats else 0
            games_played = len(stats)
            
            player_stats.append({
                "player_id": player.id,
                "player_name": player.name,
                "jersey_number": player.jersey_number,
                "position": player.position,
                "games_played": games_played,
                "total_minutes": round(total_minutes, 1),
                "total_distance_m": round(total_distance, 1),
                "avg_speed_kmh": round(avg_speed, 1),
                "total_ball_touches": total_touches,
                "avg_touches_per_game": round(total_touches / games_played, 1) if games_played > 0 else 0
            })
        
        return {
            "club": {
                "id": club.id,
                "name": club.name,
                "code": club.code,
                "city": club.city
            },
            "players": player_stats,
            "summary": {
                "total_players": len(players),
                "active_players": len([p for p in player_stats if p["games_played"] > 0])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")


@app.post("/club/upload")
async def club_upload_video(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.25,
    visualize: bool = True,
    save_frames: bool = False,
    current_user = Depends(require_club_access())
):
    """Protected video upload for club users."""
    return await upload_video_with_queue(file, confidence_threshold, visualize, save_frames)


# Add endpoint for live data (for frontend dashboard)
@app.get("/analyze/{analysis_id}/live-data")
async def get_live_analysis_data(analysis_id: str, db: Session = Depends(get_db)):
    """Get live analysis data for dashboard updates."""
    db_analysis = crud.get_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    players = crud.get_analysis_players(db, analysis_id)
    shots = crud.get_analysis_shots(db, analysis_id)
    
    return {
        "analysis_id": analysis_id,
        "status": db_analysis.status,
        "progress": {
            "frames_processed": db_analysis.frames_processed,
            "total_frames": db_analysis.total_frames,
            "percentage": (db_analysis.frames_processed / db_analysis.total_frames * 100) if db_analysis.total_frames else 0
        },
        "current_stats": {
            "total_shots": len(shots),
            "shots_made": len([s for s in shots if s.made]),
            "active_players": len(players),
            "game_time": db_analysis.duration_seconds or 0
        },
        "recent_events": [
            {
                "type": "shot",
                "timestamp": shot.timestamp,
                "player_id": shot.shooter_id,
                "made": shot.made,
                "zone": shot.shot_zone
            }
            for shot in sorted(shots, key=lambda x: x.timestamp, reverse=True)[:10]
        ]
    }
