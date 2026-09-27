from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.security import limiter
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Setup logging and initialize database tables
    setup_logging()
    logger.info("Initializing IBM Bob 2.0 Backend Service...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down IBM Bob 2.0 Backend Service...")


app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Backend API for AI Debugging & Testing Agent (IBM Bob 2.0).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Connect SlowAPI Limiter state
app.state.limiter = limiter


# 1. Custom Rate Limit Exceeded Handler
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and try again later.",
            },
        },
    )


# 2. Safe Global Exception Handler (Prevents stack traces leaking to clients)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing your request.",
            },
        },
    )


# 3. Configure CORS (Connects with Shlok's Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register V1 API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "IBM Bob 2.0",
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
