from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.user import UserOut, UserUpdate

class PaginationMeta(BaseModel):
    current_page: int
    total_pages: int
    total_count: int

class UserListResponse(BaseModel):
    users: List[UserOut]
    pagination: PaginationMeta


class AdminDashboardOut(BaseModel):
    total_users: int
    total_courses: int
    active_subscriptions: int
    total_revenue: int
    monthly_growth: float
