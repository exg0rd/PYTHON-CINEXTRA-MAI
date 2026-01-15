#!/usr/bin/env python3
"""
Script to reprocess movie 76600 with fixed FFmpeg settings
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Movie
from app.services.minio_service import MinIOService
from app.workers.video_processor import process_video_task
import asyncio

def main():
    db = next(get_db())
    minio_service = MinIOService()
    
    try:
        # Get movie 76600
        movie = db.query(Movie).filter(Movie.id == 76600).first()
        
        if not movie:
            print(" Movie 76600 not found")
            return
        
        if not movie.video_file_id:
            print(" Movie 76600 has no video file")
            return
        
        print(f"  Movie: {movie.title}")
        print(f" Video file ID: {movie.video_file_id}")
        print(f" Current status: {movie.processing_status}")
        print()
        
        # Check if original file exists in MinIO
        video_file_id = movie.video_file_id
        
        async def check_file():
            exists = await minio_service.object_exists("videos", video_file_id)
            return exists
        
        file_exists = asyncio.run(check_file())
        
        if not file_exists:
            print(f" Original video file not found in MinIO: {video_file_id}")
            return
        
        print(f" Original video file exists in MinIO")
        print()
        
        # Delete old processed files
        print("  Deleting old processed files...")
        
        async def cleanup_old_files():
            # Delete processed videos
            try:
                objects = await minio_service.list_objects("videos", f"processed-videos/{video_file_id}/")
                for obj in objects:
                    await minio_service.delete_object("videos", obj)
                    print(f"   Deleted: {obj}")
            except Exception as e:
                print(f"   No processed videos to delete: {e}")
            
            # Delete manifest
            try:
                objects = await minio_service.list_objects("manifests", f"{video_file_id}/")
                for obj in objects:
                    await minio_service.delete_object("manifests", obj)
                    print(f"   Deleted manifest: {obj}")
            except Exception as e:
                print(f"   No manifests to delete: {e}")
        
        asyncio.run(cleanup_old_files())
        print()
        
        # Reset movie status
        movie.processing_status = "pending"
        movie.hls_manifest_url = None
        movie.available_qualities = []
        db.commit()
        
        print(" Starting reprocessing...")
        print("   This will use the new FFmpeg settings with:")
        print("   - Explicit video/audio codec copy")
        print("   - H.264 bitstream filter for HLS compatibility")
        print("   - Independent segments flag")
        print("   - Enhanced logging for debugging")
        print()
        
        # Trigger reprocessing
        result = process_video_task.delay(video_file_id, 76600)
        
        print(f" Reprocessing task started!")
        print(f"   Task ID: {result.id}")
        print()
        print(" Monitor progress:")
        print(f"   - Check backend logs: tail -f backend/logs/celery.log")
        print(f"   - Check task status in admin panel")
        print()
        print(" The new code will log:")
        print("   - Input file codec info before HLS segmentation")
        print("   - Number of segments created")
        print("   - First segment codec verification")
        print("   - Warnings if video track is missing")
        
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
