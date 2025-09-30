from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, desc
from typing import List, Optional
from ..models.user_contract import UserContract


class UserContractRepository:
    """Repository for user contract operations following SOLID principles."""
    
    def __init__(self):
        pass
    
    async def get_by_id(self, db: AsyncSession, user_contract_id: int) -> Optional[UserContract]:
        """Get user contract by ID with relationships."""
        result = await db.execute(
            select(UserContract)
            .options(
                selectinload(UserContract.user),
                selectinload(UserContract.template)
            )
            .where(UserContract.user_contract_id == user_contract_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> List[UserContract]:
        """Get all contracts for a user."""
        result = await db.execute(
            select(UserContract)
            .options(selectinload(UserContract.template))
            .where(UserContract.user_id == user_id)
            .order_by(desc(UserContract.created_at))
        )
        return result.scalars().all()
    
    async def get_by_user_and_template(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> List[UserContract]:
        """Get contracts for a specific user and template."""
        result = await db.execute(
            select(UserContract)
            .where(
                and_(
                    UserContract.user_id == user_id,
                    UserContract.template_id == template_id
                )
            )
            .order_by(desc(UserContract.created_at))
        )
        return result.scalars().all()
    
    async def get_by_status(self, db: AsyncSession, status: str) -> List[UserContract]:
        """Get contracts by status."""
        result = await db.execute(
            select(UserContract)
            .options(
                selectinload(UserContract.user),
                selectinload(UserContract.template)
            )
            .where(UserContract.status == status)
            .order_by(desc(UserContract.created_at))
        )
        return result.scalars().all()
    
    async def get_user_contracts_by_status(
        self, 
        db: AsyncSession, 
        user_id: int, 
        status: str
    ) -> List[UserContract]:
        """Get contracts for a user by status."""
        result = await db.execute(
            select(UserContract)
            .options(selectinload(UserContract.template))
            .where(
                and_(
                    UserContract.user_id == user_id,
                    UserContract.status == status
                )
            )
            .order_by(desc(UserContract.created_at))
        )
        return result.scalars().all()
    
    async def get_draft_contracts(self, db: AsyncSession, user_id: int) -> List[UserContract]:
        """Get draft contracts for a user."""
        return await self.get_user_contracts_by_status(db, user_id, "draft")
    
    async def get_completed_contracts(self, db: AsyncSession, user_id: int) -> List[UserContract]:
        """Get completed contracts for a user."""
        return await self.get_user_contracts_by_status(db, user_id, "completed")
    
    async def get_signed_contracts(self, db: AsyncSession, user_id: int) -> List[UserContract]:
        """Get signed contracts for a user."""
        return await self.get_user_contracts_by_status(db, user_id, "signed")
    
    async def update_status(
        self, 
        db: AsyncSession, 
        user_contract_id: int, 
        status: str
    ) -> bool:
        """Update contract status."""
        contract = await self.get_by_id(db, user_contract_id)
        if contract:
            contract.status = status
            await db.commit()
            return True
        return False
    
    async def update_contract_data(
        self, 
        db: AsyncSession, 
        user_contract_id: int, 
        contract_data: dict
    ) -> bool:
        """Update contract data."""
        contract = await self.get_by_id(db, user_contract_id)
        if contract:
            contract.contract_data = contract_data
            await db.commit()
            return True
        return False
    
    async def update_final_content(
        self, 
        db: AsyncSession, 
        user_contract_id: int, 
        final_content: str
    ) -> bool:
        """Update final contract content."""
        contract = await self.get_by_id(db, user_contract_id)
        if contract:
            contract.final_content = final_content
            await db.commit()
            return True
        return False
    
    async def get_recent_contracts(self, db: AsyncSession, limit: int = 10) -> List[UserContract]:
        """Get recently created contracts."""
        result = await db.execute(
            select(UserContract)
            .options(
                selectinload(UserContract.user),
                selectinload(UserContract.template)
            )
            .order_by(desc(UserContract.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_contracts_count_by_user(self, db: AsyncSession, user_id: int) -> dict:
        """Get contracts count by status for a user."""
        result = await db.execute(
            select(UserContract.status, db.func.count(UserContract.user_contract_id))
            .where(UserContract.user_id == user_id)
            .group_by(UserContract.status)
        )
        return {status: count for status, count in result.fetchall()}
