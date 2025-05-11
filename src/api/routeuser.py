from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/me-debug", tags=["users"])
async def debug_current_user(request: Request):
    """
    Devuelve TODO lo que hay en request.state.user para depurar.
    """
    # Obtener todos los atributos de request.state
    state_attrs = {attr: getattr(request.state, attr) for attr in dir(request.state) 
                  if not attr.startswith('_') and not callable(getattr(request.state, attr))}
    
    # Obtener todos los headers de la petición
    headers = dict(request.headers.items())
    
    return {
        "state_user": getattr(request.state, "user", None),
        "state_attrs": state_attrs,
        "request_headers": headers,
        "request_method": request.method,
        "request_url": str(request.url)
    }

@router.get("/me", tags=["users"])
async def get_current_user(request: Request):
    """
    Obtiene la información del usuario autenticado
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
