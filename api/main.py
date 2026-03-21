"""PathReview API — main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, health, profiles, reviews

app = FastAPI(
    title="PathReview",
    description="AI-powered portfolio review assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
