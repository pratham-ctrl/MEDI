"""API dependencies for dependency injection"""

import logging
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth import decode_access_token
from app.services.sql_database import get_sql_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials with token
    
    Returns:
        User info dict with user_id and email
    
    Raises:
        HTTPException: If authentication fails
    """
    # Token is already extracted by HTTPBearer
    token = credentials.credentials
    
    # Decode and validate JWT token
    logger.info(f"Attempting to decode token (length: {len(token)})")
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Token decode failed - invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract user info from token
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "user_id": user_id,
        "email": email,
        "name": payload.get("name")
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Get current user from JWT token, but don't fail if not provided
    
    Args:
        credentials: HTTP Bearer credentials (optional)
    
    Returns:
        User info dict if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def validate_file_upload(
    content_type: str,
    file_size: int
) -> bool:
    """
    Validate uploaded file
    
    Args:
        content_type: MIME type
        file_size: File size in bytes
    
    Returns:
        True if valid
    
    Raises:
        HTTPException: If validation fails
    """
    from app.config import settings
    
    # Check file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Check file type
    allowed_types = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "application/pdf"
    ]
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    return True

