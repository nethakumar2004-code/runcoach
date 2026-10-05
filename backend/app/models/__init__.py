# Import every model so all tables and relationships are registered whenever app.models is imported
from app.models import user, run, goal, workout, achievement, social, training_plan, weather  # noqa: F401
