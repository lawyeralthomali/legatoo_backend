"""
Template Repository for data access operations.

This module handles all database operations related to contract templates,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .base import BaseRepository
from ..models.contract_template import ContractTemplate, Contract


class TemplateRepository(BaseRepository):
    """Repository for contract template data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize template repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, ContractTemplate)
    
    async def get_template_by_id(self, template_id: str) -> Optional[ContractTemplate]:
        """
        Get template by ID.
        
        Args:
            template_id: Template UUID string
            
        Returns:
            ContractTemplate if found, None otherwise
        """
        result = await self.db.execute(
            select(ContractTemplate).where(ContractTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_templates(self) -> List[ContractTemplate]:
        """
        Get all active templates.
        
        Returns:
            List of active ContractTemplate models
        """
        result = await self.db.execute(
            select(ContractTemplate)
            .where(ContractTemplate.is_active == True)
            .order_by(ContractTemplate.created_at.desc())
        )
        return result.scalars().all()
    
    async def create_contract(
        self,
        template_id: str,
        owner_id: int,
        filled_data: dict,
        pdf_path: Optional[str] = None,
        status: str = 'generated'
    ) -> Contract:
        """
        Create a new contract record.
        
        Args:
            template_id: Template ID
            owner_id: User ID who owns the contract
            filled_data: User-provided form data
            pdf_path: Path to generated PDF
            status: Contract status
            
        Returns:
            Created Contract model
        """
        contract = Contract(
            template_id=template_id,
            owner_id=owner_id,
            filled_data=filled_data,
            pdf_path=pdf_path,
            status=status
        )
        self.db.add(contract)
        await self.db.flush()
        await self.db.refresh(contract)
        return contract
    
    async def get_contract_by_id(self, contract_id: str) -> Optional[Contract]:
        """
        Get contract by ID.
        
        Args:
            contract_id: Contract UUID string
            
        Returns:
            Contract if found, None otherwise
        """
        result = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_contracts(self, owner_id: int) -> List[Contract]:
        """
        Get all contracts for a user.
        
        Args:
            owner_id: User ID
            
        Returns:
            List of Contract models
        """
        result = await self.db.execute(
            select(Contract)
            .where(Contract.owner_id == owner_id)
            .order_by(Contract.created_at.desc())
        )
        return result.scalars().all()

