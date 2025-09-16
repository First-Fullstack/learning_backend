from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import UserCourseProgress
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if update.name is not None:
        current_user.name = update.name
    if update.email is not None:
        current_user.email = update.email
    if update.avatar_url is not None:
        current_user.avatar_url = str(update.avatar_url)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/stats")
def my_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    progresses = (
        db.query(UserCourseProgress)
        .filter(UserCourseProgress.user_id == current_user.id)
        .all()
    )
    total_courses = len(progresses)
    completed_courses = sum(1 for p in progresses if p.progress_percentage >= 100)
    avg_completion = (
        int(sum(p.progress_percentage for p in progresses) / total_courses)
        if total_courses
        else 0
    )
    return {
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "average_completion_rate": avg_completion,
    }
