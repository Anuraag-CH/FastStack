import asyncio

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from mongoengine import DoesNotExist

import models


def to_object_id(raw: str) -> ObjectId:
    """Convert a string to ObjectId, raising 422 on invalid format."""
    try:
        return ObjectId(raw)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid id: {raw!r}",
        )


async def get_post_or_404(oid: ObjectId) -> models.Post:
    loop = asyncio.get_event_loop()

    def _fetch():
        result = models.Post.objects(id=oid).select_related()
        return result[0] if result else None

    post = await loop.run_in_executor(None, _fetch)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


async def get_user_or_404(oid: ObjectId) -> models.User:
    loop = asyncio.get_event_loop()

    def _fetch():
        try:
            return models.User.objects.get(id=oid)
        except DoesNotExist:
            return None

    user = await loop.run_in_executor(None, _fetch)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user