"""
Repository for Enjaz-related database operations.

This module handles all database operations for Enjaz accounts
and imported cases.
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ..models.enjaz_account import EnjazAccount
from ..models.case_imported import CaseImported
from ..models.user import User
from ..schemas.enjaz_schemas import CaseData
from ..utils.encryption import encrypt_data, decrypt_data


class EnjazRepository:
    """Repository for Enjaz-related database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_enjaz_account(
        self, 
        user_id: int, 
        username: str, 
        password: str
    ) -> EnjazAccount:
        """
        Create a new Enjaz account with encrypted credentials.
        
        Args:
            user_id: ID of the user
            username: Enjaz username
            password: Enjaz password
            
        Returns:
            EnjazAccount: The created account
            
        Raises:
            ValueError: If user already has an Enjaz account
        """
        # Check if user already has an Enjaz account
        existing_account = await self.get_enjaz_account_by_user_id(user_id)
        if existing_account:
            raise ValueError("User already has an Enjaz account")
        
        # Encrypt credentials
        encrypted_username = encrypt_data(username)
        encrypted_password = encrypt_data(password)
        
        # Create new account
        enjaz_account = EnjazAccount(
            user_id=user_id,
            username=encrypted_username,
            password=encrypted_password
        )
        
        self.db.add(enjaz_account)
        await self.db.commit()
        await self.db.refresh(enjaz_account)
        
        return enjaz_account
    
    async def get_enjaz_account_by_user_id(self, user_id: int) -> Optional[EnjazAccount]:
        """
        Get Enjaz account by user ID.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[EnjazAccount]: The account if found, None otherwise
        """
        result = await self.db.execute(
            select(EnjazAccount).where(EnjazAccount.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_decrypted_credentials(self, user_id: int) -> Optional[Tuple[str, str]]:
        """
        Get decrypted Enjaz credentials for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[Tuple[str, str]]: (username, password) if found, None otherwise
        """
        account = await self.get_enjaz_account_by_user_id(user_id)
        if not account:
            return None
        
        try:
            username = decrypt_data(account.username)
            password = decrypt_data(account.password)
            return (username, password)
        except ValueError:
            # If decryption fails, return None
            return None
    
    async def update_enjaz_account(
        self, 
        user_id: int, 
        username: str, 
        password: str
    ) -> Optional[EnjazAccount]:
        """
        Update existing Enjaz account credentials.
        
        Args:
            user_id: ID of the user
            username: New Enjaz username
            password: New Enjaz password
            
        Returns:
            Optional[EnjazAccount]: The updated account if found, None otherwise
        """
        # Encrypt new credentials
        encrypted_username = encrypt_data(username)
        encrypted_password = encrypt_data(password)
        
        # Update account
        result = await self.db.execute(
            update(EnjazAccount)
            .where(EnjazAccount.user_id == user_id)
            .values(
                username=encrypted_username,
                password=encrypted_password
            )
            .returning(EnjazAccount)
        )
        
        updated_account = result.scalar_one_or_none()
        if updated_account:
            await self.db.commit()
            await self.db.refresh(updated_account)
        
        return updated_account
    
    async def delete_enjaz_account(self, user_id: int) -> bool:
        """
        Delete Enjaz account for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(EnjazAccount).where(EnjazAccount.user_id == user_id)
        )
        
        if result.rowcount > 0:
            await self.db.commit()
            return True
        return False
    
    async def create_or_update_cases(
        self, 
        user_id: int, 
        cases: List[CaseData]
    ) -> Tuple[int, int]:
        """
        Create or update cases for a user.
        
        Args:
            user_id: ID of the user
            cases: List of case data from Enjaz
            
        Returns:
            Tuple[int, int]: (cases_created, cases_updated)
        """
        cases_created = 0
        cases_updated = 0
        
        for case_data in cases:
            # Check if case already exists
            existing_case = await self.get_case_by_number(user_id, case_data.case_number)
            
            if existing_case:
                # Update existing case
                await self.db.execute(
                    update(CaseImported)
                    .where(CaseImported.id == existing_case.id)
                    .values(
                        case_type=case_data.case_type,
                        status=case_data.status,
                        case_data=case_data.additional_data
                    )
                )
                cases_updated += 1
            else:
                # Create new case
                new_case = CaseImported(
                    user_id=user_id,
                    case_number=case_data.case_number,
                    case_type=case_data.case_type,
                    status=case_data.status,
                    case_data=case_data.additional_data
                )
                self.db.add(new_case)
                cases_created += 1
        
        await self.db.commit()
        return cases_created, cases_updated
    
    async def get_case_by_number(
        self, 
        user_id: int, 
        case_number: str
    ) -> Optional[CaseImported]:
        """
        Get a case by case number for a specific user.
        
        Args:
            user_id: ID of the user
            case_number: Case number
            
        Returns:
            Optional[CaseImported]: The case if found, None otherwise
        """
        result = await self.db.execute(
            select(CaseImported)
            .where(
                CaseImported.user_id == user_id,
                CaseImported.case_number == case_number
            )
        )
        return result.scalar_one_or_none()
    
    async def get_cases_by_user_id(
        self, 
        user_id: int, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CaseImported]:
        """
        Get all cases for a user with optional pagination.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of cases to return
            offset: Number of cases to skip
            
        Returns:
            List[CaseImported]: List of cases
        """
        query = select(CaseImported).where(CaseImported.user_id == user_id)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_cases_count_by_user_id(self, user_id: int) -> int:
        """
        Get total count of cases for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Total number of cases
        """
        result = await self.db.execute(
            select(CaseImported).where(CaseImported.user_id == user_id)
        )
        return len(result.scalars().all())
    
    async def delete_cases_by_user_id(self, user_id: int) -> int:
        """
        Delete all cases for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of cases deleted
        """
        result = await self.db.execute(
            delete(CaseImported).where(CaseImported.user_id == user_id)
        )
        
        if result.rowcount > 0:
            await self.db.commit()
        
        return result.rowcount
