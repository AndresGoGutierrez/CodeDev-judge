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

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change to DEBUG for more information

router = APIRouter(prefix="/api/admin/users")

@router.get("/")
async def get_all_users(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    _: dict = Depends(is_admin)
):
    """
    Get all users.
    Only accessible to administrators.
    """
    try:
        # Get user token from request.state
        user_token = request.state.user_token
        logger.debug(f"User token: {user_token[:10]}...")
        
        # Simulate response for debugging
        # IMPORTANT: Remove in production
        logger.debug("Simulating user response for debugging")
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
        
        # Call the authentication service to get the list of users
        logger.debug(f"Calling authentication service: {settings.AUTH_SERVICE_URL}/api/admin/users")
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        logger.debug(f"Authentication service response: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error getting users: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error getting users: {response.text}"
            )
        
        users = response.json()
        logger.debug(f"Users received: {len(users)}")
        
        # Apply pagination
        paginated_users = users[skip:skip+limit]
        
        return paginated_users
    
    except requests.RequestException as e:
        logger.error(f"Error communicating with authentication service: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with authentication service: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_detail(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    _: dict = Depends(is_admin)
):
    """
    Get details of a specific user.
    Only accessible to administrators.
    """
    try:
        # Get user token from request.state
        user_token = request.state.user_token
        
        # Call the authentication service to get user details
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error getting user: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with authentication service: {str(e)}"
        )

@router.put("/{user_id}")
async def update_user(
    request: Request,
    user_data: dict,
    user_id: str = Path(..., description="User ID"),
    _: dict = Depends(is_admin)
):
    """
    Update user information.
    Only accessible to administrators.
    """
    try:
        # Get user token from request.state
        user_token = request.state.user_token
        
        # Call the authentication service to update user
        response = requests.put(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            json=user_data,
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error updating user: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with authentication service: {str(e)}"
        )

@router.patch("/{user_id}/role")
async def change_user_role(
    request: Request,
    role_data: dict,
    user_id: str = Path(..., description="User ID"),
    _: dict = Depends(is_admin)
):
    """
    Change user role.
    Only accessible to administrators.
    """
    try:
        # Get user token from request.state
        user_token = request.state.user_token
        
        # Call the authentication service to change user role
        response = requests.patch(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error changing user role: {response.text}"
            )
        
        return response.json()
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with authentication service: {str(e)}"
        )

@router.get("/{user_id}/submissions", response_model=List[submission_schemas.SubmissionPublic])
async def get_user_submissions(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: dict = Depends(is_admin)
):
    """
    Get all submissions of a specific user.
    Only accessible to administrators.
    """
    # Verify that the user exists
    try:
        # Get user token from request.state
        user_token = request.state.user_token
        
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}", "x-access-token": user_token},
            timeout=5
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error verifying user: {response.text}"
            )
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with authentication service: {str(e)}"
        )
    
    # Get user submissions
    submissions = db.query(Submission).filter(
        Submission.user_id == user_id
    ).order_by(Submission.created_at.desc()).offset(skip).limit(limit).all()
    
    return submissions
