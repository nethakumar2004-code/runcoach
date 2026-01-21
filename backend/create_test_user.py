#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models.user import User
from app.dependencies import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("Test user already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            return existing_user.id
        
        # Create test user
        test_user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            name="Test User",
            experience_level="intermediate"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("Test user created successfully!")
        print(f"User ID: {test_user.id}")
        print(f"Email: {test_user.email}")
        print("Password: password123")
        
        return test_user.id
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()