"""
Legal Case Service

Business logic layer for managing legal cases.
Provides clean separation between routes and data access.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.legal_knowledge_repository import (
    LegalCaseRepository,
    CaseSectionRepository
)

logger = logging.getLogger(__name__)


class LegalCaseService:
    """Service for managing legal cases."""

    def __init__(self, db: AsyncSession):
        """Initialize the legal case service."""
        self.db = db
        self.case_repo = LegalCaseRepository(db)
        self.section_repo = CaseSectionRepository(db)

    async def list_legal_cases(
        self,
        skip: int = 0,
        limit: int = 50,
        jurisdiction: Optional[str] = None,
        case_type: Optional[str] = None,
        court_level: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all legal cases with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            jurisdiction: Filter by jurisdiction
            case_type: Filter by case type
            court_level: Filter by court level
            status: Filter by status
            search: Search in case title or case number
            
        Returns:
            Dictionary with success status, message, data, and errors
        """
        try:
            # Handle search separately if provided
            if search:
                cases = await self.case_repo.search_cases(search, limit=limit)
                total = len(cases)
                # Apply skip/limit to search results
                cases = cases[skip:skip + limit] if skip < len(cases) else []
            else:
                # Use repository filtering
                cases, total = await self.case_repo.get_cases(
                    skip=skip,
                    limit=limit,
                    jurisdiction=jurisdiction,
                    case_type=case_type,
                    court_level=court_level
                )
                
                # Note: status filter not in repository yet, filter in memory if needed
                if status:
                    cases = [c for c in cases if c.status == status]
                    total = len(cases)
            
            # Format response
            cases_data = []
            for case in cases:
                cases_data.append({
                    'id': case.id,
                    'case_number': case.case_number,
                    'title': case.title,
                    'description': case.description,
                    'jurisdiction': case.jurisdiction,
                    'court_name': case.court_name,
                    'decision_date': case.decision_date.isoformat() if case.decision_date else None,
                    'case_type': case.case_type,
                    'court_level': case.court_level,
                    'status': case.status,
                    'document_id': case.document_id,
                    'created_at': case.created_at.isoformat() if case.created_at else None
                })
            
            return {
                "success": True,
                "message": f"Retrieved {len(cases_data)} legal cases",
                "data": {
                    "cases": cases_data,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                },
                "errors": []
            }
        
        except Exception as e:
            logger.error(f"Failed to list legal cases: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list legal cases: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_legal_case(
        self,
        case_id: int,
        include_sections: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific legal case.
        
        Args:
            case_id: ID of the legal case
            include_sections: Include case sections in response
            
        Returns:
            Dictionary with success status, message, data, and errors
        """
        try:
            # Get case from repository
            case = await self.case_repo.get_case_by_id(case_id)
            
            if not case:
                return {
                    "success": False,
                    "message": f"Legal case with ID {case_id} not found",
                    "data": None,
                    "errors": [{"field": "case_id", "message": "Case not found"}]
                }
            
            # Format case data
            case_data = {
                'id': case.id,
                'case_number': case.case_number,
                'title': case.title,
                'description': case.description,
                'jurisdiction': case.jurisdiction,
                'court_name': case.court_name,
                'decision_date': case.decision_date.isoformat() if case.decision_date else None,
                'case_type': case.case_type,
                'court_level': case.court_level,
                'document_id': case.document_id,
                'status': case.status,
                'created_at': case.created_at.isoformat() if case.created_at else None,
                'updated_at': case.updated_at.isoformat() if case.updated_at else None
            }
            
            # Get sections if requested
            if include_sections:
                sections = await self.section_repo.get_sections_by_case(case_id)
                
                case_data['sections'] = [
                    {
                        'id': section.id,
                        'section_type': section.section_type,
                        'content': section.content,
                        'created_at': section.created_at.isoformat() if section.created_at else None
                    }
                    for section in sections
                ]
                case_data['sections_count'] = len(sections)
            
            return {
                "success": True,
                "message": "Legal case retrieved successfully",
                "data": case_data,
                "errors": []
            }
        
        except Exception as e:
            logger.error(f"Failed to get legal case: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get legal case: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def update_legal_case(
        self,
        case_id: int,
        case_number: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        court_name: Optional[str] = None,
        decision_date: Optional[str] = None,
        case_type: Optional[str] = None,
        court_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update legal case metadata.
        
        Args:
            case_id: ID of the legal case
            case_number: Optional new case number
            title: Optional new title
            description: Optional new description
            jurisdiction: Optional new jurisdiction
            court_name: Optional new court name
            decision_date: Optional new decision date (YYYY-MM-DD)
            case_type: Optional new case type
            court_level: Optional new court level
            
        Returns:
            Dictionary with success status, message, data, and errors
        """
        try:
            # Prepare updates dictionary
            updates = {}
            
            if case_number is not None:
                updates['case_number'] = case_number
            if title is not None:
                updates['title'] = title
            if description is not None:
                updates['description'] = description
            if jurisdiction is not None:
                updates['jurisdiction'] = jurisdiction
            if court_name is not None:
                updates['court_name'] = court_name
            if decision_date is not None:
                try:
                    updates['decision_date'] = datetime.strptime(decision_date, '%Y-%m-%d').date()
                except ValueError:
                    return {
                        "success": False,
                        "message": "Invalid date format. Use YYYY-MM-DD",
                        "data": None,
                        "errors": [{"field": "decision_date", "message": "Invalid date format"}]
                    }
            if case_type is not None:
                updates['case_type'] = case_type
            if court_level is not None:
                updates['court_level'] = court_level
            
            # Update via repository
            case = await self.case_repo.update_legal_case(case_id, **updates)
            
            if not case:
                return {
                    "success": False,
                    "message": f"Legal case with ID {case_id} not found",
                    "data": None,
                    "errors": [{"field": "case_id", "message": "Case not found"}]
                }
            
            return {
                "success": True,
                "message": "Legal case updated successfully",
                "data": {
                    'id': case.id,
                    'case_number': case.case_number,
                    'title': case.title,
                    'updated_at': case.updated_at.isoformat() if case.updated_at else None
                },
                "errors": []
            }
        
        except Exception as e:
            logger.error(f"Failed to update legal case: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update legal case: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def delete_legal_case(self, case_id: int) -> Dict[str, Any]:
        """
        Delete a legal case and all its sections.
        
        Args:
            case_id: ID of the legal case to delete
            
        Returns:
            Dictionary with success status, message, data, and errors
        """
        try:
            # Delete via repository
            deleted = await self.case_repo.delete_legal_case(case_id)
            
            if not deleted:
                return {
                    "success": False,
                    "message": f"Legal case with ID {case_id} not found",
                    "data": None,
                    "errors": [{"field": "case_id", "message": "Case not found"}]
                }
            
            return {
                "success": True,
                "message": f"Legal case {case_id} deleted successfully",
                "data": {"deleted_case_id": case_id},
                "errors": []
            }
        
        except Exception as e:
            logger.error(f"Failed to delete legal case: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete legal case: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    async def get_case_sections(
        self,
        case_id: int,
        section_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all sections of a legal case.
        
        Args:
            case_id: ID of the legal case
            section_type: Optional filter by section type
            
        Returns:
            Dictionary with success status, message, data, and errors
        """
        try:
            # Get sections via repository
            sections = await self.section_repo.get_sections_by_case(
                case_id,
                section_type=section_type
            )
            
            sections_data = [
                {
                    'id': section.id,
                    'case_id': section.case_id,
                    'section_type': section.section_type,
                    'content': section.content,
                    'created_at': section.created_at.isoformat() if section.created_at else None
                }
                for section in sections
            ]
            
            return {
                "success": True,
                "message": f"Retrieved {len(sections_data)} sections",
                "data": {
                    "sections": sections_data,
                    "count": len(sections_data)
                },
                "errors": []
            }
        
        except Exception as e:
            logger.error(f"Failed to get case sections: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get case sections: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

