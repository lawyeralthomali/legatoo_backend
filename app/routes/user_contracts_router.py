from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..db.database import get_db
from ..services.user_contract_service import UserContractService
from ..schemas.user_contract import (
    UserContractCreate, UserContractUpdate, UserContractResponse,
    ContractStatusUpdate, UserContractSummary
)
from ..schemas.response import ApiResponse

router = APIRouter(prefix="/api/contracts/user-contracts", tags=["user-contracts"])

@router.get("/", response_model=ApiResponse[List[UserContractResponse]])
async def get_user_contracts(
    user_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get user contracts with optional status filtering."""
    service = UserContractService()
    
    if status:
        contracts = await service.get_contracts_by_status(db, user_id, status)
    else:
        contracts = await service.get_user_contracts(db, user_id)
    
    return ApiResponse(
        success=True,
        message="User contracts retrieved successfully",
        data=contracts,
        errors=[]
    )

@router.get("/{user_contract_id}", response_model=ApiResponse[UserContractResponse])
async def get_user_contract(
    user_contract_id: int, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user contract."""
    service = UserContractService()
    contract = await service.get_user_contract_by_id(db, user_contract_id, user_id)
    
    return ApiResponse(
        success=True,
        message="Contract retrieved successfully",
        data=contract,
        errors=[]
    )

@router.post("/", response_model=ApiResponse[UserContractResponse])
async def create_user_contract(
    contract: UserContractCreate, 
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user contract."""
    service = UserContractService()
    new_contract = await service.create_user_contract(
        db=db,
        user_id=user_id,
        template_id=contract.template_id,
        contract_data=contract.contract_data
    )
    
    return ApiResponse(
        success=True,
        message="Contract created successfully",
        data=new_contract,
        errors=[]
    )

@router.put("/{user_contract_id}", response_model=ApiResponse[UserContractResponse])
async def update_user_contract(
    user_contract_id: int, 
    user_id: int,
    contract_update: UserContractUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update a user contract."""
    service = UserContractService()
    
    if contract_update.contract_data is not None:
        updated_contract = await service.update_contract_data(
            db=db,
            user_contract_id=user_contract_id,
            user_id=user_id,
            contract_data=contract_update.contract_data
        )
    elif contract_update.final_content is not None:
        updated_contract = await service.update_final_content(
            db=db,
            user_contract_id=user_contract_id,
            final_content=contract_update.final_content
        )
    elif contract_update.status is not None:
        updated_contract = await service.update_contract_status(
            db=db,
            user_contract_id=user_contract_id,
            user_id=user_id,
            status=contract_update.status
        )
    else:
        # Get the contract if no specific update is provided
        updated_contract = await service.get_user_contract_by_id(db, user_contract_id, user_id)
    
    return ApiResponse(
        success=True,
        message="Contract updated successfully",
        data=updated_contract,
        errors=[]
    )

@router.patch("/{user_contract_id}/status", response_model=ApiResponse[UserContractResponse])
async def update_contract_status(
    user_contract_id: int,
    user_id: int,
    status_update: ContractStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update contract status."""
    service = UserContractService()
    updated_contract = await service.update_contract_status(
        db=db,
        user_contract_id=user_contract_id,
        user_id=user_id,
        status=status_update.status
    )
    
    return ApiResponse(
        success=True,
        message="Contract status updated successfully",
        data=updated_contract,
        errors=[]
    )

@router.delete("/{user_contract_id}", response_model=ApiResponse[dict])
async def delete_user_contract(
    user_contract_id: int, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Delete a user contract."""
    service = UserContractService()
    await service.delete_user_contract(db, user_contract_id, user_id)
    
    return ApiResponse(
        success=True,
        message="Contract deleted successfully",
        data={"user_contract_id": user_contract_id},
        errors=[]
    )

@router.get("/user/{user_id}/drafts/", response_model=ApiResponse[List[UserContractResponse]])
async def get_draft_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's draft contracts."""
    service = UserContractService()
    contracts = await service.get_draft_contracts(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Draft contracts retrieved successfully",
        data=contracts,
        errors=[]
    )

@router.get("/user/{user_id}/completed/", response_model=ApiResponse[List[UserContractResponse]])
async def get_completed_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's completed contracts."""
    service = UserContractService()
    contracts = await service.get_completed_contracts(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Completed contracts retrieved successfully",
        data=contracts,
        errors=[]
    )

@router.get("/user/{user_id}/signed/", response_model=ApiResponse[List[UserContractResponse]])
async def get_signed_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's signed contracts."""
    service = UserContractService()
    contracts = await service.get_signed_contracts(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Signed contracts retrieved successfully",
        data=contracts,
        errors=[]
    )

@router.get("/user/{user_id}/summary/", response_model=ApiResponse[UserContractSummary])
async def get_contracts_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get contracts summary for a user."""
    service = UserContractService()
    summary = await service.get_contracts_summary(db, user_id)
    
    return ApiResponse(
        success=True,
        message="Contracts summary retrieved successfully",
        data=summary,
        errors=[]
    )

@router.post("/{user_contract_id}/duplicate", response_model=ApiResponse[UserContractResponse])
async def duplicate_contract(
    user_contract_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing contract."""
    service = UserContractService()
    new_contract = await service.duplicate_contract(db, user_contract_id, user_id)
    
    return ApiResponse(
        success=True,
        message="Contract duplicated successfully",
        data=new_contract,
        errors=[]
    )