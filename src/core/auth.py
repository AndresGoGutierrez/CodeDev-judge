from fastapi import Depends, HTTPException, status, Request
from typing import List, Optional

# Dependencia para verificar que el usuario está autenticado
async def get_current_user(request: Request):
    """
    Verifica que el usuario está autenticado y devuelve sus datos.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dependencia para verificar roles específicos
def has_role(required_roles: List[str]):
    """
    Crea una dependencia que verifica si el usuario tiene alguno de los roles requeridos.
    """
    async def role_checker(user = Depends(get_current_user)):
        user_roles = user.get("roles", [])
        
        # Verificar si el usuario tiene alguno de los roles requeridos
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para acceder a este recurso. Se requiere uno de estos roles: {required_roles}",
            )
        return user
    
    return role_checker

# Dependencias específicas para roles comunes
is_admin = has_role(["admin"])
is_moderator = has_role(["moderator", "admin"])  # Los admin también pueden hacer lo que hacen los moderadores
is_authenticated = get_current_user  # Cualquier usuario autenticado

# Función para verificar si el usuario es propietario de un recurso
async def is_owner_or_admin(request: Request, resource_user_id: str):
    """
    Verifica si el usuario es propietario del recurso o es administrador.
    """
    user = await get_current_user(request)
    user_roles = user.get("roles", [])
    
    # Si es admin, permitir acceso
    if "admin" in user_roles:
        return True
    
    # Si es el propietario, permitir acceso
    if user.get("id") == resource_user_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permiso para acceder a este recurso",
    )
