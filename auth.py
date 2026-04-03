from datetime import UTC, datetime, timedelta

import jwt

from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings



password_hash = PasswordHash.recommended()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(data: dict,expires_delta: timedelta = None) -> str:
    """Create a JWT access token"""
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> None:
    """Verify a JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM],options={"require":["exp","sub"]})
    
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")