from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.subscription import Purchase, Subscription

router = APIRouter()


@router.get("/stats")
def stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Note: In real app, enforce admin permissions
    users_count = db.query(func.count(User.id)).scalar() or 0
    courses_count = db.query(func.count(Course.id)).scalar() or 0
    sales = db.query(func.coalesce(func.sum(Purchase.amount), 0)).scalar()
    active_subs = db.query(func.count(Subscription.id)).filter(Subscription.is_active == True).scalar() or 0
    growth_rate = 0
    return {
        "users": users_count,
        "courses": courses_count,
        "sales": float(sales or 0),
        "active_subscriptions": active_subs,
        "growth_rate": growth_rate,
    }
