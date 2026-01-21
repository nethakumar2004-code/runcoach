from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db import Base

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, accepted, blocked
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    addressee = relationship("User", foreign_keys=[addressee_id])

class ActivityFeed(Base):
    __tablename__ = "activity_feed"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)  # run_completed, achievement_earned, goal_achieved
    activity_data = Column(Text, nullable=True)  # JSON data about the activity
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_public = Column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User")

class ActivityLike(Base):
    __tablename__ = "activity_likes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id = Column(String, ForeignKey("activity_feed.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    activity = relationship("ActivityFeed")
    user = relationship("User")

class ActivityComment(Base):
    __tablename__ = "activity_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id = Column(String, ForeignKey("activity_feed.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    activity = relationship("ActivityFeed")
    user = relationship("User")

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    challenge_type = Column(String, nullable=False)  # distance, time, frequency
    target_value = Column(Integer, nullable=False)  # target distance/time/runs
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    creator = relationship("User")

class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    challenge_id = Column(String, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    current_progress = Column(Integer, nullable=False, default=0)
    completed = Column(Boolean, nullable=False, default=False)

    # Relationships
    challenge = relationship("Challenge")
    user = relationship("User")

class Kudos(Base):
    __tablename__ = "kudos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("completed_runs.id"), nullable=False)
    giver_id = Column(String, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    run = relationship("CompletedRun")
    giver = relationship("User", foreign_keys=[giver_id])
    receiver = relationship("User", foreign_keys=[receiver_id])