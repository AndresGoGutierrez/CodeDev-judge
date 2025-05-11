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
    Crear un nuevo envío de código y ponerlo en cola para evaluación.
    Requiere autenticación.
    """
    # Verificar que el problema existe
    problem = db.query(Problem).filter(Problem.id_problem == submission.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Obtener el ID del usuario del token
    user = request.state.user
    user_id = user.get("id")
    
    # Crear el envío en la base de datos usando los nombres de columnas correctos
    db_submission = Submission(
        user_id=user_id,  # Usar el ID del usuario autenticado
        problem_id=submission.problem_id,
        sourceCode=submission.code,
        language_id=submission.language_id,
        language_submission=submission.language,
        status_submission=SubmissionStatus.PENDING
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Procesar el envío en segundo plano
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
    Obtener lista de envíos con filtros opcionales.
    Requiere autenticación. Los usuarios normales solo pueden ver sus propios envíos.
    Los administradores pueden ver todos los envíos.
    """
    query = db.query(Submission)
    
    # Obtener el usuario actual
    current_user = request.state.user
    user_roles = current_user.get("roles", [])
    
    # Si no es admin, solo puede ver sus propios envíos
    if "admin" not in user_roles and "moderator" not in user_roles:
        query = query.filter(Submission.user_id == current_user.get("id"))
    # Si es admin/moderador y se especifica un user_id, filtrar por ese user_id
    elif user_id:
        query = query.filter(Submission.user_id == user_id)
    
    # Aplicar filtros adicionales
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if status:
        query = query.filter(Submission.status_submission == status)
    
    # Ordenar por fecha de creación descendente (más recientes primero)
    query = query.order_by(Submission.created_at.desc())
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions


@router.get("/{submission_id}", response_model=schemas.Submission)
async def get_submission(
    request: Request,
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Obtener un envío específico por ID, incluyendo resultados de pruebas.
    Los usuarios solo pueden ver sus propios envíos, los administradores pueden ver todos.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Verificar permisos
    await is_owner_or_admin(request, submission.user_id)
    
    return submission


@router.get("/{submission_id}/results", response_model=List[schemas.TestResult])
async def get_submission_results(
    request: Request,
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Obtener los resultados de las pruebas para un envío específico.
    Los usuarios solo pueden ver sus propios resultados, los administradores pueden ver todos.
    """
    # Verificar que el envío existe
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Verificar permisos
    await is_owner_or_admin(request, submission.user_id)
    
    # Obtener resultados
    results = db.query(TestResult).filter(
        TestResult.submission_id == submission_id
    ).all()
    
    return results

@router.post("/{submission_id}/reprocess", response_model=schemas.SubmissionPublic, dependencies=[Depends(is_moderator)])
async def reprocess_submission(
    background_tasks: BackgroundTasks,
    submission_id: int = Path(..., description="ID del envío"),
    db: Session = Depends(get_db)
):
    """
    Reprocesar un envío existente.
    Requiere rol de moderador o admin.
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

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    request: Request,
    submission_id: int = Path(..., description="ID del envío a eliminar"),
    db: Session = Depends(get_db)
):
    """
    Eliminar una submission por su ID.
    Los usuarios solo pueden eliminar sus propios envíos, los administradores pueden eliminar cualquiera.
    """
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    
    # Verificar permisos
    await is_owner_or_admin(request, submission.user_id)
    
    # Eliminar también resultados asociados, si los hay
    db.query(TestResult).filter(TestResult.submission_id == submission_id).delete()
    
    db.delete(submission)
    db.commit()
    
    return

@router.get("/problem/{problem_id}", response_model=List[schemas.SubmissionPublic], dependencies=[Depends(is_authenticated)])
async def get_submissions_by_problem(
    request: Request,
    problem_id: int = Path(..., description="ID del problema"),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los envíos asociados a un problema específico.
    Los usuarios normales solo ven sus propios envíos, los administradores ven todos.
    """
    # Verificar que el problema exista
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Obtener el usuario actual
    current_user = request.state.user
    user_roles = current_user.get("roles", [])
    
    # Construir la consulta
    query = db.query(Submission).filter(Submission.problem_id == problem_id)
    
    # Si no es admin, solo puede ver sus propios envíos
    if "admin" not in user_roles and "moderator" not in user_roles:
        query = query.filter(Submission.user_id == current_user.get("id"))
    
    # Obtener los envíos
    submissions = query.order_by(Submission.created_at.desc()).all()
    
    return submissions
