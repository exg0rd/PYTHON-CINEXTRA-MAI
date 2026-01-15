#!/usr/bin/env python3
"""
Improve video processing progress reporting by monitoring FFmpeg output
"""

import re
import subprocess
from typing import Optional, Callable

def parse_ffmpeg_progress(line: str, total_duration: float) -> Optional[float]:
    """
    Parse FFmpeg progress from output line
    Returns progress as percentage (0-100)
    """
    # Look for time= output from FFmpeg
    time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        centiseconds = int(time_match.group(4))
        
        current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
        progress = (current_time / total_duration) * 100
        return min(progress, 100)
    
    return None

def run_ffmpeg_with_progress(cmd: list, total_duration: float, progress_callback: Callable[[float], None]) -> bool:
    """
    Run FFmpeg command with real-time progress monitoring
    """
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        last_progress = 0
        for line in iter(process.stdout.readline, ''):
            # Parse progress from FFmpeg output
            progress = parse_ffmpeg_progress(line, total_duration)
            if progress is not None and progress > last_progress:
                progress_callback(progress)
                last_progress = progress
        
        process.wait()
        return process.returncode == 0
        
    except Exception as e:
        print(f"Error running FFmpeg: {e}")
        return False

# Test the progress parsing
if __name__ == "__main__":
    # Test with sample FFmpeg output
    test_lines = [
        "frame=  123 fps= 25 q=23.0 size=    1024kB time=00:00:05.12 bitrate=1638.4kbits/s speed=1.02x",
        "frame=  246 fps= 25 q=23.0 size=    2048kB time=00:00:10.24 bitrate=1638.4kbits/s speed=1.02x",
        "frame=  369 fps= 25 q=23.0 size=    3072kB time=00:00:15.36 bitrate=1638.4kbits/s speed=1.02x"
    ]
    
    total_duration = 100.0  # 100 seconds total
    
    for line in test_lines:
        progress = parse_ffmpeg_progress(line, total_duration)
        if progress:
            print(f"Progress: {progress:.1f}%")