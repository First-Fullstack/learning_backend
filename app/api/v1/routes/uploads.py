from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.auth import get_current_user
from app.db.deps import get_db
from app.models.user import User
from app.models.course import Course
from app.services.storage import storage_service

router = APIRouter()


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    url = storage_service.upload_bytes(content, key_prefix=f"avatars/{current_user.id}", content_type=file.content_type)
    current_user.avatar_url = url
    db.commit()
    return {"url": url}


@router.post("/courses/{course_id}/thumbnail")
async def upload_course_thumbnail(course_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    content = await file.read()
    url = storage_service.upload_bytes(content, key_prefix=f"courses/{course_id}/thumbnails", content_type=file.content_type)
    course.thumbnail_url = url
    db.commit()
    return {"url": url}


@router.post("/courses/{course_id}/video")
async def upload_course_video(course_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    content = await file.read()
    url = storage_service.upload_bytes(content, key_prefix=f"courses/{course_id}/videos", content_type=file.content_type)
    course.video_url = url
    db.commit()
    return {"url": url}
