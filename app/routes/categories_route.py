from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..db.database import get_db
from ..services.contract_category_service import ContractCategoryService
from ..schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from ..schemas.response import ApiResponse
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/api/contracts/categories", tags=["categories"])

@router.get("/", response_model=ApiResponse[List[CategoryResponse]])
async def get_categories(
    parent_id: Optional[int] = Query(None, description="Filter by parent category"),
    is_active: bool = Query(True, description="Filter by active status"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all categories with optional filtering."""
    service = ContractCategoryService()
    categories = await service.get_categories(db, parent_id, is_active)
    
    return ApiResponse(
        success=True,
        message="Categories retrieved successfully",
        data=categories,
        errors=[]
    )

@router.get("/{category_id}", response_model=ApiResponse[CategoryResponse])
async def get_category(
    category_id: int, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID."""
    service = ContractCategoryService()
    category = await service.get_category_by_id(db, category_id)
    
    return ApiResponse(
        success=True,
        message="Category retrieved successfully",
        data=category,
        errors=[]
    )

@router.post("/", response_model=ApiResponse[CategoryResponse])
async def create_category(
    category: CategoryCreate, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category."""
    service = ContractCategoryService()
    new_category = await service.create_category(db, category)
    
    return ApiResponse(
        success=True,
        message="Category created successfully",
        data=new_category,
        errors=[]
    )

@router.put("/{category_id}", response_model=ApiResponse[CategoryResponse])
async def update_category(
    category_id: int, 
    category_update: CategoryUpdate, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category."""
    service = ContractCategoryService()
    updated_category = await service.update_category(db, category_id, category_update)
    
    return ApiResponse(
        success=True,
        message="Category updated successfully",
        data=updated_category,
        errors=[]
    )

@router.delete("/{category_id}", response_model=ApiResponse[dict])
async def delete_category(
    category_id: int, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a category (soft delete)."""
    service = ContractCategoryService()
    await service.delete_category(db, category_id)
    
    return ApiResponse(
        success=True,
        message="Category deleted successfully",
        data={"category_id": category_id},
        errors=[]
    )

@router.get("/search/", response_model=ApiResponse[List[CategoryResponse]])
async def search_categories(
    q: str = Query(..., description="Search term"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search categories by name."""
    service = ContractCategoryService()
    categories = await service.search_categories(db, q)
    
    return ApiResponse(
        success=True,
        message="Search completed successfully",
        data=categories,
        errors=[]
    )

@router.get("/hierarchy/", response_model=ApiResponse[List[CategoryResponse]])
async def get_category_hierarchy(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get complete category hierarchy."""
    service = ContractCategoryService()
    hierarchy = await service.get_category_hierarchy(db)
    
    return ApiResponse(
        success=True,
        message="Category hierarchy retrieved successfully",
        data=hierarchy,
        errors=[]
    )