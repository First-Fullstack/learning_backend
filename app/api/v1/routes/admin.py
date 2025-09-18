from fastapi import APIRouter, Depends, Query
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