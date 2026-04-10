import asyncio
from fastapi import APIRouter, HTTPException, status
import models
from schemas import PostCreate, PostResponse, PostUpdate
from auth import CurrentUser
from utils import get_post_or_404, to_object_id

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("", response_model=list[PostResponse])
async def get_posts():
    loop = asyncio.get_running_loop()
    # Offload blocking MongoEngine query to the default ThreadPoolExecutor
    posts = await loop.run_in_executor(
        None, 
        lambda: list(models.Post.objects().select_related())
    )
    return [PostResponse.from_mongo(p) for p in posts]

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, user: CurrentUser):
    loop = asyncio.get_running_loop()

    def _create_transaction():
        new_post = models.Post(
            title=post.title,
            content=post.content,
            user=user
        ).save()
        return new_post

    new_post = await loop.run_in_executor(None, _create_transaction)
    if new_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post creation failed")
    return PostResponse.from_mongo(new_post)

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    oid = to_object_id(post_id)
    # get_post_or_404 should already be handling its own threading via asyncio
    post = await get_post_or_404(oid)
    return PostResponse.from_mongo(post)

@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, post_update: PostUpdate, user: CurrentUser):
    loop = asyncio.get_running_loop()
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)

    # Check if the current user is the owner
    if post.user.id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    def _update():
        if post_update.title is not None:
            post.title = post_update.title
        if post_update.content is not None:
            post.content = post_update.content
        post.save()
        return post

    updated = await loop.run_in_executor(None, _update)
    return PostResponse.from_mongo(updated)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, user: CurrentUser):
    loop = asyncio.get_running_loop()
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)

    if post.user.id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await loop.run_in_executor(None, post.delete)