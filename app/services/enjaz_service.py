"""
Service layer for Enjaz operations.

This module handles business logic for Enjaz account management
and case synchronization.
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.enjaz_repository import EnjazRepository
from ..schemas.enjaz_schemas import (
    EnjazCredentialsRequest,
    EnjazAccountResponse,
    CaseImportedResponse,
    SyncCasesResponse,
    CasesListResponse,
    CaseData
)
from ..utils.enjaz_bot import scrape_enjaz_cases
from ..utils.api_exceptions import ApiException
from ..schemas.response import ApiResponse


class EnjazService:
    """Service for Enjaz-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.enjaz_repo = EnjazRepository(db)
    
    async def connect_enjaz_account(
        self, 
        user_id: int, 
        credentials: EnjazCredentialsRequest
    ) -> ApiResponse:
        """
        Connect an Enjaz account for a user.
        
        Args:
            user_id: ID of the user
            credentials: Enjaz credentials
            
        Returns:
            ApiResponse: Response with success status and data
        """
        try:
            # Check if user already has an Enjaz account
            existing_account = await self.enjaz_repo.get_enjaz_account_by_user_id(user_id)
            
            if existing_account:
                # Update existing account
                updated_account = await self.enjaz_repo.update_enjaz_account(
                    user_id, 
                    credentials.username, 
                    credentials.password
                )
                
                if updated_account:
                    account_response = EnjazAccountResponse(
                        id=updated_account.id,
                        username="***masked***",  # Mask username for security
                        created_at=updated_account.created_at,
                        updated_at=updated_account.updated_at
                    )
                    
                    return ApiResponse(
                        success=True,
                        message="Enjaz account updated successfully",
                        data=account_response.dict()
                    )
                else:
                    raise ApiException(
                        status_code=500,
                        message="Failed to update Enjaz account"
                    )
            else:
                # Create new account
                new_account = await self.enjaz_repo.create_enjaz_account(
                    user_id,
                    credentials.username,
                    credentials.password
                )
                
                account_response = EnjazAccountResponse(
                    id=new_account.id,
                    username="***masked***",  # Mask username for security
                    created_at=new_account.created_at,
                    updated_at=new_account.updated_at
                )
                
                return ApiResponse(
                    success=True,
                    message="Enjaz account connected successfully",
                    data=account_response.dict()
                )
                
        except ValueError as e:
            raise ApiException(
                status_code=400,
                message=str(e)
            )
        except Exception as e:
            raise ApiException(
                status_code=500,
                message=f"Failed to connect Enjaz account: {str(e)}"
            )
    
    async def sync_cases(self, user_id: int) -> ApiResponse:
        """
        Sync cases from Enjaz system for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            ApiResponse: Response with sync results
        """
        try:
            # Get user's Enjaz credentials
            credentials = await self.enjaz_repo.get_decrypted_credentials(user_id)
            if not credentials:
                raise ApiException(
                    status_code=400,
                    message="No Enjaz account found. Please connect your Enjaz account first."
                )
            
            username, password = credentials
            
            # Scrape cases from Enjaz
            scraped_cases = await scrape_enjaz_cases(username, password, headless=True)
            
            if not scraped_cases:
                return ApiResponse(
                    success=False,
                    message="No cases found or failed to scrape cases from Enjaz",
                    data=None
                )
            
            # Save cases to database
            cases_created, cases_updated = await self.enjaz_repo.create_or_update_cases(
                user_id, 
                scraped_cases
            )
            
            total_cases = len(scraped_cases)
            
            sync_response = SyncCasesResponse(
                success=True,
                message=f"Successfully synced {total_cases} cases",
                cases_imported=cases_created,
                cases_updated=cases_updated,
                total_cases=total_cases
            )
            
            return ApiResponse(
                success=True,
                message="Cases synced successfully",
                data=sync_response.dict()
            )
            
        except ApiException:
            raise
        except Exception as e:
            raise ApiException(
                status_code=500,
                message=f"Failed to sync cases: {str(e)}"
            )
    
    async def get_user_cases(
        self, 
        user_id: int, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> ApiResponse:
        """
        Get all cases for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of cases to return
            offset: Number of cases to skip
            
        Returns:
            ApiResponse: Response with cases list
        """
        try:
            # Get cases from database
            cases = await self.enjaz_repo.get_cases_by_user_id(user_id, limit, offset)
            total_count = await self.enjaz_repo.get_cases_count_by_user_id(user_id)
            
            # Convert to response format
            cases_response = [
                CaseImportedResponse(
                    id=case.id,
                    case_number=case.case_number,
                    case_type=case.case_type,
                    status=case.status,
                    case_data=case.case_data,
                    created_at=case.created_at,
                    updated_at=case.updated_at
                )
                for case in cases
            ]
            
            cases_list_response = CasesListResponse(
                success=True,
                message=f"Retrieved {len(cases_response)} cases",
                data=cases_response,
                total_count=total_count
            )
            
            return ApiResponse(
                success=True,
                message="Cases retrieved successfully",
                data=cases_list_response.dict()
            )
            
        except Exception as e:
            raise ApiException(
                status_code=500,
                message=f"Failed to retrieve cases: {str(e)}"
            )
    
    async def get_enjaz_account_status(self, user_id: int) -> ApiResponse:
        """
        Get Enjaz account connection status for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            ApiResponse: Response with account status
        """
        try:
            account = await self.enjaz_repo.get_enjaz_account_by_user_id(user_id)
            
            if account:
                account_response = EnjazAccountResponse(
                    id=account.id,
                    username="***masked***",
                    created_at=account.created_at,
                    updated_at=account.updated_at
                )
                
                return ApiResponse(
                    success=True,
                    message="Enjaz account is connected",
                    data=account_response.dict()
                )
            else:
                return ApiResponse(
                    success=False,
                    message="No Enjaz account connected",
                    data=None
                )
                
        except Exception as e:
            raise ApiException(
                status_code=500,
                message=f"Failed to check Enjaz account status: {str(e)}"
            )
    
    async def disconnect_enjaz_account(self, user_id: int) -> ApiResponse:
        """
        Disconnect and delete Enjaz account for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            ApiResponse: Response confirming disconnection
        """
        try:
            # Delete Enjaz account
            account_deleted = await self.enjaz_repo.delete_enjaz_account(user_id)
            
            if account_deleted:
                # Also delete all associated cases
                cases_deleted = await self.enjaz_repo.delete_cases_by_user_id(user_id)
                
                return ApiResponse(
                    success=True,
                    message=f"Enjaz account disconnected successfully. {cases_deleted} associated cases were also deleted.",
                    data={
                        "account_deleted": True,
                        "cases_deleted": cases_deleted
                    }
                )
            else:
                return ApiResponse(
                    success=False,
                    message="No Enjaz account found to disconnect",
                    data=None
                )
                
        except Exception as e:
            raise ApiException(
                status_code=500,
                message=f"Failed to disconnect Enjaz account: {str(e)}"
            )
