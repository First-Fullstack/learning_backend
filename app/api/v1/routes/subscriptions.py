from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.subscription import Subscription, PlanType, Purchase
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut, PurchaseCreate, PurchaseOut

router = APIRouter()


@router.post("/subscribe", response_model=SubscriptionOut)
def subscribe(data: SubscriptionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = Subscription(user_id=current_user.id, plan=data.plan, is_active=True)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/cancel")
def cancel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id, Subscription.is_active == True)
        .order_by(Subscription.id.desc())
        .first()
    )
    if sub:
        sub.is_active = False
        db.commit()
    return {"status": "canceled"}


@router.post("/purchase", response_model=PurchaseOut)
def purchase(data: PurchaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = Purchase(
        user_id=current_user.id,
        course_id=data.course_id,
        amount=data.amount,
        currency=data.currency,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
