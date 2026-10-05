from sqlalchemy import Column, String, Integer, Date, ForeignKey, Text
import uuid
from app.db import Base

class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"

    # Plain strings like every other table: the Postgres-only UUID type crashed table creation on SQLite
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # easy, long, interval, tempo, rest
    target_distance_km = Column(Integer, nullable=True)
    target_intensity = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
