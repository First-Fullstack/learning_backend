from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, AuthResponse, Token, TokenPayload, LoginRequest
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter()

reuseable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user: User | None = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={
                "error": 400,
                "message": "Email already registered",
                "details": {}
            }
        )
    try:
        user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=str(user.id))
        return AuthResponse(user=user, token=token)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": 500,
                "message": "Database error",
                "details": {"exception": str(e)}
            }
        )

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証失敗"
        )
    user.last_login_at = datetime.now(tz=timezone.utc)
    db.commit()
    token = create_access_token(subject=str(user.id))
    return AuthResponse(user=user, token=token)


@router.post("/logout")
def logout():
    return {"message": "logged out"}


@router.post("/password/reset")
def password_reset_request(email: str):
    return {"message": "If the email exists, a reset link was sent."}

def get_current_user(db: Session = Depends(get_db), token: str = Depends(reuseable_oauth2)) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    user = db.get(User, int(token_data.sub)) if token_data.sub else None
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return user
