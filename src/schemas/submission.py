from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from src.models.enumsModel import SubmissionStatus

class TestResultBase(BaseModel):
    status: SubmissionStatus = Field(..., alias="status_test")
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    output: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None

class TestResult(TestResultBase):
    id: int
    submission_id: int
    test_case_id: int
    judge0_token: Optional[str] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SubmissionBase(BaseModel):
    problem_id: int
    language: str = Field(..., alias="language_submission")
    language_id: int = Field(..., description="ID del lenguaje de programación")
    code: str = Field(..., alias="sourceCode")
    user_id: str = Field(..., description="ID del usuario (de otro microservicio)")

class SubmissionCreate(SubmissionBase):
    pass

class Submission(SubmissionBase):
    id: int = Field(..., alias="id_submission")
    status: SubmissionStatus = Field(..., alias="status_submission")
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    judge0_token: Optional[str] = None
    results: List[TestResult] = []

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SubmissionPublic(BaseModel):
    id: int = Field(..., alias="id_submission")
    problem_id: int
    user_id: str
    language: str = Field(..., alias="language_submission")
    status: SubmissionStatus = Field(..., alias="status_submission")
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class Judge0Submission(BaseModel):
    source_code: str
    language_id: int
    stdin: str = ""
    expected_output: Optional[str] = None
    cpu_time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    stack_limit: Optional[int] = None
    max_processes_and_or_threads: Optional[int] = None
    enable_per_process_and_thread_time_limit: Optional[bool] = None
    enable_per_process_and_thread_memory_limit: Optional[bool] = None
    callback_url: Optional[str] = None

class Judge0Response(BaseModel):
    token: str

class Judge0Result(BaseModel):
    token: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    exit_code: Optional[int] = None
    exit_signal: Optional[int] = None
    status: Dict[str, Any]
    created_at: Optional[str] = ""  # Cambiado a opcional con valor por defecto
    finished_at: Optional[str] = None
    time: Optional[float] = None
    memory: Optional[int] = None