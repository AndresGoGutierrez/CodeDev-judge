from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from src.core.db_postgres import get_db
from src.models.problemModel import Problem
from src.models.testcaseModel import TestCase
from src.schemas import problem as schemas
from src.middleware.admin_middleware import is_admin

router = APIRouter(prefix="/api/admin/problems")

@router.get("/", response_model=List[schemas.Problem])
async def get_all_problems(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Get all problems (including non-public ones).
    Accessible only to administrators.
    """
    problems = db.query(Problem).offset(skip).limit(limit).all()
    return problems

@router.get("/{problem_id}", response_model=schemas.Problem)
async def get_problem_detail(
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Get full details of a specific problem.
    Accessible only to administrators.
    """
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    return problem

@router.post("/", response_model=schemas.Problem)
async def create_problem(
    problem: schemas.ProblemCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Create a new problem with its test cases.
    Accessible only to administrators.
    """
    # Create the problem
    db_problem = Problem(
        title=problem.title,
        description=problem.description,
        inputFormat=problem.inputFormat,
        outputFormat=problem.outputFormat,
        constraints=problem.constraints,
        tags=problem.tags,
        difficulty=problem.difficulty,
        time_limit=problem.time_limit,
        memory_limit=problem.memory_limit,
        is_public=problem.is_public,
        external_id=problem.external_id
    )
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    
    # Create the test cases
    for test_case in problem.test_cases:
        db_test_case = TestCase(
            problem_id=db_problem.id_problem,
            input_data=test_case.input_data,
            expected_output=test_case.expected_output,
            is_sample=test_case.is_sample,
            order=test_case.order
        )
        db.add(db_test_case)
    
    db.commit()
    db.refresh(db_problem)
    
    return db_problem

@router.put("/{problem_id}", response_model=schemas.Problem)
async def update_problem(
    problem_update: schemas.ProblemUpdate,
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Update an existing problem.
    Accessible only to administrators.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Update the provided fields
    update_data = problem_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_problem, key, value)
    
    db.commit()
    db.refresh(db_problem)
    
    return db_problem

@router.delete("/{problem_id}", response_model=dict)
async def delete_problem(
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Delete a problem and its test cases.
    Accessible only to administrators.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Delete the problem (test cases will be deleted via cascade)
    db.delete(db_problem)
    db.commit()
    
    return {"message": "Problem successfully deleted"}

@router.post("/{problem_id}/testcases", response_model=schemas.TestCase)
async def add_test_case(
    test_case: schemas.TestCaseCreate,
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Add a new test case to an existing problem.
    Accessible only to administrators.
    """
    # Check if the problem exists
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    try:
        # Create the test case
        db_test_case = TestCase(
            problem_id=problem_id,
            input_data=test_case.input_data,
            expected_output=test_case.expected_output,
            is_sample=test_case.is_sample,
            order=test_case.order
        )
        
        db.add(db_test_case)
        db.commit()
        db.refresh(db_test_case)
        
        return db_test_case
    
    except Exception as e:
        # Handle database errors
        db.rollback()  # Roll back any changes if an error occurs
        raise HTTPException(status_code=500, detail=f"Error creating the test case: {str(e)}")

@router.delete("/{problem_id}/testcases/{test_case_id}", response_model=dict)
async def delete_test_case(
    problem_id: int = Path(..., description="Problem ID"),
    test_case_id: int = Path(..., description="Test case ID"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Delete a specific test case.
    Accessible only to administrators.
    """
    # Check if the test case exists and belongs to the problem
    test_case = db.query(TestCase).filter(
        TestCase.id_test == test_case_id,
        TestCase.problem_id == problem_id
    ).first()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Delete the test case
    db.delete(test_case)
    db.commit()
    
    return {"message": "Test case successfully deleted"}
