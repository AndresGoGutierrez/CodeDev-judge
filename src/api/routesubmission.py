from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Query, status, Request
from sqlalchemy.orm import Session
from src.core.db_postgres import get_db

from src.models.problemModel import Problem
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult
from src.models.enumsModel import SubmissionStatus

from src.schemas import submission as schemas

from src.services.evaluator import process_submission
from src.core.auth import is_authenticated, is_admin, is_moderator, is_owner_or_admin

router = APIRouter()

@router.post("/", response_model=schemas.SubmissionPublic, dependencies=[Depends(is_authenticated)])
async def create_submission(
    submission: schemas.SubmissionCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new code submission and queue it for evaluation.
    Requires authentication.
    """
    # Check that the problem exists
    problem = db.query(Problem).filter(Problem.id_problem == submission.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Get user ID from token
    user = request.state.user
    user_id = user.get("id")
    
    # Create the submission in the database using the correct column names
    db_submission = Submission(
        user_id=user_id,  # Use authenticated user ID
        problem_id=submission.problem_id,
        sourceCode=submission.code,
        language_id=submission.language_id,
        language_submission=submission.language,
        status_submission=SubmissionStatus.PENDING
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Process the submission in the background
    background_tasks.add_task(
        process_submission, 
        submission_id=db_submission.id_submission,
        db=db
    )
    
    return db_submission

@router.get("/", response_model=List[schemas.SubmissionPublic], dependencies=[Depends(is_authenticated)])
async def get_submissions(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    user_id: Optional[str] = None,
    problem_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of submissions with optional filters.
    Requires authentication. Regular users can only see their own submissions.
    Admins can see all submissions.
    """
    query = db.query(Submission)
    
    # Get current user
    current_user = request.state.user
    user_roles = current_user.get("roles", [])
    
    # If not admin, can only see own submissions
    if "admin" not in user_roles and "moderator" not in user_roles:
        query = query.filter(Submission.user_id == current_user.get("id"))
    # If admin/moderator and user_id is specified, filter by that user_id
    elif user_id:
        query = query.filter(Submission.user_id == user_id)
    
    # Apply additional filters
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if status:
        query = query.filter(Submission.status_submission == status)
    
    # Order by creation date descending (newest first)
    query = query.order_by(Submission.created_at.desc())
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions


@router.get("/{submission_id}", response_model=schemas.Submission)
async def get_submission(
    request: Request,
    submission_id: int = Path(..., description="Submission ID"),
    db: Session = Depends(get_db)
):
    """
    Get a specific submission by ID, including test results.
    Users can only view their own submissions, admins can view all.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    await is_owner_or_admin(request, submission.user_id)
    
    return submission


@router.get("/{submission_id}/results", response_model=List[schemas.TestResult])
async def get_submission_results(
    request: Request,
    submission_id: int = Path(..., description="Submission ID"),
    db: Session = Depends(get_db)
):
    """
    Get the test results for a specific submission.
    Users can only see their own results, admins can see all.
    """
    # Check that the submission exists
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    await is_owner_or_admin(request, submission.user_id)
    
    # Get results
    results = db.query(TestResult).filter(
        TestResult.submission_id == submission_id
    ).all()
    
    return results

@router.post("/{submission_id}/reprocess", response_model=schemas.SubmissionPublic, dependencies=[Depends(is_moderator)])
async def reprocess_submission(
    background_tasks: BackgroundTasks,
    submission_id: int = Path(..., description="Submission ID"),
    db: Session = Depends(get_db)
):
    """
    Reprocess an existing submission.
    Requires moderator or admin role.
    """
    # Check that the submission exists
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Delete previous results
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    # Update status to pending
    submission.status_submission = SubmissionStatus.PENDING
    submission.execution_time = None
    submission.memory_used = None
    db.commit()
    db.refresh(submission)
    
    # Process the submission in the background
    background_tasks.add_task(
        process_submission, 
        submission_id=submission.id_submission,
        db=db
    )
    
    return submission

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    request: Request,
    submission_id: int = Path(..., description="Submission ID to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a submission by its ID.
    Users can only delete their own submissions, admins can delete any.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    await is_owner_or_admin(request, submission.user_id)
    
    # Also delete associated results, if any
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    db.delete(submission)
    db.commit()
    
    return

@router.get("/problem/{problem_id}", response_model=List[schemas.SubmissionPublic], dependencies=[Depends(is_authenticated)])
async def get_submissions_by_problem(
    request: Request,
    problem_id: int = Path(..., description="Problem ID"),
    db: Session = Depends(get_db)
):
    """
    Get all submissions associated with a specific problem.
    Regular users only see their own submissions, admins see all.
    """
    # Check that the problem exists
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Get current user
    current_user = request.state.user
    user_roles = current_user.get("roles", [])
    
    # Build the query
    query = db.query(Submission).filter(Submission.problem_id == problem_id)
    
    # If not admin, only show own submissions
    if "admin" not in user_roles and "moderator" not in user_roles:
        query = query.filter(Submission.user_id == current_user.get("id"))
    
    # Get submissions
    submissions = query.order_by(Submission.created_at.desc()).all()
    
    return submissions
