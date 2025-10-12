"""
Legal Case Service

Business logic layer for managing legal cases.
Provides clean separation between routes and data access.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....repositories.legal_knowledge_repository import (
    LegalCaseRepository,
    CaseSectionRepository
)
from ....models.legal_knowledge import LegalCase, CaseSection, KnowledgeDocument, KnowledgeChunk

logger = logging.getLogger(__name__)


def _format_case_chunk_content(section_type: str, content: str) -> str:
    """
    Format case chunk content to include section type for better search results.
    
    Args:
        section_type: The type of the case section (e.g., "summary", "facts", "ruling")
        content: The content of the section
        
    Returns:
        Formatted content with section type header and content combined
    """
    # Map section types to Arabic labels
    section_labels = {
        "summary": "ملخص القضية",
        "facts": "وقائع القضية",
        "arguments": "حجج الأطراف",
        "ruling": "الحكم",
        "legal_basis": "الأساس القانوني"
    }
    
    label = section_labels.get(section_type, section_type)
    return f"**{label}**\n\n{content}"


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

    async def upload_json_case_structure(
        self,
        json_data: Dict[str, Any],
        uploaded_by: int = 1
    ) -> Dict[str, Any]:
        """
        Upload legal case structure from JSON data directly to database.
        
        Args:
            json_data: JSON data containing legal case structure
            uploaded_by: User ID who uploaded the data
            
        Returns:
            Dict with success status and processing results
            
        Expected JSON structure:
        {
            "legal_cases": [
                {
                    "case_number": "123/2024",
                    "title": "Case Title",
                    "description": "Case description",
                    "jurisdiction": "الرياض",
                    "court_name": "المحكمة العامة",
                    "decision_date": "2024-01-15",
                    "case_type": "مدني",
                    "court_level": "ابتدائي",
                    "sections": [
                        {
                            "section_type": "summary",
                            "content": "Case summary..."
                        },
                        {
                            "section_type": "facts",
                            "content": "Facts of the case..."
                        },
                        {
                            "section_type": "ruling",
                            "content": "Court ruling..."
                        }
                    ]
                }
            ],
            "processing_report": {
                "total_cases": 1,
                "warnings": [],
                "errors": []
            }
        }
        """
        try:
            logger.info("Starting JSON case structure upload")
            
            # Extract legal cases data
            legal_cases = json_data.get("legal_cases", [])
            if not legal_cases:
                return {
                    "success": False,
                    "message": "No legal cases found in JSON",
                    "data": None,
                    "errors": [{"field": "legal_cases", "message": "Missing or empty legal_cases array"}]
                }
            
            processing_report = json_data.get("processing_report", {})
            
            # Generate unique hash for JSON upload based on content
            json_content = json.dumps(json_data, sort_keys=True, ensure_ascii=False)
            unique_hash = hashlib.sha256(json_content.encode('utf-8')).hexdigest()
            
            total_cases = 0
            total_sections = 0
            created_case_ids = []
            
            # Process each legal case
            for case_data in legal_cases:
                # Create KnowledgeDocument for the case (no file, just metadata)
                case_title = case_data.get("title", "Unknown Case")
                knowledge_doc = KnowledgeDocument(
                    title=f"JSON Upload: {case_title}",
                    category="case",
                    file_path=f"json_upload_case_{unique_hash[:8]}_{total_cases}.json",
                    file_hash=f"{unique_hash}_{total_cases}",  # Unique hash per case
                    source_type="uploaded",
                    uploaded_by=uploaded_by,
                    status="processed",
                    document_metadata={
                        "source": "json_upload",
                        "case_type": case_data.get("case_type"),
                        "court_level": case_data.get("court_level"),
                        "processing_report": processing_report
                    }
                )
                
                self.db.add(knowledge_doc)
                await self.db.flush()
                logger.info(f"Created KnowledgeDocument {knowledge_doc.id} for case")
                
                # Parse decision_date if provided
                decision_date = None
                if case_data.get("decision_date"):
                    decision_date = self._parse_date(case_data.get("decision_date"))
                
                # Create LegalCase
                legal_case = LegalCase(
                    document_id=knowledge_doc.id,
                    case_number=case_data.get("case_number"),
                    title=case_title,
                    description=case_data.get("description"),
                    jurisdiction=case_data.get("jurisdiction"),
                    court_name=case_data.get("court_name"),
                    decision_date=decision_date,
                    case_type=case_data.get("case_type"),
                    court_level=case_data.get("court_level"),
                    status="processed",
                    created_at=datetime.utcnow()
                )
                
                self.db.add(legal_case)
                await self.db.flush()
                logger.info(f"Created LegalCase {legal_case.id}: {legal_case.title}")
                
                total_cases += 1
                created_case_ids.append(legal_case.id)
                
                # Process case sections
                sections_data = case_data.get("sections", [])
                chunk_index = 0
                
                for section_data in sections_data:
                    section_type = section_data.get("section_type", "summary")
                    content = section_data.get("content", "")
                    
                    # Validate section_type
                    valid_types = ["summary", "facts", "arguments", "ruling", "legal_basis"]
                    if section_type not in valid_types:
                        logger.warning(f"Invalid section_type '{section_type}', defaulting to 'summary'")
                        section_type = "summary"
                    
                    # Create CaseSection
                    case_section = CaseSection(
                        case_id=legal_case.id,
                        section_type=section_type,
                        content=content,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(case_section)
                    await self.db.flush()
                    total_sections += 1
                    
                    # Create KnowledgeChunk for the section with section type included
                    chunk_content = _format_case_chunk_content(section_type, content)
                    chunk = KnowledgeChunk(
                        document_id=knowledge_doc.id,
                        chunk_index=chunk_index,
                        content=chunk_content,
                        case_id=legal_case.id,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(chunk)
                    chunk_index += 1
            
            # Commit all changes
            await self.db.commit()
            
            # Prepare response data
            response_data = {
                "cases": [
                    {
                        "id": case_id,
                        "case_number": legal_cases[idx].get("case_number"),
                        "title": legal_cases[idx].get("title")
                    }
                    for idx, case_id in enumerate(created_case_ids)
                ],
                "statistics": {
                    "total_cases": total_cases,
                    "total_sections": total_sections,
                    "processing_report": processing_report
                }
            }
            
            logger.info(f"Successfully processed JSON case structure: {total_cases} cases, {total_sections} sections")
            
            return {
                "success": True,
                "message": f"Successfully processed {total_cases} legal case(s) with {total_sections} section(s)",
                "data": response_data,
                "errors": []
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to upload JSON case structure: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to upload JSON case structure: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If no format works, return None
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {str(e)}")
            return None

