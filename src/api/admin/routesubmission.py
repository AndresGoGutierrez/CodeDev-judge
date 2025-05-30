from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session

from src.core.db_postgres import get_db
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult
from src.schemas import submission as schemas
from src.middleware.admin_middleware import is_admin
from src.services.evaluator import process_submission

router = APIRouter(prefix="/api/admin/submissions")

@router.get("/", response_model=List[schemas.SubmissionPublic])
async def get_all_submissions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    problem_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Obtener todos los envíos con filtros opcionales.
    Solo accesible para administradores.
    """
    query = db.query(Submission)
    
    # Aplicar filtros
    if user_id:
        query = query.filter(Submission.user_id == user_id)
    
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if status:
        query = query.filter(Submission.status_submission == status)
    
    # Ordenar por fecha de creación descendente (más recientes primero)
    query = query.order_by(Submission.created_at.desc())
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions

@router.get("/{submission_id}", response_model=schemas.Submission)
async def get_submission_detail(
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Obtener detalles completos de un envío específico.
    Solo accesible para administradores.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    return submission

@router.post("/{submission_id}/reprocess", response_model=schemas.SubmissionPublic)
async def reprocess_submission(
    background_tasks: BackgroundTasks,
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Reprocesar un envío existente.
    Solo accesible para administradores.
    """
    # Verificar que el envío existe
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Eliminar resultados anteriores
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    # Actualizar estado a pendiente
    submission.status_submission = "PENDING"
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

@router.delete("/{submission_id}", response_model=dict)
async def delete_submission(
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Eliminar un envío específico.
    Solo accesible para administradores.
    """
    # Verificar que el envío existe
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Eliminar resultados asociados
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    # Eliminar el envío
    db.delete(submission)
    db.commit()
    
    return {"message": "Envío eliminado correctamente"}
