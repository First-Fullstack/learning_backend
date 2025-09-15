from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[HttpUrl] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[HttpUrl] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
