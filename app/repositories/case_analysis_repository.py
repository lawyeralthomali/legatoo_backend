"""
Repository for Case Analysis History.

Handles database operations for case analysis history.
"""

from typing import List, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from ..models.case_analysis import CaseAnalysis
from ..models.profile import Profile


class CaseAnalysisRepository:
    """Repository for case analysis database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_analysis(
        self,
        user_id: int,
        filename: str,
        file_size_mb: Optional[float],
        analysis_type: str,
        lawsuit_type: str,
        result_seeking: Optional[str],
        user_context: Optional[str],
        analysis_data: dict,
        risk_score: Optional[int],
        risk_label: Optional[str],
        raw_response: Optional[str],
        additional_files: Optional[list]
    ) -> CaseAnalysis:
        """Create a new case analysis record."""
        # For SQLite, JSON columns need to be stored as JSON strings
        # SQLAlchemy should handle this, but ensure it's a dict
        if isinstance(analysis_data, str):
            try:
                analysis_data = json.loads(analysis_data)
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as is if it's not valid JSON string
        
        # SQLAlchemy JSON type will handle additional_files serialization automatically
        analysis = CaseAnalysis(
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
        
        try:
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            return analysis
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def get_analysis_by_id(
        self,
        analysis_id: int,
        user_id: Optional[int] = None
    ) -> Optional[CaseAnalysis]:
        """Get a case analysis by ID, optionally filtered by user_id."""
        query = select(CaseAnalysis).where(CaseAnalysis.id == analysis_id)
        
        if user_id:
            query = query.where(CaseAnalysis.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_analyses(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        analysis_type: Optional[str] = None
    ) -> List[CaseAnalysis]:
        """Get all analyses for a user."""
        query = select(CaseAnalysis).where(CaseAnalysis.user_id == user_id)
        
        if analysis_type:
            query = query.where(CaseAnalysis.analysis_type == analysis_type)
        
        query = query.order_by(desc(CaseAnalysis.created_at)).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_user_analyses_count(
        self,
        user_id: int,
        analysis_type: Optional[str] = None
    ) -> int:
        """Get total count of analyses for a user."""
        from sqlalchemy import func
        
        query = select(func.count(CaseAnalysis.id)).where(CaseAnalysis.user_id == user_id)
        
        if analysis_type:
            query = query.where(CaseAnalysis.analysis_type == analysis_type)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def delete_analysis(
        self,
        analysis_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Delete a case analysis, optionally filtered by user_id."""
        query = select(CaseAnalysis).where(CaseAnalysis.id == analysis_id)
        
        if user_id:
            query = query.where(CaseAnalysis.user_id == user_id)
        
        result = await self.db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if analysis:
            try:
                await self.db.delete(analysis)
                await self.db.commit()
                return True
            except Exception as e:
                await self.db.rollback()
                raise
        
        return False

