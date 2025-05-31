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
    Processes a submission, running the code against all test cases.
    """
    # Get the submission
    submission = db.query(Submission).filter(Submission.id_submission == submission_id).first()
    if not submission:
        raise ValueError(f"Submission {submission_id} not found")
    
    # Update status to "processing"
    submission.status = SubmissionStatus.PROCESSING
    db.commit()
    
    try:
        # Get the problem and its test cases
        problem = db.query(Problem).filter(Problem.id_problem == submission.problem_id).first()
        if not problem:
            raise ValueError(f"Problem {submission.problem_id} not found")
        
        test_cases = db.query(TestCase).filter(
            TestCase.problem_id == problem.id_problem
        ).order_by(TestCase.order).all()
        
        if not test_cases:
            raise ValueError(f"No test cases found for problem {problem.id}")
        
        # Get the language ID for Judge0
        language_id = settings.LANGUAGE_MAP.get(submission.language_id)
        if not language_id:
            raise ValueError(f"Unsupported language: {submission.language_id}")
        
        JUDGE0_MAX_MEMORY_KB = 512000
        
        # Prepare submissions for Judge0 (one per test case)
        judge0_submissions = []
        for test_case in test_cases:
            judge0_sub = Judge0Submission(
                source_code=submission.sourceCode,
                language_id=language_id,
                stdin=test_case.input_data,
                expected_output=test_case.expected_output,
                cpu_time_limit=problem.time_limit,
                memory_limit=min(problem.memory_limit * 1024, JUDGE0_MAX_MEMORY_KB),  # Convert MB to KB
                max_processes_and_or_threads=60,
                enable_per_process_and_thread_time_limit=True,
                enable_per_process_and_thread_memory_limit=True
            )
            judge0_submissions.append((test_case.id_test, judge0_sub))
        
        # Submit all test cases to Judge0
        responses = await judge0_client.batch_submit([sub for _, sub in judge0_submissions])
        
        # Map tokens to test cases
        token_to_test_case = {}
        for i, (test_case_id, _) in enumerate(judge0_submissions):
            token_to_test_case[responses[i].token] = test_case_id
        
        # Wait for and get all results
        tokens = [resp.token for resp in responses]
        results = await wait_for_all_results(tokens)
        
        # Process results
        all_passed = True
        max_time = 0
        max_memory = 0
        
        for token, result in results.items():
            test_case_id = token_to_test_case[token]
            
            # Determine the result status
            status = map_judge0_status_to_submission_status(result.status["id"])
            
            if status != SubmissionStatus.ACCEPTED:
                all_passed = False
            
            # Update statistics
            if result.time and result.time > max_time:
                max_time = result.time
            if result.memory and result.memory > max_memory:
                max_memory = result.memory
            
            # Save the result for this test case
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
        
        # Update the final status of the submission
        submission.status_submission = SubmissionStatus.ACCEPTED if all_passed else SubmissionStatus.WRONG_ANSWER
        submission.execution_time = max_time
        submission.memory_used = max_memory
        
        db.commit()
        db.refresh(submission)
        
        return submission
    
    except Exception as e:
        # In case of error, update the submission status
        submission.status_submission = SubmissionStatus.SYSTEM_ERROR
        db.commit()
        raise e


async def wait_for_all_results(tokens: List[str], max_attempts: int = 20, initial_delay: float = 0.5) -> Dict[str, Any]:
    """
    Waits and polls periodically until all results are obtained.
    """
    results = {}
    pending_tokens = set(tokens)
    delay = initial_delay
    
    for attempt in range(max_attempts):
        if not pending_tokens:
            break
        
        # Query pending results
        batch_results = await judge0_client.batch_get_results(list(pending_tokens))
        
        # Process results
        for result in batch_results:
            # If the result is complete, save it
            if result.status["id"] >= 3:  # 3 or higher means no longer queued or processing
                results[result.token] = result
                pending_tokens.remove(result.token)
        
        # If there are still pending, wait before querying again
        if pending_tokens:
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)  # Gradually increase wait time, max 5 seconds
    
    # If there are still pending tokens, mark them as error
    if pending_tokens:
        for token in pending_tokens:
            results[token] = {
                "token": token,
                "status": {"id": 13, "description": "Internal Error"},  # 13 is Internal Error in Judge0
                "time": None,
                "memory": None
            }
    
    return results

def map_judge0_status_to_submission_status(judge0_status_id: int) -> SubmissionStatus:
    """
    Maps Judge0 status codes to our submission statuses.
    
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