"""
Contracts Library API Router

RESTful endpoints for managing contracts, templates, revisions, and AI generation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..utils.auth import get_current_user
from ..schemas.profile_schemas import TokenData
from ..schemas.contracts_library import (
    ContractCreate, ContractUpdate, ContractResponse, ContractListResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    RevisionCreate, RevisionHistoryResponse,
    AIGenerateRequest, AIGenerateResponse,
    ContractFilters, TemplateFilters
)
from ..services.contracts.contracts_library_service import ContractsLibraryService

router = APIRouter(prefix="/contracts", tags=["contracts"])


# ============ Contract Endpoints ============

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contract."""
    service = ContractsLibraryService(db)
    try:
        contract = await service.create_contract(contract_data, current_user.sub)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    category: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    ai_generated: Optional[bool] = Query(None),
    search_query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contracts with filtering and pagination."""
    filters = ContractFilters(
        category=category,
        jurisdiction=jurisdiction,
        status=status,
        language=language,
        ai_generated=ai_generated,
        search_query=search_query,
        page=page,
        page_size=page_size
    )
    service = ContractsLibraryService(db)
    try:
        result = await service.list_contracts(filters, current_user.sub)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contract by ID."""
    service = ContractsLibraryService(db)
    try:
        # Ensure user_id is an int (handle both int and UUID types from TokenData)
        user_id = int(current_user.sub) if isinstance(current_user.sub, (int, str)) and str(current_user.sub).isdigit() else None
        
        contract = await service.get_contract(contract_id, user_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Contract with ID '{contract_id}' not found"
            )
        return contract
    except ValueError as e:
        if "Access denied" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: str,
    update_data: ContractUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update contract."""
    service = ContractsLibraryService(db)
    try:
        contract = await service.update_contract(contract_id, update_data, current_user.sub)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        return contract
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete (archive) contract."""
    service = ContractsLibraryService(db)
    try:
        success = await service.delete_contract(contract_id, current_user.sub)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============ AI Generation Endpoints ============

@router.post("/generate", response_model=AIGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_contract_with_ai(
    request: AIGenerateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a contract using AI."""
    service = ContractsLibraryService(db)
    try:
        result = await service.generate_contract_with_ai(request, current_user.sub)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/{request_id}/save", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def save_ai_generated_contract(
    request_id: str,
    contract_data: ContractCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save AI-generated content as a contract."""
    service = ContractsLibraryService(db)
    try:
        contract = await service.save_ai_generated_contract(request_id, contract_data, current_user.sub)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============ Revision Endpoints ============

@router.get("/{contract_id}/history", response_model=RevisionHistoryResponse)
async def get_revision_history(
    contract_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get revision history for a contract."""
    service = ContractsLibraryService(db)
    try:
        history = await service.get_revision_history(contract_id, current_user.sub)
        return history
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{contract_id}/revise", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_revision(
    contract_id: str,
    revision_data: RevisionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new revision for a contract."""
    from ..schemas.contracts_library import RevisionResponse
    service = ContractsLibraryService(db)
    try:
        revision = await service.create_revision(contract_id, revision_data, current_user.sub)
        # Return updated contract
        contract = await service.get_contract(contract_id, current_user.sub)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============ Template Endpoints ============

@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contract template."""
    service = ContractsLibraryService(db)
    try:
        template = await service.create_template(template_data, current_user.sub)
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/templates", response_model=dict)
async def list_templates(
    category: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    search_query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[TokenData] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contract templates with filtering."""
    tag_list = tags.split(",") if tags else None
    filters = TemplateFilters(
        category=category,
        jurisdiction=jurisdiction,
        language=language,
        is_public=is_public,
        tags=tag_list,
        search_query=search_query,
        page=page,
        page_size=page_size
    )
    service = ContractsLibraryService(db)
    try:
        user_id = current_user.sub if current_user else None
        result = await service.list_templates(filters, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get template by ID."""
    service = ContractsLibraryService(db)
    try:
        user_id = current_user.sub if current_user else None
        template = await service.get_template(template_id, user_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    update_data: TemplateUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update template."""
    service = ContractsLibraryService(db)
    try:
        template = await service.update_template(template_id, update_data, current_user.sub)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete template."""
    service = ContractsLibraryService(db)
    try:
        success = await service.delete_template(template_id, current_user.sub)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/templates/{template_id}/generate", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def generate_from_template(
    template_id: str,
    placeholder_data: dict,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a contract from a template by replacing placeholders."""
    service = ContractsLibraryService(db)
    try:
        contract = await service.generate_from_template(template_id, placeholder_data, current_user.sub)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
