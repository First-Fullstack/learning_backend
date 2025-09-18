from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.user import UserOut

class PaginationMeta(BaseModel):
    current_page: int
    total_pages: int
    total_count: int

class UserListResponse(BaseModel):
    users: List[UserOut]
    pagination: PaginationMeta
