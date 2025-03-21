"""FastAPI backend service for the microfrontend application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microfrontend API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Return a welcome message.

    Returns:
        dict: A welcome message dictionary
    """
    return {"message": "Welcome to the Microfrontend API"}


@app.get("/api/items")
async def get_items() -> list[dict]:
    """Get a list of items.

    Returns:
        list: A list of items with their details
    """
    return [
        {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
        {"id": 2, "name": "Item 2", "description": "Description for Item 2"},
        {"id": 3, "name": "Item 3", "description": "Description for Item 3"},
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
