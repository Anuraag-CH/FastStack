from __future__ import annotations

from datetime import UTC, datetime

from mongoengine import (
    DateTimeField,
    Document,
    ReferenceField,
    StringField,
)


class User(Document):
    meta = {"collection": "users"}

    username = StringField(max_length=50, unique=True, required=True)
    email = StringField(max_length=120, unique=True, required=True)
    image_file = StringField(max_length=200, null=True, default=None)

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Document):
    meta = {
        "collection": "posts",
        "indexes": ["user"],
    }

    title = StringField(max_length=100, required=True)
    content = StringField(required=True)
    user = ReferenceField(User, required=True)
    date_posted = DateTimeField(default=lambda: datetime.now(UTC))

    @property
    def author(self):
        return self.user

