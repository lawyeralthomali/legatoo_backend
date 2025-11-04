"""
Repository for Contracts Library data access.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from ..models.contracts_library import (
    ContractLibrary, ContractTemplateLibrary, ContractRevision, ContractAIRequest
)


class ContractsLibraryRepository:
    """Repository for contracts library operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ Contract Operations ============
    
    async def create_contract(self, contract_data: Dict[str, Any]) -> ContractLibrary:
        """Create a new contract."""
        contract = ContractLibrary(**contract_data)
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract
    
    async def get_contract_by_id(self, contract_id: str) -> Optional[ContractLibrary]:
        """Get contract by ID."""
        result = await self.db.execute(
            select(ContractLibrary).where(ContractLibrary.id == contract_id)
        )
        return result.scalar_one_or_none()
    
    async def get_contracts(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[ContractLibrary], int]:
        """
        Get contracts with pagination and filtering.
        
        Returns:
            Tuple of (contracts list, total count)
        """
        query = select(ContractLibrary)
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.get("category"):
                conditions.append(ContractLibrary.category == filters["category"])
            
            if filters.get("jurisdiction"):
                conditions.append(ContractLibrary.jurisdiction == filters["jurisdiction"])
            
            if filters.get("status"):
                conditions.append(ContractLibrary.status == filters["status"])
            
            if filters.get("language"):
                conditions.append(ContractLibrary.language == filters["language"])
            
            if filters.get("ai_generated") is not None:
                conditions.append(ContractLibrary.ai_generated == filters["ai_generated"])
            
            if filters.get("created_by"):
                conditions.append(ContractLibrary.created_by == filters["created_by"])
            
            if filters.get("search_query"):
                search_term = f"%{filters['search_query']}%"
                conditions.append(
                    or_(
                        ContractLibrary.title.ilike(search_term),
                        ContractLibrary.content.ilike(search_term),
                        ContractLibrary.category.ilike(search_term)
                    )
                )
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        contracts = await self.db.execute(
            query.order_by(desc(ContractLibrary.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        return contracts.scalars().all(), total
    
    async def update_contract(
        self,
        contract_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[ContractLibrary]:
        """Update contract."""
        contract = await self.get_contract_by_id(contract_id)
        if not contract:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(contract, key, value)
        
        await self.db.commit()
        await self.db.refresh(contract)
        return contract
    
    async def delete_contract(self, contract_id: str) -> bool:
        """Soft delete (archive) contract."""
        contract = await self.get_contract_by_id(contract_id)
        if not contract:
            return False
        
        contract.status = "archived"
        await self.db.commit()
        return True
    
    # ============ Template Operations ============
    
    async def create_template(self, template_data: Dict[str, Any]) -> ContractTemplateLibrary:
        """Create a new template."""
        template = ContractTemplateLibrary(**template_data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_template_by_id(self, template_id: str) -> Optional[ContractTemplateLibrary]:
        """Get template by ID."""
        result = await self.db.execute(
            select(ContractTemplateLibrary).where(ContractTemplateLibrary.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_templates(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[ContractTemplateLibrary], int]:
        """Get templates with pagination and filtering."""
        query = select(ContractTemplateLibrary)
        
        if filters:
            conditions = []
            
            if filters.get("category"):
                # Check if category in tags or description
                conditions.append(
                    or_(
                        ContractTemplateLibrary.description.ilike(f"%{filters['category']}%")
                    )
                )
            
            if filters.get("jurisdiction"):
                conditions.append(ContractTemplateLibrary.jurisdiction == filters["jurisdiction"])
            
            if filters.get("language"):
                conditions.append(ContractTemplateLibrary.language == filters["language"])
            
            if filters.get("is_public") is not None:
                conditions.append(ContractTemplateLibrary.is_public == filters["is_public"])
            
            if filters.get("created_by"):
                conditions.append(ContractTemplateLibrary.created_by == filters["created_by"])
            
            if filters.get("search_query"):
                search_term = f"%{filters['search_query']}%"
                conditions.append(
                    or_(
                        ContractTemplateLibrary.name.ilike(search_term),
                        ContractTemplateLibrary.description.ilike(search_term),
                        ContractTemplateLibrary.content.ilike(search_term)
                    )
                )
            
            if filters.get("tags"):
                # Filter by tags (tags is a JSON array)
                tag_conditions = []
                for tag in filters["tags"]:
                    tag_conditions.append(
                        ContractTemplateLibrary.tags.contains([tag])
                    )
                if tag_conditions:
                    conditions.append(or_(*tag_conditions))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        templates = await self.db.execute(
            query.order_by(desc(ContractTemplateLibrary.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        return templates.scalars().all(), total
    
    async def update_template(
        self,
        template_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[ContractTemplateLibrary]:
        """Update template."""
        template = await self.get_template_by_id(template_id)
        if not template:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(template, key, value)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template."""
        template = await self.get_template_by_id(template_id)
        if not template:
            return False
        
        await self.db.delete(template)
        await self.db.commit()
        return True
    
    # ============ Revision Operations ============
    
    async def create_revision(self, revision_data: Dict[str, Any]) -> ContractRevision:
        """Create a new revision."""
        revision = ContractRevision(**revision_data)
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision
    
    async def get_revision_history(
        self,
        contract_id: str
    ) -> List[ContractRevision]:
        """Get all revisions for a contract."""
        result = await self.db.execute(
            select(ContractRevision)
            .where(ContractRevision.contract_id == contract_id)
            .order_by(desc(ContractRevision.revision_number))
        )
        return result.scalars().all()
    
    async def get_latest_revision_number(self, contract_id: str) -> int:
        """Get the latest revision number for a contract."""
        result = await self.db.execute(
            select(func.max(ContractRevision.revision_number))
            .where(ContractRevision.contract_id == contract_id)
        )
        max_revision = result.scalar()
        return max_revision if max_revision else 0
    
    # ============ AI Request Operations ============
    
    async def create_ai_request(self, request_data: Dict[str, Any]) -> ContractAIRequest:
        """Create a new AI request record."""
        request = ContractAIRequest(**request_data)
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request
    
    async def get_ai_request_by_id(self, request_id: str) -> Optional[ContractAIRequest]:
        """Get AI request by ID."""
        result = await self.db.execute(
            select(ContractAIRequest).where(ContractAIRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def update_ai_request(
        self,
        request_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[ContractAIRequest]:
        """Update AI request."""
        request = await self.get_ai_request_by_id(request_id)
        if not request:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(request, key, value)
        
        await self.db.commit()
        await self.db.refresh(request)
        return request
