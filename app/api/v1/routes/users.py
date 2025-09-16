import os
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import UserCourseProgress
from app.schemas.user import UserOut, UserUpdate, UpdatePassword
from app.core.security import verify_password, get_password_hash

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

@router.put("/password")
def update_password(
    payload: UpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        return {"error": "Current password is incorrect."}, 400
    # Update to new password
    current_user.password_hash = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"message": "Password updated successfully."}

@router.get("/progress")
def my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    progresses = (
        db.query(UserCourseProgress)
        .filter(UserCourseProgress.user_id == current_user.id)
        .all()
    )
    result = []
    for p in progresses:
        result.append({
            "course_id": p.course_id,
            "progress_percentage": p.progress_percentage,
            "current_video_id": p.current_video_id,
            "started_at": p.started_at.isoformat() if p.started_at else None,
            "last_accessed_at": p.last_accessed_at.isoformat() if p.last_accessed_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        })
    return result
