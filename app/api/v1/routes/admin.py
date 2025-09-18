from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.purchase import CoursePurchase
from app.models.subscription_plan import UserSubscription
from app.schemas.admin import UserListResponse, PaginationMeta
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.get("/stats")
def stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users_count = db.query(func.count(User.id)).scalar() or 0
    courses_count = db.query(func.count(Course.id)).scalar() or 0
    sales = db.query(func.coalesce(func.sum(CoursePurchase.amount), 0)).scalar() or 0
    active_subs = (
        db.query(func.count(UserSubscription.id))
        .filter(UserSubscription.status == "active")
        .scalar()
        or 0
    )
    growth_rate = 0
    return {
        "users": users_count,
        "courses": courses_count,
        "sales": float(sales),
        "active_subscriptions": active_subs,
        "growth_rate": growth_rate,
    }

@router.get("/users", response_model=UserListResponse)
def list_users(
    search: Optional[str] = Query(None, description="検索キーワード"),
    status: Optional[str] = Query(
        "all",
        description="ステータスでフィルタリング",
        enum=["all", "active", "inactive", "cancelled"]
    ),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    db: Session = Depends(get_db),
):
    """
    管理者がユーザー一覧を取得します
    """
    # --- Build base query ---
    query = db.query(User)

    # Optional search
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))

    # Optional status filter
    if status != "all":
        if status == "active":
            query = query.filter(User.is_active.is_(True))
        elif status == "inactive":
            query = query.filter(User.is_active.is_(False))
        elif status == "cancelled":
            query = query.filter(User.is_cancelled.is_(True))  # adjust if column exists

    # Pagination
    total_count = query.count()
    users = (
        query.order_by(User.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    total_pages = (total_count + limit - 1) // limit

    return UserListResponse(
        users=users,
        pagination=PaginationMeta(
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
        ),
    )

@router.get("/users/{user_id}", response_model=UserOut)
def get_user_detail(
    user_id: int = Path(..., description="ユーザーID"),
    db: Session = Depends(get_db),
    # current_admin: User = Depends(get_current_admin_user),  # or your admin dependency
):
    """
    管理者が特定ユーザーの詳細情報を取得します
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user  # SQLAlchemy ORM object; FastAPI + Pydantic will serialize

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    # current_admin: User = Depends(get_current_admin)   # if you have admin auth
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Permanently remove a user record from the database.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)    # 🗑 actually remove from DB
    db.commit()
    return None        # 204 No Content → no response body