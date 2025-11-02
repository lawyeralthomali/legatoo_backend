"""
Service for managing case analysis history.

Handles business logic for case analysis history operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.case_analysis import CaseAnalysis
from ...repositories.case_analysis_repository import CaseAnalysisRepository


class CaseAnalysisHistoryService:
    """Service for case analysis history operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CaseAnalysisRepository(db)
    
    async def save_analysis(
        self,
        user_id: int,
        filename: str,
        file_size_mb: Optional[float],
        analysis_type: str,
        lawsuit_type: str,
        result_seeking: Optional[str],
        user_context: Optional[str],
        analysis_data: dict,
        risk_score: Optional[int] = None,
        risk_label: Optional[str] = None,
        raw_response: Optional[str] = None,
        additional_files: Optional[list] = None
    ) -> CaseAnalysis:
        """Save a new case analysis to history."""
        return await self.repository.create_analysis(
            user_id=user_id,
            filename=filename,
            file_size_mb=file_size_mb,
            analysis_type=analysis_type,
            lawsuit_type=lawsuit_type,
            result_seeking=result_seeking,
            user_context=user_context,
            analysis_data=analysis_data,
            risk_score=risk_score,
            risk_label=risk_label,
            raw_response=raw_response,
            additional_files=additional_files
        )
    
    async def get_analysis_by_id(
        self,
        analysis_id: int,
        user_id: Optional[int] = None
    ) -> Optional[CaseAnalysis]:
        """Get a specific analysis by ID."""
        return await self.repository.get_analysis_by_id(analysis_id, user_id)
    
    async def get_user_analyses(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        analysis_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all analyses for a user with pagination."""
        analyses = await self.repository.get_user_analyses(
            user_id=user_id,
            skip=skip,
            limit=limit,
            analysis_type=analysis_type
        )
        
        total = await self.repository.get_user_analyses_count(
            user_id=user_id,
            analysis_type=analysis_type
        )
        
        return {
            "analyses": [analysis.to_dict() for analysis in analyses],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def delete_analysis(
        self,
        analysis_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Delete an analysis."""
        return await self.repository.delete_analysis(analysis_id, user_id)

