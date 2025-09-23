from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan, UserSubscription
from app.schemas.subscription import SubscriptionPlanOut, SubscribeIn, SubscribeOut

router = APIRouter()

@router.get('/plans', response_model=list[SubscriptionPlanOut])
def list_plans(db: Session = Depends(get_db)):
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

@router.post("/subscribe", response_model=SubscribeOut)
def subscribe(body: SubscribeIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.get(SubscriptionPlan, body.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=400, detail="invalid plan")

    # Here you'd call your payment processor using body.payment_method_id
    # For now, assume payment succeeds and create the subscription
    sub = UserSubscription(user_id=current_user.id, plan_id=plan.id, status="active")
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return SubscribeOut(subscription_id=str(sub.id), status=sub.status)


@router.post("/cancel")
def cancel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = (
        db.query(UserSubscription)
        .filter(UserSubscription.user_id == current_user.id, UserSubscription.status == "active")
        .order_by(UserSubscription.id.desc())
        .first()
    )
    if sub:
        sub.status = "cancelled"
        db.commit()
    return {"status": "canceled"}
