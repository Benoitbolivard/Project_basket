from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title="Basketball Analytics API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Global processor instance
processor = None
analysis_cache: Dict[str, Dict[str, Any]] = {}

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
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "processor_ready": processor is not None}

@app.post("/analyze/video", response_model=AnalysisResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest
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
        
        # Cache results
        analysis_cache[analysis_id] = results
        
        # Convert to response model
        video_analysis = VideoAnalysisResult(**results)
        
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
    save_frames: bool = False
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
        response = await analyze_video(background_tasks, request)
        
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
async def get_analysis_results(analysis_id: str):
    """
    Get analysis results by ID.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Analysis results
    """
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_cache[analysis_id]

@app.get("/analyze/{analysis_id}/download")
async def download_analysis_json(analysis_id: str):
    """
    Download analysis results as JSON file.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        JSON file download
    """
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        import json
        json.dump(analysis_cache[analysis_id], temp_file, indent=2, default=str)
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
async def delete_analysis(analysis_id: str):
    """
    Delete analysis results from cache.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Success status
    """
    if analysis_id in analysis_cache:
        del analysis_cache[analysis_id]
        return {"message": "Analysis deleted", "success": True}
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")

@app.get("/analyze")
async def list_analyses():
    """
    List all cached analyses.
    
    Returns:
        List of analysis IDs and basic info
    """
    analyses = []
    for analysis_id, results in analysis_cache.items():
        summary = {
            "analysis_id": analysis_id,
            "video_path": results.get('video_metadata', {}).get('video_path', 'unknown'),
            "duration": results.get('video_metadata', {}).get('duration_seconds', 0),
            "total_frames": results.get('processing_summary', {}).get('total_frames_processed', 0),
            "players_tracked": results.get('processing_summary', {}).get('unique_players_tracked', 0)
        }
        analyses.append(summary)
    
    return {"analyses": analyses, "total_count": len(analyses)}

def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        os.unlink(file_path)
    except OSError:
        pass  # File already deleted or doesn't exist
