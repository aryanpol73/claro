from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import router

app = FastAPI()

# --- NEW CHANGE: Create a list of allowed websites to handle different ports and live servers ---
allowed_websites = [
    "http://localhost:5173",   # Your normal React frontend
    "http://localhost:5174",   # Backup port if 5173 is busy
    "http://127.0.0.1:5173",   # Another way computers write localhost
    "https://my-rag-app.com"   # Your future live website (notice there is no slash at the very end)
]

app.add_middleware(
    CORSMiddleware,
    # --- NEW CHANGE: Give the middleware our safe list ---
    allow_origins=allowed_websites,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)