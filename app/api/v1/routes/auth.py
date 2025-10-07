from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.deps import get_db
from app.models.user import User
from app.models.token import PasswordResetToken
from app.schemas.user import ResetPassword, UserCreate, AuthResponse, Token, TokenPayload, LoginRequest, PasswordResetConfirm
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter()

reuseable_oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


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
                "message": "メールアドレスはすでに登録されています",
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
                "message": "サーバーエラー",
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

    # ユーザーの last_login_at を更新
    db.execute(
        text("UPDATE users SET last_login_at = :ts, email_verified = true WHERE id = :id"),
        {"ts": datetime.now(tz=timezone.utc), "id": user.id},
    )
    db.commit()
    db.refresh(user)

    # アクセストークン生成
    token = create_access_token(subject=str(user.id))

    # Token を DB に保存
    expires_minutes = settings.access_token_expire_minutes
    expire_at = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)

    db_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expire_at,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    # レスポンス
    return AuthResponse(user=user, token=token)


@router.post("/logout")
def logout():
    return {"message": "ログアウト成功"}

@router.post("/password/reset")
def password_reset_request(payload: ResetPassword, db: Session = Depends(get_db)):
    # Try to find user by email
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        return {"message": "リセットメール送信成功"}
    else:
        return {"message": "メールアドレスが存在しません"}

@router.post("/password/reset/confirm", status_code=200)
def reset_password_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset_entry = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    expires_minutes = settings.access_token_expire_minutes
    reset_entry.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    # 2. Fetch the user
    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Update password
    user.password_hash = get_password_hash(payload.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reset_entry)

    return {"message": "Password successfully reset"}


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

# def create_password_reset_token(db: Session, user: User) -> PasswordResetToken:
#     # Token expiry (example: 30 minutes)
#     expires_minutes = settings.access_token_expire_minutes
#     expire_at = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)

#     # Generate token string (JWT)
#     token = create_access_token(subject=str(user.id), expires_minutes=expires_minutes)

#     # Save into DB
#     db_token = PasswordResetToken(
#         user_id=user.id,
#         token=token,
#         expires_at=expire_at,
#     )
#     db.add(db_token)
#     db.commit()
#     db.refresh(db_token)

#     return db_token