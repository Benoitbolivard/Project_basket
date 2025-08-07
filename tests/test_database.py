"""Test database functionality."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Set testing mode
os.environ["TESTING"] = "true"

from backend.app.database import get_db, create_tables, drop_tables
from backend.app import crud
from backend.app.models import VideoAnalysisResult, VideoMetadata, ProcessingSummary, GameStatistics


def test_database_crud():
    """Test basic CRUD operations."""
    print("Testing database CRUD operations...")
    
    # Create tables
    create_tables()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test data
        video_metadata = VideoMetadata(
            video_path="/test/path.mp4",
            fps=30.0,
            width=640,
            height=480,
            total_frames=300,
            duration_seconds=10.0
        )
        
        processing_summary = ProcessingSummary(
            total_frames_processed=300,
            frames_with_ball_detected=150,
            ball_detection_rate=0.5,
            total_events_detected=5,
            unique_players_tracked=2,
            processing_time_seconds=30.0
        )
        
        game_statistics = GameStatistics(
            game_duration=10.0,
            total_shots=3,
            possession_changes=5
        )
        
        analysis_result = VideoAnalysisResult(
            video_metadata=video_metadata,
            processing_summary=processing_summary,
            game_statistics=game_statistics
        )
        
        # Test CREATE
        db_analysis = crud.create_video_analysis(db, analysis_result)
        assert db_analysis.id is not None
        analysis_id = str(db_analysis.id)
        print(f"✓ Created analysis with ID: {analysis_id}")
        
        # Test READ
        retrieved_analysis = crud.get_video_analysis(db, analysis_id)
        assert retrieved_analysis is not None
        assert retrieved_analysis.video_path == "/test/path.mp4"
        assert retrieved_analysis.video_fps == 30.0
        print("✓ Retrieved analysis successfully")
        
        # Test conversion to dict
        analysis_dict = crud.db_analysis_to_dict(retrieved_analysis)
        assert "video_metadata" in analysis_dict
        assert "processing_summary" in analysis_dict
        assert "game_statistics" in analysis_dict
        print("✓ Converted to dictionary successfully")
        
        # Test LIST
        all_analyses = crud.get_video_analyses(db)
        assert len(all_analyses) >= 1
        print(f"✓ Listed {len(all_analyses)} analyses")
        
        # Test DELETE
        deleted = crud.delete_video_analysis(db, analysis_id)
        assert deleted is True
        
        # Verify deletion
        deleted_analysis = crud.get_video_analysis(db, analysis_id)
        assert deleted_analysis is None
        print("✓ Deleted analysis successfully")
        
        print("All database CRUD tests passed! ✅")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_database_crud()