from app.db.base import Base

# Import models so Alembic/metadata can discover them
from app.models.user import User  # noqa: F401
from app.models.course import Category, Course, CourseProgress  # noqa: F401
from app.models.quiz import Quiz, QuizOption, QuizAttempt  # noqa: F401
from app.models.subscription import Subscription, Purchase  # noqa: F401
