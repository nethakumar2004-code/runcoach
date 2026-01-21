#!/usr/bin/env python3
"""
Add test runs for analytics testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.db import get_db
from app.models.run import CompletedRun
from app.models.user import User

def add_test_runs():
    db = next(get_db())
    
    # Get the test user (assuming user ID 1 exists)
    user = db.query(User).first()
    if not user:
        print("No user found. Please create a user first.")
        return
    
    print(f"Adding test runs for user: {user.email}")
    
    # Add 5 test runs over the last 30 days
    test_runs = [
        {
            "days_ago": 2,
            "distance_km": 5.0,
            "duration_sec": 1500,  # 25 minutes (5:00/km pace)
            "training_load": 75.0
        },
        {
            "days_ago": 5,
            "distance_km": 3.0,
            "duration_sec": 900,   # 15 minutes (5:00/km pace)
            "training_load": 55.0
        },
        {
            "days_ago": 8,
            "distance_km": 7.0,
            "duration_sec": 2100,  # 35 minutes (5:00/km pace)
            "training_load": 95.0
        },
        {
            "days_ago": 12,
            "distance_km": 4.0,
            "duration_sec": 1200,  # 20 minutes (5:00/km pace)
            "training_load": 65.0
        },
        {
            "days_ago": 15,
            "distance_km": 6.0,
            "duration_sec": 1800,  # 30 minutes (5:00/km pace)
            "training_load": 85.0
        }
    ]
    
    for run_data in test_runs:
        start_time = datetime.utcnow() - timedelta(days=run_data["days_ago"])
        
        # Calculate pace (seconds per km)
        avg_pace = run_data["duration_sec"] / run_data["distance_km"]
        
        new_run = CompletedRun(
            user_id=user.id,
            start_datetime=start_time,
            distance_km=run_data["distance_km"],
            duration_sec=run_data["duration_sec"],
            avg_pace_s_per_km=avg_pace,
            training_load=run_data["training_load"]
        )
        
        db.add(new_run)
        print(f"Added run: {run_data['distance_km']}km in {run_data['duration_sec']}s ({run_data['days_ago']} days ago)")
    
    db.commit()
    print("Test runs added successfully!")

if __name__ == "__main__":
    add_test_runs()