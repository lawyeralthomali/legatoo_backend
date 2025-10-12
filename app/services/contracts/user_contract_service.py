from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from ...repositories.user_contract_repository import UserContractRepository
from ...models.user_contract import UserContract
from ...utils.api_exceptions import ApiException


class UserContractService:
    """Service for user contract business logic following SOLID principles."""
    
    def __init__(self):
        self.repository = UserContractRepository()
    
    async def get_user_contracts(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[UserContract]:
        """Get all contracts for a user."""
        return await self.repository.get_by_user_id(db, user_id)
    
    async def get_user_contract_by_id(
        self, 
        db: AsyncSession, 
        user_contract_id: int,
        user_id: int
    ) -> UserContract:
        """Get a specific user contract with ownership validation."""
        contract = await self.repository.get_by_id(db, user_contract_id)
        if not contract:
            raise ApiException(
                status_code=404,
                message="Contract not found",
                errors=[{"field": "user_contract_id", "message": "Contract does not exist"}]
            )
        
        if contract.user_id != user_id:
            raise ApiException(
                status_code=403,
                message="Access denied",
                errors=[{"field": "user_contract_id", "message": "You don't have permission to access this contract"}]
            )
        
        return contract
    
    async def create_user_contract(
        self, 
        db: AsyncSession, 
        user_id: int,
        template_id: int,
        contract_data: Dict[str, Any]
    ) -> UserContract:
        """Create a new user contract."""
        # Validate template exists and is active
        from ...repositories.contract_template_repository import ContractTemplateRepository
        template_repo = ContractTemplateRepository()
        template = await template_repo.get_by_id(db, template_id)
        
        if not template or not template.is_active:
            raise ApiException(
                status_code=400,
                message="Invalid template",
                errors=[{"field": "template_id", "message": "Template not found or inactive"}]
            )
        
        # Process template and generate final content
        from .contract_template_service import ContractTemplateService
        template_service = ContractTemplateService()
        
        # Generate final content
        final_content = template_service._process_template(template.contract_structure, contract_data)
        
        # Create user contract
        user_contract = UserContract(
            user_id=user_id,
            template_id=template_id,
            contract_data=contract_data,
            final_content=final_content,
            status="draft"
        )
        
        db.add(user_contract)
        await db.commit()
        await db.refresh(user_contract)
        
        return user_contract
    
    async def update_contract_data(
        self, 
        db: AsyncSession, 
        user_contract_id: int,
        user_id: int,
        contract_data: Dict[str, Any]
    ) -> UserContract:
        """Update contract data and regenerate content."""
        contract = await self.get_user_contract_by_id(db, user_contract_id, user_id)
        
        # Get template to regenerate content
        template = contract.template
        if not template:
            raise ApiException(
                status_code=400,
                message="Template not found",
                errors=[{"field": "template_id", "message": "Associated template not found"}]
            )
        
        # Process template with new data
        from .contract_template_service import ContractTemplateService
        template_service = ContractTemplateService()
        final_content = template_service._process_template(template.contract_structure, contract_data)
        
        # Update contract
        contract.contract_data = contract_data
        contract.final_content = final_content
        
        await db.commit()
        await db.refresh(contract)
        
        return contract
    
    async def update_contract_status(
        self, 
        db: AsyncSession, 
        user_contract_id: int,
        user_id: int,
        status: str
    ) -> UserContract:
        """Update contract status."""
        valid_statuses = ["draft", "completed", "signed"]
        if status not in valid_statuses:
            raise ApiException(
                status_code=400,
                message="Invalid status",
                errors=[{"field": "status", "message": f"Status must be one of: {', '.join(valid_statuses)}"}]
            )
        
        contract = await self.get_user_contract_by_id(db, user_contract_id, user_id)
        contract.status = status
        
        await db.commit()
        await db.refresh(contract)
        
        return contract
    
    async def get_contracts_by_status(
        self, 
        db: AsyncSession, 
        user_id: int,
        status: str
    ) -> List[UserContract]:
        """Get user contracts by status."""
        valid_statuses = ["draft", "completed", "signed"]
        if status not in valid_statuses:
            raise ApiException(
                status_code=400,
                message="Invalid status",
                errors=[{"field": "status", "message": f"Status must be one of: {', '.join(valid_statuses)}"}]
            )
        
        return await self.repository.get_user_contracts_by_status(db, user_id, status)
    
    async def get_draft_contracts(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[UserContract]:
        """Get user's draft contracts."""
        return await self.repository.get_draft_contracts(db, user_id)
    
    async def get_completed_contracts(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[UserContract]:
        """Get user's completed contracts."""
        return await self.repository.get_completed_contracts(db, user_id)
    
    async def get_signed_contracts(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[UserContract]:
        """Get user's signed contracts."""
        return await self.repository.get_signed_contracts(db, user_id)
    
    async def get_contracts_summary(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Dict[str, Any]:
        """Get contracts summary for a user."""
        contracts_count = await self.repository.get_contracts_count_by_user(db, user_id)
        
        return {
            "total_contracts": sum(contracts_count.values()),
            "by_status": contracts_count,
            "draft_count": contracts_count.get("draft", 0),
            "completed_count": contracts_count.get("completed", 0),
            "signed_count": contracts_count.get("signed", 0)
        }
    
    async def delete_user_contract(
        self, 
        db: AsyncSession, 
        user_contract_id: int,
        user_id: int
    ) -> bool:
        """Delete a user contract (only if it's still in draft status)."""
        contract = await self.get_user_contract_by_id(db, user_contract_id, user_id)
        
        if contract.status != "draft":
            raise ApiException(
                status_code=400,
                message="Cannot delete contract",
                errors=[{"field": "status", "message": "Only draft contracts can be deleted"}]
            )
        
        await db.delete(contract)
        await db.commit()
        
        return True
    
    async def duplicate_contract(
        self, 
        db: AsyncSession, 
        user_contract_id: int,
        user_id: int
    ) -> UserContract:
        """Duplicate an existing contract."""
        original_contract = await self.get_user_contract_by_id(db, user_contract_id, user_id)
        
        # Create new contract with same data but draft status
        new_contract = UserContract(
            user_id=user_id,
            template_id=original_contract.template_id,
            contract_data=original_contract.contract_data,
            final_content=original_contract.final_content,
            status="draft"
        )
        
        db.add(new_contract)
        await db.commit()
        await db.refresh(new_contract)
        
        return new_contract
