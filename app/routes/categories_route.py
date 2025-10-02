from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from uuid import UUID
from ..db.database import get_db
from ..services.contract_category_service import ContractCategoryService
from ..schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response
)
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/api/contracts/categories", tags=["categories"])

@router.get("/", response_model=ApiResponse)
async def get_categories(
    parent_id: Optional[int] = Query(None, description="Filter by parent category"),
    is_active: bool = Query(True, description="Filter by active status"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get all categories with optional filtering."""
    try:
        service = ContractCategoryService()
        categories = await service.get_categories(db, parent_id, is_active)
        
        return create_success_response(
            message="Categories retrieved successfully",
            data={"categories": categories}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve categories",
            errors=[ErrorDetail(field="categories", message=f"Internal server error: {str(e)}")]
        )

@router.get("/{category_id}", response_model=ApiResponse)
async def get_category(
    category_id: int, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get a specific category by ID."""
    try:
        service = ContractCategoryService()
        category = await service.get_category_by_id(db, category_id)
        
        if not category:
            return create_not_found_response(
                resource="Category",
                field="category_id"
            )
        
        return create_success_response(
            message="Category retrieved successfully",
            data=category
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve category",
            errors=[ErrorDetail(field="category", message=f"Internal server error: {str(e)}")]
        )

@router.post("/", response_model=ApiResponse)
async def create_category(
    category: CategoryCreate, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Create a new category."""
    try:
        service = ContractCategoryService()
        new_category = await service.create_category(db, category)
        
        return create_success_response(
            message="Category created successfully",
            data=new_category
        )
    except Exception as e:
        return create_error_response(
            message="Failed to create category",
            errors=[ErrorDetail(field="category", message=f"Internal server error: {str(e)}")]
        )

@router.put("/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: int, 
    category_update: CategoryUpdate, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Update an existing category."""
    try:
        service = ContractCategoryService()
        updated_category = await service.update_category(db, category_id, category_update)
        
        if not updated_category:
            return create_not_found_response(
                resource="Category",
                field="category_id"
            )
        
        return create_success_response(
            message="Category updated successfully",
            data=updated_category
        )
    except Exception as e:
        return create_error_response(
            message="Failed to update category",
            errors=[ErrorDetail(field="category", message=f"Internal server error: {str(e)}")]
        )

@router.delete("/{category_id}", response_model=ApiResponse)
async def delete_category(
    category_id: int, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Delete a category (soft delete)."""
    try:
        service = ContractCategoryService()
        success = await service.delete_category(db, category_id)
        
        if not success:
            return create_not_found_response(
                resource="Category",
                field="category_id"
            )
        
        return create_success_response(
            message="Category deleted successfully",
            data={"category_id": category_id}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to delete category",
            errors=[ErrorDetail(field="category", message=f"Internal server error: {str(e)}")]
        )

@router.get("/search/", response_model=ApiResponse)
async def search_categories(
    q: str = Query(..., description="Search term"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Search categories by name."""
    try:
        service = ContractCategoryService()
        categories = await service.search_categories(db, q)
        
        return create_success_response(
            message="Search completed successfully",
            data={"categories": categories}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to search categories",
            errors=[ErrorDetail(field="search", message=f"Internal server error: {str(e)}")]
        )

@router.get("/hierarchy/", response_model=ApiResponse)
async def get_category_hierarchy(
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get complete category hierarchy."""
    try:
        service = ContractCategoryService()
        hierarchy = await service.get_category_hierarchy(db)
        
        return create_success_response(
            message="Category hierarchy retrieved successfully",
            data={"hierarchy": hierarchy}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve category hierarchy",
            errors=[ErrorDetail(field="hierarchy", message=f"Internal server error: {str(e)}")]
        )