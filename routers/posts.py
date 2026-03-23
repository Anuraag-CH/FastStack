import asyncio

from fastapi import APIRouter, HTTPException, status

import models
from schemas import PostCreate, PostResponse, PostUpdate
from utils import get_post_or_404, get_user_or_404, to_object_id

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=list[PostResponse])
async def get_posts():
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(
        None, lambda: models.Post.objects().select_related()
    )
    return [PostResponse.from_mongo(p) for p in posts]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate):
    oid = to_object_id(post.user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()

    def _create():
        new_post = models.Post(title=post.title, content=post.content, user=user).save()
        new_post.reload()
        return new_post

    new_post = await loop.run_in_executor(None, _create)
    return PostResponse.from_mongo(new_post)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)
    return PostResponse.from_mongo(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, post_update: PostUpdate):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)

    requesting_user_id = to_object_id(post_update.user_id)
    if post.user.id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the author of this post",
        )

    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, post.save)
    return PostResponse.from_mongo(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, post.delete)
