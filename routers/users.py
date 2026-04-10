import asyncio

from fastapi import APIRouter, HTTPException, status, Depends
from mongoengine import NotUniqueError

import models
from schemas import PostResponse, UserCreate, UserPublic, UserUpdate, UserPrivate, Token
from utils import get_user_or_404, to_object_id

router = APIRouter(prefix="/api/users", tags=["users"])

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from auth import create_access_token, hash_password, verify_token, verify_password, oauth2_scheme
from config import settings
from auth import CurrentUser


@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    loop = asyncio.get_event_loop()

    existing_username = await loop.run_in_executor(
        None, lambda: models.User.objects(username=user.username.lower()).first()
    )
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    existing_email = await loop.run_in_executor(
        None, lambda: models.User.objects(email=user.email.lower()).first()
    )
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    def _create():
        try:
            return models.User(username=user.username, email=user.email.lower(), password=hash_password(user.password)).save()
        except NotUniqueError:
            return None

    new_user = await loop.run_in_executor(None, _create)
    if new_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")
    return UserPrivate.from_mongo(new_user)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    loop = asyncio.get_event_loop()
    email = form_data.username.lower()

    user = await loop.run_in_executor(
        None, lambda: models.User.objects(email=email).first()
    )
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserPrivate)
async def get_current_user(user: CurrentUser):
    return UserPrivate.from_mongo(user)


@router.get("/{user_id}", response_model=UserPrivate)
async def get_user(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    return UserPrivate.from_mongo(user)


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: str):
    loop = asyncio.get_event_loop()
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    posts = await loop.run_in_executor(
        None, lambda: models.Post.objects(user=user).select_related()
    )
    return [PostResponse.from_mongo(p) for p in posts]


@router.patch("/{user_id}", response_model=UserPublic)
async def patch_user(user_id: str, user_update: UserUpdate):
    loop = asyncio.get_event_loop()
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await loop.run_in_executor(None, user.save)
    return UserPublic.from_mongo(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    loop = asyncio.get_event_loop()
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    await user.delete()