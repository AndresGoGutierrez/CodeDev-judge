from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from src.models.problemModel import Problem
from src.models.testcaseModel import TestCase
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult
from src.models.enumsModel import SubmissionStatus

from src.services.judge0 import judge0_client, Judge0Submission
from src.core.config import settings

import asyncio
import json

async def process_submission(submission_id: int, db: Session) -> Submission:
    """
    Procesa un envío, ejecutando el código contra todos los casos de prueba.
    """
    # Obtener el envío
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise ValueError(f"Envío {submission_id} no encontrado")
    
    # Actualizar estado a "processing"
    submission.status = SubmissionStatus.PROCESSING
    db.commit()
    
    try:
        # Obtener el problema y sus casos de prueba
        problem = db.query(Problem).filter(Problem.id_problem == submission.problem_id).first()
        if not problem:
            raise ValueError(f"Problema {submission.problem_id} no encontrado")
        
        test_cases = db.query(TestCase).filter(
            TestCase.problem_id == problem.id_problem
        ).order_by(TestCase.order).all()
        
        if not test_cases:
            raise ValueError(f"No hay casos de prueba para el problema {problem.id}")
        
        # Obtener el ID del lenguaje para Judge0
        language_id = settings.LANGUAGE_MAP.get(submission.language_id)
        if not language_id:
            raise ValueError(f"Lenguaje no soportado: {submission.language_id}")
        
        JUDGE0_MAX_MEMORY_KB = 512000
        
        # Preparar envíos para Judge0 (uno por cada caso de prueba)
        judge0_submissions = []
        for test_case in test_cases:
            judge0_sub = Judge0Submission(
                source_code=submission.sourceCode,
                language_id=language_id,
                stdin=test_case.input_data,
                expected_output=test_case.expected_output,
                cpu_time_limit=problem.time_limit,
                memory_limit=min(problem.memory_limit * 1024, JUDGE0_MAX_MEMORY_KB),  # Convertir MB a KB
                max_processes_and_or_threads=60,
                enable_per_process_and_thread_time_limit=True,
                enable_per_process_and_thread_memory_limit=True
            )
            judge0_submissions.append((test_case.id_test, judge0_sub))
        
        # Enviar todos los casos de prueba a Judge0
        responses = await judge0_client.batch_submit([sub for _, sub in judge0_submissions])
        
        # Mapear tokens a casos de prueba
        token_to_test_case = {}
        for i, (test_case_id, _) in enumerate(judge0_submissions):
            token_to_test_case[responses[i].token] = test_case_id
        
        # Esperar y obtener todos los resultados
        tokens = [resp.token for resp in responses]
        results = await wait_for_all_results(tokens)
        
        # Procesar resultados
        all_passed = True
        max_time = 0
        max_memory = 0
        
        for token, result in results.items():
            test_case_id = token_to_test_case[token]
            
            # Determinar el estado del resultado
            status = map_judge0_status_to_submission_status(result.status["id"])
            
            if status != SubmissionStatus.ACCEPTED:
                all_passed = False
            
            # Actualizar estadísticas
            if result.time and result.time > max_time:
                max_time = result.time
            if result.memory and result.memory > max_memory:
                max_memory = result.memory
            
            # Guardar el resultado de este caso de prueba
            test_result = TestResult(
                submission_id=submission.id_submission,
                test_case_id=test_case_id,
                status_test=status,
                execution_time=result.time,
                memory_used=result.memory,
                output=result.stdout,
                stderr=result.stderr,
                compile_output=result.compile_output,
                judge0_token=token,
                judge0_response=result.dict()
            )
            db.add(test_result)
        
        # Actualizar el estado final del envío
        submission.status_submission = SubmissionStatus.ACCEPTED if all_passed else SubmissionStatus.WRONG_ANSWER
        submission.execution_time = max_time
        submission.memory_used = max_memory
        
        db.commit()
        db.refresh(submission)
        
        return submission
    
    except Exception as e:
        # En caso de error, actualizar el estado del envío
        submission.status_submission = SubmissionStatus.SYSTEM_ERROR
        db.commit()
        raise e


async def wait_for_all_results(tokens: List[str], max_attempts: int = 20, initial_delay: float = 0.5) -> Dict[str, Any]:
    """
    Espera y consulta periódicamente hasta obtener todos los resultados.
    """
    results = {}
    pending_tokens = set(tokens)
    delay = initial_delay
    
    for attempt in range(max_attempts):
        if not pending_tokens:
            break
        
        # Consultar resultados pendientes
        batch_results = await judge0_client.batch_get_results(list(pending_tokens))
        
        # Procesar resultados
        for result in batch_results:
            # Si el resultado está completo, guardarlo
            if result.status["id"] >= 3:  # 3 o mayor significa que ya no está en cola o procesando
                results[result.token] = result
                pending_tokens.remove(result.token)
        
        # Si aún quedan pendientes, esperar antes de consultar de nuevo
        if pending_tokens:
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)  # Aumentar el tiempo de espera gradualmente, máximo 5 segundos
    
    # Si aún quedan tokens pendientes, marcarlos como error
    if pending_tokens:
        for token in pending_tokens:
            results[token] = {
                "token": token,
                "status": {"id": 13, "description": "Internal Error"},  # 13 es Internal Error en Judge0
                "time": None,
                "memory": None
            }
    
    return results

def map_judge0_status_to_submission_status(judge0_status_id: int) -> SubmissionStatus:
    """
    Mapea los códigos de estado de Judge0 a nuestros estados de envío.
    
    Judge0 status codes:
    1 - In Queue, 2 - Processing,
    3 - Accepted, 4 - Wrong Answer, 5 - Time Limit Exceeded,
    6 - Compilation Error, 7 - Runtime Error (SIGSEGV),
    8 - Runtime Error (SIGXFSZ), 9 - Runtime Error (SIGFPE),
    10 - Runtime Error (SIGABRT), 11 - Runtime Error (NZEC),
    12 - Runtime Error (Other), 13 - Internal Error
    """
    status_map = {
        1: SubmissionStatus.IN_QUEUE,
        2: SubmissionStatus.PROCESSING,
        3: SubmissionStatus.ACCEPTED,
        4: SubmissionStatus.WRONG_ANSWER,
        5: SubmissionStatus.TIME_LIMIT_EXCEEDED,
        6: SubmissionStatus.COMPILATION_ERROR,
        7: SubmissionStatus.RUNTIME_ERROR,
        8: SubmissionStatus.RUNTIME_ERROR,
        9: SubmissionStatus.RUNTIME_ERROR,
        10: SubmissionStatus.RUNTIME_ERROR,
        11: SubmissionStatus.RUNTIME_ERROR,
        12: SubmissionStatus.RUNTIME_ERROR,
        13: SubmissionStatus.SYSTEM_ERROR
    }
    
    return status_map.get(judge0_status_id, SubmissionStatus.SYSTEM_ERROR)