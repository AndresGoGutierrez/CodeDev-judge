from sqlalchemy import Column, String, Integer, ForeignKey, Float, Text, Enum, JSON
from sqlalchemy.orm import relationship

from src.models.enumsModel import SubmissionStatus


from src.models.baseModel import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("submissions.id_submission"), nullable=False
    )
    test_case_id = Column(Integer, ForeignKey("test_cases.id_test"), nullable=False)
    status_test = Column(Enum(SubmissionStatus))
    execution_time = Column(Float, nullable=True)
    memory_used = Column(Integer, nullable=True)
    output = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    judge0_token = Column(String, nullable=True)
    judge0_response = Column(JSON, nullable=True)

    submission = relationship("Submission", back_populates="results")
    test_case = relationship("TestCase", back_populates="results")
