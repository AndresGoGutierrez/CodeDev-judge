from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship


from src.models.baseModel import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    id_test = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id_problem"), nullable=False)
    input_data = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    problem = relationship("Problem", back_populates="test_cases")
    results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")
