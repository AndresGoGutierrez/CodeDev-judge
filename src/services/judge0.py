import httpx
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.core.config import settings
from src.schemas.submission import Judge0Submission, Judge0Response, Judge0Result

class Judge0Client:
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url
        self.headers = {}
        if auth_token:
            self.headers["X-Auth-Token"] = auth_token
    
    async def submit(self, submission: Judge0Submission) -> Judge0Response:
        """
        Sends code to be evaluated without base64 encoding.
        """
        # Prepare payload without base64 encoding
        payload = submission.dict()
        
        # Use the source code as is
        source_code = payload.get("source_code") or payload.get("sourceCode")
        if source_code:
            payload["source_code"] = source_code
            
            # Remove sourceCode if it exists to avoid confusion
            if "sourceCode" in payload:
                del payload["sourceCode"]
        
        # Do not use base64
        payload["base64_encoded"] = False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/submissions",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 201:
                raise Exception(f"Error sending code to Judge0: {response.text}")
            
            return Judge0Response(**response.json())
    
    async def batch_submit(self, submissions: List[Judge0Submission]) -> List[Judge0Response]:
        """
        Sends multiple codes to be evaluated in batch without base64 encoding.
        """
        # Prepare payloads without base64 encoding
        payloads = []
        for submission in submissions:
            payload = submission.dict()
            
            # Use the source code as is
            source_code = payload.get("source_code") or payload.get("sourceCode")
            if source_code:
                payload["source_code"] = source_code
                
                # Remove sourceCode if it exists to avoid confusion
                if "sourceCode" in payload:
                    del payload["sourceCode"]
            
            payloads.append(payload)
        
        # Do not use base64
        batch_payload = {
            "submissions": payloads,
            "base64_encoded": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/submissions/batch",
                json=batch_payload,
                headers=self.headers
            )
            
            if response.status_code != 201:
                raise Exception(f"Error sending batch to Judge0: {response.text}")
            
            return [Judge0Response(**item) for item in response.json()]
    
    async def get_result(self, token: str) -> Judge0Result:
        """
        Gets the result of an evaluation without using base64.
        """
        async with httpx.AsyncClient() as client:
            # Do not use base64_encoded
            response = await client.get(
                f"{self.base_url}/submissions/{token}",
                params={"base64_encoded": "false"},
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Error getting result from Judge0: {response.text}")
            
            result_data = response.json()
            
            # No need to decode
            return Judge0Result(**result_data)
    
    async def batch_get_results(self, tokens: List[str]) -> List[Judge0Result]:
        """
        Gets results of multiple evaluations without using base64.
        """
        # Convert the list of tokens to a comma-separated string
        tokens_str = ",".join(tokens)
        
        async with httpx.AsyncClient() as client:
            # Do not use base64_encoded
            response = await client.get(
                f"{self.base_url}/submissions/batch",
                params={"tokens": tokens_str, "base64_encoded": "false"},
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Error getting results from Judge0: {response.text}")
            
            # Print the response for debugging
            print(f"Judge0 response: {response.text}")
            
            response_data = response.json()
            results = []
            
            # Check if the response has the expected structure
            if isinstance(response_data, dict) and "submissions" in response_data:
                # Process the submissions array
                submissions = response_data["submissions"]
                for item in submissions:
                    if isinstance(item, dict):
                        # No need to process fields
                        results.append(Judge0Result(**item))
                    else:
                        print(f"Warning: Submission item is not a dictionary: {item}")
            elif isinstance(response_data, list):
                # If the response is directly a list of submissions
                for item in response_data:
                    if isinstance(item, dict):
                        # No need to process fields
                        results.append(Judge0Result(**item))
                    else:
                        print(f"Warning: Submission item is not a dictionary: {item}")
            else:
                raise Exception(f"Unrecognized response format: {type(response_data)}")
            
            # Check that we have results for all tokens
            if len(results) != len(tokens):
                print(f"Warning: Number of results ({len(results)}) does not match number of tokens ({len(tokens)})")
                
                # Create a map of tokens to results to check which are missing
                token_to_result = {result.token: result for result in results}
                
                # Add error results for missing tokens
                for token in tokens:
                    if token not in token_to_result:
                        print(f"Warning: No result found for token: {token}")
                        results.append(Judge0Result(
                            token=token,
                            status={"id": 13, "description": "Internal Error"},
                            stdout=None,
                            stderr=None,
                            compile_output=None,
                            time=None,
                            memory=None,
                            created_at="",
                            finished_at=None
                        ))
            
            return results

# Create a client instance
judge0_client = Judge0Client(
    base_url=settings.JUDGE0_URL,
    auth_token=settings.JUDGE0_AUTH_TOKEN
)