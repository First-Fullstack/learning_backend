from fastapi import APIRouter

from app.api.v1.routes import auth, users, courses, quizzes, subscriptions, uploads
from app.api.v1.routes import admin_route

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(subscriptions.router, prefix="/subscription", tags=["subscription"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(admin_route.router, prefix="/admin", tags=["admin"])