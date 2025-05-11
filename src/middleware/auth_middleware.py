from fastapi import Request
from fastapi.responses import JSONResponse
import requests
import logging
from jwt import DecodeError, ExpiredSignatureError

from src.core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Rutas que no requieren autenticación
PUBLIC_PATHS = [
    "/",              # FastAPI root
    "/health",        # Health check
    "/api/auth/signin",     # Cualquier ruta de auth en Node.js
    "/api/auth/signup",     # Cualquier ruta de auth en Node.js
    "/docs",          # Swagger UI
    "/openapi.json",   # OpenAPI spec
    "/api/auth/mock-verify",  # Endpoint de prueba
    "/api/auth/generate-test-token"  # Endpoint de prueba
]

async def verify_token_middleware(request: Request, call_next):
    path = request.url.path
    logger.info(f"Request path: {path}")

    # Verificar si la ruta es pública (debe coincidir exactamente o ser un prefijo específico)
    is_public = False
    for public_path in PUBLIC_PATHS:
        # Coincidencia exacta
        if path == public_path:
            is_public = True
            break
        # Coincidencia de prefijo para documentación
        if public_path in ["/docs", "/openapi.json"] and path.startswith(public_path):
            is_public = True
            break
        # Coincidencia para archivos estáticos
        if path.startswith("/static/"):
            is_public = True
            break
        # Rutas públicas de problemas
        if path == "/api/problems" or path.startswith("/api/problems/") and request.method == "GET":
            # Solo las solicitudes GET a problemas son públicas
            is_public = True
            break

    if is_public:
        logger.info(f"Public path detected: {path}")
        return await call_next(request)

    # Obtener header Authorization
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("No Bearer token provided")
        return JSONResponse(status_code=401, content={"message": "No authorization token provided"})

    token = auth_header.split(" ", 1)[1]
    logger.info(f"Token extracted, length: {len(token)}")

    # Llamar al servicio Node.js para verificar token
    try:
        logger.info(f"Calling auth service at: {settings.AUTH_SERVICE_URL}/api/auth/verify")
        resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/api/auth/verify",
            json={"token": token},
            timeout=5
        )
        logger.info(f"Auth service response status: {resp.status_code}")
        
        if resp.status_code == 200:
            logger.info(f"Auth service response body: {resp.text[:100]}...")
        else:
            logger.warning(f"Auth service error response: {resp.text}")
            
    except requests.RequestException as e:
        logger.error(f"Cannot reach auth service: {str(e)}")
        return JSONResponse(status_code=502, content={"message": f"Cannot reach auth service: {str(e)}"})

    if resp.status_code != 200:
        logger.warning(f"Invalid token response from auth service: {resp.status_code}")
        return JSONResponse(status_code=401, content={"message": "Invalid or expired token"})

    # Inyectamos la info del usuario en request.state
    try:
        user_data = resp.json()
        logger.info(f"User data received: {user_data}")
        request.state.user = user_data
        logger.info("User data assigned to request.state.user")
    except Exception as e:
        logger.error(f"Error processing user data: {str(e)}")
        return JSONResponse(status_code=500, content={"message": f"Error processing user data: {str(e)}"})

    # Continuar con la petición
    response = await call_next(request)
    return response
