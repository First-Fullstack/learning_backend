from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.purchase import CoursePurchase
from app.models.subscription_plan import UserSubscription

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
