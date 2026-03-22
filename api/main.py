from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import structlog

from api.middleware.request_id import RequestIDMiddleware
from api.routes import auth, profiles, reviews, health
from core.database import init_db

log = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="PathReview API",
    description="AI-powered portfolio review assistant",
    version="1.0.0",
)


# Configure OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="PathReview API",
        version="1.0.0",
        description="AI-powered portfolio review assistant",
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://pathreview.example.com/logo.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)


# Exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    log.error(
        "unhandled_exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(reviews.router)
app.include_router(health.router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await init_db()
        log.info("application_startup_completed")
    except Exception as exc:
        log.error("application_startup_failed", error=str(exc))
        raise


# Root endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "PathReview API is running",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
