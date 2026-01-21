from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    race_distance = Column(String, nullable=False)  # 5k, 10k, half, marathon
    race_date = Column(Date, nullable=False)
    target_time_seconds = Column(Integer, nullable=False)
    training_days_per_week = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
