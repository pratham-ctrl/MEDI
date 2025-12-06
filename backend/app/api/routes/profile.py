"""User profile API routes"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserProfile, UserProfileUpdate
from app.services.sql_database import get_sql_service
from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's profile
    
    Args:
        current_user: Authenticated user
    
    Returns:
        User profile with statistics
    """
    try:
        sql_service = get_sql_service()
        
        # Get user info
        user = sql_service.get_user(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get prescriptions count
        prescriptions = sql_service.list_user_prescriptions(
            current_user["user_id"],
            limit=1000
        )
        prescriptions_count = len(prescriptions)
        
        # Get total medicines count
        total_medicines = sum(
            len(p.get("extracted_data", {}).get("medicines", []))
            for p in prescriptions
        )
        
        return UserProfile(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            phone=user.get("phone"),
            date_of_birth=user.get("date_of_birth"),
            gender=user.get("gender"),
            created_at=user["created_at"],
            prescriptions_count=prescriptions_count,
            total_medicines=total_medicines
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving profile"
        )


@router.put("/me", response_model=UserProfile)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile
    
    Args:
        profile_update: Profile fields to update
        current_user: Authenticated user
    
    Returns:
        Updated user profile
    """
    try:
        sql_service = get_sql_service()
        
        # Update user
        sql_service.update_user(
            user_id=current_user["user_id"],
            **profile_update.dict(exclude_unset=True)
        )
        
        # Return updated profile
        return await get_profile(current_user)
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile"
        )


@router.get("/prescriptions")
async def get_user_prescriptions(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    Get user's prescriptions
    
    Args:
        current_user: Authenticated user
        limit: Maximum results
    
    Returns:
        List of prescriptions
    """
    try:
        sql_service = get_sql_service()
        prescriptions = sql_service.list_user_prescriptions(
            current_user["user_id"],
            limit
        )
        
        return prescriptions
        
    except Exception as e:
        logger.error(f"Error getting prescriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving prescriptions"
        )

