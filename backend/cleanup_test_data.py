#!/usr/bin/env python3
"""
Clean up all test data and show only real user runs
"""
import sys
import os
# Change to backend directory to use the correct database
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
sys.path.append('.')

from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models.run import CompletedRun
from app.models.user import User

def cleanup_test_data():
    db = SessionLocal()
    try:
        # Get test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("No test user found")
            return
        
        print(f"Test user: {test_user.id} ({test_user.email})")
        
        # Get all runs for this user
        all_runs = db.query(CompletedRun).filter(CompletedRun.user_id == test_user.id).all()
        print(f"Total runs before cleanup: {len(all_runs)}")
        
        # Delete ALL test runs (they all have the same pattern - exact 5min/km pace)
        # Real user runs would have more varied paces
        runs_to_delete = []
        
        for run in all_runs:
            # Delete runs that are clearly test data:
            # 1. Exact 300s/km pace (5:00/km) - test data pattern
            # 2. Very small distances (GPS noise)
            # 3. Runs with notes containing "Test" or "test"
            
            is_test_run = False
            
            # Check for exact 300s/km pace (test data pattern)
            if abs(run.avg_pace_s_per_km - 300.0) < 0.1:
                is_test_run = True
                print(f"Test run (exact 5:00/km pace): {run.distance_km}km")
            
            # Check for very small distances
            if run.distance_km < 0.1:  # Less than 100 meters
                is_test_run = True
                print(f"GPS noise run: {run.distance_km}km")
            
            # Check for test notes
            if run.notes and ("test" in run.notes.lower() or "Test" in run.notes):
                is_test_run = True
                print(f"Test run (notes): {run.notes}")
            
            if is_test_run:
                runs_to_delete.append(run)
        
        # Delete the marked runs
        for run in runs_to_delete:
            db.delete(run)
        
        db.commit()
        
        # Show remaining runs
        remaining_runs = db.query(CompletedRun).filter(CompletedRun.user_id == test_user.id).all()
        print(f"\nRemaining runs after cleanup: {len(remaining_runs)}")
        
        if remaining_runs:
            print("Your real runs:")
            for i, run in enumerate(remaining_runs, 1):
                pace_min = int(run.avg_pace_s_per_km // 60)
                pace_sec = int(run.avg_pace_s_per_km % 60)
                print(f"{i}. {run.distance_km:.2f}km in {run.duration_sec}s on {run.start_datetime.strftime('%Y-%m-%d %H:%M')} (pace: {pace_min}:{pace_sec:02d}/km)")
                if run.notes:
                    print(f"   Notes: {run.notes}")
        else:
            print("No real runs found. All data was test data.")
            
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_test_data()