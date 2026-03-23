import asyncio

from fastapi import APIRouter, HTTPException, status
from mongoengine import NotUniqueError

import models
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate
from utils import get_user_or_404, to_object_id

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    loop = asyncio.get_event_loop()

    existing_username = await loop.run_in_executor(
        None, lambda: models.User.objects(username=user.username).first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = await loop.run_in_executor(
        None, lambda: models.User.objects(email=user.email).first()
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    def _create():
        try:
            return models.User(username=user.username, email=user.email).save()
        except NotUniqueError:
            return None

    new_user = await loop.run_in_executor(None, _create)
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    return UserResponse.from_mongo(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    return UserResponse.from_mongo(user)


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(
        None, lambda: models.Post.objects(user=user).select_related()
    )
    return [PostResponse.from_mongo(p) for p in posts]


@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(user_id: str, user_update: UserUpdate):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, user.save)
    return UserResponse.from_mongo(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, user.delete)