from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey
import uuid
from app.db import Base

class Goal(Base):
    __tablename__ = "goals"

    # Plain strings like every other table: the Postgres-only UUID type crashed table creation on SQLite
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    race_distance = Column(String, nullable=False)  # 5k, 10k, half, marathon
    race_date = Column(Date, nullable=False)
    target_time_seconds = Column(Integer, nullable=False)
    training_days_per_week = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
