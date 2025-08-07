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

app = FastAPI(title="Basketball Analytics API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
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

@app.post("/analyze/upload")
async def analyze_uploaded_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    confidence_threshold: float = 0.25,
    visualize: bool = True,
    save_frames: bool = False,
    db: Session = Depends(get_db)
):
    """
    Upload and analyze a basketball video file.
    
    Args:
        file: Uploaded video file
        confidence_threshold: Detection confidence threshold
        visualize: Create visualized output video
        save_frames: Save individual analyzed frames
        db: Database session
        
    Returns:
        Analysis response with results
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_video_path = temp_file.name
        
        # Create analysis request
        request = AnalysisRequest(
            video_path=temp_video_path,
            confidence_threshold=confidence_threshold,
            visualize=visualize,
            save_frames=save_frames
        )
        
        # Analyze video
        response = await analyze_video(background_tasks, request, db)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, temp_video_path)
        
        return response
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Upload and analysis failed",
            error=str(e)
        )

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
