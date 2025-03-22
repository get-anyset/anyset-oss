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

## Configuration

The application uses Pydantic settings for configuration. You can override any setting with environment variables using the `APP_` prefix:

```bash
# Example: change the port
export APP_PORT=8080

# Example: enable debug mode
export APP_DEBUG=true

# Example: set specific CORS origins
export APP_CORS_ORIGINS='["http://localhost:3000", "http://localhost:3001"]'
```

Alternatively, you can create a `.env` file in the project root with your configuration.

## API Documentation

FastAPI generates automatic documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Code Quality

This project uses Ruff for linting and formatting.

```bash
# Install dev dependencies
uv pip install ".[dev]"

# Check code with ruff
ruff check .

# Format code with ruff
ruff format .
``` 