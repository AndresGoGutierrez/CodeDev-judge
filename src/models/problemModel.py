from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


from src.models.baseModel import Base

class Problem(Base):
    __tablename__ = "problems"

    id_problem = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    inputFormat = Column(String)
    outputFormat = Column(String)
    constraints = Column(String)
    difficulty = Column(String)
    time_limit = Column(Float, default=1.0)
    memory_limit = Column(Integer, default=256)
    is_public = Column(Boolean, default=True)
    tags = Column(String)
    external_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem")
