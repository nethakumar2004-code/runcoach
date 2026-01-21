#!/usr/bin/env python3

import sys
import os
# Change to backend directory to use the correct database
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
sys.path.append('.')

from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models.run import CompletedRun
from app.models.user import User
from app.dependencies import get_password_hash

def test_run_creation():
    db = SessionLocal()
    try:
        # Get or create test user (the one used by dev-token)
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                password_hash=get_password_hash("password123"),
                name="Test User",
                experience_level="intermediate"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        print(f"Test user: {test_user.id} ({test_user.email})")
        
        # Check existing runs
        existing_runs = db.query(CompletedRun).filter(CompletedRun.user_id == test_user.id).all()
        print(f"Existing runs: {len(existing_runs)}")
        
        # Add multiple test runs for analytics
        test_runs = [
            {
                "days_ago": 1,
                "distance_km": 5.0,
                "duration_sec": 1500,  # 25 minutes (5:00/km pace)
                "training_load": 75.0
            },
            {
                "days_ago": 3,
                "distance_km": 3.0,
                "duration_sec": 900,   # 15 minutes (5:00/km pace)
                "training_load": 55.0
            },
            {
                "days_ago": 7,
                "distance_km": 7.0,
                "duration_sec": 2100,  # 35 minutes (5:00/km pace)
                "training_load": 95.0
            },
            {
                "days_ago": 10,
                "distance_km": 4.0,
                "duration_sec": 1200,  # 20 minutes (5:00/km pace)
                "training_load": 65.0
            },
            {
                "days_ago": 14,
                "distance_km": 6.0,
                "duration_sec": 1800,  # 30 minutes (5:00/km pace)
                "training_load": 85.0
            }
        ]
        
        for run_data in test_runs:
            start_time = datetime.utcnow() - timedelta(days=run_data["days_ago"])
            
            # Calculate pace (seconds per km)
            avg_pace = run_data["duration_sec"] / run_data["distance_km"]
            
            test_run = CompletedRun(
                user_id=test_user.id,
                start_datetime=start_time,
                distance_km=run_data["distance_km"],
                duration_sec=run_data["duration_sec"],
                avg_pace_s_per_km=avg_pace,
                rpe=5,
                notes=f"Test run {run_data['days_ago']} days ago",
                training_load=run_data["training_load"],
                gps_route=[],
                hr_data=[],
                splits=[]
            )
            
            print(f"Creating test run: {run_data['distance_km']}km in {run_data['duration_sec']}s ({run_data['days_ago']} days ago)")
            db.add(test_run)
        
        db.commit()
        print(f"✅ {len(test_runs)} test runs created successfully!")
        
        # Test querying runs
        all_runs = db.query(CompletedRun).filter(CompletedRun.user_id == test_user.id).all()
        print(f"✅ Total runs for user: {len(all_runs)}")
        
        # Show recent runs (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_runs = db.query(CompletedRun).filter(
            CompletedRun.user_id == test_user.id,
            CompletedRun.start_datetime >= thirty_days_ago
        ).all()
        print(f"✅ Recent runs (last 30 days): {len(recent_runs)}")
        
        # Show run details
        for run in recent_runs:
            print(f"  - {run.distance_km}km in {run.duration_sec}s on {run.start_datetime.strftime('%Y-%m-%d')}")
            
    except Exception as e:
        print(f"❌ Error creating test runs: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_run_creation()