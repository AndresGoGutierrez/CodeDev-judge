from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, JSON, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.models.enumsModel import SubmissionStatus

from src.models.baseModel import Base

class Submission(Base):
    __tablename__ = "submissions"

    id_submission = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id_problem"), nullable=False)
    language_id = Column(Integer)
    language_submission = Column(String)
    sourceCode = Column(Text)
    status_submission = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    execution_time = Column(Float, nullable=True)
    memory_used = Column(Integer, nullable=True)
    judge0_token = Column(String, nullable=True)

    result = Column(JSON, nullable=True)  # Added nullable=True to avoid errors
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Added
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  # Added

    problem = relationship("Problem", back_populates="submissions")
    results = relationship("TestResult", back_populates="submission", cascade="all, delete-orphan")