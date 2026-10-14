from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import router

app = FastAPI(
    title="Claro API",
    description="AI-Powered Academic Research Assistant & Cite-or-Refuse RAG Platform",
    version="1.0.0",
)

# Allowed origins for frontend local dev and preview environments
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)