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
    Obtener lista de problemas públicos.
    Opcionalmente filtrar por dificultad.
    """
    query = db.query(Problem).filter(Problem.is_public == True)
    
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    
    problems = query.offset(skip).limit(limit).all()
    return problems


@router.get("/{problem_id}", response_model=schemas.ProblemPublic)
def get_problem(problem_id: int = Path(..., description="ID del problema"), db: Session = Depends(get_db)):
    """
    Obtener un problema específico por ID.
    Solo incluye casos de prueba marcados como ejemplos.
    """
    problem = db.query(Problem).filter(
        Problem.id_problem == problem_id,
        Problem.is_public == True
    ).first()
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Filtrar solo los casos de prueba de ejemplo
    problem.sample_test_cases = [tc for tc in problem.test_cases if tc.is_sample]
    
    return problem

@router.post("/", response_model=schemas.Problem, dependencies=[Depends(is_moderator)])
def create_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo problema con sus casos de prueba.
    Requiere rol de moderador o admin.
    """
    # Crear el problema
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
    
    # Crear los casos de prueba
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
    problem_id: int = Path(..., description="ID del problema"),
    db: Session = Depends(get_db)
):
    """
    Actualizar un problema existente.
    Requiere rol de admin.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Actualizar los campos proporcionados
    update_data = problem_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_problem, key, value)
    
    db.commit()
    db.refresh(db_problem)
    
    return db_problem

@router.delete("/{problem_id}", response_model=dict, dependencies=[Depends(is_admin)])
def delete_problem(
    problem_id: int = Path(..., description="ID del problema"),
    db: Session = Depends(get_db)
):
    """
    Eliminar un problema y sus casos de prueba.
    Requiere rol de admin.
    """
    db_problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    
    if not db_problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    # Eliminar el problema (los casos de prueba se eliminarán en cascada)
    db.delete(db_problem)
    db.commit()
    
    return {"message": "Problema eliminado correctamente"}

@router.post("/{problem_id}/test-cases", response_model=schemas.TestCase, dependencies=[Depends(is_moderator)])
def add_test_case(
    test_case: schemas.TestCaseCreate,
    problem_id: int = Path(..., description="ID del problema"),
    db: Session = Depends(get_db)
):
    """
    Añadir un nuevo caso de prueba a un problema existente.
    Requiere rol de moderador o admin.
    """
    # Verificar que el problema existe
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    try:
        # Crear el caso de prueba
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
        # Manejo de errores de base de datos
        db.rollback()  # Revertir cualquier cambio si ocurre un error
        raise HTTPException(status_code=500, detail=f"Error al crear el test case: {str(e)}")

@router.get("/{problem_id}/test-cases", response_model=List[schemas.TestCase], dependencies=[Depends(is_authenticated)])
def get_test_cases(
    problem_id: int = Path(..., description="ID del problema"),
    only_samples: bool = False,
    db: Session = Depends(get_db)
):
    """
    Obtener todos los casos de prueba de un problema.
    Opcionalmente filtrar solo por casos de ejemplo.
    Requiere autenticación.
    """
    # Verificar que el problema existe
    problem = db.query(Problem).filter(Problem.id_problem == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    
    try:
        # Consultar casos de prueba
        query = db.query(TestCase).filter(TestCase.problem_id == problem_id)
        
        if only_samples:
            query = query.filter(TestCase.is_sample == True)
        
        # Si deseas agregar paginación, puedes hacerlo aquí (opcional)
        test_cases = query.order_by(TestCase.order).all()
        
        return test_cases
    
    except exc.SQLAlchemyError as e:
        # Manejo de errores en la consulta
        raise HTTPException(status_code=500, detail=f"Error al obtener los casos de prueba: {str(e)}")

@router.delete("/{problem_id}/test-cases/{test_case_id}", response_model=dict, dependencies=[Depends(is_admin)])
def delete_test_case(
    problem_id: int = Path(..., description="ID del problema"),
    test_case_id: int = Path(..., description="ID del caso de prueba"),
    db: Session = Depends(get_db)
):
    """
    Eliminar un caso de prueba específico.
    Requiere rol de admin.
    """
    # Verificar que el caso de prueba existe y pertenece al problema
    test_case = db.query(TestCase).filter(
        TestCase.id_test == test_case_id,
        TestCase.problem_id == problem_id
    ).first()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Caso de prueba no encontrado")
    
    # Eliminar el caso de prueba
    db.delete(test_case)
    db.commit()
    
    return {"message": "Caso de prueba eliminado correctamente"}
