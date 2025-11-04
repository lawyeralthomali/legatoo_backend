"""
Contracts Library Service

Business logic layer for contracts library operations including
CRUD, AI generation, revisions, and template management.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ...repositories.contracts_library_repository import ContractsLibraryRepository
from ...schemas.contracts_library import (
    ContractCreate, ContractUpdate, ContractResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    RevisionCreate, RevisionResponse,
    AIGenerateRequest, AIGenerateResponse,
    ContractFilters, TemplateFilters
)
from .ai_contract_generator import AIContractGenerator
from ...config.enhanced_logging import get_logger

logger = get_logger(__name__)


class ContractsLibraryService:
    """Service for contracts library operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ContractsLibraryRepository(db)
        self.ai_generator = AIContractGenerator()
    
    # ============ Contract Operations ============
    
    async def create_contract(
        self,
        contract_data: ContractCreate,
        user_id: int
    ) -> ContractResponse:
        """Create a new contract."""
        # Ensure user_id is an int
        if not isinstance(user_id, int):
            user_id = int(user_id)
        
        contract_dict = contract_data.dict()
        contract_dict["created_by"] = user_id
        contract_dict["version"] = 1
        
        contract = await self.repository.create_contract(contract_dict)
        return ContractResponse.model_validate(contract)
    
    async def get_contract(self, contract_id: str, user_id: Optional[int] = None) -> Optional[ContractResponse]:
        """Get contract by ID with access control."""
        # Ensure user_id is an int if provided
        if user_id is not None and not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = None
        
        contract = await self.repository.get_contract_by_id(contract_id)
        if not contract:
            return None
        
        # Check access: user can only access their own contracts unless admin
        if user_id is not None and contract.created_by != user_id:
            # TODO: Add admin check here
            raise ValueError("Access denied: You don't have permission to view this contract")
        
        return ContractResponse.model_validate(contract)
    
    async def list_contracts(
        self,
        filters: ContractFilters,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination."""
        # Filter by user's contracts unless admin
        filter_dict = filters.dict(exclude={"page", "page_size", "search_query"})
        filter_dict["search_query"] = filters.search_query
        
        if user_id:
            # Regular users only see their own contracts
            filter_dict["created_by"] = user_id
        
        skip = (filters.page - 1) * filters.page_size
        contracts, total = await self.repository.get_contracts(
            skip=skip,
            limit=filters.page_size,
            filters=filter_dict
        )
        
        return {
            "contracts": [ContractResponse.model_validate(c) for c in contracts],
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size
        }
    
    async def update_contract(
        self,
        contract_id: str,
        update_data: ContractUpdate,
        user_id: int
    ) -> Optional[ContractResponse]:
        """Update contract (creates revision automatically)."""
        contract = await self.repository.get_contract_by_id(contract_id)
        if not contract:
            return None
        
        # Check access
        if contract.created_by != user_id:
            raise ValueError("Access denied: You don't have permission to edit this contract")
        
        # Get current content for revision
        old_content = contract.content
        old_version = contract.version
        
        # Update contract
        update_dict = update_data.dict(exclude_unset=True)
        if "content" in update_dict and update_dict["content"] != old_content:
            # Create revision before updating
            latest_revision = await self.repository.get_latest_revision_number(contract_id)
            await self.repository.create_revision({
                "contract_id": contract_id,
                "revision_number": latest_revision + 1,
                "updated_content": old_content or "",
                "updated_by": user_id,
                "changes_summary": update_dict.get("changes_summary", "Contract updated")
            })
            # Increment version
            update_dict["version"] = old_version + 1
        
        updated_contract = await self.repository.update_contract(contract_id, update_dict)
        if not updated_contract:
            return None
        
        return ContractResponse.model_validate(updated_contract)
    
    async def delete_contract(self, contract_id: str, user_id: int) -> bool:
        """Soft delete (archive) contract."""
        contract = await self.repository.get_contract_by_id(contract_id)
        if not contract:
            return False
        
        # Check access
        if contract.created_by != user_id:
            raise ValueError("Access denied: You don't have permission to delete this contract")
        
        return await self.repository.delete_contract(contract_id)
    
    # ============ AI Generation ============
    
    async def generate_contract_with_ai(
        self,
        request: AIGenerateRequest,
        user_id: int
    ) -> AIGenerateResponse:
        """Generate contract using AI."""
        # Generate contract with AI
        result = await self.ai_generator.generate_contract(
            prompt_text=request.prompt_text,
            category=request.category,
            jurisdiction=request.jurisdiction,
            language=request.language or "en",
            structured_data=request.structured_data,
            ai_model=request.ai_model
        )
        
        if not result["success"]:
            raise ValueError(f"AI generation failed: {result.get('error', 'Unknown error')}")
        
        # Save AI request
        ai_request = await self.repository.create_ai_request({
            "user_id": user_id,
            "prompt_text": request.prompt_text,
            "ai_model": result["ai_model"],
            "generated_content": result["generated_content"]
        })
        
        return AIGenerateResponse(
            request_id=ai_request.id,
            generated_content=result["generated_content"],
            ai_model=result["ai_model"],
            created_at=result["created_at"],
            contract_id=None
        )
    
    async def save_ai_generated_contract(
        self,
        request_id: str,
        contract_data: ContractCreate,
        user_id: int
    ) -> ContractResponse:
        """Save AI-generated content as a contract."""
        # Get AI request
        ai_request = await self.repository.get_ai_request_by_id(request_id)
        if not ai_request or ai_request.user_id != user_id:
            raise ValueError("AI request not found or access denied")
        
        # Create contract from AI content
        contract_dict = contract_data.dict()
        contract_dict["created_by"] = user_id
        contract_dict["content"] = ai_request.generated_content
        contract_dict["ai_generated"] = True
        contract_dict["version"] = 1
        
        contract = await self.repository.create_contract(contract_dict)
        
        # Link AI request to contract
        await self.repository.update_ai_request(request_id, {
            "used_in_contract_id": contract.id
        })
        
        return ContractResponse.model_validate(contract)
    
    # ============ Revision Operations ============
    
    async def create_revision(
        self,
        contract_id: str,
        revision_data: RevisionCreate,
        user_id: int
    ) -> RevisionResponse:
        """Create a new revision for a contract."""
        contract = await self.repository.get_contract_by_id(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        # Check access
        if contract.created_by != user_id:
            raise ValueError("Access denied")
        
        # Get next revision number
        latest_revision = await self.repository.get_latest_revision_number(contract_id)
        
        # Create revision
        revision = await self.repository.create_revision({
            "contract_id": contract_id,
            "revision_number": latest_revision + 1,
            "updated_content": revision_data.updated_content,
            "updated_by": user_id,
            "changes_summary": revision_data.changes_summary
        })
        
        # Update contract version
        await self.repository.update_contract(contract_id, {
            "version": latest_revision + 1,
            "content": revision_data.updated_content
        })
        
        return RevisionResponse.model_validate(revision)
    
    async def get_revision_history(self, contract_id: str, user_id: int) -> Dict[str, Any]:
        """Get revision history for a contract."""
        contract = await self.repository.get_contract_by_id(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        # Check access
        if contract.created_by != user_id:
            raise ValueError("Access denied")
        
        revisions = await self.repository.get_revision_history(contract_id)
        
        return {
            "contract_id": contract_id,
            "revisions": [RevisionResponse.model_validate(r) for r in revisions],
            "total_revisions": len(revisions)
        }
    
    # ============ Template Operations ============
    
    async def create_template(
        self,
        template_data: TemplateCreate,
        user_id: int
    ) -> TemplateResponse:
        """Create a new template."""
        template_dict = template_data.dict()
        template_dict["created_by"] = user_id
        
        template = await self.repository.create_template(template_dict)
        return TemplateResponse.model_validate(template)
    
    async def get_template(self, template_id: str, user_id: Optional[int] = None) -> Optional[TemplateResponse]:
        """Get template by ID."""
        template = await self.repository.get_template_by_id(template_id)
        if not template:
            return None
        
        # Check access: public templates or user's own templates
        if user_id and not template.is_public and template.created_by != user_id:
            raise ValueError("Access denied: Template is private")
        
        return TemplateResponse.model_validate(template)
    
    async def list_templates(
        self,
        filters: TemplateFilters,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List templates with filtering."""
        filter_dict = filters.dict(exclude={"page", "page_size", "search_query"})
        filter_dict["search_query"] = filters.search_query
        
        # Regular users see public templates + their own
        if user_id and filters.created_by is None:
            # Show public templates OR user's templates
            # This is handled in repository by checking is_public or created_by
            pass
        
        skip = (filters.page - 1) * filters.page_size
        templates, total = await self.repository.get_templates(
            skip=skip,
            limit=filters.page_size,
            filters=filter_dict
        )
        
        # Filter out private templates user doesn't own
        if user_id:
            filtered_templates = [
                t for t in templates
                if t.is_public or t.created_by == user_id
            ]
        else:
            filtered_templates = [t for t in templates if t.is_public]
        
        return {
            "templates": [TemplateResponse.model_validate(t) for t in filtered_templates],
            "total": len(filtered_templates),
            "page": filters.page,
            "page_size": filters.page_size
        }
    
    async def update_template(
        self,
        template_id: str,
        update_data: TemplateUpdate,
        user_id: int
    ) -> Optional[TemplateResponse]:
        """Update template."""
        template = await self.repository.get_template_by_id(template_id)
        if not template:
            return None
        
        # Check access
        if template.created_by != user_id:
            raise ValueError("Access denied")
        
        update_dict = update_data.dict(exclude_unset=True)
        updated_template = await self.repository.update_template(template_id, update_dict)
        if not updated_template:
            return None
        
        return TemplateResponse.model_validate(updated_template)
    
    async def delete_template(self, template_id: str, user_id: int) -> bool:
        """Delete template."""
        template = await self.repository.get_template_by_id(template_id)
        if not template:
            return False
        
        # Check access
        if template.created_by != user_id:
            raise ValueError("Access denied")
        
        return await self.repository.delete_template(template_id)
    
    async def generate_from_template(
        self,
        template_id: str,
        placeholder_data: Dict[str, Any],
        user_id: int
    ) -> ContractResponse:
        """Generate contract from template by replacing placeholders."""
        template = await self.repository.get_template_by_id(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Check access
        if not template.is_public and template.created_by != user_id:
            raise ValueError("Access denied")
        
        # Replace placeholders
        content = self.ai_generator.replace_placeholders(
            template.content,
            placeholder_data
        )
        
        # Create contract
        contract = await self.repository.create_contract({
            "title": f"{template.name} - Generated Contract",
            "category": None,  # Can extract from template tags
            "jurisdiction": template.jurisdiction,
            "language": template.language,
            "status": "draft",
            "content": content,
            "created_by": user_id,
            "version": 1,
            "ai_generated": False
        })
        
        return ContractResponse.model_validate(contract)
