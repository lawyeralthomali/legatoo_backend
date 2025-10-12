from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from uuid import UUID
from ..db.database import get_db
from ..services.contracts.contract_template_service import ContractTemplateService
from ..schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse
from ..schemas.user_contract import ContractGenerationRequest, ContractGenerationResponse
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response,
    raise_error_response
)
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/api/contracts/templates", tags=["templates"])

@router.get("/", response_model=ApiResponse)
async def get_templates(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    is_featured: Optional[bool] = Query(None, description="Filter featured templates"),
    is_premium: Optional[bool] = Query(None, description="Filter premium templates"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get templates with filtering and search options."""
    try:
        service = ContractTemplateService()
        templates = await service.get_templates(
            db=db,
            category_id=category_id,
            search=search,
            is_featured=is_featured,
            is_premium=is_premium
        )
        
        return create_success_response(
            message="Templates retrieved successfully",
            data=templates
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve templates",
            field="templates",
            errors=[ErrorDetail(field="templates", message=f"Internal server error: {str(e)}")]
        )

@router.get("/{template_id}", response_model=ApiResponse)
async def get_template(
    template_id: int, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID."""
    try:
        service = ContractTemplateService()
        template = await service.get_template_by_id(db, template_id)
        
        if not template:
            raise_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Template not found",
                field="template_id",
                errors=[ErrorDetail(field="template_id", message="The requested template was not found")]
            )
        
        return create_success_response(
            message="Template retrieved successfully",
            data=template
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve template",
            field="template",
            errors=[ErrorDetail(field="template", message=f"Internal server error: {str(e)}")]
        )

@router.post("/", response_model=ApiResponse)
async def create_template(
    template: TemplateCreate, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new template."""
    try:
        service = ContractTemplateService()
        new_template = await service.create_template(db, template, current_user_id)
        
        return create_success_response(
            message="Template created successfully",
            data=new_template
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create template",
            field="template",
            errors=[ErrorDetail(field="template", message=f"Internal server error: {str(e)}")]
        )

@router.put("/{template_id}", response_model=ApiResponse)
async def update_template(
    template_id: int, 
    template_update: TemplateUpdate, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing template."""
    try:
        service = ContractTemplateService()
        updated_template = await service.update_template(db, template_id, template_update)
        
        return create_success_response(
            message="Template updated successfully",
            data=updated_template
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update template",
            field="template",
            errors=[ErrorDetail(field="template", message=f"Internal server error: {str(e)}")]
        )

@router.delete("/{template_id}", response_model=ApiResponse)
async def delete_template(
    template_id: int, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a template (soft delete)."""
    try:
        service = ContractTemplateService()
        await service.delete_template(db, template_id)
        
        return create_success_response(
            message="Template deleted successfully",
            data={"template_id": template_id}
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete template",
            field="template",
            errors=[ErrorDetail(field="template", message=f"Internal server error: {str(e)}")]
        )

@router.get("/featured/", response_model=ApiResponse)
async def get_featured_templates(
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get featured templates."""
    try:
        service = ContractTemplateService()
        templates = await service.get_featured_templates(db)
        
        return create_success_response(
            message="Featured templates retrieved successfully",
            data=templates
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve featured templates",
            field="templates",
            errors=[ErrorDetail(field="templates", message=f"Internal server error: {str(e)}")]
        )

@router.get("/premium/", response_model=ApiResponse)
async def get_premium_templates(
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get premium templates."""
    try:
        service = ContractTemplateService()
        templates = await service.get_premium_templates(db)
        
        return create_success_response(
            message="Premium templates retrieved successfully",
            data=templates
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve premium templates",
            field="templates",
            errors=[ErrorDetail(field="templates", message=f"Internal server error: {str(e)}")]
        )

@router.get("/free/", response_model=ApiResponse)
async def get_free_templates(
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get free templates."""
    try:
        service = ContractTemplateService()
        templates = await service.get_free_templates(db)
        
        return create_success_response(
            message="Free templates retrieved successfully",
            data=templates
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve free templates",
            field="templates",
            errors=[ErrorDetail(field="templates", message=f"Internal server error: {str(e)}")]
        )

@router.post("/{template_id}/generate", response_model=ApiResponse)
async def generate_contract(
    template_id: int, 
    contract_data: ContractGenerationRequest, 
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate a contract from a template."""
    try:
        service = ContractTemplateService()
        result = await service.generate_contract_from_template(
            db=db,
            template_id=template_id,
            contract_data=contract_data.contract_data,
            user_id=current_user_id
        )
        
        return create_success_response(
            message="Contract generated successfully",
            data=result
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to generate contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )