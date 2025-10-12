from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..db.database import get_db
from ..services.contracts.user_contract_service import UserContractService
from ..schemas.user_contract import (
    UserContractCreate, UserContractUpdate, UserContractResponse,
    ContractStatusUpdate, UserContractSummary
)
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response,
    raise_error_response
)

router = APIRouter(prefix="/api/contracts/user-contracts", tags=["user-contracts"])

@router.get("/", response_model=ApiResponse)
async def get_user_contracts(
    user_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get user contracts with optional status filtering."""
    try:
        service = UserContractService()
        
        if status:
            contracts = await service.get_contracts_by_status(db, user_id, status)
        else:
            contracts = await service.get_user_contracts(db, user_id)
        
        return create_success_response(
            message="User contracts retrieved successfully",
            data=contracts
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve user contracts",
            field="contracts",
            errors=[ErrorDetail(field="contracts", message=f"Internal server error: {str(e)}")]
        )

@router.get("/{user_contract_id}", response_model=ApiResponse)
async def get_user_contract(
    user_contract_id: int, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user contract."""
    try:
        service = UserContractService()
        contract = await service.get_user_contract_by_id(db, user_contract_id, user_id)
        
        if not contract:
            raise_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Contract not found",
                field="user_contract_id",
                errors=[ErrorDetail(field="user_contract_id", message="The requested contract was not found")]
            )
        
        return create_success_response(
            message="Contract retrieved successfully",
            data=contract
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )

@router.post("/", response_model=ApiResponse)
async def create_user_contract(
    contract: UserContractCreate, 
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user contract."""
    try:
        service = UserContractService()
        new_contract = await service.create_user_contract(
            db=db,
            user_id=user_id,
            template_id=contract.template_id,
            contract_data=contract.contract_data
        )
        
        return create_success_response(
            message="Contract created successfully",
            data=new_contract
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )

@router.put("/{user_contract_id}", response_model=ApiResponse)
async def update_user_contract(
    user_contract_id: int, 
    user_id: int,
    contract_update: UserContractUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update a user contract."""
    try:
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
        
        return create_success_response(
            message="Contract updated successfully",
            data=updated_contract
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )

@router.patch("/{user_contract_id}/status", response_model=ApiResponse)
async def update_contract_status(
    user_contract_id: int,
    user_id: int,
    status_update: ContractStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update contract status."""
    try:
        service = UserContractService()
        updated_contract = await service.update_contract_status(
            db=db,
            user_contract_id=user_contract_id,
            user_id=user_id,
            status=status_update.status
        )
        
        return create_success_response(
            message="Contract status updated successfully",
            data=updated_contract
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update contract status",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )

@router.delete("/{user_contract_id}", response_model=ApiResponse)
async def delete_user_contract(
    user_contract_id: int, 
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Delete a user contract."""
    try:
        service = UserContractService()
        await service.delete_user_contract(db, user_contract_id, user_id)
        
        return create_success_response(
            message="Contract deleted successfully",
            data={"user_contract_id": user_contract_id}
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )

@router.get("/user/{user_id}/drafts/", response_model=ApiResponse)
async def get_draft_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's draft contracts."""
    try:
        service = UserContractService()
        contracts = await service.get_draft_contracts(db, user_id)
        
        return create_success_response(
            message="Draft contracts retrieved successfully",
            data=contracts
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve draft contracts",
            field="contracts",
            errors=[ErrorDetail(field="contracts", message=f"Internal server error: {str(e)}")]
        )

@router.get("/user/{user_id}/completed/", response_model=ApiResponse)
async def get_completed_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's completed contracts."""
    try:
        service = UserContractService()
        contracts = await service.get_completed_contracts(db, user_id)
        
        return create_success_response(
            message="Completed contracts retrieved successfully",
            data=contracts
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve completed contracts",
            field="contracts",
            errors=[ErrorDetail(field="contracts", message=f"Internal server error: {str(e)}")]
        )

@router.get("/user/{user_id}/signed/", response_model=ApiResponse)
async def get_signed_contracts(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's signed contracts."""
    try:
        service = UserContractService()
        contracts = await service.get_signed_contracts(db, user_id)
        
        return create_success_response(
            message="Signed contracts retrieved successfully",
            data=contracts
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve signed contracts",
            field="contracts",
            errors=[ErrorDetail(field="contracts", message=f"Internal server error: {str(e)}")]
        )

@router.get("/user/{user_id}/summary/", response_model=ApiResponse)
async def get_contracts_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get contracts summary for a user."""
    try:
        service = UserContractService()
        summary = await service.get_contracts_summary(db, user_id)
        
        return create_success_response(
            message="Contracts summary retrieved successfully",
            data=summary
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve contracts summary",
            field="summary",
            errors=[ErrorDetail(field="summary", message=f"Internal server error: {str(e)}")]
        )

@router.post("/{user_contract_id}/duplicate", response_model=ApiResponse)
async def duplicate_contract(
    user_contract_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing contract."""
    try:
        service = UserContractService()
        new_contract = await service.duplicate_contract(db, user_contract_id, user_id)
        
        return create_success_response(
            message="Contract duplicated successfully",
            data=new_contract
        )
    
    except Exception as e:
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to duplicate contract",
            field="contract",
            errors=[ErrorDetail(field="contract", message=f"Internal server error: {str(e)}")]
        )