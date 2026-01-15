#!/usr/bin/env python3
"""
Check current video processing progress
"""

import os
import glob
import time

def check_current_processing():
    """Check progress of currently processing videos"""
    
    print(" Checking video processing progress...")
    print("=" * 50)
    
    # Find temp processing directories
    temp_dirs = glob.glob("/tmp/video_processing_*")
    
    if not temp_dirs:
        print(" No video processing in progress")
        return
    
    for temp_dir in temp_dirs:
        print(f"\n Processing directory: {temp_dir}")
        
        try:
            files = os.listdir(temp_dir)
            input_file = None
            output_files = []
            
            for file in files:
                file_path = os.path.join(temp_dir, file)
                if not os.path.isfile(file_path):
                    continue
                    
                if file == "input_video":
                    input_file = file_path
                elif file.startswith("output_"):
                    output_files.append(file_path)
            
            if input_file:
                input_size = os.path.getsize(input_file)
                print(f"    Input file: {input_size / 1024 / 1024:.1f} MB")
                
                for output_file in output_files:
                    output_size = os.path.getsize(output_file)
                    progress = (output_size / input_size) * 100
                    quality = os.path.basename(output_file).replace("output_", "").replace(".mp4", "")
                    
                    print(f"    {quality}: {output_size / 1024 / 1024:.1f} MB ({progress:.1f}% estimated)")
                    
                    # Check if file is still being written (size changing)
                    time.sleep(1)
                    new_size = os.path.getsize(output_file)
                    if new_size > output_size:
                        print(f"       Actively processing (+{(new_size - output_size) / 1024:.1f} KB/sec)")
                    else:
                        print(f"      ⏸  Processing may be stalled")
            
        except Exception as e:
            print(f"    Error checking directory: {e}")

if __name__ == "__main__":
    check_current_processing()