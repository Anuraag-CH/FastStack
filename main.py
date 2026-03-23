import asyncio
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mongoengine import DoesNotExist, NotUniqueError
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from database import connect_db
from schemas import PostCreate, PostResponse, PostUpdate, UserCreate, UserResponse, UserUpdate

connect_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# HTML routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request):
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(None, lambda: models.Post.objects().select_related())
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request, post_id: str):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)
    return templates.TemplateResponse(
        request,
        "post.html",
        {"post": post, "title": post.title[:50]},
    )


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(request: Request, user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(
        None, lambda: models.Post.objects(user=user).select_related()
    )
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    loop = asyncio.get_event_loop()

    existing_username = await loop.run_in_executor(
        None, lambda: models.User.objects(username=user.username).first()
    )
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    existing_email = await loop.run_in_executor(
        None, lambda: models.User.objects(email=user.email).first()
    )
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

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


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    return UserResponse.from_mongo(user)


@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(
        None, lambda: models.Post.objects(user=user).select_related()
    )
    return [PostResponse.from_mongo(p) for p in posts]


@app.patch("/api/users/{user_id}", response_model=UserResponse)
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


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    oid = to_object_id(user_id)
    user = await get_user_or_404(oid)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, user.delete)


@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts():
    loop = asyncio.get_event_loop()
    posts = await loop.run_in_executor(None, lambda: models.Post.objects().select_related())
    return [PostResponse.from_mongo(p) for p in posts]


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
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


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)
    return PostResponse.from_mongo(post)


@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, post_update: PostUpdate):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)

    requesting_user_id = to_object_id(post_update.user_id)
    if post.user.id != requesting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the author of this post")

    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, post.save)
    return PostResponse.from_mongo(post)


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str):
    oid = to_object_id(post_id)
    post = await get_post_or_404(oid)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, post.delete)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)