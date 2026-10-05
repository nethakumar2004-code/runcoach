#!/usr/bin/env python3
"""
Initialize database tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.migrations import run_migrations

def init_database():
    print("Creating / upgrading database tables...")
    run_migrations()
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()