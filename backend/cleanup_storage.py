#!/usr/bin/env python3
"""
Clean up MinIO storage by removing old or unused video files
"""

import asyncio
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Movie
from app.services.minio_service import MinIOService
from app.core.logging import logger


async def check_storage_usage():
    """Check MinIO storage usage"""
    print("Checking MinIO storage usage...")
    print("=" * 50)
    
    try:
        minio_service = MinIOService()
        buckets = ["videos", "thumbnails", "manifests"]
        total_objects = 0
        
        for bucket in buckets:
            try:
                objects = await minio_service.list_objects(bucket)
                print(f"Bucket '{bucket}': {len(objects)} objects")
                total_objects += len(objects)
                
                if objects:
                    print(f"   Examples: {objects[:3]}")
                    
            except Exception as e:
                print(f"   Error accessing bucket '{bucket}': {e}")
        
        print(f"\nTotal objects across all buckets: {total_objects}")
        
    except Exception as e:
        print(f"Error checking storage: {e}")


async def find_orphaned_files():
    """Find files in MinIO that don't have corresponding database records"""
    print("\nFinding orphaned files...")
    print("=" * 50)
    
    try:
        minio_service = MinIOService()
        db = next(get_db())
        
        movies = db.query(Movie).filter(Movie.video_file_id.isnot(None)).all()
        db_file_ids = {movie.video_file_id for movie in movies}
        
        print(f"Found {len(db_file_ids)} video files in database")
        
        video_objects = await minio_service.list_objects("videos")
        orphaned_videos = []
        
        for obj in video_objects:
            if "/" in obj:
                parts = obj.split("/")
                if len(parts) >= 2 and parts[0] == "processed-videos":
                    file_id = parts[1]
                else:
                    continue
            else:
                file_id = obj
            
            if file_id not in db_file_ids:
                orphaned_videos.append(obj)
        
        print(f"Found {len(orphaned_videos)} orphaned video files")
        
        thumbnail_objects = await minio_service.list_objects("thumbnails")
        orphaned_thumbnails = []
        
        for obj in thumbnail_objects:
            if "/" in obj:
                file_id = obj.split("/")[0]
                if file_id not in db_file_ids:
                    orphaned_thumbnails.append(obj)
        
        print(f"Found {len(orphaned_thumbnails)} orphaned thumbnail files")
        
        manifest_objects = await minio_service.list_objects("manifests")
        orphaned_manifests = []
        
        for obj in manifest_objects:
            if "/" in obj:
                file_id = obj.split("/")[0]
                if file_id not in db_file_ids:
                    orphaned_manifests.append(obj)
        
        print(f"Found {len(orphaned_manifests)} orphaned manifest files")
        
        return {
            "videos": orphaned_videos,
            "thumbnails": orphaned_thumbnails,
            "manifests": orphaned_manifests
        }
        
    except Exception as e:
        print(f"Error finding orphaned files: {e}")
        return {"videos": [], "thumbnails": [], "manifests": []}
    finally:
        db.close()


async def cleanup_orphaned_files(orphaned_files, confirm=True):
    """Clean up orphaned files"""
    
    total_files = sum(len(files) for files in orphaned_files.values())
    
    if total_files == 0:
        print("No orphaned files to clean up")
        return
    
    print(f"\nFound {total_files} orphaned files to clean up:")
    for bucket, files in orphaned_files.items():
        if files:
            print(f"   {bucket}: {len(files)} files")
    
    if confirm:
        response = input("\nDo you want to delete these orphaned files? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled")
            return
    
    print("\nCleaning up orphaned files...")
    
    try:
        minio_service = MinIOService()
        deleted_count = 0
        
        for bucket, files in orphaned_files.items():
            for obj in files:
                try:
                    await minio_service.delete_object(bucket, obj)
                    deleted_count += 1
                    print(f"   Deleted {bucket}/{obj}")
                except Exception as e:
                    print(f"   Failed to delete {bucket}/{obj}: {e}")
        
        print(f"\nSuccessfully deleted {deleted_count} orphaned files")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")


async def cleanup_failed_uploads():
    """Clean up movies with failed processing status"""
    print("\nCleaning up failed uploads...")
    print("=" * 50)
    
    try:
        db = next(get_db())
        
        failed_movies = db.query(Movie).filter(
            Movie.processing_status == "failed"
        ).all()
        
        print(f"Found {len(failed_movies)} movies with failed processing")
        
        if not failed_movies:
            print("No failed uploads to clean up")
            return
        
        minio_service = MinIOService()
        cleaned_count = 0
        
        for movie in failed_movies:
            if movie.video_file_id:
                try:
                    await minio_service.delete_object("videos", movie.video_file_id)
                    
                    processed_objects = await minio_service.list_objects(
                        "videos", f"processed-videos/{movie.video_file_id}/"
                    )
                    for obj in processed_objects:
                        await minio_service.delete_object("videos", obj)
                    
                    thumbnail_objects = await minio_service.list_objects(
                        "thumbnails", f"{movie.video_file_id}/"
                    )
                    for obj in thumbnail_objects:
                        await minio_service.delete_object("thumbnails", obj)
                    
                    manifest_objects = await minio_service.list_objects(
                        "manifests", f"{movie.video_file_id}/"
                    )
                    for obj in manifest_objects:
                        await minio_service.delete_object("manifests", obj)
                    
                    movie.video_file_id = None
                    movie.processing_status = None
                    movie.available_qualities = []
                    movie.hls_manifest_url = None
                    movie.duration_seconds = None
                    
                    cleaned_count += 1
                    print(f"   Cleaned up movie {movie.id}: {movie.title}")
                    
                except Exception as e:
                    print(f"   Failed to clean up movie {movie.id}: {e}")
        
        db.commit()
        print(f"\nSuccessfully cleaned up {cleaned_count} failed uploads")
        
    except Exception as e:
        print(f"Error cleaning up failed uploads: {e}")
    finally:
        db.close()


async def get_disk_usage():
    """Check disk usage of the system"""
    print("\nChecking disk usage...")
    print("=" * 50)
    
    try:
        import shutil
        
        total, used, free = shutil.disk_usage(".")
        
        print(f"Disk Usage:")
        print(f"   Total: {total // (1024**3):.1f} GB")
        print(f"   Used:  {used // (1024**3):.1f} GB")
        print(f"   Free:  {free // (1024**3):.1f} GB")
        print(f"   Usage: {(used/total)*100:.1f}%")
        
        if free < 5 * 1024**3:
            print("WARNING: Low disk space (less than 5GB free)")
        elif free < 1 * 1024**3:
            print("CRITICAL: Very low disk space (less than 1GB free)")
        
    except Exception as e:
        print(f"Error checking disk usage: {e}")


async def main():
    """Main cleanup function"""
    print("MinIO Storage Cleanup Tool")
    print("=" * 50)
    
    await get_disk_usage()
    await check_storage_usage()
    
    orphaned_files = await find_orphaned_files()
    await cleanup_failed_uploads()
    await cleanup_orphaned_files(orphaned_files, confirm=True)
    
    print("\nStorage cleanup completed!")
    print("\nTips to prevent storage issues:")
    print("   - Regularly clean up test uploads")
    print("   - Monitor disk usage with 'df -h'")
    print("   - Consider increasing MinIO storage limits")
    print("   - Set up automatic cleanup for old files")


if __name__ == "__main__":
    asyncio.run(main())
