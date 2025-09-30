from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..db.database import get_db
from ..services.contract_template_service import ContractTemplateService
from ..schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse
from ..schemas.user_contract import ContractGenerationRequest, ContractGenerationResponse
from ..schemas.response import ApiResponse
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/api/contracts/templates", tags=["templates"])

@router.get("/", response_model=ApiResponse[List[TemplateResponse]])
async def get_templates(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    is_featured: Optional[bool] = Query(None, description="Filter featured templates"),
    is_premium: Optional[bool] = Query(None, description="Filter premium templates"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get templates with filtering and search options."""
    service = ContractTemplateService()
    templates = await service.get_templates(
        db=db,
        category_id=category_id,
        search=search,
        is_featured=is_featured,
        is_premium=is_premium
    )
    
    return ApiResponse(
        success=True,
        message="Templates retrieved successfully",
        data=templates,
        errors=[]
    )

@router.get("/{template_id}", response_model=ApiResponse[TemplateResponse])
async def get_template(
    template_id: int, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID."""
    service = ContractTemplateService()
    template = await service.get_template_by_id(db, template_id)
    
    return ApiResponse(
        success=True,
        message="Template retrieved successfully",
        data=template,
        errors=[]
    )

@router.post("/", response_model=ApiResponse[TemplateResponse])
async def create_template(
    template: TemplateCreate, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new template."""
    service = ContractTemplateService()
    new_template = await service.create_template(db, template, current_user_id)
    
    return ApiResponse(
        success=True,
        message="Template created successfully",
        data=new_template,
        errors=[]
    )

@router.put("/{template_id}", response_model=ApiResponse[TemplateResponse])
async def update_template(
    template_id: int, 
    template_update: TemplateUpdate, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing template."""
    service = ContractTemplateService()
    updated_template = await service.update_template(db, template_id, template_update)
    
    return ApiResponse(
        success=True,
        message="Template updated successfully",
        data=updated_template,
        errors=[]
    )

@router.delete("/{template_id}", response_model=ApiResponse[dict])
async def delete_template(
    template_id: int, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a template (soft delete)."""
    service = ContractTemplateService()
    await service.delete_template(db, template_id)
    
    return ApiResponse(
        success=True,
        message="Template deleted successfully",
        data={"template_id": template_id},
        errors=[]
    )

@router.get("/featured/", response_model=ApiResponse[List[TemplateResponse]])
async def get_featured_templates(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get featured templates."""
    service = ContractTemplateService()
    templates = await service.get_featured_templates(db)
    
    return ApiResponse(
        success=True,
        message="Featured templates retrieved successfully",
        data=templates,
        errors=[]
    )

@router.get("/premium/", response_model=ApiResponse[List[TemplateResponse]])
async def get_premium_templates(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get premium templates."""
    service = ContractTemplateService()
    templates = await service.get_premium_templates(db)
    
    return ApiResponse(
        success=True,
        message="Premium templates retrieved successfully",
        data=templates,
        errors=[]
    )

@router.get("/free/", response_model=ApiResponse[List[TemplateResponse]])
async def get_free_templates(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get free templates."""
    service = ContractTemplateService()
    templates = await service.get_free_templates(db)
    
    return ApiResponse(
        success=True,
        message="Free templates retrieved successfully",
        data=templates,
        errors=[]
    )

@router.post("/{template_id}/generate", response_model=ApiResponse[ContractGenerationResponse])
async def generate_contract(
    template_id: int, 
    contract_data: ContractGenerationRequest, 
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate a contract from a template."""
    service = ContractTemplateService()
    result = await service.generate_contract_from_template(
        db=db,
        template_id=template_id,
        contract_data=contract_data.contract_data,
        user_id=current_user_id
    )
    
    return ApiResponse(
        success=True,
        message="Contract generated successfully",
        data=result,
        errors=[]
    )