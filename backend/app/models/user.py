from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)  # beginner/intermediate/advanced

    # Note: Relationships commented out to avoid circular import issues
    # training_plans = relationship("UserTrainingPlan", back_populates="user")
    # weather_alerts = relationship("WeatherAlert", back_populates="user")
