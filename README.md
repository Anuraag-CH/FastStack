# FastStack

FastAPI application with **MongoDB** (via [MongoEngine](https://mongoengine.org/)), **Jinja2** server-rendered pages, and a small **REST API** for users and posts.

## Features

- HTML: home/post list, single post, and per-user post pages with shared layout and error pages
- JSON API: create/fetch users and posts, list posts (all or by user)
- Static assets under `/static`; user media served from `/media`
- Centralized HTTP and validation error handling (JSON for `/api/*`, HTML elsewhere)

## Prerequisites

- **Python 3.9+**
- **MongoDB** reachable at the URL you configure (local or remote)
- **pip**

## Configuration

1. Copy the example environment file and adjust values:

   ```bash
   cp .env.example .env
   ```

2. Set variables (see `.env.example`):

   | Variable       | Purpose                          |
   | -------------- | -------------------------------- |
   | `MONGODB_URL`  | MongoDB connection string        |
   | `DB_NAME`      | Database name used by the app    |

   Use placeholders for secrets in docs; never commit real credentials.

## Setup

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   ```

2. **Activate it**

   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
   - Windows (CMD): `.\.venv\Scripts\activate.bat`
   - macOS / Linux: `source .venv/bin/activate`

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Start MongoDB** so it matches `MONGODB_URL` in `.env`.

## Running the app

- **Python entrypoint** (binds `0.0.0.0:8000`):

  ```bash
  python main.py
  ```

- **Uvicorn** (e.g. with auto-reload during development):

  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

Then open:

| URL | Description |
| --- | ----------- |
| `http://127.0.0.1:8000/` | Home (post list) |
| `http://127.0.0.1:8000/posts` | Same as `/` |
| `http://127.0.0.1:8000/posts/{post_id}` | Single post (MongoDB ObjectId) |
| `http://127.0.0.1:8000/users/{user_id}/posts` | Posts by user |
| `http://127.0.0.1:8000/docs` | OpenAPI UI (**API routes only**; HTML routes are omitted from the schema) |
| `http://127.0.0.1:8000/redoc` | ReDoc |

## API reference

Base URL: `http://127.0.0.1:8000`

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/api/users` | Create user (`username`, `email`). Returns `201` or `400` if duplicate. |
| `GET` | `/api/users/{user_id}` | Get user by id. |
| `GET` | `/api/users/{user_id}/posts` | List posts for that user. |
| `GET` | `/api/posts` | List all posts (with author). |
| `POST` | `/api/posts` | Create post (`title`, `content`, `user_id`). Returns `201`. |
| `GET` | `/api/posts/{post_id}` | Get one post. |

Path ids are MongoDB **ObjectId** strings; invalid ids yield `422`.

## Project structure

| Path | Role |
| ---- | ---- |
| `main.py` | FastAPI app, routes, exception handlers |
| `database.py` | Load `.env`, `mongoengine.connect` |
| `models.py` | `User` and `Post` documents |
| `schemas.py` | Pydantic request/response models |
| `templates/` | Jinja2 templates (`layout.html`, pages, `error.html`) |
| `static/` | CSS, JS, default profile image, manifest |
| `media/` | Runtime uploads (e.g. profile pictures); served at `/media` |
| `requirements.txt` | Python dependencies |
| `.env.example` | Sample environment variables |


