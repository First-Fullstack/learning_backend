from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.api.v1.routes.admin import users, courses, quizzes
from app.db.deps import get_db
from app.models.user import User
from app.models.course import Course
from app.models.subscription_plan import SubscriptionPlan, UserSubscription
from app.schemas.admin import AdminDashboardOut

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(courses.router, prefix="/courses", tags=["admin-courses"])
router.include_router(quizzes.router, prefix="/quizzes", tags=["admin-quizzes"])

@router.get('/dashboard', response_model=AdminDashboardOut)
def dashboard(db: Session = Depends(get_db)):
    # Totals
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    active_subscriptions = (
        db.query(func.count(UserSubscription.id))
        .filter(UserSubscription.status == "active")
        .scalar()
        or 0
    )

    # Revenue (current month)
    now = datetime.now(timezone.utc)
    start_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Join subscriptions with plans, filter by started_at in current month and active status
    current_revenue = (
        db.query(func.coalesce(func.sum(SubscriptionPlan.price_monthly), 0))
        .select_from(UserSubscription)
        .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
        .filter(
            UserSubscription.status == "active",
            UserSubscription.started_at >= start_current,
        )
        .scalar()
        or 0
    )

    # Last month revenue
    # Compute the start of last month and end of last month
    month = start_current.month - 1 or 12
    year = start_current.year - 1 if start_current.month == 1 else start_current.year
    start_last = start_current.replace(year=year, month=month)
    end_last = start_current
    last_revenue = (
        db.query(func.coalesce(func.sum(SubscriptionPlan.price_monthly), 0))
        .select_from(UserSubscription)
        .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
        .filter(
            UserSubscription.status == "active",
            UserSubscription.started_at >= start_last,
            UserSubscription.started_at < end_last,
        )
        .scalar()
        or 0
    )

    # Monthly growth
    monthly_growth = 0.0
    if last_revenue > 0:
        monthly_growth = ((current_revenue - last_revenue) / last_revenue) * 100.0

    return AdminDashboardOut(
        total_users=total_users,
        total_courses=total_courses,
        active_subscriptions=active_subscriptions,
        total_revenue=int(current_revenue),
        monthly_growth=monthly_growth,
    )