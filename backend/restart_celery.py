#!/usr/bin/env python3
"""
Restart Celery worker to apply video processing improvements
"""

import os
import signal
import subprocess
import time
import sys

def restart_celery_worker():
    """Restart the Celery worker process"""
    
    print("Restarting Celery worker...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", "celery.*worker"], 
            capture_output=True, 
            text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"Found {len(pids)} Celery worker process(es)")
            
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    print(f"   Stopping process {pid}")
                    os.kill(pid, signal.SIGTERM)
                except (ValueError, ProcessLookupError) as e:
                    print(f"   Could not stop process {pid}: {e}")
            
            print("   Waiting for processes to stop...")
            time.sleep(3)
            
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    os.kill(pid, signal.SIGKILL)
                    print(f"   Force killed process {pid}")
                except (ValueError, ProcessLookupError):
                    pass
        else:
            print("No existing Celery worker processes found")
    
    except Exception as e:
        print(f"Error checking for existing processes: {e}")
    
    pid_file = "celery.pid"
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
            print(f"Removed PID file: {pid_file}")
        except Exception as e:
            print(f"Could not remove PID file: {e}")
    
    print("\nStarting new Celery worker...")
    
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        cmd = [
            "./venv/bin/celery", "-A", "app.workers.celery_app", "worker",
            "--loglevel=info",
            "--concurrency=2",
            "--pidfile=celery.pid",
            "--logfile=logs/celery.log"
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        os.makedirs("logs", exist_ok=True)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        time.sleep(2)
        
        if process.poll() is None:
            print("Celery worker started successfully!")
            print(f"   Process ID: {process.pid}")
            print(f"   Log file: logs/celery.log")
            print(f"   Concurrency: 2 workers")
            
            return True
        else:
            stdout, stderr = process.communicate()
            print("Failed to start Celery worker")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Error starting Celery worker: {e}")
        return False

if __name__ == "__main__":
    success = restart_celery_worker()
    sys.exit(0 if success else 1)
