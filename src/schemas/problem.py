from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TestCaseBase(BaseModel):
    input_data: str
    expected_output: str
    is_sample: bool = False
    order: int = 0

class TestCaseCreate(TestCaseBase):
    pass

class TestCase(TestCaseBase):
    id_test: int  # Añadido el campo id_test que faltaba
    problem_id: int  # Mantener solo problem_id, eliminar id_problem

    class Config:
        orm_mode = True

class ProblemBase(BaseModel):
    title: str
    description: str
    inputFormat: Optional[str] = None
    outputFormat: Optional[str] = None
    constraints: Optional[str] = None
    difficulty: str = Field(..., description="Dificultad: easy, medium, hard")
    time_limit: float = Field(1.0, description="Tiempo límite en segundos")
    memory_limit: int = Field(256, description="Memoria límite en MB")
    is_public: bool = True
    external_id: Optional[str] = None
    tags: Optional[str] = None

class ProblemCreate(ProblemBase):
    test_cases: List[TestCaseCreate]

class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    inputFormat: Optional[str] = None
    outputFormat: Optional[str] = None
    constraints: Optional[str] = None
    difficulty: Optional[str] = None
    time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    is_public: Optional[bool] = None
    external_id: Optional[str] = None
    tags: Optional[str] = None

class Problem(ProblemBase):
    id_problem: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    test_cases: List[TestCase] = []

    class Config:
        orm_mode = True

class ProblemPublic(BaseModel):
    id_problem: int
    title: str
    description: str
    difficulty: str
    time_limit: float
    memory_limit: int
    sample_test_cases: List[TestCase] = []

    class Config:
        orm_mode = True