# API Service

A FastAPI backend service for the microfrontend application.

## Setup

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies with uv
pip install uv
uv pip install -e .
```

## Running the Service

```bash
# Run the development server
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

FastAPI generates automatic documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 