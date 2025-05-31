from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/me-debug", tags=["users"])
async def debug_current_user(request: Request):
    """
    Returns EVERYTHING in request.state.user for debugging.
    """
    # Get all attributes from request.state
    state_attrs = {attr: getattr(request.state, attr) for attr in dir(request.state) 
                  if not attr.startswith('_') and not callable(getattr(request.state, attr))}
    
    # Get all request headers
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
    Retrieves information about the authenticated user
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
