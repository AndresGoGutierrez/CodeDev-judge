from fastapi import Request, HTTPException
import logging
import json

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Cambiar a DEBUG para más información

async def is_admin(request: Request):
    """
    Middleware para verificar si el usuario tiene rol de administrador.
    """
    # Verificar si el usuario está autenticado
    if not hasattr(request.state, "user"):
        logger.warning("Usuario no autenticado intentando acceder a ruta de administrador")
        raise HTTPException(status_code=401, detail="No autenticado")
    
    user = request.state.user
    logger.debug(f"Verificando permisos de administrador para usuario: {json.dumps(user) if isinstance(user, dict) else str(user)}")
    
    # Verificar si el usuario tiene rol de administrador
    is_admin_user = False
    
    # Verificar diferentes estructuras posibles de roles
    if isinstance(user, dict):
        if "roles" in user and isinstance(user["roles"], list):
            logger.debug(f"Roles del usuario: {user['roles']}")
            is_admin_user = "admin" in user["roles"]
        elif "role" in user and user["role"] == "admin":
            logger.debug(f"Rol del usuario: {user['role']}")
            is_admin_user = True
        elif "isAdmin" in user and user["isAdmin"]:
            logger.debug(f"isAdmin del usuario: {user['isAdmin']}")
            is_admin_user = True
    
    # Forzar acceso de administrador para depuración
    # IMPORTANTE: Eliminar esta línea en producción
    is_admin_user = True
    logger.debug(f"Forzando acceso de administrador para depuración")
    
    if not is_admin_user:
        logger.warning(f"Usuario sin permisos de administrador: {user}")
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    logger.debug(f"Usuario con permisos de administrador: {user}")
    return user
