#!/usr/bin/env python3
"""
Check runs in database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models.run import CompletedRun
from app.models.user import User

def check_runs():
    db = SessionLocal()
    try:
        # Get test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("ERROR: Test user not found")
            return
        
        print(f"Test user: {test_user.id} ({test_user.email})")
        
        # Get all runs for this user
        all_runs = db.query(CompletedRun).filter(CompletedRun.user_id == test_user.id).all()
        print(f"Total runs in database: {len(all_runs)}")
        
        for i, run in enumerate(all_runs, 1):
            print(f"{i}. {run.distance_km}km in {run.duration_sec}s on {run.start_datetime} (pace: {run.avg_pace_s_per_km:.0f}s/km)")
            
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_runs()