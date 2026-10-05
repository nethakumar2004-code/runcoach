import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app import models  # noqa: F401  registers every table
from app.db import SessionLocal
from app.migrations import run_migrations
from app.routers import runs, dashboard, auth, achievements, social, analytics, training_plans, weather
from app.services.achievements import initialize_default_achievements

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("runcoach")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    with SessionLocal() as db:
        initialize_default_achievements(db)
    if config.DEV_MODE:
        logger.warning("RUNCOACH_DEV_MODE is on: dev-token login and debug endpoints are enabled")
    yield


app = FastAPI(title="Adaptive Run Coach API", lifespan=lifespan)

# The mobile app sends a bearer token, not cookies, so credentials are not needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Return a readable message in `detail` (the app can show it as-is), plus the structured errors."""
    errors = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    messages = []
    for err in errors:
        field = ".".join(str(part) for part in err["loc"] if part != "body")
        msg = err["msg"].removeprefix("Value error, ")
        messages.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages), "errors": errors})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Full details go to the server log only; clients never see internal error text
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(dashboard.router, tags=["dashboard"])  # no prefix, path is /dashboard
app.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(training_plans.router, tags=["training-plans"])
app.include_router(weather.router, tags=["weather"])

if config.DEV_MODE:
    app.include_router(training_plans.dev_router)
