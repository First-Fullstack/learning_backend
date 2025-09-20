from fastapi import APIRouter

from app.api.v1.routes.admin import users, courses, quizzes

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(courses.router, prefix="/courses", tags=["admin-users"])
# router.include_router(courses.router, prefix="/quizzes", tags=["admin-users"])