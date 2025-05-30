from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from typing import List, Optional
import requests
from sqlalchemy.orm import Session
import logging

from src.core.db_postgres import get_db
from src.core.config import settings
from src.middleware.admin_middleware import is_admin
from src.models.submissionModel import Submission
from src.schemas import submission as submission_schemas

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Cambiar a DEBUG para más información

router = APIRouter(prefix="/api/admin/users")

@router.get("/")
async def get_all_users(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    _: dict = Depends(is_admin)
):
    """
    Obtener todos los usuarios.
    Solo accesible para administradores.
    """
    try:
        # Obtener el token del usuario de request.state
        user_token = request.state.user_token
        logger.debug(f"Token del usuario: {user_token[:10]}...")
        
        # Simular respuesta para depuración
        # IMPORTANTE: Eliminar en producción
        logger.debug("Simulando respuesta de usuarios para depuración")
        return [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"],
                "createdAt": "2023-05-16T00:00:00.000Z"
            },
            {
                "id": "2",
                "username": "user1",
                "email": "user1@example.com",
                "roles": ["user"],
                "createdAt": "2023-05-16T00:00:00.000Z"
            },
            {
                "id": "3",
                "username": "user2",
                "email": "user2@example.com",
                "roles": ["user"],
                "createdAt": "2023-05-16T00:00:00.000Z"
            }
        ]
        
        # Llamar al servicio de autenticación para obtener la lista de usuarios
        logger.debug(f"Llamando al servicio de autenticación: {settings.AUTH_SERVICE_URL}/api/admin/users")
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        logger.debug(f"Respuesta del servicio de autenticación: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error al obtener usuarios: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener usuarios: {response.text}"
            )
        
        users = response.json()
        logger.debug(f"Usuarios recibidos: {len(users)}")
        
        # Aplicar paginación
        paginated_users = users[skip:skip+limit]
        
        return paginated_users
    
    except requests.RequestException as e:
        logger.error(f"Error al comunicarse con el servicio de autenticación: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con el servicio de autenticación: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_detail(
    request: Request,
    user_id: str = Path(..., description="ID del usuario"),
    _: dict = Depends(is_admin)
):
    """
    Obtener detalles de un usuario específico.
    Solo accesible para administradores.
    """
    try:
        # Obtener el token del usuario de request.state
        user_token = request.state.user_token
        
        # Llamar al servicio de autenticación para obtener los detalles del usuario
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener usuario: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con el servicio de autenticación: {str(e)}"
        )

@router.put("/{user_id}")
async def update_user(
    request: Request,
    user_data: dict,
    user_id: str = Path(..., description="ID del usuario"),
    _: dict = Depends(is_admin)
):
    """
    Actualizar información de un usuario.
    Solo accesible para administradores.
    """
    try:
        # Obtener el token del usuario de request.state
        user_token = request.state.user_token
        
        # Llamar al servicio de autenticación para actualizar el usuario
        response = requests.put(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            json=user_data,
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al actualizar usuario: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con el servicio de autenticación: {str(e)}"
        )

@router.patch("/{user_id}/role")
async def change_user_role(
    request: Request,
    role_data: dict,
    user_id: str = Path(..., description="ID del usuario"),
    _: dict = Depends(is_admin)
):
    """
    Cambiar el rol de un usuario.
    Solo accesible para administradores.
    """
    try:
        # Obtener el token del usuario de request.state
        user_token = request.state.user_token
        
        # Llamar al servicio de autenticación para cambiar el rol del usuario
        response = requests.patch(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al cambiar rol de usuario: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con el servicio de autenticación: {str(e)}"
        )

@router.get("/{user_id}/submissions", response_model=List[submission_schemas.SubmissionPublic])
async def get_user_submissions(
    request: Request,
    user_id: str = Path(..., description="ID del usuario"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Obtener todos los envíos de un usuario específico.
    Solo accesible para administradores.
    """
    # Verificar que el usuario existe
    try:
        # Obtener el token del usuario de request.state
        user_token = request.state.user_token
        
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al verificar usuario: {response.text}"
            )
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con el servicio de autenticación: {str(e)}"
        )
    
    # Obtener los envíos del usuario
    submissions = db.query(Submission).filter(
        Submission.user_id == user_id
    ).order_by(Submission.created_at.desc()).offset(skip).limit(limit).all()
    
    return submissions
