from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import uuid
import os
import sys
from typing import Dict, Any

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
from .database import get_db, create_tables
from . import crud

app = FastAPI(title="Basketball Analytics API", version="1.0.0")

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

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
    return {"message": "Basketball Analytics API", "version": "1.0.0"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy", 
        "processor_ready": processor is not None,
        "database_status": db_status
    }

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
        
    Returns:
        Analysis response with results or status
    """
    try:
        # Validate video file exists
        if not Path(request.video_path).exists():
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.video_path}")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
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
        
        # Convert to response model and save to database
        video_analysis = VideoAnalysisResult(**results)
        db_analysis = crud.create_video_analysis(db, video_analysis)
        analysis_id = str(db_analysis.id)
        
        return AnalysisResponse(
            success=True,
            message="Video analysis completed successfully",
            analysis_id=analysis_id,
            results=video_analysis
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Video analysis failed",
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
        
    Returns:
        Analysis results
    """
    db_analysis = crud.get_video_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return crud.db_analysis_to_dict(db_analysis)

@app.get("/analyze/{analysis_id}/download")
async def download_analysis_json(analysis_id: str, db: Session = Depends(get_db)):
    """
    Download analysis results as JSON file.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        JSON file download
    """
    db_analysis = crud.get_video_analysis(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Get analysis data as dictionary
    analysis_data = crud.db_analysis_to_dict(db_analysis)
    
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
        
    Returns:
        Success status
    """
    if crud.delete_video_analysis(db, analysis_id):
        return {"message": "Analysis deleted", "success": True}
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")

@app.get("/analyze")
async def list_analyses(db: Session = Depends(get_db)):
    """
    List all analyses.
    
    Returns:
        List of analysis IDs and basic info
    """
    db_analyses = crud.get_video_analyses(db)
    analyses = []
    
    for db_analysis in db_analyses:
        summary = {
            "analysis_id": str(db_analysis.id),
            "video_path": db_analysis.video_path,
            "duration": db_analysis.video_duration_seconds,
            "total_frames": db_analysis.total_frames_processed,
            "players_tracked": db_analysis.unique_players_tracked,
            "created_at": db_analysis.created_at.isoformat() if db_analysis.created_at else None
        }
        analyses.append(summary)
    
    return {"analyses": analyses, "total_count": len(analyses)}

def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        os.unlink(file_path)
    except OSError:
        pass  # File already deleted or doesn't exist
