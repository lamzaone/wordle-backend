from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin_words, auth, daily, games, health, leaderboard, profile
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.errors import ServiceError

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc) or exc.detail})


app.include_router(health.router)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(games.router)
api_router.include_router(daily.router)
api_router.include_router(leaderboard.router)
api_router.include_router(admin_words.router)

app.include_router(api_router, prefix=settings.api_v1_prefix)
