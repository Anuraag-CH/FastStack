from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

posts = [
    {
    "id": 1,
    "title": "FastAPI",
    "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+.",
    "Date Posted": "March 15, 2026",
    },
    {
    "id": 2,
    "title": "Python    ",
    "content": "Python is a versatile programming language that is widely used for web development, data science, artificial intelligence, and more.",
    "Date Posted": "March 15, 2026",
    },
]

@app.get("/", include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html",{"posts": posts, "title": "Home"})
    


@app.get("/api/posts")
def get_posts():
    return posts

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)