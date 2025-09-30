from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .template import TemplateResponse


class FavoriteBase(BaseModel):
    template_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteResponse(FavoriteBase):
    favorite_id: int
    user_id: int
    created_at: datetime
    template: Optional[TemplateResponse] = None
    
    class Config:
        from_attributes = True


class FavoriteToggleResponse(BaseModel):
    template_id: int
    is_favorite: bool
    action: str  # 'added' or 'removed'


class FavoriteCountResponse(BaseModel):
    template_id: int
    favorite_count: int


class MostFavoritedTemplate(BaseModel):
    template_id: int
    favorite_count: int
