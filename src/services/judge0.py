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
        Envía un código para ser evaluado sin codificación base64.
        """
        # Preparar el payload sin codificación base64
        payload = submission.dict()
        
        # Usar el código fuente tal como está
        source_code = payload.get("source_code") or payload.get("sourceCode")
        if source_code:
            payload["source_code"] = source_code
            
            # Eliminar sourceCode si existe para evitar confusión
            if "sourceCode" in payload:
                del payload["sourceCode"]
        
        # No usar base64
        payload["base64_encoded"] = False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/submissions",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 201:
                raise Exception(f"Error al enviar código a Judge0: {response.text}")
            
            return Judge0Response(**response.json())
    
    async def batch_submit(self, submissions: List[Judge0Submission]) -> List[Judge0Response]:
        """
        Envía múltiples códigos para ser evaluados en batch sin codificación base64.
        """
        # Preparar los payloads sin codificación base64
        payloads = []
        for submission in submissions:
            payload = submission.dict()
            
            # Usar el código fuente tal como está
            source_code = payload.get("source_code") or payload.get("sourceCode")
            if source_code:
                payload["source_code"] = source_code
                
                # Eliminar sourceCode si existe para evitar confusión
                if "sourceCode" in payload:
                    del payload["sourceCode"]
            
            payloads.append(payload)
        
        # No usar base64
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
                raise Exception(f"Error al enviar batch a Judge0: {response.text}")
            
            return [Judge0Response(**item) for item in response.json()]
    
    async def get_result(self, token: str) -> Judge0Result:
        """
        Obtiene el resultado de una evaluación sin usar base64.
        """
        async with httpx.AsyncClient() as client:
            # No usar base64_encoded
            response = await client.get(
                f"{self.base_url}/submissions/{token}",
                params={"base64_encoded": "false"},
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Error al obtener resultado de Judge0: {response.text}")
            
            result_data = response.json()
            
            # No es necesario decodificar
            return Judge0Result(**result_data)
    
    async def batch_get_results(self, tokens: List[str]) -> List[Judge0Result]:
        """
        Obtiene los resultados de múltiples evaluaciones sin usar base64.
        """
        # Convertir la lista de tokens a una cadena separada por comas
        tokens_str = ",".join(tokens)
        
        async with httpx.AsyncClient() as client:
            # No usar base64_encoded
            response = await client.get(
                f"{self.base_url}/submissions/batch",
                params={"tokens": tokens_str, "base64_encoded": "false"},
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Error al obtener resultados de Judge0: {response.text}")
            
            # Imprimir la respuesta para depuración
            print(f"Respuesta de Judge0: {response.text}")
            
            response_data = response.json()
            results = []
            
            # Verificar si la respuesta tiene la estructura esperada
            if isinstance(response_data, dict) and "submissions" in response_data:
                # Procesar el array de submissions
                submissions = response_data["submissions"]
                for item in submissions:
                    if isinstance(item, dict):
                        # No es necesario procesar los campos
                        results.append(Judge0Result(**item))
                    else:
                        print(f"Advertencia: Item de submission no es un diccionario: {item}")
            elif isinstance(response_data, list):
                # Si la respuesta es directamente una lista de submissions
                for item in response_data:
                    if isinstance(item, dict):
                        # No es necesario procesar los campos
                        results.append(Judge0Result(**item))
                    else:
                        print(f"Advertencia: Item de submission no es un diccionario: {item}")
            else:
                raise Exception(f"Formato de respuesta no reconocido: {type(response_data)}")
            
            # Verificar que tenemos resultados para todos los tokens
            if len(results) != len(tokens):
                print(f"Advertencia: Número de resultados ({len(results)}) no coincide con número de tokens ({len(tokens)})")
                
                # Crear un mapa de tokens a resultados para verificar cuáles faltan
                token_to_result = {result.token: result for result in results}
                
                # Añadir resultados de error para los tokens faltantes
                for token in tokens:
                    if token not in token_to_result:
                        print(f"Advertencia: No se encontró resultado para el token: {token}")
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

# Crear una instancia del cliente
judge0_client = Judge0Client(
    base_url=settings.JUDGE0_URL,
    auth_token=settings.JUDGE0_AUTH_TOKEN
)