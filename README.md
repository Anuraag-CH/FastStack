# FastStack

Simple FastAPI starter project that exposes a single `GET /` endpoint returning `{"message": "Hello World"}` and runs with `uvicorn`.

## Prerequisites

- Python 3.9+
- `pip` (Python package manager)

## Setup

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment**:

   - On Windows (PowerShell):

     ```bash
     .\.venv\Scripts\Activate.ps1
     ```

   - On Windows (Command Prompt):

     ```bash
     .\.venv\Scripts\activate.bat
     ```

   - On macOS / Linux:

     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Running the app

You can run the app either directly with `python` or with `uvicorn`:

- **Using `python` (uses the `if __name__ == "__main__"` block in `main.py`)**:

  ```bash
  python main.py
  ```

- **Using `uvicorn` explicitly**:

  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

Once running, open your browser at:

- `http://127.0.0.1:8000/` – root endpoint
- `http://127.0.0.1:8000/docs` – interactive Swagger UI

## Running tests

This project uses `pytest` for testing.



## Project structure

- `main.py` – FastAPI application and entry point
- `requirements.txt` – Python dependencies
