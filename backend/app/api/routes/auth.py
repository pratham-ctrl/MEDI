"""Authentication API routes"""

import logging
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import UserLogin, UserLoginResponse, UserCreate, User
from app.services.sql_database import get_sql_service
from app.utils.auth import hash_password, verify_password, create_access_token
from app.api.dependencies import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=UserLoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    User signup endpoint - creates a new user account and returns access token
    
    Args:
        user_data: User registration data
    
    Returns:
        JWT access token and created user object
    
    Raises:
        HTTPException: If user already exists or creation fails
    """
    sql_service = get_sql_service()
    
    # Check if user already exists
    with sql_service.get_connection("users") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE email = ?", (user_data.email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
    
    # Generate user ID
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    try:
        with sql_service.get_connection("users") as conn:
            cursor = conn.cursor()
            
            # Create user
            cursor.execute("""
                INSERT INTO Users (user_id, email, name, phone, date_of_birth, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (
                user_id,
                user_data.email,
                user_data.name,
                user_data.phone,
                user_data.date_of_birth
            ))
            
            # Store password hash (we'll store it in a simple way for now)
            # Create UserPasswords table on the fly if needed
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserPasswords' AND xtype='U')
                BEGIN
                    CREATE TABLE UserPasswords (
                        user_id NVARCHAR(50) PRIMARY KEY,
                        password_hash NVARCHAR(255) NOT NULL,
                        created_at DATETIME DEFAULT GETDATE()
                    )
                END
            """)
            
            cursor.execute("""
                INSERT INTO UserPasswords (user_id, password_hash, created_at)
                VALUES (?, ?, GETDATE())
            """, (user_id, hashed_password))
            
            conn.commit()
        
        logger.info(f"User created successfully: {user_id}")
        
        # Create user object
        user = User(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone,
            date_of_birth=user_data.date_of_birth,
            language_preference=user_data.language_preference,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.user_id,
                "email": user.email,
                "name": user.name
            }
        )
        
        # Return token and user info
        return UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
            user=user
        )
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(credentials: UserLogin):
    """
    User login endpoint - authenticates user and returns JWT token
    
    Args:
        credentials: User login credentials (email and password)
    
    Returns:
        JWT access token and user info
    
    Raises:
        HTTPException: If authentication fails
    """
    sql_service = get_sql_service()
    
    # Get user from database
    try:
        with sql_service.get_connection("users") as conn:
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute("""
                SELECT user_id, email, name, phone, date_of_birth, created_at, last_login
                FROM Users WHERE email = ?
            """, (credentials.email,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            user_id = row[0]
            
            # Get password hash
            cursor.execute("""
                SELECT password_hash FROM UserPasswords WHERE user_id = ?
            """, (user_id,))
            
            password_row = cursor.fetchone()
            
            if not password_row:
                # User exists but no password set (shouldn't happen with new signup)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            stored_hash = password_row[0]
            
            # Verify password
            if not verify_password(credentials.password, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Create user object
            user = User(
                user_id=row[0],
                email=row[1],
                name=row[2],
                phone=row[3],
                date_of_birth=str(row[4]) if row[4] else None,
                language_preference="en",
                created_at=row[5],
                last_login=row[6]
            )
            
            # Update last login
            cursor.execute("""
                UPDATE Users SET last_login = GETDATE() WHERE user_id = ?
            """, (user.user_id,))
            conn.commit()
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.user_id,
                "email": user.email,
                "name": user.name
            }
        )
        
        logger.info(f"User logged in successfully: {user.user_id}")
        
        return UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,  # Convert to seconds
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    User logout endpoint
    
    Note: Since we're using stateless JWT, logout is handled client-side
    by deleting the token. For production, implement token blacklisting.
    """
    logger.info(f"User logged out: {current_user['user_id']}")
    return {
        "message": "Logged out successfully",
        "user_id": current_user["user_id"]
    }


@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify JWT token and return user info
    
    Args:
        current_user: Current authenticated user from token
    
    Returns:
        User info if token is valid
    """
    return {
        "valid": True,
        "user": current_user
    }


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information
    
    Args:
        current_user: Current authenticated user from token
    
    Returns:
        Full user object
    """
    sql_service = get_sql_service()
    
    with sql_service.get_connection("users") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, email, name, phone, date_of_birth, created_at, last_login
            FROM Users WHERE user_id = ?
        """, (current_user["user_id"],))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return User(
            user_id=row[0],
            email=row[1],
            name=row[2],
            phone=row[3],
            date_of_birth=str(row[4]) if row[4] else None,
            language_preference="en",
            created_at=row[5],
            last_login=row[6]
        )

