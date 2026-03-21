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
from schemas import PostCreate, PostResponse, UserCreate, UserResponse

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


def get_post_or_404(oid: ObjectId) -> models.Post:
    result = models.Post.objects(id=oid).select_related()
    post = result[0] if result else None
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


def get_user_or_404(oid: ObjectId) -> models.User:
    try:
        return models.User.objects.get(id=oid)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# ---------------------------------------------------------------------------
# HTML routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    posts = models.Post.objects().select_related()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: str):
    oid = to_object_id(post_id)
    post = get_post_or_404(oid)
    return templates.TemplateResponse(
        request,
        "post.html",
        {"post": post, "title": post.title[:50]},
    )


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(request: Request, user_id: str):
    oid = to_object_id(user_id)
    user = get_user_or_404(oid)
    posts = models.Post.objects(user=user).select_related()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate):
    if models.User.objects(username=user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    if models.User.objects(email=user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    try:
        new_user = models.User(username=user.username, email=user.email).save()
    except NotUniqueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    return UserResponse.from_mongo(new_user)


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    oid = to_object_id(user_id)
    user = get_user_or_404(oid)
    return UserResponse.from_mongo(user)


@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id: str):
    oid = to_object_id(user_id)
    user = get_user_or_404(oid)
    posts = models.Post.objects(user=user).select_related()
    return [PostResponse.from_mongo(p) for p in posts]


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    posts = models.Post.objects().select_related()
    return [PostResponse.from_mongo(p) for p in posts]


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    oid = to_object_id(post.user_id)
    user = get_user_or_404(oid)
    new_post = models.Post(title=post.title, content=post.content, user=user).save()
    new_post.reload()
    return PostResponse.from_mongo(new_post)


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str):
    oid = to_object_id(post_id)
    post = get_post_or_404(oid)
    return PostResponse.from_mongo(post)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
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
def validation_exception_handler(request: Request, exception: RequestValidationError):
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