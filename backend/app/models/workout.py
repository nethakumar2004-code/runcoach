from sqlalchemy import Column, String, Integer, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base

class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # easy, long, interval, tempo, rest
    target_distance_km = Column(Integer, nullable=True)
    target_intensity = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
