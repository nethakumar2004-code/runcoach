from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, engine
from app.routers import runs, dashboard, auth, achievements, social, analytics, training_plans, weather
from app.models import user, goal, workout, run, achievement, social as social_models, training_plan, weather as weather_models  # for table registration

app = FastAPI(title="Adaptive Run Coach API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(dashboard.router, tags=["dashboard"])  # no prefix, path is /dashboard
app.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(training_plans.router, tags=["training-plans"])
app.include_router(weather.router, tags=["weather"])
