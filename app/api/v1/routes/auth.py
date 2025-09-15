from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, Token, TokenPayload
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter()

reuseable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user: User | None = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.post("/logout")
def logout():
    # Stateless JWT; client discards token
    return {"message": "logged out"}


@router.post("/password/reset")
def password_reset_request(email: str):
    # Stub for sending reset email
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
