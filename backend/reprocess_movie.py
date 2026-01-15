#!/usr/bin/env python3
"""
Reprocess a movie's video
"""

import sys
import requests

def reprocess_movie(movie_id: int, token: str):
    """Trigger video reprocessing for a movie"""
    
    url = f"http://localhost:8000/api/admin/movies/{movie_id}/reprocess-video"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Reprocessing video for movie {movie_id}...")
    
    try:
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f" Reprocessing started successfully!")
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"\nMonitor progress:")
            print(f"   curl http://localhost:8000/api/admin/upload/status/{result.get('task_id')} -H 'Authorization: Bearer {token}'")
        else:
            print(f" Failed to reprocess: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f" Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reprocess_movie.py <movie_id> <admin_token>")
        print("\nExample:")
        print("  python reprocess_movie.py 111332 your-jwt-token-here")
        print("\nTo get your token:")
        print("  1. Login to admin panel")
        print("  2. Open browser console")
        print("  3. Run: localStorage.getItem('token')")
        sys.exit(1)
    
    movie_id = int(sys.argv[1])
    token = sys.argv[2]
    
    reprocess_movie(movie_id, token)
