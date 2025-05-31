from fastapi import Depends, HTTPException, status, Request
from typing import List, Optional

# Dependency to verify that the user is authenticated
async def get_current_user(request: Request):
    """
    Verifies that the user is authenticated and returns their data.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dependency to verify specific roles
def has_role(required_roles: List[str]):
    """
    Creates a dependency that checks if the user has any of the required roles.
    """
    async def role_checker(user = Depends(get_current_user)):
        user_roles = user.get("roles", [])
        
        # Check if the user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to access this resource. One of the following roles is required: {required_roles}",
            )
        return user
    
    return role_checker

# Specific dependencies for common roles
is_admin = has_role(["admin"])
is_moderator = has_role(["moderator", "admin"])  # Admins can also do what moderators do
is_authenticated = get_current_user  # Any authenticated user

# Function to verify if the user is the owner of a resource
async def is_owner_or_admin(request: Request, resource_user_id: str):
    """
    Checks if the user is the owner of the resource or an admin.
    """
    user = await get_current_user(request)
    user_roles = user.get("roles", [])
    
    # If admin, allow access
    if "admin" in user_roles:
        return True
    
    # If the owner, allow access
    if user.get("id") == resource_user_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource",
    )
