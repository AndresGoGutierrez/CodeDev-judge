from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import exc

from src.core.db_postgres import get_db
from src.models.problemModel import Problem
from src.models.testcaseModel import TestCase
from src.schemas import problem as schemas
from src.core.auth import is_authenticated, is_admin, is_moderator

router = APIRouter()

@router.get("/", response_model=List[schemas.ProblemPublic])
def get_problems(
    skip: int = 0, 
    limit: int = 100, 
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of public problems.
    Optionally filter by difficulty.
    """
    query = db.query(Problem).filter(Problem.is_public == True)
    
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    
    problems = query.offset(skip).limit(limit).all()
    return problems


@router.get("/{problem_id}", response_model=schemas.ProblemPublic)
def get_problem(problem_id: int = Path(..., description="Problem ID"), db: Session = Depends(get_db)):
    """
    Get a specific problem by ID.
    Includes only test cases marked as examples.
    """
    problem = db.query(Problem).filter(
        Problem.id_problem == problem_id,
        Problem.is_public == True
    ).first()
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Filter only example test cases
    problem.test_cases = [tc for tc in problem.test_cases if tc.is_sample]
    
    return problem

@router.post("/", response_model=schemas.Problem, dependencies=[Depends(is_moderator)])
def create_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    """
    Create a new problem with its test cases.
    Requires moderator or admin role.
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

@router.put("/{problem_id}", response_model=schemas.Problem, dependencies=[Depends(is_admin)])
def update_problem(
    problem_update: schemas.ProblemUpdate,
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db)
):
    """
    Update an existing problem.
    Requires admin role.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Update provided fields
    update_data = problem_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_problem, key, value)
    
    db.commit()
    db.refresh(db_problem)
    
    return db_problem

@router.delete("/{problem_id}", response_model=dict, dependencies=[Depends(is_admin)])
def delete_problem(
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db)
):
    """
    Delete a problem and its test cases.
    Requires admin role.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Delete the problem (test cases will be deleted via cascade)
    db.delete(db_problem)
    db.commit()
    
    return {"message": "Problem successfully deleted"}

@router.post("/{problem_id}/test-cases", response_model=schemas.TestCase, dependencies=[Depends(is_moderator)])
def add_test_case(
    test_case: schemas.TestCaseCreate,
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db)
):
    """
    Add a new test case to an existing problem.
    Requires moderator or admin role.
    """
    # Verify the problem exists
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
        db.rollback()  # Revert any changes if an error occurs
        raise HTTPException(status_code=500, detail=f"Error creating test case: {str(e)}")

@router.get("/{problem_id}/test-cases", response_model=List[schemas.TestCase], dependencies=[Depends(is_authenticated)])
def get_test_cases(
    problem_id: int = Path(..., description="Problem ID"),
    only_samples: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all test cases of a problem.
    Optionally filter only example cases.
    Requires authentication.
    """
    # Verify the problem exists
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    try:
        # Query test cases
        query = db.query(TestCase).filter(TestCase.problem_id == problem_id)
        
        if only_samples:
            query = query.filter(TestCase.is_sample == True)
        
        # If you want to add pagination, you can do it here (optional)
        test_cases = query.order_by(TestCase.order).all()
        
        return test_cases
    
    except exc.SQLAlchemyError as e:
        # Handle query errors
        raise HTTPException(status_code=500, detail=f"Error fetching test cases: {str(e)}")

@router.delete("/{problem_id}/test-cases/{test_case_id}", response_model=dict, dependencies=[Depends(is_admin)])
def delete_test_case(
    problem_id: int = Path(..., description="Problem ID"),
    test_case_id: int = Path(..., description="Test case ID"),
    db: Session = Depends(get_db)
):
    """
    Delete a specific test case.
    Requires admin role.
    """
    # Verify the test case exists and belongs to the problem
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
