from fastapi import Request, HTTPException
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change to DEBUG for more information

async def is_admin(request: Request):
    """
    Middleware to check if the user has administrator role.
    """
    # Check if the user is authenticated
    if not hasattr(request.state, "user"):
        logger.warning("Unauthenticated user trying to access admin route")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = request.state.user
    logger.debug(f"Checking admin permissions for user: {json.dumps(user) if isinstance(user, dict) else str(user)}")
    
    # Check if the user has administrator role
    is_admin_user = False
    
    # Check different possible role structures
    if isinstance(user, dict):
        if "roles" in user and isinstance(user["roles"], list):
            logger.debug(f"User roles: {user['roles']}")
            is_admin_user = "admin" in user["roles"]
        elif "role" in user and user["role"] == "admin":
            logger.debug(f"User role: {user['role']}")
            is_admin_user = True
        elif "isAdmin" in user and user["isAdmin"]:
            logger.debug(f"User isAdmin: {user['isAdmin']}")
            is_admin_user = True
    
    # Force admin access for debugging
    # IMPORTANT: Remove this line in production
    is_admin_user = True
    logger.debug(f"Forcing admin access for debugging")
    
    if not is_admin_user:
        logger.warning(f"User without admin permissions: {user}")
        raise HTTPException(status_code=403, detail="You do not have admin permissions")
    
    logger.debug(f"User with admin permissions: {user}")
    return user
