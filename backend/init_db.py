#!/usr/bin/env python3
"""
Initialize database tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import Base, engine
from app.models import user, goal, workout, run, achievement, social, training_plan, weather

def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_database()