import email
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None   # nullable in DB
    email_verified: bool

    class Config:
        from_attributes = True  # Pydantic v2 (use orm_mode=True for v1)

class LoginRequest(BaseModel):
    email: str
    password: str

class ResetPassword(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str

# --- New wrapper for the register/login response ---
class AuthResponse(BaseModel):
    user: UserOut          # nested user info
    token: str             # JWT or similar


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
