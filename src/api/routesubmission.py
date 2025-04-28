from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Query
from sqlalchemy.orm import Session
from src.core.db_postgres import get_db

from src.models.problemModel import Problem
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult
from src.models.enumsModel import SubmissionStatus

from src.schemas import submission as schemas

from src.services.evaluator import process_submission

router = APIRouter()

@router.post("/", response_model=schemas.SubmissionPublic)
async def create_submission(
    submission: schemas.SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo envío de código y ponerlo en cola para evaluación.
    """
    # Verificar que el problema existe
    problem = db.query(Problem).filter(Problem.id_problem == submission.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Crear el envío en la base de datos usando los nombres de columnas correctos
    db_submission = Submission(
        user_id=submission.user_id,
        problem_id=submission.problem_id,
        sourceCode=submission.code,  # Usar el nombre de la columna en la base de datos
        language_id=submission.language_id,  # Añadido language_id
        language_submission=submission.language,  # Usar el nombre de la columna en la base de datos
        status_submission=SubmissionStatus.PENDING  # Usar el nombre de la columna en la base de datos
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Procesar el envío en segundo plano
    background_tasks.add_task(
        process_submission, 
        submission_id=db_submission.id_submission,  # Usar id_submission en lugar de id
        db=db
    )
    
    return db_submission

@router.get("/", response_model=List[schemas.SubmissionPublic])
def get_submissions(
    skip: int = 0, 
    limit: int = 100,
    user_id: Optional[str] = None,
    problem_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener lista de envíos con filtros opcionales.
    """
    query = db.query(Submission)
    
    # Aplicar filtros
    if user_id:
        query = query.filter(Submission.user_id == user_id)
    
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if status:
        query = query.filter(Submission.status == status)
    
    # Ordenar por fecha de creación descendente (más recientes primero)
    query = query.order_by(Submission.created_at.desc())
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions


@router.get("/{submission_id}", response_model=schemas.Submission)
def get_submission(
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Obtener un envío específico por ID, incluyendo resultados de pruebas.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    return submission


@router.get("/{submission_id}/results", response_model=List[schemas.TestResult])
def get_submission_results(
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Obtener los resultados de las pruebas para un envío específico.
    """
    # Verificar que el envío existe
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Obtener resultados
    results = db.query(TestResult).filter(
        TestResult.submission_id == submission_id
    ).all()
    
    return results

@router.post("/{submission_id}/reprocess", response_model=schemas.SubmissionPublic)
async def reprocess_submission(
    background_tasks: BackgroundTasks,
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Reprocesar un envío existente.
    """
    # Verificar que el envío existe
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Eliminar resultados anteriores
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    # Actualizar estado a pendiente
    submission.status_submission = SubmissionStatus.PENDING
    submission.execution_time = None
    submission.memory_used = None
    db.commit()
    db.refresh(submission)
    
    # Procesar el envío en segundo plano
    background_tasks.add_task(
        process_submission, 
        submission_id=submission.id_submission,
        db=db
    )
    
    return submission
