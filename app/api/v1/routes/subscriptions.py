from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan, UserSubscription
from app.schemas.subscription import SubscriptionPlanOut, SubscribeIn, SubscribeOut, ChangePlanIn, ChangePlanOut

router = APIRouter()

@router.get('/plans', response_model=list[SubscriptionPlanOut])
def list_plans(db: Session = Depends(get_db)):
    try:
        plans = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.price_monthly.asc())
            .all()
        )
        # Attach features from simple presets; in real app this likely comes from DB
        for p in plans:
            if not hasattr(p, 'features'):
                # type: ignore - dynamic attribute for serialization
                p.features = [
                    "全コース視聴",
                    "進捗管理",
                    "クイズ機能",
                    "修了証書",
                ]
        return plans
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )

@router.post("/subscribe", response_model=SubscribeOut)
def subscribe(body: SubscribeIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        plan = db.get(SubscriptionPlan, body.plan_id)
        if not plan or not plan.is_active:
            raise HTTPException(status_code=400, detail="invalid plan")

        # Cancel existing active subscription if any
        existing = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == current_user.id, UserSubscription.status == "active")
            .order_by(UserSubscription.id.desc())
            .first()
        )
        now = datetime.now(timezone.utc)
        if existing:
            existing.status = "cancelled"
            existing.cancelled_at = now

        # Here you'd call your payment processor using body.payment_method_id
        # For now, assume payment succeeds and create the subscription
        sub = UserSubscription(
            user_id=current_user.id,
            plan_id=plan.id,
            status="active",
            started_at=now,
            expires_at=now + timedelta(days=30),
            stripe_subscription_id=f"mock_sub_{current_user.id}_{int(now.timestamp())}",
            stripe_customer_id=f"mock_cus_{current_user.id}",
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return SubscribeOut(subscription_id=str(sub.id), status=sub.status)
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )


@router.post("/cancel")
def cancel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        sub = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == current_user.id, UserSubscription.status == "active")
            .order_by(UserSubscription.id.desc())
            .first()
        )
        if sub:
            now = datetime.now(timezone.utc)
            sub.status = "cancelled"
            sub.cancelled_at = now
            # Optionally end access immediately
            if sub.expires_at is None or sub.expires_at > now:
                sub.expires_at = now
            db.commit()
        return {"status": "canceled"}
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )


@router.post("/change-plan", response_model=ChangePlanOut)
def change_plan(
    body: ChangePlanIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate new plan
        new_plan = db.get(SubscriptionPlan, body.new_plan_id)
        if not new_plan or not new_plan.is_active:
            raise HTTPException(status_code=400, detail="invalid plan")

        # Find current active subscription
        sub = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == current_user.id, UserSubscription.status == "active")
            .order_by(UserSubscription.id.desc())
            .first()
        )
        now = datetime.now(timezone.utc)
        if not sub:
            # No active sub: behave like subscribe
            new_sub = UserSubscription(
                user_id=current_user.id,
                plan_id=new_plan.id,
                status="active",
                started_at=now,
                expires_at=now + timedelta(days=30),
                stripe_subscription_id=f"mock_sub_{current_user.id}_{int(now.timestamp())}",
                stripe_customer_id=f"mock_cus_{current_user.id}",
            )
            db.add(new_sub)
            db.commit()
            db.refresh(new_sub)
            return ChangePlanOut(subscription_id=str(new_sub.id), status=new_sub.status)

        # Change plan in place (simplified). In real life you'd proration via payment provider
        sub.plan_id = new_plan.id
        sub.updated_at = now
        db.commit()
        db.refresh(sub)
        return ChangePlanOut(subscription_id=str(sub.id), status=sub.status)
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )
