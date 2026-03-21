from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_file: str | None
    image_path: str

    @classmethod
    def from_mongo(cls, user) -> "UserResponse":
        return cls(
            id=str(user.id),
            username=user.username,
            email=user.email,
            image_file=user.image_file,
            image_path=user.image_path,
        )


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    user_id: str  # TEMPORARY — MongoDB ObjectId string


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    date_posted: datetime
    author: UserResponse

    @classmethod
    def from_mongo(cls, post) -> "PostResponse":
        return cls(
            id=str(post.id),
            title=post.title,
            content=post.content,
            user_id=str(post.user.id),
            date_posted=post.date_posted,
            author=UserResponse.from_mongo(post.user),
        )