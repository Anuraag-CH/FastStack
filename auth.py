import asyncio
from datetime import UTC, datetime, timedelta

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from mongoengine.errors import DoesNotExist, ValidationError as MongoValidationError

from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings

from typing import Annotated
from fastapi import Depends, HTTPException, status

import models
from database import connect_db

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
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
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    loop = asyncio.get_event_loop()
    try:
        user = await loop.run_in_executor(None, lambda: models.User.objects.get(id=oid))
    except (DoesNotExist, MongoValidationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]