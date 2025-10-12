from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..db.database import get_db
from ..services.contracts.user_favorite_service import UserFavoriteService
from ..schemas.favorite import (
    FavoriteCreate, FavoriteResponse, FavoriteToggleResponse,
    FavoriteCountResponse, MostFavoritedTemplate
)
from ..schemas.response import ApiResponse

router = APIRouter(prefix="/api/contracts/favorites", tags=["favorites"])

@router.get("/", response_model=ApiResponse[List[FavoriteResponse]])
async def get_user_favorites(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's favorite templates."""
    service = UserFavoriteService()
    favorites = await service.get_user_favorites(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Favorites retrieved successfully",
        data=favorites,
        errors=[]
    )

@router.post("/", response_model=ApiResponse[FavoriteResponse])
async def add_favorite(
    favorite: FavoriteCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Add a template to favorites."""
    service = UserFavoriteService()
    new_favorite = await service.add_favorite(db, user_id, favorite.template_id)
    
    return ApiResponse(
        success=True,
        message="Template added to favorites successfully",
        data=new_favorite,
        errors=[]
    )

@router.delete("/{template_id}", response_model=ApiResponse[dict])
async def remove_favorite(
    template_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove a template from favorites."""
    service = UserFavoriteService()
    await service.remove_favorite(db, user_id, template_id)
    
    return ApiResponse(
        success=True,
        message="Template removed from favorites successfully",
        data={"template_id": template_id},
        errors=[]
    )

@router.post("/toggle/{template_id}", response_model=ApiResponse[FavoriteToggleResponse])
async def toggle_favorite(
    template_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle favorite status for a template."""
    service = UserFavoriteService()
    result = await service.toggle_favorite(db, user_id, template_id)
    
    return ApiResponse(
        success=True,
        message="Favorite status toggled successfully",
        data=result,
        errors=[]
    )

@router.get("/check/{template_id}", response_model=ApiResponse[dict])
async def check_favorite(
    template_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Check if a template is in favorites."""
    service = UserFavoriteService()
    is_favorite = await service.is_favorite(db, user_id, template_id)
    
    return ApiResponse(
        success=True,
        message="Favorite status checked successfully",
        data={"template_id": template_id, "is_favorite": is_favorite},
        errors=[]
    )

@router.get("/count/", response_model=ApiResponse[dict])
async def get_favorite_count(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get favorite count for a user."""
    service = UserFavoriteService()
    count = await service.get_favorite_count(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Favorite count retrieved successfully",
        data={"user_id": user_id, "favorite_count": count},
        errors=[]
    )

@router.get("/template/{template_id}/count", response_model=ApiResponse[FavoriteCountResponse])
async def get_template_favorite_count(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get favorite count for a template."""
    service = UserFavoriteService()
    count = await service.get_template_favorite_count(db, template_id)
    
    return ApiResponse(
        success=True,
        message="Template favorite count retrieved successfully",
        data={"template_id": template_id, "favorite_count": count},
        errors=[]
    )

@router.get("/most-favorited/", response_model=ApiResponse[List[MostFavoritedTemplate]])
async def get_most_favorited_templates(
    limit: int = Query(10, description="Number of templates to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get most favorited templates."""
    service = UserFavoriteService()
    templates = await service.get_most_favorited_templates(db, limit)
    
    return ApiResponse(
        success=True,
        message="Most favorited templates retrieved successfully",
        data=templates,
        errors=[]
    )

@router.get("/recent/", response_model=ApiResponse[List[FavoriteResponse]])
async def get_recent_favorites(
    limit: int = Query(10, description="Number of favorites to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get recently added favorites."""
    service = UserFavoriteService()
    favorites = await service.get_recent_favorites(db, limit)
    
    return ApiResponse(
        success=True,
        message="Recent favorites retrieved successfully",
        data=favorites,
        errors=[]
    )

@router.delete("/clear/", response_model=ApiResponse[dict])
async def clear_user_favorites(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Clear all favorites for a user."""
    service = UserFavoriteService()
    count = await service.clear_user_favorites(db, user_id)
    
    return ApiResponse(
        success=True,
        message="All favorites cleared successfully",
        data={"user_id": user_id, "removed_count": count},
        errors=[]
    )