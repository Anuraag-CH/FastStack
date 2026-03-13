from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

posts = [
    {
    "id": 1,
    "title": "FastAPI",
    "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+.",
    "created_at": "2026-03-12",
    "updated_at": "2026-03-12",
    },
    {
    "id": 2,
    "title": "Python    ",
    "content": "Python is a versatile programming language that is widely used for web development, data science, artificial intelligence, and more.",
    "created_at": "2026-03-12",
    "updated_at": "2026-03-12",
    },
]

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    return """
    <html>
    <body>
    <h1>Welcome to the FastAPI API</h1>
    <p>This is a simple API built with FastAPI</p>
    <a href="/api/posts">Get Posts</a>
    </body>
    </html>
    """


@app.get("/api/posts")
def get_posts():
    return posts

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)