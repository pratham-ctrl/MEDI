"""Authentication utilities for JWT token management"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token (e.g., user_id, email)
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    # Create token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT access token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and return the user_id
    
    Args:
        token: JWT token string
    
    Returns:
        user_id if token is valid, None otherwise
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    return user_id

