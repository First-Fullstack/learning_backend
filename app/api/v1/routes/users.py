import os
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import UserCourseProgress
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.get("/profile", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserOut)
def update_me(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if update.name is not None:
        current_user.name = update.name
    if update.email is not None:
        current_user.email = update.email
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/avatar")
async def update_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure directory exists
    upload_dir = "public/avatars"
    os.makedirs(upload_dir, exist_ok=True)

    # Save uploaded file
    file_location = f"{upload_dir}/{current_user.id}_{avatar.filename}"
    with open(file_location, "wb") as f:
        f.write(await avatar.read())  # async read

    # Update DB column
    current_user.avatar_url = f"/static/avatars/{current_user.id}_{avatar.filename}"
    db.commit()
    db.refresh(current_user)

    # Return only avatar_url
    return {"avatar_url": current_user.avatar_url}

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
