from fastapi import Request
from fastapi.responses import JSONResponse
import requests
import logging
import json

from src.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change to DEBUG for more information

# Paths that do not require authentication
PUBLIC_PATHS = [
    "/",              # FastAPI root
    "/health",        # Health check
    "/api/auth/signin",     # Any auth route in Node.js
    "/api/auth/signup",     # Any auth route in Node.js
    "/api/languages",
    "/docs",          # Swagger UI
    "/openapi.json",   # OpenAPI spec
    "/api/auth/mock-verify",  # Test endpoint
    "/api/auth/generate-test-token"  # Test endpoint
]

async def verify_token_middleware(request: Request, call_next):
    path = request.url.path
    logger.debug(f"Request path: {path}")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    # Allow OPTIONS requests for CORS preflight
    if request.method == "OPTIONS":
        logger.debug("Allowing OPTIONS request for CORS preflight")
        response = await call_next(request)
        return response

    # Check if the path is public (must exactly match or be a specific prefix)
    is_public = False
    for public_path in PUBLIC_PATHS:
        # Exact match
        if path == public_path:
            is_public = True
            break
        # Prefix match for documentation
        if public_path in ["/docs", "/openapi.json"] and path.startswith(public_path):
            is_public = True
            break
        # Match for static files
        if path.startswith("/static/"):
            is_public = True
            break
        # Public paths for problems
        if path == "/api/problems" or (path.startswith("/api/problems/") and request.method == "GET"):
            # Only GET requests to problems are public
            is_public = True
            break

    if is_public:
        logger.debug(f"Public path detected: {path}")
        return await call_next(request)

    # Verify authentication token
    auth_header = request.headers.get("Authorization")
    x_access_token = request.headers.get("x-access-token")
    
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        logger.debug(f"Token extracted from Authorization header, length: {len(token)}")
    elif x_access_token:
        token = x_access_token
        logger.debug(f"Token extracted from x-access-token header, length: {len(token)}")
    
    if not token:
        logger.warning("No authentication token provided")
        return JSONResponse(
            status_code=401,
            content={"detail": "No authentication token provided"}
        )

    # Store the token in request.state to use it in routes
    request.state.user_token = token

    # Call Node.js service to verify token
    try:
        logger.debug(f"Calling auth service at: {settings.AUTH_SERVICE_URL}/api/auth/verify")
        resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/api/auth/verify",
            json={"token": token},
            timeout=5
        )
        logger.debug(f"Auth service response status: {resp.status_code}")
        
        if resp.status_code == 200:
            logger.debug(f"Auth service response body: {resp.text[:100]}...")
        else:
            logger.warning(f"Auth service error response: {resp.text}")
            
    except requests.RequestException as e:
        logger.error(f"Cannot reach auth service: {str(e)}")
        return JSONResponse(status_code=502, content={"message": f"Cannot reach auth service: {str(e)}"})

    if resp.status_code != 200:
        logger.warning(f"Invalid token response from auth service: {resp.status_code}")
        return JSONResponse(status_code=401, content={"message": "Invalid or expired token"})

    # Inject user info into request.state
    try:
        user_data = resp.json()
        logger.debug(f"User data received: {json.dumps(user_data)}")
        request.state.user = user_data
        
        # Check if the user has administrator role
        is_admin = False
        if "roles" in user_data and isinstance(user_data["roles"], list):
            is_admin = "admin" in user_data["roles"]
        elif "role" in user_data and user_data["role"] == "admin":
            is_admin = True
        elif "isAdmin" in user_data and user_data["isAdmin"]:
            is_admin = True
        
        request.state.is_admin = is_admin
        logger.debug(f"User is admin: {is_admin}")
        
    except Exception as e:
        logger.error(f"Error processing user data: {str(e)}")
        return JSONResponse(status_code=500, content={"message": f"Error processing user data: {str(e)}"})

    # Continue with the request
    response = await call_next(request)
    return response
