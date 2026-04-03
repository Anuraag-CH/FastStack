from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    image_file: str | None
    image_path: str

    @classmethod
    def from_mongo(cls, user) -> "UserPublic":
        return cls(
            id=str(user.id),
            username=user.username,
            image_file=user.image_file,
            image_path=user.image_path,
        )


class UserPrivate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    image_file: str | None
    image_path: str

    @classmethod
    def from_mongo(cls, user) -> "UserPrivate":
        return cls(
            id=str(user.id),
            username=user.username,
            email=user.email,
            image_file=user.image_file,
            image_path=user.image_path,
        )


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=120)
    image_file: Optional[str] = Field(default=None, min_length=1, max_length=200)


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    user_id: str  # TEMPORARY - until authentication


class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    content: Optional[str] = Field(default=None, min_length=1)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    date_posted: datetime
    author: UserPublic

    @classmethod
    def from_mongo(cls, post) -> "PostResponse":
        return cls(
            id=str(post.id),
            title=post.title,
            content=post.content,
            user_id=str(post.user.id),
            date_posted=post.date_posted,
            author=UserPublic.from_mongo(post.user),
        )